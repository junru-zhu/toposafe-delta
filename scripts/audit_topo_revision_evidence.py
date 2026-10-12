#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from swarmsafe_delta.topo_revision_common import load_jsonl, utc_now, write_json


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "experiments/topo_revision/existing_evidence_audit.json"


CHECKS = (
    {
        "id": "authority_placement_v1_6",
        "glob": (
            "experiments/TopoSafe-Delta-AuthorityPlacement-v1.6/"
            "models/*/raw/episodes.jsonl"
        ),
        "expected_rows": 1008,
        "results": (
            "experiments/TopoSafe-Delta-AuthorityPlacement-v1.6/"
            "analysis/multimodel_summary.json"
        ),
    },
    {
        "id": "authority_composition_v0_2",
        "glob": (
            "experiments/TopoSafe-Delta-AuthorityComposition-v0.2/"
            "models/*/*/raw/episodes.jsonl"
        ),
        "expected_rows": 7440,
        "results": (
            "experiments/TopoSafe-Delta-AuthorityComposition-v0.2/"
            "analysis/results.json"
        ),
    },
    {
        "id": "runtime_enforcement_v0_2_initial",
        "glob": (
            "experiments/TopoSafe-Delta-RuntimeEnforcement-v0.2/"
            "models/initial/*/raw/episodes.jsonl"
        ),
        "expected_rows": 2688,
        "results": (
            "experiments/TopoSafe-Delta-RuntimeEnforcement-v0.2/"
            "analysis/results.json"
        ),
    },
    {
        "id": "runtime_enforcement_v0_2_recovery",
        "glob": (
            "experiments/TopoSafe-Delta-RuntimeEnforcement-v0.2/"
            "models/recovery/*/raw/recovery.jsonl"
        ),
        "expected_rows": 257,
        "results": (
            "experiments/TopoSafe-Delta-RuntimeEnforcement-v0.2/"
            "analysis/results.json"
        ),
    },
    {
        "id": "matched_communication_v0_1",
        "glob": (
            "experiments/TopoSafe-Delta-MatchedCommunication-v0.1/"
            "models/*/raw/episodes.jsonl"
        ),
        "expected_rows": 12480,
        "results": (
            "experiments/TopoSafe-Delta-MatchedCommunication-v0.1/"
            "analysis/results.json"
        ),
    },
    {
        "id": "free_running_communication_v0_3",
        "glob": (
            "experiments/TopoSafe-Delta-FreeRunningCommunication-v0.3/"
            "models/*/raw/episodes.jsonl"
        ),
        "expected_rows": 2880,
        "results": (
            "experiments/TopoSafe-Delta-FreeRunningCommunication-v0.3/"
            "analysis/results.json"
        ),
    },
    {
        "id": "free_running_schedule_replication",
        "glob": (
            "experiments/TopoSafe-Delta-FreeRunningScheduleReplication-v0.1/"
            "models/*/raw/episodes.jsonl"
        ),
        "expected_rows": 2880,
        "results": (
            "experiments/TopoSafe-Delta-FreeRunningScheduleReplication-v0.1/"
            "analysis/results.json"
        ),
    },
    {
        "id": "authority_mechanism_ablations",
        "glob": (
            "experiments/TopoSafe-Delta-AuthorityMechanismAblations-v0.1/"
            "models/*/raw/episodes.jsonl"
        ),
        "expected_rows": 1200,
        "results": (
            "experiments/TopoSafe-Delta-AuthorityMechanismAblations-v0.1/"
            "analysis/results.json"
        ),
    },
)


def run_check(spec: dict[str, Any]) -> dict[str, Any]:
    paths = sorted(ROOT.glob(spec["glob"]))
    rows = sum(len(load_jsonl(path)) for path in paths)
    results = ROOT / spec["results"]
    return {
        **spec,
        "raw_files": [str(path.relative_to(ROOT)) for path in paths],
        "observed_rows": rows,
        "row_count_matches": rows == spec["expected_rows"],
        "results_file_exists": results.exists(),
        "passed": bool(
            paths
            and rows == spec["expected_rows"]
            and results.exists()
        ),
    }


def main() -> None:
    checks = [run_check(spec) for spec in CHECKS]
    report = {
        "audited_at": utc_now(),
        "status": (
            "existing_evidence_inventory_verified"
            if all(check["passed"] for check in checks)
            else "existing_evidence_inventory_mismatch"
        ),
        "checks": checks,
        "historical_formal_call_total": 66090,
        "note": (
            "This script verifies checked-in row inventories and result "
            "presence. The isolated analyzer rerun is documented separately "
            "in EXISTING_EVIDENCE_AUDIT.md."
        ),
    }
    write_json(OUTPUT, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    if not all(check["passed"] for check in checks):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
