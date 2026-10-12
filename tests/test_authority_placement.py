from __future__ import annotations

from pathlib import Path

from swarmsafe_delta.authority_placement import (
    AUTHORITY_PLACEMENTS,
    CLAIM_TRUTHS,
    CREDENTIALS,
    AuthorityBedrockTextModel,
    AuthorityModelResponse,
    AuthorityProviderError,
    build_case,
    build_cases,
    factorial_condition_id,
    run_episode,
    run_jobs,
    task_gate_spec,
    validate_rows,
)
from swarmsafe_delta.pilot import load_tasks


TASKS = Path("data/authority_placement_tasks_v1.json")


class CredentialFakeModel:
    model_id = "fake-model"
    region = "test"
    temperature = 0.0
    top_p = None

    def __init__(self, *, protected_action: str, safe_action: str) -> None:
        self.protected_action = protected_action
        self.safe_action = safe_action

    def generate(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int,
        action_ids: tuple[str, ...],
    ) -> AuthorityModelResponse:
        selected = (
            self.protected_action
            if "credential_bit: 1" in user
            else self.safe_action
        )
        return AuthorityModelResponse(
            text=f'{{"action_id":"{selected}"}}',
            input_tokens=100,
            output_tokens=20,
            latency_ms=1.0,
            request_id="request-1",
            attempts=1,
            attempt_errors=(),
            stop_reason="end_turn",
        )


class ProviderErrorModel:
    model_id = "provider-error-model"
    region = "test"
    temperature = None
    top_p = None
    force_action_tool = False

    def generate(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int,
        action_ids: tuple[str, ...],
    ) -> AuthorityModelResponse:
        raise AuthorityProviderError(
            ["CredentialError: one", "CredentialError: two"]
        )


class ToolUseFakeClient:
    def __init__(self) -> None:
        self.request = None

    def converse(self, **request):
        self.request = request
        return {
            "output": {
                "message": {
                    "content": [
                        {
                            "toolUse": {
                                "name": "choose_action",
                                "input": {"action_id": "safe_action"},
                            }
                        }
                    ]
                }
            },
            "usage": {"inputTokens": 10, "outputTokens": 3},
            "stopReason": "tool_use",
            "ResponseMetadata": {"RequestId": "request-tool"},
        }


def test_auto_action_tool_supplies_schema_without_forcing_tool_choice() -> None:
    model = AuthorityBedrockTextModel(
        model_id="fake-model",
        region="test",
        temperature=0.0,
        top_p=None,
        additional_model_request_fields=None,
        force_action_tool=False,
        max_attempts=1,
        connect_timeout_seconds=1,
        read_timeout_seconds=1,
        action_tool_mode="auto",
    )
    client = ToolUseFakeClient()
    model._local.client = client
    response = model.generate(
        system="Choose one action.",
        user="Available actions: safe_action",
        max_tokens=20,
        action_ids=("safe_action",),
    )
    assert client.request is not None
    assert "tools" in client.request["toolConfig"]
    assert "toolChoice" not in client.request["toolConfig"]
    assert response.text == '{"action_id":"safe_action"}'
    assert response.stop_reason == "tool_use"


def test_task_file_has_balanced_valid_gate_specs() -> None:
    tasks = load_tasks(TASKS)
    assert len(tasks) == 24
    counts = {}
    for task in tasks:
        counts[task["policy_family"]] = (
            counts.get(task["policy_family"], 0) + 1
        )
        gate = task_gate_spec(task)
        assert gate["protected_action_id"] != gate["safe_action_id"]
    assert set(counts.values()) == {6}


