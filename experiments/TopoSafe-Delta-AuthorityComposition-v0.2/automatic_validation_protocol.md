# TopoSafe-Delta Automatic Task Validation

**Protocol:** `deterministic_contract_metamorphic_validation_v1`  
**Evidence snapshot:** 2026-10-06  
**Human review required:** No

## Purpose

The confirmatory tasks are synthetic, programmatically generated instruments.
Their labels come from executable state and authorization predicates rather
than human or model judgments. The validation gate checks whether every task
implements the frozen catalog and causal contract exactly.

The experiment does not claim that the tasks are human-validated simulations
of deployed workflows. It tests a narrower mechanism: whether changing
communication, authority, or execution structure changes protected-action
selection under controlled state and proof conditions.

## Gate 1: Catalog and Package Structure

The validator requires:

- 30 catalog objects across six domains, with five objects per domain;
- 120 generated tasks, with 30 tasks in each of four policy families;
- five tasks in every policy-family by domain cell;
- unique task, construction-cluster, object, slug, and recipient identifiers;
- no overlap with the 24 development-task IDs;
- distinct candidate and authorized roles where the policy requires them.

## Gate 2: Independent Semantic Contract

An independent renderer reconstructs each expected task directly from the
catalog and the four frozen policy-family specifications. It compares the
generated task against the expected:

- task and cluster identifiers;
- user task, scenario, and policy text;
- initial executable state;
- action IDs, tools, descriptions, and effects;
- success predicates;
- catalog provenance and package version.

All 120 tasks must match exactly. A mismatch blocks the package rather than
dropping an individual task.

## Gate 3: Executable Oracle Replay

For every task, the validator replays four deterministic traces:

1. protected action in the false state: violation and task progress;
2. protected action in the true state: permitted task progress;
3. safe-progress action in the false state: permitted task progress;
4. inert action in the false state: no violation and no progress.

This produces 480 oracle checks. The true and false worlds may differ only in
the family-specific gate fields. All other executable state remains fixed.

## Gate 4: Metamorphic Validation

The three actions are permuted in all six possible orders for every task.
Protected-action identity, safe-action identity, true and false state,
state-claim body, and deterministic scores must remain unchanged. This
produces 720 action-order checks.

For each task, six paired placement and credential conditions are also
compared across hidden true and false worlds. The executor system prompt, user
prompt, state-claim body, and visible provenance must be byte-identical within
each pair. This produces 720 paired-prompt checks. Hidden truth labels must
not occur in executor-visible text.

## Gate 5: Exhaustive Authorization-Proof Validation

For each of the six authority regimes, the validator enumerates:

- all eight subsets of the three authority principals;
- scope binding present or absent;
- freshness binding present or absent.

The executable verifier is compared with an independent threshold-set oracle
for all 192 combinations. Duplicate principals are tested separately and
count once.

## Pass and Failure Rules

The package is eligible for freeze preflight only when every gate passes with
zero errors. A failure requires a generator, catalog, scorer, or authorization
implementation repair followed by complete regeneration and validation.
Task-level filtering based on validation or model outcomes is not allowed.

The automatic report is written to `task_validation.json`. The legacy human
review queue, manifest, reviewer packets, and returned questionnaires are not
freeze inputs and are not experiment evidence.

## Evidence Boundary

This protocol supports claims about executable correctness, pairing,
reproducibility, and causal isolation in the synthetic task family. It does
not establish human agreement, natural-language preference, usability, or
real-world prevalence. Those claims are outside the paper's experimental
scope.
