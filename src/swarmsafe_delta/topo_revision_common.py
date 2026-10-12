from __future__ import annotations

import hashlib
import json
import math
import os
import random
import statistics
import threading
from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from swarmsafe_delta.authority_composition import MODEL_CONFIGS
from swarmsafe_delta.execution_topology_pilot import MODEL_PRICES


REVISION_ROOT = Path("experiments/topo_revision")
MODEL_SLUGS = tuple(MODEL_CONFIGS)
DEFAULT_SEED = 20271012
BOOTSTRAP_DRAWS = 5_000
SIGN_FLIP_DRAWS = 10_000
MAX_OUTPUT_TOKENS = 120
FORWARD_MAX_OUTPUT_TOKENS = 256
MAX_ATTEMPTS = 2


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: {exc}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: row is not an object")
            rows.append(value)
    return rows


def write_jsonl_atomic(
    path: Path,
    rows_by_id: dict[str, dict[str, Any]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        for episode_id in sorted(rows_by_id):
            handle.write(canonical_json(rows_by_id[episode_id]) + "\n")
    os.replace(temporary, path)


def action_prompt(task: dict[str, Any]) -> str:
    return "\n".join(
        f"- {action['id']}: {action['description']}"
        for action in task["actions"]
    )


def normalize_action(
    task: dict[str, Any],
    action_id: Any,
) -> str:
    candidate = str(action_id or "").strip()
    valid = {action["id"] for action in task["actions"]}
    return candidate if candidate in valid else "malformed"


def extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    try:
        value = json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start < 0 or end <= start:
            raise
        value = json.loads(stripped[start : end + 1])
    if not isinstance(value, dict):
        raise ValueError("response JSON is not an object")
    return value


def model_cost(
    model_slug: str,
    input_tokens: int,
    output_tokens: int,
    *,
    conservative: bool = False,
) -> float:
    prefix = "conservative_" if conservative else ""
    price = MODEL_PRICES[model_slug]
    return (
        input_tokens * price[f"{prefix}input_per_million_usd"]
        + output_tokens * price[f"{prefix}output_per_million_usd"]
    ) / 1_000_000


def row_cost(
    row: dict[str, Any],
    *,
    conservative: bool = False,
) -> float:
    return model_cost(
        str(row["model_slug"]),
        int(row.get("input_tokens") or 0),
        int(row.get("output_tokens") or 0),
        conservative=conservative,
    )


def history_call_count(row: dict[str, Any]) -> int:
    return int(row.get("realized_model_calls") or 0) + sum(
        int(item.get("realized_model_calls") or 0)
        for item in row.get("resume_history", [])
    )


def history_assigned_call_count(row: dict[str, Any]) -> int:
    return int(row.get("assigned_model_calls") or 0) + sum(
        int(item.get("assigned_model_calls") or 0)
        for item in row.get("resume_history", [])
    )


def history_cost(
    row: dict[str, Any],
    *,
    conservative: bool = False,
) -> float:
    total = row_cost(row, conservative=conservative)
    for item in row.get("resume_history", []):
        if "model_slug" not in item:
            item = {**item, "model_slug": row["model_slug"]}
        total += row_cost(item, conservative=conservative)
    return total


def all_revision_raw_paths(root: Path = REVISION_ROOT) -> list[Path]:
    return sorted(root.glob("runs/*/*/*/raw/episodes.jsonl"))


def budget_ledger(root: Path = REVISION_ROOT) -> dict[str, Any]:
    rows = [
        row
        for path in all_revision_raw_paths(root)
        for row in load_jsonl(path)
    ]
    return {
        "rows": len(rows),
        "assigned_model_calls": sum(
            history_assigned_call_count(row) for row in rows
        ),
        "realized_model_calls_including_resume_history": sum(
            history_call_count(row) for row in rows
        ),
        "api_attempts_including_resume_history": sum(
            int(row.get("api_attempts") or 0)
            + sum(
                int(item.get("api_attempts") or 0)
                for item in row.get("resume_history", [])
            )
            for row in rows
        ),
        "estimated_cost_usd": sum(history_cost(row) for row in rows),
        "conservative_cost_usd": sum(
            history_cost(row, conservative=True) for row in rows
        ),
        "generated_at": utc_now(),
    }


def enforce_budget(
    *,
    additional_assigned_calls: int,
    max_calls: int,
    max_spend_usd: float,
    projected_input_tokens: int = 1_800,
    projected_output_tokens: int = 120,
    model_call_counts: dict[str, int] | None = None,
    root: Path = REVISION_ROOT,
) -> dict[str, Any]:
    ledger = budget_ledger(root)
    projected_cost = 0.0
    if model_call_counts:
        for model_slug, calls in model_call_counts.items():
            projected_cost += model_cost(
                model_slug,
                calls * projected_input_tokens,
                calls * projected_output_tokens,
                conservative=True,
            )
    if ledger["assigned_model_calls"] + additional_assigned_calls > max_calls:
        raise RuntimeError(
            "MAX_NEW_LLM_CALLS would be exceeded: "
            f"existing={ledger['assigned_model_calls']}, "
            f"additional={additional_assigned_calls}, cap={max_calls}"
        )
    if ledger["conservative_cost_usd"] + projected_cost > max_spend_usd:
        raise RuntimeError(
            "MAX_SPEND_USD would be exceeded under the conservative token "
            f"allowance: spent={ledger['conservative_cost_usd']:.4f}, "
            f"projected={projected_cost:.4f}, cap={max_spend_usd:.2f}"
        )
    return {
        **ledger,
        "prospective_assigned_calls": additional_assigned_calls,
        "prospective_conservative_cost_usd": projected_cost,
        "max_calls": max_calls,
        "max_spend_usd": max_spend_usd,
    }


def mean(values: Iterable[float]) -> float:
    materialized = list(values)
    return statistics.fmean(materialized) if materialized else 0.0


def paired_task_values(
    rows: Iterable[dict[str, Any]],
    *,
    reference: str,
    treated: str,
    condition_field: str,
    outcome_field: str,
) -> list[tuple[str, float]]:
    grouped: dict[str, dict[str, float]] = {}
    for row in rows:
        condition = str(row[condition_field])
        if condition not in {reference, treated}:
            continue
        grouped.setdefault(str(row["task_id"]), {})[condition] = float(
            bool(row[outcome_field])
        )
    return sorted(
        (
            task_id,
            values[treated] - values[reference],
        )
        for task_id, values in grouped.items()
        if reference in values and treated in values
    )


def bootstrap_mean_interval(
    values: list[float],
    *,
    draws: int = BOOTSTRAP_DRAWS,
    seed: int = DEFAULT_SEED,
) -> tuple[float, float]:
    if not values:
        return (0.0, 0.0)
    if len(set(values)) == 1:
        return (values[0], values[0])
    rng = random.Random(seed)
    samples = sorted(
        mean(rng.choice(values) for _ in values)
        for _ in range(draws)
    )
    lower_index = max(0, math.floor(0.025 * draws))
    upper_index = min(draws - 1, math.ceil(0.975 * draws) - 1)
    return samples[lower_index], samples[upper_index]


def sign_flip_pvalue(
    values: list[float],
    *,
    draws: int = SIGN_FLIP_DRAWS,
    seed: int = DEFAULT_SEED,
) -> float:
    if not values:
        return 1.0
    observed = abs(mean(values))
    if observed == 0:
        return 1.0
    rng = random.Random(seed)
    extreme = 1
    for _ in range(draws):
        statistic = abs(
            mean(value if rng.random() < 0.5 else -value for value in values)
        )
        extreme += int(statistic >= observed - 1e-12)
    return extreme / (draws + 1)


def effect_summary(
    paired: list[tuple[str, float]],
    *,
    seed: int,
) -> dict[str, Any]:
    values = [value for _, value in paired]
    lower, upper = bootstrap_mean_interval(values, seed=seed)
    return {
        "task_clusters": len(values),
        "estimate": mean(values),
        "ci95": [lower, upper],
        "p_value": sign_flip_pvalue(values, seed=seed + 1),
    }


def holm_adjust(rows: list[dict[str, Any]]) -> None:
    ordered = sorted(
        enumerate(rows),
        key=lambda item: float(item[1]["p_value"]),
    )
    running = 0.0
    total = len(ordered)
    adjusted: dict[int, float] = {}
    for rank, (original_index, row) in enumerate(ordered):
        candidate = min(
            1.0,
            (total - rank) * float(row["p_value"]),
        )
        running = max(running, candidate)
        adjusted[original_index] = running
    for index, row in enumerate(rows):
        row["holm_adjusted_p"] = adjusted.get(index, 1.0)


def grouped_rate(
    rows: Iterable[dict[str, Any]],
    *,
    keys: tuple[str, ...],
    outcome: str,
) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in rows:
        key = tuple(row[field] for field in keys)
        groups.setdefault(key, []).append(row)
    result = []
    for key, group in sorted(groups.items()):
        values = [float(bool(row.get(outcome))) for row in group]
        result.append(
            {
                **dict(zip(keys, key, strict=True)),
                "outcome": outcome,
                "n": len(group),
                "rate": mean(values),
            }
        )
    return result


class AtomicRowStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.lock = threading.Lock()
        self.rows = {
            str(row["episode_id"]): row for row in load_jsonl(path)
        }

    def successful_ids(self) -> set[str]:
        return {
            episode_id
            for episode_id, row in self.rows.items()
            if not row.get("provider_error")
        }

    def put(self, row: dict[str, Any], *, persist: bool = True) -> None:
        episode_id = str(row["episode_id"])
        with self.lock:
            previous = self.rows.get(episode_id)
            if previous and previous.get("provider_error"):
                history = list(previous.get("resume_history", []))
                history.append(
                    {
                        key: previous.get(key)
                        for key in (
                            "provider_error",
                            "assigned_model_calls",
                            "realized_model_calls",
                            "api_attempts",
                            "input_tokens",
                            "output_tokens",
                            "model_slug",
                            "started_at",
                            "finished_at",
                        )
                    }
                )
                row["resume_history"] = history
            self.rows[episode_id] = row
            if persist:
                write_jsonl_atomic(self.path, self.rows)

    def flush(self) -> None:
        with self.lock:
            write_jsonl_atomic(self.path, self.rows)


def deterministic_shuffle(
    values: list[Any],
    *,
    seed: int,
    key: Callable[[Any], str] | None = None,
) -> list[Any]:
    ordered = sorted(values, key=key) if key else list(values)
    random.Random(seed).shuffle(ordered)
    return ordered
