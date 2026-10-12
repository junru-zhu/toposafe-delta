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
    HARD_BUDGET_CAP_USD,
    MAX_OUTPUT_TOKENS,
    analyze_rows,
    estimate_case_ceiling_cost,
    estimate_rows_cost,
    run_model_jobs,
    validate_rows,
)
from swarmsafe_delta.pilot import (
    canonical_json,
    load_tasks,
    sha256_file,
    utc_now,
)


ROOT = Path(__file__).resolve().parent.parent
PARENT = ROOT / "experiments/TopoSafe-Delta-ExecutionTopologyPilot-v0.1"
PACKAGE = (
    ROOT
    / "experiments/TopoSafe-Delta-ExecutionTopologyPilot-v0.1R-GPTTechnicalRecovery"
)
PARENT_RAW = PARENT / "models/gpt-5.4/raw/episodes.jsonl"
PARENT_MANIFEST = PARENT / "manifest.json"
PROTOCOL = PACKAGE / "protocol.md"
MANIFEST = PACKAGE / "manifest.json"
MODEL_SLUG = "gpt-5.4"
MODEL_ID_TO_SLUG = {
    config["model_id"]: slug for slug, config in MODEL_CONFIGS.items()
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=("freeze", "run", "analyze"),
        required=True,
    )
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--seed", type=int, default=2026101211)
    parser.add_argument(
        "--budget-cap-usd",
        type=float,
        default=HARD_BUDGET_CAP_USD,
    )
    return parser.parse_args()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def failed_episode_ids() -> list[str]:
    return sorted(
        row["episode_id"]
        for row in load_jsonl(PARENT_RAW)
        if row.get("provider_error")
    )


def selected_cases() -> list[dict[str, Any]]:
    failed = set(failed_episode_ids())
    cases = json.loads((PARENT / "cases.json").read_text(encoding="utf-8"))
    return [
        case
        for case in cases
        if f"{case['task_id']}::{case['condition']}" in failed
    ]


def freeze(args: argparse.Namespace) -> None:
    failed = failed_episode_ids()
    cases = selected_cases()
    if len(failed) != 6 or len(cases) != 6:
        raise RuntimeError(
            f"expected exactly six frozen provider failures, found {len(failed)}"
        )
    parent_validation = json.loads(
        (PARENT / "models/gpt-5.4/validation.json").read_text(
            encoding="utf-8"
        )
    )
    if parent_validation.get("provider_errors") != 6:
        raise RuntimeError("parent validation no longer records six errors")
    required = [
        PARENT_RAW,
        PARENT_MANIFEST,
        PARENT / "cases.json",
        PARENT / "candidate_tasks.json",
        PROTOCOL,
        Path(__file__),
        ROOT / "src/swarmsafe_delta/execution_topology_pilot.py",
    ]
    source_hashes = {
        str(path.relative_to(ROOT)): sha256_file(path) for path in required
    }
    ceiling = estimate_case_ceiling_cost(
        cases,
        MODEL_SLUG,
        max_output_tokens=MAX_OUTPUT_TOKENS,
    )
    manifest = {
        "experiment_id": (
            "TopoSafe-Delta-ExecutionTopologyPilot-v0.1R-GPTTechnicalRecovery"
        ),
        "parent_experiment_id": EXPERIMENT_ID,
        "status": "frozen_pre_run",
        "evidence_type": "technical_recovery_sensitivity",
        "frozen_at": utc_now(),
        "selection_rule": "exact parent rows with provider_error=true",
        "failed_episode_ids": failed,
        "planned_calls": len(cases),
        "model_slug": MODEL_SLUG,
        "workers": args.workers,
        "schedule_seed": args.seed,
        "max_output_tokens": MAX_OUTPUT_TOKENS,
        "maximum_provider_attempts": 1,
        "read_timeout_seconds": 180,
        "hard_budget_cap_usd": args.budget_cap_usd,
        "conservative_recovery_cost_ceiling_usd": ceiling[
            "conservative_cost_ceiling_usd"
        ],
        "parent_raw_sha256": sha256_file(PARENT_RAW),
        "source_hashes": source_hashes,
    }
    write_json(MANIFEST, manifest)
    print(canonical_json(manifest))


