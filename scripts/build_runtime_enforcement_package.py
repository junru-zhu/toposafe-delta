#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from swarmsafe_delta.pilot import canonical_json, load_tasks, sha256_file
from swarmsafe_delta.runtime_enforcement import (
    MODEL_SLUGS,
    SOURCE_STUDIES,
    build_package_rows,
    smoke_cases,
)
from swarmsafe_delta.topology_pilot import load_jsonl


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "experiments/TopoSafe-Delta-AuthorityComposition-v0.2"
PACKAGE = ROOT / "experiments/TopoSafe-Delta-RuntimeEnforcement-v0.1"


def main() -> None:
    tasks = load_tasks(SOURCE / "candidate_tasks.json")
    study_a_validation = json.loads(
        (SOURCE / "models/study_a/validation_report.json").read_text()
    )
    source_rows = []
    source_hashes = {}
    for study in SOURCE_STUDIES:
        for slug in MODEL_SLUGS:
            path = SOURCE / f"models/{study}/{slug}/raw/episodes.jsonl"
            source_hashes[str(path.relative_to(ROOT))] = sha256_file(path)
            model_valid = bool(
                study_a_validation["models"][slug]["passed"]
            )
            source_rows.extend(
                (study, slug, model_valid, row)
                for row in load_jsonl(path)
            )
    replays, cases = build_package_rows(
        tasks=tasks,
        source_rows=source_rows,
    )
    PACKAGE.mkdir(parents=True, exist_ok=True)
    (PACKAGE / "gate_replay.jsonl").write_text(
        "".join(canonical_json(row) + "\n" for row in replays),
        encoding="utf-8",
    )
    (PACKAGE / "recovery_cases.json").write_text(
        json.dumps(cases, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    model_counts = Counter(
        case["source_model_slug"] for case in cases
    )
    selected_smoke = smoke_cases(cases)
    summary = {
        "source_experiment": (
            "TopoSafe-Delta-AuthorityComposition-v0.2"
        ),
        "proof_bearing_source_rows": len(replays),
        "runtime_gate_blocked_rows": len(cases),
        "formal_recovery_calls": len(cases),
        "model_recovery_calls": {
            slug: model_counts[slug] for slug in MODEL_SLUGS
        },
        "excluded_smoke_calls": len(selected_smoke),
        "smoke_calls_by_model": dict(
            Counter(case["source_model_slug"] for case in selected_smoke)
        ),
        "human_review_required": False,
        "human_review_used_as_evidence": False,
        "source_hashes": source_hashes,
    }
    (PACKAGE / "package_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    print(canonical_json(summary))


if __name__ == "__main__":
    main()
