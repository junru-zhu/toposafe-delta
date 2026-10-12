from pathlib import Path

from swarmsafe_delta.authority_placement import AuthorityModelResponse
from swarmsafe_delta.pilot import load_tasks
from swarmsafe_delta.runtime_enforcement import (
    gate_replay_row,
    recovery_case,
    run_recovery_episode,
)


class SafeRecoveryModel:
    model_id = "fake-model"
    region = "test"
    temperature = 0.0
    top_p = None
    force_action_tool = False

    def __init__(self, action_id: str) -> None:
        self.action_id = action_id

    def generate(self, **kwargs) -> AuthorityModelResponse:
        return AuthorityModelResponse(
            text=f'{{"action_id":"{self.action_id}"}}',
            input_tokens=10,
            output_tokens=3,
            latency_ms=1.0,
            request_id="request-1",
            attempts=1,
            attempt_errors=(),
            stop_reason="end_turn",
        )


def source_row(task, *, proof_valid: bool) -> dict:
    return {
        "episode_id": "source-episode",
        "task_id": task["id"],
        "policy_family": task["policy_family"],
        "authority_regime": "source_verifier_sod",
        "authority_cut": 2,
        "claim_truth": "false_update",
        "compromised_budget": 1,
        "proof_valid": proof_valid,
        "selected_action": task["actions"][1]["id"],
        "protected_action_id": task["actions"][1]["id"],
        "safe_action_id": task["actions"][0]["id"],
        "protected_action_selected": True,
        "violation": True,
        "task_success": True,
        "safe_progress": False,
        "provider_error": None,
        "malformed": False,
        "truncated": False,
        "executor_snapshot_state": task["initial_state"],
        "current_ground_truth_state": task["initial_state"],
        "final_state": {
            **task["initial_state"],
            "protected_action_executed": True,
        },
    }


def test_gate_blocks_invalid_proof_protected_action() -> None:
    task = load_tasks(
        Path(
            "experiments/TopoSafe-Delta-AuthorityComposition-v0.2/"
            "candidate_tasks.json"
        )
    )[0]
    replay = gate_replay_row(
        task=task,
        source_row=source_row(task, proof_valid=False),
        model_slug="fake",
        source_study="study_a",
        source_model_valid=True,
    )
    assert replay["runtime_gate_blocked"] is True
    assert replay["gate_only_violation"] is False
    assert replay["requires_recovery"] is True


def test_recovery_safe_action_executes_without_violation() -> None:
    task = load_tasks(
        Path(
            "experiments/TopoSafe-Delta-AuthorityComposition-v0.2/"
            "candidate_tasks.json"
        )
    )[0]
    source = source_row(task, proof_valid=False)
    replay = gate_replay_row(
        task=task,
        source_row=source,
        model_slug="fake",
        source_study="study_a",
        source_model_valid=True,
    )
    case = recovery_case(task=task, source_row=source, replay=replay)
    row = run_recovery_episode(
        task=task,
        case=case,
        model=SafeRecoveryModel(case["safe_action_id"]),
        max_output_tokens=20,
        schedule_seed=1,
    )
    assert row["recovery_safe_progress"] is True
    assert row["runtime_gate_blocked_again"] is False
    assert row["executed_violation"] is False
