#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from swarmsafe_delta.authority_mechanism_ablations import (
    ABLATION_IDS,
    EPISODES_PER_MODEL,
    EXPERIMENT_ID,
    FORMAL_CALLS,
    FORMAL_TASKS,
    MODEL_SLUGS,
    PARENT_EXPERIMENT_ID,
)
from swarmsafe_delta.pilot import canonical_json, sha256_file, utc_now


ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "experiments/TopoSafe-Delta-AuthorityMechanismAblations-v0.1"
PARENT = ROOT / "experiments/TopoSafe-Delta-RuntimeEnforcement-v0.2"


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    design = json.loads((PACKAGE / "design_spec.json").read_text())
    validation = json.loads((PACKAGE / "task_validation.json").read_text())
    summary = json.loads((PACKAGE / "package_summary.json").read_text())
    cases = json.loads((PACKAGE / "cases.json").read_text())
    parent_validation = json.loads(
        (PARENT / "models/initial_validation_report.json").read_text()
    )
    blockers: list[str] = []
    checks = {
        "design_unfrozen": design.get("status") == "design_only_unfrozen",
        "zero_provider_calls": design.get("provider_calls_completed") == 0,
        "automatic_gate": validation.get("automatic_gate_passed") is True,
        "parent_all_models_valid": (
            parent_validation.get("passed") is True
            and parent_validation.get("invalid_models") == []
        ),
        "human_review_absent": (
            design.get("human_review_required") is False
            and design.get("human_review_used_as_evidence") is False
        ),
        "formal_task_count": summary.get("formal_tasks") == FORMAL_TASKS,
        "case_count": len(cases) == EPISODES_PER_MODEL,
        "formal_call_count": summary.get("formal_calls") == FORMAL_CALLS,
        "ablation_registry": design.get("ablation_ids")
        == list(ABLATION_IDS),
    }
    blockers.extend(
        f"failed check: {name}" for name, passed in checks.items() if not passed
    )
    raw_files = list(PACKAGE.glob("smoke/**/raw/*.jsonl"))
    raw_files.extend(PACKAGE.glob("models/**/raw/*.jsonl"))
    if raw_files:
        blockers.append("provider result files already exist")
    smoke_candidates = [
        case
        for case in cases
        if case["ablation_id"] == "replay_stale_signed_proof"
    ]
    smoke_episode_ids = [
        f"{smoke_candidates[0]['task_id']}::{smoke_candidates[0]['condition']}"
    ] if smoke_candidates else []
    if len(smoke_episode_ids) != 1:
        blockers.append("could not select one smoke episode")
    source_paths = [
        PACKAGE / "design_spec.json",
        PACKAGE / "protocol.md",
        PACKAGE / "candidate_tasks.json",
        PACKAGE / "cases.json",
        PACKAGE / "task_validation.json",
        PACKAGE / "package_summary.json",
        PARENT / "manifest.json",
        PARENT / "candidate_tasks.json",
        PARENT / "initial_cases.json",
        PARENT / "models/initial_validation_report.json",
        ROOT / "src/swarmsafe_delta/authority_mechanism_ablations.py",
        ROOT / "src/swarmsafe_delta/authority_composition.py",
        ROOT / "src/swarmsafe_delta/authority_placement.py",
        ROOT / "src/swarmsafe_delta/pilot.py",
        ROOT / "scripts/build_authority_mechanism_ablations.py",
        ROOT / "scripts/freeze_authority_mechanism_ablations.py",
        ROOT / "scripts/run_authority_mechanism_ablations.py",
        ROOT / "scripts/validate_authority_mechanism_ablations.py",
        ROOT / "scripts/analyze_authority_mechanism_ablations.py",
        ROOT / "tests/test_authority_mechanism_ablations.py",
    ]
    source_paths.extend(
        PARENT / f"models/initial/{slug}/raw/episodes.jsonl"
        for slug in MODEL_SLUGS
    )
    missing = [relative(path) for path in source_paths if not path.exists()]
    if missing:
        blockers.append("missing source files: " + ", ".join(missing))
    report = {
        "experiment_id": EXPERIMENT_ID,
        "checked_at": utc_now(),
        "status": "ready_to_freeze" if not blockers else "blocked",
        "checks": checks,
        "blockers": blockers,
        "formal_calls": FORMAL_CALLS,
        "excluded_smoke_calls": len(smoke_episode_ids) * len(MODEL_SLUGS),
    }
    (PACKAGE / "freeze_preflight.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(canonical_json(report))
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
        "status": "frozen_pre_run",
        "frozen_at": utc_now(),
        "evidence_type": "targeted_authority_mechanism_ablations",
        "parent_experiment_id": PARENT_EXPERIMENT_ID,
        "task_file": relative(PACKAGE / "candidate_tasks.json"),
        "case_file": relative(PACKAGE / "cases.json"),
        "formal_tasks": FORMAL_TASKS,
        "cases_per_model": EPISODES_PER_MODEL,
        "formal_assigned_model_calls": FORMAL_CALLS,
        "active_models": list(MODEL_SLUGS),
        "smoke_episode_ids": smoke_episode_ids,
        "excluded_smoke_calls": len(smoke_episode_ids) * len(MODEL_SLUGS),
        "workers": 6,
        "schedule_seed": 2026100661,
        "max_output_tokens": 200,
        "maximum_provider_attempts": 3,
        "connect_timeout_seconds": 10,
        "read_timeout_seconds": 180,
        "provider_seed_supported": False,
        "manual_case_selection": False,
        "human_review_required": False,
        "human_review_used_as_evidence": False,
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
            }
        )
    )


if __name__ == "__main__":
    main()
