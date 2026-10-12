#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from swarmsafe_delta.authority_composition import MODEL_CONFIGS
from swarmsafe_delta.authority_placement import AuthorityBedrockTextModel
from swarmsafe_delta.execution_topology_confirmatory import (
    AUTHORITY_REGIMES,
    BOOTSTRAP_DRAWS,
    CLAIM_TRUTHS,
    EXECUTION_LAYOUTS,
    EXPERIMENT_ID,
    FORMAL_CALLS,
    FORMAL_CASES_PER_MODEL,
    HARD_BUDGET_CAP_USD,
    MAX_ATTEMPTS,
    MAX_OUTPUT_TOKENS,
    MODEL_PRICES,
    PER_CALL_TOKEN_ALLOWANCE,
    PRIMARY_CONTRASTS,
    PROPOSAL_ROLES,
    RESULT_STATUS,
    analyze_rows,
    build_fresh_tasks,
    build_proposal_cases,
    projected_allowance_usd,
    run_model_jobs,
    select_cases_by_episode_ids,
    smoke_episode_ids,
    validate_package,
    validate_rows,
)
from swarmsafe_delta.pilot import (
    canonical_json,
    load_tasks,
    sha256_file,
    utc_now,
)
from swarmsafe_delta.topology_pilot import load_jsonl, sha256_text


ROOT = Path(__file__).resolve().parent.parent
PACKAGE = (
    ROOT
    / "experiments/TopoSafe-Delta-ExecutionTopologyConfirmatory-v0.1"
)
CATALOG = ROOT / "data/toposafe_execution_topology_catalog_v0.1.json"
DESIGN = PACKAGE / "design_spec.json"
PROTOCOL = PACKAGE / "protocol.md"
MANIFEST = PACKAGE / "manifest.json"
MODULE = ROOT / "src/swarmsafe_delta/execution_topology_confirmatory.py"
PRIOR_TASK_SOURCES = (
    ROOT
    / "experiments/TopoSafe-Delta-AuthorityComposition-v0.2/"
    "candidate_tasks.json",
    ROOT
    / "experiments/TopoSafe-Delta-RuntimeEnforcement-v0.2/"
    "candidate_tasks.json",
    ROOT / "data/authority_placement_tasks_v1.json",
)
TRANSITIVE_SOURCES = (
    ROOT / "src/swarmsafe_delta/authority_composition.py",
    ROOT / "src/swarmsafe_delta/authority_placement.py",
    ROOT / "src/swarmsafe_delta/authority_task_construction.py",
    ROOT / "src/swarmsafe_delta/execution_topology_pilot.py",
)
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
    parser.add_argument("--model-slug", choices=tuple(MODEL_CONFIGS))
    parser.add_argument("--workers", type=int, default=10)
    parser.add_argument("--seed", type=int, default=2026101242)
    parser.add_argument(
        "--budget-cap-usd",
        type=float,
        default=HARD_BUDGET_CAP_USD,
    )
    return parser.parse_args()


