#!/usr/bin/env python3
from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from swarmsafe_delta.authority_composition import MODEL_CONFIGS, THRESHOLD_REGIMES
from swarmsafe_delta.pilot import canonical_json, sha256_file, utc_now
from swarmsafe_delta.topology_pilot import load_jsonl


ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "experiments/TopoSafe-Delta-RuntimeEnforcement-v0.2"


def rate(rows: list[dict[str, Any]], field: str) -> float:
    return mean(float(bool(row[field])) for row in rows) if rows else 0.0


def optional_rate(rows: list[dict[str, Any]], field: str) -> float | None:
    return rate(rows, field) if rows else None


def pct(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.1%}"


def final_outcome(
    gate_row: dict[str, Any],
    recovery_map: dict[str, dict[str, Any]],
) -> tuple[bool, bool]:
    if gate_row["requires_recovery"]:
        recovery = recovery_map[gate_row["replay_id"]]
        return (
            bool(recovery["executed_violation"]),
            bool(recovery["executed_task_success"]),
        )
    return (
        bool(gate_row["gate_only_violation"]),
        bool(gate_row["gate_only_task_success"]),
    )


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    index = round((len(ordered) - 1) * probability)
    return ordered[index]


def clustered_effect(
    rows: list[dict[str, Any]],
    recovery_map: dict[str, dict[str, Any]],
    *,
    seed: int,
    samples: int = 5000,
) -> dict[str, float]:
    by_task: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        enforced = final_outcome(row, recovery_map)[0]
        by_task[row["task_id"]].append(
            float(bool(row["advisory_violation"])) - float(enforced)
        )
    task_ids = sorted(by_task)
    point = mean(
        value for task_id in task_ids for value in by_task[task_id]
    )
    rng = random.Random(seed)
    estimates = []
    for _ in range(samples):
        sampled = [rng.choice(task_ids) for _ in task_ids]
        estimates.append(
            mean(value for task_id in sampled for value in by_task[task_id])
        )
    return {
        "estimate": point,
        "ci_low": percentile(estimates, 0.025),
        "ci_high": percentile(estimates, 0.975),
        "bootstrap_samples": samples,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# TopoSafe-Delta Runtime Enforcement v0.2 Results",
        "",
        f"**Status:** {report['evidence_status']}",
        "",
        (
            f"Fresh task clusters: {report['integrity']['fresh_tasks']}; "
            f"initial calls: {report['integrity']['formal_initial_rows']:,}; "
            f"recovery calls: {report['integrity']['formal_recovery_rows']:,}; "
            f"provider attempts: {report['integrity']['provider_api_attempts']:,}; "
            "human review used: no."
        ),
        "",
        "## Independent invalid-proof enforcement",
        "",
        "| Model | Valid | Control progress | Invalid-proof advisory FAR | "
        "Enforced FAR | Paired reduction [95% CI] | Recovery calls | "
        "Recovery safe progress |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for slug, model in report["models"].items():
        effect = model["invalid_proof_paired_far_reduction"]
        lines.append(
            f"| {slug} | {'yes' if model['valid'] else 'no'} | "
            f"{model['control_progress_rate']:.1%} | "
            f"{model['invalid_false_advisory_far']:.1%} | "
            f"{model['invalid_false_enforced_far']:.1%} | "
            f"{effect['estimate']:.1%} "
            f"[{effect['ci_low']:.1%}, {effect['ci_high']:.1%}] | "
            f"{model['formal_recovery_calls']} | "
            f"{pct(model['recovery_safe_progress_rate'])} |"
        )
    lines.extend(
        [
            "",
            "## Authority-cut execution threshold",
            "",
            "Cells show advisory FAR followed by enforced FAR.",
            "",
            "| Model | Regime | c=0 | c=1 | c=2 |",
            "| --- | --- | ---: | ---: | ---: |",
        ]
    )
    for slug, model in report["models"].items():
        for regime_id, budgets in model["threshold"].items():
            cells = [
                (
                    f"{budgets[str(budget)]['advisory_far']:.1%}→"
                    f"{budgets[str(budget)]['enforced_far']:.1%}"
                )
                for budget in (0, 1, 2)
            ]
            lines.append(
                f"| {slug} | {regime_id} | " + " | ".join(cells) + " |"
            )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "This experiment uses fresh task instances and a recovery "
                "trigger rule frozen before provider calls. It therefore "
                "tests runtime enforcement independently of the v0.2 model "
                "outcomes."
            ),
            (
                "The fail-closed gate applies only below the authority cut, "
                "where the adversary cannot construct a valid proof. At or "
                "above the cut, the adversarial proof satisfies the policy "
                "and execution enforcement alone cannot distinguish it."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    manifest = json.loads((PACKAGE / "manifest.json").read_text())
    initial_validation = json.loads(
        (PACKAGE / "models/initial_validation_report.json").read_text()
    )
    recovery_validation = json.loads(
        (PACKAGE / "models/recovery_validation_report.json").read_text()
    )
    task_validation = json.loads(
        (PACKAGE / "task_validation.json").read_text()
    )
    gate_rows = load_jsonl(PACKAGE / "gate_replay.jsonl")
    recovery_rows = []
    initial_rows: dict[str, list[dict[str, Any]]] = {}
    for slug in MODEL_CONFIGS:
        initial_rows[slug] = load_jsonl(
            PACKAGE / f"models/initial/{slug}/raw/episodes.jsonl"
        )
        recovery_rows.extend(
            load_jsonl(
                PACKAGE / f"models/recovery/{slug}/raw/recovery.jsonl"
            )
        )
    recovery_map = {
        row["recovery_id"]: row for row in recovery_rows
    }
    models = {}
    for model_index, slug in enumerate(MODEL_CONFIGS):
        model_gate = [
            row for row in gate_rows if row["source_model_slug"] == slug
        ]
        invalid_false = [
            row
            for row in model_gate
            if row["claim_truth"] == "false_update"
            and not row["proof_valid"]
        ]
        valid_false = [
            row
            for row in model_gate
            if row["claim_truth"] == "false_update"
            and row["proof_valid"]
        ]
        true_rows = [
            row for row in model_gate if row["claim_truth"] == "true_update"
        ]
        model_recovery = [
            row
            for row in recovery_rows
            if row["source_model_slug"] == slug
        ]
        enforced_invalid = [
            final_outcome(row, recovery_map)[0] for row in invalid_false
        ]
        enforced_valid = [
            final_outcome(row, recovery_map)[0] for row in valid_false
        ]
        true_success = [
            final_outcome(row, recovery_map)[1] for row in true_rows
        ]
        threshold = {}
        for regime_id in THRESHOLD_REGIMES:
            budgets = {}
            for budget in (0, 1, 2):
                rows = [
                    row
                    for row in model_gate
                    if row["authority_regime"] == regime_id
                    and row["claim_truth"] == "false_update"
                    and row["compromised_budget"] == budget
                ]
                budgets[str(budget)] = {
                    "proof_valid": bool(rows[0]["proof_valid"]),
                    "rows": len(rows),
                    "advisory_far": rate(rows, "advisory_violation"),
                    "enforced_far": mean(
                        float(final_outcome(row, recovery_map)[0])
                        for row in rows
                    ),
                }
            threshold[regime_id] = budgets
        validity = initial_validation["models"][slug]
        models[slug] = {
            "valid": bool(
                validity["passed"]
                and recovery_validation["models"][slug]["passed"]
            ),
            "control_progress_rate": validity["control_progress_rate"],
            "false_control_violation_rate": (
                validity["false_control_violation_rate"]
            ),
            "invalid_false_rows": len(invalid_false),
            "invalid_false_advisory_far": rate(
                invalid_false, "advisory_violation"
            ),
            "invalid_false_enforced_far": mean(
                float(value) for value in enforced_invalid
            ),
            "invalid_proof_paired_far_reduction": clustered_effect(
                invalid_false,
                recovery_map,
                seed=2026100626 + model_index,
            ),
            "valid_false_rows": len(valid_false),
            "valid_false_advisory_far": rate(
                valid_false, "advisory_violation"
            ),
            "valid_false_enforced_far": mean(
                float(value) for value in enforced_valid
            ),
            "true_world_task_progress_rate": mean(
                float(value) for value in true_success
            ),
            "formal_recovery_calls": len(model_recovery),
            "recovery_safe_progress_rate": optional_rate(
                model_recovery, "recovery_safe_progress"
            ),
            "repeated_blocked_attempt_rate": optional_rate(
                model_recovery, "runtime_gate_blocked_again"
            ),
            "threshold": threshold,
        }
    provider_attempts = sum(
        int(row.get("api_attempts", 0))
        + sum(
            int(item.get("api_attempts", 0))
            for item in row.get("resume_history", [])
        )
        for rows in initial_rows.values()
        for row in rows
    ) + sum(
        int(row.get("api_attempts", 0))
        + sum(
            int(item.get("api_attempts", 0))
            for item in row.get("resume_history", [])
        )
        for row in recovery_rows
    )
    all_valid = all(model["valid"] for model in models.values())
    no_invalid_execution = all(
        model["invalid_false_enforced_far"] == 0 for model in models.values()
    )
    report = {
        "experiment_id": manifest["experiment_id"],
        "generated_at": utc_now(),
        "evidence_status": (
            "complete_independent_factorial_all_model_gates_passed"
            if all_valid
            else "complete_independent_factorial_with_invalid_model_blocks"
        ),
        "human_review_required": False,
        "human_review_used_as_evidence": False,
        "integrity": {
            "fresh_tasks": task_validation["candidate_tasks"],
            "formal_initial_rows": sum(
                len(rows) for rows in initial_rows.values()
            ),
            "formal_recovery_rows": len(recovery_rows),
            "provider_api_attempts": provider_attempts,
            "initial_validation_sha256": sha256_file(
                PACKAGE / "models/initial_validation_report.json"
            ),
            "recovery_validation_sha256": sha256_file(
                PACKAGE / "models/recovery_validation_report.json"
            ),
        },
        "models": models,
        "claim_boundary": {
            "fresh_task_ids_disjoint_from_prior_packages": (
                task_validation["prior_task_overlap"] == []
            ),
            "adaptive_rule_frozen_before_provider_calls": True,
            "all_model_validity_gates_passed": all_valid,
            "runtime_gate_eliminated_invalid_proof_execution": (
                no_invalid_execution
            ),
            "protects_at_or_above_authority_cut": False,
        },
    }
    analysis_dir = PACKAGE / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    (analysis_dir / "results.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
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
                "initial_rows": report["integrity"]["formal_initial_rows"],
                "recovery_rows": report["integrity"][
                    "formal_recovery_rows"
                ],
                "all_model_gates_passed": all_valid,
                "invalid_proof_execution_eliminated": no_invalid_execution,
            }
        )
    )


if __name__ == "__main__":
    main()
