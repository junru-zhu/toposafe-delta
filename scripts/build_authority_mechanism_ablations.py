#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from swarmsafe_delta.authority_mechanism_ablations import (
    EXPERIMENT_ID,
    FORMAL_CALLS,
    MODEL_SLUGS,
    PARENT_EXPERIMENT_ID,
    build_cases,
    select_tasks,
    validate_case_contracts,
)
from swarmsafe_delta.pilot import canonical_json, load_tasks
from swarmsafe_delta.topology_pilot import load_jsonl, sha256_text


ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "experiments/TopoSafe-Delta-AuthorityMechanismAblations-v0.1"
PARENT = ROOT / "experiments/TopoSafe-Delta-RuntimeEnforcement-v0.2"


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parent_tasks = load_tasks(PARENT / "candidate_tasks.json")
    tasks = select_tasks(parent_tasks)
    cases = build_cases(parent_tasks)
    validation = validate_case_contracts(parent_tasks, cases)
    parent_validation = json.loads(
        (PARENT / "models/initial_validation_report.json").read_text()
    )
    validation["parent_experiment_id"] = PARENT_EXPERIMENT_ID
    validation["parent_all_model_gates_passed"] = bool(
        parent_validation.get("passed")
        and not parent_validation.get("invalid_models")
    )
    reference_ids = {
        f"{case['task_id']}::{case['reference_condition']}"
        for case in cases
    }
    reference_report = {}
    for slug in MODEL_SLUGS:
        raw_path = PARENT / f"models/initial/{slug}/raw/episodes.jsonl"
        rows = {row["episode_id"]: row for row in load_jsonl(raw_path)}
        missing = sorted(reference_ids - set(rows))
        provider_errors = sorted(
            episode_id
            for episode_id in reference_ids
            if episode_id in rows and rows[episode_id].get("provider_error")
        )
        reference_report[slug] = {
            "references_expected": len(reference_ids),
            "references_observed": len(reference_ids) - len(missing),
            "missing": missing,
            "provider_errors": provider_errors,
        }
        if missing or provider_errors:
            validation["errors"].append(f"{slug}: invalid parent references")
    validation["reference_rows"] = reference_report
    validation["passed"] = bool(
        validation["passed"]
        and validation["parent_all_model_gates_passed"]
        and not validation["errors"]
    )
    validation["automatic_gate_passed"] = validation["passed"]
    PACKAGE.mkdir(parents=True, exist_ok=True)
    write_json(PACKAGE / "candidate_tasks.json", tasks)
    write_json(PACKAGE / "cases.json", cases)
    write_json(PACKAGE / "task_validation.json", validation)
    summary = {
        "experiment_id": EXPERIMENT_ID,
        "status": (
            "automatic_gate_passed"
            if validation["passed"]
            else "automatic_gate_failed"
        ),
        "parent_experiment_id": PARENT_EXPERIMENT_ID,
        "formal_tasks": len(tasks),
        "cases_per_model": len(cases),
        "formal_calls": FORMAL_CALLS,
        "models": len(MODEL_SLUGS),
        "candidate_tasks_sha256": sha256_text(canonical_json(tasks)),
        "cases_sha256": sha256_text(canonical_json(cases)),
        "human_review_required": False,
        "human_review_used_as_evidence": False,
    }
    write_json(PACKAGE / "package_summary.json", summary)
    print(canonical_json(summary))
    if not validation["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
