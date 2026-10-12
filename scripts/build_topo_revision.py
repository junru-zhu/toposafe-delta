#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from swarmsafe_delta.topo_revision_authority_cut import (
    build_control_cases,
    build_treatment_cases,
    select_control_tasks,
    select_pilot_tasks as select_e2_pilot_tasks,
    validate_cases as validate_e2_cases,
)
from swarmsafe_delta.topo_revision_common import (
    BOOTSTRAP_DRAWS,
    DEFAULT_SEED,
    MAX_ATTEMPTS,
    MAX_OUTPUT_TOKENS,
    MODEL_SLUGS,
    REVISION_ROOT,
    sha256_file,
    utc_now,
    write_json,
)
from swarmsafe_delta.topo_revision_provenance import (
    build_cases as build_e1_cases,
    select_pilot_tasks as select_e1_pilot_tasks,
    validate_cases as validate_e1_cases,
)
from swarmsafe_delta.topo_revision_tasks import (
    E1_DOMAINS,
    E3_DOMAINS,
    build_e1_tasks,
    build_e2_tasks,
    build_e3_tasks,
    validate_tasks,
)
from swarmsafe_delta.topo_revision_workflow import (
    build_cases as build_e3_cases,
    select_pilot_tasks as select_e3_pilot_tasks,
    validate_cases as validate_e3_cases,
)


ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / REVISION_ROOT
FROZEN = PACKAGE / "frozen"
MANIFEST = PACKAGE / "manifest.json"
SOURCE_PATHS = (
    PACKAGE / "EXISTING_EVIDENCE_AUDIT.md",
    PACKAGE / "PROTOCOL.md",
    PACKAGE / "EXPERIMENT_MATRIX.csv",
    ROOT / "src/swarmsafe_delta/topo_revision_common.py",
    ROOT / "src/swarmsafe_delta/topo_revision_tasks.py",
    ROOT / "src/swarmsafe_delta/topo_revision_provenance.py",
    ROOT / "src/swarmsafe_delta/topo_revision_authority_cut.py",
    ROOT / "src/swarmsafe_delta/topo_revision_workflow.py",
    ROOT / "scripts/build_topo_revision.py",
    ROOT / "scripts/run_topo_revision.py",
    ROOT / "scripts/validate_topo_revision.py",
    ROOT / "scripts/analyze_topo_revision.py",
    ROOT / "scripts/plot_topo_revision.py",
    ROOT / "scripts/audit_topo_revision_evidence.py",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("build", "freeze"), required=True)
    return parser.parse_args()


def git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
    ).strip()


