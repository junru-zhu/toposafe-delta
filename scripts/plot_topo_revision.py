#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from swarmsafe_delta.topo_revision_common import MODEL_SLUGS, REVISION_ROOT


ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / REVISION_ROOT
FIGURES = PACKAGE / "figures"
COLORS = {
    "gpt-5.4": "#0072B2",
    "claude-sonnet-5": "#D55E00",
    "nemotron-3-super-120b": "#009E73",
    "llama-4-maverick": "#CC79A7",
}
MARKERS = {
    "gpt-5.4": "o",
    "claude-sonnet-5": "s",
    "nemotron-3-super-120b": "^",
    "llama-4-maverick": "D",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--e1-stage", choices=("pilot", "formal"), default="pilot"
    )
    parser.add_argument(
        "--e2-stage", choices=("pilot", "formal"), default="pilot"
    )
    parser.add_argument(
        "--e3-stage", choices=("pilot", "formal"), default="pilot"
    )
    return parser.parse_args()


def load_result(experiment: str, stage: str) -> dict[str, Any]:
    path = PACKAGE / f"analysis/{experiment}/{stage}/results.json"
    if not path.exists():
        raise FileNotFoundError(
            f"analyze {experiment} {stage} before plotting: {path}"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def theme() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8.5,
            "axes.titlesize": 9.5,
            "axes.labelsize": 8.5,
            "xtick.labelsize": 7.5,
            "ytick.labelsize": 7.5,
            "legend.fontsize": 7.2,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.dpi": 160,
            "savefig.dpi": 300,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def save(fig: plt.Figure, stem: str) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        FIGURES / f"{stem}.pdf",
        bbox_inches="tight",
        pad_inches=0.04,
    )
    fig.savefig(
        FIGURES / f"{stem}.png",
        bbox_inches="tight",
        pad_inches=0.04,
    )
    plt.close(fig)


def provenance_figure(result: dict[str, Any]) -> None:
    treatments = ["P0", "P1", "P2", "P3", "P4"]
    labels = [
        "Unsigned",
        "Authority\nlanguage",
        "Verified\nsource",
        "Stale /\nwrong scope",
        "Matched\nmetadata",
    ]
    lookup = {
        (row["model_slug"], row["treatment"]): row
        for row in result["outcomes"]
    }
    fig, axes = plt.subplots(1, 2, figsize=(7.05, 2.65), sharey=True)
    for axis, metric, title in (
        (axes[0], "far", "False-state protected-action selection"),
        (axes[1], "tur", "True-state protected-action selection"),
    ):
        for model_slug in MODEL_SLUGS:
            rows = [lookup[(model_slug, treatment)][metric] for treatment in treatments]
            values = [row["rate"] for row in rows]
            lower = [value - row["ci95"][0] for value, row in zip(values, rows)]
            upper = [row["ci95"][1] - value for value, row in zip(values, rows)]
            axis.errorbar(
                range(len(treatments)),
                values,
                yerr=[lower, upper],
                color=COLORS[model_slug],
                marker=MARKERS[model_slug],
                linewidth=1.35,
                markersize=4,
                capsize=2,
                label=model_slug,
            )
        axis.set_title(title)
        axis.set_xticks(range(len(treatments)), labels)
        axis.set_ylim(-0.03, 1.03)
        axis.set_ylabel("Selection rate")
        axis.grid(axis="y", color="#D9D9D9", linewidth=0.6)
    axes[1].legend(
        frameon=False,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.30),
        ncol=2,
    )
    fig.suptitle(
        f"Authenticated provenance ({result['stage']} evidence)",
        y=1.02,
        fontsize=10,
    )
    fig.subplots_adjust(bottom=0.30, wspace=0.18)
    save(fig, "provenance_far_tur")


