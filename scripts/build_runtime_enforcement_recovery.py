#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from swarmsafe_delta.pilot import canonical_json, load_tasks, sha256_file, utc_now
from swarmsafe_delta.runtime_enforcement_factorial import (
    MAX_RECOVERY_CALLS,
    MODEL_SLUGS,
    build_gate_rows_and_recovery_cases,
)
from swarmsafe_delta.topology_pilot import load_jsonl


ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "experiments/TopoSafe-Delta-RuntimeEnforcement-v0.2"


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    recovery_raw = list((PACKAGE / "models/recovery").glob("**/*.jsonl"))
    if recovery_raw:
        raise RuntimeError("Refusing to rebuild recovery cases after calls exist")
    root_manifest_path = PACKAGE / "manifest.json"
    validation_path = PACKAGE / "models/initial_validation_report.json"
    root_manifest = json.loads(root_manifest_path.read_text())
    validation = json.loads(validation_path.read_text())
    if not validation["passed"]:
        raise RuntimeError("Initial model validation did not pass")
    tasks = load_tasks(ROOT / root_manifest["task_file"])
    initial_rows = []
    source_hashes = {}
    for slug in MODEL_SLUGS:
        path = PACKAGE / f"models/initial/{slug}/raw/episodes.jsonl"
        source_hashes[str(path.relative_to(ROOT))] = sha256_file(path)
        initial_rows.extend(
            (slug, validation["models"][slug]["passed"], row)
            for row in load_jsonl(path)
        )
    gate_rows, recovery_cases = build_gate_rows_and_recovery_cases(
        tasks=tasks,
        initial_rows=initial_rows,
    )
    if len(recovery_cases) > MAX_RECOVERY_CALLS:
        raise RuntimeError("Recovery trigger count exceeds frozen maximum")
    (PACKAGE / "gate_replay.jsonl").write_text(
        "".join(canonical_json(row) + "\n" for row in gate_rows),
        encoding="utf-8",
    )
    write_json(PACKAGE / "recovery_cases.json", recovery_cases)
    counts = Counter(
        case["source_model_slug"] for case in recovery_cases
    )
    recovery_manifest = {
        "experiment_id": root_manifest["experiment_id"],
        "status": "derived_from_frozen_initial_rule",
        "created_at": utc_now(),
        "root_manifest_sha256": sha256_file(root_manifest_path),
        "initial_validation_sha256": sha256_file(validation_path),
        "initial_source_hashes": source_hashes,
        "gate_replay_rows": len(gate_rows),
        "formal_recovery_calls": len(recovery_cases),
        "maximum_formal_recovery_calls": MAX_RECOVERY_CALLS,
        "model_recovery_calls": {
            slug: counts[slug] for slug in MODEL_SLUGS
        },
        "manual_recovery_selection": False,
        "human_review_required": False,
        "human_review_used_as_evidence": False,
    }
    write_json(PACKAGE / "recovery_manifest.json", recovery_manifest)
    print(canonical_json(recovery_manifest))


if __name__ == "__main__":
    main()
