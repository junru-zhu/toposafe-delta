#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from swarmsafe_delta.message_mediation_pilot import (
    ALL_CONDITIONS,
    analyze_rows,
    build_message_bank,
    render_summary_markdown,
    run_jobs,
    validate_rows,
)
from swarmsafe_delta.pilot import (
    BedrockTextModel,
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
        description="Run the TopoSafe-Delta message-mediation pilot."
    )
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
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "experiments/TopoSafe-Delta-MessageMediationPilot-v1"
        ),
    )
    parser.add_argument(
        "--model-id",
        default="global.amazon.nova-2-lite-v1:0",
    )
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--omit-top-p", action="store_true")
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--seed", type=int, default=2026100503)
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


def render_protocol() -> str:
    return """# TopoSafe-Delta Message-Mediation Pilot Protocol

**Status:** Development trajectory-fork diagnostic.

The executor is the only model call and the only node allowed to alter external
state. Every condition uses one delivered recommendation, the same tool
permissions, and the same action budget.

## Conditions

1. `direct_original`: original message with the exact executor prompt format
   used by the preceding role-placement pilot.
2. `hidden_relay_identical`: a logged one-hop route, but the executor receives
   the exact same prompt as `direct_original`.
3. `relay_verbatim`: original text with visible relay provenance.
4. `source_paraphrase`: frozen action-preserving paraphrase in the original
   executor prompt format.
5. `relay_paraphrase`: the same paraphrase with relay provenance.
6. `verifier_rewrite`: frozen policy-verifier message with verifier provenance.

The direct-versus-hidden-relay pair is a negative control for a graph path that
is not visible in executor context. The remaining conditions test provenance,
wording, and policy transformation.
"""


def main() -> None:
    args = parse_args()
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
        "status": "development_message_mediation_pilot_only",
        "created_at": utc_now(),
        "task_file": str(args.tasks),
        "task_file_sha256": sha256_file(args.tasks),
        "role_raw": str(args.role_raw),
        "role_raw_sha256": sha256_file(args.role_raw),
        "module_sha256": sha256_file(
            Path("src/swarmsafe_delta/message_mediation_pilot.py")
        ),
        "runner_source_sha256": sha256_file(
            Path("scripts/run_message_mediation_pilot.py")
        ),
        "task_ids": selected_task_ids,
        "message_bank": message_bank,
        "conditions": conditions,
        "source_regimes": source_regimes,
        "model_id": args.model_id,
        "region": args.region,
        "temperature": args.temperature,
        "top_p": None if args.omit_top_p else 0.9,
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
            "Outcome-selected development trajectory-fork pilot using frozen "
            "messages from the prior role-placement run; not confirmatory or "
            "submission evidence."
        ),
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "protocol.md").write_text(
        render_protocol(),
        encoding="utf-8",
    )
    model = BedrockTextModel(
        model_id=args.model_id,
        region=args.region,
        temperature=args.temperature,
        top_p=None if args.omit_top_p else 0.9,
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
                "summary": str(analysis_dir / "summary.json"),
                "validation": validation,
            }
        )
    )
    if not validation["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
