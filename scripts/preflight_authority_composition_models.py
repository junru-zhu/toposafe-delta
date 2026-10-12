#!/usr/bin/env python3
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from swarmsafe_delta.authority_composition import (
    MODEL_CONFIGS,
    build_study_a_cases,
)
from swarmsafe_delta.authority_placement import AuthorityBedrockTextModel
from swarmsafe_delta.pilot import load_tasks, utc_now
from swarmsafe_delta.topology_pilot import sha256_text


REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGE = (
    REPO_ROOT / "experiments/TopoSafe-Delta-AuthorityComposition-v0.2"
)
TASKS_PATH = PACKAGE / "candidate_tasks.json"
OUTPUT_PATH = PACKAGE / "preflight/model_preflight.json"


def run_one(slug: str, case: dict, task: dict) -> dict:
    config = MODEL_CONFIGS[slug]
    model = AuthorityBedrockTextModel(
        model_id=config["model_id"],
        region=config["region"],
        temperature=config["temperature"],
        top_p=config["top_p"],
        additional_model_request_fields=config[
            "additional_model_request_fields"
        ],
        force_action_tool=config["force_action_tool"],
        max_attempts=2,
        connect_timeout_seconds=10,
        read_timeout_seconds=120,
        action_tool_mode=config.get("action_tool_mode"),
    )
    try:
        response = model.generate(
            system=case["executor_system"],
            user=case["executor_user"],
            max_tokens=80,
            action_ids=tuple(action["id"] for action in task["actions"]),
        )
        return {
            "model_slug": slug,
            "model_id": config["model_id"],
            "region": config["region"],
            "response_mode": (
                "auto_action_tool"
                if config.get("action_tool_mode") == "auto"
                else (
                    "forced_action_tool"
                    if config["force_action_tool"]
                    else "json_text"
                )
            ),
            "status": "pass",
            "response_sha256": sha256_text(response.text),
            "stop_reason": response.stop_reason,
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "latency_ms": response.latency_ms,
            "request_id": response.request_id,
            "attempts": response.attempts,
            "attempt_errors": list(response.attempt_errors),
        }
    except Exception as exc:
        return {
            "model_slug": slug,
            "model_id": config["model_id"],
            "region": config["region"],
            "response_mode": (
                "auto_action_tool"
                if config.get("action_tool_mode") == "auto"
                else (
                    "forced_action_tool"
                    if config["force_action_tool"]
                    else "json_text"
                )
            ),
            "status": "fail",
            "error": f"{type(exc).__name__}: {exc}",
        }


def main() -> None:
    tasks = load_tasks(TASKS_PATH)
    task = tasks[0]
    case = next(
        row
        for row in build_study_a_cases([task])
        if row["condition"] == "study_a__source_single__true_update"
    )
    rows = []
    with ThreadPoolExecutor(max_workers=len(MODEL_CONFIGS)) as pool:
        futures = {
            pool.submit(run_one, slug, case, task): slug
            for slug in MODEL_CONFIGS
        }
        for future in as_completed(futures):
            rows.append(future.result())
    rows.sort(key=lambda row: row["model_slug"])
    report = {
        "evidence_type": "excluded_transport_response_preflight",
        "excluded_from_formal_analysis": True,
        "provider_calls": len(rows),
        "timestamp_utc": utc_now(),
        "case_id": f"{task['id']}::{case['condition']}",
        "models": rows,
        "passed": sum(row["status"] == "pass" for row in rows),
        "failed": sum(row["status"] == "fail" for row in rows),
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    if report["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
