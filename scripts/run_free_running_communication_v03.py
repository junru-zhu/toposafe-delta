#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

from swarmsafe_delta.free_running_communication_v03 import (
    EXPERIMENT_ID,
    FORWARD_MAX_OUTPUT_TOKENS,
    FORWARD_RESPONSE_MODE,
    activate,
)
from swarmsafe_delta.pilot import sha256_file
from swarmsafe_delta.structured_forwarding import StructuredForwardBedrockModel


activate()

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts import run_free_running_communication as implementation


PACKAGE = ROOT / "experiments/TopoSafe-Delta-FreeRunningCommunication-v0.3"
implementation.PACKAGE = PACKAGE
implementation.EXPERIMENT_ID = EXPERIMENT_ID
implementation.FORWARD_MAX_OUTPUT_TOKENS = FORWARD_MAX_OUTPUT_TOKENS
text_model = implementation.model


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


def argument(name: str) -> str:
    index = sys.argv.index(name)
    return sys.argv[index + 1]


def main() -> None:
    implementation.main()
    stage = argument("--stage")
    slug = argument("--model-slug")
    stage_root = PACKAGE / ("smoke" if stage == "smoke" else "models")
    manifest_path = stage_root / slug / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["forward_response_mode"] = FORWARD_RESPONSE_MODE
    manifest["wrapper_runner_sha256"] = sha256_file(Path(__file__))
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
