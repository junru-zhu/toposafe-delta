#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from swarmsafe_delta.pilot import canonical_json, sha256_file, utc_now
from swarmsafe_delta.runtime_enforcement_factorial import (
    EXPERIMENT_ID,
    FORMAL_INITIAL_CALLS,
    MAX_RECOVERY_CALLS,
    MODEL_SLUGS,
)


ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "experiments/TopoSafe-Delta-RuntimeEnforcement-v0.2"


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
    cases = json.loads((PACKAGE / "initial_cases.json").read_text())
    blockers: list[str] = []
    checks = {
        "design_unfrozen": design.get("status") == "design_only_unfrozen",
        "zero_provider_calls": design.get("provider_calls_completed") == 0,
        "automatic_task_gate": validation.get("automatic_gate_passed") is True,
        "human_review_absent": (
            design.get("human_review_required") is False
            and design.get("human_review_used_as_evidence") is False
        ),
        "initial_call_budget": (
            summary.get("formal_initial_calls") == FORMAL_INITIAL_CALLS
        ),
        "recovery_call_ceiling": (
            summary.get("maximum_formal_recovery_calls")
            == MAX_RECOVERY_CALLS
        ),
        "initial_cases_per_model": len(cases) == 672,
    }
    for name, passed in checks.items():
        if not passed:
            blockers.append(f"failed check: {name}")
    if (PACKAGE / "models").exists():
        raw_files = list((PACKAGE / "models").glob("**/*.jsonl"))
        if raw_files:
            blockers.append("formal model rows already exist")
    smoke_candidates = [
        case
        for case in cases
        if (
            case["policy_family"] == "approval_bypass"
            and case["authority_regime"] == "source_verifier_sod"
            and case["claim_truth"] == "false_update"
            and case["compromised_budget"] == 0
        )
        or (
            case["policy_family"] == "protected_transfer"
            and case["authority_regime"] == "two_of_three_quorum"
            and case["claim_truth"] == "true_update"
        )
    ]
    smoke_episode_ids = sorted(
        {
            f"{case['task_id']}::{case['condition']}"
            for case in smoke_candidates
        }
    )[:2]
    if len(smoke_episode_ids) != 2:
        blockers.append("could not select two smoke episodes")
    source_paths = [
        ROOT / "data/toposafe_runtime_enforcement_task_catalog_v0.2.json",
        PACKAGE / "design_spec.json",
        PACKAGE / "protocol.md",
        PACKAGE / "candidate_tasks.json",
        PACKAGE / "initial_cases.json",
        PACKAGE / "task_validation.json",
        PACKAGE / "package_summary.json",
        ROOT / "src/swarmsafe_delta/runtime_enforcement_factorial.py",
        ROOT / "src/swarmsafe_delta/runtime_enforcement.py",
        ROOT / "src/swarmsafe_delta/authority_composition.py",
        ROOT / "src/swarmsafe_delta/authority_placement.py",
        ROOT / "src/swarmsafe_delta/authority_task_construction.py",
        ROOT / "src/swarmsafe_delta/authority_automatic_validation.py",
        ROOT / "src/swarmsafe_delta/pilot.py",
        ROOT / "scripts/build_runtime_enforcement_factorial.py",
        ROOT / "scripts/freeze_runtime_enforcement_factorial.py",
        ROOT / "scripts/run_runtime_enforcement_factorial.py",
        ROOT / "scripts/validate_runtime_enforcement_factorial.py",
        ROOT / "scripts/build_runtime_enforcement_recovery.py",
        ROOT / "scripts/analyze_runtime_enforcement_factorial.py",
    ]
    missing = [relative(path) for path in source_paths if not path.exists()]
    if missing:
        blockers.append("missing source files: " + ", ".join(missing))
    preflight = {
        "experiment_id": EXPERIMENT_ID,
        "checked_at": utc_now(),
        "status": "ready_to_freeze" if not blockers else "blocked",
        "checks": checks,
        "blockers": blockers,
        "formal_initial_calls": FORMAL_INITIAL_CALLS,
        "maximum_formal_recovery_calls": MAX_RECOVERY_CALLS,
        "excluded_smoke_calls": len(smoke_episode_ids) * len(MODEL_SLUGS),
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
        "status": "frozen_pre_run",
        "frozen_at": utc_now(),
        "evidence_type": "fresh_independent_runtime_enforcement_factorial",
        "task_file": relative(PACKAGE / "candidate_tasks.json"),
        "initial_case_file": relative(PACKAGE / "initial_cases.json"),
        "formal_tasks": 48,
        "initial_cases_per_model": 672,
        "formal_initial_calls": FORMAL_INITIAL_CALLS,
        "maximum_formal_recovery_calls": MAX_RECOVERY_CALLS,
        "adaptive_recovery_rule": (
            "all fresh non-control protected-action selections with "
            "proof_valid=false receive one recovery turn"
        ),
        "manual_recovery_selection": False,
        "active_models": list(MODEL_SLUGS),
        "smoke_initial_episode_ids": smoke_episode_ids,
        "excluded_smoke_calls": len(smoke_episode_ids) * len(MODEL_SLUGS),
        "workers": 6,
        "schedule_seed": 2026100625,
        "max_output_tokens": 200,
        "maximum_provider_attempts": 3,
        "connect_timeout_seconds": 10,
        "read_timeout_seconds": 180,
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
                "manifest": relative(manifest_path),
                "source_hashes": len(source_hashes),
            }
        )
    )


if __name__ == "__main__":
    main()
