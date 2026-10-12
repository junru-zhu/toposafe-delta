# TopoSafe-Delta Paper Proposal

**Status:** Research proposal with completed development diagnostics and a
five-model message-mediation replication; all confirmatory hypotheses and
experiments remain planned.  
**Evidence snapshot:** 2026-10-05.  
**Relationship to SwarmSafe-Delta:** A separate topology-focused paper that
reuses the matched-budget and executable-state measurement principles. It does
not replace the current SwarmSafe-Delta manuscript.

## Recommended Working Title

**The Path Is the Policy: Causal Mediation of Executable Risk in Tool-Using
Multi-Agent Systems**

Topology-forward alternative:

**TopoSafe-Delta: Causal Decomposition of Communication Topology and Role
Placement in Tool-Using LLM Agent Teams**

Alternative title:

**Is the Graph Dangerous, or the Hub? Measuring Topology-Induced Executable
Safety Risk in LLM Agent Teams**

## One-Sentence Story

Existing work shows that architecture and topology can change security
outcomes, but it remains unclear whether an unsafe recommendation is adopted
because of its path, semantic rewriting, sender provenance, policy
verification, repeated exposure, or the placement of an action-authorized role.

## Research Gap

Topology-security studies already compare canonical communication graphs,
exploit attacker position, combine role and topology information, and design
topology-aware defenses. However, canonical topology changes usually alter
several treatment dimensions simultaneously:

1. the number of communication edges;
2. the number and length of delivered messages;
3. path length and repeated exposure;
4. degree concentration and centrality;
5. assignment of planner, verifier, aggregator, or executor roles to nodes;
6. realized model calls, tokens, and trajectory length.

Consequently, a higher violation or attack-success rate in a star or complete
graph is a property of the whole tested configuration, not an identified causal
effect of routing structure.

Recent work also studies PII leakage across topologies, routing-based failure
injection, and role-consistent propagation through message packaging and
provenance. The remaining gap is therefore narrower. Within the current search
boundary, no inspected study factorially combines:

- fixed executor-facing action recommendations;
- exact-text and action-preserving paraphrase interventions;
- sender/provenance swaps and policy-verifier transformations;
- ex-ante matched model-call, token, delivered-message, tool, and action
  budgets;
- balanced role-to-node assignment;
- deterministic policy-defined executable violations.

## Development Pilot Snapshot

The five-model message-mediation runs produced 1,290 valid episodes and 1,290
assigned model calls with zero provider errors.

- Direct risky delivery produced `24/25` violations; routing through one or two
  policy-aware reviewers produced `0/25`.
- In a role-placement pilot, direct risky delivery produced `14/15`
  violations, a faithful relay produced `5/15`, and a policy verifier produced
  `0/15`.
- The faithful relay retained the risky action recommendation in `15/15`
  episodes, so its reduction cannot be attributed to correcting the action
  label.
- In a matched trajectory-fork pilot, a hidden one-hop route with a byte-
  identical executor prompt was `24/25` versus `23/25` direct on Nova and
  `3/15` versus `3/15` on Llama.
- On Nova, changing only to an action-preserving paraphrase reduced violations
  from `23/25` to `7/25`; adding visible relay provenance to the same paraphrase
  reduced them to `0/25`. The paraphrase was shorter, so wording and length
  remain confounded.
- On Llama, all visible relay, paraphrase, and verifier conditions were `0/15`,
  while direct and hidden-identical conditions were both `3/15`.
- Nemotron reproduced the susceptible pattern: direct and hidden-identical were
  `20/25`, relay provenance was `5/25`, source paraphrase was `2/25`, and
  relay-paraphrase/verifier were `0/25`.
- GPT-5.4 and Claude Sonnet 5 were all-zero across the frozen risky-message
  cells, so their mediator effects are not estimable under this message family.
- Safe controls produced zero violations and task success was `1.000` in every
  cell except one non-violating GPT risky-direct abstention.

These are outcome-selected development results, not confirmatory evidence.
They motivate a message-transformation, provenance, and authority decomposition
rather than a named-topology ranking.

They also identify a necessary precondition for cross-model topology studies:
each model must first be calibrated into a non-floor, non-saturated
susceptibility region. Reusing one fixed risky message across models can make
topology effects appear absent simply because the model never crosses its
action boundary.

## Central Scientific Question

> Under matched communication and action opportunities, does routing structure
> itself change executable safety risk, or are apparent topology effects mainly
> explained by message volume and the placement of influential or
> action-authorized roles?