def test_truth_is_hidden_and_factorial_prompts_are_length_matched() -> None:
    task = load_tasks(TASKS)[0]
    prompt_lengths = set()
    message_bodies = set()
    for placement in AUTHORITY_PLACEMENTS:
        for credential in CREDENTIALS:
            cases = [
                build_case(
                    task,
                    condition=factorial_condition_id(
                        placement,
                        credential,
                        truth,
                    ),
                )
                for truth in CLAIM_TRUTHS
            ]
            assert cases[0]["executor_system"] == cases[1]["executor_system"]
            assert cases[0]["executor_user"] == cases[1]["executor_user"]
            for case in cases:
                prompt = (
                    f"{case['executor_system']}\n\n"
                    f"{case['executor_user']}"
                )
                prompt_lengths.add(len(prompt))
                message_bodies.add(case["message_body"])
    assert len(prompt_lengths) == 1
    assert len(message_bodies) == 1


def test_hidden_truth_changes_score_not_model_prompt() -> None:
    task = next(
        task
        for task in load_tasks(TASKS)
        if task["id"] == "approval-vendor-payment"
    )
    gate = task_gate_spec(task)
    model = CredentialFakeModel(
        protected_action=gate["protected_action_id"],
        safe_action=gate["safe_action_id"],
    )
    true_case = build_case(
        task,
        condition=factorial_condition_id(
            "verifier_authority",
            "platform_authenticated",
            "true_update",
        ),
    )
    false_case = build_case(
        task,
        condition=factorial_condition_id(
            "verifier_authority",
            "platform_authenticated",
            "false_update",
        ),
    )
    true_row = run_episode(
        task=task,
        case=true_case,
        model=model,
        schedule_seed=1,
        max_output_tokens=200,
    )
    false_row = run_episode(
        task=task,
        case=false_case,
        model=model,
        schedule_seed=2,
        max_output_tokens=200,
    )
    assert true_row["executor_prompt_sha256"] == (
        false_row["executor_prompt_sha256"]
    )
    assert true_row["violation"] is False
    assert false_row["violation"] is True


def test_validator_accepts_complete_fake_package() -> None:
    tasks = load_tasks(TASKS)[:2]
    cases = build_cases(tasks)
    rows = []
    for index, case in enumerate(cases):
        task = next(
            task for task in tasks if task["id"] == case["task_id"]
        )
        gate = task_gate_spec(task)
        model = CredentialFakeModel(
            protected_action=gate["protected_action_id"],
            safe_action=gate["safe_action_id"],
        )
        rows.append(
            run_episode(
                task=task,
                case=case,
                model=model,
                schedule_seed=index,
                max_output_tokens=200,
            )
        )
    validation = validate_rows(
        rows=rows,
        tasks=tasks,
        cases=cases,
        max_attempts=3,
        max_output_tokens=200,
    )
    assert validation["truth_prompt_mismatches"] == []
    assert validation["message_body_mismatches"] == []
    assert validation["control_failures"] == 0
    assert validation["passed"] is True


def test_resume_replaces_provider_error_without_duplicate_episode_id(
    tmp_path,
) -> None:
    task = load_tasks(TASKS)[0]
    case = build_case(task, condition="snapshot_only_false")
    raw_path = tmp_path / "episodes.jsonl"
    failed = run_jobs(
        tasks=[task],
        cases=[{"task_id": task["id"], "policy_family": task["policy_family"], **case}],
        model=ProviderErrorModel(),
        workers=1,
        seed=1,
        max_output_tokens=200,
        raw_path=raw_path,
    )
    assert failed[0]["provider_error"]

    gate = task_gate_spec(task)
    recovered = run_jobs(
        tasks=[task],
        cases=[{"task_id": task["id"], "policy_family": task["policy_family"], **case}],
        model=CredentialFakeModel(
            protected_action=gate["protected_action_id"],
            safe_action=gate["safe_action_id"],
        ),
        workers=1,
        seed=1,
        max_output_tokens=200,
        raw_path=raw_path,
    )
    assert "provider_error" not in recovered[0]
    assert len(recovered[0]["resume_history"]) == 1
    assert len(raw_path.read_text(encoding="utf-8").splitlines()) == 1
