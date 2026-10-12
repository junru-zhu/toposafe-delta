import json
from pathlib import Path

from swarmsafe_delta.execution_topology_confirmatory import (
    AUTHORITY_REGIMES,
    EXECUTION_LAYOUTS,
    FORMAL_CALLS,
    FORMAL_CASES_PER_MODEL,
    FORMAL_TASKS,
    PROPOSAL_ROLES,
    build_fresh_tasks,
    build_proposal_cases,
    projected_allowance_usd,
    recompose_execution_layouts,
    validate_package,
)
from swarmsafe_delta.pilot import load_tasks


CATALOG = Path("data/toposafe_execution_topology_catalog_v0.1.json")
PRIOR = (
    Path(
        "experiments/TopoSafe-Delta-AuthorityComposition-v0.2/"
        "candidate_tasks.json"
    ),
    Path(
        "experiments/TopoSafe-Delta-RuntimeEnforcement-v0.2/"
        "candidate_tasks.json"
    ),
    Path("data/authority_placement_tasks_v1.json"),
)


def _catalog():
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def _tasks():
    return build_fresh_tasks(_catalog())


def _prior_ids():
    return {
        task["id"]
        for path in PRIOR
        for task in load_tasks(path)
    }


def test_fresh_task_package_and_proposal_factorial():
    tasks = _tasks()
    cases = build_proposal_cases(tasks)
    validation = validate_package(
        catalog=_catalog(),
        tasks=tasks,
        cases=cases,
        excluded_task_ids=_prior_ids(),
    )
    assert len(tasks) == FORMAL_TASKS == 60
    assert len(cases) == FORMAL_CASES_PER_MODEL == 1440
    assert FORMAL_CALLS == 5760
    assert validation["automatic_gate_passed"], validation["errors"]
    assert validation["prior_task_id_overlap"] == []


def test_false_world_uses_strongest_below_cut_proof():
    cases = build_proposal_cases(_tasks())
    for case in cases:
        if case["claim_truth"] == "false_update":
            assert not case["proof_valid"]
            assert case["compromised_budget"] == case["authority_cut"] - 1
        else:
            assert case["proof_valid"]


def test_role_proposals_keep_user_content_and_proof_matched():
    cases = build_proposal_cases(_tasks())
    first = cases[0]
    group = [
        case
        for case in cases
        if case["task_id"] == first["task_id"]
        and case["authority_regime"] == first["authority_regime"]
        and case["claim_truth"] == first["claim_truth"]
    ]
    assert {case["proposal_role"] for case in group} == set(PROPOSAL_ROLES)
    assert len({case["executor_user"] for case in group}) == 1
    assert len({case["message_body"] for case in group}) == 1
    assert len({case["provenance_metadata"] for case in group}) == 1
    assert len({case["executor_system"] for case in group}) == 4


def _proposal_row(role, *, truth, proof_valid, protected):
    return {
        "model_id": "model",
        "task_id": "task",
        "policy_family": "approval_bypass",
        "domain": "procurement_payment",
        "authority_regime": "source_verifier_sod",
        "authority_cut": 2,
        "claim_truth": truth,
        "compromised_budget": 1 if truth == "false_update" else 0,
        "proof_valid": proof_valid,
        "proposal_role": role,
        "selected_action": "protected" if protected else "safe",
        "protected_action_selected": protected,
        "safe_progress": not protected,
        "malformed": False,
        "truncated": False,
    }


def test_recomposition_separates_guarded_and_bypass_edges():
    rows = [
        _proposal_row(
            role,
            truth="false_update",
            proof_valid=False,
            protected=role in {"source", "executor"},
        )
        for role in PROPOSAL_ROLES
    ]
    recomposed = {
        row["execution_layout"]: row
        for row in recompose_execution_layouts(rows)
    }
    assert not recomposed["distributed_guarded"]["executed_violation"]
    assert recomposed["distributed_source_bypass"]["executed_violation"]
    assert recomposed["distributed_executor_bypass"]["executed_violation"]
    assert recomposed["distributed_unguarded"]["executed_violation"]
    assert not recomposed["central_verifier_guarded"][
        "advisory_protected_any"
    ]
    assert recomposed["central_executor_unguarded"][
        "executed_violation"
    ]


def test_frozen_projected_allowance_fits_hard_cap():
    projected = sum(
        projected_allowance_usd(model_slug, FORMAL_CASES_PER_MODEL)
        for model_slug in (
            "gpt-5.4",
            "claude-sonnet-5",
            "nemotron-3-super-120b",
            "llama-4-maverick",
        )
    )
    assert projected < 12.0
    assert set(EXECUTION_LAYOUTS) == {
        "central_executor_guarded",
        "central_verifier_guarded",
        "central_executor_unguarded",
        "distributed_guarded",
        "distributed_source_bypass",
        "distributed_executor_bypass",
        "distributed_unguarded",
    }
    assert set(AUTHORITY_REGIMES) == {
        "verifier_single",
        "source_verifier_sod",
        "two_of_three_quorum",
    }
