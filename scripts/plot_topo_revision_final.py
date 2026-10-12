#!/usr/bin/env python3
from __future__ import annotations

import json

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from scripts import plot_topo_revision as plots


def load(path: str):
    return json.loads((plots.PACKAGE / path).read_text(encoding="utf-8"))


def final_pareto(result) -> None:
    rows = [
        row
        for row in result["outcomes"]
        if row["model_slug"] == "llama-4-maverick"
    ]
    points = []
    for policy in ("A1", "A2", "A3"):
        cut = {"A1": 1, "A2": 2, "A3": 2}[policy]
        false_row = next(
            row
            for row in rows
            if row["policy_id"] == policy
            and row["world_state"] == "FALSE"
            and row["compromised_budget"] == cut
        )
        true_row = next(
            row
            for row in rows
            if row["policy_id"] == policy
            and row["world_state"] == "TRUE"
            and row["compromised_budget"] == cut - 1
        )
        points.append(
            (
                true_row["committed_protected"]["rate"],
                1 - false_row["committed_protected"]["rate"],
            )
        )
    fig, axis = plt.subplots(figsize=(5.4, 3.6))
    utility, safety = points[0]
    axis.scatter(
        utility,
        safety,
        color=plots.COLORS["llama-4-maverick"],
        marker="D",
        s=70,
        edgecolor="#222222",
        linewidth=0.5,
        zorder=3,
    )
    axis.annotate(
        "A1 = A2 = A3",
        (utility, safety),
        xytext=(-8, 12),
        textcoords="offset points",
        ha="right",
        fontsize=8,
    )
    axis.text(
        0.03,
        0.94,
        "All policies: 100% true-state completion,\n"
        "0% safety after the authority cut is crossed.",
        transform=axis.transAxes,
        va="top",
        fontsize=8,
        color="#444444",
    )
    axis.set(
        xlabel="True-state committed task completion",
        ylabel="Safety: 1 − false-state committed action",
        xlim=(-0.03, 1.03),
        ylim=(-0.03, 1.03),
        title="Safety–utility frontier (Llama formal block)",
    )
    axis.grid(color="#D9D9D9", linewidth=0.6)
    plots.save(fig, "safety_utility_pareto")


def final_workflow_heatmap(result) -> None:
    rows = [
        row
        for row in result["outcomes"]
        if row["model_slug"] == "nemotron-3-super-120b"
        and row["world_state"] == "FALSE"
    ]
    row_keys = [
        (auth, execution)
        for auth in ("A1", "A2")
        for execution in ("E0", "E1")
    ]
    matrix = np.zeros((4, 3))
    for row_index, (auth, execution) in enumerate(row_keys):
        for column, topology in enumerate(("C1", "C2", "C3")):
            match = next(
                row
                for row in rows
                if row["authorization_policy"] == auth
                and row["execution_policy"] == execution
                and row["topology"] == topology
            )
            matrix[row_index, column] = match["false_commit_rate"]
    fig, axis = plt.subplots(figsize=(5.15, 3.2))
    image = axis.imshow(
        matrix,
        cmap="magma_r",
        vmin=0,
        vmax=1,
        aspect="auto",
    )
    axis.set_xticks(range(3), ["Direct", "Chain", "Redundant"])
    axis.set_yticks(
        range(4),
        ["A1 / E0", "A1 / E1", "A2 / E0", "A2 / E1"],
    )
    axis.set_title(
        "End-to-end false-state commits\n"
        "(Nemotron clean pilot block, n=3 tasks/cell)"
    )
    for row_index in range(4):
        for column in range(3):
            value = matrix[row_index, column]
            axis.text(
                column,
                row_index,
                f"{100 * value:.0f}%",
                ha="center",
                va="center",
                color="white" if value >= 0.25 else "#222222",
                fontsize=8,
            )
    colorbar = fig.colorbar(image, ax=axis, fraction=0.045, pad=0.03)
    colorbar.set_label("False-state committed action rate")
    plots.save(fig, "end_to_end_safety_heatmap")


def final_trust_boundary() -> None:
    fig, axis = plt.subplots(figsize=(7.05, 2.35))
    axis.set_xlim(0, 10)
    axis.set_ylim(0, 3)
    axis.axis("off")
    layers = (
        (
            0.25,
            "#E6F2FA",
            "#0072B2",
            "Communication $G_C$",
            "Who receives or rewrites\n"
            "the operational claim",
        ),
        (
            3.6,
            "#E8F5EF",
            "#009E73",
            "Authorization $G_A$",
            "Which independent credentials\n"
            "form an action-bound proof",
        ),
        (
            6.95,
            "#FCEEE8",
            "#D55E00",
            "Execution $G_E$",
            "Which requested transitions\n"
            "the tool can commit",
        ),
    )
    for x, fill, edge, title, body in layers:
        axis.add_patch(
            FancyBboxPatch(
                (x, 1.15),
                2.8,
                1.15,
                boxstyle="round,pad=0.05,rounding_size=0.07",
                facecolor=fill,
                edgecolor=edge,
                linewidth=1.2,
            )
        )
        axis.text(x + 0.15, 2.03, title, fontsize=9, weight="bold")
        axis.text(x + 0.15, 1.60, body, fontsize=7.5, va="center")
    for start, end, label in (
        (3.05, 3.6, "message"),
        (6.4, 6.95, "proof + request"),
    ):
        axis.add_patch(
            FancyArrowPatch(
                (start, 1.73),
                (end, 1.73),
                arrowstyle="-|>",
                mutation_scale=10,
                linewidth=1.0,
                color="#444444",
            )
        )
        axis.text(
            (start + end) / 2,
            1.92,
            label,
            ha="center",
            fontsize=6.8,
        )
    axis.text(
        0.25,
        0.48,
        "World truth is scored independently. Authentic provenance does not "
        "authorize an action; a policy-valid proof can still encode a false "
        "claim after the authority cut is crossed.",
        fontsize=7.6,
        color="#444444",
    )
    plots.save(fig, "three_layer_trust_boundary")


def main() -> None:
    plots.theme()
    e1 = load("analysis/E1/formal/results.json")
    e2 = load("analysis/E2/formal/results.json")
    e3 = load("analysis/E3/pilot/adjudicated_results.json")

    plots.MODEL_SLUGS = (
        "claude-sonnet-5",
        "nemotron-3-super-120b",
        "llama-4-maverick",
    )
    plots.provenance_figure(e1)

    plots.MODEL_SLUGS = ("llama-4-maverick",)
    plots.authority_heatmap(e2)
    final_pareto(e2)

    plots.MODEL_SLUGS = ("nemotron-3-super-120b",)
    final_workflow_heatmap(e3)
    plots.interaction_figure(e3)
    plots.trace_figure(e3)

    final_trust_boundary()
    print(
        json.dumps(
            {
                "figure_directory": str(plots.FIGURES),
                "E1": "three complete formal model blocks",
                "E2": "one complete formal model block",
                "E3": "one clean pilot model block after post-run audit",
                "formats": ["PDF", "PNG"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
