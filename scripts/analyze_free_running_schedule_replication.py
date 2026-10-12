#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from swarmsafe_delta.free_running_schedule_replication import (
    ANALYSIS_BOOTSTRAP_SEED,
    EXPERIMENT_ID,
    PARENT_EXPERIMENT_ID,
)
from swarmsafe_delta.pilot import canonical_json, sha256_file
from swarmsafe_delta.topology_pilot import load_jsonl


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts import analyze_free_running_communication as base_analysis  # noqa: E402


PACKAGE = (
    ROOT / "experiments/TopoSafe-Delta-FreeRunningScheduleReplication-v0.1"
)
PARENT = ROOT / "experiments/TopoSafe-Delta-FreeRunningCommunication-v0.3"
B1 = ROOT / "experiments/TopoSafe-Delta-MatchedCommunication-v0.1"
MODEL_SLUGS = base_analysis.MODEL_SLUGS
TOPOLOGY_IDS = base_analysis.TOPOLOGY_IDS
THRESHOLD_REGIMES = base_analysis.THRESHOLD_REGIMES
OUTCOMES = (
    ("advisory_far", "false_update", "protected_action_selected"),
    ("executed_far", "false_update", "executed_violation"),
    ("true_utilization", "true_update", "protected_action_selected"),
)


def schedule_contrast_difference(
    replication_rows: list[dict[str, Any]],
    parent_rows: list[dict[str, Any]],
    *,
    topology_id: str,
    authority_regime: str,
    claim_truth: str,
    field: str,
    seed: int,
) -> dict[str, Any]:
    def index(
        rows: list[dict[str, Any]],
    ) -> dict[tuple[str, str], float]:
        return {
            (row["task_id"], row["topology_id"]): float(bool(row[field]))
            for row in rows
            if row["topology_id"] in {"topo_A", topology_id}
            and row["authority_regime"] == authority_regime
            and row["claim_truth"] == claim_truth
        }

    replication = index(replication_rows)
    parent = index(parent_rows)
    task_ids = sorted(
        task_id
        for task_id, topology in replication
        if topology == "topo_A"
        and (task_id, topology_id) in replication
        and (task_id, "topo_A") in parent
        and (task_id, topology_id) in parent
    )
    if not task_ids:
        raise ValueError("Schedule comparison requires common task pairs")
    deltas = {
        task_id: (
            replication[(task_id, topology_id)]
            - replication[(task_id, "topo_A")]
            - parent[(task_id, topology_id)]
            + parent[(task_id, "topo_A")]
        )
        for task_id in task_ids
    }
    return {
        "reference_schedule": PARENT_EXPERIMENT_ID,
        "replication_schedule": EXPERIMENT_ID,
        "reference_topology": "topo_A",
        "treated_topology": topology_id,
        "authority_regime": authority_regime,
        "claim_truth": claim_truth,
        "field": field,
        "estimand": "replication_topology_effect_minus_parent_topology_effect",
        **base_analysis.bootstrap_effect(deltas, seed=seed),
    }


def joint_classification(
    parent_models: dict[str, Any],
    replication_models: dict[str, Any],
    *,
    field: str,
) -> dict[str, Any]:
    keys = sorted(
        set.intersection(
            *[
                set(replication_models[slug][field])
                for slug in MODEL_SLUGS
            ]
        )
    )
    replicated = []
    conditional = []
    opposite = []
    jointly_equivalent = []
    for key in keys:
        positive = []
        negative = []
        opposite_models = []
        for slug in MODEL_SLUGS:
            parent = parent_models[slug][field][key]
            replication = replication_models[slug][field][key]
            parent_large = bool(
                parent["large_effect"] and parent["ci_excludes_zero"]
            )
            replication_large = bool(
                replication["large_effect"]
                and replication["ci_excludes_zero"]
            )
            if parent_large and replication_large:
                if parent["estimate"] > 0 and replication["estimate"] > 0:
                    positive.append(slug)
                elif parent["estimate"] < 0 and replication["estimate"] < 0:
                    negative.append(slug)
                else:
                    opposite_models.append(slug)
        support = positive if len(positive) >= len(negative) else negative
        item = {
            "contrast": key,
            "models": support,
            "direction": "positive" if support is positive else "negative",
        }
        if len(support) >= 3:
            replicated.append(item)
        elif support:
            conditional.append(item)
        if opposite_models:
            opposite.append(
                {"contrast": key, "models": opposite_models}
            )
        if all(
            parent_models[slug][field][key]["practically_equivalent"]
            and replication_models[slug][field][key][
                "practically_equivalent"
            ]
            for slug in MODEL_SLUGS
        ):
            jointly_equivalent.append(key)
    return {
        "replicated_large_effects_in_both_schedules": replicated,
        "model_conditional_large_effects_in_both_schedules": conditional,
        "opposite_large_effects_between_schedules": opposite,
        "jointly_practically_equivalent_contrasts": jointly_equivalent,
    }


