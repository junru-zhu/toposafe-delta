#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from swarmsafe_delta.authority_mechanism_ablations import (
    MODEL_SLUGS,
    validate_rows,
)
from swarmsafe_delta.pilot import canonical_json, load_tasks, sha256_file
from swarmsafe_delta.topology_pilot import load_jsonl


ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "experiments/TopoSafe-Delta-AuthorityMechanismAblations-v0.1"
PARENT = ROOT / "experiments/TopoSafe-Delta-RuntimeEnforcement-v0.2"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("smoke", "formal"), required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest_path = PACKAGE / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    tasks = load_tasks(ROOT / manifest["task_file"])
    all_cases = json.loads((ROOT / manifest["case_file"]).read_text())
    selected = set(manifest["smoke_episode_ids"])
    parent_validation = json.loads(
        (PARENT / "models/initial_validation_report.json").read_text()
    )
    stage_root = PACKAGE / ("smoke" if args.stage == "smoke" else "models")
    models = {}
    for slug in MODEL_SLUGS:
        cases = all_cases
        if args.stage == "smoke":
            cases = [
                case
                for case in cases
                if f"{case['task_id']}::{case['condition']}" in selected
            ]
        model_dir = stage_root / slug
        raw_path = model_dir / "raw/episodes.jsonl"
        model_manifest_path = model_dir / "manifest.json"
        if not raw_path.exists() or not model_manifest_path.exists():
            models[slug] = {
                "passed": False,
                "missing": [
                    str(path)
                    for path in (raw_path, model_manifest_path)
                    if not path.exists()
                ],
            }
            continue
        model_manifest = json.loads(model_manifest_path.read_text())
        if model_manifest.get("root_manifest_sha256") != sha256_file(
            manifest_path
        ):
            models[slug] = {
                "passed": False,
                "root_manifest_hash_mismatch": True,
            }
            continue
        models[slug] = validate_rows(
            rows=load_jsonl(raw_path),
            tasks=tasks,
            cases=cases,
            max_attempts=model_manifest["max_attempts"],
            max_output_tokens=model_manifest["max_output_tokens"],
            parent_model_gate_passed=bool(
                parent_validation["models"][slug]["passed"]
            ),
        )
    passed = all(report.get("passed") for report in models.values())
    report = {
        "experiment_id": manifest["experiment_id"],
        "stage": args.stage,
        "passed": passed,
        "models": models,
        "rows_expected": sum(
            int(report.get("episodes_expected", 0))
            for report in models.values()
        ),
        "rows_observed": sum(
            int(report.get("episodes_observed", 0))
            for report in models.values()
        ),
        "provider_errors": sum(
            int(report.get("provider_errors", 0))
            for report in models.values()
        ),
        "invalid_models": [
            slug for slug, report in models.items() if not report.get("passed")
        ],
        "root_manifest_sha256": sha256_file(manifest_path),
    }
    report_path = stage_root / "validation_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(canonical_json(report))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
