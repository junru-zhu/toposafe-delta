#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from swarmsafe_delta.authority_composition import (
    MODEL_CONFIGS,
    SMOKE_TASK_IDS,
    build_study_a_cases,
    build_threshold_cases,
    validate_rows,
)
from swarmsafe_delta.pilot import canonical_json, load_tasks, sha256_file
from swarmsafe_delta.topology_pilot import load_jsonl


REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGE = (
    REPO_ROOT / "experiments/TopoSafe-Delta-AuthorityComposition-v0.2"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("smoke", "formal"), required=True)
    parser.add_argument(
        "--study",
        choices=("study_a", "threshold"),
        required=True,
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root_manifest_path = PACKAGE / "manifest.json"
    if not root_manifest_path.exists():
        raise RuntimeError("No frozen authority-composition manifest exists")
    root_manifest = json.loads(
        root_manifest_path.read_text(encoding="utf-8")
    )
    tasks = load_tasks(REPO_ROOT / root_manifest["task_file"])
    if args.study == "study_a":
        if args.stage == "smoke":
            selected = set(SMOKE_TASK_IDS)
            tasks = [task for task in tasks if task["id"] in selected]
        cases = build_study_a_cases(tasks)
    else:
        if args.stage == "smoke":
            raise ValueError("Smoke validation is frozen for Study A only")
        cases = build_threshold_cases(tasks)

    stage_dir = "smoke" if args.stage == "smoke" else "models"
    stage_root = PACKAGE / stage_dir / args.study
    models = {}
    for slug in MODEL_CONFIGS:
        model_dir = stage_root / slug
        raw_path = model_dir / "raw/episodes.jsonl"
        manifest_path = model_dir / "manifest.json"
        if not raw_path.exists() or not manifest_path.exists():
            models[slug] = {
                "passed": False,
                "missing": [
                    str(path)
                    for path in (manifest_path, raw_path)
                    if not path.exists()
                ],
            }
            continue
        model_manifest = json.loads(
            manifest_path.read_text(encoding="utf-8")
        )
        if model_manifest.get("root_manifest_sha256") != sha256_file(
            root_manifest_path
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
        )
    passed = all(report.get("passed") for report in models.values())
    report = {
        "experiment_id": root_manifest["experiment_id"],
        "stage": args.stage,
        "study": args.study,
        "passed": passed,
        "models": models,
        "episodes_expected": len(cases) * len(MODEL_CONFIGS),
        "episodes_observed": sum(
            row.get("episodes_observed", 0) for row in models.values()
        ),
        "provider_errors": sum(
            row.get("provider_errors", 0) for row in models.values()
        ),
        "invalid_or_missing_models": [
            slug for slug, row in models.items() if not row.get("passed")
        ],
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
