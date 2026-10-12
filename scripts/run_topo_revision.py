#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from swarmsafe_delta.authority_composition import MODEL_CONFIGS
from swarmsafe_delta.authority_placement import AuthorityBedrockTextModel
from swarmsafe_delta.structured_forwarding import StructuredForwardBedrockModel
from swarmsafe_delta.topo_revision_authority_cut import (
    run_episode as run_e2_episode,
)
from swarmsafe_delta.topo_revision_common import (
    AtomicRowStore,
    DEFAULT_SEED,
    MAX_ATTEMPTS,
    MAX_OUTPUT_TOKENS,
    MODEL_SLUGS,
    REVISION_ROOT,
    budget_ledger,
    enforce_budget,
    sha256_file,
    utc_now,
    write_json,
)
from swarmsafe_delta.topo_revision_provenance import (
    run_episode as run_e1_episode,
)
from swarmsafe_delta.topo_revision_workflow import (
    run_episode as run_e3_episode,
)

from scripts.validate_topo_revision import load_cases, validate_rows


ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / REVISION_ROOT
MANIFEST = PACKAGE / "manifest.json"
PROGRESS_EVERY = 10


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", choices=("E1", "E2", "E3"), required=True)
    parser.add_argument(
        "--stage",
        choices=("pilot", "formal"),
        default=os.environ.get("RUN_MODE"),
    )
    parser.add_argument(
        "--model-slug",
        choices=(*MODEL_SLUGS, "all"),
        default="all",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=int(os.environ.get("MAX_PARALLEL_REQUESTS", "5")),
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=int(os.environ.get("EXPERIMENT_SEED", str(DEFAULT_SEED))),
    )
    parser.add_argument(
        "--max-calls",
        type=int,
        default=int(os.environ.get("MAX_NEW_LLM_CALLS", "15000")),
    )
    parser.add_argument(
        "--max-spend-usd",
        type=float,
        default=float(os.environ.get("MAX_SPEND_USD", "250")),
    )
    parser.add_argument("--connect-timeout-seconds", type=int, default=10)
    parser.add_argument("--read-timeout-seconds", type=int, default=180)
    args = parser.parse_args()
    if not args.stage:
        parser.error("--stage or RUN_MODE is required")
    if not 1 <= args.workers <= 5:
        parser.error("workers must be between 1 and 5")
    return args


def load_tasks(experiment: str) -> list[dict[str, Any]]:
    path = PACKAGE / f"frozen/{experiment.lower()}_tasks.json"
    return json.loads(path.read_text(encoding="utf-8"))


def verify_frozen(args: argparse.Namespace) -> dict[str, Any]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("status") != "frozen_pre_run":
        raise RuntimeError("revision manifest is not frozen_pre_run")
    if args.seed != manifest["schedule_seed"]:
        raise ValueError("runtime seed differs from frozen seed")
    mismatches = []
    for relative, expected in manifest["source_hashes"].items():
        path = ROOT / relative
        if not path.exists():
            mismatches.append(f"{relative}: missing")
        elif sha256_file(path) != expected:
            mismatches.append(f"{relative}: hash mismatch")
    if mismatches:
        raise RuntimeError("frozen source mismatch: " + " | ".join(mismatches))
    return manifest


def require_pilot(experiment: str, model_slug: str) -> None:
    path = (
        PACKAGE
        / f"runs/{experiment}/pilot/{model_slug}/validation.json"
    )
    if not path.exists():
        raise RuntimeError(
            f"{experiment} pilot validation missing for {model_slug}"
        )
    report = json.loads(path.read_text(encoding="utf-8"))
    if not report.get("passed"):
        raise RuntimeError(
            f"{experiment} pilot gate failed for {model_slug}"
        )


def executor_model(
    model_slug: str,
    args: argparse.Namespace,
) -> AuthorityBedrockTextModel:
    config = MODEL_CONFIGS[model_slug]
    return AuthorityBedrockTextModel(
        model_id=config["model_id"],
        region=config["region"],
        temperature=config["temperature"],
        top_p=config["top_p"],
        additional_model_request_fields=config[
            "additional_model_request_fields"
        ],
        force_action_tool=config["force_action_tool"],
        action_tool_mode=config.get("action_tool_mode"),
        max_attempts=MAX_ATTEMPTS,
        connect_timeout_seconds=args.connect_timeout_seconds,
        read_timeout_seconds=args.read_timeout_seconds,
    )


def forward_model(
    model_slug: str,
    args: argparse.Namespace,
) -> StructuredForwardBedrockModel:
    config = MODEL_CONFIGS[model_slug]
    return StructuredForwardBedrockModel(
        model_id=config["model_id"],
        region=config["region"],
        temperature=config["temperature"],
        top_p=config["top_p"],
        additional_model_request_fields=config[
            "additional_model_request_fields"
        ],
        force_action_tool=False,
        action_tool_mode="none",
        max_attempts=MAX_ATTEMPTS,
        connect_timeout_seconds=args.connect_timeout_seconds,
        read_timeout_seconds=args.read_timeout_seconds,
    )


