#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from swarmsafe_delta.authority_composition import (
    EXPERIMENT_ID,
    MODEL_CONFIGS,
    SMOKE_TASK_IDS,
    build_study_a_cases,
    build_threshold_cases,
    canonical_json,
    confirmatory_call_total,
    validate_design_spec,
)
from swarmsafe_delta.authority_automatic_validation import (
    AUTOMATIC_VALIDATION_PROTOCOL,
)
from swarmsafe_delta.pilot import load_tasks, sha256_file, utc_now
from swarmsafe_delta.topology_pilot import sha256_text


REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGE = (
    REPO_ROOT / "experiments/TopoSafe-Delta-AuthorityComposition-v0.2"
)
TASKS_PATH = PACKAGE / "candidate_tasks.json"
TASK_VALIDATION_PATH = PACKAGE / "task_validation.json"
AUTOMATIC_VALIDATION_PROTOCOL_PATH = (
    PACKAGE / "automatic_validation_protocol.md"
)
DESIGN_SPEC_PATH = PACKAGE / "design_spec.json"
PROTOCOL_PATH = PACKAGE / "protocol.md"
MODEL_PREFLIGHT_PATH = PACKAGE / "preflight/model_preflight.json"
SOURCE_PATHS = (
    TASKS_PATH,
    TASK_VALIDATION_PATH,
    AUTOMATIC_VALIDATION_PROTOCOL_PATH,
    DESIGN_SPEC_PATH,
    PROTOCOL_PATH,
    REPO_ROOT / "data/toposafe_authority_task_catalog_v0.1.json",
    REPO_ROOT / "src/swarmsafe_delta/authority_composition.py",
    REPO_ROOT / "src/swarmsafe_delta/authority_automatic_validation.py",
    REPO_ROOT / "src/swarmsafe_delta/authority_task_construction.py",
    REPO_ROOT / "src/swarmsafe_delta/authority_placement.py",
    REPO_ROOT / "src/swarmsafe_delta/pilot.py",
    REPO_ROOT / "scripts/preflight_authority_composition_models.py",
    REPO_ROOT / "scripts/run_authority_composition.py",
    REPO_ROOT / "scripts/validate_authority_composition.py",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Write a preflight report without creating a frozen manifest.",
    )
    return parser.parse_args()


