#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from swarmsafe_delta.free_running_schedule_replication import (
    ANALYSIS_BOOTSTRAP_SEED,
    EXPERIMENT_ID,
    FORWARD_MAX_OUTPUT_TOKENS,
    FORWARD_RESPONSE_MODE,
    PARENT_EXPERIMENT_ID,
    SCHEDULE_SEED,
    activate,
)
from swarmsafe_delta.pilot import canonical_json, load_tasks, sha256_file, utc_now
from swarmsafe_delta.topology_pilot import sha256_text


activate()

from swarmsafe_delta.free_running_communication import (  # noqa: E402
    EXECUTOR_MAX_OUTPUT_TOKENS,
    FORMAL_ASSIGNED_MODEL_CALLS,
    FORMAL_EPISODES,
    MODEL_CALLS_PER_EPISODE,
    MODEL_SLUGS,
    validate_case_contracts,
)


ROOT = Path(__file__).resolve().parent.parent
PACKAGE = (
    ROOT / "experiments/TopoSafe-Delta-FreeRunningScheduleReplication-v0.1"
)
PARENT = ROOT / "experiments/TopoSafe-Delta-FreeRunningCommunication-v0.3"
B1 = ROOT / "experiments/TopoSafe-Delta-MatchedCommunication-v0.1"


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true")
    return parser.parse_args()


def prompt_inventory(cases: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "episode_id": f"{case['task_id']}::{case['condition']}",
            "source_message_sha256": sha256_text(case["source_message"]),
            "source_proof_sha256": sha256_text(
                canonical_json(case["source_proof"])
            ),
            "delivery_schedule_sha256": case["delivery_schedule_sha256"],
            "topology_metadata_sha256": case["topology_metadata_sha256"],
        }
        for case in cases
    ]


