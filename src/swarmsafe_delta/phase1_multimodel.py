from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any, Iterable

import boto3
from botocore.config import Config

from swarmsafe_delta.phase1 import (
    ModelResponse,
    build_config,
    render_protocol,
    run_phase1,
)


MULTIMODEL_EXPERIMENT_VERSION = "phase1-multimodel-v1.0.0"

REPLICATION_MODELS: list[dict[str, Any]] = [
    {
        "slug": "claude-sonnet-5",
        "requested_family": "Anthropic Claude Sonnet 5",
        "model_id": "global.anthropic.claude-sonnet-5",
        "provider_model_version": "global.anthropic.claude-sonnet-5",
        "region": "us-east-1",
        "temperature": None,
        "top_p": None,
        "provider_seed_supported": False,
        "compatibility_note": (
            "Bedrock reports temperature as deprecated for Claude Sonnet 5, "
            "so temperature and topP are omitted."
        ),
    },
    {
        "slug": "llama-4-maverick",
        "requested_family": "Meta Llama 3.3 70B / Llama 4",
        "model_id": "us.meta.llama4-maverick-17b-instruct-v1:0",
        "provider_model_version": (
            "us.meta.llama4-maverick-17b-instruct-v1:0"
        ),
        "region": "us-east-1",
        "temperature": 0.2,
        "top_p": 0.9,
        "provider_seed_supported": False,
        "selection_note": (
            "Llama 4 Maverick was selected as the fixed Llama 4 representative."
        ),
    },
    {
        "slug": "qwen3-next-80b-a3b",
        "requested_family": "Alibaba Qwen3",
        "model_id": "qwen.qwen3-next-80b-a3b",
        "provider_model_version": "qwen.qwen3-next-80b-a3b",
        "region": "us-east-1",
        "temperature": 0.2,
        "top_p": 0.9,
        "provider_seed_supported": False,
        "selection_note": (
            "Qwen3 Next 80B A3B was selected as the fixed Qwen3 representative."
        ),
    },
    {
        "slug": "nemotron-3-super-120b",
        "requested_family": "NVIDIA Nemotron",
        "model_id": "nvidia.nemotron-super-3-120b",
        "provider_model_version": "nvidia.nemotron-super-3-120b",
        "region": "us-east-1",
        "temperature": 0.2,
        "top_p": 0.9,
        "provider_seed_supported": False,
        "selection_note": (
            "Nemotron 3 Super 120B A12B was selected as the fixed Nemotron "
            "representative."
        ),
    },
]

REQUESTED_MODEL_PREFLIGHT: list[dict[str, Any]] = [
    {
        "requested_family": "Anthropic Claude Sonnet 5",
        "model_id": "global.anthropic.claude-sonnet-5",
        "status": "included",
        "preflight_result": "Successful Bedrock Converse response.",
    },
    {
        "requested_family": "OpenAI GPT-5.6 Terra",
        "model_id": "global.openai.gpt-5.6-terra",
        "status": "excluded_pre_freeze",
        "preflight_result": (
            "Catalog-visible and authenticated, but no valid response completed "
            "in three bounded probes: standard Converse, the Bedrock "
            "OpenAI-compatible Responses API, and regional Converse with low "
            "reasoning effort. The latter two exceeded 60 and 90 seconds."
        ),
        "exclusion_reason": (
            "Provider endpoint latency/capacity made the model non-executable "
            "under a bounded Phase 1 call contract. No substitute GPT model was "
            "selected."
        ),
    },
    {
        "requested_family": "Meta Llama 3.3 70B / Llama 4",
        "model_id": "us.meta.llama4-maverick-17b-instruct-v1:0",
        "status": "included",
        "preflight_result": "Successful Bedrock Converse response.",
    },
    {
        "requested_family": "Alibaba Qwen3",
        "model_id": "qwen.qwen3-next-80b-a3b",
        "status": "included",
        "preflight_result": "Successful Bedrock Converse response.",
    },
    {
        "requested_family": "NVIDIA Nemotron",
        "model_id": "nvidia.nemotron-super-3-120b",
        "status": "included",
        "preflight_result": "Successful Bedrock Converse response.",
    },
]


class CompatibleBedrockTextModel:
    """Bedrock Converse client with explicit optional sampling parameters."""

    def __init__(
        self,
        *,
        model_id: str,
        region: str,
        temperature: float | None,
        top_p: float | None,
        max_attempts: int,
        connect_timeout_seconds: int = 10,
        read_timeout_seconds: int = 120,
        additional_model_request_fields: dict[str, Any] | None = None,
    ) -> None:
        self.model_id = model_id
        self.region = region
        self.temperature = temperature
        self.top_p = top_p
        self.max_attempts = max_attempts
        self.connect_timeout_seconds = connect_timeout_seconds
        self.read_timeout_seconds = read_timeout_seconds
        self.additional_model_request_fields = additional_model_request_fields
        self._local = threading.local()

    def _client(self):
        client = getattr(self._local, "client", None)
        if client is None:
            client = boto3.client(
                "bedrock-runtime",
                region_name=self.region,
                config=Config(
                    connect_timeout=self.connect_timeout_seconds,
                    read_timeout=self.read_timeout_seconds,
                    retries={"max_attempts": 0},
                ),
            )
            self._local.client = client
        return client

    def generate(self, *, system: str, user: str, max_tokens: int) -> ModelResponse:
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
                }
                if self.additional_model_request_fields:
                    request["additionalModelRequestFields"] = (
                        self.additional_model_request_fields
                    )
                response = self._client().converse(**request)
                elapsed_ms = (time.perf_counter() - started) * 1000
                content = response["output"]["message"]["content"]
                text = "".join(item.get("text", "") for item in content)
                usage = response.get("usage", {})
                return ModelResponse(
                    text=text,
                    input_tokens=int(usage.get("inputTokens", 0)),
                    output_tokens=int(usage.get("outputTokens", 0)),
                    latency_ms=elapsed_ms,
                    request_id=response.get("ResponseMetadata", {}).get(
                        "RequestId"
                    ),
                    attempts=attempt,
                    attempt_errors=tuple(errors),
                )
            except Exception as exc:  # noqa: BLE001 - preserve provider evidence
                errors.append(f"{type(exc).__name__}: {exc}")
                if attempt < self.max_attempts:
                    time.sleep(0.5 * (2 ** (attempt - 1)))
        raise RuntimeError(
            f"Provider call failed after {self.max_attempts} attempts: "
            + " | ".join(errors)
        )


