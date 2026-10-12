#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from swarmsafe_delta.authority_placement import (
    EXPERIMENT_ID,
    MODEL_CONFIGS,
    SMOKE_TASK_IDS,
    AuthorityBedrockTextModel,
    analyze_rows,
    build_cases,
    render_summary_markdown,
    run_jobs,
    validate_rows,
)
from swarmsafe_delta.pilot import (
    canonical_json,
    load_tasks,
    sha256_file,
    utc_now,
)


ROOT = Path("experiments/TopoSafe-Delta-AuthorityPlacement-v1.6")
TASKS_PATH = Path("data/authority_placement_tasks_v1.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("smoke", "formal"), required=True)
    parser.add_argument(
        "--model-slug",
        choices=tuple(MODEL_CONFIGS),
        required=True,
    )
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--seed", type=int, default=2026100607)
    parser.add_argument("--max-output-tokens", type=int, default=200)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--connect-timeout-seconds", type=int, default=10)
    parser.add_argument("--read-timeout-seconds", type=int, default=180)
    return parser.parse_args()


def verify_frozen_sources(manifest: dict) -> None:
    mismatches = []
    for raw_path, expected in manifest["source_hashes"].items():
        path = Path(raw_path)
        observed = sha256_file(path)
        if observed != expected:
            mismatches.append(
                f"{path}: expected {expected}, observed {observed}"
            )
    if mismatches:
        raise RuntimeError(
            "Frozen source hash mismatch: " + " | ".join(mismatches)
        )


def main() -> None:
    args = parse_args()
    manifest = json.loads(
        (ROOT / "manifest.json").read_text(encoding="utf-8")
    )
    if manifest["status"] != "frozen_pre_run":
        raise RuntimeError("Experiment manifest is not frozen_pre_run")
    verify_frozen_sources(manifest)
    if args.max_output_tokens != manifest["max_output_tokens"]:
        raise ValueError("--max-output-tokens differs from frozen manifest")
    if args.max_attempts != manifest["maximum_provider_attempts"]:
        raise ValueError("--max-attempts differs from frozen manifest")
    if args.read_timeout_seconds != manifest["read_timeout_seconds"]:
        raise ValueError("--read-timeout-seconds differs from manifest")
    if args.workers != manifest["workers"]:
        raise ValueError("--workers differs from frozen manifest")

    tasks = load_tasks(TASKS_PATH)
    if args.stage == "smoke":
        selected_ids = set(SMOKE_TASK_IDS)
        tasks = [task for task in tasks if task["id"] in selected_ids]
        output_dir = ROOT / "smoke" / args.model_slug
    else:
        output_dir = ROOT / "models" / args.model_slug
    cases = build_cases(tasks)
    model_config = MODEL_CONFIGS[args.model_slug]
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = output_dir / "raw" / "episodes.jsonl"
    analysis_dir = output_dir / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    model_manifest = {
        "experiment_id": EXPERIMENT_ID,
        "status": f"{args.stage}_assigned",
        "created_at": utc_now(),
        "stage": args.stage,
        "model_slug": args.model_slug,
        **model_config,
        "tasks": [task["id"] for task in tasks],
        "conditions": [case["condition"] for case in cases[:14]],
        "planned_episodes": len(cases),
        "planned_model_calls": len(cases),
        "workers": args.workers,
        "schedule_seed": args.seed,
        "provider_seed_supported": False,
        "max_output_tokens": args.max_output_tokens,
        "max_attempts": args.max_attempts,
        "connect_timeout_seconds": args.connect_timeout_seconds,
        "read_timeout_seconds": args.read_timeout_seconds,
        "root_manifest_sha256": sha256_file(ROOT / "manifest.json"),
        "task_file_sha256": sha256_file(TASKS_PATH),
        "runner_sha256": sha256_file(
            Path("scripts/run_authority_placement.py")
        ),
        "module_sha256": sha256_file(
            Path("src/swarmsafe_delta/authority_placement.py")
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
    summary = analyze_rows(
        rows=rows,
        tasks=tasks,
        validation=validation,
        seed=args.seed,
    )
    summary["model_slug"] = args.model_slug
    summary["model_id"] = model_config["model_id"]
    summary["stage"] = args.stage
    (analysis_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    (analysis_dir / "summary.md").write_text(
        render_summary_markdown(summary),
        encoding="utf-8",
    )
    print(
        canonical_json(
            {
                "stage": args.stage,
                "model_slug": args.model_slug,
                "episodes": len(rows),
                "validation_passed": validation["passed"],
                "provider_errors": validation["provider_errors"],
                "summary": str(analysis_dir / "summary.json"),
            }
        )
    )
    if not validation["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