def main() -> None:
    args = parse_args()
    tasks = load_tasks(PACKAGE / "candidate_tasks.json")
    cases = json.loads((PACKAGE / "cases.json").read_text())
    validation = json.loads((PACKAGE / "task_validation.json").read_text())
    design = json.loads((PACKAGE / "design_spec.json").read_text())
    parent_manifest_path = PARENT / "manifest.json"
    parent_validation_path = PARENT / "models/validation_report.json"
    parent_results_path = PARENT / "analysis/results.json"
    parent_manifest = json.loads(parent_manifest_path.read_text())
    parent_validation = json.loads(parent_validation_path.read_text())
    contracts = validate_case_contracts(tasks, cases)
    blockers = list(contracts["errors"])

    if design.get("status") != "design_only_unfrozen":
        blockers.append("design status is not design_only_unfrozen")
    if design.get("provider_calls_completed") != 0:
        blockers.append("design reports provider calls before freeze")
    if validation.get("automatic_gate_passed") is not True:
        blockers.append("automatic schedule-replication gate did not pass")
    if validation.get("human_review_required") is not False:
        blockers.append("human review is still required")
    if validation.get("human_review_used_as_evidence") is not False:
        blockers.append("human review is still used as evidence")
    if parent_manifest.get("experiment_id") != PARENT_EXPERIMENT_ID:
        blockers.append("parent experiment identity mismatch")
    if parent_validation.get("passed") is not True:
        blockers.append("parent B2 four-model validation did not pass")
    if parent_manifest.get("schedule_seed") == SCHEDULE_SEED:
        blockers.append("replication schedule seed equals parent")
    if sha256_file(PACKAGE / "candidate_tasks.json") != sha256_file(
        PARENT / "candidate_tasks.json"
    ):
        blockers.append("candidate-task file differs from parent")
    inventory_sha256 = sha256_text(canonical_json(prompt_inventory(cases)))
    if inventory_sha256 != parent_manifest.get("prompt_inventory_sha256"):
        blockers.append("prompt inventory differs from parent")
    parent_source_mismatches = []
    for path_text, expected in parent_manifest["source_hashes"].items():
        path = ROOT / path_text
        observed = sha256_file(path) if path.exists() else "missing"
        if observed != expected:
            parent_source_mismatches.append(path_text)
    if parent_source_mismatches:
        blockers.append(
            "parent frozen sources changed: "
            + ", ".join(parent_source_mismatches)
        )
    if list(PACKAGE.glob("models/**/raw/episodes.jsonl")):
        blockers.append("formal model rows already exist")

    smoke_ids = list(parent_manifest["smoke_episode_ids"])
    all_ids = {
        f"{case['task_id']}::{case['condition']}" for case in cases
    }
    if not set(smoke_ids).issubset(all_ids):
        blockers.append("smoke episode IDs are absent from cases")

    new_sources = [
        PACKAGE / "design_spec.json",
        PACKAGE / "protocol.md",
        PACKAGE / "candidate_tasks.json",
        PACKAGE / "cases.json",
        PACKAGE / "task_validation.json",
        PACKAGE / "package_summary.json",
        ROOT / "src/swarmsafe_delta/free_running_schedule_replication.py",
        ROOT / "scripts/build_free_running_schedule_replication.py",
        ROOT / "scripts/freeze_free_running_schedule_replication.py",
        ROOT / "scripts/run_free_running_schedule_replication.py",
        ROOT / "scripts/validate_free_running_schedule_replication.py",
        ROOT / "scripts/analyze_free_running_schedule_replication.py",
        ROOT / "tests/test_free_running_schedule_replication.py",
    ]
    parent_artifacts = [
        parent_manifest_path,
        parent_validation_path,
        parent_results_path,
        PARENT / "analysis/results.md",
        PARENT / "candidate_tasks.json",
        PARENT / "cases.json",
        *[
            PARENT / f"models/{slug}/manifest.json"
            for slug in MODEL_SLUGS
        ],
        *[
            PARENT / f"models/{slug}/raw/episodes.jsonl"
            for slug in MODEL_SLUGS
        ],
        B1 / "models/validation_report.json",
        B1 / "analysis/results.json",
        *[
            B1 / f"models/{slug}/raw/episodes.jsonl"
            for slug in MODEL_SLUGS
        ],
    ]
    inherited_sources = [
        ROOT / path_text for path_text in parent_manifest["source_hashes"]
    ]
    source_paths = list(
        dict.fromkeys([*new_sources, *parent_artifacts, *inherited_sources])
    )
    missing = [relative(path) for path in source_paths if not path.exists()]
    if missing:
        blockers.append("missing source files: " + ", ".join(missing))

    checks = {
        "automatic_gate": validation.get("automatic_gate_passed") is True,
        "case_contract": contracts["passed"],
        "parent_all_models_valid": parent_validation.get("passed") is True,
        "parent_source_hashes": not parent_source_mismatches,
        "prompt_inventory_identical": (
            inventory_sha256 == parent_manifest.get("prompt_inventory_sha256")
        ),
        "schedule_seed_changed": (
            SCHEDULE_SEED != parent_manifest.get("schedule_seed")
        ),
        "human_review_absent": (
            validation.get("human_review_required") is False
            and validation.get("human_review_used_as_evidence") is False
        ),
        "zero_provider_calls": design.get("provider_calls_completed") == 0,
        "design_unfrozen": design.get("status") == "design_only_unfrozen",
    }
    preflight = {
        "experiment_id": EXPERIMENT_ID,
        "parent_experiment_id": PARENT_EXPERIMENT_ID,
        "checked_at": utc_now(),
        "status": "ready_to_freeze" if not blockers else "blocked",
        "checks": checks,
        "formal_episodes": FORMAL_EPISODES,
        "formal_assigned_model_calls": FORMAL_ASSIGNED_MODEL_CALLS,
        "excluded_smoke_model_calls": (
            len(smoke_ids) * len(MODEL_SLUGS) * MODEL_CALLS_PER_EPISODE
        ),
        "blockers": blockers,
    }
    (PACKAGE / "freeze_preflight.json").write_text(
        json.dumps(preflight, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    print(canonical_json(preflight))
    if args.check_only:
        raise SystemExit(1 if blockers else 0)
    if blockers:
        raise SystemExit(1)
    manifest_path = PACKAGE / "manifest.json"
    if manifest_path.exists():
        existing = json.loads(manifest_path.read_text())
        if existing.get("status") == "frozen_pre_run":
            raise RuntimeError("Refusing to replace an existing frozen manifest")

    source_hashes = {
        relative(path): sha256_file(path) for path in source_paths
    }
    manifest = {
        "experiment_id": EXPERIMENT_ID,
        "parent_experiment_id": PARENT_EXPERIMENT_ID,
        "status": "frozen_pre_run",
        "frozen_at": utc_now(),
        "evidence_type": "independent_execution_schedule_replication",
        "changed_factor": "schedule_seed_and_resulting_execution_order",
        "task_file": relative(PACKAGE / "candidate_tasks.json"),
        "case_file": relative(PACKAGE / "cases.json"),
        "formal_tasks": len(tasks),
        "episodes_per_model": len(cases),
        "formal_episodes": FORMAL_EPISODES,
        "model_calls_per_episode": MODEL_CALLS_PER_EPISODE,
        "formal_assigned_model_calls": FORMAL_ASSIGNED_MODEL_CALLS,
        "active_models": list(MODEL_SLUGS),
        "smoke_episode_ids": smoke_ids,
        "excluded_smoke_model_calls": (
            len(smoke_ids) * len(MODEL_SLUGS) * MODEL_CALLS_PER_EPISODE
        ),
        "workers": parent_manifest["workers"],
        "parent_schedule_seed": parent_manifest["schedule_seed"],
        "schedule_seed": SCHEDULE_SEED,
        "analysis_bootstrap_seed": ANALYSIS_BOOTSTRAP_SEED,
        "forward_max_output_tokens": FORWARD_MAX_OUTPUT_TOKENS,
        "executor_max_output_tokens": EXECUTOR_MAX_OUTPUT_TOKENS,
        "forward_response_mode": FORWARD_RESPONSE_MODE,
        "maximum_provider_attempts": parent_manifest[
            "maximum_provider_attempts"
        ],
        "connect_timeout_seconds": parent_manifest[
            "connect_timeout_seconds"
        ],
        "read_timeout_seconds": parent_manifest["read_timeout_seconds"],
        "provider_seed_supported": False,
        "human_review_required": False,
        "human_review_used_as_evidence": False,
        "manual_case_selection": False,
        "prompt_inventory_sha256": inventory_sha256,
        "parent_manifest_sha256": sha256_file(parent_manifest_path),
        "parent_validation_sha256": sha256_file(parent_validation_path),
        "parent_results_sha256": sha256_file(parent_results_path),
        "source_hashes": source_hashes,
    }
    shutil.copyfile(PACKAGE / "protocol.md", PACKAGE / "frozen_protocol.md")
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    print(
        canonical_json(
            {
                "status": manifest["status"],
                "manifest_sha256": sha256_file(manifest_path),
                "source_hashes": len(source_hashes),
                "schedule_seed": SCHEDULE_SEED,
            }
        )
    )


if __name__ == "__main__":
    main()
