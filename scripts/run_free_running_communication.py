#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from swarmsafe_delta.authority_composition import MODEL_CONFIGS
from swarmsafe_delta.authority_placement import AuthorityBedrockTextModel
from swarmsafe_delta.free_running_communication import (
    EXECUTOR_MAX_OUTPUT_TOKENS,
    EXPERIMENT_ID,
    FORWARD_MAX_OUTPUT_TOKENS,
    MODEL_CALLS_PER_EPISODE,
    run_jobs,
    validate_rows,
)
from swarmsafe_delta.pilot import (
    canonical_json,
    load_tasks,
    sha256_file,
    utc_now,
)


ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "experiments/TopoSafe-Delta-FreeRunningCommunication-v0.1"
B1 = ROOT / "experiments/TopoSafe-Delta-MatchedCommunication-v0.1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("smoke", "formal"), required=True)
    parser.add_argument(
        "--model-slug", choices=tuple(MODEL_CONFIGS), required=True
    )
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--seed", type=int, default=2026100641)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--connect-timeout-seconds", type=int, default=10)
    parser.add_argument("--read-timeout-seconds", type=int, default=180)
    return parser.parse_args()


def verify_hashes(source_hashes: dict[str, str]) -> None:
    mismatches = []
    for relative, expected in source_hashes.items():
        path = ROOT / relative
        observed = sha256_file(path) if path.exists() else "missing"
        if observed != expected:
            mismatches.append(
                f"{relative}: expected {expected}, observed {observed}"
            )
    if mismatches:
        raise RuntimeError("Frozen source mismatch: " + " | ".join(mismatches))


def model(
    config: dict[str, object],
    *,
    forward: bool,
    max_attempts: int,
    connect_timeout_seconds: int,
    read_timeout_seconds: int,
) -> AuthorityBedrockTextModel:
    return AuthorityBedrockTextModel(
        model_id=str(config["model_id"]),
        region=str(config["region"]),
        temperature=config["temperature"],
        top_p=config["top_p"],
        additional_model_request_fields=config[
            "additional_model_request_fields"
        ],
        force_action_tool=False if forward else bool(config["force_action_tool"]),
        action_tool_mode="none" if forward else config.get("action_tool_mode"),
        max_attempts=max_attempts,
        connect_timeout_seconds=connect_timeout_seconds,
        read_timeout_seconds=read_timeout_seconds,
    )


def main() -> None:
    args = parse_args()
    manifest_path = PACKAGE / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("status") != "frozen_pre_run":
        raise RuntimeError("Experiment manifest is not frozen_pre_run")
    verify_hashes(manifest["source_hashes"])
    runtime = {
        "workers": args.workers,
        "schedule_seed": args.seed,
        "maximum_provider_attempts": args.max_attempts,
        "connect_timeout_seconds": args.connect_timeout_seconds,
        "read_timeout_seconds": args.read_timeout_seconds,
    }
    mismatches = [
        key for key, value in runtime.items() if manifest.get(key) != value
    ]
    if mismatches:
        raise ValueError(
            "Runtime arguments differ from frozen manifest: "
            + ", ".join(mismatches)
        )
    tasks = load_tasks(ROOT / manifest["task_file"])
    cases = json.loads((ROOT / manifest["case_file"]).read_text())
    if args.stage == "smoke":
        selected = set(manifest["smoke_episode_ids"])
        cases = [
            case
            for case in cases
            if f"{case['task_id']}::{case['condition']}" in selected
        ]
    stage_root = PACKAGE / ("smoke" if args.stage == "smoke" else "models")
    output_dir = stage_root / args.model_slug
    raw_path = output_dir / "raw/episodes.jsonl"
    config = MODEL_CONFIGS[args.model_slug]
    model_manifest = {
        "experiment_id": EXPERIMENT_ID,
        "created_at": utc_now(),
        "stage": args.stage,
        "model_slug": args.model_slug,
        "planned_episodes": len(cases),
        "planned_model_calls": len(cases) * MODEL_CALLS_PER_EPISODE,
        **config,
        **runtime,
        "forward_response_mode": "json_text",
        "forward_max_output_tokens": FORWARD_MAX_OUTPUT_TOKENS,
        "executor_max_output_tokens": EXECUTOR_MAX_OUTPUT_TOKENS,
        "root_manifest_sha256": sha256_file(manifest_path),
        "runner_sha256": sha256_file(Path(__file__)),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "manifest.json").write_text(
        json.dumps(model_manifest, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    forward_model = model(
        config,
        forward=True,
        max_attempts=args.max_attempts,
        connect_timeout_seconds=args.connect_timeout_seconds,
        read_timeout_seconds=args.read_timeout_seconds,
    )
    executor_model = model(
        config,
        forward=False,
        max_attempts=args.max_attempts,
        connect_timeout_seconds=args.connect_timeout_seconds,
        read_timeout_seconds=args.read_timeout_seconds,
    )
    rows = run_jobs(
        tasks=tasks,
        cases=cases,
        forward_model=forward_model,
        executor_model=executor_model,
        workers=args.workers,
        seed=args.seed,
        raw_path=raw_path,
    )
    b1_validation = json.loads(
        (B1 / "models/validation_report.json").read_text()
    )
    b1_gate = bool(b1_validation["models"][args.model_slug]["passed"])
    validation = validate_rows(
        rows=rows,
        tasks=tasks,
        cases=cases,
        max_attempts=args.max_attempts,
        b1_model_control_gate_passed=b1_gate,
    )
    analysis_dir = output_dir / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    (analysis_dir / "validation.json").write_text(
        json.dumps(validation, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    print(
        canonical_json(
            {
                "stage": args.stage,
                "model_slug": args.model_slug,
                "episodes": len(rows),
                "assigned_model_calls": (
                    len(rows) * MODEL_CALLS_PER_EPISODE
                ),
                "provider_errors": validation["provider_errors"],
                "validation_passed": validation["passed"],
            }
        )
    )
    if not validation["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
