from pathlib import Path

from swarmsafe_delta.execution_topology_pilot import (
    AUTHORITY_REGIMES,
    CLAIM_TRUTHS,
    EXECUTION_HOLDERS,
    FORMAL_CASES_PER_MODEL,
    FORMAL_TASKS,
    apply_fail_closed_enforcement,
    build_cases,
    select_pilot_tasks,
    validate_package,
)
from swarmsafe_delta.pilot import load_tasks


SOURCE = Path(
    "experiments/TopoSafe-Delta-RuntimeEnforcement-v0.2/"
    "candidate_tasks.json"
)


def _tasks():
    return select_pilot_tasks(load_tasks(SOURCE))


def test_selection_and_factorial_balance():
    tasks = _tasks()
    cases = build_cases(tasks)
    assert len(tasks) == FORMAL_TASKS
    assert len(cases) == FORMAL_CASES_PER_MODEL
    assert validate_package(tasks, cases)["automatic_gate_passed"]
    assert {case["execution_holder"] for case in cases} == set(
        EXECUTION_HOLDERS
    )
    assert {case["authority_regime"] for case in cases} == set(
        AUTHORITY_REGIMES
    )
    assert {case["claim_truth"] for case in cases} == set(CLAIM_TRUTHS)


def test_holder_changes_only_system_role_and_capability_assignment():
    cases = build_cases(_tasks())
    group = [
        case
        for case in cases
        if case["task_id"] == cases[0]["task_id"]
        and case["authority_regime"] == cases[0]["authority_regime"]
        and case["claim_truth"] == cases[0]["claim_truth"]
    ]
    assert len(group) == 4
    assert len({case["executor_user"] for case in group}) == 1
    assert len({case["message_body"] for case in group}) == 1
    assert len({case["provenance_metadata"] for case in group}) == 1
    assert len({case["executor_system"] for case in group}) == 4


def test_fail_closed_gate_blocks_invalid_protected_action():
    tasks = _tasks()
    task = tasks[0]
    cases = build_cases(tasks)
    invalid = next(
        case
        for case in cases
        if case["task_id"] == task["id"]
        and case["claim_truth"] == "false_update"
    )
    result = apply_fail_closed_enforcement(
        task=task,
        case=invalid,
        selected_action=invalid["protected_action_id"],
    )
    assert result["enforcement_blocked"]
    assert not result["protected_action_executed"]
    assert not result["executed_violation"]


def test_valid_proof_allows_protected_action():
    tasks = _tasks()
    task = tasks[0]
    cases = build_cases(tasks)
    valid = next(
        case
        for case in cases
        if case["task_id"] == task["id"]
        and case["claim_truth"] == "true_update"
    )
    result = apply_fail_closed_enforcement(
        task=task,
        case=valid,
        selected_action=valid["protected_action_id"],
    )
    assert not result["enforcement_blocked"]
    assert result["protected_action_executed"]
    assert not result["executed_violation"]
