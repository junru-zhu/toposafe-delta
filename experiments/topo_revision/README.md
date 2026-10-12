# TopoSafe Revision v1.0

This directory is the isolated 2026-10-12 evidence-strengthening package for
TopoSafe-Delta. It does not overwrite the historical frozen studies or the
evidence-frozen manuscript.

## Start here

1. `FINAL_RESEARCH_REPORT.md` — conclusions, hypothesis decisions, costs,
   paper impact, and remaining blockers.
2. `POST_RUN_INTEGRITY_AUDIT.md` — model-block validity and the E3 forwarder
   adjudication.
3. `EXISTING_EVIDENCE_AUDIT.md` — mapping from historical claims to code and
   data.
4. `PROTOCOL.md` — hypotheses, designs, statistical methods, validity gates,
   and budgets frozen before model outcomes.
5. `EXPERIMENT_MATRIX.csv` — planned call accounting.

## Directory map

| Path | Contents |
| --- | --- |
| `frozen/` | Generated tasks, cases, pilot selections, and deterministic preflight |
| `runs/` | Raw model rows, intermediate traces, retries, and validation reports |
| `analysis/` | Machine-derived outcomes, effects, confidence intervals, and selected traces |
| `figures/` | Paper-ready PDF and PNG figures |
| `RUN_INVENTORY.*` | Every experiment/stage/model validity status |
| `COST_LEDGER.*` | Calls, tokens, API attempts, and estimated costs |

## Evidence boundary

- E1: three complete formal model blocks.
- E2: deterministic structural result plus one complete formal Llama block.
- E3: one clean Nemotron pilot block; formal NOT RUN.
- E4: NOT RUN.

Raw provider output is retained for private reproducibility review. The package
contains no real credentials, production data, real payment actions, identity
changes, or document releases.
