#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from swarmsafe_delta.authority_composition_control_sensitivity import (
    EXPERIMENT_ID,
    build_report,
    render_markdown,
    sha256_file,
)


ROOT = Path(__file__).resolve().parent.parent
PACKAGE = (
    ROOT
    / "experiments/TopoSafe-Delta-AuthorityCompositionControlSensitivity-v0.1"
)


def main() -> None:
    report = build_report(ROOT)
    PACKAGE.mkdir(parents=True, exist_ok=True)
    analysis = PACKAGE / "analysis"
    analysis.mkdir(parents=True, exist_ok=True)
    results_json = analysis / "results.json"
    results_md = analysis / "results.md"
    results_json.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    results_md.write_text(render_markdown(report), encoding="utf-8")

    source_paths = (
        "experiments/TopoSafe-Delta-AuthorityComposition-v0.2/"
        "analysis/results.json",
        "experiments/TopoSafe-Delta-AuthorityComposition-v0.2/"
        "models/study_a/validation_report.json",
        "experiments/TopoSafe-Delta-RuntimeEnforcement-v0.2/protocol.md",
        "experiments/TopoSafe-Delta-RuntimeEnforcement-v0.2/"
        "models/initial_validation_report.json",
        "experiments/TopoSafe-Delta-AuthorityCompositionControlSensitivity-"
        "v0.1/design_spec.json",
        "experiments/TopoSafe-Delta-AuthorityCompositionControlSensitivity-"
        "v0.1/protocol.md",
        "scripts/analyze_authority_composition_control_sensitivity.py",
        "src/swarmsafe_delta/"
        "authority_composition_control_sensitivity.py",
        "tests/test_authority_composition_control_sensitivity.py",
    )
    manifest = {
        "experiment_id": EXPERIMENT_ID,
        "status": report["evidence_status"],
        "new_provider_calls": 0,
        "human_review_required": False,
        "source_hashes": {
            relative: sha256_file(ROOT / relative)
            for relative in source_paths
        },
    }
    (PACKAGE / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": report["evidence_status"],
                "new_provider_calls": 0,
                "original_invalid_models": report[
                    "original_preregistered_gate"
                ]["invalid_models"],
                "sensitivity_valid_models": report[
                    "post_hoc_sensitivity_gate"
                ]["valid_models"],
                "threshold_regimes_replicated_at_three_models": report[
                    "threshold_replication"
                ]["regimes_replicated_at_three_models"],
                "results": str(results_md.relative_to(ROOT)),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
