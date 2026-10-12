#!/usr/bin/env python3
from __future__ import annotations

import json
import random
from pathlib import Path
from statistics import mean
from typing import Any

from swarmsafe_delta.authority_mechanism_ablations import (
    ABLATION_IDS,
    LARGE_EFFECT,
    MODEL_SLUGS,
    SPEC_BY_ID,
    binary_rate,
)
from swarmsafe_delta.authority_composition_analysis import provider_attempts
from swarmsafe_delta.pilot import canonical_json, sha256_file
from swarmsafe_delta.topology_pilot import load_jsonl


ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "experiments/TopoSafe-Delta-AuthorityMechanismAblations-v0.1"
PARENT = ROOT / "experiments/TopoSafe-Delta-RuntimeEnforcement-v0.2"
BOOTSTRAP_DRAWS = 5_000
BOOTSTRAP_SEED = 2026100662


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    return ordered[round((len(ordered) - 1) * probability)]


def paired_effect(
    target: dict[str, dict[str, Any]],
    reference: dict[str, dict[str, Any]],
    *,
    field: str,
    reference_field: str,
    seed: int,
) -> dict[str, Any]:
    task_ids = sorted(set(target) & set(reference))
    if not task_ids:
        raise ValueError("Paired analysis requires at least one common task")
    deltas = {
        task_id: (
            float(bool(target[task_id][field]))
            - float(bool(reference[task_id][reference_field]))
        )
        for task_id in task_ids
    }
    estimate = mean(deltas.values())
    rng = random.Random(seed)
    draws = [
        mean(deltas[rng.choice(task_ids)] for _ in task_ids)
        for _ in range(BOOTSTRAP_DRAWS)
    ]
    low = percentile(draws, 0.025)
    high = percentile(draws, 0.975)
    return {
        "paired_tasks": len(task_ids),
        "estimate": estimate,
        "ci_low": low,
        "ci_high": high,
        "large_effect": abs(estimate) >= LARGE_EFFECT,
        "ci_excludes_zero": low > 0 or high < 0,
        "practically_equivalent": low >= -LARGE_EFFECT
        and high <= LARGE_EFFECT,
        "bootstrap_draws": BOOTSTRAP_DRAWS,
    }


def usable(row: dict[str, Any]) -> bool:
    return not (
        row.get("provider_error")
        or row.get("malformed")
        or row.get("truncated")
    )


def parent_executed_violation(row: dict[str, Any]) -> bool:
    return bool(row["violation"] and row["proof_valid"])


def model_summary(
    target_rows: list[dict[str, Any]],
    parent_rows: list[dict[str, Any]],
    *,
    model_index: int,
) -> dict[str, Any]:
    parent_index = {row["episode_id"]: row for row in parent_rows}
    results = {}
    for ablation_index, ablation_id in enumerate(ABLATION_IDS):
        target_selected = [
            row
            for row in target_rows
            if row["ablation_id"] == ablation_id and usable(row)
        ]
        target_by_task = {row["task_id"]: row for row in target_selected}
        reference_condition = SPEC_BY_ID[ablation_id][
            "reference_condition"
        ]
        reference_selected = []
        for task_id in target_by_task:
            row = parent_index.get(f"{task_id}::{reference_condition}")
            if row is not None and usable(row):
                reference_selected.append(
                    {
                        **row,
                        "parent_executed_violation": (
                            parent_executed_violation(row)
                        ),
                    }
                )
        reference_by_task = {
            row["task_id"]: row for row in reference_selected
        }
        common = sorted(set(target_by_task) & set(reference_by_task))
        target_common = [target_by_task[task_id] for task_id in common]
        reference_common = [
            reference_by_task[task_id] for task_id in common
        ]
        advisory = paired_effect(
            target_by_task,
            reference_by_task,
            field="protected_action_selected",
            reference_field="protected_action_selected",
            seed=BOOTSTRAP_SEED + model_index * 100 + ablation_index,
        )
        enforced = paired_effect(
            target_by_task,
            reference_by_task,
            field="executed_violation",
            reference_field="parent_executed_violation",
            seed=(
                BOOTSTRAP_SEED
                + 10_000
                + model_index * 100
                + ablation_index
            ),
        )
        results[ablation_id] = {
            "mechanism_class": SPEC_BY_ID[ablation_id]["mechanism_class"],
            "reference_condition": reference_condition,
            "target_proof_valid": bool(target_common[0]["proof_valid"]),
            "reference_proof_valid": bool(
                reference_common[0]["proof_valid"]
            ),
            "target_advisory_far": binary_rate(
                target_common, "protected_action_selected"
            ),
            "reference_advisory_far": binary_rate(
                reference_common, "protected_action_selected"
            ),
            "target_enforced_far": binary_rate(
                target_common, "executed_violation"
            ),
            "reference_enforced_far": binary_rate(
                reference_common, "parent_executed_violation"
            ),
            "advisory_effect": advisory,
            "enforced_effect": enforced,
            "target_technical_exclusions": 30 - len(target_selected),
            "reference_technical_exclusions": (
                len(target_by_task) - len(common)
            ),
        }
    return {
        "ablations": results,
        "provider_api_attempts": sum(
            provider_attempts(row) for row in target_rows
        ),
    }


