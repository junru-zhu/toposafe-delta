# TopoSafe-Delta Authority Composition v0.2

**Status:** Corrected design-only package, unfrozen, with zero v0.2 provider
calls.  
**Evidence snapshot:** 2026-10-06  
**Purpose:** Turn the authority-cut hypothesis into an auditable confirmatory
protocol after automatic candidate construction and before model freeze or
paid execution.

## 1. Structural Object

For each protected transition \(x\), the authority layer defines a family of
admissible signer sets. The authority cut \(\kappa_A(x)\) is the minimum number
of independent authority principals whose deviation can produce a
policy-valid proof for \(x\), while uncompromised principals follow the frozen
signing policy.

The experiment uses three fixed principal aliases:

- `A`: source;
- `B`: relay;
- `C`: verifier.

The six primary regimes are unsigned, source-single, relay-single,
verifier-single, source-plus-verifier separation of duties, and 2-of-3
quorum. Their authority cuts are respectively not applicable, 1, 1, 1, 2,
and 2.

## 2. Threat and Enforcement Boundary

Compromised authority principals can authenticate an arbitrary state claim.
Honest principals authenticate only a fresh claim supported by their
independent evidence. Communication and execution topology remain fixed.

The structural cut does not by itself guarantee behavioral safety. The LLM
executor remains the test subject and can choose a protected action even when
the presented proof is invalid. The measured result therefore combines:

1. whether a compromise budget can construct a protocol-valid proof; and
2. whether the executor enforces the proof policy before acting.

The executor-visible proof uses three fixed slots with one-bit authenticated
share indicators. Varying the compromise budget changes bits rather than the
number of proof slots, preventing proof length from becoming the threshold
signal.

## 3. Study A: Authority Composition

Study A is specified for 120 new candidate tasks, four model families, and 14
cells per task-model block. The complete package must pass the frozen
deterministic contract and metamorphic validation protocol before it becomes
confirmatory evidence:

\[
6\ \text{authority regimes} \times
2\ \text{truth worlds} + 2\ \text{controls} = 14.
\]

The primary false world has compromise budget \(c=1\). A single-authority
regime can therefore present a valid false proof, whereas separation of duties
and quorum cannot. True worlds present a valid proof whenever the regime
supports authenticated authorization.

Formal calls:

\[
120 \times 14 \times 4 = 6{,}720.
\]

## 4. Study C1: Authority-Cut Threshold

The threshold test uses a stratified 30-task subset and three regimes:
verifier-single, source-plus-verifier separation of duties, and 2-of-3 quorum.
Study A already supplies the true-update and false-update-\(c=1\) rows.

The extension adds false worlds at:

- \(c=0\): no compromised authority principal;
- \(c=2\): the adversary reaches or exceeds every tested cut.

New calls:

\[
30\ \text{tasks} \times
3\ \text{regimes} \times
2\ \text{new budgets} \times
4\ \text{models}
=720.
\]

The authority-cut mechanism is supported only if FAR is lower below the cut
and rises or sharply converges once \(c\) reaches the cut. A flat response to
\(c\) falsifies the structural explanation even if quorum has a lower average
FAR.

## 5. Study C2: Targeted Mechanism Ablations

Ten targeted cells are run on the same 30 tasks and four models. Each cell has
a prespecified matched reference in Study A or C1:

1. two signatures from the same principal;
2. scope binding removed;
3. freshness binding removed;
4. stale signed proof replayed;
5. source and verifier identities swapped;
6. verifier compromised instead of source;
7. authority labels randomized while proof validity is preserved;
8. one quorum share removed;
9. the same unsigned claim duplicated;
10. natural-language consensus without authenticated shares.

New calls:

\[
30 \times 10 \times 4 = 1{,}200.
\]

These are mechanism cells, not a full factorial. Their reference rows are
reused rather than recollected.

## 6. Corrected Confirmatory Call Budget

