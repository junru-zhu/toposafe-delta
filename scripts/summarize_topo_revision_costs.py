#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

from swarmsafe_delta.topo_revision_common import (
    REVISION_ROOT,
    history_assigned_call_count,
    history_call_count,
    history_cost,
    load_jsonl,
)


ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / REVISION_ROOT


def latex_escape(value: object) -> str:
    return (
        str(value)
        .replace("\\", r"\textbackslash{}")
        .replace("_", r"\_")
        .replace("%", r"\%")
        .replace("&", r"\&")
        .replace("#", r"\#")
    )


def main() -> None:
    rows = []
    for path in sorted(PACKAGE.glob("runs/*/*/*/raw/episodes.jsonl")):
        experiment, stage, model_slug = path.parts[-5:-2]
        raw = load_jsonl(path)
        rows.append(
            {
                "experiment": experiment,
                "stage": stage,
                "model_slug": model_slug,
                "episode_rows": len(raw),
                "assigned_calls_including_recovery": sum(
                    history_assigned_call_count(row) for row in raw
                ),
                "realized_calls_including_recovery": sum(
                    history_call_count(row) for row in raw
                ),
                "api_attempts_including_recovery": sum(
                    int(row.get("api_attempts") or 0)
                    + sum(
                        int(item.get("api_attempts") or 0)
                        for item in row.get("resume_history", [])
                    )
                    for row in raw
                ),
                "input_tokens_including_recovery": sum(
                    int(row.get("input_tokens") or 0)
                    + sum(
                        int(item.get("input_tokens") or 0)
                        for item in row.get("resume_history", [])
                    )
                    for row in raw
                ),
                "output_tokens_including_recovery": sum(
                    int(row.get("output_tokens") or 0)
                    + sum(
                        int(item.get("output_tokens") or 0)
                        for item in row.get("resume_history", [])
                    )
                    for row in raw
                ),
                "estimated_cost_usd": sum(history_cost(row) for row in raw),
                "conservative_cost_usd": sum(
                    history_cost(row, conservative=True) for row in raw
                ),
            }
        )
    path = PACKAGE / "COST_LEDGER.csv"
    fields = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    lines = [
        "# TopoSafe revision cost ledger",
        "",
        "Costs are estimates from recorded token usage and the repository's "
        "pricing snapshot, not an AWS billing statement.",
        "",
        "| Experiment | Stage | Model | Assigned calls | Realized calls | "
        "Estimated USD | Conservative USD |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['experiment']} | {row['stage']} | "
            f"{row['model_slug']} | "
            f"{row['assigned_calls_including_recovery']:,} | "
            f"{row['realized_calls_including_recovery']:,} | "
            f"${row['estimated_cost_usd']:.4f} | "
            f"${row['conservative_cost_usd']:.4f} |"
        )
    (PACKAGE / "COST_LEDGER.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )
    tex_lines = [
        r"\begin{tabular}{lllrrrr}",
        r"\toprule",
        (
            r"Experiment & Stage & Model & Assigned & Realized & "
            r"Estimated USD & Conservative USD \\"
        ),
        r"\midrule",
    ]
    for row in rows:
        tex_lines.append(
            f"{latex_escape(row['experiment'])} & "
            f"{latex_escape(row['stage'])} & "
            f"{latex_escape(row['model_slug'])} & "
            f"{row['assigned_calls_including_recovery']:,} & "
            f"{row['realized_calls_including_recovery']:,} & "
            f"{row['estimated_cost_usd']:.4f} & "
            f"{row['conservative_cost_usd']:.4f} \\\\"
        )
    tex_lines.extend([r"\bottomrule", r"\end{tabular}"])
    (PACKAGE / "COST_LEDGER.tex").write_text(
        "\n".join(tex_lines) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
