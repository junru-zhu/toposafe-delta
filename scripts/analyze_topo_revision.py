#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from swarmsafe_delta.topo_revision_authority_cut import POLICIES
from swarmsafe_delta.topo_revision_common import (
    DEFAULT_SEED,
    MODEL_SLUGS,
    REVISION_ROOT,
    bootstrap_mean_interval,
    effect_summary,
    grouped_rate,
    holm_adjust,
    load_jsonl,
    mean,
    paired_task_values,
    write_json,
)
from swarmsafe_delta.topo_revision_provenance import PRIMARY_CONTRASTS


ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / REVISION_ROOT


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", choices=("E1", "E2", "E3"), required=True)
    parser.add_argument("--stage", choices=("pilot", "formal"), required=True)
    return parser.parse_args()


def load_rows(experiment: str, stage: str) -> list[dict[str, Any]]:
    return [
        row
        for model_slug in MODEL_SLUGS
        for row in load_jsonl(
            PACKAGE
            / f"runs/{experiment}/{stage}/{model_slug}/raw/episodes.jsonl"
        )
    ]


def validity(experiment: str, stage: str) -> dict[str, Any]:
    result = {}
    for model_slug in MODEL_SLUGS:
        path = (
            PACKAGE
            / f"runs/{experiment}/{stage}/{model_slug}/validation.json"
        )
        result[model_slug] = (
            json.loads(path.read_text(encoding="utf-8"))
            if path.exists()
            else {"passed": False, "errors": ["validation missing"]}
        )
    return result


def rate_with_ci(
    rows: list[dict[str, Any]],
    outcome: str,
    *,
    seed: int,
) -> dict[str, Any]:
    values = [float(bool(row.get(outcome))) for row in rows]
    lower, upper = bootstrap_mean_interval(values, seed=seed)
    return {
        "n": len(values),
        "rate": mean(values),
        "ci95": [lower, upper],
    }


def e1_analysis(
    rows: list[dict[str, Any]],
    model_validity: dict[str, Any],
) -> dict[str, Any]:
    completed = [row for row in rows if not row.get("provider_error")]
    outcomes = []
    for model_index, model_slug in enumerate(MODEL_SLUGS):
        model_rows = [
            row for row in completed if row["model_slug"] == model_slug
        ]
        for treatment in ("P0", "P1", "P2", "P3", "P4"):
            false_rows = [
                row
                for row in model_rows
                if row["treatment"] == treatment
                and row["world_state"] == "FALSE"
            ]
            true_rows = [
                row
                for row in model_rows
                if row["treatment"] == treatment
                and row["world_state"] == "TRUE"
            ]
            far = rate_with_ci(
                false_rows,
                "protected_action_selected",
                seed=DEFAULT_SEED + model_index,
            )
            tur = rate_with_ci(
                true_rows,
                "protected_action_selected",
                seed=DEFAULT_SEED + 100 + model_index,
            )
            paired = {}
            by_task = defaultdict(dict)
            for row in [*false_rows, *true_rows]:
                by_task[row["task_id"]][row["world_state"]] = float(
                    bool(row["protected_action_selected"])
                )
            tcg_values = [
                values["TRUE"] - values["FALSE"]
                for values in by_task.values()
                if {"TRUE", "FALSE"} <= set(values)
            ]
            tcg_ci = bootstrap_mean_interval(
                tcg_values,
                seed=DEFAULT_SEED + 200 + model_index,
            )
            paired["task_clusters"] = len(tcg_values)
            paired["estimate"] = mean(tcg_values)
            paired["ci95"] = list(tcg_ci)
            outcomes.append(
                {
                    "model_slug": model_slug,
                    "model_valid": model_validity[model_slug]["passed"],
                    "treatment": treatment,
                    "far": far,
                    "tur": tur,
                    "tcg": paired,
                    "safe_progress_rate": mean(
                        float(bool(row["safe_progress"]))
                        for row in model_rows
                        if row["treatment"] == treatment
                    ),
                    "abstention_rate": mean(
                        float(bool(row["abstention"]))
                        for row in model_rows
                        if row["treatment"] == treatment
                    ),
                    "malformed_rate": mean(
                        float(bool(row["malformed"]))
                        for row in model_rows
                        if row["treatment"] == treatment
                    ),
                }
            )
    effects = []
    for model_index, model_slug in enumerate(MODEL_SLUGS):
        model_rows = [
            row
            for row in completed
            if row["model_slug"] == model_slug
        ]
        for contrast_index, (
            contrast_id,
            reference,
            treated,
        ) in enumerate(PRIMARY_CONTRASTS):
            for outcome_index, (state, outcome_name) in enumerate(
                (("FALSE", "FAR"), ("TRUE", "TUR"))
            ):
                state_rows = [
                    row
                    for row in model_rows
                    if row["world_state"] == state
                ]
                paired = paired_task_values(
                    state_rows,
                    reference=reference,
                    treated=treated,
                    condition_field="treatment",
                    outcome_field="protected_action_selected",
                )
                summary = effect_summary(
                    paired,
                    seed=(
                        DEFAULT_SEED
                        + model_index * 100
                        + contrast_index * 10
                        + outcome_index
                    ),
                )
                effects.append(
                    {
                        "experiment": "E1",
                        "model_slug": model_slug,
                        "model_valid": model_validity[model_slug]["passed"],
                        "contrast": contrast_id,
                        "reference": reference,
                        "treated": treated,
                        "outcome": outcome_name,
                        **summary,
                    }
                )
    holm_adjust(effects)
    return {
        "outcomes": outcomes,
        "primary_effects": effects,
    }


