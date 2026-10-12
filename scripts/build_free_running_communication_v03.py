#!/usr/bin/env python3
import sys
from pathlib import Path

from swarmsafe_delta.free_running_communication_v03 import (
    EXPERIMENT_ID,
    activate,
)


activate()

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts import build_free_running_communication as implementation


implementation.PACKAGE = (
    ROOT / "experiments/TopoSafe-Delta-FreeRunningCommunication-v0.3"
)
implementation.EXPERIMENT_ID = EXPERIMENT_ID


if __name__ == "__main__":
    implementation.main()
