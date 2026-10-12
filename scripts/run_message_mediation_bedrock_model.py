#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from swarmsafe_delta.message_mediation_pilot import (
    ALL_CONDITIONS,
    analyze_rows,
    build_message_bank,
    render_summary_markdown,
    run_jobs,
    validate_rows,
)
from swarmsafe_delta.phase1_multimodel import CompatibleBedrockTextModel
from swarmsafe_delta.pilot import (
    canonical_json,
    load_tasks,
    sha256_file,
    utc_now,
)
from swarmsafe_delta.topology_pilot import (
    ALL_SOURCE_REGIMES,
    load_jsonl,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run one Bedrock model on the frozen TopoSafe-Delta "
            "message-mediation protocol."
        )
    )
    parser.add_argument("--model-slug", required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--tasks",
        type=Path,
        default=Path("data/calibration_boundary_tasks_v0.2.json"),
    )
    parser.add_argument(
        "--role-raw",
        type=Path,
        default=Path(
            "experiments/TopoSafe-Delta-RolePlacementPilot-v1/"
            "raw/episodes.jsonl"
        ),
    )
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument("--temperature", type=float)
    parser.add_argument("--top-p", type=float)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--connect-timeout-seconds", type=int, default=10)
    parser.add_argument("--read-timeout-seconds", type=int, default=180)
    parser.add_argument("--additional-fields-json")
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--seed", type=int, default=2026100505)
    parser.add_argument("--task-id", action="append", default=[])
    parser.add_argument(
        "--condition",
        action="append",
        choices=ALL_CONDITIONS,
        default=[],
    )
    parser.add_argument(
        "--source-regime",
        action="append",
        choices=ALL_SOURCE_REGIMES,
        default=[],
    )
    return parser.parse_args()


def parse_additional_fields(raw: str | None) -> dict[str, Any] | None:
    if raw is None:
        return None
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("--additional-fields-json must decode to an object")
    return value


def render_protocol(args: argparse.Namespace) -> str:
    return f"""# TopoSafe-Delta Message-Mediation Model Replication

**Status:** Development replication of the frozen message-mediation protocol.

- Model slug: `{args.model_slug}`
- Model ID: `{args.model_id}`
- Region: `{args.region}`
- Temperature: `{args.temperature}`
- Top-p: `{args.top_p}`
- Read timeout: `{args.read_timeout_seconds}` seconds
- Maximum attempts: `{args.max_attempts}`
- Additional fields: `{args.additional_fields_json}`

The task set, frozen messages, conditions, prompt construction, executable
scoring, and paired analysis are identical to the Nova development pilot.
Provider-specific inference settings are recorded rather than silently
normalized.
"""


def main() -> None:
    args = parse_args()
    additional_fields = parse_additional_fields(
        args.additional_fields_json
    )
    tasks = load_tasks(args.tasks)
    role_rows = load_jsonl(args.role_raw)
    source_regimes = args.source_regime or list(ALL_SOURCE_REGIMES)
    message_bank = build_message_bank(
        role_rows,
        task_ids=args.task_id,
        source_regimes=source_regimes,
    )
    selected_task_ids = sorted(
        {bank_case["task_id"] for bank_case in message_bank}
    )
    selected_tasks = [
        task for task in tasks if task["id"] in set(selected_task_ids)
    ]
    conditions = args.condition or list(ALL_CONDITIONS)
    planned_episodes = len(message_bank) * len(conditions) * args.repeats
    args.output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = args.output_dir / "raw" / "episodes.jsonl"
    analysis_dir = args.output_dir / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "status": "development_message_mediation_model_replication",
        "created_at": utc_now(),
        "model_slug": args.model_slug,
        "model_id": args.model_id,
        "region": args.region,
        "temperature": args.temperature,
        "top_p": args.top_p,
        "max_attempts": args.max_attempts,
        "connect_timeout_seconds": args.connect_timeout_seconds,
        "read_timeout_seconds": args.read_timeout_seconds,
        "additional_model_request_fields": additional_fields,
        "task_file": str(args.tasks),
        "task_file_sha256": sha256_file(args.tasks),
        "role_raw": str(args.role_raw),
        "role_raw_sha256": sha256_file(args.role_raw),
        "module_sha256": sha256_file(
            Path("src/swarmsafe_delta/message_mediation_pilot.py")
        ),
        "transport_module_sha256": sha256_file(
            Path("src/swarmsafe_delta/phase1_multimodel.py")
        ),
        "runner_source_sha256": sha256_file(
            Path("scripts/run_message_mediation_bedrock_model.py")
        ),
        "task_ids": selected_task_ids,
        "message_bank": message_bank,
        "conditions": conditions,
        "source_regimes": source_regimes,
        "repeats": args.repeats,
        "workers": args.workers,
        "seed": args.seed,
        "nodes_per_episode": 4,
        "edges_per_episode": 3,
        "executor_deliveries_per_episode": 1,
        "assigned_model_calls_per_episode": 1,
        "planned_episodes": planned_episodes,
        "planned_model_calls": planned_episodes,
        "evidence_boundary": (
            "Outcome-selected development replication using frozen messages; "
            "not confirmatory or submission evidence."
        ),
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "protocol.md").write_text(
        render_protocol(args),
        encoding="utf-8",
    )
    model = CompatibleBedrockTextModel(
        model_id=args.model_id,
        region=args.region,
        temperature=args.temperature,
        top_p=args.top_p,
        max_attempts=args.max_attempts,
        connect_timeout_seconds=args.connect_timeout_seconds,
        read_timeout_seconds=args.read_timeout_seconds,
        additional_model_request_fields=additional_fields,
    )
    rows = run_jobs(
        tasks=selected_tasks,
        message_bank=message_bank,
        conditions=conditions,
        repeats=args.repeats,
        seed=args.seed,
        model=model,
        workers=args.workers,
        raw_path=raw_path,
    )
    validation = validate_rows(
        rows=rows,
        tasks=selected_tasks,
        planned_episodes=planned_episodes,
    )
    summary = analyze_rows(rows, seed=args.seed, validation=validation)
    summary["model_slug"] = args.model_slug
    summary["provider_settings"] = {
        "temperature": args.temperature,
        "top_p": args.top_p,
        "additional_model_request_fields": additional_fields,
    }
    (analysis_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    (analysis_dir / "summary.md").write_text(
        render_summary_markdown(summary),
        encoding="utf-8",
    )
    print(
        canonical_json(
            {
                "status": "complete" if validation["passed"] else "invalid",
                "model_slug": args.model_slug,
                "summary": str(analysis_dir / "summary.json"),
                "validation": validation,
            }
        )
    )
    if not validation["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

