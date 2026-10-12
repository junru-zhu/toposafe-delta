#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from swarmsafe_delta.matched_communication_topology import (
    MODEL_SLUGS,
    validate_rows,
)
from swarmsafe_delta.pilot import (
    canonical_json,
    load_tasks,
    sha256_file,
)
from swarmsafe_delta.topology_pilot import load_jsonl


ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "experiments/TopoSafe-Delta-MatchedCommunication-v0.1"


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
    if args.stage == "smoke":
        selected = set(manifest["smoke_episode_ids"])
        cases = [
            case
            for case in all_cases
            if f"{case['task_id']}::{case['condition']}" in selected
        ]
    else:
        cases = all_cases
    stage_root = PACKAGE / ("smoke" if args.stage == "smoke" else "models")
    models = {}
    for slug in MODEL_SLUGS:
        model_dir = stage_root / slug
        raw_path = model_dir / "raw/episodes.jsonl"
        model_manifest_path = model_dir / "manifest.json"
        if not raw_path.exists() or not model_manifest_path.exists():
            models[slug] = {
                "passed": False,
                "episodes_expected": len(cases),
                "episodes_observed": 0,
                "provider_errors": 0,
                "missing_files": [
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
                "episodes_expected": len(cases),
                "episodes_observed": 0,
                "provider_errors": 0,
                "root_manifest_hash_mismatch": True,
            }
            continue
        rows = load_jsonl(raw_path)
        models[slug] = validate_rows(
            rows=rows,
            tasks=tasks,
            cases=cases,
            max_attempts=manifest["maximum_provider_attempts"],
            max_output_tokens=manifest["max_output_tokens"],
            require_responsiveness=args.stage == "formal",
        )
    passed = all(report["passed"] for report in models.values())
    report = {
        "experiment_id": manifest["experiment_id"],
        "stage": args.stage,
        "passed": passed,
        "models": models,
        "rows_expected": len(cases) * len(MODEL_SLUGS),
        "rows_observed": sum(
            report.get("episodes_observed", 0) for report in models.values()
        ),
        "provider_errors": sum(
            report.get("provider_errors", 0) for report in models.values()
        ),
        "invalid_models": [
            slug for slug, report in models.items() if not report["passed"]
        ],
        "root_manifest_sha256": sha256_file(manifest_path),
    }
    report_path = stage_root / "validation_report.json"
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
