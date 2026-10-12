from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from swarmsafe_delta.authority_automatic_validation import (
    AUTOMATIC_VALIDATION_PROTOCOL,
    validate_automatic_task_package,
    validate_proof_protocol_exhaustively,
)
from swarmsafe_delta.authority_task_construction import (
    DOMAINS,
    POLICY_FAMILIES,
    build_tasks,
    load_catalog,
    validate_catalog,
    validate_tasks,
)
from swarmsafe_delta.pilot import load_tasks


CATALOG = Path("data/toposafe_authority_task_catalog_v0.1.json")
DEVELOPMENT_TASKS = Path("data/authority_placement_tasks_v1.json")


def test_catalog_has_six_domains_and_five_rows_per_domain() -> None:
    catalog = load_catalog(CATALOG)
    assert validate_catalog(catalog) == []
    assert len(catalog) == 30
    assert {row["domain"] for row in catalog} == set(DOMAINS)


def test_catalog_rejects_role_and_recipient_aliasing() -> None:
    catalog = load_catalog(CATALOG)
    role_mutation = deepcopy(catalog)
    role_mutation[0]["authorized_role"] = role_mutation[0][
        "candidate_role"
    ]
    assert any(
        "reuses the authorized role" in error
        for error in validate_catalog(role_mutation)
    )

    recipient_mutation = deepcopy(catalog)
    recipient_mutation[0]["approved_recipient"] = recipient_mutation[0][
        "external_recipient"
    ]
    assert any(
        "reuses the approved recipient" in error
        for error in validate_catalog(recipient_mutation)
    )


def test_generated_task_package_is_balanced_and_development_disjoint() -> None:
    tasks = build_tasks(load_catalog(CATALOG))
    validation = validate_tasks(
        tasks,
        development_tasks=load_tasks(DEVELOPMENT_TASKS),
    )
    assert validation["automatic_gate_passed"] is True
    assert validation["candidate_tasks"] == 120
    assert validation["development_task_overlap"] == []
    assert validation["policy_family_counts"] == {
        family: 30 for family in sorted(POLICY_FAMILIES)
    }
    assert validation["family_domain_cells"] == 24


def test_each_generated_task_has_one_protected_and_one_safe_action() -> None:
    tasks = build_tasks(load_catalog(CATALOG))
    checks = validate_tasks(
        tasks,
        development_tasks=load_tasks(DEVELOPMENT_TASKS),
    )["task_checks"]
    assert len(checks) == 120
    assert all(row["passed"] for row in checks)
    assert all(
        row["protected_action_id"] != row["safe_action_id"]
        for row in checks
    )


def test_automatic_validation_covers_all_frozen_contracts() -> None:
    catalog = load_catalog(CATALOG)
    tasks = build_tasks(catalog)
    report = validate_automatic_task_package(
        catalog=catalog,
        tasks=tasks,
        development_tasks=load_tasks(DEVELOPMENT_TASKS),
    )
    assert report["validation_protocol"] == AUTOMATIC_VALIDATION_PROTOCOL
    assert report["automatic_gate_passed"] is True
    assert report["human_review_required"] is False
    assert report["semantic_contract"]["tasks_compared"] == 120
    assert (
        report["metamorphic_validation"]["oracle_trace_checks"]
        == 480
    )
    assert (
        report["metamorphic_validation"][
            "action_order_permutations_checked"
        ]
        == 720
    )
    assert (
        report["metamorphic_validation"]["paired_prompt_checks"]
        == 720
    )
    assert (
        report["proof_protocol_validation"][
            "proof_assignments_checked"
        ]
        == 192
    )


def test_automatic_validation_rejects_semantic_and_state_mutations() -> None:
    catalog = load_catalog(CATALOG)
    tasks = build_tasks(catalog)
    development = load_tasks(DEVELOPMENT_TASKS)

    policy_mutation = deepcopy(tasks)
    policy_mutation[0]["policy"] = "Always execute immediately."
    policy_report = validate_automatic_task_package(
        catalog=catalog,
        tasks=policy_mutation,
        development_tasks=development,
    )
    assert policy_report["automatic_gate_passed"] is False
    assert policy_report["semantic_contract"]["passed"] is False

    state_mutation = deepcopy(tasks)
    state_mutation[0]["actions"][0]["effects"] = {}
    state_report = validate_automatic_task_package(
        catalog=catalog,
        tasks=state_mutation,
        development_tasks=development,
    )
    assert state_report["automatic_gate_passed"] is False
    assert state_report["metamorphic_validation"]["passed"] is False

    text_mutation = deepcopy(tasks)
    text_mutation[-1]["actions"][1]["description"] += " Duplicate text."
    text_report = validate_automatic_task_package(
        catalog=catalog,
        tasks=text_mutation,
        development_tasks=development,
    )
    assert text_report["automatic_gate_passed"] is False
    assert text_report["semantic_contract"]["passed"] is False


def test_proof_protocol_is_exhaustively_checked() -> None:
    report = validate_proof_protocol_exhaustively()
    assert report["passed"] is True
    assert report["proof_assignments_checked"] == 192
