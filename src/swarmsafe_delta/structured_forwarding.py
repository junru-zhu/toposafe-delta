from __future__ import annotations

import time
from typing import Any

from swarmsafe_delta.authority_placement import (
    AuthorityBedrockTextModel,
    AuthorityModelResponse,
    AuthorityProviderError,
)
from swarmsafe_delta.pilot import canonical_json


FORWARD_TOOL_NAME = "forward_envelope"
FORWARD_TOOL_SCHEMA = {
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


class StructuredForwardBedrockModel(AuthorityBedrockTextModel):
    """Bedrock Converse model with one uniform auto-selected envelope tool."""

    def generate(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int,
        action_ids: tuple[str, ...],
    ) -> AuthorityModelResponse:
        del action_ids
        errors: list[str] = []
        for attempt in range(1, self.max_attempts + 1):
            started = time.perf_counter()
            try:
                inference_config: dict[str, Any] = {"maxTokens": max_tokens}
                if self.temperature is not None:
                    inference_config["temperature"] = self.temperature
                if self.top_p is not None:
                    inference_config["topP"] = self.top_p
                request: dict[str, Any] = {
                    "modelId": self.model_id,
                    "system": [{"text": system}],
                    "messages": [
                        {"role": "user", "content": [{"text": user}]}
                    ],
                    "inferenceConfig": inference_config,
                    "toolConfig": {
                        "tools": [
                            {
                                "toolSpec": {
                                    "name": FORWARD_TOOL_NAME,
                                    "description": (
                                        "Return the rewritten communication "
                                        "envelope."
                                    ),
                                    "inputSchema": {
                                        "json": FORWARD_TOOL_SCHEMA
                                    },
                                }
                            }
                        ]
                    },
                }
                if self.additional_model_request_fields:
                    request["additionalModelRequestFields"] = (
                        self.additional_model_request_fields
                    )
                response = self._client().converse(**request)
                elapsed_ms = (time.perf_counter() - started) * 1000
                content = response["output"]["message"]["content"]
                text = "".join(item.get("text", "") for item in content)
                tool_inputs = [
                    item["toolUse"]["input"]
                    for item in content
                    if item.get("toolUse", {}).get("name")
                    == FORWARD_TOOL_NAME
                ]
                if tool_inputs:
                    text = canonical_json(tool_inputs[0])
                usage = response.get("usage", {})
                return AuthorityModelResponse(
                    text=text,
                    input_tokens=int(usage.get("inputTokens", 0)),
                    output_tokens=int(usage.get("outputTokens", 0)),
                    latency_ms=elapsed_ms,
                    request_id=response.get("ResponseMetadata", {}).get(
                        "RequestId"
                    ),
                    attempts=attempt,
                    attempt_errors=tuple(errors),
                    stop_reason=response.get("stopReason"),
                )
            except Exception as exc:
                errors.append(f"{type(exc).__name__}: {exc}")
                if attempt < self.max_attempts:
                    time.sleep(0.5 * (2 ** (attempt - 1)))
        raise AuthorityProviderError(errors)
