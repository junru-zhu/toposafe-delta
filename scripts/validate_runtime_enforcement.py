#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from swarmsafe_delta.pilot import canonical_json, sha256_file
from swarmsafe_delta.runtime_enforcement import validate_recovery_rows
from swarmsafe_delta.topology_pilot import load_jsonl


ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "experiments/TopoSafe-Delta-RuntimeEnforcement-v0.1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("smoke", "formal"), required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest_path = PACKAGE / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    all_cases = json.loads(
        (PACKAGE / "recovery_cases.json").read_text(encoding="utf-8")
    )
    active_models = manifest["active_models"]
    stage_dir = "smoke" if args.stage == "smoke" else "models"
    selected_smoke = set(manifest["smoke_recovery_ids"])
    models = {}
    for slug in active_models:
        cases = [
            case for case in all_cases
            if case["source_model_slug"] == slug
            and (
                args.stage == "formal"
                or case["recovery_id"] in selected_smoke
            )
        ]
        model_dir = PACKAGE / stage_dir / slug
        raw_path = model_dir / "raw/recovery.jsonl"
        model_manifest_path = model_dir / "manifest.json"
        if not raw_path.exists() or not model_manifest_path.exists():
            models[slug] = {"passed": False, "missing": True}
            continue
        model_manifest = json.loads(
            model_manifest_path.read_text(encoding="utf-8")
        )
        if model_manifest.get("root_manifest_sha256") != sha256_file(
            manifest_path
        ):
            models[slug] = {
                "passed": False,
                "root_manifest_hash_mismatch": True,
            }
            continue
        models[slug] = validate_recovery_rows(
            rows=load_jsonl(raw_path),
            cases=cases,
            max_attempts=model_manifest["maximum_provider_attempts"],
            max_output_tokens=model_manifest["max_output_tokens"],
        )
    passed = all(row.get("passed") for row in models.values())
    report = {
        "experiment_id": manifest["experiment_id"],
        "stage": args.stage,
        "passed": passed,
        "models": models,
        "rows_expected": sum(
            row.get("rows_expected", 0) for row in models.values()
        ),
        "rows_observed": sum(
            row.get("rows_observed", 0) for row in models.values()
        ),
        "provider_errors": sum(
            row.get("provider_errors", 0) for row in models.values()
        ),
        "invalid_or_missing_models": [
            slug for slug, row in models.items() if not row.get("passed")
        ],
    }
    report_path = PACKAGE / stage_dir / "validation_report.json"
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
