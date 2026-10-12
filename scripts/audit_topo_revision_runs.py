#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from swarmsafe_delta.topo_revision_common import (
    MODEL_SLUGS,
    REVISION_ROOT,
    load_jsonl,
    utc_now,
    write_json,
)


ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / REVISION_ROOT


def latex_escape(value: object) -> str:
    return (
        str(value)
        .replace("\\", r"\textbackslash{}")
        .replace("_", r"\_")
        .replace("%", r"\%")
        .replace("&", r"\&")
        .replace("#", r"\#")
    )


def validation(
    experiment: str,
    stage: str,
    model_slug: str,
) -> dict[str, Any]:
    path = (
        PACKAGE
        / f"runs/{experiment}/{stage}/{model_slug}/validation.json"
    )
    if not path.exists():
        return {
            "experiment": experiment,
            "stage": stage,
            "model_slug": model_slug,
            "passed": False,
            "expected_rows": None,
            "observed_rows": 0,
            "provider_errors": 0,
            "errors": ["NOT RUN: validation file absent"],
        }
    return json.loads(path.read_text(encoding="utf-8"))


def e3_forward_audit(model_slug: str) -> dict[str, Any]:
    rows = load_jsonl(
        PACKAGE
        / f"runs/E3/pilot/{model_slug}/raw/episodes.jsonl"
    )
    traces = [
        trace
        for row in rows
        for trace in row.get("intermediate_traces", [])
    ]
    technical = sum(bool(trace["technical_failure"]) for trace in traces)
    explicit = sum(bool(trace["explicit_drop"]) for trace in traces)
    schema_clean = (
        len(rows) == 72
        and len(traces) == 120
        and technical == 0
    )
    return {
        "model_slug": model_slug,
        "episodes": len(rows),
        "intermediate_calls": len(traces),
        "technical_failures": technical,
        "technical_failure_rate": (
            technical / len(traces) if traces else 1.0
        ),
        "explicit_drops": explicit,
        "strict_forward_schema_gate_passed": schema_clean,
        "adjudicated_status": (
            "clean_pilot_block"
            if schema_clean
            else "invalid_forward_schema_gate"
        ),
    }


