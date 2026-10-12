#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from swarmsafe_delta.authority_composition import MODEL_CONFIGS
from swarmsafe_delta.authority_placement import AuthorityBedrockTextModel
from swarmsafe_delta.execution_topology_confirmatory import (
    FORMAL_CASES_PER_MODEL,
    HARD_BUDGET_CAP_USD,
    MAX_ATTEMPTS,
    MAX_OUTPUT_TOKENS,
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
R1 = (
    ROOT
    / "experiments/"
    "TopoSafe-Delta-ExecutionTopologyConfirmatory-v0.1R-TechnicalCompletion"
)
PACKAGE = (
    ROOT
    / "experiments/"
    "TopoSafe-Delta-ExecutionTopologyConfirmatory-v0.1R2-GPTTechnicalCompletion"
)
EXPERIMENT_ID = (
    "TopoSafe-Delta-ExecutionTopologyConfirmatory-v0.1R2-GPTTechnicalCompletion"
)
DESIGN = PACKAGE / "design_spec.json"
PROTOCOL = PACKAGE / "protocol.md"
MANIFEST = PACKAGE / "manifest.json"
PARENT_TASKS = PARENT / "candidate_tasks.json"
PARENT_CASES = PARENT / "proposal_cases.json"
R1_GPT_SMOKE = R1 / "smoke/gpt-5.4/raw/proposals.jsonl"
R1_NEMOTRON_RECOVERY = (
    R1 / "models/nemotron-3-super-120b/raw/proposals.jsonl"
)
GPT_SLUG = "gpt-5.4"
READ_TIMEOUT_SECONDS = 600
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
    parser.add_argument("--workers", type=int, default=10)
    parser.add_argument("--seed", type=int, default=2026101242)
    parser.add_argument(
        "--budget-cap-usd",
        type=float,
        default=HARD_BUDGET_CAP_USD,
    )
    return parser.parse_args()


def parent_cases() -> list[dict[str, Any]]:
    return json.loads(PARENT_CASES.read_text(encoding="utf-8"))


def longest_smoke_ids(cases: list[dict[str, Any]]) -> list[str]:
    selected = []
    for truth in ("false_update", "true_update"):
        candidates = [
            case for case in cases if case["claim_truth"] == truth
        ]
        case = max(
            candidates,
            key=lambda row: len(
                (
                    row["executor_system"] + row["executor_user"]
                ).encode("utf-8")
            ),
        )
        selected.append(f"{case['task_id']}::{case['condition']}")
    return sorted(selected)


def build() -> None:
    if MANIFEST.exists():
        raise RuntimeError("R2 is already frozen")
    prior_smoke = load_jsonl(R1_GPT_SMOKE)
    errors = []
    if len(prior_smoke) != 2:
        errors.append(f"expected 2 R1 GPT smoke rows, found {len(prior_smoke)}")
    if sum(bool(row.get("provider_error")) for row in prior_smoke) != 2:
        errors.append("R1 GPT smoke is not a two-timeout failure")
    if (R1 / "models/gpt-5.4/raw/proposals.jsonl").exists():
        errors.append("R1 unexpectedly contains formal GPT rows")
    cases = parent_cases()
    selection = {
        "r2_experiment_id": EXPERIMENT_ID,
        "selection_basis": "complete_gpt_block_after_failed_technical_smoke",
        "behavioral_outcome_used_for_selection": False,
        "selected_episode_ids": [
            f"{case['task_id']}::{case['condition']}" for case in cases
        ],
    }
    write_json(PACKAGE / "recovery_selection.json", selection)
    validation = {
        "status": (
            "automatic_r2_gate_passed"
            if not errors
            else "automatic_r2_gate_failed"
        ),
        "passed": not errors,
        "selected_formal_calls": len(cases),
        "r1_failed_smoke_rows": len(prior_smoke),
        "r1_failed_smoke_provider_errors": sum(
            bool(row.get("provider_error")) for row in prior_smoke
        ),
        "errors": errors,
    }
    write_json(PACKAGE / "selection_validation.json", validation)
    summary = {
        "r2_experiment_id": EXPERIMENT_ID,
        "status": validation["status"],
        "formal_calls": len(cases),
        "excluded_smoke_calls": 2,
        "read_timeout_seconds": READ_TIMEOUT_SECONDS,
        "projected_conservative_cost_usd": projected_allowance_usd(
            GPT_SLUG, len(cases)
        ),
        "hard_budget_cap_including_parent_and_recoveries_usd": (
            HARD_BUDGET_CAP_USD
        ),
    }
    write_json(PACKAGE / "package_summary.json", summary)
    print(canonical_json(summary))
    if errors:
        raise SystemExit(1)


def validate_design() -> None:
    design = json.loads(DESIGN.read_text(encoding="utf-8"))
    errors = []
    if design.get("status") != (
        "pre_run_gpt_timeout_amendment_unfrozen"
    ):
        errors.append("R2 design status is incorrect")
    if design.get("provider_calls_completed") != 0:
        errors.append("R2 design reports completed calls")
    if design.get("formal_calls") != FORMAL_CASES_PER_MODEL:
        errors.append("R2 formal-call count differs from code")
    amendment = design.get("technical_amendment", {})
    if amendment.get("read_timeout_seconds_r2") != READ_TIMEOUT_SECONDS:
        errors.append("R2 timeout differs from code")
    if errors:
        raise RuntimeError("R2 design invalid: " + " | ".join(errors))


def freeze(args: argparse.Namespace) -> None:
    if MANIFEST.exists():
        raise RuntimeError("R2 manifest already exists")
    required = [
        DESIGN,
        PROTOCOL,
        PACKAGE / "recovery_selection.json",
        PACKAGE / "selection_validation.json",
        PACKAGE / "package_summary.json",
        PARENT / "manifest.json",
        PARENT_TASKS,
        PARENT_CASES,
        PARENT / "models/claude-sonnet-5/raw/proposals.jsonl",
        PARENT / "models/claude-sonnet-5/validation.json",
        PARENT / "models/llama-4-maverick/raw/proposals.jsonl",
        PARENT / "models/llama-4-maverick/validation.json",
        PARENT / "models/nemotron-3-super-120b/raw/proposals.jsonl",
        PARENT / "models/nemotron-3-super-120b/validation.json",
        PARENT
        / "aborted_provider_outage/gpt-5.4/raw/proposals.jsonl",
        R1 / "manifest.json",
        R1_GPT_SMOKE,
        R1 / "smoke/gpt-5.4/validation.json",
        R1_NEMOTRON_RECOVERY,
        R1 / "models/nemotron-3-super-120b/validation.json",
        ROOT / "src/swarmsafe_delta/execution_topology_confirmatory.py",
        ROOT / "src/swarmsafe_delta/execution_topology_pilot.py",
        ROOT / "scripts/run_execution_topology_confirmatory_recovery.py",
        Path(__file__),
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise RuntimeError(f"missing R2 freeze inputs: {missing}")
    validate_design()
    validation = json.loads(
        (PACKAGE / "selection_validation.json").read_text(
            encoding="utf-8"
        )
    )
    if not validation["passed"]:
        raise RuntimeError("R2 selection gate failed")
    cases = parent_cases()
    manifest = {
        "r2_experiment_id": EXPERIMENT_ID,
        "status": "frozen_pre_run",
        "frozen_at": utc_now(),
        "formal_calls": len(cases),
        "smoke_episode_ids": longest_smoke_ids(cases),
        "workers": args.workers,
        "schedule_seed": args.seed,
        "read_timeout_seconds": READ_TIMEOUT_SECONDS,
        "max_output_tokens": MAX_OUTPUT_TOKENS,
        "maximum_provider_attempts": MAX_ATTEMPTS,
        "hard_budget_cap_including_parent_and_recoveries_usd": (
            args.budget_cap_usd
        ),
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
        raise RuntimeError("R2 manifest is not frozen_pre_run")
    mismatches = []
    for relative, expected in manifest["source_hashes"].items():
        path = ROOT / relative
        if not path.exists():
            mismatches.append(f"{relative}: missing")
        elif sha256_file(path) != expected:
            mismatches.append(f"{relative}: hash mismatch")
    if mismatches:
        raise RuntimeError("R2 frozen mismatch: " + " | ".join(mismatches))
    runtime = {
        "workers": args.workers,
        "schedule_seed": args.seed,
        "hard_budget_cap_including_parent_and_recoveries_usd": (
            args.budget_cap_usd
        ),
    }
    changed = [
        key
        for key, value in runtime.items()
        if manifest.get(key) != value
    ]
    if changed:
        raise ValueError(
            "R2 runtime arguments differ from freeze: "
            + ", ".join(changed)
        )


def accounted_rows() -> list[tuple[str, dict[str, Any]]]:
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
    rows.extend(
        (
            "gpt-5.4",
            row,
        )
        for row in load_jsonl(
            PARENT
            / "aborted_provider_outage/gpt-5.4/raw/proposals.jsonl"
        )
    )
    for path in R1.glob("smoke/*/raw/proposals.jsonl"):
        rows.extend((path.parts[-3], row) for row in load_jsonl(path))
    rows.extend(
        ("nemotron-3-super-120b", row)
        for row in load_jsonl(R1_NEMOTRON_RECOVERY)
    )
    for path in PACKAGE.glob("smoke/*/raw/proposals.jsonl"):
        rows.extend((GPT_SLUG, row) for row in load_jsonl(path))
    for path in PACKAGE.glob("models/*/raw/proposals.jsonl"):
        rows.extend((GPT_SLUG, row) for row in load_jsonl(path))
    return rows


def spent_conservative_usd() -> float:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for slug, row in accounted_rows():
        grouped.setdefault(slug, []).append(row)
    return sum(
        estimate_rows_cost(rows, slug, conservative=True)
        for slug, rows in grouped.items()
    )


def validate_gpt_rows(
    rows: list[dict[str, Any]],
    cases: list[dict[str, Any]],
) -> dict[str, Any]:
    validation = validate_rows(rows, cases)
    validation["r2_experiment_id"] = EXPERIMENT_ID
    return validation


def require_smoke_pass() -> None:
    path = PACKAGE / "smoke/gpt-5.4/validation.json"
    if not path.exists():
        raise RuntimeError("R2 GPT smoke validation is missing")
    if not json.loads(path.read_text(encoding="utf-8"))["passed"]:
        raise RuntimeError("R2 GPT smoke failed")


def run(args: argparse.Namespace) -> None:
    if not args.stage:
        raise ValueError("--stage is required for R2 run")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    verify_frozen(manifest, args)
    if args.stage == "formal":
        require_smoke_pass()
    tasks = load_tasks(PARENT_TASKS)
    cases = parent_cases()
    if args.stage == "smoke":
        ids = set(manifest["smoke_episode_ids"])
        cases = [
            case
            for case in cases
            if f"{case['task_id']}::{case['condition']}" in ids
        ]
        stage_dir = "smoke"
    else:
        stage_dir = "models"
    output_dir = PACKAGE / stage_dir / GPT_SLUG
    raw_path = output_dir / "raw/proposals.jsonl"

    def before_batch(batch_calls: int) -> None:
        spent = spent_conservative_usd()
        prospective = projected_allowance_usd(
            GPT_SLUG, batch_calls
        )
        cap = manifest[
            "hard_budget_cap_including_parent_and_recoveries_usd"
        ]
        if spent + prospective > cap:
            raise RuntimeError(
                "R2 combined hard budget cap would be exceeded: "
                f"spent={spent:.6f}, prospective={prospective:.6f}, "
                f"cap={cap:.2f}"
            )

    config = MODEL_CONFIGS[GPT_SLUG]
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
        read_timeout_seconds=manifest["read_timeout_seconds"],
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
    validation = validate_gpt_rows(rows, cases)
    write_json(output_dir / "validation.json", validation)
    budget = {
        "r2_experiment_id": EXPERIMENT_ID,
        "stage": args.stage,
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
            rows, GPT_SLUG, conservative=False
        ),
        "conservative_cost_usd": estimate_rows_cost(
            rows, GPT_SLUG, conservative=True
        ),
        "combined_cumulative_conservative_cost_usd": (
            spent_conservative_usd()
        ),
        "hard_budget_cap_usd": manifest[
            "hard_budget_cap_including_parent_and_recoveries_usd"
        ],
    }
    write_json(output_dir / "budget.json", budget)
    print(
        canonical_json(
            {
                "stage": args.stage,
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
    combined: dict[str, list[dict[str, Any]]] = {
        "gpt-5.4": load_jsonl(
            PACKAGE / "models/gpt-5.4/raw/proposals.jsonl"
        ),
        "claude-sonnet-5": load_jsonl(
            PARENT / "models/claude-sonnet-5/raw/proposals.jsonl"
        ),
        "llama-4-maverick": load_jsonl(
            PARENT / "models/llama-4-maverick/raw/proposals.jsonl"
        ),
    }
    nemotron = {
        row["episode_id"]: row
        for row in load_jsonl(
            PARENT / "models/nemotron-3-super-120b/raw/proposals.jsonl"
        )
    }
    for row in load_jsonl(R1_NEMOTRON_RECOVERY):
        nemotron[row["episode_id"]] = row
    combined["nemotron-3-super-120b"] = [
        nemotron[episode_id] for episode_id in sorted(nemotron)
    ]
    validations = {
        slug: validate_rows(rows, all_cases)
        for slug, rows in combined.items()
    }
    if not all(row["passed"] for row in validations.values()):
        raise RuntimeError(
            "R2 combined validation failed: "
            + canonical_json(validations)
        )
    proposal_rows = [
        row for slug in MODEL_CONFIGS for row in combined[slug]
    ]
    result = analyze_rows(
        proposal_rows=proposal_rows,
        model_slug_by_id=MODEL_ID_TO_SLUG,
    )
    layout_rows = result.pop("layout_rows_data")
    result["status"] = "r2_technical_completion_sensitivity_complete"
    result["parent_primary_gate"] = (
        "failed_and_incomplete_due_provider_outage"
    )
    result["combined_model_validations"] = validations
    result["technical_completion_sources"] = {
        "gpt-5.4": "complete R2 block",
        "claude-sonnet-5": "immutable parent",
        "llama-4-maverick": "immutable parent",
        "nemotron-3-super-120b": (
            "immutable parent plus seven exact R1 technical replacements"
        ),
    }
    analysis_dir = PACKAGE / "analysis"
    write_jsonl(analysis_dir / "combined_layout_rows.jsonl", layout_rows)
    write_json(analysis_dir / "combined_results.json", result)

    lines = [
        "# Direct Execution Topology v0.1R2 Combined Results",
        "",
        (
            "**Status:** complete four-model technical-completion "
            "sensitivity"
        ),
        "",
        (
            "The original parent technical gate remains failed and its GPT "
            "block remains incomplete. This sensitivity uses a complete "
            "separately frozen GPT block with a client-timeout amendment and "
            "the seven exact Nemotron R1 technical replacements."
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
                "The technical completion does not retroactively make the "
                "immutable parent gate pass."
            ),
            "",
        ]
    )
    (analysis_dir / "combined_results.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    budget = {
        "r2_experiment_id": EXPERIMENT_ID,
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
        "r2_experiment_id": EXPERIMENT_ID,
        "status": "r2_technical_completion_sensitivity_complete",
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
