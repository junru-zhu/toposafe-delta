#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from swarmsafe_delta.authority_placement import (
    AUTHORITY_PLACEMENTS,
    CLAIM_TRUTHS,
    CONTROL_CONDITIONS,
    CREDENTIALS,
    EXPERIMENT_ID,
    MODEL_CONFIGS,
    SMOKE_TASK_IDS,
    build_cases,
    factorial_cells,
    factorial_condition_id,
    task_gate_spec,
)
from swarmsafe_delta.pilot import (
    canonical_json,
    load_tasks,
    sha256_file,
    utc_now,
)
from swarmsafe_delta.topology_pilot import sha256_text


ROOT = Path("experiments/TopoSafe-Delta-AuthorityPlacement-v1.6")
TASKS_PATH = Path("data/authority_placement_tasks_v1.json")
MATRIX_PATH = ROOT / "condition_matrix.json"
PROTOCOL_PATH = ROOT / "protocol.md"
SOURCE_PATHS = (
    TASKS_PATH,
    MATRIX_PATH,
    PROTOCOL_PATH,
    Path("src/swarmsafe_delta/authority_placement.py"),
    Path("src/swarmsafe_delta/pilot.py"),
    Path("scripts/run_authority_placement.py"),
    Path("scripts/validate_authority_placement.py"),
    Path("scripts/analyze_authority_placement.py"),
)


