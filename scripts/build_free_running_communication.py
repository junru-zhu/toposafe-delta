#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from swarmsafe_delta.authority_composition import select_threshold_tasks
from swarmsafe_delta.free_running_communication import (
    EPISODES_PER_MODEL,
    EXPERIMENT_ID,
    FORMAL_ASSIGNED_MODEL_CALLS,
    FORMAL_EPISODES,
    build_cases,
    validate_case_contracts,
)
from swarmsafe_delta.pilot import canonical_json, load_tasks, sha256_file
from swarmsafe_delta.topology_pilot import sha256_text


ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "experiments/TopoSafe-Delta-FreeRunningCommunication-v0.1"
PARENT = ROOT / "experiments/TopoSafe-Delta-AuthorityComposition-v0.2"
B1 = ROOT / "experiments/TopoSafe-Delta-MatchedCommunication-v0.1"


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parent_tasks_path = PARENT / "candidate_tasks.json"
    parent_validation_path = PARENT / "task_validation.json"
    b1_validation_path = B1 / "models/validation_report.json"
    all_tasks = load_tasks(parent_tasks_path)
    tasks = select_threshold_tasks(all_tasks)
    cases = build_cases(tasks)
    parent_validation = json.loads(parent_validation_path.read_text())
    b1_validation = json.loads(b1_validation_path.read_text())
    contracts = validate_case_contracts(tasks, cases)
    errors = list(contracts["errors"])
    if parent_validation.get("automatic_gate_passed") is not True:
        errors.append("parent automatic task validation did not pass")
    if parent_validation.get("human_review_required") is not False:
        errors.append("parent task package requires human review")
    if parent_validation.get("human_review_used_as_evidence") is not False:
        errors.append("parent task package uses human review as evidence")
    if b1_validation.get("passed") is not True:
        errors.append("B1 four-model validity report did not pass")
    report = {
        "experiment_id": EXPERIMENT_ID,
        "status": "automatic_gate_passed" if not errors else "automatic_gate_failed",
        "automatic_gate_passed": not errors,
        "human_review_required": False,
        "human_review_used_as_evidence": False,
        "manual_case_selection": False,
        "parent_task_file": str(parent_tasks_path.relative_to(ROOT)),
        "parent_task_file_sha256": sha256_file(parent_tasks_path),
        "parent_task_validation_sha256": sha256_file(
            parent_validation_path
        ),
        "b1_validation_sha256": sha256_file(b1_validation_path),
        "candidate_tasks": len(tasks),
        "candidate_tasks_canonical_sha256": sha256_text(
            canonical_json(tasks)
        ),
        "episodes_per_model": len(cases),
        "formal_episodes": FORMAL_EPISODES,
        "formal_assigned_model_calls": FORMAL_ASSIGNED_MODEL_CALLS,
        "case_contracts": contracts,
        "errors": errors,
    }
    write_json(PACKAGE / "candidate_tasks.json", tasks)
    write_json(PACKAGE / "cases.json", cases)
    write_json(PACKAGE / "task_validation.json", report)
    summary = {
        "experiment_id": EXPERIMENT_ID,
        "status": report["status"],
        "formal_tasks": len(tasks),
        "episodes_per_model": len(cases),
        "formal_episodes": FORMAL_EPISODES,
        "formal_assigned_model_calls": FORMAL_ASSIGNED_MODEL_CALLS,
        "candidate_tasks_sha256": sha256_file(
            PACKAGE / "candidate_tasks.json"
        ),
        "cases_sha256": sha256_file(PACKAGE / "cases.json"),
        "human_review_required": False,
        "human_review_used_as_evidence": False,
    }
    write_json(PACKAGE / "package_summary.json", summary)
    print(canonical_json(summary))
    if len(cases) != EPISODES_PER_MODEL or errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
