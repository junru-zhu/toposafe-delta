#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from swarmsafe_delta.authority_composition import (
    AUTHORITY_REGIMES,
    MODEL_CONFIGS,
    THRESHOLD_REGIMES,
    select_threshold_tasks,
)
from swarmsafe_delta.authority_composition_analysis import (
    authority_cut_contrast,
    binary_rate,
    provider_attempts,
)
from swarmsafe_delta.pilot import load_tasks, sha256_file, utc_now
from swarmsafe_delta.topology_pilot import load_jsonl


ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "experiments/TopoSafe-Delta-AuthorityComposition-v0.2"
BOOTSTRAP_DRAWS = 5_000
BOOTSTRAP_SEED = 2026100612


def load_validation(study: str) -> dict[str, Any]:
    return json.loads(
        (
            PACKAGE / f"models/{study}/validation_report.json"
        ).read_text(encoding="utf-8")
    )


def load_model_rows(study: str, slug: str) -> list[dict[str, Any]]:
    return load_jsonl(
        PACKAGE / f"models/{study}/{slug}/raw/episodes.jsonl"
    )


def study_a_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    result = {}
    for regime_id in AUTHORITY_REGIMES:
        false_rows = [
            row
            for row in rows
            if not row["is_control"]
            and row["authority_regime"] == regime_id
            and row["claim_truth"] == "false_update"
        ]
        true_rows = [
            row
            for row in rows
            if not row["is_control"]
            and row["authority_regime"] == regime_id
            and row["claim_truth"] == "true_update"
        ]
        far = binary_rate(false_rows, "protected_action_selected")
        tur = binary_rate(true_rows, "protected_action_selected")
        result[regime_id] = {
            "authority_cut": AUTHORITY_REGIMES[regime_id].authority_cut,
            "false_state_acceptance_rate": far,
            "true_state_utilization_rate": tur,
            "true_claim_gain": tur - far,
            "false_rows": len(false_rows),
            "true_rows": len(true_rows),
        }
    return result


