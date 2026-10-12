from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from swarmsafe_delta.authority_mechanism_ablations import (
    ABLATION_IDS,
    FORMAL_CALLS,
    build_cases,
    run_jobs,
    select_tasks,
    validate_case_contracts,
    validate_rows,
)
from swarmsafe_delta.authority_placement import AuthorityModelResponse
from swarmsafe_delta.pilot import load_tasks
from scripts.analyze_authority_mechanism_ablations import (
    paired_effect,
    parent_executed_violation,
)


TASKS_PATH = Path(
    "experiments/TopoSafe-Delta-RuntimeEnforcement-v0.2/"
    "candidate_tasks.json"
)
DESIGN_PATH = Path(
    "experiments/TopoSafe-Delta-AuthorityMechanismAblations-v0.1/"
    "design_spec.json"
)


class ProtectedActionFakeModel:
    model_id = "fake-model"
    region = "test"
    temperature = 0.0
    top_p = None
    force_action_tool = False
    action_tool_mode = None

    def generate(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int,
        action_ids: tuple[str, ...],
    ) -> AuthorityModelResponse:
        protected = next(
            action_id
            for action_id in action_ids
            if action_id != action_ids[0] and action_id != "stop_without_progress"
        )
        return AuthorityModelResponse(
            text=json.dumps({"action_id": protected}),
            input_tokens=100,
            output_tokens=20,
            latency_ms=1.0,
            request_id="request-1",
            attempts=1,
            attempt_errors=(),
            stop_reason="end_turn",
        )


def package():
    parent_tasks = load_tasks(TASKS_PATH)
    selected = select_tasks(parent_tasks)
    cases = build_cases(parent_tasks)
    return selected, cases


def test_task_selection_and_call_accounting() -> None:
    tasks, cases = package()
    assert len(tasks) == 30
    assert len(cases) == 300
    assert FORMAL_CALLS == 1_200
    assert Counter(task["domain"] for task in tasks) == {
        "access_account": 5,
        "customer_operations": 5,
        "data_governance": 5,
        "incident_response": 5,
        "procurement_payment": 5,
        "software_delivery": 5,
    }
    assert Counter(case["ablation_id"] for case in cases) == {
        ablation_id: 30 for ablation_id in ABLATION_IDS
    }


def test_case_contracts_and_expected_proof_validity() -> None:
    tasks, cases = package()
    report = validate_case_contracts(tasks, cases)
    assert report["passed"] is True
    validity = {
        ablation_id: {
            case["proof_valid"]
            for case in cases
            if case["ablation_id"] == ablation_id
        }
        for ablation_id in ABLATION_IDS
    }
    assert validity["swap_source_verifier_identities"] == {True}
    assert validity["randomize_authority_labels"] == {True}
    assert all(
        values == {False}
        for ablation_id, values in validity.items()
        if ablation_id not in {
            "swap_source_verifier_identities",
            "randomize_authority_labels",
        }
    )


def test_duplicate_principal_does_not_satisfy_quorum() -> None:
    _, cases = package()
    case = next(
        row
        for row in cases
        if row["ablation_id"] == "duplicate_same_principal"
    )
    proof = json.loads(case["provenance_metadata"])
    assert sum(share["credential_bit"] for share in proof["shares"]) == 2
    assert len(
        {
            share["principal_id"]
            for share in proof["shares"]
            if share["credential_bit"]
        }
    ) == 1
    assert case["proof_valid"] is False


def test_invalid_proof_is_blocked_after_advisory_selection(tmp_path) -> None:
    tasks, cases = package()
    case = next(
        row
        for row in cases
        if row["ablation_id"] == "remove_one_quorum_share"
    )
    task = next(row for row in tasks if row["id"] == case["task_id"])
    rows = run_jobs(
        tasks=[task],
        cases=[case],
        model=ProtectedActionFakeModel(),
        workers=1,
        seed=1,
        max_output_tokens=200,
        raw_path=tmp_path / "episodes.jsonl",
    )
    assert rows[0]["protected_action_selected"] is True
    assert rows[0]["runtime_gate_blocked"] is True
    assert rows[0]["executed_violation"] is False
    validation = validate_rows(
        rows=rows,
        tasks=[task],
        cases=[case],
        max_attempts=3,
        max_output_tokens=200,
        parent_model_gate_passed=True,
    )
    assert validation["passed"] is True


def test_design_excludes_human_review() -> None:
    design = json.loads(DESIGN_PATH.read_text())
    assert design["provider_calls_completed"] == 0
    assert design["human_review_required"] is False
    assert design["human_review_used_as_evidence"] is False
    assert design["factorial"]["formal_calls"] == 1_200


def test_parent_runtime_gate_reconstruction() -> None:
    assert parent_executed_violation(
        {"violation": True, "proof_valid": True}
    )
    assert not parent_executed_violation(
        {"violation": True, "proof_valid": False}
    )
    assert not parent_executed_violation(
        {"violation": False, "proof_valid": True}
    )


def test_paired_effect_uses_only_common_tasks() -> None:
    target = {
        "task-1": {"outcome": True},
        "task-2": {"outcome": False},
        "target-only": {"outcome": True},
    }
    reference = {
        "task-1": {"outcome": False},
        "task-2": {"outcome": False},
        "reference-only": {"outcome": True},
    }
    effect = paired_effect(
        target,
        reference,
        field="outcome",
        reference_field="outcome",
        seed=1,
    )
    assert effect["paired_tasks"] == 2
    assert effect["estimate"] == 0.5
