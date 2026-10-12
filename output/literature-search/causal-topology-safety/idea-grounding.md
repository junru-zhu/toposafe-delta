# Idea-Grounding Packet: Communication, Authority and Execution Topology

**Search date:** 2026-10-06  
**Target idea:** TopoSafe-Delta  
**Evidence boundary:** Literature observations are source-backed; the three-graph
decomposition and authority-cut hypothesis are research inferences to test.

## Source-Supported Observations

1. Communication topology and architecture can change measured multi-agent
   security outcomes.
2. Roles, memory, delegation depth, handoffs and tool exposure interact with
   topology.
3. Authorization drift exists across centralized and decentralized agent
   architectures.
4. Topology-aware detection, routing and remediation already exist.
5. Identity, authorization and delegation enforcement are active system-design
   directions.

## Inferred Opportunity

Most empirical studies use one architecture label for several distinct
relations. A safer and more identifiable model separates:

\[
\mathcal{M}=(G_C,G_A,G_E)
\]

- \(G_C\): message reachability;
- \(G_A\): state-update authorization;
- \(G_E\): protected-action execution.

This decomposition is valuable only if the experiment changes one graph while
matching the other two, messages and budgets.

## Central Mechanism

For protected transition \(x\):

\[
\kappa_A(x)
=
\text{minimum independent compromised principals needed for a valid proof}
\]

The existing Authority-Placement v1.6 conditions all have
\(\kappa_A=1\). The observed weak placement contrasts and strong credential
effects are therefore consistent with, but do not prove, the authority-cut
mechanism.

## Falsifiable Research Question

> When communication and execution topology are fixed, does increasing the
> number of independent authorities required for a protected state transition
> reduce false-state acceptance while retaining true-state utilization, and
> does that advantage vanish when the compromised-principal budget reaches the
> authority cut?

## Strongest Alternative Explanations

| Alternative | Discriminating test |
| --- | --- |
| Models simply prefer majority wording | Duplicate one signer twice; compare with two independent signers |
| Quorum works because prompts are longer | Match proof length and token count |
| Central verifier is enough | Compare verifier-single with source+verifier SoD |
| Safety comes from refusing everything | Report TUR, safe progress and unnecessary verification |
| Topology effect is only message count | Match delivery slots, bytes and calls |
| Topology effect is semantic rewriting | Compare frozen-message and free-running intermediaries |
| Signatures prove truth | Pair valid identity credentials with hidden false state |
| Quorum is universally secure | Raise compromised principals to \(c\ge\kappa_A\) |

## Minimum Convincing Evidence

1. Replicate the credential/placement result on 120 held-out tasks.
2. Compare single authority, separation of duties and quorum.
3. Demonstrate the \(c<\kappa_A\) versus \(c\ge\kappa_A\) threshold.
4. Run matched communication topologies with fixed authority and execution.
5. Validate on a free-running intermediary subset.
6. Preserve deterministic executable scoring and transparent validity gates.

## Main No-Go Conditions

- If true/false message bodies are not exactly paired, the truth-calibration
  claim fails.
- If authority regimes change tool permissions or action space, the
  authority-topology claim fails.
- If topology regimes change total traffic or role placement without balancing,
  the causal topology claim fails.
- If quorum reduces FAR only by collapsing TUR or safe progress, the defense
  claim fails.
- If the threshold ablation does not track \(\kappa_A\), authority cut should
  not be presented as the mechanism.

## Recommended Paper Identity

This should be a causal measurement paper with a falsifiable structural
mechanism, not:

- a graph-ranking benchmark;
- a broad attack catalog;
- a generic authorization framework;
- a model leaderboard.

Recommended title:

> TopoSafe-Delta: Separating Communication, Authority, and Execution Topology
> in Multi-Agent LLM Safety

## Canonical Handoff

The complete research gap, experiment package and evidence-bounded conclusion
are in
[`docs/toposafe-authority-topology-paper-plan.md`](../../../docs/toposafe-authority-topology-paper-plan.md).