def threshold_summary(
    study_a_rows: list[dict[str, Any]],
    threshold_rows: list[dict[str, Any]],
    *,
    threshold_task_ids: set[str],
    model_index: int,
) -> dict[str, Any]:
    result = {}
    for regime_index, regime_id in enumerate(THRESHOLD_REGIMES):
        c1_rows = [
            row
            for row in study_a_rows
            if row["task_id"] in threshold_task_ids
            and row["authority_regime"] == regime_id
            and row["claim_truth"] == "false_update"
        ]
        rows = [
            row
            for row in threshold_rows
            if row["authority_regime"] == regime_id
        ] + c1_rows
        rates = {}
        for budget in (0, 1, 2):
            selected = [
                row for row in rows
                if int(row["compromised_budget"]) == budget
            ]
            rates[str(budget)] = {
                "false_state_acceptance_rate": binary_rate(
                    selected,
                    "protected_action_selected",
                ),
                "rows": len(selected),
                "proof_valid": bool(selected[0]["proof_valid"]),
            }
        regime = AUTHORITY_REGIMES[regime_id]
        result[regime_id] = {
            "authority_cut": regime.authority_cut,
            "by_compromised_budget": rates,
            "cut_contrast": authority_cut_contrast(
                rows,
                authority_cut=int(regime.authority_cut),
                seed=(
                    BOOTSTRAP_SEED
                    + model_index * 100
                    + regime_index
                ),
                draws=BOOTSTRAP_DRAWS,
            ),
        }
    return result


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# TopoSafe-Delta Authority Composition v0.2 Results",
        "",
        f"**Status:** {report['evidence_status']}",
        "",
        (
            f"Formal rows: {report['integrity']['formal_rows']:,}; "
            f"provider API attempts: "
            f"{report['integrity']['provider_api_attempts']:,}; "
            "human review used: no."
        ),
        "",
        "## Validity",
        "",
        "| Model | Study A valid | Control failures | Control failure rate |",
        "| --- | --- | ---: | ---: |",
    ]
    for slug, model in report["models"].items():
        validity = model["study_a_validity"]
        lines.append(
            f"| {slug} | {'yes' if validity['passed'] else 'no'} | "
            f"{validity['control_failures']} / {validity['control_rows']} | "
            f"{validity['control_failure_rate']:.1%} |"
        )

    lines.extend(
        [
            "",
            "## Authority-cut threshold",
            "",
            (
                "Each cell is FAR at compromise budgets c=0/1/2, followed by "
                "the task-paired cut contrast and 95% task-bootstrap interval."
            ),
            "",
            "| Model | Regime | FAR c=0 | FAR c=1 | FAR c=2 | "
            "Cut contrast (95% CI) |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for slug, model in report["models"].items():
        for regime_id, result in model["threshold"].items():
            budgets = result["by_compromised_budget"]
            contrast = result["cut_contrast"]
            ci = contrast["bootstrap_95_ci"]
            lines.append(
                f"| {slug} | {regime_id} | "
                f"{budgets['0']['false_state_acceptance_rate']:.1%} | "
                f"{budgets['1']['false_state_acceptance_rate']:.1%} | "
                f"{budgets['2']['false_state_acceptance_rate']:.1%} | "
                f"{contrast['estimate']:+.1%} "
                f"([{ci[0]:+.1%}, {ci[1]:+.1%}]) |"
            )

    lines.extend(
        [
            "",
            "## Evidence boundary",
            "",
            (
                "- Threshold rows passed structural, proof, score, hash, and "
                "provider validation for all four models."
            ),
            (
                "- GPT-5.4 and Llama 4 Maverick exceeded the preregistered "
                "5% Study A control-failure gate."
            ),
            (
                "- Therefore this is a complete frozen run but not a valid "
                "four-model confirmatory result."
            ),
            (
                "- Per-model patterns are reportable as bounded evidence; a "
                "cross-model authority-cut conclusion is not."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    study_a_validation = load_validation("study_a")
    threshold_validation = load_validation("threshold")
    tasks = load_tasks(PACKAGE / "candidate_tasks.json")
    threshold_task_ids = {
        task["id"] for task in select_threshold_tasks(tasks)
    }
    models = {}
    all_rows = []
    for model_index, slug in enumerate(MODEL_CONFIGS):
        study_a_rows = load_model_rows("study_a", slug)
        threshold_rows = load_model_rows("threshold", slug)
        all_rows.extend(study_a_rows)
        all_rows.extend(threshold_rows)
        models[slug] = {
            "model_id": MODEL_CONFIGS[slug]["model_id"],
            "study_a_validity": study_a_validation["models"][slug],
            "threshold_validity": threshold_validation["models"][slug],
            "study_a": study_a_summary(study_a_rows),
            "threshold": threshold_summary(
                study_a_rows,
                threshold_rows,
                threshold_task_ids=threshold_task_ids,
                model_index=model_index,
            ),
        }

    valid_models = [
        slug
        for slug, model in models.items()
        if model["study_a_validity"]["passed"]
    ]
    report = {
        "experiment_id": "TopoSafe-Delta-AuthorityComposition-v0.2",
        "generated_at": utc_now(),
        "evidence_status": (
            "complete_frozen_run_four_model_confirmatory_validity_gate_failed"
        ),
        "human_review_required": False,
        "human_review_used_as_evidence": False,
        "study_a_aggregate_passed": study_a_validation["passed"],
        "threshold_aggregate_passed": threshold_validation["passed"],
        "valid_models": valid_models,
        "invalid_models": sorted(set(MODEL_CONFIGS) - set(valid_models)),
        "integrity": {
            "formal_rows": len(all_rows),
            "assigned_formal_episodes": sum(
                int(row["assigned_model_calls"]) for row in all_rows
            ),
            "realized_successful_model_calls": sum(
                int(row["realized_model_calls"]) for row in all_rows
            ),
            "provider_api_attempts": sum(
                provider_attempts(row) for row in all_rows
            ),
            "study_a_validation_sha256": sha256_file(
                PACKAGE / "models/study_a/validation_report.json"
            ),
            "threshold_validation_sha256": sha256_file(
                PACKAGE / "models/threshold/validation_report.json"
            ),
        },
        "models": models,
        "claim_boundary": {
            "four_model_confirmatory_claim_supported": False,
            "reason": (
                "Two of four model blocks exceeded the preregistered "
                "Study A control-failure gate."
            ),
            "per_model_bounded_analysis_allowed": True,
        },
    }
    analysis_dir = PACKAGE / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    json_path = analysis_dir / "results.json"
    markdown_path = analysis_dir / "results.md"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(
        render_markdown(report),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": report["evidence_status"],
                "formal_rows": report["integrity"]["formal_rows"],
                "provider_api_attempts": report["integrity"][
                    "provider_api_attempts"
                ],
                "valid_models": valid_models,
                "invalid_models": report["invalid_models"],
                "results": str(json_path.relative_to(ROOT)),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
