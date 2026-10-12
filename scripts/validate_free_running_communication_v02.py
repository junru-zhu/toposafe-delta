#!/usr/bin/env python3
import sys
from pathlib import Path

from swarmsafe_delta.free_running_communication_v02 import activate


activate()

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts import validate_free_running_communication as implementation


implementation.PACKAGE = (
    ROOT / "experiments/TopoSafe-Delta-FreeRunningCommunication-v0.2"
)


if __name__ == "__main__":
    implementation.main()
