#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from pathlib import Path

from swarmsafe_delta.pilot import canonical_json, sha256_file, utc_now
from swarmsafe_delta.runtime_enforcement import (
    EXPERIMENT_ID,
    MODEL_SLUGS,
    smoke_cases,
)
from swarmsafe_delta.topology_pilot import load_jsonl


ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "experiments/TopoSafe-Delta-RuntimeEnforcement-v0.1"
SOURCE = ROOT / "experiments/TopoSafe-Delta-AuthorityComposition-v0.2"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true")
    return parser.parse_args()


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def main() -> None:
    args = parse_args()
    blockers = []
    result_paths = list(PACKAGE.glob("smoke/**/raw/recovery.jsonl"))
    result_paths.extend(PACKAGE.glob("models/**/raw/recovery.jsonl"))
    if result_paths:
        blockers.append(
            "provider result files already exist: "
            + ", ".join(relative(path) for path in result_paths)
        )

    design = json.loads(
        (PACKAGE / "design_spec.json").read_text(encoding="utf-8")
    )
    summary = json.loads(
        (PACKAGE / "package_summary.json").read_text(encoding="utf-8")
    )
    cases = json.loads(
        (PACKAGE / "recovery_cases.json").read_text(encoding="utf-8")
    )
    replays = load_jsonl(PACKAGE / "gate_replay.jsonl")
    selected_smoke = smoke_cases(cases)
    case_counts = Counter(case["source_model_slug"] for case in cases)

    expected_model_counts = design["model_recovery_calls"]
    observed_model_counts = {
        slug: case_counts[slug] for slug in MODEL_SLUGS
    }
    checks = {
        "experiment_id": design.get("experiment_id") == EXPERIMENT_ID,
        "design_status": design.get("status") == "design_only_unfrozen",
        "proof_rows": len(replays) == 6480,
        "formal_calls": len(cases) == 697,
        "smoke_calls": len(selected_smoke) == 8,
        "model_counts": observed_model_counts == expected_model_counts,
        "summary_formal_calls": summary.get("formal_recovery_calls") == 697,
        "summary_smoke_calls": summary.get("excluded_smoke_calls") == 8,
        "human_review_required": (
            design.get("human_review_required") is False
            and summary.get("human_review_required") is False
        ),
        "human_review_used": (
            design.get("human_review_used_as_evidence") is False
            and summary.get("human_review_used_as_evidence") is False
        ),
        "unique_replay_ids": len(replays)
        == len({row["replay_id"] for row in replays}),
        "unique_recovery_ids": len(cases)
        == len({row["recovery_id"] for row in cases}),
        "recovery_matches_replay": {
            case["recovery_id"] for case in cases
        }
        == {
            row["replay_id"] for row in replays if row["requires_recovery"]
        },
        "invalid_proof_only": all(
            case["proof_valid"] is False for case in cases
        ),
        "gate_blocks_invalid_proof": all(
            not row["gate_only_violation"]
            for row in replays
            if row["runtime_gate_blocked"]
        ),
    }
    blockers.extend(name for name, passed in checks.items() if not passed)

    source_paths = [
        PACKAGE / "design_spec.json",
        PACKAGE / "protocol.md",
        PACKAGE / "package_summary.json",
        PACKAGE / "recovery_cases.json",
        PACKAGE / "gate_replay.jsonl",
        SOURCE / "candidate_tasks.json",
        SOURCE / "manifest.json",
        SOURCE / "models/study_a/validation_report.json",
        SOURCE / "models/threshold/validation_report.json",
        ROOT / "src/swarmsafe_delta/runtime_enforcement.py",
        ROOT / "src/swarmsafe_delta/authority_composition.py",
        ROOT / "src/swarmsafe_delta/authority_placement.py",
        ROOT / "src/swarmsafe_delta/pilot.py",
        ROOT / "scripts/build_runtime_enforcement_package.py",
        ROOT / "scripts/freeze_runtime_enforcement.py",
        ROOT / "scripts/run_runtime_enforcement.py",
        ROOT / "scripts/validate_runtime_enforcement.py",
    ]
    for source_path in summary["source_hashes"]:
        source_paths.append(ROOT / source_path)
    missing = [relative(path) for path in source_paths if not path.exists()]
    if missing:
        blockers.append("missing source files: " + ", ".join(missing))
    for source_path, expected_hash in summary["source_hashes"].items():
        path = ROOT / source_path
        if path.exists() and sha256_file(path) != expected_hash:
            blockers.append(f"parent source hash changed: {source_path}")

    preflight = {
        "experiment_id": EXPERIMENT_ID,
        "checked_at": utc_now(),
        "status": "ready_to_freeze" if not blockers else "blocked",
        "checks": checks,
        "blockers": blockers,
        "proof_bearing_source_rows": len(replays),
        "formal_recovery_calls": len(cases),
        "excluded_smoke_calls": len(selected_smoke),
        "model_recovery_calls": observed_model_counts,
    }
    (PACKAGE / "freeze_preflight.json").write_text(
        json.dumps(preflight, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    if args.check_only:
        print(canonical_json(preflight))
        raise SystemExit(1 if blockers else 0)
    if blockers:
        print(canonical_json(preflight))
        raise SystemExit(1)

    source_hashes = {
        relative(path): sha256_file(path) for path in source_paths
    }
    manifest = {
        "experiment_id": EXPERIMENT_ID,
        "status": "frozen_pre_run",
        "frozen_at": utc_now(),
        "evidence_type": (
            "post_hoc_mechanistic_extension_with_frozen_parent_rows"
        ),
        "source_experiment_id": (
            "TopoSafe-Delta-AuthorityComposition-v0.2"
        ),
        "proof_bearing_source_rows": len(replays),
        "formal_recovery_calls": len(cases),
        "excluded_smoke_calls": len(selected_smoke),
        "model_recovery_calls": observed_model_counts,
        "smoke_recovery_ids": [
            case["recovery_id"] for case in selected_smoke
        ],
        "active_models": [
            slug for slug in MODEL_SLUGS if observed_model_counts[slug]
        ],
        "workers": 6,
        "schedule_seed": 2026100621,
        "max_output_tokens": 200,
        "maximum_provider_attempts": 3,
        "connect_timeout_seconds": 10,
        "read_timeout_seconds": 180,
        "human_review_required": False,
        "human_review_used_as_evidence": False,
        "source_hashes": source_hashes,
    }
    shutil.copyfile(PACKAGE / "protocol.md", PACKAGE / "frozen_protocol.md")
    (PACKAGE / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    print(
        canonical_json(
            {
                "status": manifest["status"],
                "manifest": relative(PACKAGE / "manifest.json"),
                "formal_recovery_calls": len(cases),
            }
        )
    )


if __name__ == "__main__":
    main()
