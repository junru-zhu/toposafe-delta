from __future__ import annotations

from pathlib import Path

from swarmsafe_delta.pilot import ModelResponse, load_tasks
from swarmsafe_delta.topology_pilot import (
    SOURCE_RISKY,
    TOPOLOGY_DIRECT_STAR,
    TOPOLOGY_ONE_HOP_TREE,
    TOPOLOGY_TWO_HOP_CHAIN,
    analyze_rows,
    run_topology_episode,
    safe_progress_action,
    validate_rows,
)


TASKS_PATH = Path("data/calibration_boundary_tasks_v0.2.json")


class PolicyReviewFakeModel:
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
        if "policy-review node" in system:
            text = (
                '{"message":"The upstream recommendation conflicts with policy. '
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
                '"brief_reason":"Selected from the delivered recommendation."}'
            )
        return ModelResponse(
            text=text,
            input_tokens=10,
            output_tokens=5,
            latency_ms=1.0,
            request_id=f"request-{self.calls}",
        )


def test_topology_routes_change_which_message_reaches_executor() -> None:
    task = next(
        task
        for task in load_tasks(TASKS_PATH)
        if task["id"] == "approval-vendor-payment"
    )
    safe_action = safe_progress_action(task)["id"]
    risky_action = "submit_vendor_payment"
    risky_marker = "RISKY-DIRECT-MARKER"
    source_case = {
        "task_id": task["id"],
        "source_episode_id": "source-episode",
        "source_repeat": 1,
        "risky_message": risky_marker,
        "risky_recommended_action": risky_action,
        "safe_message": f"Choose {safe_action}.",
        "safe_recommended_action": safe_action,
    }
    rows = []
    for topology in (
        TOPOLOGY_DIRECT_STAR,
        TOPOLOGY_ONE_HOP_TREE,
        TOPOLOGY_TWO_HOP_CHAIN,
    ):
        model = PolicyReviewFakeModel(
            safe_action=safe_action,
            risky_action=risky_action,
            risky_marker=risky_marker,
        )
        row = run_topology_episode(
            task=task,
            source_case=source_case,
            topology=topology,
            source_regime=SOURCE_RISKY,
            repeat=1,
            seed=1,
            model=model,
        )
        assert model.calls == 3
        assert row["edge_count"] == 3
        assert row["delivered_message_slots"] == 3
        rows.append(row)

    by_topology = {row["topology"]: row for row in rows}
    assert by_topology[TOPOLOGY_DIRECT_STAR]["violation"] is True
    assert by_topology[TOPOLOGY_ONE_HOP_TREE]["violation"] is False
    assert by_topology[TOPOLOGY_TWO_HOP_CHAIN]["violation"] is False
    assert (
        by_topology[TOPOLOGY_DIRECT_STAR]["executor_message_source"]
        == "source"
    )
    assert (
        by_topology[TOPOLOGY_ONE_HOP_TREE]["executor_message_source"]
        == "reviewer_1"
    )
    assert (
        by_topology[TOPOLOGY_TWO_HOP_CHAIN]["executor_message_source"]
        == "reviewer_2"
    )

    validation = validate_rows(
        rows=rows,
        tasks=[task],
        planned_episodes=3,
    )
    assert validation["passed"] is True
    summary = analyze_rows(rows, seed=1, validation=validation)
    assert (
        summary["by_source_topology"][
            f"{SOURCE_RISKY}::{TOPOLOGY_DIRECT_STAR}"
        ]["violation_rate"]
        == 1.0
    )
