#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from swarmsafe_delta.authority_composition import MODEL_CONFIGS
from swarmsafe_delta.authority_placement import AuthorityBedrockTextModel
from swarmsafe_delta.pilot import (
    canonical_json,
    load_tasks,
    sha256_file,
    utc_now,
)
from swarmsafe_delta.runtime_enforcement_factorial import (
    EXPERIMENT_ID,
    run_factorial_recovery_jobs,
    run_initial_jobs,
    validate_factorial_recovery_rows,
    validate_initial_rows,
)


ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "experiments/TopoSafe-Delta-RuntimeEnforcement-v0.2"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("smoke", "formal"), required=True)
    parser.add_argument(
        "--phase", choices=("initial", "recovery"), required=True
    )
    parser.add_argument(
        "--model-slug", choices=tuple(MODEL_CONFIGS), required=True
    )
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--seed", type=int, default=2026100625)
    parser.add_argument("--max-output-tokens", type=int, default=200)
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


def main() -> None:
    args = parse_args()
    if args.stage == "smoke" and args.phase != "initial":
        raise ValueError("Recovery reuses the v0.1 provider path; no duplicate smoke")
    manifest_path = PACKAGE / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("status") != "frozen_pre_run":
        raise RuntimeError("Experiment manifest is not frozen_pre_run")
    verify_hashes(manifest["source_hashes"])
    runtime = {
        "workers": args.workers,
        "schedule_seed": args.seed,
        "max_output_tokens": args.max_output_tokens,
        "maximum_provider_attempts": args.max_attempts,
        "connect_timeout_seconds": args.connect_timeout_seconds,
        "read_timeout_seconds": args.read_timeout_seconds,
    }
    mismatch = [
        key for key, value in runtime.items() if manifest.get(key) != value
    ]
    if mismatch:
        raise ValueError(
            "Runtime arguments differ from frozen manifest: "
            + ", ".join(mismatch)
        )
    tasks = load_tasks(ROOT / manifest["task_file"])
    all_initial_cases = json.loads(
        (ROOT / manifest["initial_case_file"]).read_text()
    )
    if args.phase == "initial":
        cases = all_initial_cases
        if args.stage == "smoke":
            selected = set(manifest["smoke_initial_episode_ids"])
            cases = [
                case
                for case in cases
                if f"{case['task_id']}::{case['condition']}" in selected
            ]
    else:
        recovery_manifest_path = PACKAGE / "recovery_manifest.json"
        recovery_manifest = json.loads(recovery_manifest_path.read_text())
        if recovery_manifest["root_manifest_sha256"] != sha256_file(
            manifest_path
        ):
            raise RuntimeError("Recovery manifest does not match frozen root")
        verify_hashes(recovery_manifest["initial_source_hashes"])
        cases = [
            case
            for case in json.loads(
                (PACKAGE / "recovery_cases.json").read_text()
            )
            if case["source_model_slug"] == args.model_slug
        ]
    stage_root = PACKAGE / ("smoke" if args.stage == "smoke" else "models")
    output_dir = stage_root / args.phase / args.model_slug
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_name = "episodes.jsonl" if args.phase == "initial" else "recovery.jsonl"
    raw_path = output_dir / "raw" / raw_name
    config = MODEL_CONFIGS[args.model_slug]
    model_manifest = {
        "experiment_id": EXPERIMENT_ID,
        "created_at": utc_now(),
        "stage": args.stage,
        "phase": args.phase,
        "model_slug": args.model_slug,
        "planned_calls": len(cases),
        **config,
        **runtime,
        "root_manifest_sha256": sha256_file(manifest_path),
        "runner_sha256": sha256_file(Path(__file__)),
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(model_manifest, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    model = AuthorityBedrockTextModel(
        model_id=config["model_id"],
        region=config["region"],
        temperature=config["temperature"],
        top_p=config["top_p"],
        additional_model_request_fields=config[
            "additional_model_request_fields"
        ],
        force_action_tool=config["force_action_tool"],
        max_attempts=args.max_attempts,
        connect_timeout_seconds=args.connect_timeout_seconds,
        read_timeout_seconds=args.read_timeout_seconds,
        action_tool_mode=config.get("action_tool_mode"),
    )
    if args.phase == "initial":
        rows = run_initial_jobs(
            tasks=tasks,
            cases=cases,
            model=model,
            workers=args.workers,
            seed=args.seed,
            max_output_tokens=args.max_output_tokens,
            raw_path=raw_path,
        )
        validation = validate_initial_rows(
            rows=rows,
            tasks=tasks,
            cases=cases,
            max_attempts=args.max_attempts,
            max_output_tokens=args.max_output_tokens,
        )
    else:
        rows = run_factorial_recovery_jobs(
            tasks=tasks,
            cases=cases,
            model=model,
            workers=args.workers,
            seed=args.seed,
            max_output_tokens=args.max_output_tokens,
            raw_path=raw_path,
        )
        validation = validate_factorial_recovery_rows(
            rows=rows,
            cases=cases,
            max_attempts=args.max_attempts,
            max_output_tokens=args.max_output_tokens,
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
                "phase": args.phase,
                "model_slug": args.model_slug,
                "rows": len(rows),
                "provider_errors": validation["provider_errors"],
                "validation_passed": validation["passed"],
            }
        )
    )
    if not validation["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