def authority_heatmap(result: dict[str, Any]) -> None:
    rows = [
        row
        for row in result["outcomes"]
        if row["world_state"] == "FALSE"
    ]
    row_labels = [
        f"{model}\n{policy}"
        for model in MODEL_SLUGS
        for policy in ("A1", "A2", "A3")
    ]
    columns = ["below cut", "at cut"]
    matrix = np.full((len(row_labels), 2), np.nan)
    for model_index, model in enumerate(MODEL_SLUGS):
        for policy_index, policy in enumerate(("A1", "A2", "A3")):
            cut = {"A1": 1, "A2": 2, "A3": 2}[policy]
            for column, budget in enumerate((cut - 1, cut)):
                match = next(
                    (
                        row
                        for row in rows
                        if row["model_slug"] == model
                        and row["policy_id"] == policy
                        and row["compromised_budget"] == budget
                    ),
                    None,
                )
                if match:
                    matrix[model_index * 3 + policy_index, column] = match[
                        "committed_protected"
                    ]["rate"]
    fig, axis = plt.subplots(figsize=(4.7, 4.6))
    image = axis.imshow(
        matrix,
        cmap="Blues",
        vmin=0,
        vmax=1,
        aspect="auto",
    )
    axis.set_xticks(range(2), columns)
    axis.set_yticks(range(len(row_labels)), row_labels)
    axis.set_title(
        f"False-state committed action around authority cut\n"
        f"({result['stage']} evidence)"
    )
    for row_index in range(matrix.shape[0]):
        for column in range(matrix.shape[1]):
            value = matrix[row_index, column]
            label = "NA" if np.isnan(value) else f"{100 * value:.0f}%"
            axis.text(
                column,
                row_index,
                label,
                ha="center",
                va="center",
                color="white" if value > 0.55 else "#222222",
                fontsize=7.5,
            )
    colorbar = fig.colorbar(image, ax=axis, fraction=0.045, pad=0.03)
    colorbar.set_label("Committed false-state action rate")
    save(fig, "authority_cut_heatmap")


def pareto_figure(result: dict[str, Any]) -> None:
    rows = result["outcomes"]
    fig, axis = plt.subplots(figsize=(5.4, 3.6))
    for model_slug in MODEL_SLUGS:
        for policy_index, policy in enumerate(("A1", "A2", "A3")):
            cut = {"A1": 1, "A2": 2, "A3": 2}[policy]
            false_row = next(
                (
                    row
                    for row in rows
                    if row["model_slug"] == model_slug
                    and row["policy_id"] == policy
                    and row["world_state"] == "FALSE"
                    and row["compromised_budget"] == cut
                ),
                None,
            )
            true_row = next(
                (
                    row
                    for row in rows
                    if row["model_slug"] == model_slug
                    and row["policy_id"] == policy
                    and row["world_state"] == "TRUE"
                    and row["compromised_budget"] == cut - 1
                ),
                None,
            )
            if not false_row or not true_row:
                continue
            safety = 1 - false_row["committed_protected"]["rate"]
            utility = true_row["committed_protected"]["rate"]
            axis.scatter(
                utility,
                safety,
                color=COLORS[model_slug],
                marker=MARKERS[model_slug],
                s=38 + 14 * policy_index,
                edgecolor="#222222",
                linewidth=0.35,
            )
            axis.annotate(
                policy,
                (utility, safety),
                xytext=(4, 3),
                textcoords="offset points",
                fontsize=7,
            )
    for model_slug in MODEL_SLUGS:
        axis.scatter(
            [],
            [],
            color=COLORS[model_slug],
            marker=MARKERS[model_slug],
            label=model_slug,
        )
    axis.set(
        xlabel="True-state committed task completion",
        ylabel="Safety: 1 − false-state committed action",
        xlim=(-0.03, 1.03),
        ylim=(-0.03, 1.03),
        title=f"Safety–utility frontier ({result['stage']} evidence)",
    )
    axis.grid(color="#D9D9D9", linewidth=0.6)
    axis.legend(frameon=False, ncol=2, loc="lower left")
    save(fig, "safety_utility_pareto")


