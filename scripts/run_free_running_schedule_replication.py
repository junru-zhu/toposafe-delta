#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from swarmsafe_delta.authority_composition import MODEL_CONFIGS
from swarmsafe_delta.free_running_schedule_replication import (
    EXPERIMENT_ID,
    FORWARD_MAX_OUTPUT_TOKENS,
    FORWARD_RESPONSE_MODE,
    PARENT_EXPERIMENT_ID,
    SCHEDULE_SEED,
    activate,
)
from swarmsafe_delta.pilot import canonical_json, sha256_file
from swarmsafe_delta.structured_forwarding import StructuredForwardBedrockModel


activate()

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts import run_free_running_communication as implementation  # noqa: E402


PACKAGE = (
    ROOT / "experiments/TopoSafe-Delta-FreeRunningScheduleReplication-v0.1"
)
PARENT = ROOT / "experiments/TopoSafe-Delta-FreeRunningCommunication-v0.3"
implementation.PACKAGE = PACKAGE
implementation.EXPERIMENT_ID = EXPERIMENT_ID
implementation.FORWARD_MAX_OUTPUT_TOKENS = FORWARD_MAX_OUTPUT_TOKENS
text_model = implementation.model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("smoke", "formal"), required=True)
    parser.add_argument(
        "--model-slug", choices=tuple(MODEL_CONFIGS), required=True
    )
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--seed", type=int, default=SCHEDULE_SEED)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--connect-timeout-seconds", type=int, default=10)
    parser.add_argument("--read-timeout-seconds", type=int, default=180)
    return parser.parse_args()


implementation.parse_args = parse_args


def model(
    config,
    *,
    forward,
    max_attempts,
    connect_timeout_seconds,
    read_timeout_seconds,
):
    if not forward:
        return text_model(
            config,
            forward=False,
            max_attempts=max_attempts,
            connect_timeout_seconds=connect_timeout_seconds,
            read_timeout_seconds=read_timeout_seconds,
        )
    return StructuredForwardBedrockModel(
        model_id=str(config["model_id"]),
        region=str(config["region"]),
        temperature=config["temperature"],
        top_p=config["top_p"],
        additional_model_request_fields=config[
            "additional_model_request_fields"
        ],
        force_action_tool=False,
        action_tool_mode="none",
        max_attempts=max_attempts,
        connect_timeout_seconds=connect_timeout_seconds,
        read_timeout_seconds=read_timeout_seconds,
    )


implementation.model = model


def main() -> None:
    args = parse_args()
    implementation.main()
    stage_root = PACKAGE / ("smoke" if args.stage == "smoke" else "models")
    model_dir = stage_root / args.model_slug
    manifest_path = model_dir / "manifest.json"
    model_manifest = json.loads(manifest_path.read_text())
    model_manifest.update(
        {
            "forward_response_mode": FORWARD_RESPONSE_MODE,
            "wrapper_runner_sha256": sha256_file(Path(__file__)),
            "parent_experiment_id": PARENT_EXPERIMENT_ID,
            "changed_factor": "schedule_seed_and_resulting_execution_order",
        }
    )
    manifest_path.write_text(
        json.dumps(
            model_manifest, ensure_ascii=False, indent=2, sort_keys=True
        )
        + "\n",
        encoding="utf-8",
    )

    validation_path = model_dir / "analysis/validation.json"
    validation = json.loads(validation_path.read_text())
    parent_validation = json.loads(
        (PARENT / "models/validation_report.json").read_text()
    )
    parent_gate = bool(
        parent_validation["models"][args.model_slug]["passed"]
    )
    validation["parent_b2_model_gate_passed"] = parent_gate
    validation["passed"] = bool(validation["passed"] and parent_gate)
    validation_path.write_text(
        json.dumps(validation, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    print(
        canonical_json(
            {
                "stage": args.stage,
                "model_slug": args.model_slug,
                "parent_b2_model_gate_passed": parent_gate,
                "schedule_replication_validation_passed": validation[
                    "passed"
                ],
            }
        )
    )
    if not validation["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
