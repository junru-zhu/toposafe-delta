#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from swarmsafe_delta.authority_composition import (
    EXPERIMENT_ID,
    MODEL_CONFIGS,
    SMOKE_TASK_IDS,
    build_study_a_cases,
    build_threshold_cases,
    run_jobs,
    validate_rows,
)
from swarmsafe_delta.authority_placement import AuthorityBedrockTextModel
from swarmsafe_delta.pilot import (
    canonical_json,
    load_tasks,
    sha256_file,
    utc_now,
)


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
    parser.add_argument(
        "--model-slug",
        choices=tuple(MODEL_CONFIGS),
        required=True,
    )
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--seed", type=int, default=2026100611)
    parser.add_argument("--max-output-tokens", type=int, default=200)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--connect-timeout-seconds", type=int, default=10)
    parser.add_argument("--read-timeout-seconds", type=int, default=180)
    return parser.parse_args()


def verify_frozen_sources(manifest: dict) -> None:
    mismatches = []
    for relative_path, expected in manifest["source_hashes"].items():
        path = REPO_ROOT / relative_path
        if not path.exists():
            mismatches.append(f"{relative_path}: missing")
            continue
        observed = sha256_file(path)
        if observed != expected:
            mismatches.append(
                f"{relative_path}: expected {expected}, observed {observed}"
            )
    if mismatches:
        raise RuntimeError(
            "Frozen source hash mismatch: " + " | ".join(mismatches)
        )


def main() -> None:
    args = parse_args()
    manifest_path = PACKAGE / "manifest.json"
    if not manifest_path.exists():
        raise RuntimeError(
            "No frozen manifest exists; run freeze_authority_composition.py "
            "after all gates pass"
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "frozen_pre_run":
        raise RuntimeError("Experiment manifest is not frozen_pre_run")
    verify_frozen_sources(manifest)
    frozen_values = {
        "workers": args.workers,
        "schedule_seed": args.seed,
        "max_output_tokens": args.max_output_tokens,
        "maximum_provider_attempts": args.max_attempts,
        "connect_timeout_seconds": args.connect_timeout_seconds,
        "read_timeout_seconds": args.read_timeout_seconds,
    }
    mismatches = [
        key
        for key, observed in frozen_values.items()
        if manifest.get(key) != observed
    ]
    if mismatches:
        raise ValueError(
            "Runtime arguments differ from the frozen manifest: "
            + ", ".join(mismatches)
        )
    if args.stage == "smoke" and args.study != "study_a":
        raise ValueError("Smoke preflight is frozen for Study A only")

    tasks = load_tasks(REPO_ROOT / manifest["task_file"])
    if args.study == "study_a":
        if args.stage == "smoke":
            selected = set(SMOKE_TASK_IDS)
            tasks = [task for task in tasks if task["id"] in selected]
        cases = build_study_a_cases(tasks)
    else:
        cases = build_threshold_cases(tasks)

    stage_dir = "smoke" if args.stage == "smoke" else "models"
    output_dir = PACKAGE / stage_dir / args.study / args.model_slug
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = output_dir / "raw/episodes.jsonl"
    model_config = MODEL_CONFIGS[args.model_slug]
    model_manifest = {
        "experiment_id": EXPERIMENT_ID,
        "status": f"{args.stage}_assigned",
        "created_at": utc_now(),
        "stage": args.stage,
        "study": args.study,
        "model_slug": args.model_slug,
        **model_config,
        "tasks": sorted({case["task_id"] for case in cases}),
        "conditions": sorted({case["condition"] for case in cases}),
        "planned_episodes": len(cases),
        "planned_model_calls": len(cases),
        "workers": args.workers,
        "schedule_seed": args.seed,
        "provider_seed_supported": False,
        "max_output_tokens": args.max_output_tokens,
        "max_attempts": args.max_attempts,
        "connect_timeout_seconds": args.connect_timeout_seconds,
        "read_timeout_seconds": args.read_timeout_seconds,
        "root_manifest_sha256": sha256_file(manifest_path),
        "task_file_sha256": sha256_file(
            REPO_ROOT / manifest["task_file"]
        ),
        "runner_sha256": sha256_file(Path(__file__)),
        "module_sha256": sha256_file(
            REPO_ROOT / "src/swarmsafe_delta/authority_composition.py"
        ),
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(
            model_manifest,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    model = AuthorityBedrockTextModel(
        model_id=model_config["model_id"],
        region=model_config["region"],
        temperature=model_config["temperature"],
        top_p=model_config["top_p"],
        additional_model_request_fields=model_config[
            "additional_model_request_fields"
        ],
        force_action_tool=model_config["force_action_tool"],
        max_attempts=args.max_attempts,
        connect_timeout_seconds=args.connect_timeout_seconds,
        read_timeout_seconds=args.read_timeout_seconds,
        action_tool_mode=model_config.get("action_tool_mode"),
    )
    rows = run_jobs(
        tasks=tasks,
        cases=cases,
        model=model,
        workers=args.workers,
        seed=args.seed,
        max_output_tokens=args.max_output_tokens,
        raw_path=raw_path,
    )
    validation = validate_rows(
        rows=rows,
        tasks=tasks,
        cases=cases,
        max_attempts=args.max_attempts,
        max_output_tokens=args.max_output_tokens,
    )
    analysis_dir = output_dir / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    (analysis_dir / "validation.json").write_text(
        json.dumps(
            validation,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        canonical_json(
            {
                "stage": args.stage,
                "study": args.study,
                "model_slug": args.model_slug,
                "episodes": len(rows),
                "validation_passed": validation["passed"],
                "provider_errors": validation["provider_errors"],
            }
        )
    )
    if not validation["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