def relative(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def validate_model_preflight(report: dict[str, Any] | None) -> list[str]:
    if report is None:
        return ["excluded model transport preflight has not been run"]
    errors: list[str] = []
    if report.get("evidence_type") != "excluded_transport_response_preflight":
        errors.append("model preflight evidence type is invalid")
    if report.get("excluded_from_formal_analysis") is not True:
        errors.append("model preflight is not marked analysis-excluded")
    indexed = {
        row.get("model_slug"): row for row in report.get("models", [])
    }
    if set(indexed) != set(MODEL_CONFIGS):
        errors.append("model preflight roster does not match frozen candidates")
    for slug, config in MODEL_CONFIGS.items():
        row = indexed.get(slug, {})
        expected_response_mode = (
            "auto_action_tool"
            if config.get("action_tool_mode") == "auto"
            else (
                "forced_action_tool"
                if config["force_action_tool"]
                else "json_text"
            )
        )
        if row.get("model_id") != config["model_id"]:
            errors.append(f"{slug}: preflight model ID does not match code")
        if row.get("region") != config["region"]:
            errors.append(f"{slug}: preflight region does not match code")
        if row.get("response_mode") != expected_response_mode:
            errors.append(
                f"{slug}: preflight response mode does not match code"
            )
        if row.get("status") != "pass":
            errors.append(f"{slug}: transport/response preflight did not pass")
    return errors


def prompt_checks(
    study_a_cases: list[dict[str, Any]],
    threshold_cases: list[dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    for cases in (study_a_cases, threshold_cases):
        by_task_regime: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for case in cases:
            if case["is_control"]:
                continue
            key = (case["task_id"], case["authority_regime"])
            by_task_regime.setdefault(key, []).append(case)
        for key, rows in by_task_regime.items():
            message_hashes = {
                sha256_text(row["message_body"]) for row in rows
            }
            prompt_lengths = {
                len(f"{row['executor_system']}\n\n{row['executor_user']}")
                for row in rows
            }
            if len(message_hashes) != 1:
                errors.append(f"{key}: message body changed across cells")
            if len(prompt_lengths) != 1:
                errors.append(f"{key}: prompt length changed across cells")
    return errors


def main() -> None:
    args = parse_args()
    blockers: list[str] = []
    raw_paths = list(PACKAGE.glob("smoke/**/raw/episodes.jsonl"))
    raw_paths.extend(PACKAGE.glob("models/**/raw/episodes.jsonl"))
    if raw_paths:
        blockers.append(
            "provider result files already exist: "
            + ", ".join(relative(path) for path in raw_paths)
        )

    tasks = load_tasks(TASKS_PATH)
    design_spec = json.loads(DESIGN_SPEC_PATH.read_text(encoding="utf-8"))
    task_validation = json.loads(
        TASK_VALIDATION_PATH.read_text(encoding="utf-8")
    )
    if len(tasks) != 120:
        blockers.append(f"expected 120 candidate tasks, found {len(tasks)}")
    if task_validation.get("automatic_gate_passed") is not True:
        blockers.append("deterministic task gate has not passed")
    if (
        task_validation.get("validation_protocol")
        != AUTOMATIC_VALIDATION_PROTOCOL
    ):
        blockers.append("automatic validation protocol does not match code")
    if task_validation.get("candidate_tasks_sha256") != sha256_text(
        canonical_json(tasks)
    ):
        blockers.append("automatic validation task hash does not match tasks")
    if task_validation.get("human_review_required") is not False:
        blockers.append("task package still requires human review")
    if task_validation.get("human_review_used_as_evidence") is not False:
        blockers.append("task package still uses human review as evidence")
    required_automatic_checks = (
        ("semantic_contract", "tasks_compared", 120),
        (
            "metamorphic_validation",
            "action_order_permutations_checked",
            720,
        ),
        ("metamorphic_validation", "oracle_trace_checks", 480),
        ("metamorphic_validation", "paired_prompt_checks", 720),
        (
            "proof_protocol_validation",
            "proof_assignments_checked",
            192,
        ),
    )
    for section, field, expected in required_automatic_checks:
        report = task_validation.get(section, {})
        if report.get("passed") is not True:
            blockers.append(f"{section} did not pass")
        if report.get(field) != expected:
            blockers.append(
                f"{section}.{field} is {report.get(field)}, "
                f"expected {expected}"
            )
    blockers.extend(validate_design_spec(design_spec))

    model_preflight = (
        json.loads(MODEL_PREFLIGHT_PATH.read_text(encoding="utf-8"))
        if MODEL_PREFLIGHT_PATH.exists()
        else None
    )
    blockers.extend(validate_model_preflight(model_preflight))

    missing_sources = [
        relative(path) for path in SOURCE_PATHS if not path.exists()
    ]
    if missing_sources:
        blockers.append(f"freeze source files are missing: {missing_sources}")

    study_a_cases = build_study_a_cases(tasks)
    threshold_cases = build_threshold_cases(tasks)
    if len(study_a_cases) != 1680:
        blockers.append(
            f"Study A case count is {len(study_a_cases)}, expected 1680"
        )
    if len(threshold_cases) != 180:
        blockers.append(
            f"threshold case count is {len(threshold_cases)}, expected 180"
        )
    all_case_ids = [
        f"{case['task_id']}::{case['condition']}"
        for case in [*study_a_cases, *threshold_cases]
    ]
    if len(all_case_ids) != len(set(all_case_ids)):
        blockers.append("implemented study case IDs are not unique")
    blockers.extend(prompt_checks(study_a_cases, threshold_cases))
    if set(SMOKE_TASK_IDS) - {task["id"] for task in tasks}:
        blockers.append("smoke task IDs are absent from candidate tasks")

    report = {
        "experiment_id": EXPERIMENT_ID,
        "checked_at": utc_now(),
        "status": "ready_to_freeze" if not blockers else "blocked",
        "candidate_tasks": len(tasks),
        "automatic_task_gate_passed": bool(
            task_validation.get("automatic_gate_passed")
        ),
        "automatic_validation": {
            "protocol": task_validation.get("validation_protocol"),
            "semantic_contract_tasks": task_validation.get(
                "semantic_contract", {}
            ).get("tasks_compared"),
            "oracle_trace_checks": task_validation.get(
                "metamorphic_validation", {}
            ).get("oracle_trace_checks"),
            "action_order_permutations": task_validation.get(
                "metamorphic_validation", {}
            ).get("action_order_permutations_checked"),
            "paired_prompt_checks": task_validation.get(
                "metamorphic_validation", {}
            ).get("paired_prompt_checks"),
            "proof_assignments": task_validation.get(
                "proof_protocol_validation", {}
            ).get("proof_assignments_checked"),
            "passed": task_validation.get("automatic_gate_passed"),
        },
        "human_review_required": False,
        "legacy_human_review_artifacts_used": False,
        "model_preflight_present": model_preflight is not None,
        "models": list(MODEL_CONFIGS),
        "study_a_cases_per_model": len(study_a_cases),
        "threshold_cases_per_model": len(threshold_cases),
        "implemented_formal_calls": (
            len(study_a_cases) + len(threshold_cases)
        )
        * len(MODEL_CONFIGS),
        "full_confirmatory_calls_planned": confirmatory_call_total(),
        "blockers": blockers,
    }
    (PACKAGE / "freeze_preflight.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    if blockers:
        print(canonical_json(report))
        if not args.check_only:
            raise SystemExit(1)
        return
    if args.check_only:
        print(canonical_json(report))
        return

    frozen_at = utc_now()
    source_hashes = {
        relative(path): sha256_file(path) for path in SOURCE_PATHS
    }
    source_hashes[relative(MODEL_PREFLIGHT_PATH)] = sha256_file(
        MODEL_PREFLIGHT_PATH
    )
    prompt_inventory = [
        {
            "episode_id": f"{case['task_id']}::{case['condition']}",
            "system_sha256": sha256_text(case["executor_system"]),
            "user_sha256": sha256_text(case["executor_user"]),
            "message_body_sha256": sha256_text(case["message_body"]),
            "provenance_metadata_sha256": sha256_text(
                case["provenance_metadata"]
            ),
        }
        for case in [*study_a_cases, *threshold_cases]
    ]
    manifest = {
        "experiment_id": EXPERIMENT_ID,
        "status": "frozen_pre_run",
        "frozen_at": frozen_at,
        "task_file": relative(TASKS_PATH),
        "automatic_validation_file": relative(TASK_VALIDATION_PATH),
        "automatic_validation_protocol": relative(
            AUTOMATIC_VALIDATION_PROTOCOL_PATH
        ),
        "human_review_required": False,
        "legacy_human_review_artifacts_used": False,
        "model_preflight": relative(MODEL_PREFLIGHT_PATH),
        "source_hashes": source_hashes,
        "prompt_inventory_sha256": sha256_text(
            canonical_json(prompt_inventory)
        ),
        "models": MODEL_CONFIGS,
        "studies": {
            "study_a": {
                "cases_per_model": len(study_a_cases),
                "formal_calls": len(study_a_cases) * len(MODEL_CONFIGS),
            },
            "threshold": {
                "cases_per_model": len(threshold_cases),
                "formal_calls": len(threshold_cases) * len(MODEL_CONFIGS),
            },
        },
        "implemented_formal_calls": (
            len(study_a_cases) + len(threshold_cases)
        )
        * len(MODEL_CONFIGS),
        "full_confirmatory_calls_planned": confirmatory_call_total(),
        "not_yet_implemented_in_this_runner": [
            "study_b1_matched_topology",
            "study_b2_free_running_subset",
            "schedule_robustness_subset",
            "study_c_targeted_mechanism_ablations",
        ],
        "smoke_task_ids": list(SMOKE_TASK_IDS),
        "smoke_calls": len(SMOKE_TASK_IDS) * 14 * len(MODEL_CONFIGS),
        "max_output_tokens": 200,
        "maximum_provider_attempts": 3,
        "connect_timeout_seconds": 10,
        "read_timeout_seconds": 180,
        "workers": 6,
        "schedule_seed": 2026100611,
        "provider_seed_supported": False,
        "graph_budget": {
            "nodes": 4,
            "edges": 3,
            "executor_deliveries": 1,
            "model_calls": 1,
        },
        "evidence_boundary": (
            "Study A and the authority-cut threshold extension are frozen "
            "only after deterministic contract, oracle-replay, metamorphic, "
            "paired-prompt, and exhaustive proof-policy validation of all "
            "120 tasks, plus an excluded model transport preflight. No human "
            "review is required or used as experiment evidence. Model "
            "preflight and smoke rows are excluded from formal analysis. The "
            "remaining matched-topology and targeted ablation studies retain "
            "planned status."
        ),
    }
    (PACKAGE / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    frozen_protocol = PROTOCOL_PATH.read_text(encoding="utf-8")
    frozen_protocol += (
        f"\n\n## Partial Confirmatory Freeze\n\nFrozen at `{frozen_at}` for "
        "Study A and Study C1 only. Study B and Study C2 remain planned.\n\n"
        "## Frozen Source Hashes\n\n```json\n"
        + json.dumps(source_hashes, indent=2, sort_keys=True)
        + "\n```\n"
    )
    (PACKAGE / "frozen_protocol.md").write_text(
        frozen_protocol,
        encoding="utf-8",
    )
    print(
        canonical_json(
            {
                "status": "frozen_pre_run",
                "manifest": relative(PACKAGE / "manifest.json"),
                "implemented_formal_calls": manifest[
                    "implemented_formal_calls"
                ],
                "full_confirmatory_calls_planned": confirmatory_call_total(),
            }
        )
    )


if __name__ == "__main__":
    main()
