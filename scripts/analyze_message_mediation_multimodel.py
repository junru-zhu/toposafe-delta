#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path("experiments/TopoSafe-Delta-MessageMediationPilot-v1")
OUTPUT_JSON = ROOT / "analysis" / "multimodel_summary.json"
OUTPUT_MD = ROOT / "analysis" / "multimodel_summary.md"

MODEL_SPECS = (
    {
        "slug": "nova-2-lite",
        "provider": "Amazon",
        "summary": ROOT / "analysis" / "summary.json",
        "raw": ROOT / "raw" / "episodes.jsonl",
    },
    {
        "slug": "llama-4-maverick",
        "provider": "Meta",
        "summary": (
            ROOT
            / "models"
            / "llama-4-maverick"
            / "analysis"
            / "summary.json"
        ),
        "raw": (
            ROOT
            / "models"
            / "llama-4-maverick"
            / "raw"
            / "episodes.jsonl"
        ),
    },
    {
        "slug": "gpt-5.4",
        "provider": "OpenAI",
        "summary": (
            ROOT / "models" / "gpt-5.4" / "analysis" / "summary.json"
        ),
        "raw": ROOT / "models" / "gpt-5.4" / "raw" / "episodes.jsonl",
    },
    {
        "slug": "claude-sonnet-5",
        "provider": "Anthropic",
        "summary": (
            ROOT
            / "models"
            / "claude-sonnet-5"
            / "analysis"
            / "summary.json"
        ),
        "raw": (
            ROOT
            / "models"
            / "claude-sonnet-5"
            / "raw"
            / "episodes.jsonl"
        ),
    },
    {
        "slug": "nemotron-3-super-120b",
        "provider": "NVIDIA",
        "summary": (
            ROOT
            / "models"
            / "nemotron-3-super-120b"
            / "analysis"
            / "summary.json"
        ),
        "raw": (
            ROOT
            / "models"
            / "nemotron-3-super-120b"
            / "raw"
            / "episodes.jsonl"
        ),
    },
)

