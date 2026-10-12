#!/usr/bin/env python3
import sys
from pathlib import Path

from swarmsafe_delta.free_running_communication_v02 import activate


activate()

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts import analyze_free_running_communication as implementation


implementation.PACKAGE = (
    ROOT / "experiments/TopoSafe-Delta-FreeRunningCommunication-v0.2"
)
original_render_markdown = implementation.render_markdown


def render_markdown(report):
    return original_render_markdown(report).replace(
        "Free-Running Communication v0.1 Results",
        "Free-Running Communication v0.2 Results",
        1,
    )


implementation.render_markdown = render_markdown


if __name__ == "__main__":
    implementation.main()
