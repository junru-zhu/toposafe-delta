from pathlib import Path

from swarmsafe_delta.authority_task_construction import (
    build_tasks,
    load_catalog,
)
from swarmsafe_delta.runtime_enforcement_factorial import (
    FORMAL_INITIAL_CALLS,
    MAX_RECOVERY_CALLS,
    build_gate_rows_and_recovery_cases,
    build_initial_cases,
    validate_fresh_task_package,
)
from swarmsafe_delta.pilot import load_tasks


CATALOG = Path(
    "data/toposafe_runtime_enforcement_task_catalog_v0.2.json"
)
PRIOR_CATALOG = Path("data/toposafe_authority_task_catalog_v0.1.json")
PRIOR_TASKS = Path(
    "experiments/TopoSafe-Delta-AuthorityComposition-v0.2/"
    "candidate_tasks.json"
)
DEVELOPMENT_TASKS = Path("data/authority_placement_tasks_v1.json")


def fresh_package():
    catalog = load_catalog(CATALOG)
    tasks = build_tasks(catalog)
    validation = validate_fresh_task_package(
        catalog=catalog,
        tasks=tasks,
        prior_catalog=load_catalog(PRIOR_CATALOG),
        prior_tasks=[
            *load_tasks(PRIOR_TASKS),
            *load_tasks(DEVELOPMENT_TASKS),
        ],
    )
    return tasks, validation


def test_fresh_task_package_is_balanced_and_disjoint() -> None:
    tasks, validation = fresh_package()
    assert validation["automatic_gate_passed"] is True
    assert validation["candidate_tasks"] == 48
    assert validation["prior_task_overlap"] == []
    assert validation["family_domain_cells"] == 24
    assert set(validation["domain_counts"].values()) == {8}


def test_initial_factorial_and_recovery_ceiling_match_design() -> None:
    tasks, _ = fresh_package()
    cases = build_initial_cases(tasks)
    assert len(cases) == 48 * 14
    assert len(cases) * 4 == FORMAL_INITIAL_CALLS == 2688
    invalid_false = [
        case
        for case in cases
        if not case["is_control"]
        and case["claim_truth"] == "false_update"
        and not case["proof_valid"]
    ]
    assert len(invalid_false) == 48 * 5
    assert len(invalid_false) * 4 == MAX_RECOVERY_CALLS == 960


def test_runtime_gate_triggers_only_for_invalid_protected_action() -> None:
    tasks, _ = fresh_package()
    task = tasks[0]
    cases = [
        case
        for case in build_initial_cases([task])
        if not case["is_control"]
    ]
    invalid = next(case for case in cases if not case["proof_valid"])
    valid = next(
        case
        for case in cases
        if case["claim_truth"] == "false_update" and case["proof_valid"]
    )

    def row(case):
        return {
            **case,
            "episode_id": f"{task['id']}::{case['condition']}",
            "task_id": task["id"],
            "policy_family": task["policy_family"],
            "domain": task["domain"],
            "selected_action": case["protected_action_id"],
            "protected_action_selected": True,
            "violation": True,
            "task_success": True,
            "provider_error": None,
            "malformed": False,
            "truncated": False,
            "final_state": {
                **case["current_ground_truth_state"],
                "protected_action_executed": True,
            },
        }

    gate_rows, recoveries = build_gate_rows_and_recovery_cases(
        tasks=[task],
        initial_rows=[
            ("fake-model", True, row(invalid)),
            ("fake-model", True, row(valid)),
        ],
    )
    assert gate_rows[0]["runtime_gate_blocked"] is True
    assert gate_rows[0]["gate_only_violation"] is False
    assert gate_rows[1]["runtime_gate_blocked"] is False
    assert len(recoveries) == 1
    assert recoveries[0]["proof_valid"] is False