def main() -> None:
    raw_paths = list(ROOT.glob("smoke/*/raw/episodes.jsonl"))
    raw_paths.extend(ROOT.glob("models/*/raw/episodes.jsonl"))
    if raw_paths:
        raise RuntimeError(
            "Refusing to freeze after provider results exist: "
            + ", ".join(str(path) for path in raw_paths)
        )

    tasks = load_tasks(TASKS_PATH)
    matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    errors = []
    if matrix.get("experiment_id") != EXPERIMENT_ID:
        errors.append("Condition matrix experiment ID does not match code")
    if matrix.get("max_output_tokens") != 200:
        errors.append("Condition matrix max_output_tokens must be 200")
    family_counts = Counter(task["policy_family"] for task in tasks)
    expected_families = {
        "approval_bypass": 6,
        "false_completion": 6,
        "protected_transfer": 6,
        "unauthorized_execution": 6,
    }
    if len(tasks) != 24:
        errors.append(f"Expected 24 tasks, found {len(tasks)}")
    if dict(sorted(family_counts.items())) != expected_families:
        errors.append(
            f"Unexpected policy-family counts: {dict(family_counts)}"
        )
    if set(SMOKE_TASK_IDS) - {task["id"] for task in tasks}:
        errors.append("Smoke task IDs are missing from the task file")

    code_cells = [
        {
            "authority_placement": cell["authority_placement"],
            "credential": cell["credential"],
            "claim_truth": cell["claim_truth"],
        }
        for cell in factorial_cells()
    ]
    if matrix["factorial_cells"] != code_cells:
        errors.append("Condition matrix does not match code factorial cells")
    if matrix["factors"] != {
        "authority_placement": list(AUTHORITY_PLACEMENTS),
        "credential": list(CREDENTIALS),
        "claim_truth": list(CLAIM_TRUTHS),
    }:
        errors.append("Condition matrix factors do not match code")

    task_checks = []
    for task in tasks:
        try:
            gate = task_gate_spec(task)
            task_checks.append(
                {
                    "task_id": task["id"],
                    "policy_family": task["policy_family"],
                    "gate_name": gate["gate_name"],
                    "protected_action_id": gate["protected_action_id"],
                    "safe_action_id": gate["safe_action_id"],
                    "passed": True,
                }
            )
        except Exception as exc:
            errors.append(f"{task['id']}: {type(exc).__name__}: {exc}")
            task_checks.append(
                {
                    "task_id": task["id"],
                    "policy_family": task["policy_family"],
                    "passed": False,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )

    cases = build_cases(tasks)
    prompt_checks = []
    indexed = {
        (case["task_id"], case["condition"]): case for case in cases
    }
    for task in tasks:
        task_id = task["id"]
        factorial_task_cases = [
            case
            for case in cases
            if case["task_id"] == task_id and not case["is_control"]
        ]
        message_hashes = {
            sha256_text(case["message_body"])
            for case in factorial_task_cases
        }
        prompt_lengths = {
            len(
                f"{case['executor_system']}\n\n"
                f"{case['executor_user']}"
            )
            for case in factorial_task_cases
        }
        truth_mismatches = []
        for placement in AUTHORITY_PLACEMENTS:
            for credential in CREDENTIALS:
                true_case = indexed[
                    (
                        task_id,
                        factorial_condition_id(
                            placement,
                            credential,
                            "true_update",
                        ),
                    )
                ]
                false_case = indexed[
                    (
                        task_id,
                        factorial_condition_id(
                            placement,
                            credential,
                            "false_update",
                        ),
                    )
                ]
                true_prompt = (
                    f"{true_case['executor_system']}\n\n"
                    f"{true_case['executor_user']}"
                )
                false_prompt = (
                    f"{false_case['executor_system']}\n\n"
                    f"{false_case['executor_user']}"
                )
                if true_prompt != false_prompt:
                    truth_mismatches.append(f"{placement}:{credential}")
        passed = (
            len(message_hashes) == 1
            and len(prompt_lengths) == 1
            and not truth_mismatches
        )
        if not passed:
            errors.append(f"{task_id}: frozen prompt checks failed")
        prompt_checks.append(
            {
                "task_id": task_id,
                "message_body_hash_count": len(message_hashes),
                "prompt_length_count": len(prompt_lengths),
                "truth_prompt_mismatches": truth_mismatches,
                "passed": passed,
            }
        )

    task_validation = {
        "status": "passed" if not errors else "failed",
        "tasks": len(tasks),
        "family_counts": dict(sorted(family_counts.items())),
        "factorial_cells": len(factorial_cells()),
        "controls": list(CONTROL_CONDITIONS),
        "episodes_per_model": len(cases),
        "task_checks": task_checks,
        "prompt_checks": prompt_checks,
        "errors": errors,
    }
    (ROOT / "task_validation.json").write_text(
        json.dumps(
            task_validation,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    if errors:
        raise RuntimeError("Freeze validation failed: " + " | ".join(errors))

    frozen_at = utc_now()
    source_hashes = {
        str(path): sha256_file(path) for path in SOURCE_PATHS
    }
    prompt_inventory = [
        {
            "task_id": case["task_id"],
            "condition": case["condition"],
            "system_sha256": sha256_text(case["executor_system"]),
            "user_sha256": sha256_text(case["executor_user"]),
            "message_body_sha256": sha256_text(case["message_body"]),
        }
        for case in cases
    ]
    manifest = {
        "experiment_id": EXPERIMENT_ID,
        "status": "frozen_pre_run",
        "frozen_at": frozen_at,
        "task_file": str(TASKS_PATH),
        "condition_matrix": str(MATRIX_PATH),
        "protocol": str(PROTOCOL_PATH),
        "source_hashes": source_hashes,
        "prompt_inventory_sha256": sha256_text(
            canonical_json(prompt_inventory)
        ),
        "task_count": len(tasks),
        "factorial_cells": len(factorial_cells()),
        "control_cells": len(CONTROL_CONDITIONS),
        "episodes_per_model": len(cases),
        "models": MODEL_CONFIGS,
        "smoke_task_ids": list(SMOKE_TASK_IDS),
        "smoke_calls": len(SMOKE_TASK_IDS) * len(cases) // len(tasks)
        * len(MODEL_CONFIGS),
        "formal_calls": len(cases) * len(MODEL_CONFIGS),
        "max_output_tokens": 200,
        "maximum_provider_attempts": 3,
        "read_timeout_seconds": 180,
        "workers": 6,
        "schedule_seed": 2026100607,
        "provider_seed_supported": False,
        "graph_budget": {
            "nodes": 4,
            "edges": 3,
            "executor_deliveries": 1,
            "model_calls": 1,
        },
        "evidence_boundary": (
            "Corrected protocol frozen before any v1.6 provider call. v1 "
            "through v1.5 remain immutable invalid/excluded runs. v1.6 "
            "uses exact state-field patches, the preregistered 200-token "
            "budget, deterministic control scoring, and a forced enumerated "
            "action tool for Claude Sonnet 5. Provider-error resume atomically "
            "replaces failed rows while preserving their failure history."
        ),
    }
    (ROOT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    protocol = PROTOCOL_PATH.read_text(encoding="utf-8")
    protocol = protocol.replace(
        "**Status:** Corrected protocol planned; no v1.6 results have been collected.",
        f"**Status:** Frozen before provider calls at `{frozen_at}`.",
        1,
    )
    protocol += (
        "\n\n## Frozen Source Hashes\n\n```json\n"
        + json.dumps(source_hashes, indent=2, sort_keys=True)
        + "\n```\n"
    )
    (ROOT / "frozen_protocol.md").write_text(
        protocol,
        encoding="utf-8",
    )
    print(
        canonical_json(
            {
                "status": "frozen_pre_run",
                "manifest": str(ROOT / "manifest.json"),
                "task_validation": str(ROOT / "task_validation.json"),
                "smoke_calls": manifest["smoke_calls"],
                "formal_calls": manifest["formal_calls"],
            }
        )
    )


if __name__ == "__main__":
    main()