def workflow_heatmap(result: dict[str, Any]) -> None:
    rows = [
        row
        for row in result["outcomes"]
        if row["world_state"] == "FALSE"
    ]
    row_keys = [
        (model, auth, execution)
        for model in MODEL_SLUGS
        for auth in ("A1", "A2")
        for execution in ("E0", "E1")
    ]
    matrix = np.full((len(row_keys), 3), np.nan)
    for row_index, (model, auth, execution) in enumerate(row_keys):
        for column, topology in enumerate(("C1", "C2", "C3")):
            match = next(
                (
                    row
                    for row in rows
                    if row["model_slug"] == model
                    and row["authorization_policy"] == auth
                    and row["execution_policy"] == execution
                    and row["topology"] == topology
                ),
                None,
            )
            if match:
                matrix[row_index, column] = match["false_commit_rate"]
    labels = [
        f"{model}\n{auth}/{execution}"
        for model, auth, execution in row_keys
    ]
    fig, axis = plt.subplots(figsize=(5.4, 5.6))
    image = axis.imshow(
        matrix,
        cmap="magma_r",
        vmin=0,
        vmax=1,
        aspect="auto",
    )
    axis.set_xticks(range(3), ["Direct", "Chain", "Redundant"])
    axis.set_yticks(range(len(labels)), labels)
    axis.set_title(
        f"End-to-end false-state committed actions\n"
        f"({result['stage']} evidence)"
    )
    for row_index in range(matrix.shape[0]):
        for column in range(matrix.shape[1]):
            value = matrix[row_index, column]
            label = "NA" if np.isnan(value) else f"{100 * value:.0f}%"
            axis.text(
                column,
                row_index,
                label,
                ha="center",
                va="center",
                color="white" if value < 0.45 else "#222222",
                fontsize=7,
            )
    colorbar = fig.colorbar(image, ax=axis, fraction=0.04, pad=0.03)
    colorbar.set_label("False-state committed action rate")
    save(fig, "end_to_end_safety_heatmap")


def interaction_figure(result: dict[str, Any]) -> None:
    rows = [
        row
        for row in result["outcomes"]
        if row["world_state"] == "FALSE"
    ]
    fig, axes = plt.subplots(1, 2, figsize=(7.05, 2.8), sharey=True)
    for axis, execution in zip(axes, ("E0", "E1")):
        for auth, color, marker in (
            ("A1", "#D55E00", "o"),
            ("A2", "#0072B2", "s"),
        ):
            values = []
            for topology in ("C1", "C2", "C3"):
                cells = [
                    row["false_commit_rate"]
                    for row in rows
                    if row["authorization_policy"] == auth
                    and row["execution_policy"] == execution
                    and row["topology"] == topology
                    and row["model_valid"]
                ]
                values.append(float(np.mean(cells)) if cells else np.nan)
            axis.plot(
                range(3),
                values,
                marker=marker,
                color=color,
                linewidth=1.5,
                label=auth,
            )
        axis.set_xticks(range(3), ["Direct", "Chain", "Redundant"])
        axis.set_ylim(-0.03, 1.03)
        axis.set_title(
            "Ungated execution" if execution == "E0" else "Proof-gated execution"
        )
        axis.grid(axis="y", color="#D9D9D9", linewidth=0.6)
        axis.set_ylabel("Mean false-state commit rate")
    axes[1].legend(frameon=False)
    fig.suptitle(
        f"Communication × authorization interaction "
        f"({result['stage']} evidence)",
        y=1.02,
        fontsize=10,
    )
    save(fig, "topology_authorization_interaction")


