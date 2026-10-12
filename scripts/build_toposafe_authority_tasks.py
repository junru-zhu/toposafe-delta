#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from swarmsafe_delta.authority_task_construction import build_task_package


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CATALOG = ROOT / "data/toposafe_authority_task_catalog_v0.1.json"
DEFAULT_DEVELOPMENT_TASKS = ROOT / "data/authority_placement_tasks_v1.json"
DEFAULT_OUTPUT = (
    ROOT / "experiments/TopoSafe-Delta-AuthorityComposition-v0.2"
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument(
        "--development-tasks",
        type=Path,
        default=DEFAULT_DEVELOPMENT_TASKS,
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = build_task_package(
        catalog_path=args.catalog.resolve(),
        development_tasks_path=args.development_tasks.resolve(),
        output_dir=args.output_dir.resolve(),
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    if not result["automatic_gate_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
