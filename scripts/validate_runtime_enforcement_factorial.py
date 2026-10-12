#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from swarmsafe_delta.pilot import canonical_json, load_tasks, sha256_file
from swarmsafe_delta.runtime_enforcement_factorial import (
    MODEL_SLUGS,
    validate_factorial_recovery_rows,
    validate_initial_rows,
)
from swarmsafe_delta.topology_pilot import load_jsonl


ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "experiments/TopoSafe-Delta-RuntimeEnforcement-v0.2"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("smoke", "formal"), required=True)
    parser.add_argument(
        "--phase", choices=("initial", "recovery"), required=True
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.stage == "smoke" and args.phase != "initial":
        raise ValueError("No separate recovery smoke stage is defined")
    manifest = json.loads((PACKAGE / "manifest.json").read_text())
    tasks = load_tasks(ROOT / manifest["task_file"])
    all_initial_cases = json.loads(
        (ROOT / manifest["initial_case_file"]).read_text()
    )
    selected_smoke = set(manifest["smoke_initial_episode_ids"])
    recovery_cases = (
        json.loads((PACKAGE / "recovery_cases.json").read_text())
        if args.phase == "recovery"
        else []
    )
    stage_root = PACKAGE / ("smoke" if args.stage == "smoke" else "models")
    models = {}
    for slug in MODEL_SLUGS:
        output_dir = stage_root / args.phase / slug
        if args.phase == "initial":
            raw_path = output_dir / "raw/episodes.jsonl"
            cases = all_initial_cases
            if args.stage == "smoke":
                cases = [
                    case
                    for case in cases
                    if f"{case['task_id']}::{case['condition']}"
                    in selected_smoke
                ]
            rows = load_jsonl(raw_path) if raw_path.exists() else []
            models[slug] = validate_initial_rows(
                rows=rows,
                tasks=tasks,
                cases=cases,
                max_attempts=manifest["maximum_provider_attempts"],
                max_output_tokens=manifest["max_output_tokens"],
            )
        else:
            raw_path = output_dir / "raw/recovery.jsonl"
            cases = [
                case
                for case in recovery_cases
                if case["source_model_slug"] == slug
            ]
            rows = load_jsonl(raw_path) if raw_path.exists() else []
            models[slug] = validate_factorial_recovery_rows(
                rows=rows,
                cases=cases,
                max_attempts=manifest["maximum_provider_attempts"],
                max_output_tokens=manifest["max_output_tokens"],
            )
    passed = all(report["passed"] for report in models.values())
    report = {
        "experiment_id": manifest["experiment_id"],
        "stage": args.stage,
        "phase": args.phase,
        "passed": passed,
        "models": models,
        "rows_expected": sum(
            row["episodes_expected"]
            if args.phase == "initial"
            else row["rows_expected"]
            for row in models.values()
        ),
        "rows_observed": sum(
            row["episodes_observed"]
            if args.phase == "initial"
            else row["rows_observed"]
            for row in models.values()
        ),
        "provider_errors": sum(
            row["provider_errors"] for row in models.values()
        ),
        "invalid_models": [
            slug for slug, row in models.items() if not row["passed"]
        ],
        "root_manifest_sha256": sha256_file(PACKAGE / "manifest.json"),
    }
    name = f"{args.phase}_validation_report.json"
    report_path = stage_root / name
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    print(canonical_json(report))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
