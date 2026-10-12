from __future__ import annotations

from swarmsafe_delta import free_running_communication as base


EXPERIMENT_ID = "TopoSafe-Delta-FreeRunningCommunication-v0.2"
FORWARD_MAX_OUTPUT_TOKENS = 512


def activate() -> None:
    """Apply the v0.2 constants before importing the v0.1 generic runners."""
    base.EXPERIMENT_ID = EXPERIMENT_ID
    base.FORWARD_MAX_OUTPUT_TOKENS = FORWARD_MAX_OUTPUT_TOKENS
