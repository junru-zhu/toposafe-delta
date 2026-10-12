from __future__ import annotations

import json
from pathlib import Path

from swarmsafe_delta.authority_composition import (
    AUTHORITY_REGIMES,
    CALL_BUDGET,
    build_study_a_cases,
    build_threshold_cases,
    build_proof,
    confirmatory_call_total,
    duplicate_same_principal_proof,
    render_executor_visible_proof,
    run_jobs,
    select_threshold_tasks,
    validate_design_spec,
    validate_rows,
)
from swarmsafe_delta.authority_placement import AuthorityModelResponse
from swarmsafe_delta.pilot import load_tasks


DESIGN_SPEC = Path(
    "experiments/TopoSafe-Delta-AuthorityComposition-v0.2/design_spec.json"
)
CANDIDATE_TASKS = Path(
    "experiments/TopoSafe-Delta-AuthorityComposition-v0.2/candidate_tasks.json"
)


class SafeActionFakeModel:
    model_id = "fake-model"
    region = "test"
    temperature = 0.0
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
        return AuthorityModelResponse(
            text=f'{{"action_id":"{action_ids[0]}"}}',
            input_tokens=100,
            output_tokens=20,
            latency_ms=1.0,
            request_id="request-1",
            attempts=1,
            attempt_errors=(),
            stop_reason="end_turn",
        )


def test_authority_cut_matches_minimum_compromise_threshold() -> None:
    for regime_id, regime in AUTHORITY_REGIMES.items():
        if regime.authority_cut is None:
            proof = build_proof(
                regime_id,
                claim_truth="false_update",
                compromised_budget=3,
            )
            assert proof["proof_valid"] is False
            continue
        below = build_proof(
            regime_id,
            claim_truth="false_update",
            compromised_budget=regime.authority_cut - 1,
        )
        at_cut = build_proof(
            regime_id,
            claim_truth="false_update",
            compromised_budget=regime.authority_cut,
        )
        assert below["proof_valid"] is False
        assert at_cut["proof_valid"] is True


def test_true_updates_have_valid_proofs_for_authenticated_regimes() -> None:
    for regime_id, regime in AUTHORITY_REGIMES.items():
        proof = build_proof(
            regime_id,
            claim_truth="true_update",
            compromised_budget=0,
        )
        assert proof["proof_valid"] is (regime.authority_cut is not None)


def test_duplicate_signatures_do_not_create_independent_quorum() -> None:
    proof = duplicate_same_principal_proof()
    assert sum(
        share["credential_bit"] for share in proof["shares"]
    ) == 2
    assert proof["proof_valid"] is False


def test_threshold_prompts_change_bits_without_changing_length() -> None:
    visible = [
        render_executor_visible_proof(
            build_proof(
                regime_id,
                claim_truth="false_update",
                compromised_budget=budget,
            )
        )
        for regime_id in (
            "verifier_single",
            "source_verifier_sod",
            "two_of_three_quorum",
        )
        for budget in (0, 1, 2)
    ]
    by_regime = [visible[index : index + 3] for index in range(0, 9, 3)]
    assert all(len({len(row) for row in group}) == 1 for group in by_regime)


def test_design_spec_and_call_budget_are_consistent() -> None:
    spec = json.loads(DESIGN_SPEC.read_text(encoding="utf-8"))
    assert validate_design_spec(spec) == []
    assert CALL_BUDGET["study_c_authority_cut_extension"] == 720
    assert CALL_BUDGET["study_c_targeted_mechanism_ablations"] == 1200
    assert confirmatory_call_total() == 26_880


def test_study_a_and_threshold_case_counts_match_call_budget() -> None:
    tasks = load_tasks(CANDIDATE_TASKS)
    study_a = build_study_a_cases(tasks)
    threshold = build_threshold_cases(tasks)
    assert len(study_a) == 120 * 14
    assert len(threshold) == 30 * 6
    assert len(study_a) * 4 == CALL_BUDGET[
        "study_a_authority_composition"
    ]
    assert len(threshold) * 4 == CALL_BUDGET[
        "study_c_authority_cut_extension"
    ]


def test_threshold_subset_is_unique_and_domain_balanced() -> None:
    selected = select_threshold_tasks(load_tasks(CANDIDATE_TASKS))
    assert len(selected) == len({task["id"] for task in selected}) == 30
    assert {
        domain: sum(task["domain"] == domain for task in selected)
        for domain in {task["domain"] for task in selected}
    } == {
        "access_account": 5,
        "customer_operations": 5,
        "data_governance": 5,
        "incident_response": 5,
        "procurement_payment": 5,
        "software_delivery": 5,
    }


def test_cut_two_false_proof_crosses_validity_at_c2() -> None:
    for regime_id in ("source_verifier_sod", "two_of_three_quorum"):
        below = build_proof(
            regime_id,
            claim_truth="false_update",
            compromised_budget=1,
        )
        at_cut = build_proof(
            regime_id,
            claim_truth="false_update",
            compromised_budget=2,
        )
        assert below["proof_valid"] is False
        assert at_cut["proof_valid"] is True


def test_composition_runner_enriches_rows_without_mutating_legacy_runner(
    tmp_path,
) -> None:
    task = load_tasks(CANDIDATE_TASKS)[0]
    case = build_study_a_cases([task])[0]
    raw_path = tmp_path / "episodes.jsonl"
    rows = run_jobs(
        tasks=[task],
        cases=[case],
        model=SafeActionFakeModel(),
        workers=1,
        seed=1,
        max_output_tokens=200,
        raw_path=raw_path,
    )
    assert rows[0]["study"] == "study_a_authority_composition"
    assert rows[0]["authority_regime"] == "unsigned"
    assert rows[0]["status"] == (
        "authority_composition_confirmatory_candidate"
    )
    validation = validate_rows(
        rows=rows,
        tasks=[task],
        cases=[case],
        max_attempts=3,
        max_output_tokens=200,
    )
    assert validation["passed"] is True
