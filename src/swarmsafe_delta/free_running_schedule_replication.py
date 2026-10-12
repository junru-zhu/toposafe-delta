from __future__ import annotations

from swarmsafe_delta import free_running_communication as base


EXPERIMENT_ID = "TopoSafe-Delta-FreeRunningScheduleReplication-v0.1"
PARENT_EXPERIMENT_ID = "TopoSafe-Delta-FreeRunningCommunication-v0.3"
STUDY_ID = "study_b2_free_running_schedule_replication"
RESULT_STATUS = "free_running_schedule_replication_formal"
SCHEDULE_SEED = 2026100671
ANALYSIS_BOOTSTRAP_SEED = 2026100672
FORWARD_MAX_OUTPUT_TOKENS = 512
FORWARD_RESPONSE_MODE = "structured_tool_auto"


def activate() -> None:
    base.EXPERIMENT_ID = EXPERIMENT_ID
    base.STUDY_ID = STUDY_ID
    base.RESULT_STATUS = RESULT_STATUS
    base.FORWARD_MAX_OUTPUT_TOKENS = FORWARD_MAX_OUTPUT_TOKENS
