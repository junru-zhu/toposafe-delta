#!/usr/bin/env python3
"""Render the evidence-frozen NAACL headline-results figure."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


OUT = Path(__file__).resolve().parent


def main() -> None:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "font.size": 8.5,
            "axes.titlesize": 9.5,
            "axes.labelsize": 8.5,
            "legend.fontsize": 7.5,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )

    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.35), constrained_layout=True)

    labels = ["C:S", "C:R", "C:V", "N:S", "N:R", "N:V"]
    far_gain = np.array([33.3, 41.7, 41.7, 33.3, 33.3, 37.5])
    tur_gain = np.array([37.5, 41.7, 41.7, 37.5, 37.5, 33.3])
    x = np.arange(len(labels))
    width = 0.36
    axes[0].bar(
        x - width / 2,
        far_gain,
        width,
        label="Δ false acceptance",
        color="#D55E00",
        hatch="//",
        edgecolor="#333333",
        linewidth=0.5,
    )
    axes[0].bar(
        x + width / 2,
        tur_gain,
        width,
        label="Δ true utilization",
        color="#56B4E9",
        edgecolor="#333333",
        linewidth=0.5,
    )
    axes[0].axhline(0, color="#333333", linewidth=0.7)
    axes[0].set_xticks(x, labels)
    axes[0].set_ylim(0, 50)
    axes[0].set_ylabel("Authenticated − unsigned (pp)")
    axes[0].set_title("(a) Authentication amplifies acceptance")
    axes[0].legend(frameon=False, loc="lower left")

    models = ["GPT-5.4", "Claude 5", "Nemotron 3", "Llama 4"]
    advisory = np.array([0.8, 0.0, 52.1, 54.2])
    enforced = np.zeros_like(advisory)
    y = np.arange(len(models))
    axes[1].barh(
        y + 0.17,
        advisory,
        0.34,
        label="Advisory FAR",
        color="#E69F00",
        edgecolor="#333333",
        linewidth=0.5,
    )
    axes[1].barh(
        y - 0.17,
        enforced,
        0.34,
        label="Enforced FAR",
        color="#009E73",
        edgecolor="#333333",
        linewidth=0.5,
    )
    axes[1].scatter(
        np.zeros_like(y),
        y - 0.17,
        marker="|",
        s=160,
        linewidth=2.5,
        color="#009E73",
        zorder=4,
    )
    axes[1].set_yticks(y, models)
    axes[1].invert_yaxis()
    axes[1].set_xlim(0, 60)
    axes[1].set_xlabel("Invalid-proof false acceptance rate (%)")
    axes[1].set_title("(b) Verification closes the execution boundary")
    axes[1].legend(frameon=False, loc="upper right")
    for index, value in enumerate(advisory):
        if value > 0:
            axes[1].text(
                value + 0.8,
                index + 0.17,
                f"{value:.1f}",
                va="center",
                ha="left",
                fontsize=7.0,
                color="#444444",
            )

    for ax in axes:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(axis="y", color="#D9D9D9", linewidth=0.5, alpha=0.7)
        ax.set_axisbelow(True)

    fig.savefig(OUT / "figure_2_results.pdf", bbox_inches="tight")
    fig.savefig(OUT / "figure_2_results.png", dpi=220, bbox_inches="tight")


if __name__ == "__main__":
    main()