def load_catalog() -> list[dict[str, str]]:
    value = json.loads(CATALOG.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError("execution-topology catalog must be a JSON list")
    return [dict(row) for row in value]


def prior_task_ids() -> set[str]:
    ids: set[str] = set()
    for path in PRIOR_TASK_SOURCES:
        if path.exists():
            ids.update(task["id"] for task in load_tasks(path))
    return ids


def build() -> None:
    if MANIFEST.exists():
        raise RuntimeError("package is already frozen; build is immutable")
    catalog = load_catalog()
    tasks = build_fresh_tasks(catalog)
    cases = build_proposal_cases(tasks)
    validation = validate_package(
        catalog=catalog,
        tasks=tasks,
        cases=cases,
        excluded_task_ids=prior_task_ids(),
    )
    write_json(PACKAGE / "candidate_tasks.json", tasks)
    write_json(PACKAGE / "proposal_cases.json", cases)
    write_json(PACKAGE / "task_validation.json", validation)
    projected = {
        slug: {
            "formal_calls": len(cases),
            "per_call_token_allowance": PER_CALL_TOKEN_ALLOWANCE[slug],
            "projected_conservative_cost_usd": projected_allowance_usd(
                slug, len(cases)
            ),
        }
        for slug in MODEL_CONFIGS
    }
    summary = {
        "experiment_id": EXPERIMENT_ID,
        "status": validation["status"],
        "fresh_tasks": len(tasks),
        "proposal_cases_per_model": len(cases),
        "formal_calls": FORMAL_CALLS,
        "excluded_smoke_calls": (
            len(MODEL_CONFIGS) * 2
        ),
        "maximum_provider_attempts": MAX_ATTEMPTS,
        "max_output_tokens": MAX_OUTPUT_TOKENS,
        "hard_budget_cap_usd": HARD_BUDGET_CAP_USD,
        "projected_model_costs": projected,
        "projected_conservative_total_usd": sum(
            row["projected_conservative_cost_usd"]
            for row in projected.values()
        ),
        "candidate_tasks_sha256": sha256_text(canonical_json(tasks)),
        "proposal_cases_sha256": sha256_text(canonical_json(cases)),
    }
    write_json(PACKAGE / "package_summary.json", summary)
    print(canonical_json(summary))
    if not validation["automatic_gate_passed"]:
        raise SystemExit(1)


def validate_design() -> None:
    spec = json.loads(DESIGN.read_text(encoding="utf-8"))
    errors = []
    if spec.get("status") != "pre_run_design_unfrozen":
        errors.append("design status is not pre_run_design_unfrozen")
    if spec.get("provider_calls_completed") != 0:
        errors.append("design reports completed provider calls")
    proposal = spec.get("proposal_collection", {})
    if proposal.get("formal_calls_total") != FORMAL_CALLS:
        errors.append("design formal-call total differs from code")
    if proposal.get("formal_calls_per_model") != FORMAL_CASES_PER_MODEL:
        errors.append("design per-model total differs from code")
    if spec.get("execution_layouts") != list(EXECUTION_LAYOUTS):
        errors.append("design execution layouts differ from code")
    if errors:
        raise RuntimeError("design validation failed: " + " | ".join(errors))


def freeze(args: argparse.Namespace) -> None:
    if MANIFEST.exists():
        raise RuntimeError("manifest already exists")
    required = [
        DESIGN,
        PROTOCOL,
        CATALOG,
        PACKAGE / "candidate_tasks.json",
        PACKAGE / "proposal_cases.json",
        PACKAGE / "task_validation.json",
        PACKAGE / "package_summary.json",
        MODULE,
        Path(__file__),
        *PRIOR_TASK_SOURCES,
        *TRANSITIVE_SOURCES,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise RuntimeError(f"missing freeze inputs: {missing}")
    validate_design()
    validation = json.loads(
        (PACKAGE / "task_validation.json").read_text(encoding="utf-8")
    )
    if not validation["automatic_gate_passed"]:
        raise RuntimeError("automatic task/package gate did not pass")
    cases = json.loads(
        (PACKAGE / "proposal_cases.json").read_text(encoding="utf-8")
    )
    source_hashes = {
        str(path.relative_to(ROOT)): sha256_file(path) for path in required
    }
    manifest = {
        "experiment_id": EXPERIMENT_ID,
        "status": "frozen_pre_run",
        "frozen_at": utc_now(),
        "fresh_tasks": validation["fresh_tasks"],
        "formal_calls": FORMAL_CALLS,
        "formal_cases_per_model": len(cases),
        "smoke_episode_ids": smoke_episode_ids(cases),
        "active_models": list(MODEL_CONFIGS),
        "workers": args.workers,
        "schedule_seed": args.seed,
        "max_output_tokens": MAX_OUTPUT_TOKENS,
        "maximum_provider_attempts": MAX_ATTEMPTS,
        "hard_budget_cap_usd": args.budget_cap_usd,
        "pricing_snapshot_date": "2026-10-12",
        "model_prices": MODEL_PRICES,
        "per_call_token_allowance": PER_CALL_TOKEN_ALLOWANCE,
        "bootstrap_draws": BOOTSTRAP_DRAWS,
        "authority_regimes": list(AUTHORITY_REGIMES),
        "claim_truths": list(CLAIM_TRUTHS),
        "proposal_roles": list(PROPOSAL_ROLES),
        "execution_layouts": {
            layout_id: {
                key: list(value)
                for key, value in layout.items()
            }
            for layout_id, layout in EXECUTION_LAYOUTS.items()
        },
        "primary_contrasts": list(PRIMARY_CONTRASTS),
        "source_hashes": source_hashes,
    }
    write_json(MANIFEST, manifest)
    print(canonical_json(manifest))


def verify_frozen(
    manifest: dict[str, Any],
    args: argparse.Namespace,
) -> None:
    if manifest.get("status") != "frozen_pre_run":
        raise RuntimeError("manifest is not frozen_pre_run")
    mismatches = []
    for relative, expected in manifest["source_hashes"].items():
        path = ROOT / relative
        if not path.exists():
            mismatches.append(f"{relative}: missing")
        elif sha256_file(path) != expected:
            mismatches.append(f"{relative}: hash mismatch")
    if mismatches:
        raise RuntimeError("frozen source mismatch: " + " | ".join(mismatches))
    runtime_values = {
        "workers": args.workers,
        "schedule_seed": args.seed,
        "hard_budget_cap_usd": args.budget_cap_usd,
    }
    changed = [
        key
        for key, value in runtime_values.items()
        if manifest.get(key) != value
    ]
    if changed:
        raise ValueError(
            "runtime arguments differ from freeze: " + ", ".join(changed)
        )


def all_existing_rows() -> list[tuple[str, dict[str, Any]]]:
    rows: list[tuple[str, dict[str, Any]]] = []
    for path in sorted(PACKAGE.glob("smoke/*/raw/proposals.jsonl")):
        slug = path.parts[-3]
        rows.extend((slug, row) for row in load_jsonl(path))
    for path in sorted(PACKAGE.glob("models/*/raw/proposals.jsonl")):
        slug = path.parts[-3]
        rows.extend((slug, row) for row in load_jsonl(path))
    return rows


def spent_conservative_usd() -> float:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for slug, row in all_existing_rows():
        grouped.setdefault(slug, []).append(row)
    total = 0.0
    from swarmsafe_delta.execution_topology_pilot import estimate_rows_cost

    for slug, rows in grouped.items():
        total += estimate_rows_cost(rows, slug, conservative=True)
    return total


def require_smoke_pass(model_slug: str) -> None:
    path = PACKAGE / f"smoke/{model_slug}/validation.json"
    if not path.exists():
        raise RuntimeError(f"smoke validation missing for {model_slug}")
    validation = json.loads(path.read_text(encoding="utf-8"))
    if not validation.get("passed"):
        raise RuntimeError(f"smoke validation failed for {model_slug}")


def run(args: argparse.Namespace) -> None:
    if not args.stage or not args.model_slug:
        raise ValueError("--stage and --model-slug are required for run")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    verify_frozen(manifest, args)
    if args.stage == "formal":
        require_smoke_pass(args.model_slug)
    tasks = load_tasks(PACKAGE / "candidate_tasks.json")
    cases = json.loads(
        (PACKAGE / "proposal_cases.json").read_text(encoding="utf-8")
    )
    if args.stage == "smoke":
        cases = select_cases_by_episode_ids(
            cases, manifest["smoke_episode_ids"]
        )
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
        if spent + prospective > manifest["hard_budget_cap_usd"]:
            raise RuntimeError(
                "hard budget cap would be exceeded before next batch: "
                f"spent={spent:.6f}, prospective={prospective:.6f}, "
                f"cap={manifest['hard_budget_cap_usd']:.2f}"
            )

    model_config = MODEL_CONFIGS[args.model_slug]
    model = AuthorityBedrockTextModel(
        model_id=model_config["model_id"],
        region=model_config["region"],
        temperature=model_config["temperature"],
        top_p=model_config["top_p"],
        additional_model_request_fields=model_config[
            "additional_model_request_fields"
        ],
        force_action_tool=model_config["force_action_tool"],
        action_tool_mode=model_config.get("action_tool_mode"),
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
    )
    validation = validate_rows(rows, cases)
    write_json(output_dir / "validation.json", validation)
    from swarmsafe_delta.execution_topology_pilot import estimate_rows_cost

    budget = {
        "experiment_id": EXPERIMENT_ID,
        "stage": args.stage,
        "model_slug": args.model_slug,
        "proposal_calls": len(rows),
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
        "cumulative_conservative_cost_usd": spent_conservative_usd(),
        "hard_budget_cap_usd": manifest["hard_budget_cap_usd"],
    }
    write_json(output_dir / "budget.json", budget)
    print(
        canonical_json(
            {
                "stage": args.stage,
                "model_slug": args.model_slug,
                "proposal_calls": len(rows),
                "validation_passed": validation["passed"],
                "provider_errors": validation["provider_errors"],
                "malformed": validation["malformed"],
                "estimated_cost_usd": budget["estimated_cost_usd"],
                "cumulative_conservative_cost_usd": budget[
                    "cumulative_conservative_cost_usd"
                ],
            }
        )
    )
    if not validation["passed"]:
        raise SystemExit(1)


def _pct(value: float) -> str:
    return f"{value:.1%}"


def analyze() -> None:
    proposal_rows: list[dict[str, Any]] = []
    validations = {}
    for slug in MODEL_CONFIGS:
        raw_path = PACKAGE / f"models/{slug}/raw/proposals.jsonl"
        validation_path = PACKAGE / f"models/{slug}/validation.json"
        if not raw_path.exists() or not validation_path.exists():
            raise RuntimeError(f"formal model output missing: {slug}")
        rows = load_jsonl(raw_path)
        validation = json.loads(
            validation_path.read_text(encoding="utf-8")
        )
        proposal_rows.extend(rows)
        validations[slug] = validation
    if not all(item["passed"] for item in validations.values()):
        raise RuntimeError(
            "immutable parent technical gate failed; analyze a separately "
            "frozen recovery sensitivity instead"
        )
    result = analyze_rows(
        proposal_rows=proposal_rows,
        model_slug_by_id=MODEL_ID_TO_SLUG,
    )
    layout_rows = result.pop("layout_rows_data")
    result["model_validations"] = validations
    analysis_dir = PACKAGE / "analysis"
    write_jsonl(analysis_dir / "layout_rows.jsonl", layout_rows)
    write_json(analysis_dir / "results.json", result)

    lines = [
        "# TopoSafe-Delta Direct Execution Topology v0.1 Results",
        "",
        "**Status:** complete frozen 60-task synthetic direct G_E study",
        "",
        (
            f"Formal proposal calls: {result['proposal_rows']}; deterministic "
            f"layout rows: {result['layout_rows']}; provider errors: "
            f"{result['provider_errors']}; malformed: {result['malformed']}; "
            f"truncated: {result['truncated']}."
        ),
        "",
        (
            "Estimated formal provider cost: "
            f"${result['estimated_total_cost_usd']:.4f}; conservative "
            f"accounting: ${result['conservative_total_cost_usd']:.4f}."
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
        ]
    )
    (analysis_dir / "results.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    budget = {
        "experiment_id": EXPERIMENT_ID,
        "formal_proposal_calls": result["proposal_rows"],
        "formal_estimated_cost_usd": result["estimated_total_cost_usd"],
        "formal_conservative_cost_usd": result[
            "conservative_total_cost_usd"
        ],
        "including_smoke_conservative_cost_usd": (
            spent_conservative_usd()
        ),
        "hard_budget_cap_usd": HARD_BUDGET_CAP_USD,
        "per_model": result["costs"],
    }
    write_json(analysis_dir / "budget_summary.json", budget)
    summary = {
        "experiment_id": EXPERIMENT_ID,
        "status": "analysis_complete",
        "formal_proposal_rows": result["proposal_rows"],
        "deterministic_layout_rows": result["layout_rows"],
        "technical_gate_passed": True,
        "result_status": RESULT_STATUS,
        "results_sha256": sha256_file(analysis_dir / "results.json"),
        "layout_rows_sha256": sha256_file(
            analysis_dir / "layout_rows.jsonl"
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
