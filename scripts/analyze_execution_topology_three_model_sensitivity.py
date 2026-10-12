#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from swarmsafe_delta.authority_composition import MODEL_CONFIGS
from swarmsafe_delta.execution_topology_confirmatory import (
    analyze_rows,
    validate_rows,
)
from swarmsafe_delta.pilot import canonical_json, sha256_file
from swarmsafe_delta.topology_pilot import load_jsonl


ROOT = Path(__file__).resolve().parent.parent
PARENT = (
    ROOT
    / "experiments/TopoSafe-Delta-ExecutionTopologyConfirmatory-v0.1"
)
R1 = (
    ROOT
    / "experiments/"
    "TopoSafe-Delta-ExecutionTopologyConfirmatory-v0.1R-TechnicalCompletion"
)
PACKAGE = (
    ROOT
    / "experiments/"
    "TopoSafe-Delta-ExecutionTopologyConfirmatory-v0.1S-ThreeModelSensitivity"
)
MODELS = (
    "claude-sonnet-5",
    "nemotron-3-super-120b",
    "llama-4-maverick",
)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(canonical_json(row) + "\n")
    temporary.replace(path)


def _pct(value: float) -> str:
    return f"{value:.1%}"


def main() -> None:
    cases = json.loads(
        (PARENT / "proposal_cases.json").read_text(encoding="utf-8")
    )
    by_model = {
        "claude-sonnet-5": load_jsonl(
            PARENT / "models/claude-sonnet-5/raw/proposals.jsonl"
        ),
        "llama-4-maverick": load_jsonl(
            PARENT / "models/llama-4-maverick/raw/proposals.jsonl"
        ),
    }
    nemotron = {
        row["episode_id"]: row
        for row in load_jsonl(
            PARENT / "models/nemotron-3-super-120b/raw/proposals.jsonl"
        )
    }
    recovery_rows = load_jsonl(
        R1 / "models/nemotron-3-super-120b/raw/proposals.jsonl"
    )
    for row in recovery_rows:
        nemotron[row["episode_id"]] = row
    by_model["nemotron-3-super-120b"] = [
        nemotron[episode_id] for episode_id in sorted(nemotron)
    ]
    validations = {
        slug: validate_rows(rows, cases)
        for slug, rows in by_model.items()
    }
    if not all(row["passed"] for row in validations.values()):
        raise RuntimeError(
            "three-model source validation failed: "
            + canonical_json(validations)
        )
    model_slug_by_id = {
        MODEL_CONFIGS[slug]["model_id"]: slug for slug in MODELS
    }
    result = analyze_rows(
        proposal_rows=[
            row for slug in MODELS for row in by_model[slug]
        ],
        model_slug_by_id=model_slug_by_id,
    )
    layout_rows = result.pop("layout_rows_data")
    result["status"] = "three_model_technical_sensitivity_complete"
    result["available_models"] = list(MODELS)
    result["missing_model"] = "gpt-5.4"
    result["four_model_primary_gate"] = (
        "failed_and_incomplete_due_provider_outage"
    )
    result["model_validations"] = validations
    result["nemotron_recovery_rows"] = len(recovery_rows)
    result["cross_model_replication_claim_allowed"] = False
    result["source_hashes"] = {
        str(path.relative_to(ROOT)): sha256_file(path)
        for path in (
            PARENT / "manifest.json",
            PARENT / "proposal_cases.json",
            PARENT / "models/claude-sonnet-5/raw/proposals.jsonl",
            PARENT / "models/llama-4-maverick/raw/proposals.jsonl",
            PARENT / "models/nemotron-3-super-120b/raw/proposals.jsonl",
            R1 / "manifest.json",
            R1 / "models/nemotron-3-super-120b/raw/proposals.jsonl",
            PACKAGE / "protocol.md",
            Path(__file__),
        )
    }
    analysis_dir = PACKAGE / "analysis"
    write_jsonl(analysis_dir / "layout_rows.jsonl", layout_rows)
    write_json(analysis_dir / "results.json", result)

    key_contrasts = {
        "distributed_unguarded_exposure",
        "distributed_complete_mediation",
        "distributed_source_bypass",
        "distributed_executor_bypass",
        "guarded_single_holder_placement_advisory",
        "guarded_single_holder_placement_utility",
        "guarded_distribution_utility",
    }
    lines = [
        "# Direct Execution Topology Three-Model Sensitivity",
        "",
        (
            "**Status:** complete zero-call technical sensitivity; "
            "not a four-model confirmatory result"
        ),
        "",
        (
            "Available models: Claude Sonnet 5, Nemotron 3 Super 120B, "
            "and Llama 4 Maverick. GPT-5.4 is absent because the parent block "
            "was interrupted and two frozen recovery smoke attempts failed."
        ),
        "",
        (
            f"Validated proposal rows: {result['proposal_rows']}; "
            f"deterministic layout rows: {result['layout_rows']}; "
            f"provider errors after exact Nemotron recovery: "
            f"{result['provider_errors']}; malformed: {result['malformed']}."
        ),
        "",
        "## Key paired effects",
        "",
        "| Model | Authority | Contrast | Effect | 95% CI |",
        "| --- | --- | --- | ---: | ---: |",
    ]
    for row in result["effects"]:
        if row["contrast_id"] not in key_contrasts:
            continue
        lines.append(
            f"| {row['model_slug']} | {row['authority_regime']} | "
            f"{row['contrast_id']} | {_pct(row['estimate'])} | "
            f"[{_pct(row['ci_low'])}, {_pct(row['ci_high'])}] |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "Complete mediation drove invalid-proof executed FAR to zero "
                "for every guarded layout. Where models proposed protected "
                "actions, a single uncovered source or executor edge restored "
                "large executable risk for Llama and Nemotron. Claude proposed "
                "no invalid protected action in these cells, so changing gate "
                "coverage could not alter its executed FAR."
            ),
            "",
            (
                "Expanding unguarded capability from one executor edge to four "
                "role edges produced smaller and model-dependent additional "
                "risk. Single-holder placement and valid-task utility also "
                "remained model- and authority-regime-dependent."
            ),
            "",
            "## Evidence boundary",
            "",
            (
                "The original four-model classification rule is unchanged. "
                "These three-model effects validate the instrument and provide "
                "bounded evidence only; they do not establish cross-model "
                "replication or real-workflow generalization."
            ),
            "",
        ]
    )
    (analysis_dir / "results.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    summary = {
        "status": "three_model_technical_sensitivity_complete",
        "proposal_rows": result["proposal_rows"],
        "layout_rows": result["layout_rows"],
        "available_models": list(MODELS),
        "missing_model": "gpt-5.4",
        "cross_model_replication_claim_allowed": False,
        "results_sha256": sha256_file(analysis_dir / "results.json"),
        "layout_rows_sha256": sha256_file(
            analysis_dir / "layout_rows.jsonl"
        ),
    }
    write_json(analysis_dir / "summary.json", summary)
    print(canonical_json(summary))


if __name__ == "__main__":
    main()
