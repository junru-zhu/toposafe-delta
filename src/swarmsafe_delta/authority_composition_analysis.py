from __future__ import annotations

import random
from collections import defaultdict
from statistics import mean
from typing import Any


def binary_rate(rows: list[dict[str, Any]], field: str) -> float:
    if not rows:
        raise ValueError(f"Cannot compute {field} on an empty row set")
    return mean(float(bool(row[field])) for row in rows)


def bootstrap_mean_interval(
    values_by_task: dict[str, float],
    *,
    seed: int,
    draws: int,
) -> list[float]:
    task_ids = sorted(values_by_task)
    if len(task_ids) < 2:
        raise ValueError("At least two tasks are required for bootstrap")
    rng = random.Random(seed)
    estimates = []
    for _ in range(draws):
        sampled = [rng.choice(task_ids) for _ in task_ids]
        estimates.append(mean(values_by_task[task_id] for task_id in sampled))
    estimates.sort()
    return [
        estimates[int(0.025 * (draws - 1))],
        estimates[int(0.975 * (draws - 1))],
    ]


def authority_cut_contrast(
    rows: list[dict[str, Any]],
    *,
    authority_cut: int,
    seed: int,
    draws: int,
) -> dict[str, Any]:
    by_task_budget: dict[str, dict[int, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for row in rows:
        budget = int(row["compromised_budget"])
        by_task_budget[row["task_id"]][budget].append(
            float(bool(row["protected_action_selected"]))
        )
    expected_budgets = {0, 1, 2}
    incomplete = sorted(
        task_id
        for task_id, budgets in by_task_budget.items()
        if set(budgets) != expected_budgets
    )
    if incomplete:
        raise ValueError(
            "Incomplete authority-cut budgets for tasks: "
            + ", ".join(incomplete)
        )

    task_deltas = {}
    for task_id, budgets in by_task_budget.items():
        below = [
            value
            for budget, values in budgets.items()
            if budget < authority_cut
            for value in values
        ]
        at_or_above = [
            value
            for budget, values in budgets.items()
            if budget >= authority_cut
            for value in values
        ]
        task_deltas[task_id] = mean(at_or_above) - mean(below)

    estimate = mean(task_deltas.values())
    interval = bootstrap_mean_interval(
        task_deltas,
        seed=seed,
        draws=draws,
    )
    return {
        "authority_cut": authority_cut,
        "tasks": len(task_deltas),
        "estimate": estimate,
        "bootstrap_95_ci": interval,
        "bootstrap_draws": draws,
        "bootstrap_seed": seed,
        "positive_estimate": estimate > 0,
        "ci_excludes_zero_positive": interval[0] > 0,
    }


def provider_attempts(row: dict[str, Any]) -> int:
    return int(row.get("api_attempts", 0)) + sum(
        int(item.get("api_attempts", 0))
        for item in row.get("resume_history", [])
    )
