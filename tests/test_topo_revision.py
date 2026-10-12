from __future__ import annotations

import json

from swarmsafe_delta.authority_placement import AuthorityModelResponse
from swarmsafe_delta.topo_revision_authority_cut import (
    POLICIES,
    build_proof,
    build_treatment_cases,
    computed_authority_cut,
    verify_proof,
)
from swarmsafe_delta.topo_revision_provenance import (
    PROVENANCE_BLOCK_CHARS,
    build_cases as build_e1_cases,
    provenance_block,
    verify_attestation,
)
from swarmsafe_delta.topo_revision_tasks import (
    E1_DOMAINS,
    E3_DOMAINS,
    build_e1_tasks,
    build_e2_tasks,
    build_e3_tasks,
    validate_tasks,
)
from swarmsafe_delta.topo_revision_workflow import (
    build_cases as build_e3_cases,
    run_episode as run_e3_episode,
)


class ProtectedFakeModel:
    model_id = "fake-executor"
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
        del system, user, max_tokens
        return AuthorityModelResponse(
            text=json.dumps({"action_id": action_ids[0]}),
            input_tokens=100,
            output_tokens=10,
            latency_ms=1.0,
            request_id="executor-request",
            attempts=1,
            attempt_errors=(),
            stop_reason="end_turn",
        )


class KeepForwardFakeModel:
    model_id = "fake-forwarder"
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
        del system, max_tokens, action_ids
        marker = "message:"
        message_line = next(
            line for line in user.splitlines() if line.startswith(marker)
        )
        encoded = message_line[len(marker) :].strip()
        try:
            message = json.loads(encoded)
        except json.JSONDecodeError:
            message = encoded.strip('" ')
        payload = {
            "message": message[:240],
            "keep_A": 1,
            "keep_B": 1,
            "keep_C": 1,
            "keep_scope": 1,
            "keep_freshness": 1,
            "drop": 0,
        }
        return AuthorityModelResponse(
            text=json.dumps(payload),
            input_tokens=120,
            output_tokens=30,
            latency_ms=1.0,
            request_id="forward-request",
            attempts=1,
            attempt_errors=(),
            stop_reason="end_turn",
        )


def test_revision_task_packages_are_balanced_and_varied() -> None:
    e1 = build_e1_tasks()
    e2 = build_e2_tasks()
    e3 = build_e3_tasks()
    assert validate_tasks(
        e1,
        expected_count=60,
        expected_domains=E1_DOMAINS,
        minimum_archetypes_per_domain=3,
    ) == []
    assert validate_tasks(
        e2,
        expected_count=80,
        expected_domains=E1_DOMAINS,
        minimum_archetypes_per_domain=3,
    ) == []
    assert validate_tasks(
        e3,
        expected_count=48,
        expected_domains=E3_DOMAINS,
        minimum_archetypes_per_domain=4,
    ) == []


def test_e1_hidden_state_is_absent_from_paired_prompts() -> None:
    task = build_e1_tasks()[0]
    cases = build_e1_cases([task])
    assert len(cases) == 10
    for treatment in ("P0", "P1", "P2", "P3", "P4"):
        pair = [case for case in cases if case["treatment"] == treatment]
        assert len(pair) == 2
        assert pair[0]["executor_prompt_sha256"] == pair[1][
            "executor_prompt_sha256"
        ]
        assert "claim_matches_authoritative_state" not in pair[0][
            "executor_user"
        ]


def test_e1_provenance_conditions_do_not_authorize_action() -> None:
    tasks = build_e1_tasks()
    for index, task in enumerate(tasks[:6]):
        for treatment in ("P0", "P1", "P2", "P3", "P4"):
            block, attestation, verification = provenance_block(
                task,
                treatment=treatment,
                task_index=index,
            )
            assert len(block) == PROVENANCE_BLOCK_CHARS
            assert verification["authorizes_action"] is False
            assert verify_attestation(task, attestation) == verification
        _, _, p2 = provenance_block(
            task,
            treatment="P2",
            task_index=index,
        )
        _, _, p3 = provenance_block(
            task,
            treatment="P3",
            task_index=index,
        )
        assert p2["usable_provenance"] is True
        assert p3["identity_verified"] is True
        assert p3["usable_provenance"] is False


def test_e2_authority_cut_and_duplicate_independence() -> None:
    task = build_e2_tasks()[0]
    for policy_id, policy in POLICIES.items():
        assert computed_authority_cut(policy_id) == policy.authority_cut
        below = build_proof(
            task,
            policy_id=policy_id,
            world_state="FALSE",
            compromised_budget=policy.authority_cut - 1,
        )
        at_cut = build_proof(
            task,
            policy_id=policy_id,
            world_state="FALSE",
            compromised_budget=policy.authority_cut,
        )
        assert below["verification"]["proof_valid"] is False
        assert at_cut["verification"]["proof_valid"] is True
    duplicate = build_proof(
        task,
        policy_id="A2",
        world_state="TRUE",
        compromised_budget=0,
    )
    duplicate["shares"] = [duplicate["shares"][0], duplicate["shares"][0]]
    assert verify_proof(task, duplicate)["proof_valid"] is False


def test_e2_treatment_case_count_and_binding() -> None:
    tasks = build_e2_tasks()
    cases = build_treatment_cases(tasks)
    assert len(cases) == 80 * 12
    assert all(
        case["proof_valid"]
        is (
            case["world_state"] == "TRUE"
            or case["compromised_budget"] >= case["authority_cut"]
        )
        for case in cases
    )


def test_e3_full_factorial_call_accounting() -> None:
    tasks = build_e3_tasks()
    cases = build_e3_cases(tasks)
    assert len(cases) == 48 * 24
    assert sum(case["assigned_model_calls"] for case in cases) == 48 * 64


def test_e3_gate_blocks_invalid_proof_but_ungated_path_commits() -> None:
    task = build_e3_tasks()[0]
    cases = build_e3_cases([task])
    base_filter = {
        "topology": "C1",
        "authorization_policy": "A2",
        "world_state": "FALSE",
    }
    gated = next(
        case
        for case in cases
        if all(case[key] == value for key, value in base_filter.items())
        and case["execution_policy"] == "E1"
    )
    ungated = next(
        case
        for case in cases
        if all(case[key] == value for key, value in base_filter.items())
        and case["execution_policy"] == "E0"
    )
    forwarder = KeepForwardFakeModel()
    executor = ProtectedFakeModel()
    gated_row = run_e3_episode(
        task=task,
        case=gated,
        forward_model=forwarder,
        executor_model=executor,
        model_slug="fake",
    )
    ungated_row = run_e3_episode(
        task=task,
        case=ungated,
        forward_model=forwarder,
        executor_model=executor,
        model_slug="fake",
    )
    assert gated_row["final_proof_valid"] is False
    assert gated_row["runtime_gate_blocked"] is True
    assert gated_row["false_state_committed_action"] is False
    assert ungated_row["policy_invalid_committed_action"] is True
    assert ungated_row["false_state_committed_action"] is True
