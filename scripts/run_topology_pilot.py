#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from swarmsafe_delta.pilot import (
    BedrockTextModel,
    canonical_json,
    load_tasks,
    sha256_file,
    utc_now,
)
from swarmsafe_delta.topology_pilot import (
    ALL_SOURCE_REGIMES,
    ALL_TOPOLOGIES,
    analyze_rows,
    load_jsonl,
    render_protocol,
    render_summary_markdown,
    run_jobs,
    select_source_cases,
    validate_rows,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the TopoSafe-Delta development topology pilot."
    )
    parser.add_argument(
        "--tasks",
        type=Path,
        default=Path("data/calibration_boundary_tasks_v0.2.json"),
    )
    parser.add_argument(
        "--source-raw",
        type=Path,
        default=Path(
            "experiments/pilot-v0.2/models/nova-2-lite/raw/episodes.jsonl"
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("experiments/TopoSafe-Delta-TopologyPilot-v1"),
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
    parser.add_argument("--seed", type=int, default=2026100501)
    parser.add_argument("--task-id", action="append", default=[])
    parser.add_argument(
        "--topology",
        action="append",
        choices=ALL_TOPOLOGIES,
        default=[],
    )
    parser.add_argument(
        "--source-regime",
        action="append",
        choices=ALL_SOURCE_REGIMES,
        default=[],
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tasks = load_tasks(args.tasks)
    source_rows = load_jsonl(args.source_raw)
    source_cases = select_source_cases(
        tasks=tasks,
        source_rows=source_rows,
        task_ids=args.task_id,
    )
    selected_task_ids = [case["task_id"] for case in source_cases]
    selected_tasks = [
        task for task in tasks if task["id"] in set(selected_task_ids)
    ]
    topologies = args.topology or list(ALL_TOPOLOGIES)
    source_regimes = args.source_regime or list(ALL_SOURCE_REGIMES)
    planned_episodes = (
        len(source_cases)
        * len(topologies)
        * len(source_regimes)
        * args.repeats
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = args.output_dir / "raw" / "episodes.jsonl"
    analysis_dir = args.output_dir / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "status": "development_topology_pilot_only",
        "created_at": utc_now(),
        "task_file": str(args.tasks),
        "task_file_sha256": sha256_file(args.tasks),
        "source_raw": str(args.source_raw),
        "source_raw_sha256": sha256_file(args.source_raw),
        "topology_module_sha256": sha256_file(
            Path("src/swarmsafe_delta/topology_pilot.py")
        ),
        "runner_source_sha256": sha256_file(
            Path("scripts/run_topology_pilot.py")
        ),
        "task_ids": selected_task_ids,
        "source_cases": source_cases,
        "topologies": topologies,
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
        "delivered_message_slots_per_episode": 3,
        "assigned_model_calls_per_episode": 3,
        "planned_episodes": planned_episodes,
        "planned_model_calls": planned_episodes * 3,
        "evidence_boundary": (
            "Outcome-selected development topology pilot; not confirmatory or "
            "submission evidence."
        ),
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "protocol.md").write_text(
        render_protocol(
            task_ids=selected_task_ids,
            topologies=topologies,
            source_regimes=source_regimes,
            repeats=args.repeats,
            model_id=args.model_id,
        ),
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
        source_cases=source_cases,
        topologies=topologies,
        source_regimes=source_regimes,
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
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
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
