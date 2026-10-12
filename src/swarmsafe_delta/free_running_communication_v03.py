from __future__ import annotations

from swarmsafe_delta import free_running_communication as base


EXPERIMENT_ID = "TopoSafe-Delta-FreeRunningCommunication-v0.3"
FORWARD_MAX_OUTPUT_TOKENS = 512
FORWARD_RESPONSE_MODE = "structured_tool_auto"


def activate() -> None:
    base.EXPERIMENT_ID = EXPERIMENT_ID
    base.FORWARD_MAX_OUTPUT_TOKENS = FORWARD_MAX_OUTPUT_TOKENS
