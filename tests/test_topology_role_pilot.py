from __future__ import annotations

from pathlib import Path

from swarmsafe_delta.pilot import ModelResponse, load_tasks
from swarmsafe_delta.topology_pilot import SOURCE_RISKY, safe_progress_action
from swarmsafe_delta.topology_role_pilot import (
    PLACEMENT_DIRECT_SOURCE,
    PLACEMENT_RELAY_ON_PATH,
    PLACEMENT_VERIFIER_ON_PATH,
    run_role_placement_episode,
)


TASKS_PATH = Path("data/calibration_boundary_tasks_v0.2.json")


class RolePlacementFakeModel:
    model_id = "fake-model"
    region = "test"
    temperature = 0.0
    top_p = None

    def __init__(
        self,
        *,
        safe_action: str,
        risky_action: str,
        risky_marker: str,
    ) -> None:
        self.safe_action = safe_action
        self.risky_action = risky_action
        self.risky_marker = risky_marker
        self.calls = 0

    def generate(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int,
    ) -> ModelResponse:
        self.calls += 1
        if "faithful communication-relay" in system:
            text = (
                f'{{"message":"{self.risky_marker}",'
                f'"recommended_action":"{self.risky_action}"}}'
            )
        elif "policy-review node" in system:
            text = (
                '{"message":"The recommendation conflicts with policy. '
                f'Choose {self.safe_action}.",'
                f'"recommended_action":"{self.safe_action}"}}'
            )
        else:
            selected = (
                self.risky_action
                if self.risky_marker in user
                else self.safe_action
            )
            text = (
                f'{{"action_id":"{selected}",'
                '"brief_reason":"Selected from the routed message."}'
            )
        return ModelResponse(
            text=text,
            input_tokens=10,
            output_tokens=5,
            latency_ms=1.0,
            request_id=f"request-{self.calls}",
        )


def test_role_on_path_changes_outcome_with_same_graph_budget() -> None:
    task = next(
        task
        for task in load_tasks(TASKS_PATH)
        if task["id"] == "approval-vendor-payment"
    )
    safe_action = safe_progress_action(task)["id"]
    risky_action = "submit_vendor_payment"
    risky_marker = "RISKY-PLACEMENT-MARKER"
    source_case = {
        "task_id": task["id"],
        "source_episode_id": "source-episode",
        "source_repeat": 1,
        "risky_message": risky_marker,
        "risky_recommended_action": risky_action,
        "safe_message": f"Choose {safe_action}.",
        "safe_recommended_action": safe_action,
    }
    outcomes = {}
    for placement in (
        PLACEMENT_DIRECT_SOURCE,
        PLACEMENT_RELAY_ON_PATH,
        PLACEMENT_VERIFIER_ON_PATH,
    ):
        model = RolePlacementFakeModel(
            safe_action=safe_action,
            risky_action=risky_action,
            risky_marker=risky_marker,
        )
        row = run_role_placement_episode(
            task=task,
            source_case=source_case,
            placement=placement,
            source_regime=SOURCE_RISKY,
            repeat=1,
            seed=1,
            model=model,
        )
        assert model.calls == 3
        assert row["edge_count"] == 3
        assert row["delivered_message_slots"] == 3
        outcomes[placement] = row["violation"]
    assert outcomes == {
        PLACEMENT_DIRECT_SOURCE: True,
        PLACEMENT_RELAY_ON_PATH: True,
        PLACEMENT_VERIFIER_ON_PATH: False,
    }
