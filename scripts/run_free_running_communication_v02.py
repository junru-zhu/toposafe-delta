#!/usr/bin/env python3
import sys
from pathlib import Path

from swarmsafe_delta.free_running_communication_v02 import (
    EXPERIMENT_ID,
    FORWARD_MAX_OUTPUT_TOKENS,
    activate,
)


activate()

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts import run_free_running_communication as implementation


implementation.PACKAGE = (
    ROOT / "experiments/TopoSafe-Delta-FreeRunningCommunication-v0.2"
)
implementation.EXPERIMENT_ID = EXPERIMENT_ID
implementation.FORWARD_MAX_OUTPUT_TOKENS = FORWARD_MAX_OUTPUT_TOKENS


if __name__ == "__main__":
    implementation.main()
