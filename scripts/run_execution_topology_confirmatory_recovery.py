#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from swarmsafe_delta.authority_composition import MODEL_CONFIGS
from swarmsafe_delta.authority_placement import AuthorityBedrockTextModel
from swarmsafe_delta.execution_topology_confirmatory import (
    BOOTSTRAP_DRAWS,
    EXPERIMENT_ID as PARENT_EXPERIMENT_ID,
    FORMAL_CASES_PER_MODEL,
    HARD_BUDGET_CAP_USD,
    MAX_ATTEMPTS,
    MAX_OUTPUT_TOKENS,
    MODEL_PRICES,
    PER_CALL_TOKEN_ALLOWANCE,
    analyze_rows,
    projected_allowance_usd,
    run_model_jobs,
    validate_rows,
)
from swarmsafe_delta.execution_topology_pilot import estimate_rows_cost
from swarmsafe_delta.pilot import (
    canonical_json,
    load_tasks,
    sha256_file,
    utc_now,
)
from swarmsafe_delta.topology_pilot import load_jsonl


ROOT = Path(__file__).resolve().parent.parent
PARENT = (
    ROOT
    / "experiments/TopoSafe-Delta-ExecutionTopologyConfirmatory-v0.1"
)
PACKAGE = (
    ROOT
    / "experiments/"
    "TopoSafe-Delta-ExecutionTopologyConfirmatory-v0.1R-TechnicalCompletion"
)
RECOVERY_EXPERIMENT_ID = (
    "TopoSafe-Delta-ExecutionTopologyConfirmatory-v0.1R-TechnicalCompletion"
)
DESIGN = PACKAGE / "design_spec.json"
PROTOCOL = PACKAGE / "protocol.md"
MANIFEST = PACKAGE / "manifest.json"
PARENT_MANIFEST = PARENT / "manifest.json"
PARENT_TASKS = PARENT / "candidate_tasks.json"
PARENT_CASES = PARENT / "proposal_cases.json"
PARENT_NEMOTRON_RAW = (
    PARENT / "models/nemotron-3-super-120b/raw/proposals.jsonl"
)
ABORTED_GPT_RAW = (
    PARENT
    / "aborted_provider_outage/gpt-5.4/raw/proposals.jsonl"
)
RECOVERY_MODELS = ("gpt-5.4", "nemotron-3-super-120b")
FORMAL_RECOVERY_CALLS = {
    "gpt-5.4": FORMAL_CASES_PER_MODEL,
    "nemotron-3-super-120b": 7,
}
MODEL_ID_TO_SLUG = {
    config["model_id"]: slug for slug, config in MODEL_CONFIGS.items()
}


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(canonical_json(row) + "\n")
    temporary.replace(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=("build", "freeze", "run", "analyze"),
        required=True,
    )
    parser.add_argument("--stage", choices=("smoke", "formal"))
    parser.add_argument("--model-slug", choices=RECOVERY_MODELS)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--seed", type=int, default=2026101242)
    parser.add_argument(
        "--budget-cap-usd",
        type=float,
        default=HARD_BUDGET_CAP_USD,
    )
    return parser.parse_args()


def parent_cases() -> list[dict[str, Any]]:
    return json.loads(PARENT_CASES.read_text(encoding="utf-8"))


def selected_cases() -> dict[str, list[dict[str, Any]]]:
    cases = parent_cases()
    case_by_id = {
        f"{case['task_id']}::{case['condition']}": case for case in cases
    }
    nemotron_rows = load_jsonl(PARENT_NEMOTRON_RAW)
    nemotron_ids = sorted(
        row["episode_id"]
        for row in nemotron_rows
        if row.get("provider_error")
    )
    return {
        "gpt-5.4": cases,
        "nemotron-3-super-120b": [
            case_by_id[episode_id] for episode_id in nemotron_ids
        ],
    }