def verify_frozen(manifest: dict[str, Any], args: argparse.Namespace) -> None:
    if manifest.get("status") != "frozen_pre_run":
        raise RuntimeError("recovery manifest is not frozen_pre_run")
    if manifest.get("failed_episode_ids") != failed_episode_ids():
        raise RuntimeError("parent provider-failure selection changed")
    if manifest.get("parent_raw_sha256") != sha256_file(PARENT_RAW):
        raise RuntimeError("parent raw artifact changed")
    for relative, expected in manifest["source_hashes"].items():
        path = ROOT / relative
        if sha256_file(path) != expected:
            raise RuntimeError(f"frozen source mismatch: {relative}")
    if (
        args.workers != manifest["workers"]
        or args.seed != manifest["schedule_seed"]
        or args.budget_cap_usd != manifest["hard_budget_cap_usd"]
    ):
        raise ValueError("runtime arguments differ from recovery freeze")


def parent_conservative_cost() -> float:
    total = 0.0
    for slug in MODEL_CONFIGS:
        path = PARENT / f"models/{slug}/raw/episodes.jsonl"
        total += estimate_rows_cost(
            load_jsonl(path),
            slug,
            conservative=True,
        )
    for slug in MODEL_CONFIGS:
        path = PARENT / f"smoke/{slug}/raw/episodes.jsonl"
        total += estimate_rows_cost(
            load_jsonl(path),
            slug,
            conservative=True,
        )
    return total


def validate_recovery_rows(
    rows: list[dict[str, Any]],
    cases: list[dict[str, Any]],
) -> dict[str, Any]:
    expected = {
        f"{case['task_id']}::{case['condition']}" for case in cases
    }
    observed = [row["episode_id"] for row in rows]
    errors = []
    if set(observed) != expected:
        errors.append("recovery episode IDs differ from frozen selection")
    if len(observed) != len(set(observed)):
        errors.append("duplicate recovery episode IDs")
    provider_errors = sum(bool(row.get("provider_error")) for row in rows)
    malformed = sum(bool(row.get("malformed")) for row in rows)
    truncated = sum(bool(row.get("truncated")) for row in rows)
    if provider_errors:
        errors.append(f"provider errors remain: {provider_errors}")
    if malformed or truncated:
        errors.append(
            f"recovery has malformed={malformed}, truncated={truncated}"
        )
    if any(
        row.get("executed_violation")
        and not row.get("proof_valid")
        and row.get("protected_action_selected")
        for row in rows
    ):
        errors.append("fail-closed enforcement bypass in recovery")
    return {
        "passed": not errors,
        "episodes_expected": len(cases),
        "episodes_observed": len(rows),
        "provider_errors": provider_errors,
        "malformed": malformed,
        "truncated": truncated,
        "errors": errors,
    }


def run(args: argparse.Namespace) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    verify_frozen(manifest, args)
    cases = selected_cases()
    tasks = load_tasks(PARENT / "candidate_tasks.json")
    projected = (
        parent_conservative_cost()
        + manifest["conservative_recovery_cost_ceiling_usd"]
    )
    if projected > manifest["hard_budget_cap_usd"]:
        raise RuntimeError(
            f"recovery would exceed hard cap: {projected:.6f} > "
            f"{manifest['hard_budget_cap_usd']:.2f}"
        )
    config = MODEL_CONFIGS[MODEL_SLUG]
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
    raw_path = PACKAGE / "raw/episodes.jsonl"
    rows = run_model_jobs(
        tasks=tasks,
        cases=cases,
        model=model,
        workers=args.workers,
        seed=args.seed,
        max_output_tokens=manifest["max_output_tokens"],
        raw_path=raw_path,
    )
    validation = validate_recovery_rows(rows, cases)
    write_json(PACKAGE / "validation.json", validation)
    budget = {
        "model_slug": MODEL_SLUG,
        "episodes": len(rows),
        "input_tokens": sum(row.get("input_tokens", 0) for row in rows),
        "output_tokens": sum(row.get("output_tokens", 0) for row in rows),
        "estimated_cost_usd": estimate_rows_cost(
            rows,
            MODEL_SLUG,
            conservative=False,
        ),
        "conservative_cost_usd": estimate_rows_cost(
            rows,
            MODEL_SLUG,
            conservative=True,
        ),
        "parent_plus_recovery_conservative_cost_usd": (
            parent_conservative_cost()
            + estimate_rows_cost(rows, MODEL_SLUG, conservative=True)
        ),
        "hard_budget_cap_usd": manifest["hard_budget_cap_usd"],
    }
    write_json(PACKAGE / "budget.json", budget)
    print(
        canonical_json(
            {
                "episodes": len(rows),
                "validation_passed": validation["passed"],
                "provider_errors": validation["provider_errors"],
                "estimated_cost_usd": budget["estimated_cost_usd"],
            }
        )
    )
    if not validation["passed"]:
        raise SystemExit(1)


