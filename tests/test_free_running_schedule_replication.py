from __future__ import annotations

import json
from pathlib import Path

from scripts.analyze_free_running_schedule_replication import (
    schedule_contrast_difference,
)
from swarmsafe_delta import free_running_communication as base
from swarmsafe_delta.free_running_schedule_replication import (
    EXPERIMENT_ID,
    RESULT_STATUS,
    SCHEDULE_SEED,
    STUDY_ID,
    activate,
)
from swarmsafe_delta.pilot import load_tasks, sha256_file


PACKAGE = Path(
    "experiments/TopoSafe-Delta-FreeRunningScheduleReplication-v0.1"
)
PARENT = Path("experiments/TopoSafe-Delta-FreeRunningCommunication-v0.3")


def test_replication_uses_identical_tasks_and_prompt_inventory() -> None:
    report = json.loads((PACKAGE / "task_validation.json").read_text())
    parent_manifest = json.loads((PARENT / "manifest.json").read_text())
    assert sha256_file(PACKAGE / "candidate_tasks.json") == sha256_file(
        PARENT / "candidate_tasks.json"
    )
    assert (
        report["prompt_inventory_sha256"]
        == parent_manifest["prompt_inventory_sha256"]
    )
    assert report["automatic_gate_passed"] is True


def test_replication_changes_only_schedule_order() -> None:
    tasks = load_tasks(PACKAGE / "candidate_tasks.json")
    cases = json.loads((PACKAGE / "cases.json").read_text())
    parent_manifest = json.loads((PARENT / "manifest.json").read_text())
    parent_jobs = base.build_jobs(
        tasks=tasks,
        cases=cases,
        seed=parent_manifest["schedule_seed"],
    )
    replication_jobs = base.build_jobs(
        tasks=tasks,
        cases=cases,
        seed=SCHEDULE_SEED,
    )
    parent_ids = [
        f"{task['id']}::{case['condition']}" for task, case, _ in parent_jobs
    ]
    replication_ids = [
        f"{task['id']}::{case['condition']}"
        for task, case, _ in replication_jobs
    ]
    assert parent_ids != replication_ids
    assert set(parent_ids) == set(replication_ids)


def test_replication_activation_is_explicit_and_reversible() -> None:
    previous = (
        base.EXPERIMENT_ID,
        base.STUDY_ID,
        base.RESULT_STATUS,
        base.FORWARD_MAX_OUTPUT_TOKENS,
    )
    try:
        activate()
        assert base.EXPERIMENT_ID == EXPERIMENT_ID
        assert base.STUDY_ID == STUDY_ID
        assert base.RESULT_STATUS == RESULT_STATUS
        assert base.FORWARD_MAX_OUTPUT_TOKENS == 512
    finally:
        (
            base.EXPERIMENT_ID,
            base.STUDY_ID,
            base.RESULT_STATUS,
            base.FORWARD_MAX_OUTPUT_TOKENS,
        ) = previous


def test_schedule_difference_is_paired_by_task() -> None:
    common = {
        "authority_regime": "verifier_single",
        "claim_truth": "false_update",
    }
    parent = [
        {**common, "task_id": "t1", "topology_id": "topo_A", "outcome": 0},
        {**common, "task_id": "t1", "topology_id": "topo_B", "outcome": 0},
        {**common, "task_id": "t2", "topology_id": "topo_A", "outcome": 0},
        {**common, "task_id": "t2", "topology_id": "topo_B", "outcome": 0},
    ]
    replication = [
        {**common, "task_id": "t1", "topology_id": "topo_A", "outcome": 0},
        {**common, "task_id": "t1", "topology_id": "topo_B", "outcome": 1},
        {**common, "task_id": "t2", "topology_id": "topo_A", "outcome": 0},
        {**common, "task_id": "t2", "topology_id": "topo_B", "outcome": 0},
    ]
    effect = schedule_contrast_difference(
        replication,
        parent,
        topology_id="topo_B",
        authority_regime="verifier_single",
        claim_truth="false_update",
        field="outcome",
        seed=1,
    )
    assert effect["tasks"] == 2
    assert effect["estimate"] == 0.5


def test_design_excludes_human_review() -> None:
    design = json.loads((PACKAGE / "design_spec.json").read_text())
    assert design["provider_calls_completed"] == 0
    assert design["human_review_required"] is False
    assert design["human_review_used_as_evidence"] is False
    assert design["formal_assigned_model_calls"] == 20_160
