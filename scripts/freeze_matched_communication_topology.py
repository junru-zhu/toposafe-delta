#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from swarmsafe_delta.matched_communication_topology import (
    CASES_PER_MODEL,
    EXPERIMENT_ID,
    FORMAL_CALLS,
    MODEL_SLUGS,
    build_cases,
    validate_case_contracts,
)
from swarmsafe_delta.pilot import (
    canonical_json,
    load_tasks,
    sha256_file,
    utc_now,
)
from swarmsafe_delta.topology_pilot import sha256_text


ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "experiments/TopoSafe-Delta-MatchedCommunication-v0.1"
PARENT = ROOT / "experiments/TopoSafe-Delta-AuthorityComposition-v0.2"


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tasks = load_tasks(PACKAGE / "candidate_tasks.json")
    cases = json.loads((PACKAGE / "cases.json").read_text())
    validation = json.loads((PACKAGE / "task_validation.json").read_text())
    design = json.loads((PACKAGE / "design_spec.json").read_text())
    blockers: list[str] = []
    if design.get("status") != "design_only_unfrozen":
        blockers.append("design status is not design_only_unfrozen")
    if design.get("provider_calls_completed") != 0:
        blockers.append("design reports provider calls before freeze")
    if validation.get("automatic_gate_passed") is not True:
        blockers.append("automatic topology gate did not pass")
    if validation.get("human_review_required") is not False:
        blockers.append("human review is still required")
    if validation.get("human_review_used_as_evidence") is not False:
        blockers.append("human review is still used as evidence")
    contracts = validate_case_contracts(tasks, cases)
    blockers.extend(contracts["errors"])
    if len(cases) != CASES_PER_MODEL:
        blockers.append("case count does not match design")
    raw_files = list(PACKAGE.glob("models/**/raw/episodes.jsonl"))
    if raw_files:
        blockers.append("formal model rows already exist")

    first_task = sorted(tasks, key=lambda row: row["id"])[0]["id"]
    second_task = sorted(tasks, key=lambda row: row["id"])[1]["id"]
    smoke_ids = [
        (
            f"{first_task}::study_b1__topo_A__verifier_single__"
            "false_update"
        ),
        (
            f"{second_task}::study_b1__topo_D__source_verifier_sod__"
            "false_update"
        ),
    ]
    all_ids = {
        f"{case['task_id']}::{case['condition']}" for case in cases
    }
    if not set(smoke_ids).issubset(all_ids):
        blockers.append("smoke episode IDs are absent from cases")

    source_paths = [
        PARENT / "candidate_tasks.json",
        PARENT / "task_validation.json",
        PACKAGE / "design_spec.json",
        PACKAGE / "protocol.md",
        PACKAGE / "candidate_tasks.json",
        PACKAGE / "cases.json",
        PACKAGE / "task_validation.json",
        PACKAGE / "package_summary.json",
        ROOT / "src/swarmsafe_delta/matched_communication_topology.py",
        ROOT / "src/swarmsafe_delta/authority_composition.py",
        ROOT / "src/swarmsafe_delta/authority_placement.py",
        ROOT / "src/swarmsafe_delta/pilot.py",
        ROOT / "scripts/build_matched_communication_topology.py",
        ROOT / "scripts/freeze_matched_communication_topology.py",
        ROOT / "scripts/run_matched_communication_topology.py",
        ROOT / "scripts/validate_matched_communication_topology.py",
        ROOT / "scripts/analyze_matched_communication_topology.py",
    ]
    missing = [relative(path) for path in source_paths if not path.exists()]
    if missing:
        blockers.append("missing source files: " + ", ".join(missing))
    preflight = {
        "experiment_id": EXPERIMENT_ID,
        "checked_at": utc_now(),
        "status": "ready_to_freeze" if not blockers else "blocked",
        "automatic_gate_passed": validation.get("automatic_gate_passed"),
        "case_contract_passed": contracts["passed"],
        "formal_tasks": len(tasks),
        "cases_per_model": len(cases),
        "formal_calls": FORMAL_CALLS,
        "smoke_calls_excluded": len(smoke_ids) * len(MODEL_SLUGS),
        "human_review_required": False,
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
    prompt_inventory = [
        {
            "episode_id": f"{case['task_id']}::{case['condition']}",
            "system_sha256": case["executor_system_sha256"],
            "user_sha256": case["executor_user_sha256"],
            "message_body_sha256": sha256_text(case["message_body"]),
            "topology_metadata_sha256": case[
                "topology_metadata_sha256"
            ],
        }
        for case in cases
    ]
    manifest = {
        "experiment_id": EXPERIMENT_ID,
        "status": "frozen_pre_run",
        "frozen_at": utc_now(),
        "evidence_type": (
            "matched_frozen_message_communication_topology_factorial"
        ),
        "task_file": relative(PACKAGE / "candidate_tasks.json"),
        "case_file": relative(PACKAGE / "cases.json"),
        "formal_tasks": len(tasks),
        "cases_per_model": len(cases),
        "formal_calls": FORMAL_CALLS,
        "active_models": list(MODEL_SLUGS),
        "smoke_episode_ids": smoke_ids,
        "excluded_smoke_calls": len(smoke_ids) * len(MODEL_SLUGS),
        "workers": 6,
        "schedule_seed": 2026100631,
        "max_output_tokens": 200,
        "maximum_provider_attempts": 3,
        "connect_timeout_seconds": 10,
        "read_timeout_seconds": 180,
        "provider_seed_supported": False,
        "human_review_required": False,
        "human_review_used_as_evidence": False,
        "manual_case_selection": False,
        "source_hashes": source_hashes,
        "prompt_inventory_sha256": sha256_text(
            canonical_json(prompt_inventory)
        ),
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
                "manifest": relative(manifest_path),
                "formal_calls": FORMAL_CALLS,
                "source_hashes": len(source_hashes),
            }
        )
    )


if __name__ == "__main__":
    main()