def analyze() -> None:
    recovery_rows = load_jsonl(PACKAGE / "raw/episodes.jsonl")
    recovery_map = {row["episode_id"]: row for row in recovery_rows}
    parent_rows = []
    for slug in MODEL_CONFIGS:
        parent_rows.extend(
            load_jsonl(PARENT / f"models/{slug}/raw/episodes.jsonl")
        )
    combined = [
        recovery_map.get(row["episode_id"], row)
        if row["model_id"] == MODEL_CONFIGS[MODEL_SLUG]["model_id"]
        else row
        for row in parent_rows
    ]
    cases = json.loads((PARENT / "cases.json").read_text(encoding="utf-8"))
    per_model_validation = {}
    for slug, config in MODEL_CONFIGS.items():
        model_rows = [
            row for row in combined if row["model_id"] == config["model_id"]
        ]
        per_model_validation[slug] = validate_rows(model_rows, cases)
    cross_model_ids = [
        (row["model_id"], row["episode_id"]) for row in combined
    ]
    aggregate_errors = []
    if len(combined) != 512:
        aggregate_errors.append(f"expected 512 rows, found {len(combined)}")
    if len(cross_model_ids) != len(set(cross_model_ids)):
        aggregate_errors.append("duplicate model-episode pairs")
    if any(row.get("provider_error") for row in combined):
        aggregate_errors.append("provider errors remain after recovery")
    if any(
        row.get("executed_violation")
        and not row.get("proof_valid")
        and row.get("protected_action_selected")
        for row in combined
    ):
        aggregate_errors.append("fail-closed enforcement bypass")
    failed_models = [
        slug
        for slug, validation in per_model_validation.items()
        if not validation["passed"]
    ]
    if failed_models:
        aggregate_errors.append(
            f"combined per-model validation failed: {failed_models}"
        )
    result = analyze_rows(combined, MODEL_ID_TO_SLUG)
    result.update(
        {
            "status": "complete_four_model_technical_recovery_sensitivity",
            "parent_primary_status": (
                "complete_formal_gpt_transport_gate_failed"
            ),
            "recovered_episode_ids": sorted(recovery_map),
            "combined_validation_passed": not aggregate_errors,
            "combined_validation_errors": aggregate_errors,
            "per_model_validation": per_model_validation,
        }
    )
    analysis_dir = PACKAGE / "analysis"
    write_json(analysis_dir / "combined_results.json", result)
    lines = [
        "# TopoSafe-Delta Execution Topology Pilot v0.1R",
        "",
        "**Status:** complete four-model technical-recovery sensitivity",
        "",
        (
            "The immutable parent run contains six GPT-5.4 read timeouts and "
            "therefore fails its original four-model technical gate. This "
            "sensitivity replaces only those six provider-error rows with the "
            "separately frozen recovery responses."
        ),
        "",
        (
            f"Combined rows: {len(combined)}; recovery calls: "
            f"{len(recovery_rows)}; estimated successful-token cost: "
            f"${result['estimated_total_cost_usd']:.4f}."
        ),
        "",
        "| Model | Authority | G_E holder | Invalid-proof advisory FAR | Invalid-proof executed FAR | True protected utilization |",
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
            "This remains a development-only, previously exposed, synthetic-task "
            "pilot. The recovery does not retroactively make the immutable parent "
            "run pass its original technical gate.",
            "",
        ]
    )
    (analysis_dir / "combined_results.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )
    print(
        canonical_json(
            {
                "combined_rows": len(combined),
                "recovery_rows": len(recovery_rows),
                "combined_validation_passed": not aggregate_errors,
                "estimated_total_cost_usd": result[
                    "estimated_total_cost_usd"
                ],
            }
        )
    )
    if aggregate_errors:
        raise SystemExit(1)


def main() -> None:
    args = parse_args()
    if args.mode == "freeze":
        freeze(args)
    elif args.mode == "run":
        run(args)
    else:
        analyze()


if __name__ == "__main__":
    main()
