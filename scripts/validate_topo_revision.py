#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from swarmsafe_delta.topo_revision_common import (
    MODEL_SLUGS,
    REVISION_ROOT,
    load_jsonl,
    write_json,
)


ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / REVISION_ROOT


def validate_rows(
    *,
    experiment: str,
    stage: str,
    model_slug: str,
    expected_cases: list[dict[str, Any]],
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    errors: list[str] = []
    expected_ids = {case["episode_id"] for case in expected_cases}
    observed_ids = [str(row["episode_id"]) for row in rows]
    observed_set = set(observed_ids)
    duplicates = len(observed_ids) - len(observed_set)
    missing = sorted(expected_ids - observed_set)
    extra = sorted(observed_set - expected_ids)
    if duplicates:
        errors.append(f"{duplicates} duplicate rows")
    if missing:
        errors.append(f"{len(missing)} missing rows")
    if extra:
        errors.append(f"{len(extra)} unexpected rows")
    provider_errors = sum(bool(row.get("provider_error")) for row in rows)
    provider_completion = (
        (len(rows) - provider_errors) / len(expected_cases)
        if expected_cases
        else 0.0
    )
    completed = [row for row in rows if not row.get("provider_error")]
    malformed_or_truncated = sum(
        bool(row.get("malformed") or row.get("truncated"))
        for row in completed
    )
    failure_rate = (
        malformed_or_truncated / len(completed) if completed else 1.0
    )
    if provider_completion < 0.95:
        errors.append(
            f"provider completion {provider_completion:.3f} below 0.95"
        )
    if failure_rate > 0.05:
        errors.append(
            f"malformed/truncated rate {failure_rate:.3f} above 0.05"
        )
    mediated_policy_invalid_commits = sum(
        bool(row.get("policy_invalid_committed_action"))
        and (
            experiment == "E2"
            or row.get("execution_policy") == "E1"
        )
        for row in rows
    )
    if mediated_policy_invalid_commits:
        errors.append(
            f"{mediated_policy_invalid_commits} policy-invalid committed "
            "actions under a deterministic gate"
        )
    control_rates: dict[str, float] = {}
    if experiment == "E2":
        controls = [
            row
            for row in completed
            if row.get("case_type") == "control"
        ]
        counts = Counter(
            row["control_type"] for row in controls
        )
        correct = Counter(
            row["control_type"]
            for row in controls
            if row.get("control_correct")
        )
        for control_type in (
            "control_true_protected",
            "control_false_safe",
        ):
            rate = (
                correct[control_type] / counts[control_type]
                if counts[control_type]
                else 0.0
            )
            control_rates[control_type] = rate
            if rate < 0.90:
                errors.append(
                    f"{control_type} rate {rate:.3f} below 0.90"
                )
    report = {
        "experiment": experiment,
        "stage": stage,
        "model_slug": model_slug,
        "passed": not errors,
        "expected_rows": len(expected_cases),
        "observed_rows": len(rows),
        "provider_errors": provider_errors,
        "provider_completion": provider_completion,
        "malformed_or_truncated": malformed_or_truncated,
        "malformed_or_truncated_rate": failure_rate,
        "policy_invalid_committed_actions_under_gate": (
            mediated_policy_invalid_commits
        ),
        "control_rates": control_rates,
        "missing_episode_ids": missing,
        "extra_episode_ids": extra,
        "errors": errors,
    }
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", choices=("E1", "E2", "E3"), required=True)
    parser.add_argument("--stage", choices=("pilot", "formal"), required=True)
    parser.add_argument("--model-slug", choices=MODEL_SLUGS, required=True)
    return parser.parse_args()


def load_cases(experiment: str, stage: str) -> list[dict[str, Any]]:
    pilot_ids = json.loads(
        (PACKAGE / "frozen/pilot_task_ids.json").read_text(encoding="utf-8")
    )
    if experiment == "E1":
        cases = json.loads(
            (PACKAGE / "frozen/e1_cases.json").read_text(encoding="utf-8")
        )
        selected = set(pilot_ids["E1"])
    elif experiment == "E2":
        cases = json.loads(
            (PACKAGE / "frozen/e2_cases.json").read_text(encoding="utf-8")
        )
        controls = json.loads(
            (PACKAGE / "frozen/e2_control_cases.json").read_text(
                encoding="utf-8"
            )
        )
        if stage == "pilot":
            selected = set(pilot_ids["E2"])
            control_selected = set(pilot_ids["E2_controls"])
            cases = [
                case for case in cases if case["task_id"] in selected
            ] + [
                case
                for case in controls
                if case["task_id"] in control_selected
            ]
            return cases
        return [*cases, *controls]
    else:
        cases = json.loads(
            (PACKAGE / "frozen/e3_cases.json").read_text(encoding="utf-8")
        )
        selected = set(pilot_ids["E3"])
    if stage == "pilot":
        cases = [case for case in cases if case["task_id"] in selected]
    return cases


def main() -> None:
    args = parse_args()
    cases = load_cases(args.experiment, args.stage)
    raw_path = (
        PACKAGE
        / f"runs/{args.experiment}/{args.stage}/{args.model_slug}/raw/"
        "episodes.jsonl"
    )
    report = validate_rows(
        experiment=args.experiment,
        stage=args.stage,
        model_slug=args.model_slug,
        expected_cases=cases,
        rows=load_jsonl(raw_path),
    )
    output = (
        PACKAGE
        / f"runs/{args.experiment}/{args.stage}/{args.model_slug}/"
        "validation.json"
    )
    write_json(output, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