def smoke_ids(cases: list[dict[str, Any]]) -> list[str]:
    ranked = sorted(
        cases,
        key=lambda case: (
            len(
                (
                    case["executor_system"] + case["executor_user"]
                ).encode("utf-8")
            ),
            f"{case['task_id']}::{case['condition']}",
        ),
        reverse=True,
    )
    selected = []
    seen_truths = set()
    for case in ranked:
        if case["claim_truth"] in seen_truths:
            continue
        selected.append(f"{case['task_id']}::{case['condition']}")
        seen_truths.add(case["claim_truth"])
        if len(selected) == 2:
            return sorted(selected)
    for case in ranked:
        episode_id = f"{case['task_id']}::{case['condition']}"
        if episode_id not in selected:
            selected.append(episode_id)
        if len(selected) == 2:
            break
    return sorted(selected)


def build() -> None:
    if MANIFEST.exists():
        raise RuntimeError("recovery package is already frozen")
    selection = selected_cases()
    aborted_gpt = load_jsonl(ABORTED_GPT_RAW)
    errors = []
    if len(aborted_gpt) != 12:
        errors.append(
            f"expected 12 interrupted GPT rows, found {len(aborted_gpt)}"
        )
    if sum(bool(row.get("provider_error")) for row in aborted_gpt) != 10:
        errors.append("interrupted GPT error count is not 10")
    if len(selection["gpt-5.4"]) != FORMAL_CASES_PER_MODEL:
        errors.append("GPT recovery does not contain complete model block")
    if len(selection["nemotron-3-super-120b"]) != 7:
        errors.append("Nemotron recovery selection does not contain 7 rows")
    selected_ids = {
        slug: [
            f"{case['task_id']}::{case['condition']}"
            for case in cases
        ]
        for slug, cases in selection.items()
    }
    payload = {
        "recovery_experiment_id": RECOVERY_EXPERIMENT_ID,
        "parent_experiment_id": PARENT_EXPERIMENT_ID,
        "selection_basis": "provider_technical_status_only",
        "gpt_parent_partial_excluded_in_full": True,
        "selected_episode_ids": selected_ids,
    }
    write_json(PACKAGE / "recovery_selection.json", payload)
    validation = {
        "status": (
            "automatic_recovery_gate_passed"
            if not errors
            else "automatic_recovery_gate_failed"
        ),
        "passed": not errors,
        "gpt_interrupted_rows": len(aborted_gpt),
        "gpt_interrupted_provider_errors": sum(
            bool(row.get("provider_error")) for row in aborted_gpt
        ),
        "selected_counts": {
            slug: len(cases) for slug, cases in selection.items()
        },
        "errors": errors,
    }
    write_json(PACKAGE / "selection_validation.json", validation)
    summary = {
        "recovery_experiment_id": RECOVERY_EXPERIMENT_ID,
        "status": validation["status"],
        "formal_recovery_calls": sum(
            len(cases) for cases in selection.values()
        ),
        "excluded_smoke_calls": 4,
        "projected_recovery_conservative_cost_usd": sum(
            projected_allowance_usd(slug, len(cases))
            for slug, cases in selection.items()
        ),
        "hard_budget_cap_including_parent_usd": HARD_BUDGET_CAP_USD,
    }
    write_json(PACKAGE / "package_summary.json", summary)
    print(canonical_json(summary))
    if errors:
        raise SystemExit(1)


def validate_design() -> None:
    design = json.loads(DESIGN.read_text(encoding="utf-8"))
    errors = []
    if design.get("status") != "pre_run_recovery_design_unfrozen":
        errors.append("recovery design status is incorrect")
    if design.get("provider_calls_completed") != 0:
        errors.append("recovery design reports completed calls")
    formal = design.get("formal_recovery_calls", {})
    if formal.get("total") != sum(FORMAL_RECOVERY_CALLS.values()):
        errors.append("recovery call total differs from code")
    if errors:
        raise RuntimeError("recovery design invalid: " + " | ".join(errors))


