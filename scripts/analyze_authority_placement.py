#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from swarmsafe_delta.authority_placement import (
    AUTHORITY_PLACEMENTS,
    CREDENTIALS,
    MODEL_CONFIGS,
)
from swarmsafe_delta.pilot import canonical_json


ROOT = Path("experiments/TopoSafe-Delta-AuthorityPlacement-v1.6")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("smoke", "formal"), default="formal")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    args = parse_args()
    stage_root = ROOT / ("smoke" if args.stage == "smoke" else "models")
    summaries = []
    for slug in MODEL_CONFIGS:
        path = stage_root / slug / "analysis" / "summary.json"
        if path.exists():
            summaries.append(load_json(path))
    output = {
        "status": (
            "valid_development_evidence"
            if summaries
            and all(
                summary["validation"]["passed"] for summary in summaries
            )
            and len(summaries) == len(MODEL_CONFIGS)
            else "invalid_or_incomplete"
        ),
        "stage": args.stage,
        "models": summaries,
        "model_count": len(summaries),
        "episodes": sum(summary["episodes"] for summary in summaries),
        "total_tokens": sum(
            summary["total_tokens"] for summary in summaries
        ),
        "provider_errors": sum(
            summary["validation"]["provider_errors"]
            for summary in summaries
        ),
        "verified": [],
        "inferred": [],
        "unknown": [
            "Generalization beyond the tested synthetic tasks and providers.",
            "Free-running intermediate-agent behavior; messages are frozen.",
        ],
        "invalid_excluded": [
            summary["model_slug"]
            for summary in summaries
            if not summary["validation"]["passed"]
        ],
        "evidence_boundary": (
            "Model-specific development estimates. Combined rows are "
            "descriptive and are not pooled model rankings."
        ),
    }
    if output["status"] == "valid_development_evidence":
        output["verified"].append(
            "All frozen prompt, budget, scorer, control, provider, and "
            "truncation gates passed."
        )
        output["inferred"].append(
            "Credential and authority-placement effects should be interpreted "
            "per model using paired task-level contrasts."
        )

    analysis_dir = (
        ROOT / "analysis"
        if args.stage == "formal"
        else ROOT / "smoke" / "analysis"
    )
    analysis_dir.mkdir(parents=True, exist_ok=True)
    (analysis_dir / "multimodel_summary.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    lines = [
        "# TopoSafe-Delta Authority-Placement Multi-Model Summary",
        "",
        f"**Status:** `{output['status']}`",
        "",
        "## FAR / TUR / TCG",
        "",
        "| Model | Placement | Credential | FAR | TUR | TCG |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for summary in summaries:
        for placement in AUTHORITY_PLACEMENTS:
            for credential in CREDENTIALS:
                row = summary["trust_metrics"][
                    f"{placement}::{credential}"
                ]
                lines.append(
                    f"| {summary['model_slug']} | {placement} | "
                    f"{credential} | "
                    f"{row['false_state_acceptance_rate']:.3f} | "
                    f"{row['true_state_utilization_rate']:.3f} | "
                    f"{row['trust_calibration_gap']:+.3f} |"
                )
    lines.extend(
        [
            "",
            "## Credential Safety Cost",
            "",
            "| Model | Source | Relay | Verifier |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for summary in summaries:
        effects = summary["credential_effects"]
        lines.append(
            f"| {summary['model_slug']} | "
            f"{effects['source_authority']['credential_safety_cost']['estimate']:+.3f} | "
            f"{effects['relay_authority']['credential_safety_cost']['estimate']:+.3f} | "
            f"{effects['verifier_authority']['credential_safety_cost']['estimate']:+.3f} |"
        )
    lines.extend(
        [
            "",
            "## Validation",
            "",
            f"- Models: {output['model_count']}; episodes: "
            f"{output['episodes']}.",
            f"- Provider errors: {output['provider_errors']}.",
            f"- Total tokens: {output['total_tokens']}.",
            f"- Invalid/excluded: "
            f"{', '.join(output['invalid_excluded']) or 'none'}.",
            "",
            "## Evidence Boundary",
            "",
            output["evidence_boundary"],
            "",
        ]
    )
    (analysis_dir / "multimodel_summary.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )
    print(canonical_json(output))


if __name__ == "__main__":
    main()