def build() -> None:
    if MANIFEST.exists():
        raise RuntimeError("revision manifest already frozen")
    e1_tasks = build_e1_tasks()
    e2_tasks = build_e2_tasks()
    e3_tasks = build_e3_tasks()
    task_validation = {
        "E1": validate_tasks(
            e1_tasks,
            expected_count=60,
            expected_domains=E1_DOMAINS,
            minimum_archetypes_per_domain=3,
        ),
        "E2": validate_tasks(
            e2_tasks,
            expected_count=80,
            expected_domains=E1_DOMAINS,
            minimum_archetypes_per_domain=3,
        ),
        "E3": validate_tasks(
            e3_tasks,
            expected_count=48,
            expected_domains=E3_DOMAINS,
            minimum_archetypes_per_domain=4,
        ),
    }
    e1_cases = build_e1_cases(e1_tasks)
    e2_cases = build_treatment_cases(e2_tasks)
    e2_control_tasks = select_control_tasks(e2_tasks, stage="formal")
    e2_controls = build_control_cases(e2_control_tasks)
    e3_cases = build_e3_cases(e3_tasks)
    case_validation = {
        "E1": validate_e1_cases(e1_tasks, e1_cases),
        "E2": validate_e2_cases(
            e2_tasks,
            e2_cases,
            e2_control_tasks,
            e2_controls,
        ),
        "E3": validate_e3_cases(e3_tasks, e3_cases),
    }
    write_json(FROZEN / "e1_tasks.json", e1_tasks)
    write_json(FROZEN / "e1_cases.json", e1_cases)
    write_json(FROZEN / "e2_tasks.json", e2_tasks)
    write_json(FROZEN / "e2_cases.json", e2_cases)
    write_json(FROZEN / "e2_control_cases.json", e2_controls)
    write_json(FROZEN / "e3_tasks.json", e3_tasks)
    write_json(FROZEN / "e3_cases.json", e3_cases)
    pilot_ids = {
        "E1": [task["id"] for task in select_e1_pilot_tasks(e1_tasks)],
        "E2": [task["id"] for task in select_e2_pilot_tasks(e2_tasks)],
        "E2_controls": [
            task["id"]
            for task in select_control_tasks(e2_tasks, stage="pilot")
        ],
        "E3": [task["id"] for task in select_e3_pilot_tasks(e3_tasks)],
    }
    write_json(FROZEN / "pilot_task_ids.json", pilot_ids)
    automatic_errors = [
        *(f"{experiment}: {error}" for experiment, errors in task_validation.items() for error in errors),
        *(
            f"{experiment}: {error}"
            for experiment, report in case_validation.items()
            for error in report["errors"]
        ),
    ]
    validation = {
        "status": (
            "automatic_preflight_passed"
            if not automatic_errors
            else "automatic_preflight_failed"
        ),
        "passed": not automatic_errors,
        "task_validation": task_validation,
        "case_validation": case_validation,
        "pilot_task_ids": pilot_ids,
        "errors": automatic_errors,
        "generated_at": utc_now(),
    }
    write_json(FROZEN / "preflight_validation.json", validation)
    e3_calls_per_model = sum(
        int(case["assigned_model_calls"]) for case in e3_cases
    )
    summary = {
        "status": validation["status"],
        "formal": {
            "E1": {
                "base_tasks": len(e1_tasks),
                "executor_episodes": len(e1_cases) * len(MODEL_SLUGS),
                "assigned_calls": len(e1_cases) * len(MODEL_SLUGS),
            },
            "E2": {
                "base_tasks": len(e2_tasks),
                "executor_episodes": (
                    (len(e2_cases) + len(e2_controls))
                    * len(MODEL_SLUGS)
                ),
                "assigned_calls": (
                    (len(e2_cases) + len(e2_controls))
                    * len(MODEL_SLUGS)
                ),
            },
            "E3": {
                "base_tasks": len(e3_tasks),
                "executor_episodes": len(e3_cases) * len(MODEL_SLUGS),
                "assigned_calls": e3_calls_per_model * len(MODEL_SLUGS),
            },
        },
        "pilot": {
            "E1_assigned_calls": 160,
            "E2_assigned_calls": 208,
            "E3_assigned_calls": 768,
            "total_assigned_calls": 1_136,
        },
        "default_call_plan": {
            "pilot_all": 1_136,
            "formal_E1_E2": 6_304,
            "combined": 7_440,
            "formal_E3_additional": 12_288,
            "all_experiments_total": 19_728,
            "default_cap": 15_000,
        },
        "generated_at": utc_now(),
    }
    write_json(FROZEN / "package_summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    if not validation["passed"]:
        raise SystemExit(1)


def freeze() -> None:
    if MANIFEST.exists():
        raise RuntimeError("revision manifest already frozen")
    required_generated = (
        FROZEN / "e1_tasks.json",
        FROZEN / "e1_cases.json",
        FROZEN / "e2_tasks.json",
        FROZEN / "e2_cases.json",
        FROZEN / "e2_control_cases.json",
        FROZEN / "e3_tasks.json",
        FROZEN / "e3_cases.json",
        FROZEN / "pilot_task_ids.json",
        FROZEN / "preflight_validation.json",
        FROZEN / "package_summary.json",
    )
    missing = [
        str(path)
        for path in (*SOURCE_PATHS, *required_generated)
        if not path.exists()
    ]
    if missing:
        raise RuntimeError(f"missing freeze inputs: {missing}")
    preflight = json.loads(
        (FROZEN / "preflight_validation.json").read_text(encoding="utf-8")
    )
    if not preflight["passed"]:
        raise RuntimeError("automatic preflight did not pass")
    sources = {
        str(path.relative_to(ROOT)): sha256_file(path)
        for path in (*SOURCE_PATHS, *required_generated)
    }
    manifest: dict[str, Any] = {
        "experiment_suite": "TopoSafe-Delta-Revision-v1.0",
        "status": "frozen_pre_run",
        "frozen_at": utc_now(),
        "git_head_at_freeze": git_head(),
        "schedule_seed": DEFAULT_SEED,
        "provider_seed_supported": False,
        "bootstrap_draws": BOOTSTRAP_DRAWS,
        "maximum_provider_attempts": MAX_ATTEMPTS,
        "executor_max_output_tokens": MAX_OUTPUT_TOKENS,
        "models": list(MODEL_SLUGS),
        "default_safety_limits": {
            "MAX_NEW_LLM_CALLS": 15_000,
            "MAX_SPEND_USD": 250,
            "MAX_PARALLEL_REQUESTS": 5,
        },
        "source_hashes": sources,
    }
    write_json(MANIFEST, manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))


def main() -> None:
    args = parse_args()
    if args.mode == "build":
        build()
    else:
        freeze()


if __name__ == "__main__":
    main()
