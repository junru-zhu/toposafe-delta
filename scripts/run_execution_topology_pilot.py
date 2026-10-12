#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from swarmsafe_delta.authority_composition import MODEL_CONFIGS
from swarmsafe_delta.authority_placement import AuthorityBedrockTextModel
from swarmsafe_delta.execution_topology_pilot import (
    EXPERIMENT_ID,
    FORMAL_CALLS,
    HARD_BUDGET_CAP_USD,
    MAX_ATTEMPTS,
    MAX_OUTPUT_TOKENS,
    MODEL_PRICES,
    RESULT_STATUS,
    analyze_rows,
    build_cases,
    estimate_case_ceiling_cost,
    estimate_rows_cost,
    run_model_jobs,
    select_cases_by_episode_ids,
    select_pilot_tasks,
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
from swarmsafe_delta.topology_pilot import sha256_text


ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "experiments/TopoSafe-Delta-ExecutionTopologyPilot-v0.1"
SOURCE_TASKS = (
    ROOT
    / "experiments/TopoSafe-Delta-RuntimeEnforcement-v0.2/candidate_tasks.json"
)
MODULE = ROOT / "src/swarmsafe_delta/execution_topology_pilot.py"
DESIGN = PACKAGE / "design_spec.json"
PROTOCOL = PACKAGE / "protocol.md"
MANIFEST = PACKAGE / "manifest.json"
MODEL_ID_TO_SLUG = {
    config["model_id"]: slug for slug, config in MODEL_CONFIGS.items()
}


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=("build", "freeze", "run", "analyze"),
        required=True,
    )
    parser.add_argument("--stage", choices=("smoke", "formal"))
    parser.add_argument("--model-slug", choices=tuple(MODEL_CONFIGS))
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--seed", type=int, default=2026101211)
    parser.add_argument(
        "--budget-cap-usd",
        type=float,
        default=HARD_BUDGET_CAP_USD,
    )
    return parser.parse_args()


def build() -> None:
    source_tasks = load_tasks(SOURCE_TASKS)
    tasks = select_pilot_tasks(source_tasks)
    cases = build_cases(tasks)
    validation = validate_package(tasks, cases)
    PACKAGE.mkdir(parents=True, exist_ok=True)
    write_json(PACKAGE / "candidate_tasks.json", tasks)
    write_json(PACKAGE / "cases.json", cases)
    write_json(PACKAGE / "task_validation.json", validation)
    ceilings = {
        slug: estimate_case_ceiling_cost(
            cases,
            slug,
            max_output_tokens=MAX_OUTPUT_TOKENS,
        )
        for slug in MODEL_CONFIGS
    }
    summary = {
        "experiment_id": EXPERIMENT_ID,
        "status": (
            "automatic_gate_passed"
            if validation["automatic_gate_passed"]
            else "automatic_gate_failed"
        ),
        "development_only": True,
        "formal_tasks": len(tasks),
        "formal_cases_per_model": len(cases),
        "formal_calls": FORMAL_CALLS,
        "smoke_calls": 2 * len(MODEL_CONFIGS),
        "max_output_tokens": MAX_OUTPUT_TOKENS,
        "maximum_provider_attempts": MAX_ATTEMPTS,
        "hard_budget_cap_usd": HARD_BUDGET_CAP_USD,
        "conservative_formal_cost_ceiling_usd": sum(
            item["conservative_cost_ceiling_usd"]
            for item in ceilings.values()
        ),
        "model_cost_ceilings": ceilings,
        "candidate_tasks_sha256": sha256_text(canonical_json(tasks)),
        "cases_sha256": sha256_text(canonical_json(cases)),
    }
    write_json(PACKAGE / "package_summary.json", summary)
    print(canonical_json(summary))
    if not validation["automatic_gate_passed"]:
        raise SystemExit(1)


