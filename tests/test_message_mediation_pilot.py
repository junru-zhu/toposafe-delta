from __future__ import annotations

from pathlib import Path

from swarmsafe_delta.message_mediation_pilot import (
    CONDITION_DIRECT_ORIGINAL,
    CONDITION_HIDDEN_RELAY_IDENTICAL,
    CONDITION_RELAY_PARAPHRASE,
    CONDITION_RELAY_VERBATIM,
    CONDITION_SOURCE_PARAPHRASE,
    CONDITION_VERIFIER_REWRITE,
    build_message_bank,
    run_message_mediation_episode,
)
from swarmsafe_delta.pilot import ModelResponse, load_tasks


TASKS_PATH = Path("data/calibration_boundary_tasks_v0.2.json")


class MessageMediationFakeModel:
    model_id = "fake-model"
    region = "test"
    temperature = 0.0
    top_p = None

    def __init__(
        self,
        *,
        safe_action: str,
        risky_action: str,
    ) -> None:
        self.safe_action = safe_action
        self.risky_action = risky_action
        self.calls = []

    def generate(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int,
    ) -> ModelResponse:
        self.calls.append((system, user))
        selected = (
            self.safe_action
            if "VERIFIER-SAFE" in user
            else self.risky_action
        )
        return ModelResponse(
            text=(
                f'{{"action_id":"{selected}",'
                '"brief_reason":"Selected from delivered context."}'
            ),
            input_tokens=10,
            output_tokens=5,
            latency_ms=1.0,
            request_id=f"request-{len(self.calls)}",
        )


def test_build_message_bank_uses_frozen_direct_repeat() -> None:
    role_rows = [
        {
            "task_id": "task-1",
            "source_regime": "risky",
            "placement": "direct_source",
            "repeat": 1,
            "source_episode_id": "source-1",
            "episode_id": "role-1",
            "source_message": "ORIGINAL",
            "source_recommended_action": "risky",
            "relay": {
                "message": "PARAPHRASE",
                "recommended_action": "risky",
                "recommended_action_violation": True,
            },
            "verifier": {
                "message": "VERIFIER-SAFE",
                "recommended_action": "safe",
                "recommended_action_violation": False,
            },
        }
    ]
    bank = build_message_bank(
        role_rows,
        task_ids=["task-1"],
        source_regimes=["risky"],
    )
    assert bank == [
        {
            "task_id": "task-1",
            "source_regime": "risky",
            "source_episode_id": "source-1",
            "role_episode_id": "role-1",
            "source_message": "ORIGINAL",
            "source_recommended_action": "risky",
            "paraphrase_message": "PARAPHRASE",
            "paraphrase_recommended_action": "risky",
            "paraphrase_recommended_action_violation": True,
            "verifier_message": "VERIFIER-SAFE",
            "verifier_recommended_action": "safe",
            "verifier_recommended_action_violation": False,
        }
    ]


def test_message_mediation_conditions_isolate_visible_prompt_changes() -> None:
    task = next(
        task
        for task in load_tasks(TASKS_PATH)
        if task["id"] == "approval-vendor-payment"
    )
    safe_action = "request_payment_approval"
    risky_action = "submit_vendor_payment"
    bank_case = {
        "task_id": task["id"],
        "source_regime": "risky",
        "source_episode_id": "source-episode",
        "role_episode_id": "role-episode",
        "source_message": "ORIGINAL-RISKY",
        "source_recommended_action": risky_action,
        "paraphrase_message": "PARAPHRASE-RISKY",
        "paraphrase_recommended_action": risky_action,
        "verifier_message": "VERIFIER-SAFE",
        "verifier_recommended_action": safe_action,
    }
    rows = {}
    for condition in (
        CONDITION_DIRECT_ORIGINAL,
        CONDITION_HIDDEN_RELAY_IDENTICAL,
        CONDITION_RELAY_VERBATIM,
        CONDITION_SOURCE_PARAPHRASE,
        CONDITION_RELAY_PARAPHRASE,
        CONDITION_VERIFIER_REWRITE,
    ):
        model = MessageMediationFakeModel(
            safe_action=safe_action,
            risky_action=risky_action,
        )
        rows[condition] = run_message_mediation_episode(
            task=task,
            bank_case=bank_case,
            condition=condition,
            repeat=1,
            seed=1,
            model=model,
        )
        assert len(model.calls) == 1

    direct = rows[CONDITION_DIRECT_ORIGINAL]
    hidden = rows[CONDITION_HIDDEN_RELAY_IDENTICAL]
    assert direct["executor_prompt_sha256"] == hidden["executor_prompt_sha256"]
    assert direct["route_edges"] != hidden["route_edges"]
    assert (
        rows[CONDITION_RELAY_VERBATIM]["delivered_message"]
        == direct["delivered_message"]
    )
    assert (
        rows[CONDITION_RELAY_VERBATIM]["provenance"]
        != direct["provenance"]
    )
    assert (
        rows[CONDITION_SOURCE_PARAPHRASE]["delivered_message"]
        == rows[CONDITION_RELAY_PARAPHRASE]["delivered_message"]
    )
    assert (
        rows[CONDITION_SOURCE_PARAPHRASE]["provenance"]
        != rows[CONDITION_RELAY_PARAPHRASE]["provenance"]
    )
    assert rows[CONDITION_DIRECT_ORIGINAL]["violation"] is True
    assert rows[CONDITION_VERIFIER_REWRITE]["violation"] is False

