# TopoSafe-Delta Free-Running Schedule Replication v0.1

**Status:** Design-only and unfrozen.  
**Parent:** TopoSafe-Delta Free-Running Communication v0.3.  
**Human review:** Not required and not used as evidence.

## Question

Does the B2 conclusion persist when the same requests are executed in a
different frozen order?

## Single Intervention

The parent execution schedule uses seed `2026100641`. This replication freezes
seed `2026100671`. The seed changes the shuffled episode order and the recorded
per-episode schedule identifier. The provider does not expose a sampling seed,
so this is a request-order and execution-schedule replication rather than
deterministic model resampling.

The following components remain fixed:

- the 30 tasks and 720 episode definitions per model;
- all source claims, authorization proofs, topology metadata, delivery
  schedules, prompts, action spaces, and deterministic scorers;
- GPT-5.4, Claude Sonnet 5, Nemotron 3 Super 120B, and Llama 4 Maverick with the
  parent model configurations;
- six workers, three maximum provider attempts, 10-second connect timeout, and
  180-second read timeout;
- six structured forwarding calls with 512 output tokens each and one executor
  call with 200 output tokens;
- the fail-closed proof gate and every validity threshold.

The freeze gate requires the prompt-inventory hash to equal the parent B2 hash
and verifies every source recorded in the parent manifest.

## Scale

The factorial remains

\[
30\times4\times3\times2\times4=2{,}880
\]

episodes. Seven calls per episode yield 20,160 assigned formal model calls
before retries. The two inherited smoke episodes per model contribute 56
excluded calls.

## Analysis

The first analysis repeats the parent B2 tests for advisory FAR, enforced FAR,
true utilization, and semantic increments over B1. A large effect requires an
absolute paired estimate of at least 0.10 and a 95% task-bootstrap interval
excluding zero. Cross-model replication requires the same direction in at
least three valid model blocks.

The schedule-difference analysis estimates

\[
\Delta_{\mathrm{replication}}-\Delta_{\mathrm{parent}}
\]

for each topology, authority regime, outcome, model, and task cluster. It uses
5,000 task-bootstrap draws and the same 0.10 practical-equivalence margin.
Outcome values do not determine validity. The quality gate checks completeness,
configuration identity, retry accounting, proof monotonicity, deterministic
scoring, technical-failure rates, and invalid-proof execution.

## Evidence Boundary

This experiment tests sensitivity to request order and concurrent execution in
the frozen synthetic workflow. It does not provide deterministic sampling-seed
replication because the provider API does not expose that control.