def freeze(args: argparse.Namespace) -> None:
    required = [
        DESIGN,
        PROTOCOL,
        PACKAGE / "candidate_tasks.json",
        PACKAGE / "cases.json",
        PACKAGE / "task_validation.json",
        PACKAGE / "package_summary.json",
        SOURCE_TASKS,
        MODULE,
        Path(__file__),
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise RuntimeError(f"missing freeze inputs: {missing}")
    validation = json.loads(
        (PACKAGE / "task_validation.json").read_text(encoding="utf-8")
    )
    if not validation["automatic_gate_passed"]:
        raise RuntimeError("automatic package gate did not pass")
    cases = json.loads((PACKAGE / "cases.json").read_text(encoding="utf-8"))
    source_hashes = {
        str(path.relative_to(ROOT)): sha256_file(path) for path in required
    }
    manifest = {
        "experiment_id": EXPERIMENT_ID,
        "status": "frozen_pre_run",
        "development_only": True,
        "frozen_at": utc_now(),
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
        "source_hashes": source_hashes,
    }
    write_json(MANIFEST, manifest)
    print(canonical_json(manifest))


def verify_frozen(manifest: dict[str, Any], args: argparse.Namespace) -> None:
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
    frozen_args = {
        "workers": args.workers,
        "schedule_seed": args.seed,
        "hard_budget_cap_usd": args.budget_cap_usd,
    }
    changed = [
        key
        for key, value in frozen_args.items()
        if manifest.get(key) != value
    ]
    if changed:
        raise ValueError("runtime arguments differ from freeze: " + ", ".join(changed))


def all_existing_rows() -> list[tuple[str, dict[str, Any]]]:
    rows = []
    for path in sorted(PACKAGE.glob("smoke/*/raw/episodes.jsonl")):
        slug = path.parts[-3]
        rows.extend((slug, row) for row in load_jsonl(path))
    for path in sorted(PACKAGE.glob("models/*/raw/episodes.jsonl")):
        slug = path.parts[-3]
        rows.extend((slug, row) for row in load_jsonl(path))
    return rows


def spent_conservative_usd() -> float:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for slug, row in all_existing_rows():
        grouped.setdefault(slug, []).append(row)
    return sum(
        estimate_rows_cost(rows, slug, conservative=True)
        for slug, rows in grouped.items()
    )


def run(args: argparse.Namespace) -> None:
    if not args.stage or not args.model_slug:
        raise ValueError("--stage and --model-slug are required for run")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    verify_frozen(manifest, args)
    tasks = load_tasks(PACKAGE / "candidate_tasks.json")
    cases = json.loads((PACKAGE / "cases.json").read_text(encoding="utf-8"))
    if args.stage == "smoke":
        cases = select_cases_by_episode_ids(
            cases,
            manifest["smoke_episode_ids"],
        )
        stage_dir = "smoke"
    else:
        stage_dir = "models"
    output_dir = PACKAGE / stage_dir / args.model_slug
    raw_path = output_dir / "raw/episodes.jsonl"
    existing_ids = {row["episode_id"] for row in load_jsonl(raw_path)}
    missing_cases = [
        case
        for case in cases
        if f"{case['task_id']}::{case['condition']}" not in existing_ids
    ]
    prospective = estimate_case_ceiling_cost(
        missing_cases,
        args.model_slug,
        max_output_tokens=manifest["max_output_tokens"],
    )
    spent = spent_conservative_usd()
    projected = spent + prospective["conservative_cost_ceiling_usd"]
    if projected > manifest["hard_budget_cap_usd"]:
        raise RuntimeError(
            "hard budget cap would be exceeded: "
            f"spent={spent:.6f}, prospective={prospective['conservative_cost_ceiling_usd']:.6f}, "
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
        read_timeout_seconds=180,
    )
    rows = run_model_jobs(
        tasks=tasks,
        cases=cases,
        model=model,
        workers=args.workers,
        seed=args.seed,
        max_output_tokens=manifest["max_output_tokens"],
        raw_path=raw_path,
    )
    validation = validate_rows(rows, cases)
    write_json(output_dir / "validation.json", validation)
    budget = {
        "experiment_id": EXPERIMENT_ID,
        "stage": args.stage,
        "model_slug": args.model_slug,
        "episodes": len(rows),
        "input_tokens": sum(row.get("input_tokens", 0) for row in rows),
        "output_tokens": sum(row.get("output_tokens", 0) for row in rows),
        "estimated_cost_usd": estimate_rows_cost(
            rows,
            args.model_slug,
            conservative=False,
        ),
        "conservative_cost_usd": estimate_rows_cost(
            rows,
            args.model_slug,
            conservative=True,
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
                "episodes": len(rows),
                "validation_passed": validation["passed"],
                "provider_errors": validation["provider_errors"],
                "estimated_cost_usd": budget["estimated_cost_usd"],
                "cumulative_conservative_cost_usd": budget[
                    "cumulative_conservative_cost_usd"
                ],
            }
        )
    )
    if not validation["passed"]:
        raise SystemExit(1)


def analyze() -> None:
    rows = []
    validations = {}
    for slug in MODEL_CONFIGS:
        raw_path = PACKAGE / f"models/{slug}/raw/episodes.jsonl"
        validation_path = PACKAGE / f"models/{slug}/validation.json"
        if not raw_path.exists() or not validation_path.exists():
            raise RuntimeError(f"formal model output missing: {slug}")
        rows.extend(load_jsonl(raw_path))
        validations[slug] = json.loads(
            validation_path.read_text(encoding="utf-8")
        )
    result = analyze_rows(rows, MODEL_ID_TO_SLUG)
    result["model_validations"] = validations
    analysis_dir = PACKAGE / "analysis"
    write_json(analysis_dir / "results.json", result)
    lines = [
        "# TopoSafe-Delta Execution Topology Pilot v0.1",
        "",
        "**Status:** complete development-only direct G_E pilot",
        "",
        (
            f"Formal episodes: {result['episodes']}; provider errors: "
            f"{result['provider_errors']}; malformed: {result['malformed']}; "
            f"truncated: {result['truncated']}."
        ),
        "",
        (
            "Estimated provider cost: "
            f"${result['estimated_total_cost_usd']:.4f}; conservative accounting: "
            f"${result['conservative_total_cost_usd']:.4f}."
        ),
        "",
        "## Results",
        "",
        (
            "| Model | Authority | G_E holder | Invalid-proof advisory FAR | "
            "Invalid-proof executed FAR | True protected utilization |"
        ),
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for row in result["cells"]:
        lines.append(
            f"| {row['model_slug']} | {row['authority_regime']} | "
            f"{row['execution_holder']} | "
            f"{row['invalid_false_advisory_far']:.1%} | "
            f"{row['invalid_false_executed_far']:.1%} | "
            f"{row['true_protected_utilization']:.1%} |"
        )
    lines.extend(
        [
            "",
            "## Evidence boundary",
            "",
            (
                "This is a development pilot on eight previously exposed synthetic "
                "tasks. It directly varies execution-capability placement while "
                "holding the route, proof, message, action space, and one-call budget "
                "fixed. It is not confirmatory and does not establish real-world "
                "generalization."
            ),
            "",
        ]
    )
    (analysis_dir / "results.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )
    summary = {
        "experiment_id": EXPERIMENT_ID,
        "status": "development_pilot_complete",
        "formal_rows": len(rows),
        "estimated_total_cost_usd": result["estimated_total_cost_usd"],
        "conservative_total_cost_usd": result[
            "conservative_total_cost_usd"
        ],
        "result_status": RESULT_STATUS,
        "results_sha256": sha256_file(analysis_dir / "results.json"),
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