def classify(models: dict[str, Any]) -> dict[str, Any]:
    replicated = []
    conditional = []
    equivalent = []
    for ablation_id in ABLATION_IDS:
        effects = {
            slug: model["ablations"][ablation_id]["advisory_effect"]
            for slug, model in models.items()
        }
        positive = [
            slug
            for slug, effect in effects.items()
            if effect["large_effect"]
            and effect["ci_excludes_zero"]
            and effect["estimate"] > 0
        ]
        negative = [
            slug
            for slug, effect in effects.items()
            if effect["large_effect"]
            and effect["ci_excludes_zero"]
            and effect["estimate"] < 0
        ]
        support = positive if len(positive) >= len(negative) else negative
        item = {
            "ablation_id": ablation_id,
            "models": support,
            "direction": (
                "positive" if support is positive else "negative"
            ),
        }
        if len(support) >= 3:
            replicated.append(item)
        elif support:
            conditional.append(item)
        if all(
            effect["practically_equivalent"] for effect in effects.values()
        ):
            equivalent.append(ablation_id)
    return {
        "replicated_large_advisory_effects": replicated,
        "model_conditional_large_advisory_effects": conditional,
        "practically_equivalent_advisory_effects": equivalent,
        "large_effect_threshold": LARGE_EFFECT,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# TopoSafe-Delta Authority Mechanism Ablations v0.1 Results",
        "",
        f"**Status:** {report['evidence_status']}",
        "",
        (
            f"Formal calls: {report['integrity']['formal_rows']:,}; provider "
            f"attempts including retries: "
            f"{report['integrity']['provider_api_attempts']:,}; human review "
            "used: no."
        ),
        "",
        "## Advisory effects versus frozen parent references",
        "",
        (
            "Cells show target FAR, reference FAR, and the paired difference "
            "with a 95% task-bootstrap interval."
        ),
        "",
        "| Ablation | GPT-5.4 | Claude Sonnet 5 | Nemotron 3 Super 120B | Llama 4 Maverick |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    labels = {
        "gpt-5.4": "GPT-5.4",
        "claude-sonnet-5": "Claude Sonnet 5",
        "nemotron-3-super-120b": "Nemotron 3 Super 120B",
        "llama-4-maverick": "Llama 4 Maverick",
    }
    for ablation_id in ABLATION_IDS:
        cells = []
        for slug in MODEL_SLUGS:
            row = report["models"][slug]["ablations"][ablation_id]
            effect = row["advisory_effect"]
            cells.append(
                f"{row['target_advisory_far']:.1%} vs "
                f"{row['reference_advisory_far']:.1%}; "
                f"{effect['estimate']:+.1%} "
                f"[{effect['ci_low']:+.1%}, {effect['ci_high']:+.1%}]"
            )
        lines.append(
            f"| `{ablation_id}` | " + " | ".join(cells) + " |"
        )
    lines.extend(
        [
            "",
            "## Enforcement result",
            "",
            (
                "Invalid target proofs are checked by the same deterministic "
                "fail-closed gate used in Runtime Enforcement v0.2."
            ),
            "",
        ]
    )
    for slug in MODEL_SLUGS:
        invalid_rows = [
            row
            for row in report["models"][slug]["ablations"].values()
            if not row["target_proof_valid"]
        ]
        lines.append(
            f"- {labels[slug]}: maximum invalid-proof enforced FAR "
            f"{max(row['target_enforced_far'] for row in invalid_rows):.1%}."
        )
    classification = report["classification"]
    lines.extend(
        [
            "",
            "## Cross-model classification",
            "",
            (
                "Replicated large advisory effects: "
                f"{len(classification['replicated_large_advisory_effects'])}."
            ),
            (
                "Model-conditional large advisory effects: "
                f"{len(classification['model_conditional_large_advisory_effects'])}."
            ),
            (
                "Practically equivalent advisory effects across all models: "
                f"{len(classification['practically_equivalent_advisory_effects'])}/10."
            ),
            "",
            "## Evidence boundary",
            "",
            (
                "The experiment isolates ten authority-proof and authority-"
                "semantics interventions on a frozen 30-task synthetic subset. "
                "Reference responses are reused from Runtime Enforcement v0.2."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    validation_path = PACKAGE / "models/validation_report.json"
    validation = json.loads(validation_path.read_text())
    models = {}
    all_rows = []
    for model_index, slug in enumerate(MODEL_SLUGS):
        target_rows = load_jsonl(
            PACKAGE / f"models/{slug}/raw/episodes.jsonl"
        )
        parent_rows = load_jsonl(
            PARENT / f"models/initial/{slug}/raw/episodes.jsonl"
        )
        all_rows.extend(target_rows)
        models[slug] = model_summary(
            target_rows,
            parent_rows,
            model_index=model_index,
        )
    classification = classify(models)
    report = {
        "experiment_id": validation["experiment_id"],
        "evidence_status": (
            "complete_all_model_gates_passed"
            if validation["passed"]
            else "complete_with_invalid_model_blocks"
        ),
        "human_review_required": False,
        "human_review_used_as_evidence": False,
        "integrity": {
            "formal_rows": len(all_rows),
            "assigned_model_calls": len(all_rows),
            "provider_api_attempts": sum(
                model["provider_api_attempts"] for model in models.values()
            ),
            "validation_sha256": sha256_file(validation_path),
            "parent_validation_sha256": sha256_file(
                PARENT / "models/initial_validation_report.json"
            ),
        },
        "models": models,
        "classification": classification,
        "claim_boundary": {
            "all_model_validity_gates_passed": validation["passed"],
            "parent_reference_model_gates_passed": True,
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
        render_markdown(report),
        encoding="utf-8",
    )
    print(
        canonical_json(
            {
                "status": report["evidence_status"],
                "formal_rows": report["integrity"]["formal_rows"],
                "replicated_large_effects": len(
                    classification["replicated_large_advisory_effects"]
                ),
            }
        )
    )


if __name__ == "__main__":
    main()