def render_markdown(report: dict[str, Any]) -> str:
    original = report["classification"]["parent"]
    replication = report["classification"]["replication"]
    joint = report["classification"]["cross_schedule"]
    shift = report["classification"]["schedule_difference"]
    lines = [
        "# TopoSafe-Delta Free-Running Schedule Replication v0.1 Results",
        "",
        f"**Status:** {report['evidence_status']}",
        "",
        (
            f"Formal episodes: {report['integrity']['formal_episodes']:,}; "
            f"assigned model calls: "
            f"{report['integrity']['assigned_model_calls']:,}; provider "
            f"attempts including retries: "
            f"{report['integrity']['provider_api_attempts']:,}; human review "
            "used: no."
        ),
        "",
        "## Model validity",
        "",
        "| Model | Valid | Active forward failure | Executor failure | Invalid-proof executions |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for slug in MODEL_SLUGS:
        model = report["models"][slug]
        lines.append(
            f"| {slug} | {'yes' if model['valid'] else 'no'} | "
            f"{model['active_forward_failure_rate']:.1%} | "
            f"{model['executor_failure_rate']:.1%} | "
            f"{model['invalid_proof_executions']} |"
        )
    lines.extend(
        [
            "",
            "## Classification across schedules",
            "",
            "| Analysis | Parent B2 | Schedule replication | Large in both schedules and at least three models |",
            "| --- | ---: | ---: | ---: |",
            (
                "| Total topology effect | "
                f"{len(original['b2_total_effect']['replicated_large_effects'])} | "
                f"{len(replication['b2_total_effect']['replicated_large_effects'])} | "
                f"{len(joint['b2_total_effect']['replicated_large_effects_in_both_schedules'])} |"
            ),
            (
                "| Semantic increment over B1 | "
                f"{len(original['semantic_increment']['replicated_large_effects'])} | "
                f"{len(replication['semantic_increment']['replicated_large_effects'])} | "
                f"{len(joint['semantic_increment']['replicated_large_effects_in_both_schedules'])} |"
            ),
            "",
            (
                "Replicated large schedule shifts: "
                f"{len(shift['replicated_large_effects'])}."
            ),
            (
                "Model-conditional large schedule shifts: "
                f"{len(shift['model_conditional_large_effects'])}."
            ),
            (
                "Schedule-difference contrasts practically equivalent across "
                f"all models: {len(shift['practically_equivalent_contrasts'])}/27."
            ),
            "",
            "## Largest schedule difference by model",
            "",
            "| Model | Contrast | Replication minus parent [95% CI] |",
            "| --- | --- | ---: |",
        ]
    )
    for slug in MODEL_SLUGS:
        effects = report["models"][slug]["schedule_difference_effects"]
        key, effect = max(
            effects.items(), key=lambda item: abs(item[1]["estimate"])
        )
        lines.append(
            f"| {slug} | `{key}` | {effect['estimate']:+.1%} "
            f"[{effect['ci_low']:+.1%}, {effect['ci_high']:+.1%}] |"
        )
    lines.extend(
        [
            "",
            "## Evidence boundary",
            "",
            (
                "The provider does not expose a sampling seed. This experiment "
                "replicates the execution schedule and request ordering while "
                "holding tasks, prompts, models, budgets, scoring, and gates "
                "fixed."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    validation_path = PACKAGE / "models/validation_report.json"
    validation = json.loads(validation_path.read_text())
    parent_results_path = PARENT / "analysis/results.json"
    parent_results = json.loads(parent_results_path.read_text())
    replication_models = {}
    parent_models = parent_results["models"]
    for model_index, slug in enumerate(MODEL_SLUGS):
        replication_rows = load_jsonl(
            PACKAGE / f"models/{slug}/raw/episodes.jsonl"
        )
        parent_rows = load_jsonl(
            PARENT / f"models/{slug}/raw/episodes.jsonl"
        )
        b1_rows = load_jsonl(B1 / f"models/{slug}/raw/episodes.jsonl")
        summary = base_analysis.model_summary(
            replication_rows,
            b1_rows,
            validation["models"][slug],
            model_index=model_index,
        )
        schedule_differences = {}
        effect_index = 0
        for topology_id in TOPOLOGY_IDS[1:]:
            for regime in THRESHOLD_REGIMES:
                for outcome, truth, field in OUTCOMES:
                    key = f"{topology_id}::{regime}::{outcome}"
                    schedule_differences[key] = schedule_contrast_difference(
                        replication_rows,
                        parent_rows,
                        topology_id=topology_id,
                        authority_regime=regime,
                        claim_truth=truth,
                        field=field,
                        seed=(
                            ANALYSIS_BOOTSTRAP_SEED
                            + model_index * 10_000
                            + effect_index
                        ),
                    )
                    effect_index += 1
        summary["schedule_difference_effects"] = schedule_differences
        replication_models[slug] = summary

    schedule_models = {
        slug: {
            "valid": replication_models[slug]["valid"],
            "schedule_difference_effects": replication_models[slug][
                "schedule_difference_effects"
            ],
        }
        for slug in MODEL_SLUGS
    }
    replication_classification = {
        "b2_total_effect": base_analysis.classify(
            replication_models, field="b2_effects_vs_topo_A"
        ),
        "semantic_increment": base_analysis.classify(
            replication_models, field="semantic_increments_vs_topo_A"
        ),
    }
    cross_schedule = {
        "b2_total_effect": joint_classification(
            parent_models,
            replication_models,
            field="b2_effects_vs_topo_A",
        ),
        "semantic_increment": joint_classification(
            parent_models,
            replication_models,
            field="semantic_increments_vs_topo_A",
        ),
    }
    schedule_classification = base_analysis.classify(
        schedule_models, field="schedule_difference_effects"
    )
    report = {
        "experiment_id": EXPERIMENT_ID,
        "parent_experiment_id": PARENT_EXPERIMENT_ID,
        "evidence_status": (
            "complete_schedule_replication_all_model_gates_passed"
            if validation["passed"]
            else "complete_schedule_replication_with_invalid_model_blocks"
        ),
        "human_review_required": False,
        "human_review_used_as_evidence": False,
        "integrity": {
            "formal_episodes": validation["episodes_observed"],
            "assigned_model_calls": validation[
                "assigned_model_calls_expected"
            ],
            "provider_api_attempts": sum(
                model["provider_api_attempts"]
                for model in replication_models.values()
            ),
            "validation_sha256": sha256_file(validation_path),
            "parent_validation_sha256": sha256_file(
                PARENT / "models/validation_report.json"
            ),
            "parent_results_sha256": sha256_file(parent_results_path),
        },
        "models": replication_models,
        "classification": {
            "parent": parent_results["classification"],
            "replication": replication_classification,
            "cross_schedule": cross_schedule,
            "schedule_difference": schedule_classification,
        },
        "claim_boundary": {
            "all_model_validity_gates_passed": validation["passed"],
            "provider_seed_supported": False,
            "changed_factor": "schedule_seed_and_resulting_execution_order",
            "synthetic_task_scope": True,
        },
    }
    analysis_dir = PACKAGE / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    (analysis_dir / "results.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (analysis_dir / "results.md").write_text(
        render_markdown(report), encoding="utf-8"
    )
    print(
        canonical_json(
            {
                "status": report["evidence_status"],
                "formal_episodes": report["integrity"]["formal_episodes"],
                "assigned_model_calls": report["integrity"][
                    "assigned_model_calls"
                ],
                "replication_large_total_effects": len(
                    replication_classification["b2_total_effect"][
                        "replicated_large_effects"
                    ]
                ),
                "replicated_large_schedule_shifts": len(
                    schedule_classification["replicated_large_effects"]
                ),
            }
        )
    )


if __name__ == "__main__":
    main()
