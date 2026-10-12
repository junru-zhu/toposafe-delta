#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from swarmsafe_delta.authority_placement import (
    MODEL_CONFIGS,
    SMOKE_TASK_IDS,
    build_cases,
    validate_rows,
)
from swarmsafe_delta.pilot import canonical_json, load_tasks
from swarmsafe_delta.topology_pilot import load_jsonl


ROOT = Path("experiments/TopoSafe-Delta-AuthorityPlacement-v1.6")
TASKS_PATH = Path("data/authority_placement_tasks_v1.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("smoke", "formal"), required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root_manifest = json.loads(
        (ROOT / "manifest.json").read_text(encoding="utf-8")
    )
    tasks = load_tasks(TASKS_PATH)
    if args.stage == "smoke":
        selected_ids = set(SMOKE_TASK_IDS)
        tasks = [task for task in tasks if task["id"] in selected_ids]
        stage_root = ROOT / "smoke"
        report_path = stage_root / "validation_report.json"
    else:
        stage_root = ROOT / "models"
        report_path = ROOT / "validation_report.json"
    cases = build_cases(tasks)
    models = {}
    for slug in MODEL_CONFIGS:
        model_dir = stage_root / slug
        raw_path = model_dir / "raw" / "episodes.jsonl"
        if not raw_path.exists():
            models[slug] = {
                "passed": False,
                "missing": str(raw_path),
            }
            continue
        rows = load_jsonl(raw_path)
        model_manifest = json.loads(
            (model_dir / "manifest.json").read_text(encoding="utf-8")
        )
        models[slug] = validate_rows(
            rows=rows,
            tasks=tasks,
            cases=cases,
            max_attempts=model_manifest["max_attempts"],
            max_output_tokens=model_manifest["max_output_tokens"],
        )
    passed = all(row.get("passed") for row in models.values())
    report = {
        "experiment_id": root_manifest["experiment_id"],
        "stage": args.stage,
        "passed": passed,
        "models": models,
        "episodes_expected": len(cases) * len(MODEL_CONFIGS),
        "episodes_observed": sum(
            row.get("episodes_observed", 0) for row in models.values()
        ),
        "provider_errors": sum(
            row.get("provider_errors", 0) for row in models.values()
        ),
        "invalid_or_excluded": [
            slug for slug, row in models.items() if not row.get("passed")
        ],
    }
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