def freeze(args: argparse.Namespace) -> None:
    if MANIFEST.exists():
        raise RuntimeError("recovery manifest already exists")
    required = [
        DESIGN,
        PROTOCOL,
        PACKAGE / "recovery_selection.json",
        PACKAGE / "selection_validation.json",
        PACKAGE / "package_summary.json",
        PARENT_MANIFEST,
        PARENT_TASKS,
        PARENT_CASES,
        PARENT_NEMOTRON_RAW,
        PARENT / "models/nemotron-3-super-120b/validation.json",
        PARENT / "models/claude-sonnet-5/raw/proposals.jsonl",
        PARENT / "models/claude-sonnet-5/validation.json",
        PARENT / "models/llama-4-maverick/raw/proposals.jsonl",
        PARENT / "models/llama-4-maverick/validation.json",
        ABORTED_GPT_RAW,
        ROOT / "src/swarmsafe_delta/execution_topology_confirmatory.py",
        ROOT / "src/swarmsafe_delta/execution_topology_pilot.py",
        Path(__file__),
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise RuntimeError(f"missing recovery freeze inputs: {missing}")
    validate_design()
    selection_validation = json.loads(
        (PACKAGE / "selection_validation.json").read_text(
            encoding="utf-8"
        )
    )
    if not selection_validation["passed"]:
        raise RuntimeError("automatic recovery selection gate failed")
    selection = selected_cases()
    manifest = {
        "recovery_experiment_id": RECOVERY_EXPERIMENT_ID,
        "parent_experiment_id": PARENT_EXPERIMENT_ID,
        "status": "frozen_pre_run",
        "frozen_at": utc_now(),
        "active_models": list(RECOVERY_MODELS),
        "formal_recovery_calls": {
            slug: len(cases) for slug, cases in selection.items()
        },
        "smoke_episode_ids": {
            slug: smoke_ids(cases)
            for slug, cases in selection.items()
        },
        "workers": args.workers,
        "schedule_seed": args.seed,
        "max_output_tokens": MAX_OUTPUT_TOKENS,
        "maximum_provider_attempts": MAX_ATTEMPTS,
        "hard_budget_cap_including_parent_usd": args.budget_cap_usd,
        "per_call_token_allowance": {
            slug: PER_CALL_TOKEN_ALLOWANCE[slug]
            for slug in RECOVERY_MODELS
        },
        "source_hashes": {
            str(path.relative_to(ROOT)): sha256_file(path)
            for path in required
        },
    }
    write_json(MANIFEST, manifest)
    print(canonical_json(manifest))


def verify_frozen(
    manifest: dict[str, Any],
    args: argparse.Namespace,
) -> None:
    if manifest.get("status") != "frozen_pre_run":
        raise RuntimeError("recovery manifest is not frozen_pre_run")
    mismatches = []
    for relative, expected in manifest["source_hashes"].items():
        path = ROOT / relative
        if not path.exists():
            mismatches.append(f"{relative}: missing")
        elif sha256_file(path) != expected:
            mismatches.append(f"{relative}: hash mismatch")
    if mismatches:
        raise RuntimeError(
            "recovery frozen source mismatch: " + " | ".join(mismatches)
        )
    runtime = {
        "workers": args.workers,
        "schedule_seed": args.seed,
        "hard_budget_cap_including_parent_usd": args.budget_cap_usd,
    }
    changed = [
        key
        for key, value in runtime.items()
        if manifest.get(key) != value
    ]
    if changed:
        raise ValueError(
            "recovery runtime arguments differ from freeze: "
            + ", ".join(changed)
        )


def all_accounted_rows() -> list[tuple[str, dict[str, Any]]]:
    rows: list[tuple[str, dict[str, Any]]] = []
    for path in PARENT.glob("smoke/*/raw/proposals.jsonl"):
        rows.extend((path.parts[-3], row) for row in load_jsonl(path))
    for slug in (
        "claude-sonnet-5",
        "llama-4-maverick",
        "nemotron-3-super-120b",
    ):
        path = PARENT / f"models/{slug}/raw/proposals.jsonl"
        rows.extend((slug, row) for row in load_jsonl(path))
    rows.extend(("gpt-5.4", row) for row in load_jsonl(ABORTED_GPT_RAW))
    for path in PACKAGE.glob("smoke/*/raw/proposals.jsonl"):
        rows.extend((path.parts[-3], row) for row in load_jsonl(path))
    for path in PACKAGE.glob("models/*/raw/proposals.jsonl"):
        rows.extend((path.parts[-3], row) for row in load_jsonl(path))
    return rows


def spent_conservative_usd() -> float:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for slug, row in all_accounted_rows():
        grouped.setdefault(slug, []).append(row)
    return sum(
        estimate_rows_cost(rows, slug, conservative=True)
        for slug, rows in grouped.items()
    )


def recovery_cases(model_slug: str) -> list[dict[str, Any]]:
    return selected_cases()[model_slug]


def validate_recovery_rows(
    *,
    rows: list[dict[str, Any]],
    cases: list[dict[str, Any]],
    model_slug: str,
) -> dict[str, Any]:
    expected = {
        f"{case['task_id']}::{case['condition']}" for case in cases
    }
    observed = [row["episode_id"] for row in rows]
    provider_errors = sum(bool(row.get("provider_error")) for row in rows)
    malformed = sum(bool(row.get("malformed")) for row in rows)
    truncated = sum(bool(row.get("truncated")) for row in rows)
    errors = []
    if set(observed) != expected:
        errors.append("recovery row IDs differ from frozen selection")
    if len(observed) != len(set(observed)):
        errors.append("duplicate recovery row IDs")
    if provider_errors:
        errors.append(f"provider errors: {provider_errors}")
    if malformed or truncated:
        errors.append(
            f"recovery malformed/truncated rows: {malformed}/{truncated}"
        )
    if model_slug == "gpt-5.4" and len(rows) != FORMAL_CASES_PER_MODEL:
        errors.append("GPT recovery is not a complete model block")
    return {
        "recovery_experiment_id": RECOVERY_EXPERIMENT_ID,
        "model_slug": model_slug,
        "passed": not errors,
        "expected_rows": len(cases),
        "observed_rows": len(rows),
        "provider_errors": provider_errors,
        "malformed": malformed,
        "truncated": truncated,
        "errors": errors,
    }


def require_smoke_pass(model_slug: str) -> None:
    path = PACKAGE / f"smoke/{model_slug}/validation.json"
    if not path.exists():
        raise RuntimeError(f"recovery smoke missing for {model_slug}")
    if not json.loads(path.read_text(encoding="utf-8"))["passed"]:
        raise RuntimeError(f"recovery smoke failed for {model_slug}")


def run(args: argparse.Namespace) -> None:
    if not args.stage or not args.model_slug:
        raise ValueError("--stage and --model-slug are required for run")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    verify_frozen(manifest, args)
    if args.stage == "formal":
        require_smoke_pass(args.model_slug)
    tasks = load_tasks(PARENT_TASKS)
    cases = recovery_cases(args.model_slug)
    if args.stage == "smoke":
        ids = set(manifest["smoke_episode_ids"][args.model_slug])
        cases = [
            case
            for case in cases
            if f"{case['task_id']}::{case['condition']}" in ids
        ]
        stage_dir = "smoke"
    else:
        stage_dir = "models"
    output_dir = PACKAGE / stage_dir / args.model_slug
    raw_path = output_dir / "raw/proposals.jsonl"

    def before_batch(batch_calls: int) -> None:
        spent = spent_conservative_usd()
        prospective = projected_allowance_usd(
            args.model_slug, batch_calls
        )
        cap = manifest["hard_budget_cap_including_parent_usd"]
        if spent + prospective > cap:
            raise RuntimeError(
                "combined hard budget cap would be exceeded: "
                f"spent={spent:.6f}, prospective={prospective:.6f}, "
                f"cap={cap:.2f}"
            )

    config = MODEL_CONFIGS[args.model_slug]
    model = AuthorityBedrockTextModel(
        model_id=config["model_id"],
        region=config["region"],
        temperature=config["temperature"],
        top_p=config["top_p"],
        additional_model_request_fields=config[
            "additional_model_request_fields"
        ],
        force_action_tool=config["force_action_tool"],
        action_tool_mode=config.get("action_tool_mode"),
        max_attempts=manifest["maximum_provider_attempts"],
        connect_timeout_seconds=10,
        read_timeout_seconds=240,
    )
    rows = run_model_jobs(
        tasks=tasks,
        cases=cases,
        model=model,
        workers=args.workers,
        seed=args.seed,
        max_output_tokens=manifest["max_output_tokens"],
        raw_path=raw_path,
        before_batch=before_batch,
        batch_size=24,
    )
    validation = validate_recovery_rows(
        rows=rows,
        cases=cases,
        model_slug=args.model_slug,
    )
    write_json(output_dir / "validation.json", validation)
    budget = {
        "recovery_experiment_id": RECOVERY_EXPERIMENT_ID,
        "stage": args.stage,
        "model_slug": args.model_slug,
        "calls": len(rows),
        "provider_attempts": sum(
            int(row.get("api_attempts") or 0) for row in rows
        ),
        "input_tokens": sum(
            int(row.get("input_tokens") or 0) for row in rows
        ),
        "output_tokens": sum(
            int(row.get("output_tokens") or 0) for row in rows
        ),
        "estimated_cost_usd": estimate_rows_cost(
            rows, args.model_slug, conservative=False
        ),
        "conservative_cost_usd": estimate_rows_cost(
            rows, args.model_slug, conservative=True
        ),
        "combined_cumulative_conservative_cost_usd": (
            spent_conservative_usd()
        ),
        "combined_hard_budget_cap_usd": (
            manifest["hard_budget_cap_including_parent_usd"]
        ),
    }
    write_json(output_dir / "budget.json", budget)
    print(
        canonical_json(
            {
                "stage": args.stage,
                "model_slug": args.model_slug,
                "calls": len(rows),
                "validation_passed": validation["passed"],
                "provider_errors": validation["provider_errors"],
                "malformed": validation["malformed"],
                "combined_cumulative_conservative_cost_usd": budget[
                    "combined_cumulative_conservative_cost_usd"
                ],
            }
        )
    )
    if not validation["passed"]:
        raise SystemExit(1)


def _pct(value: float) -> str:
    return f"{value:.1%}"


def analyze() -> None:
    all_cases = parent_cases()
    combined_by_slug: dict[str, list[dict[str, Any]]] = {}
    combined_by_slug["claude-sonnet-5"] = load_jsonl(
        PARENT / "models/claude-sonnet-5/raw/proposals.jsonl"
    )
    combined_by_slug["llama-4-maverick"] = load_jsonl(
        PARENT / "models/llama-4-maverick/raw/proposals.jsonl"
    )
    nemotron_parent = {
        row["episode_id"]: row for row in load_jsonl(PARENT_NEMOTRON_RAW)
    }
    nemotron_recovery = load_jsonl(
        PACKAGE
        / "models/nemotron-3-super-120b/raw/proposals.jsonl"
    )
    frozen_nemotron_ids = {
        f"{case['task_id']}::{case['condition']}"
        for case in recovery_cases("nemotron-3-super-120b")
    }
    if {row["episode_id"] for row in nemotron_recovery} != frozen_nemotron_ids:
        raise RuntimeError("Nemotron recovery rows differ from selection")
    for row in nemotron_recovery:
        nemotron_parent[row["episode_id"]] = row
    combined_by_slug["nemotron-3-super-120b"] = [
        nemotron_parent[episode_id]
        for episode_id in sorted(nemotron_parent)
    ]
    combined_by_slug["gpt-5.4"] = load_jsonl(
        PACKAGE / "models/gpt-5.4/raw/proposals.jsonl"
    )

    validations = {
        slug: validate_rows(rows, all_cases)
        for slug, rows in combined_by_slug.items()
    }
    if not all(validation["passed"] for validation in validations.values()):
        raise RuntimeError(
            "combined technical-completion validation failed: "
            + canonical_json(validations)
        )
    proposal_rows = [
        row
        for slug in MODEL_CONFIGS
        for row in combined_by_slug[slug]
    ]
    result = analyze_rows(
        proposal_rows=proposal_rows,
        model_slug_by_id=MODEL_ID_TO_SLUG,
    )
    layout_rows = result.pop("layout_rows_data")
    result["combined_model_validations"] = validations
    result["status"] = "technical_completion_sensitivity_complete"
    result["parent_primary_gate"] = (
        "failed_and_incomplete_due_provider_outage"
    )
    result["recovery_rows"] = {
        "gpt-5.4": FORMAL_CASES_PER_MODEL,
        "nemotron-3-super-120b": len(nemotron_recovery),
    }
    analysis_dir = PACKAGE / "analysis"
    write_jsonl(analysis_dir / "combined_layout_rows.jsonl", layout_rows)
    write_json(analysis_dir / "combined_results.json", result)

    lines = [
        "# Direct Execution Topology v0.1R Combined Results",
        "",
        (
            "**Status:** complete four-model technical-completion "
            "sensitivity"
        ),
        "",
        (
            "The immutable parent gate remains failed and its GPT block "
            "remains incomplete. This sensitivity uses a separately frozen "
            "complete GPT recollection and replaces exactly seven Nemotron "
            "provider-error rows."
        ),
        "",
        (
            f"Combined proposal rows: {result['proposal_rows']}; "
            f"deterministic layout rows: {result['layout_rows']}; "
            f"provider errors: {result['provider_errors']}; malformed: "
            f"{result['malformed']}; truncated: {result['truncated']}."
        ),
        "",
        "## Primary cross-model classifications",
        "",
        (
            "| Authority | Contrast | Large and significant models | "
            "Replicated in at least 3 models | Equivalent in all models |"
        ),
        "| --- | --- | ---: | --- | --- |",
    ]
    for row in result["classifications"]:
        lines.append(
            f"| {row['authority_regime']} | {row['contrast_id']} | "
            f"{row['large_significant_models']}/4 | "
            f"{'yes' if row['replicated_large_at_least_three_models'] else 'no'} | "
            f"{'yes' if row['practically_equivalent_all_models'] else 'no'} |"
        )
    lines.extend(
        [
            "",
            "## Paired task-bootstrap effects",
            "",
            (
                "| Model | Authority | Contrast | Effect | 95% CI | "
                "Practical equivalence |"
            ),
            "| --- | --- | --- | ---: | ---: | --- |",
        ]
    )
    for row in result["effects"]:
        lines.append(
            f"| {row['model_slug']} | {row['authority_regime']} | "
            f"{row['contrast_id']} | {_pct(row['estimate'])} | "
            f"[{_pct(row['ci_low'])}, {_pct(row['ci_high'])}] | "
            f"{'yes' if row['practically_equivalent'] else 'no'} |"
        )
    lines.extend(
        [
            "",
            "## Layout outcomes",
            "",
            (
                "| Model | Authority | G_E layout | Invalid advisory FAR | "
                "Invalid executed FAR | True protected utilization |"
            ),
            "| --- | --- | --- | ---: | ---: | ---: |",
        ]
    )
    for row in result["cells"]:
        lines.append(
            f"| {row['model_slug']} | {row['authority_regime']} | "
            f"{row['execution_layout']} | "
            f"{_pct(row['invalid_proof_advisory_far'])} | "
            f"{_pct(row['invalid_proof_executed_far'])} | "
            f"{_pct(row['true_protected_utilization'])} |"
        )
    lines.extend(
        [
            "",
            "## Evidence boundary",
            "",
            result["evidence_boundary"],
            "",
            (
                "The recovery does not retroactively make the immutable "
                "parent technical gate pass."
            ),
            "",
        ]
    )
    (analysis_dir / "combined_results.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    budget = {
        "recovery_experiment_id": RECOVERY_EXPERIMENT_ID,
        "formal_combined_estimated_cost_usd": result[
            "estimated_total_cost_usd"
        ],
        "formal_combined_conservative_cost_usd": result[
            "conservative_total_cost_usd"
        ],
        "all_attempts_conservative_cost_usd": spent_conservative_usd(),
        "hard_budget_cap_usd": HARD_BUDGET_CAP_USD,
        "per_model_combined": result["costs"],
    }
    write_json(analysis_dir / "budget_summary.json", budget)
    summary = {
        "recovery_experiment_id": RECOVERY_EXPERIMENT_ID,
        "status": "technical_completion_sensitivity_complete",
        "parent_primary_gate": (
            "failed_and_incomplete_due_provider_outage"
        ),
        "combined_proposal_rows": result["proposal_rows"],
        "combined_layout_rows": result["layout_rows"],
        "combined_technical_gate_passed": True,
        "combined_results_sha256": sha256_file(
            analysis_dir / "combined_results.json"
        ),
        "combined_layout_rows_sha256": sha256_file(
            analysis_dir / "combined_layout_rows.jsonl"
        ),
    }
    write_json(analysis_dir / "summary.json", summary)
    print(canonical_json(summary))


def main() -> None:
    args = parse_args()
    if args.mode == "build":
        build()
    elif args.mode == "freeze":
        freeze(args)
    elif args.mode == "run":
        run(args)
    else:
        analyze()


if __name__ == "__main__":
    main()
