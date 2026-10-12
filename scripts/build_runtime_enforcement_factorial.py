#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from swarmsafe_delta.authority_task_construction import (
    build_tasks,
    load_catalog,
)
from swarmsafe_delta.pilot import canonical_json, load_tasks
from swarmsafe_delta.runtime_enforcement_factorial import (
    EXPERIMENT_ID,
    FORMAL_INITIAL_CALLS,
    MAX_RECOVERY_CALLS,
    build_initial_cases,
    validate_fresh_task_package,
)
from swarmsafe_delta.topology_pilot import sha256_text


ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "experiments/TopoSafe-Delta-RuntimeEnforcement-v0.2"
CATALOG = ROOT / "data/toposafe_runtime_enforcement_task_catalog_v0.2.json"
PRIOR_CATALOG = ROOT / "data/toposafe_authority_task_catalog_v0.1.json"
PRIOR_TASKS = (
    ROOT / "experiments/TopoSafe-Delta-AuthorityComposition-v0.2/"
    "candidate_tasks.json"
)
DEVELOPMENT_TASKS = ROOT / "data/authority_placement_tasks_v1.json"


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    catalog = load_catalog(CATALOG)
    prior_catalog = load_catalog(PRIOR_CATALOG)
    tasks = build_tasks(catalog)
    prior_tasks = [
        *load_tasks(PRIOR_TASKS),
        *load_tasks(DEVELOPMENT_TASKS),
    ]
    validation = validate_fresh_task_package(
        catalog=catalog,
        tasks=tasks,
        prior_catalog=prior_catalog,
        prior_tasks=prior_tasks,
    )
    cases = build_initial_cases(tasks)
    PACKAGE.mkdir(parents=True, exist_ok=True)
    write_json(PACKAGE / "candidate_tasks.json", tasks)
    write_json(PACKAGE / "initial_cases.json", cases)
    write_json(PACKAGE / "task_validation.json", validation)
    summary = {
        "experiment_id": EXPERIMENT_ID,
        "status": (
            "automatic_gate_passed"
            if validation["automatic_gate_passed"]
            else "automatic_gate_failed"
        ),
        "catalog_rows": len(catalog),
        "fresh_tasks": len(tasks),
        "initial_cases_per_model": len(cases),
        "formal_initial_calls": FORMAL_INITIAL_CALLS,
        "maximum_formal_recovery_calls": MAX_RECOVERY_CALLS,
        "candidate_tasks_sha256": sha256_text(canonical_json(tasks)),
        "initial_cases_sha256": sha256_text(canonical_json(cases)),
        "human_review_required": False,
        "human_review_used_as_evidence": False,
    }
    write_json(PACKAGE / "package_summary.json", summary)
    print(canonical_json(summary))
    if not validation["automatic_gate_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