def _e2_threshold_effects(
    completed: list[dict[str, Any]],
    model_validity: dict[str, Any],
) -> list[dict[str, Any]]:
    effects = []
    for model_index, model_slug in enumerate(MODEL_SLUGS):
        model_rows = [
            {
                **row,
                "policy_budget": (
                    f"{row['policy_id']}::c{row['compromised_budget']}"
                ),
            }
            for row in completed
            if row["model_slug"] == model_slug
            and row["case_type"] == "treatment"
        ]
        for policy_index, policy_id in enumerate(("A1", "A2", "A3")):
            cut = POLICIES[policy_id].authority_cut
            reference = f"{policy_id}::c{cut - 1}"
            treated = f"{policy_id}::c{cut}"
            false_rows = [
                row for row in model_rows if row["world_state"] == "FALSE"
            ]
            for outcome_index, outcome in enumerate(
                (
                    "protected_action_selected",
                    "false_state_committed_action",
                )
            ):
                paired = paired_task_values(
                    false_rows,
                    reference=reference,
                    treated=treated,
                    condition_field="policy_budget",
                    outcome_field=outcome,
                )
                effects.append(
                    {
                        "experiment": "E2",
                        "model_slug": model_slug,
                        "model_valid": model_validity[model_slug]["passed"],
                        "contrast": f"{policy_id}_at_cut_minus_below",
                        "reference": reference,
                        "treated": treated,
                        "outcome": outcome,
                        **effect_summary(
                            paired,
                            seed=(
                                DEFAULT_SEED
                                + model_index * 100
                                + policy_index * 10
                                + outcome_index
                            ),
                        ),
                    }
                )
        utility_rows = [
            row
            for row in model_rows
            if row["world_state"] == "TRUE"
            and (
                (row["policy_id"] == "A1" and row["compromised_budget"] == 0)
                or (
                    row["policy_id"] in {"A2", "A3"}
                    and row["compromised_budget"] == 1
                )
            )
        ]
        for contrast_index, treated in enumerate(("A2", "A3")):
            paired = paired_task_values(
                utility_rows,
                reference="A1",
                treated=treated,
                condition_field="policy_id",
                outcome_field="true_state_task_completion",
            )
            effects.append(
                {
                    "experiment": "E2",
                    "model_slug": model_slug,
                    "model_valid": model_validity[model_slug]["passed"],
                    "contrast": f"{treated}_minus_A1_true_utility",
                    "reference": "A1",
                    "treated": treated,
                    "outcome": "true_state_task_completion",
                    **effect_summary(
                        paired,
                        seed=(
                            DEFAULT_SEED
                            + 500
                            + model_index * 10
                            + contrast_index
                        ),
                    ),
                }
            )
    holm_adjust(effects)
    return effects