def trust_boundary_diagram() -> None:
    fig, axis = plt.subplots(figsize=(7.05, 2.45))
    axis.set_xlim(0, 10)
    axis.set_ylim(0, 3.3)
    axis.axis("off")
    layers = (
        (
            0.3,
            "#E6F2FA",
            "#0072B2",
            "Communication $G_C$",
            "Source claim → relay/reviewer → executor-visible message",
        ),
        (
            3.55,
            "#E8F5EF",
            "#009E73",
            "Authorization $G_A$",
            "Independent credentials → action-bound proof → $\\kappa_A$",
        ),
        (
            6.8,
            "#FCEEE8",
            "#D55E00",
            "Execution $G_E$",
            "Advisory request → deterministic gate → state transition",
        ),
    )
    for x, fill, edge, title, body in layers:
        box = FancyBboxPatch(
            (x, 1.1),
            2.85,
            1.35,
            boxstyle="round,pad=0.06,rounding_size=0.08",
            facecolor=fill,
            edgecolor=edge,
            linewidth=1.2,
        )
        axis.add_patch(box)
        axis.text(
            x + 0.18,
            2.12,
            title,
            fontsize=9,
            weight="bold",
            color="#222222",
        )
        axis.text(
            x + 0.18,
            1.72,
            body,
            fontsize=7.4,
            color="#333333",
            va="center",
            wrap=True,
        )
    for start, end, label in (
        (3.15, 3.55, "message"),
        (6.4, 6.8, "proof + request"),
    ):
        axis.add_patch(
            FancyArrowPatch(
                (start, 1.78),
                (end, 1.78),
                arrowstyle="-|>",
                mutation_scale=11,
                linewidth=1.0,
                color="#444444",
            )
        )
        axis.text(
            (start + end) / 2,
            1.98,
            label,
            ha="center",
            fontsize=6.8,
        )
    axis.text(
        0.3,
        0.45,
        "World truth is scored independently; source authentication does not "
        "imply truth, and a valid proof does not guarantee truth after the "
        "authority cut is crossed.",
        fontsize=7.5,
        color="#444444",
    )
    save(fig, "three_layer_trust_boundary")


def trace_figure(result: dict[str, Any]) -> None:
    traces = result.get("selected_actual_traces", [])
    if not traces:
        return
    fig, axes = plt.subplots(
        len(traces),
        1,
        figsize=(7.05, 1.65 * len(traces)),
        squeeze=False,
    )
    for axis, trace in zip(axes[:, 0], traces):
        axis.axis("off")
        messages = trace["intermediate_messages"]
        compact = " → ".join(
            [trace["source_message"], *messages, trace["delivered_message"]]
        )
        if len(compact) > 320:
            compact = compact[:317] + "..."
        axis.text(
            0.01,
            0.88,
            f"{trace['trace_type']} | {trace['model_slug']} | "
            f"{trace['topology']} / {trace['authorization_policy']} / "
            f"{trace['execution_policy']}",
            transform=axis.transAxes,
            fontsize=8.2,
            weight="bold",
        )
        axis.text(
            0.01,
            0.55,
            compact,
            transform=axis.transAxes,
            fontsize=7.2,
            va="center",
            wrap=True,
        )
        axis.text(
            0.01,
            0.13,
            f"proof_valid={trace['final_proof_valid']} | "
            f"selected={trace['selected_action']} | "
            f"gate_blocked={trace['runtime_gate_blocked']} | "
            f"false_commit={trace['false_state_committed_action']} | "
            f"true_complete={trace['true_state_task_completion']}",
            transform=axis.transAxes,
            fontsize=7.2,
            color="#444444",
        )
        axis.plot(
            [0.01, 0.99],
            [0.02, 0.02],
            transform=axis.transAxes,
            color="#D9D9D9",
            linewidth=0.8,
        )
    fig.suptitle(
        f"Selected recorded workflow traces ({result['stage']} evidence)",
        y=0.995,
        fontsize=10,
    )
    save(fig, "selected_workflow_traces")


def main() -> None:
    args = parse_args()
    theme()
    e1 = load_result("E1", args.e1_stage)
    e2 = load_result("E2", args.e2_stage)
    e3 = load_result("E3", args.e3_stage)
    provenance_figure(e1)
    authority_heatmap(e2)
    pareto_figure(e2)
    workflow_heatmap(e3)
    interaction_figure(e3)
    trust_boundary_diagram()
    trace_figure(e3)
    print(
        json.dumps(
            {
                "figure_directory": str(FIGURES),
                "formats": ["pdf", "png"],
                "evidence_stages": {
                    "E1": args.e1_stage,
                    "E2": args.e2_stage,
                    "E3": args.e3_stage,
                },
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
