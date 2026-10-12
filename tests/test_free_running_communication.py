from __future__ import annotations

import json
from pathlib import Path

from swarmsafe_delta.authority_placement import AuthorityModelResponse
from swarmsafe_delta.free_running_communication import (
    EPISODES_PER_MODEL,
    FORMAL_ASSIGNED_MODEL_CALLS,
    FORMAL_EPISODES,
    MODEL_CALLS_PER_EPISODE,
    TOPOLOGY_IDS,
    build_cases,
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
    "experiments/TopoSafe-Delta-FreeRunningCommunication-v0.1/"
    "design_spec.json"
)


def response(text: str) -> AuthorityModelResponse:
    return AuthorityModelResponse(
        text=text,
        input_tokens=100,
        output_tokens=20,
        latency_ms=1.0,
        request_id="request-1",
        attempts=1,
        attempt_errors=(),
        stop_reason="end_turn",
    )


class EchoForwardModel:
    model_id = "fake-forward"
    region = "test"
    temperature = 0.0
    top_p = None

    def generate(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int,
        action_ids: tuple[str, ...],
    ) -> AuthorityModelResponse:
        message_line = next(
            line for line in user.splitlines() if line.startswith("message:")
        )
        message = json.loads(message_line.removeprefix("message:").strip())
        dropped = "drop_bit:1" in user
        return response(
            json.dumps(
                {
                    "message": message,
                    "keep_A": 1,
                    "keep_B": 1,
                    "keep_C": 1,
                    "keep_scope": 1,
                    "keep_freshness": 1,
                    "drop": int(dropped),
                }
            )
        )


class DropProofForwardModel(EchoForwardModel):
    def generate(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int,
        action_ids: tuple[str, ...],
    ) -> AuthorityModelResponse:
        base = json.loads(
            super().generate(
                system=system,
                user=user,
                max_tokens=max_tokens,
                action_ids=action_ids,
            ).text
        )
        base["keep_C"] = 0
        return response(json.dumps(base))


class SelectedActionModel:
    model_id = "fake-executor"
    region = "test"
    temperature = 0.0
    top_p = None

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
        return response(json.dumps({"action_id": self.action_id}))


def package():
    tasks = load_tasks(TASKS_PATH)
    cases = build_cases(tasks)
    selected_ids = {case["task_id"] for case in cases}
    selected = [task for task in tasks if task["id"] in selected_ids]
    return selected, cases


def test_b2_case_and_provider_call_accounting() -> None:
    tasks, cases = package()
    report = validate_case_contracts(tasks, cases)
    assert report["passed"] is True
    assert len(tasks) == 30
    assert len(cases) == EPISODES_PER_MODEL == 720
    assert FORMAL_EPISODES == 2_880
    assert MODEL_CALLS_PER_EPISODE == 7
    assert FORMAL_ASSIGNED_MODEL_CALLS == 20_160


def test_b2_schedules_have_six_calls_and_expected_active_hops() -> None:
    _, cases = package()
    expected = {"topo_A": 1, "topo_B": 3, "topo_C": 4, "topo_D": 5}
    for topology_id in TOPOLOGY_IDS:
        case = next(row for row in cases if row["topology_id"] == topology_id)
        assert len(case["delivery_schedule"]) == 6
        assert sum(
            row["active_path"] for row in case["delivery_schedule"]
        ) == expected[topology_id]


def test_b2_truth_pairs_share_source_message() -> None:
    _, cases = package()
    first = cases[0]
    pair = [
        row
        for row in cases
        if row["task_id"] == first["task_id"]
        and row["topology_id"] == first["topology_id"]
        and row["authority_regime"] == first["authority_regime"]
    ]
    assert len(pair) == 2
    assert len({row["source_message"] for row in pair}) == 1


def test_b2_episode_realizes_seven_calls_and_validates() -> None:
    tasks, cases = package()
    case = next(
        row
        for row in cases
        if row["topology_id"] == "topo_D"
        and row["authority_regime"] == "verifier_single"
        and row["claim_truth"] == "true_update"
    )
    task = next(row for row in tasks if row["id"] == case["task_id"])
    row = run_episode(
        task=task,
        case=case,
        forward_model=EchoForwardModel(),
        executor_model=SelectedActionModel(case["protected_action_id"]),
        schedule_seed=1,
    )
    assert row["realized_model_calls"] == 7
    assert len(row["propagation_calls"]) == 6
    assert row["final_proof_valid"] is True
    assert row["executed_violation"] is False
    report = validate_rows(
        rows=[row],
        tasks=[task],
        cases=[case],
        max_attempts=3,
        b1_model_control_gate_passed=True,
    )
    assert report["passed"] is True


def test_b2_proof_loss_cannot_be_resurrected_and_gate_blocks() -> None:
    tasks, cases = package()
    case = next(
        row
        for row in cases
        if row["topology_id"] == "topo_C"
        and row["authority_regime"] == "verifier_single"
        and row["claim_truth"] == "false_update"
    )
    task = next(row for row in tasks if row["id"] == case["task_id"])
    row = run_episode(
        task=task,
        case=case,
        forward_model=DropProofForwardModel(),
        executor_model=SelectedActionModel(case["protected_action_id"]),
        schedule_seed=1,
    )
    assert case["source_proof_valid"] is True
    assert row["final_proof_valid"] is False
    assert row["runtime_gate_blocked"] is True
    assert row["executed_violation"] is False
    assert all(
        call["downstream_envelope"]["share_bits"]["C"] == 0
        for call in row["propagation_calls"]
        if call["active_path"]
    )


def test_b2_design_has_no_human_review() -> None:
    design = json.loads(DESIGN_PATH.read_text())
    assert design["provider_calls_completed"] == 0
    assert design["human_review_required"] is False
    assert design["human_review_used_as_evidence"] is False
    assert design["formal_assigned_model_calls"] == 20_160
