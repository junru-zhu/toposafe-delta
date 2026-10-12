#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

from swarmsafe_delta.free_running_communication_v02 import (
    EXPERIMENT_ID,
    FORWARD_MAX_OUTPUT_TOKENS,
    activate,
)
from swarmsafe_delta.pilot import canonical_json, sha256_file


activate()

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts import freeze_free_running_communication as implementation


PACKAGE = ROOT / "experiments/TopoSafe-Delta-FreeRunningCommunication-v0.2"
PREDECESSOR = (
    ROOT / "experiments/TopoSafe-Delta-FreeRunningCommunication-v0.1"
)
implementation.PACKAGE = PACKAGE
implementation.EXPERIMENT_ID = EXPERIMENT_ID
implementation.FORWARD_MAX_OUTPUT_TOKENS = FORWARD_MAX_OUTPUT_TOKENS

WRAPPER_SOURCES = (
    ROOT / "src/swarmsafe_delta/free_running_communication_v02.py",
    ROOT / "scripts/build_free_running_communication_v02.py",
    ROOT / "scripts/freeze_free_running_communication_v02.py",
    ROOT / "scripts/run_free_running_communication_v02.py",
    ROOT / "scripts/validate_free_running_communication_v02.py",
    ROOT / "scripts/analyze_free_running_communication_v02.py",
)


def main() -> None:
    predecessor_validation = PREDECESSOR / "smoke/validation_report.json"
    if not predecessor_validation.exists():
        raise RuntimeError("Missing v0.1 smoke validation evidence")
    smoke = json.loads(predecessor_validation.read_text())
    if smoke.get("invalid_models") != ["llama-4-maverick"]:
        raise RuntimeError("v0.1 smoke failure does not match correction record")
    implementation.main()
    if "--check-only" in sys.argv:
        return
    manifest_path = PACKAGE / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["predecessor_experiment_id"] = (
        "TopoSafe-Delta-FreeRunningCommunication-v0.1"
    )
    manifest["predecessor_smoke_validation_sha256"] = sha256_file(
        predecessor_validation
    )
    manifest["correction_reason"] = (
        "The v0.1 Llama smoke produced two max-token forwarding truncations "
        "at 180 tokens; two excluded diagnostics completed at 512 tokens."
    )
    manifest["model_output_token_budget_per_episode"] = (
        6 * FORWARD_MAX_OUTPUT_TOKENS
        + manifest["executor_max_output_tokens"]
    )
    manifest["source_hashes"].update(
        {
            str(path.relative_to(ROOT)): sha256_file(path)
            for path in WRAPPER_SOURCES
        }
    )
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    print(
        canonical_json(
            {
                "status": manifest["status"],
                "manifest_sha256": sha256_file(manifest_path),
                "forward_max_output_tokens": FORWARD_MAX_OUTPUT_TOKENS,
                "model_output_token_budget_per_episode": manifest[
                    "model_output_token_budget_per_episode"
                ],
                "source_hashes": len(manifest["source_hashes"]),
            }
        )
    )


if __name__ == "__main__":
    main()
