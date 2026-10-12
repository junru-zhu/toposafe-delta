from __future__ import annotations

import json
from pathlib import Path

from swarmsafe_delta.authority_placement import AuthorityModelResponse
from swarmsafe_delta.matched_communication_topology import (
    CASES_PER_MODEL,
    FORMAL_CALLS,
    TOPOLOGY_IDS,
    build_cases,
    graph_contract_report,
    run_episode,
    validate_case_contracts,
    validate_rows,
)
from swarmsafe_delta.pilot import load_tasks


TASKS_PATH = Path(
    "experiments/TopoSafe-Delta-AuthorityComposition-v0.2/"
    "candidate_tasks.json"
)
DESIGN_PATH = Path(
    "experiments/TopoSafe-Delta-MatchedCommunication-v0.1/"
    "design_spec.json"
)


class SelectedActionFakeModel:
    model_id = "fake-model"
    region = "test"
    temperature = 0.0
    top_p = None
    force_action_tool = False
    action_tool_mode = None

    def __init__(self, action_id: str) -> None:
        self.action_id = action_id

    def generate(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int,
        action_ids: tuple[str, ...],
    ) -> AuthorityModelResponse:
        assert self.action_id in action_ids
        return AuthorityModelResponse(
            text=f'{{"action_id":"{self.action_id}"}}',
            input_tokens=100,
            output_tokens=20,
            latency_ms=1.0,
            request_id="request-1",
            attempts=1,
            attempt_errors=(),
            stop_reason="end_turn",
        )


def package():
    tasks = load_tasks(TASKS_PATH)
    cases = build_cases(tasks)
    return tasks, cases


def test_graphs_are_matched_and_structurally_distinct() -> None:
    report = graph_contract_report()
    assert report["passed"] is True
    metrics = report["topologies"]
    assert set(metrics) == set(TOPOLOGY_IDS)
    assert {row["nodes"] for row in metrics.values()} == {6}
    assert {row["edges"] for row in metrics.values()} == {6}
    assert {
        row["source_executor_distance"] for row in metrics.values()
    } == {1, 3, 4, 5}
    assert {
        row["edge_disjoint_routes"] for row in metrics.values()
    } == {1, 2}


def test_case_matrix_matches_frozen_call_budget() -> None:
    tasks, cases = package()
    report = validate_case_contracts(tasks, cases)
    assert report["passed"] is True
    assert len(cases) == CASES_PER_MODEL == 3_120
    assert len(cases) * 4 == FORMAL_CALLS == 12_480
    assert set(report["role_rotation_counts"].values()) == {20}


def test_topology_prompts_are_length_matched_with_identical_claims() -> None:
    _, cases = package()
    task_id = cases[0]["task_id"]
    selected = [
        case
        for case in cases
        if case["task_id"] == task_id
        and not case["is_control"]
        and case["authority_regime"] == "verifier_single"
        and case["claim_truth"] == "false_update"
    ]
    assert len(selected) == 4
    assert len({len(case["executor_user"]) for case in selected}) == 1
    assert len({case["message_body"] for case in selected}) == 1
    assert len({case["provenance_metadata"] for case in selected}) == 1


def test_fail_closed_gate_blocks_invalid_proof_execution() -> None:
    tasks, cases = package()
    case = next(
        case
        for case in cases
        if not case["is_control"]
        and case["authority_regime"] == "source_verifier_sod"
        and case["claim_truth"] == "false_update"
    )
    task = next(task for task in tasks if task["id"] == case["task_id"])
    row = run_episode(
        task=task,
        case=case,
        model=SelectedActionFakeModel(case["protected_action_id"]),
        schedule_seed=1,
        max_output_tokens=200,
    )
    assert row["protected_action_selected"] is True
    assert row["advisory_violation"] is True
    assert row["runtime_gate_blocked"] is True
    assert row["executed_violation"] is False
    report = validate_rows(
        rows=[row],
        tasks=[task],
        cases=[case],
        max_attempts=3,
        max_output_tokens=200,
        require_responsiveness=False,
    )
    assert report["passed"] is True
    assert report["invalid_proof_executions"] == []


def test_design_spec_has_no_human_review_and_zero_completed_calls() -> None:
    design = json.loads(DESIGN_PATH.read_text())
    assert design["provider_calls_completed"] == 0
    assert design["human_review_required"] is False
    assert design["human_review_used_as_evidence"] is False
    assert design["factorial"]["formal_calls"] == FORMAL_CALLS
