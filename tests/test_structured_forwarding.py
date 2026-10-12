from __future__ import annotations

import json

from swarmsafe_delta.structured_forwarding import (
    FORWARD_TOOL_NAME,
    StructuredForwardBedrockModel,
)


class FakeClient:
    def __init__(self) -> None:
        self.request = None

    def converse(self, **request):
        self.request = request
        return {
            "output": {
                "message": {
                    "content": [
                        {
                            "toolUse": {
                                "name": FORWARD_TOOL_NAME,
                                "input": {
                                    "message": "forwarded",
                                    "keep_A": 1,
                                    "keep_B": 0,
                                    "keep_C": 1,
                                    "keep_scope": 1,
                                    "keep_freshness": 1,
                                    "drop": 0,
                                },
                            }
                        }
                    ]
                }
            },
            "usage": {"inputTokens": 10, "outputTokens": 5},
            "stopReason": "tool_use",
            "ResponseMetadata": {"RequestId": "request-1"},
        }


def test_structured_forwarding_uses_uniform_auto_tool_schema() -> None:
    model = StructuredForwardBedrockModel(
        model_id="fake",
        region="test",
        temperature=0.2,
        top_p=0.9,
        additional_model_request_fields=None,
        force_action_tool=False,
        action_tool_mode="none",
        max_attempts=3,
        connect_timeout_seconds=10,
        read_timeout_seconds=180,
    )
    client = FakeClient()
    model._local.client = client
    response = model.generate(
        system="system",
        user="user",
        max_tokens=512,
        action_ids=(),
    )
    payload = json.loads(response.text)
    assert payload["message"] == "forwarded"
    assert response.stop_reason == "tool_use"
    assert response.attempts == 1
    assert "toolChoice" not in client.request["toolConfig"]
    tool = client.request["toolConfig"]["tools"][0]["toolSpec"]
    assert tool["name"] == FORWARD_TOOL_NAME
    assert set(tool["inputSchema"]["json"]["required"]) == {
        "message",
        "keep_A",
        "keep_B",
        "keep_C",
        "keep_scope",
        "keep_freshness",
        "drop",
    }
