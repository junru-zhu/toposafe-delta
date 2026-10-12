#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import boto3
from botocore.config import Config

from swarmsafe_delta.authority_composition import MODEL_CONFIGS
from swarmsafe_delta.free_running_communication import (
    forwarder_system_prompt,
    forwarder_user_prompt,
)
from swarmsafe_delta.pilot import canonical_json


ROOT = Path(__file__).resolve().parent.parent
CASES = (
    ROOT
    / "experiments/TopoSafe-Delta-FreeRunningCommunication-v0.2/cases.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-slug", choices=tuple(MODEL_CONFIGS), required=True)
    parser.add_argument("--tool-choice", choices=("auto", "forced"), required=True)
    return parser.parse_args()


def tool_config(choice: str) -> dict[str, Any]:
    schema = {
        "type": "object",
        "properties": {
            "message": {"type": "string", "maxLength": 240},
            "keep_A": {"type": "integer", "enum": [0, 1]},
            "keep_B": {"type": "integer", "enum": [0, 1]},
            "keep_C": {"type": "integer", "enum": [0, 1]},
            "keep_scope": {"type": "integer", "enum": [0, 1]},
            "keep_freshness": {"type": "integer", "enum": [0, 1]},
            "drop": {"type": "integer", "enum": [0, 1]},
        },
        "required": [
            "message",
            "keep_A",
            "keep_B",
            "keep_C",
            "keep_scope",
            "keep_freshness",
            "drop",
        ],
        "additionalProperties": False,
    }
    value: dict[str, Any] = {
        "tools": [
            {
                "toolSpec": {
                    "name": "forward_envelope",
                    "description": (
                        "Return the rewritten communication envelope."
                    ),
                    "inputSchema": {"json": schema},
                }
            }
        ]
    }
    if choice == "forced":
        value["toolChoice"] = {"tool": {"name": "forward_envelope"}}
    return value


def main() -> None:
    args = parse_args()
    cases = json.loads(CASES.read_text())
    case = next(
        row
        for row in cases
        if row["task_id"] == "tsc-approval-account-credit"
        and row["topology_id"] == "topo_A"
        and row["authority_regime"] == "verifier_single"
        and row["claim_truth"] == "false_update"
    )
    delivery = next(row for row in case["delivery_schedule"] if row["active_path"])
    config = MODEL_CONFIGS[args.model_slug]
    request: dict[str, Any] = {
        "modelId": config["model_id"],
        "system": [{"text": forwarder_system_prompt()}],
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "text": forwarder_user_prompt(
                            slot=delivery["slot"],
                            edge_nodes=delivery["edge_nodes"],
                            active_path=True,
                            envelope=case["source_envelope"],
                        )
                    }
                ],
            }
        ],
        "inferenceConfig": {"maxTokens": 512},
        "toolConfig": tool_config(args.tool_choice),
    }
    if config["temperature"] is not None:
        request["inferenceConfig"]["temperature"] = config["temperature"]
    if config["top_p"] is not None:
        request["inferenceConfig"]["topP"] = config["top_p"]
    if config["additional_model_request_fields"]:
        request["additionalModelRequestFields"] = config[
            "additional_model_request_fields"
        ]
    client = boto3.client(
        "bedrock-runtime",
        region_name=config["region"],
        config=Config(connect_timeout=10, read_timeout=180, retries={"max_attempts": 0}),
    )
    started = time.perf_counter()
    try:
        response = client.converse(**request)
        content = response["output"]["message"]["content"]
        tool_inputs = [
            item["toolUse"]["input"]
            for item in content
            if item.get("toolUse", {}).get("name") == "forward_envelope"
        ]
        result = {
            "model_slug": args.model_slug,
            "tool_choice": args.tool_choice,
            "success": bool(tool_inputs),
            "stop_reason": response.get("stopReason"),
            "tool_inputs": tool_inputs,
            "text": "".join(item.get("text", "") for item in content),
            "usage": response.get("usage", {}),
            "latency_ms": (time.perf_counter() - started) * 1000,
        }
    except Exception as exc:
        result = {
            "model_slug": args.model_slug,
            "tool_choice": args.tool_choice,
            "success": False,
            "error": f"{type(exc).__name__}: {exc}",
            "latency_ms": (time.perf_counter() - started) * 1000,
        }
    print(canonical_json(result))
    if not result["success"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