| Component | Formal calls |
| --- | ---: |
| Study A: authority composition | 6,720 |
| Study B1: matched communication topology | 12,480 |
| Study B2: free-running subset | 2,880 |
| Schedule robustness subset | 2,880 |
| Study C1: authority-cut threshold extension | 720 |
| Study C2: targeted mechanism ablations | 1,200 |
| **New confirmatory total** | **26,880** |

The earlier 24,960 total was arithmetically correct for Studies A, B1, B2, and
schedule replication, but it did not include the threshold and ablation calls
required by the central mechanism claim.

## 7. Primary Outcomes

- false-state acceptance rate, stratified by \(c\) and \(\kappa_A\);
- true-state utilization rate;
- true-claim gain, \(\mathrm{TUR}-\mathrm{FAR}\);
- invalid-proof execution rate;
- safe-progress rate;
- unnecessary-verification rate;
- malformed, truncation, provider-error, and control-failure rates.

The threshold contrast is task-paired:

\[
\Delta_{\mathrm{cut}}
=
\mathrm{FAR}(c\ge\kappa_A)
-
\mathrm{FAR}(c<\kappa_A).
\]

It is reported per model with task-cluster bootstrap intervals. Schedule
replications are not treated as independent tasks.

## 8. Freeze Gates

This design cannot be frozen until:

1. all 120 tasks pass catalog, independent semantic-contract, oracle-replay,
   action-order, paired-prompt, and exhaustive proof-policy validation;
2. the fourth model family, endpoint, response mode, and token budget are fixed;
3. the runner generates all proof cells from one executable regime registry;
4. duplicate principals do not satisfy quorum in deterministic tests;
5. prompt slots and resource budgets pass the matched checks;
6. result validation replays every proof-validity and world-state label;
7. smoke calls exercise each distinct response mode without entering paper
   evidence.

Any change after provider calls begin creates a separately identified corrected
run. Development tasks and Authority-Placement v1.6 outputs remain separate.

### v0.1 exclusion and v0.2 correction boundary

The excluded v0.1 smoke produced 28 rows per model. GPT-5.4, Claude Sonnet 5,
and Nemotron 3 Super 120B passed. Llama 4 Maverick had 12 malformed,
max-token-truncated rows out of 28, with zero provider errors and zero control
failures. A separate excluded diagnostic showed that the same Llama endpoint
returns a compact valid action through supported automatic tool use, while
forced tool choice is unsupported.

Version v0.2 therefore changes only Llama's response transport from JSON text
to automatic `choose_action` tool use. Its model ID, prompt content, task
package, action schema, temperature, token budget, scoring, and statistical
design are unchanged. All v0.1 preflight and smoke rows are excluded from v0.2
and from formal analysis. Every model must rerun preflight and smoke under the
v0.2 frozen sources.

## 9. Current Implementation State

As of 2026-10-06:

- 120 candidate tasks have been generated across six domains and four policy
  families;
- the automatic validation suite checks all 120 task contracts, 480 oracle
  traces, 720 action-order permutations, 720 paired prompts, and 192
  authorization-proof assignments;
- human review is not required and is not used as experiment evidence;
- GPT-5.4, Claude Sonnet 5, Nemotron 3 Super 120B, and Llama 4 Maverick are
  configured; GPT-5.4 and Nemotron use JSON text, Claude uses forced action
  tool selection, and Llama uses automatic action-tool selection;
- the executable runner and replay validator cover Study A and the 720-call
  authority-cut threshold extension, totaling 7,440 implemented formal calls;
- matched-topology, schedule-robustness, and targeted mechanism-ablation
  runners remain planned;
- after automatic validation passes, the check-only freeze preflight is
  blocked only by the excluded four-model preflight.

No v0.2 authority-composition provider call has been made. The excluded v0.1
preflight, smoke, and response-mode diagnostic remain in the separate v0.1
package.

The task family is synthetic and programmatically specified. The protocol
supports executable and causal-validity claims, not human-validated realism or
estimates of real-world incident prevalence.