def write_inventory(rows: list[dict[str, Any]]) -> None:
    path = PACKAGE / "RUN_INVENTORY.csv"
    fields = [
        "experiment",
        "stage",
        "model_slug",
        "observed_rows",
        "provider_errors",
        "passed_original_validator",
        "adjudicated_status",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    tex_lines = [
        r"\begin{tabular}{lllrrll}",
        r"\toprule",
        (
            r"Experiment & Stage & Model & Rows & Provider errors & "
            r"Original validator & Adjudicated status \\"
        ),
        r"\midrule",
    ]
    for row in rows:
        tex_lines.append(
            f"{latex_escape(row['experiment'])} & "
            f"{latex_escape(row['stage'])} & "
            f"{latex_escape(row['model_slug'])} & "
            f"{row['observed_rows']} & "
            f"{row['provider_errors']} & "
            f"{latex_escape(row['passed_original_validator'])} & "
            f"{latex_escape(row['adjudicated_status'])} \\\\"
        )
    tex_lines.extend([r"\bottomrule", r"\end{tabular}"])
    (PACKAGE / "RUN_INVENTORY.tex").write_text(
        "\n".join(tex_lines) + "\n",
        encoding="utf-8",
    )


def write_e3_adjudicated_outcomes(result: dict[str, Any]) -> None:
    rows = [row for row in result["outcomes"] if row["model_valid"]]
    fields = [
        "model_slug",
        "topology",
        "authorization_policy",
        "execution_policy",
        "world_state",
        "n",
        "proof_valid_rate",
        "advisory_protected_rate",
        "false_commit_rate",
        "true_completion_rate",
        "safe_progress_rate",
        "message_delivery_rate",
        "mean_message_similarity",
        "unsupported_authority_introduction_rate",
    ]
    output_dir = PACKAGE / "analysis/E3/pilot"
    with (output_dir / "adjudicated_outcomes.csv").open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows({field: row[field] for field in fields} for row in rows)
    tex_lines = [
        r"\begin{tabular}{lllllrrrrr}",
        r"\toprule",
        (
            r"Model & Topology & Auth. & Exec. & State & $n$ & "
            r"Proof valid & Advisory & False commit & True completion \\"
        ),
        r"\midrule",
    ]
    for row in rows:
        tex_lines.append(
            f"{latex_escape(row['model_slug'])} & "
            f"{latex_escape(row['topology'])} & "
            f"{latex_escape(row['authorization_policy'])} & "
            f"{latex_escape(row['execution_policy'])} & "
            f"{latex_escape(row['world_state'])} & "
            f"{row['n']} & "
            f"{row['proof_valid_rate']:.3f} & "
            f"{row['advisory_protected_rate']:.3f} & "
            f"{row['false_commit_rate']:.3f} & "
            f"{row['true_completion_rate']:.3f} \\\\"
        )
    tex_lines.extend([r"\bottomrule", r"\end{tabular}"])
    (output_dir / "adjudicated_outcomes.tex").write_text(
        "\n".join(tex_lines) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    e3_audit = {
        model_slug: e3_forward_audit(model_slug)
        for model_slug in MODEL_SLUGS
    }
    inventory = []
    for experiment in ("E1", "E2", "E3"):
        for stage in ("pilot", "formal"):
            for model_slug in MODEL_SLUGS:
                report = validation(experiment, stage, model_slug)
                adjudicated = (
                    e3_audit[model_slug]["adjudicated_status"]
                    if experiment == "E3" and stage == "pilot"
                    else (
                        "valid"
                        if report["passed"]
                        else "invalid_or_not_run"
                    )
                )
                inventory.append(
                    {
                        "experiment": experiment,
                        "stage": stage,
                        "model_slug": model_slug,
                        "observed_rows": report["observed_rows"],
                        "provider_errors": report["provider_errors"],
                        "passed_original_validator": report["passed"],
                        "adjudicated_status": adjudicated,
                    }
                )
    report = {
        "audited_at": utc_now(),
        "status": "post_run_integrity_audit_complete",
        "e1_formal": {
            model_slug: validation("E1", "formal", model_slug)["passed"]
            for model_slug in MODEL_SLUGS
        },
        "e2_pilot": {
            model_slug: validation("E2", "pilot", model_slug)
            for model_slug in MODEL_SLUGS
        },
        "e2_formal": {
            model_slug: validation("E2", "formal", model_slug)["passed"]
            for model_slug in MODEL_SLUGS
        },
        "e3_pilot_forward_schema": e3_audit,
        "integrity_finding": (
            "The original generic E3 validator did not aggregate "
            "intermediate forwarder schema/truncation failures. The frozen "
            "protocol requires no schema mismatch, so the post-run "
            "adjudication treats only the zero-failure Nemotron block as a "
            "clean E3 pilot block. Raw rows and original validation files "
            "remain unchanged."
        ),
    }
    write_json(PACKAGE / "POST_RUN_INTEGRITY_AUDIT.json", report)
    write_inventory(inventory)

    result_path = PACKAGE / "analysis/E3/pilot/results.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    for model_slug in MODEL_SLUGS:
        clean = e3_audit[model_slug][
            "strict_forward_schema_gate_passed"
        ]
        result["model_validity"][model_slug][
            "post_run_forward_schema_gate_passed"
        ] = clean
        result["model_validity"][model_slug][
            "post_run_adjudicated_passed"
        ] = clean
    for row in result["outcomes"]:
        row["model_valid"] = e3_audit[row["model_slug"]][
            "strict_forward_schema_gate_passed"
        ]
    result["evidence_status"] = "pilot_only_post_run_adjudicated"
    result["post_run_integrity_audit"] = (
        "experiments/topo_revision/POST_RUN_INTEGRITY_AUDIT.json"
    )
    result["selected_actual_traces"] = [
        trace
        for trace in result.get("selected_actual_traces", [])
        if e3_audit[trace["model_slug"]][
            "strict_forward_schema_gate_passed"
        ]
    ]
    write_json(
        PACKAGE / "analysis/E3/pilot/adjudicated_results.json",
        result,
    )
    write_e3_adjudicated_outcomes(result)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