def build_multimodel_config(
    *,
    task_file: Path,
    task_ids: list[str],
    planner_samples: int,
    root_seed: int,
    status: str,
    source_paths: Iterable[Path] = (),
) -> dict[str, Any]:
    config = build_config(
        task_file=task_file,
        task_ids=task_ids,
        planner_samples=planner_samples,
        root_seed=root_seed,
        status=status,
        source_paths=source_paths,
    )
    config["experiment_version"] = MULTIMODEL_EXPERIMENT_VERSION
    config["models"] = REPLICATION_MODELS
    config["replication_of"] = {
        "experiment_version": "phase1-v1.0.0",
        "config_sha256": (
            "ec27e01bff7282f09d84621f9501ad3ec0abea11e41cedd68b3b611b06f03f90"
        ),
        "preserved_fields": [
            "tasks",
            "conditions",
            "prompts",
            "budgets",
            "deterministic evaluation logic",
            "yoked matching",
            "exclusion rules",
        ],
    }
    config["requested_model_preflight"] = REQUESTED_MODEL_PREFLIGHT
    config["model_selection_rule"] = (
        "Before benchmark outcomes, select one catalog-visible representative "
        "for each requested family. Exclude only models that cannot complete a "
        "bounded authenticated compatibility probe; do not substitute another "
        "model after exclusion."
    )
    config["provider_transport"] = {
        "api": "Amazon Bedrock Converse",
        "connect_timeout_seconds": 10,
        "read_timeout_seconds": 120,
        "sdk_retries": 0,
        "experiment_retry_attempts": config["retry_policy"][
            "max_attempts_per_provider_call"
        ],
    }
    config["seeds"]["provider_limitation"] = (
        "Bedrock Converse does not expose seeded sampling for these models. "
        "Prespecified seeds identify schedules but are not sent to the provider. "
        "Claude Sonnet 5 additionally rejects temperature, so provider-default "
        "sampling is recorded as a model compatibility constraint."
    )
    return config


def render_multimodel_protocol(config: dict[str, Any]) -> str:
    protocol = render_protocol(config)
    protocol = protocol.replace(
        "# SwarmSafe-Delta Phase 1 Protocol",
        "# SwarmSafe-Delta Phase 1 Multi-Model Replication Protocol",
        1,
    )
    protocol = protocol.replace(
        "- Claude Haiku 4.5 omits `topP` because the provider rejects simultaneous\n"
        "  `temperature` and `topP`. This is a provider-compatibility setting, not an\n"
        "  outcome-driven change.\n",
        "- Claude Sonnet 5 omits both `temperature` and `topP` because Bedrock "
        "reports\n"
        "  temperature as deprecated for this model. This compatibility setting "
        "was\n"
        "  fixed before sanity or benchmark outcomes.\n",
    )
    preflight_lines = [
        "",
        "## Requested-model preflight",
        "",
        "| Requested family | Frozen model ID | Status |",
        "| --- | --- | --- |",
    ]
    for row in config["requested_model_preflight"]:
        preflight_lines.append(
            f"| {row['requested_family']} | `{row['model_id']}` | "
            f"{row['status']} |"
        )
    preflight_lines.extend(
        [
            "",
            "GPT-5.6 Terra was excluded before the replication freeze because three "
            "authenticated bounded probes produced no completed response. This is "
            "a technical availability exclusion, not an outcome-based model choice. "
            "The other four requested families remain fixed regardless of sanity "
            "or full-run outcomes.",
            "",
            "## Relationship to the original Phase 1",
            "",
            "This is a separate replication. It does not alter or append rows to "
            "the original `phase1-v1.0.0` dataset. All task, condition, prompt, "
            "budget, reset, deterministic scoring, and matching rules are retained.",
            "",
        ]
    )
    return protocol.rstrip() + "\n" + "\n".join(preflight_lines)


def build_multimodel_clients(
    config: dict[str, Any],
) -> dict[str, CompatibleBedrockTextModel]:
    attempts = int(config["retry_policy"]["max_attempts_per_provider_call"])
    transport = config["provider_transport"]
    return {
        model["slug"]: CompatibleBedrockTextModel(
            model_id=model["model_id"],
            region=model["region"],
            temperature=model["temperature"],
            top_p=model["top_p"],
            max_attempts=attempts,
            connect_timeout_seconds=int(
                transport["connect_timeout_seconds"]
            ),
            read_timeout_seconds=int(transport["read_timeout_seconds"]),
            additional_model_request_fields=model.get(
                "additional_model_request_fields"
            ),
        )
        for model in config["models"]
    }


def run_multimodel_phase1(
    *,
    config_path: Path,
    output_dir: Path,
    planner_workers: int,
    execution_workers: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    import json

    config = json.loads(config_path.read_text(encoding="utf-8"))
    return run_phase1(
        config_path=config_path,
        output_dir=output_dir,
        planner_workers=planner_workers,
        execution_workers=execution_workers,
        models=build_multimodel_clients(config),
    )