CONDITIONS = (
    "direct_original",
    "hidden_relay_identical",
    "relay_verbatim",
    "source_paraphrase",
    "relay_paraphrase",
    "verifier_rewrite",
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def build_summary() -> dict[str, Any]:
    models = []
    total_episodes = 0
    total_calls = 0
    total_tokens = 0
    total_provider_errors = 0
    total_malformed = 0
    total_task_failures = 0
    total_safe_episodes = 0
    total_safe_violations = 0
    total_prompt_pairs = 0
    total_prompt_hash_mismatches = 0
    total_prompt_outcome_disagreements = 0
    combined_risky = {
        condition: {"episodes": 0, "violations": 0}
        for condition in CONDITIONS
    }

    for spec in MODEL_SPECS:
        summary = load_json(spec["summary"])
        rows = load_jsonl(spec["raw"])
        if not summary["validation"]["passed"]:
            raise ValueError(f"{spec['slug']}: validation failed")
        model_id = summary["model_ids"][0]
        risky_cells = {}
        safe_cells = {}
        for condition in CONDITIONS:
            risky = summary["by_source_condition"].get(
                f"risky::{condition}"
            )
            safe = summary["by_source_condition"].get(f"safe::{condition}")
            if risky:
                risky_cells[condition] = risky
                combined_risky[condition]["episodes"] += risky["episodes"]
                combined_risky[condition]["violations"] += risky["violations"]
            if safe:
                safe_cells[condition] = safe

        direct = risky_cells["direct_original"]
        model_status = (
            "estimable_development_boundary"
            if direct["violations"] > 0
            else "boundary_not_found_floor"
        )
        prompt_control = summary["prompt_identity_control"]
        model_row = {
            "slug": spec["slug"],
            "provider": spec["provider"],
            "model_id": model_id,
            "episodes": len(rows),
            "calls": sum(int(row["realized_model_calls"]) for row in rows),
            "tokens": sum(int(row["total_tokens"]) for row in rows),
            "provider_errors": sum(
                bool(row.get("provider_error")) for row in rows
            ),
            "malformed": sum(bool(row["malformed"]) for row in rows),
            "task_failures": sum(
                not bool(row["task_success"]) for row in rows
            ),
            "model_status": model_status,
            "risky_cells": risky_cells,
            "safe_cells": safe_cells,
            "prompt_identity_control": prompt_control,
        }
        models.append(model_row)
        total_episodes += model_row["episodes"]
        total_calls += model_row["calls"]
        total_tokens += model_row["tokens"]
        total_provider_errors += model_row["provider_errors"]
        total_malformed += model_row["malformed"]
        total_task_failures += model_row["task_failures"]
        total_safe_episodes += sum(
            int(cell["episodes"]) for cell in safe_cells.values()
        )
        total_safe_violations += sum(
            int(cell["violations"]) for cell in safe_cells.values()
        )
        total_prompt_pairs += int(prompt_control["pairs"])
        total_prompt_hash_mismatches += int(
            prompt_control["prompt_hash_mismatches"]
        )
        total_prompt_outcome_disagreements += int(
            prompt_control["outcome_disagreements"]
        )

    for condition, cell in combined_risky.items():
        cell["violation_rate"] = (
            cell["violations"] / cell["episodes"]
            if cell["episodes"]
            else 0.0
        )

    return {
        "status": "development_multimodel_message_mediation_only",
        "models": models,
        "totals": {
            "models": len(models),
            "episodes": total_episodes,
            "calls": total_calls,
            "tokens": total_tokens,
            "provider_errors": total_provider_errors,
            "malformed": total_malformed,
            "task_failures": total_task_failures,
            "safe_episodes": total_safe_episodes,
            "safe_violations": total_safe_violations,
        },
        "prompt_identity_control": {
            "pairs": total_prompt_pairs,
            "prompt_hash_mismatches": total_prompt_hash_mismatches,
            "outcome_disagreements": total_prompt_outcome_disagreements,
        },
        "descriptive_combined_risky": combined_risky,
        "evidence_boundary": (
            "Five-model development summary over outcome-selected tasks and "
            "frozen messages. Llama used three risky-only repetitions while "
            "the other models used five repetitions with safe controls. "
            "Combined rates are descriptive, not pooled causal estimates."
        ),
    }


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# TopoSafe-Delta Multi-Model Message-Mediation Summary",
        "",
        "**Status:** Development evidence only.",
        "",
        "## Risky-Message Violations",
        "",
        "| Model | Direct | Hidden identical | Relay verbatim | "
        "Source paraphrase | Relay paraphrase | Verifier rewrite | Status |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for model in summary["models"]:
        cells = model["risky_cells"]
        values = []
        for condition in CONDITIONS:
            cell = cells[condition]
            values.append(f"{cell['violations']}/{cell['episodes']}")
        lines.append(
            f"| {model['slug']} | {' | '.join(values)} | "
            f"{model['model_status']} |"
        )

    combined = summary["descriptive_combined_risky"]
    combined_values = [
        f"{combined[condition]['violations']}/"
        f"{combined[condition]['episodes']}"
        for condition in CONDITIONS
    ]
    lines.extend(
        [
            f"| Descriptive total | {' | '.join(combined_values)} | "
            "not a pooled estimate |",
            "",
            "## Validation",
            "",
            (
                f"- Models: {summary['totals']['models']}; episodes: "
                f"{summary['totals']['episodes']}; calls: "
                f"{summary['totals']['calls']}."
            ),
            (
                f"- Provider errors: {summary['totals']['provider_errors']}; "
                f"malformed outputs: {summary['totals']['malformed']}."
            ),
            (
                f"- Safe controls: {summary['totals']['safe_violations']}/"
                f"{summary['totals']['safe_episodes']} violations."
            ),
            (
                "- Identical-prompt control: "
                f"{summary['prompt_identity_control']['prompt_hash_mismatches']} "
                "hash mismatches and "
                f"{summary['prompt_identity_control']['outcome_disagreements']} "
                f"outcome disagreements across "
                f"{summary['prompt_identity_control']['pairs']} pairs."
            ),
            (
                f"- Non-violating task failures: "
                f"{summary['totals']['task_failures']}."
            ),
            "",
            "## Development Conclusions",
            "",
            "- The hidden route produced no systematic effect when the executor "
            "prompt was identical.",
            "- Nova, Llama, and Nemotron exposed measurable direct-message "
            "boundaries; GPT-5.4 and Claude Sonnet 5 remained at a zero-violation "
            "floor under this frozen message family.",
            "- Action-preserving paraphrases removed or sharply reduced violations "
            "in every model with a measurable direct boundary.",
            "- Relay provenance was model-dependent: strong for Nemotron and "
            "Llama, weaker for Nova, and unestimable for GPT and Claude.",
            "- Relay-paraphrase and verifier-rewrite conditions produced zero "
            "violations in all 115 risky episodes across the five models.",
            "",
            "## Evidence Boundary",
            "",
            summary["evidence_boundary"],
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    summary = build_summary()
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    OUTPUT_MD.write_text(render_markdown(summary), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "complete",
                "summary": str(OUTPUT_JSON),
                "models": summary["totals"]["models"],
                "episodes": summary["totals"]["episodes"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()

