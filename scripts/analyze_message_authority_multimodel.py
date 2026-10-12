#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from swarmsafe_delta.message_authority_calibration import (
    ALL_AUTHORITY_CONDITIONS,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate message-authority calibration model results."
    )
    parser.add_argument(
        "--experiment-dir",
        type=Path,
        default=Path(
            "experiments/TopoSafe-Delta-MessageAuthorityCalibration-v1"
        ),
    )
    parser.add_argument("--model-slug", action="append", default=[])
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    args = parse_args()
    model_dirs = sorted(
        path
        for path in (args.experiment_dir / "models").iterdir()
        if path.is_dir()
        and (not args.model_slug or path.name in set(args.model_slug))
    )
    models = []
    for model_dir in model_dirs:
        summary_path = model_dir / "analysis" / "summary.json"
        manifest_path = model_dir / "manifest.json"
        if not summary_path.exists() or not manifest_path.exists():
            continue
        summary = load_json(summary_path)
        manifest = load_json(manifest_path)
        models.append(
            {
                "model_slug": model_dir.name,
                "model_id": manifest["model_id"],
                "episodes": summary["episodes"],
                "valid_episodes": summary["valid_episodes"],
                "total_tokens": summary["total_tokens"],
                "status": summary["status"],
                "selected_condition": summary["selected_condition"],
                "condition_order": summary["condition_order"],
                "by_condition": summary["by_condition"],
                "validation": summary["validation"],
            }
        )

    output = {
        "status": "development_multimodel_authority_calibration",
        "models": models,
        "model_count": len(models),
        "episodes": sum(model["episodes"] for model in models),
        "valid_episodes": sum(
            model["valid_episodes"] for model in models
        ),
        "total_tokens": sum(model["total_tokens"] for model in models),
        "provider_errors": sum(
            model["validation"]["provider_errors"] for model in models
        ),
        "evidence_boundary": (
            "Descriptive multi-model development calibration. Selected "
            "conditions are outcome-dependent and require fresh validation."
        ),
    }
    analysis_dir = args.experiment_dir / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    (analysis_dir / "multimodel_summary.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )

    condition_order = models[0]["condition_order"] if models else []
    lines = [
        "# TopoSafe-Delta Multi-Model Message-Authority Calibration",
        "",
        "**Status:** Development evidence only.",
        "",
        "## False-State Acceptance",
        "",
        "| Model | "
        + " | ".join(condition_order)
        + " | Calibration |",
        "| --- | "
        + " | ".join("---:" for _ in condition_order)
        + " | --- |",
    ]
    for model in models:
        cells = []
        for condition in model["condition_order"]:
            row = model["by_condition"][condition]
            cells.append(f"{row['violations']}/{row['episodes']}")
        lines.append(
            f"| {model['model_slug']} | {' | '.join(cells)} | "
            f"{model['selected_condition'] or model['status']} |"
        )
    lines.extend(
        [
            "",
            "## Validation",
            "",
            f"- Models: {output['model_count']}; episodes: "
            f"{output['episodes']}; valid: {output['valid_episodes']}.",
            f"- Provider errors: {output['provider_errors']}.",
            f"- Total tokens: {output['total_tokens']}.",
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
    print(json.dumps(output, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
