# TopoSafe-Delta

TopoSafe-Delta studies executable safety in multi-agent LLM systems by
separating three structures that are often bundled under one architecture
label:

- `G_C`: who can deliver messages to whom;
- `G_A`: which independent principals can authorize a protected transition;
- `G_E`: which agents can execute the protected action.

The central mechanism is the **authority cut** `kappa_A(x)`: the minimum number
of independent principals that must deviate to construct a policy-valid false
authorization proof for protected transition `x`.

## Canonical paper

**Title:** *When Messages Become Authority: Separating Communication,
Authorization, and Execution in Multi-Agent LLMs*

- Source: [`manuscript/naacl2027/main.tex`](manuscript/naacl2027/main.tex)
- Compiled paper: [`manuscript/naacl2027/main.pdf`](manuscript/naacl2027/main.pdf)
- Venue-neutral manuscript:
  [`manuscript/toposafe-delta.md`](manuscript/toposafe-delta.md)
- Claim audit:
  [`reviews/toposafe-naacl-claim-integrity-audit.md`](reviews/toposafe-naacl-claim-integrity-audit.md)

The manuscript evidence was frozen on 2026-10-07. It reports 66,090 formal
model calls across the included studies. It has not been submitted.

## Current evidence boundary

The paper supports the following bounded conclusions for the evaluated
synthetic protected-action tasks:

1. Communication, authorization, and execution must be intervened on
   separately to identify which layer changes executable safety.
2. Authentication can increase acceptance of both true and false claims
   without improving truth discrimination.
3. Moving one authority between source, relay, and verifier does not create a
   stable advantage when the authority cut remains one.
4. Communication-topology effects are model-conditional after authority and
   execution are fixed; the evaluated studies do not support a universal
   ranking of chain, star, tree, or mesh.
5. Authority composition controls structural proof forgeability, while
   fail-closed deterministic verification is what prevents invalid proofs from
   reaching protected execution.

The 2026-10-12 execution-topology extension is included in this repository but
is **not integrated into the paper's formal claims**. Claude Sonnet 5, Llama 4
Maverick, and Nemotron 3 Super 120B were collected; the GPT-5.4 block remained
incomplete after bounded transport-timeout recovery attempts. Its three-model
analysis is explicitly labeled sensitivity evidence.

See [`STATUS.md`](STATUS.md) and [`EXPERIMENTS.md`](EXPERIMENTS.md) for exact
status boundaries.

## Repository layout

| Path | Contents |
| --- | --- |
| `manuscript/` | Paper source, figures, bibliography, and compiled PDF |
| `experiments/` | Frozen TopoSafe experiment packages, raw outputs, validation, and analyses |
| `src/` | Reusable experiment and deterministic scoring implementation |
| `scripts/` | Build, freeze, run, validate, and analyze entry points |
| `tests/` | Offline unit and integrity tests |
| `data/` | Synthetic task catalogs |
| `docs/` | Research plan and mechanism specification |
| `output/` | Literature search and idea-grounding records |
| `reviews/` | Claim-integrity audits and revision ledger |
| `submission/` | Draft submission-preparation material; no submission record |

## Local setup

Python 3.11 or newer is required.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest
```

Model-running scripts use Amazon Bedrock through the caller's own configured
AWS credentials. No credentials are included in this repository. Unit tests
do not require live model calls.

## Reproducibility and integrity

- Parent runs, technical recoveries, and post-hoc sensitivities remain in
  separate directories.
- Failed preregistered gates are retained rather than overwritten.
- Primary labels come from deterministic synthetic environment state and proof
  validation, not an LLM judge.
- Raw provider outputs are retained for private reproducibility review.
- The repository is a private research snapshot. No public artifact release or
  venue submission is implied.