## Core Insight

A communication graph does not have a safety value in isolation. Executable
risk is produced by an interaction among:

- **routing structure:** which paths can carry a message;
- **traffic exposure:** how many message tokens are delivered;
- **role placement:** which topological positions generate, verify, aggregate,
  or execute decisions;
- **action authority:** which recipient can change the external world;
- **message adoption:** whether a recipient follows risky advice.

The paper should therefore estimate separate effects instead of producing one
ranking of named topologies.

## Proposed Causal Quantities

Let \(R(G, \pi, K)\) be executable policy-violation risk under communication
graph \(G\), role assignment \(\pi\), and delivered-message budget \(K\).

### 1. Routing-Structure Effect

For graph pairs \(G\) and \(G'\) with the same agent count, edge count,
in/out-degree sequence, delivered-message slots, and role assignment:

\[
\Delta_{\mathrm{route}}(G,G';\pi,K)
= R(G,\pi,K)-R(G',\pi,K).
\]

Degree-preserving edge swaps change higher-order routing properties such as
clustering, path overlap, modularity, and source-to-executor reach while holding
local exposure fixed.

### 2. Role-Placement Effect

Within the same graph and traffic schedule, move a fixed role between a
high-centrality and low-centrality node:

\[
\Delta_{\mathrm{place}}(G;r)
= R(G,\pi_{r\rightarrow high},K)
-R(G,\pi_{r\rightarrow low},K).
\]

Primary roles of interest are planner, verifier, aggregator, and
action-authorized executor.

### 3. Topology-Placement Interaction

\[
\Delta_{\mathrm{interaction}}
= \Delta_{\mathrm{place}}(G;r)
-\Delta_{\mathrm{place}}(G';r).
\]

This tests whether central placement is dangerous only in particular routing
structures.

### 4. Local Edge-Delivery Effect

From a shared pre-delivery trajectory state, deliver the same candidate message
through the original edge, mask it, replace it with a matched benign message,
or reroute it to a degree-matched recipient. This is a local mechanism
estimand, not a substitute for the system-level graph effect.

## Research Questions

- **RQ1:** After matching delivered traffic and degree sequence, does routing
  structure change executable violation risk?
- **RQ2:** How much of the canonical star/ring/tree/complete difference is
  explained by message volume and degree concentration?
- **RQ3:** Does placing the executor, verifier, or aggregator at a central node
  change risk more than changing the graph family?
- **RQ4:** Do topology rankings reverse between independent internal errors and
  contagious risky recommendations?
- **RQ5:** Which delivered edges causally change message adoption, tool calls,
  or policy-defined world states?
- **RQ6:** Can a small authority-aware routing intervention reduce violations
  without materially reducing safe task success?

## Experimental Design

### Tasks

Use tool-mediated tasks with frozen policy contracts and deterministic state
checks:

- approval bypass;
- false-completion reporting;
- protected-data transfer;
- unauthorized external write;
- unsafe shortcut under an otherwise legitimate task.

Primary experiments should use normal system and task prompts. Controlled
risky, benign, and contradictory peer seeds are secondary stress tests, not the
main threat model.

### Agents And Roles

- Four to six agents per team.
- Fixed role set across all graph arms.
- Balanced role permutations so every critical role occupies high-, medium-,
  and low-centrality nodes equally often.
- Identical model, prompt, tool permission, and action budget for corresponding
  paired episodes.

### Graph Conditions

1. **Traffic-matched graph pairs:** Same \(N\), edge count, degree sequence, and
   per-round delivery slots; different clustering, modularity, path overlap, or
   source-to-executor routing.
2. **Centralization pairs:** Same \(N\), edge count, and total message budget;
   intentionally different degree concentration.
3. **Canonical external-validity graphs:** Star, ring, chain/tree, hierarchy,
   and complete, reported as configuration comparisons rather than pure causal
   topology effects.
4. **Shadow no-delivery control:** Generate and log candidate messages without
   delivering them, preserving the SwarmSafe-Delta communication baseline.

### Outcomes

Primary:

- any policy-defined executable violation;
- safe task success.

Mechanism and cost:

- risky-message generation, receipt, and adoption;
- cascade size and time-to-violation;
- first violating tool call and responsible state transition;
- over-refusal;
- model calls, tokens, delivered message tokens, tool actions, latency, and
  cost.

### Minimum Discriminating Experiments

1. **Matched-rewire test:** Compare degree- and traffic-matched graph pairs.
2. **Role permutation test:** Keep the graph fixed and rotate critical roles
   across centrality positions.
3. **Threat-regime test:** Compare ordinary independent errors with a controlled
   contagious risky recommendation.
4. **Trajectory-fork test:** Mask, replace, or reroute a candidate causal
   message from the same pre-delivery state.
5. **Simple-metric baseline:** Test whether edge count, degree, shortest path,
   or raw centrality already explains the result before proposing a new metric.

## Planned Scale

### Pilot

- 12 calibrated tasks;
- 2 models;
- 4 graph conditions;
- 3 balanced role placements;
- 2 message regimes;
- 3 repetitions.

Approximately 1,728 episodes before trajectory forks.

### Minimum Credible Study

- 24 to 40 frozen test tasks;
- 3 to 4 models;
- 6 graph conditions, including matched rewires and canonical graphs;
- balanced role placements;
- 3 to 5 repetitions.

Final scale should be selected after paired or clustered power analysis using
pilot event rates. No directional result is assumed.

## Falsifiable Outcomes

- If matched rewires do not change risk, there is no evidence for a
  routing-structure effect in the tested distribution.
- If canonical graph differences disappear after traffic and role matching,
  the paper should report that previously observed topology rankings may be
  configuration effects rather than graph-structure effects.
- If role placement dominates graph structure, the main empirical contribution
  becomes the role-position interaction rather than a universal topology
  ranking.
- If effects reverse across message regimes, the correct conclusion is that
  topology safety is threat-conditional.
- If masking or rerouting candidate messages does not change downstream action,
  those edges cannot be called causal propagation paths.
- If primary violations remain too sparse, the frozen study must not proceed
  until task calibration identifies a measurable decision boundary.

## Intended Contributions

1. **Causal evaluation protocol:** Separate routing structure, traffic exposure,
   and role placement under matched ex-ante budgets.
2. **Executable safety evidence:** Evaluate topology using deterministic tool
   receipts and world-state predicates rather than dialogue harmfulness alone.
3. **Mechanism analysis:** Connect graph-level effects to message adoption and
   edge-level trajectory interventions.
4. **Conditional design guidance:** Report when a topology is safer under the
   tested threat and authority regime, without claiming a universal safest
   graph.

## Strongest Overlap Risks

- **MASTER:** Already combines roles and topologies. Our difference must be
  causal balancing and executable environment state, not the existence of the
  interaction.
- **TOMA:** Already routes attacks toward high-privilege agents and validates
  security impacts. Our primary setting must be normal-operation internal
  errors and matched graph/role interventions.
- **E2-Explainer:** Already performs causal edge masking. Our contribution must
  be safety estimands, interaction-aware topology controls, and executable
  outcomes.
- **NetSafe:** Already establishes topology-dependent safety. We must not repeat
  canonical graph rankings as the paper's main result.

## No-Go Conditions

Do not proceed as a full paper if:

- delivered message counts or role placement cannot be matched across the main
  graph interventions;
- the only measurable endpoint is an LLM judgment of harmful text;
- the study requires an externally injected jailbreak to produce every event;
- a simple traffic-count baseline fully explains the proposed contribution and
  no role/topology interaction remains;
- task calibration cannot produce a stable non-floor, non-ceiling executable
  violation rate.

## Proposal Abstract

Communication topology is increasingly treated as a safety-relevant design
choice in LLM agent teams, yet existing comparisons of star, chain, tree, and
fully connected systems change message exposure, path structure, centrality,
role placement, and resource use at the same time. As a result, observed
security differences cannot determine whether risk is caused by routing
structure itself or by placing influential and action-authorized roles in
high-exposure positions. We propose TopoSafe-Delta, a paired evaluation protocol
for decomposing topology-induced executable safety risk in tool-using LLM agent
teams. The protocol matches ex-ante model, token, message, tool, and action
budgets; compares degree- and traffic-matched graph interventions; balances
critical roles across topological positions; and evaluates violations from
deterministic environment states. Graph-level effects are complemented by
trajectory forks that mask, replace, or reroute individual messages from a
shared pre-delivery state. The study is designed to test whether routing
structure has an independent safety effect, whether role placement dominates
canonical topology rankings, and whether topology effects change between
ordinary internal errors and contagious risky recommendations. All empirical
claims remain to be tested.
