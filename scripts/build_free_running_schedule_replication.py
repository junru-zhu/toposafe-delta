#!/usr/bin/env python3
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from swarmsafe_delta.free_running_schedule_replication import (
    EXPERIMENT_ID,
    PARENT_EXPERIMENT_ID,
    RESULT_STATUS,
    SCHEDULE_SEED,
    STUDY_ID,
    activate,
)
from swarmsafe_delta.pilot import canonical_json, load_tasks, sha256_file
from swarmsafe_delta.topology_pilot import sha256_text


activate()

from swarmsafe_delta.free_running_communication import (  # noqa: E402
    FORMAL_ASSIGNED_MODEL_CALLS,
    FORMAL_EPISODES,
    validate_case_contracts,
)


ROOT = Path(__file__).resolve().parent.parent
PACKAGE = (
    ROOT / "experiments/TopoSafe-Delta-FreeRunningScheduleReplication-v0.1"
)
PARENT = ROOT / "experiments/TopoSafe-Delta-FreeRunningCommunication-v0.3"


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def prompt_inventory(cases: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "episode_id": f"{case['task_id']}::{case['condition']}",
            "source_message_sha256": sha256_text(case["source_message"]),
            "source_proof_sha256": sha256_text(
                canonical_json(case["source_proof"])
            ),
            "delivery_schedule_sha256": case["delivery_schedule_sha256"],
            "topology_metadata_sha256": case["topology_metadata_sha256"],
        }
        for case in cases
    ]


def main() -> None:
    parent_manifest_path = PARENT / "manifest.json"
    parent_validation_path = PARENT / "models/validation_report.json"
    parent_tasks_path = PARENT / "candidate_tasks.json"
    parent_cases_path = PARENT / "cases.json"
    parent_manifest = json.loads(parent_manifest_path.read_text())
    parent_validation = json.loads(parent_validation_path.read_text())
    tasks = load_tasks(parent_tasks_path)
    parent_cases = json.loads(parent_cases_path.read_text())
    cases = []
    for source in parent_cases:
        case = deepcopy(source)
        case["study"] = STUDY_ID
        case["result_status"] = RESULT_STATUS
        cases.append(case)

    contracts = validate_case_contracts(tasks, cases)
    errors = list(contracts["errors"])
    if parent_manifest.get("experiment_id") != PARENT_EXPERIMENT_ID:
        errors.append("parent experiment ID mismatch")
    if parent_manifest.get("status") != "frozen_pre_run":
        errors.append("parent manifest is not frozen")
    if parent_validation.get("passed") is not True:
        errors.append("parent four-model validation did not pass")
    if parent_manifest.get("schedule_seed") == SCHEDULE_SEED:
        errors.append("replication schedule seed equals the parent seed")
    allowed_case_differences = {"study", "result_status"}
    for parent_case, case in zip(parent_cases, cases):
        parent_core = {
            key: value
            for key, value in parent_case.items()
            if key not in allowed_case_differences
        }
        case_core = {
            key: value
            for key, value in case.items()
            if key not in allowed_case_differences
        }
        if parent_core != case_core:
            errors.append(
                f"{case['task_id']}::{case['condition']}:case mismatch"
            )
    inventory_sha256 = sha256_text(canonical_json(prompt_inventory(cases)))
    if inventory_sha256 != parent_manifest.get("prompt_inventory_sha256"):
        errors.append("prompt inventory differs from the parent B2 run")

    write_json(PACKAGE / "candidate_tasks.json", tasks)
    write_json(PACKAGE / "cases.json", cases)
    if sha256_file(PACKAGE / "candidate_tasks.json") != sha256_file(
        parent_tasks_path
    ):
        errors.append("candidate-task bytes differ from the parent B2 run")

    report = {
        "experiment_id": EXPERIMENT_ID,
        "parent_experiment_id": PARENT_EXPERIMENT_ID,
        "status": (
            "automatic_gate_passed"
            if not errors
            else "automatic_gate_failed"
        ),
        "automatic_gate_passed": not errors,
        "changed_factor": "schedule_seed_and_resulting_execution_order",
        "parent_schedule_seed": parent_manifest["schedule_seed"],
        "replication_schedule_seed": SCHEDULE_SEED,
        "prompt_inventory_sha256": inventory_sha256,
        "parent_prompt_inventory_sha256": parent_manifest[
            "prompt_inventory_sha256"
        ],
        "candidate_tasks": len(tasks),
        "episodes_per_model": len(cases),
        "formal_episodes": FORMAL_EPISODES,
        "formal_assigned_model_calls": FORMAL_ASSIGNED_MODEL_CALLS,
        "case_contracts": contracts,
        "human_review_required": False,
        "human_review_used_as_evidence": False,
        "manual_case_selection": False,
        "errors": errors,
    }
    write_json(PACKAGE / "task_validation.json", report)
    summary = {
        "experiment_id": EXPERIMENT_ID,
        "parent_experiment_id": PARENT_EXPERIMENT_ID,
        "status": report["status"],
        "formal_tasks": len(tasks),
        "episodes_per_model": len(cases),
        "formal_episodes": FORMAL_EPISODES,
        "formal_assigned_model_calls": FORMAL_ASSIGNED_MODEL_CALLS,
        "candidate_tasks_sha256": sha256_file(
            PACKAGE / "candidate_tasks.json"
        ),
        "cases_sha256": sha256_file(PACKAGE / "cases.json"),
        "prompt_inventory_sha256": inventory_sha256,
        "human_review_required": False,
        "human_review_used_as_evidence": False,
    }
    write_json(PACKAGE / "package_summary.json", summary)
    print(canonical_json(summary))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