def error_row(
    *,
    case: dict[str, Any],
    model_slug: str,
    model: Any,
    exc: Exception,
    stage: str,
) -> dict[str, Any]:
    return {
        **case,
        "stage": stage,
        "model_slug": model_slug,
        "model_id": model.model_id,
        "provider_error": f"{type(exc).__name__}: {exc}",
        "selected_action": "provider_error",
        "protected_action_selected": False,
        "policy_invalid_committed_action": False,
        "false_state_committed_action": False,
        "true_state_task_completion": False,
        "safe_progress": False,
        "abstention": False,
        "malformed": True,
        "truncated": False,
        "assigned_model_calls": case["assigned_model_calls"],
        "realized_model_calls": 0,
        "api_attempts": int(getattr(exc, "attempts", 0)),
        "attempt_errors": list(getattr(exc, "attempt_errors", ())),
        "input_tokens": 0,
        "output_tokens": 0,
        "latency_ms": 0,
        "request_ids": [],
        "started_at": utc_now(),
        "finished_at": utc_now(),
        "status": "incomplete_provider_error",
    }


def main() -> None:
    args = parse_args()
    verify_frozen(args)
    selected_models = (
        list(MODEL_SLUGS)
        if args.model_slug == "all"
        else [args.model_slug]
    )
    if args.stage == "formal":
        for model_slug in selected_models:
            require_pilot(args.experiment, model_slug)
    tasks = load_tasks(args.experiment)
    task_map = {task["id"]: task for task in tasks}
    cases = load_cases(args.experiment, args.stage)
    stores = {
        model_slug: AtomicRowStore(
            PACKAGE
            / f"runs/{args.experiment}/{args.stage}/{model_slug}/raw/"
            "episodes.jsonl"
        )
        for model_slug in selected_models
    }
    jobs = []
    model_call_counts = {model_slug: 0 for model_slug in selected_models}
    for model_slug in selected_models:
        successful = stores[model_slug].successful_ids()
        for case in cases:
            if case["episode_id"] in successful:
                continue
            jobs.append((model_slug, case))
            model_call_counts[model_slug] += int(
                case["assigned_model_calls"]
            )
    random.Random(args.seed).shuffle(jobs)
    prospective_calls = sum(model_call_counts.values())
    preflight_budget = enforce_budget(
        additional_assigned_calls=prospective_calls,
        max_calls=args.max_calls,
        max_spend_usd=args.max_spend_usd,
        model_call_counts=model_call_counts,
        root=PACKAGE,
    )
    write_json(
        PACKAGE
        / f"runs/{args.experiment}/{args.stage}/pre_run_budget.json",
        {
            **preflight_budget,
            "experiment": args.experiment,
            "stage": args.stage,
            "selected_models": selected_models,
            "missing_jobs": len(jobs),
            "model_call_counts": model_call_counts,
            "workers": args.workers,
            "seed": args.seed,
        },
    )
    models = {
        model_slug: executor_model(model_slug, args)
        for model_slug in selected_models
    }
    forwarders = (
        {
            model_slug: forward_model(model_slug, args)
            for model_slug in selected_models
        }
        if args.experiment == "E3"
        else {}
    )
    completed = 0
    progress_lock = threading.Lock()

    def execute(job: tuple[str, dict[str, Any]]) -> tuple[str, dict[str, Any]]:
        model_slug, base_case = job
        case = {**base_case, "stage": args.stage}
        task = task_map[case["task_id"]]
        model = models[model_slug]
        try:
            if args.experiment == "E1":
                row = run_e1_episode(
                    task=task,
                    case=case,
                    model=model,
                    model_slug=model_slug,
                    schedule_seed=args.seed,
                    max_output_tokens=MAX_OUTPUT_TOKENS,
                )
            elif args.experiment == "E2":
                row = run_e2_episode(
                    task=task,
                    case=case,
                    model=model,
                    model_slug=model_slug,
                    schedule_seed=args.seed,
                    max_output_tokens=MAX_OUTPUT_TOKENS,
                )
            else:
                row = run_e3_episode(
                    task=task,
                    case=case,
                    forward_model=forwarders[model_slug],
                    executor_model=model,
                    model_slug=model_slug,
                    schedule_seed=args.seed,
                    max_output_tokens=MAX_OUTPUT_TOKENS,
                )
        except Exception as exc:
            row = error_row(
                case=case,
                model_slug=model_slug,
                model=model,
                exc=exc,
                stage=args.stage,
            )
        return model_slug, row

    try:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(execute, job): job for job in jobs}
            for future in as_completed(futures):
                model_slug, row = future.result()
                stores[model_slug].put(row, persist=False)
                with progress_lock:
                    completed += 1
                    if completed % PROGRESS_EVERY == 0:
                        for store in stores.values():
                            store.flush()
                        print(
                            json.dumps(
                                {
                                    "experiment": args.experiment,
                                    "stage": args.stage,
                                    "completed_jobs": completed,
                                    "total_jobs": len(jobs),
                                },
                                sort_keys=True,
                            ),
                            flush=True,
                        )
    finally:
        for store in stores.values():
            store.flush()

    reports = {}
    failed = False
    for model_slug, store in stores.items():
        report = validate_rows(
            experiment=args.experiment,
            stage=args.stage,
            model_slug=model_slug,
            expected_cases=cases,
            rows=list(store.rows.values()),
        )
        reports[model_slug] = report
        write_json(
            PACKAGE
            / f"runs/{args.experiment}/{args.stage}/{model_slug}/"
            "validation.json",
            report,
        )
        failed = failed or not report["passed"]
    ledger = budget_ledger(PACKAGE)
    write_json(PACKAGE / "COST_LEDGER.json", ledger)
    print(
        json.dumps(
            {
                "experiment": args.experiment,
                "stage": args.stage,
                "new_jobs": len(jobs),
                "validity": {
                    slug: report["passed"]
                    for slug, report in reports.items()
                },
                "ledger": ledger,
            },
            indent=2,
            sort_keys=True,
        )
    )
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