def e2_analysis(
    rows: list[dict[str, Any]],
    model_validity: dict[str, Any],
) -> dict[str, Any]:
    completed = [row for row in rows if not row.get("provider_error")]
    treatment = [
        row for row in completed if row["case_type"] == "treatment"
    ]
    rates = []
    for model_index, model_slug in enumerate(MODEL_SLUGS):
        for policy_id in ("A1", "A2", "A3"):
            for budget in sorted(
                {
                    row["compromised_budget"]
                    for row in treatment
                    if row["policy_id"] == policy_id
                }
            ):
                for state in ("FALSE", "TRUE"):
                    cell = [
                        row
                        for row in treatment
                        if row["model_slug"] == model_slug
                        and row["policy_id"] == policy_id
                        and row["compromised_budget"] == budget
                        and row["world_state"] == state
                    ]
                    rates.append(
                        {
                            "model_slug": model_slug,
                            "model_valid": model_validity[model_slug][
                                "passed"
                            ],
                            "policy_id": policy_id,
                            "authority_cut": POLICIES[
                                policy_id
                            ].authority_cut,
                            "compromised_budget": budget,
                            "world_state": state,
                            "proof_valid_rate": mean(
                                float(bool(row["proof_valid"]))
                                for row in cell
                            ),
                            "advisory_protected": rate_with_ci(
                                cell,
                                "protected_action_selected",
                                seed=(
                                    DEFAULT_SEED
                                    + model_index
                                    + budget * 10
                                ),
                            ),
                            "committed_protected": rate_with_ci(
                                cell,
                                "protected_action_committed",
                                seed=(
                                    DEFAULT_SEED
                                    + 100
                                    + model_index
                                    + budget * 10
                                ),
                            ),
                            "safe_progress_rate": mean(
                                float(bool(row["safe_progress"]))
                                for row in cell
                            ),
                            "abstention_rate": mean(
                                float(bool(row["abstention"]))
                                for row in cell
                            ),
                        }
                    )
    return {
        "structural": {
            policy_id: {
                "eligible_principals": list(policy.eligible_principals),
                "threshold": policy.threshold,
                "authority_cut": policy.authority_cut,
            }
            for policy_id, policy in POLICIES.items()
        },
        "outcomes": rates,
        "primary_effects": _e2_threshold_effects(
            completed,
            model_validity,
        ),
        "technical_controls": {
            model_slug: model_validity[model_slug].get(
                "control_rates", {}
            )
            for model_slug in MODEL_SLUGS
        },
    }


def e3_analysis(
    rows: list[dict[str, Any]],
    model_validity: dict[str, Any],
) -> dict[str, Any]:
    completed = [row for row in rows if not row.get("provider_error")]
    rates = []
    for model_slug in MODEL_SLUGS:
        for topology in ("C1", "C2", "C3"):
            for auth in ("A1", "A2"):
                for execution in ("E0", "E1"):
                    for state in ("FALSE", "TRUE"):
                        cell = [
                            row
                            for row in completed
                            if row["model_slug"] == model_slug
                            and row["topology"] == topology
                            and row["authorization_policy"] == auth
                            and row["execution_policy"] == execution
                            and row["world_state"] == state
                        ]
                        rates.append(
                            {
                                "model_slug": model_slug,
                                "model_valid": model_validity[model_slug][
                                    "passed"
                                ],
                                "topology": topology,
                                "authorization_policy": auth,
                                "execution_policy": execution,
                                "world_state": state,
                                "n": len(cell),
                                "message_delivery_rate": mean(
                                    float(bool(row["message_delivered"]))
                                    for row in cell
                                ),
                                "mean_message_similarity": mean(
                                    float(row["message_similarity"])
                                    for row in cell
                                ),
                                "unsupported_authority_introduction_rate": mean(
                                    float(
                                        bool(
                                            row[
                                                "unsupported_authority_claim_introduced"
                                            ]
                                        )
                                    )
                                    for row in cell
                                ),
                                "proof_valid_rate": mean(
                                    float(bool(row["final_proof_valid"]))
                                    for row in cell
                                ),
                                "advisory_protected_rate": mean(
                                    float(
                                        bool(
                                            row[
                                                "protected_action_selected"
                                            ]
                                        )
                                    )
                                    for row in cell
                                ),
                                "false_commit_rate": mean(
                                    float(
                                        bool(
                                            row[
                                                "false_state_committed_action"
                                            ]
                                        )
                                    )
                                    for row in cell
                                ),
                                "true_completion_rate": mean(
                                    float(
                                        bool(
                                            row[
                                                "true_state_task_completion"
                                            ]
                                        )
                                    )
                                    for row in cell
                                ),
                                "safe_progress_rate": mean(
                                    float(bool(row["safe_progress"]))
                                    for row in cell
                                ),
                            }
                        )
    traces = []
    for outcome_name, predicate in (
        (
            "false_state_committed",
            lambda row: row.get("false_state_committed_action"),
        ),
        (
            "gate_blocked_invalid_proof",
            lambda row: row.get("runtime_gate_blocked"),
        ),
        (
            "true_state_completed",
            lambda row: row.get("true_state_task_completion"),
        ),
    ):
        candidates = sorted(
            (row for row in completed if predicate(row)),
            key=lambda row: row["episode_id"],
        )
        if candidates:
            row = candidates[0]
            traces.append(
                {
                    "trace_type": outcome_name,
                    "episode_id": row["episode_id"],
                    "model_slug": row["model_slug"],
                    "task_id": row["task_id"],
                    "topology": row["topology"],
                    "authorization_policy": row[
                        "authorization_policy"
                    ],
                    "execution_policy": row["execution_policy"],
                    "world_state": row["world_state"],
                    "source_message": row["source_message"],
                    "intermediate_messages": [
                        trace["downstream_envelope"]["message"]
                        for trace in row["intermediate_traces"]
                    ],
                    "delivered_message": row["delivered_message"],
                    "final_proof_valid": row["final_proof_valid"],
                    "selected_action": row["selected_action"],
                    "runtime_gate_blocked": row["runtime_gate_blocked"],
                    "false_state_committed_action": row[
                        "false_state_committed_action"
                    ],
                    "true_state_task_completion": row[
                        "true_state_task_completion"
                    ],
                }
            )
    return {"outcomes": rates, "selected_actual_traces": traces}


def flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    if not isinstance(value, dict):
        return {prefix: value}
    result = {}
    for key, item in value.items():
        name = f"{prefix}.{key}" if prefix else key
        if isinstance(item, dict):
            result.update(flatten(item, name))
        elif isinstance(item, list):
            result[name] = json.dumps(item, ensure_ascii=False)
        else:
            result[name] = item
    return result


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flattened = [flatten(row) for row in rows]
    fields = sorted({key for row in flattened for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(flattened)


def tex_escape(value: Any) -> str:
    return (
        str(value)
        .replace("\\", r"\textbackslash{}")
        .replace("_", r"\_")
        .replace("%", r"\%")
        .replace("&", r"\&")
    )


def write_effect_tex(path: Path, effects: list[dict[str, Any]]) -> None:
    lines = [
        r"\begin{tabular}{llllrr}",
        r"\toprule",
        r"Model & Contrast & Outcome & $n$ & Effect & 95\% CI \\",
        r"\midrule",
    ]
    for row in effects:
        lower, upper = row["ci95"]
        lines.append(
            f"{tex_escape(row['model_slug'])} & "
            f"{tex_escape(row['contrast'])} & "
            f"{tex_escape(row['outcome'])} & "
            f"{row['task_clusters']} & "
            f"{row['estimate']:.3f} & "
            f"[{lower:.3f}, {upper:.3f}] \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    rows = load_rows(args.experiment, args.stage)
    model_validity = validity(args.experiment, args.stage)
    if args.experiment == "E1":
        analysis = e1_analysis(rows, model_validity)
    elif args.experiment == "E2":
        analysis = e2_analysis(rows, model_validity)
    else:
        analysis = e3_analysis(rows, model_validity)
    result = {
        "experiment": args.experiment,
        "stage": args.stage,
        "evidence_status": (
            "confirmatory"
            if args.stage == "formal"
            and all(
                report["passed"] for report in model_validity.values()
            )
            else (
                "pilot_only"
                if args.stage == "pilot"
                else "formal_incomplete_or_invalid"
            )
        ),
        "model_validity": model_validity,
        "raw_rows": len(rows),
        **analysis,
    }
    output = PACKAGE / f"analysis/{args.experiment}/{args.stage}"
    write_json(output / "results.json", result)
    write_csv(output / "outcomes.csv", analysis["outcomes"])
    if "primary_effects" in analysis:
        write_csv(
            output / "primary_effects.csv",
            analysis["primary_effects"],
        )
        write_effect_tex(
            output / "primary_effects.tex",
            analysis["primary_effects"],
        )
    if "selected_actual_traces" in analysis:
        write_json(
            output / "selected_actual_traces.json",
            analysis["selected_actual_traces"],
        )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
