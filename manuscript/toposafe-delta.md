# TopoSafe-Delta: Authority Cut for Decoupling Communication, Authorization, and Execution in Multi-Agent LLMs

**Manuscript status:** Evidence-frozen venue-neutral manuscript.  
**Evidence snapshot:** 2026-10-07.

## Abstract

Multi-agent LLM safety studies often compare chains, stars, trees, and meshes,
but these labels jointly change message flow, authorization, and execution
access, preventing causal attribution. TopoSafe-Delta represents a system with
separately intervenable communication, authority, and execution graphs and
defines the authority cut \(\kappa_A\) as the minimum number of independent
principals that must deviate to construct a policy-valid false authorization
proof. We evaluate this framework on synthetic protected-action tasks with
executable ground truth, four model families, 120-task matched factorials,
free-running relays, proof ablations, and schedule replication, totaling
66,090 formal model calls without human or model-judge labels. Authentication
increased acceptance of both true and false claims in the valid development
blocks, while moving one authority produced no stable advantage. After
authority and execution were fixed, neither frozen-message nor free-running
communication topologies produced a cross-model replicated large safety
effect. Advisory responses around \(\kappa_A\) remained model-dependent, but
a deterministic fail-closed gate prevented every invalid-proof protected
action in the fresh four-model factorial, and all 257 triggered recoveries made
safe progress. These results identify authority composition and runtime proof
enforcement, rather than communication topology alone, as the mechanisms that
set the executable safety boundary in this task family.

## 1. Introduction

Tool-using LLM agents increasingly operate as teams in which one agent gathers
state, another relays or verifies it, and a final executor selects an action.
This organization creates a basic measurement problem. A single architecture
label such as chain, star, tree, or mesh simultaneously describes who can send
messages, whose statements are authorized to change protected state, and who
can execute a consequential action. When these relations move together, an
observed safety difference cannot be assigned to communication structure
alone.

Recent work has established that multi-agent architecture matters. NetSafe
compares canonical communication topologies under harmful-information
propagation, while G-Safeguard constructs utterance graphs for topology-guided
detection and intervention. Architecture Matters jointly studies roles,
communication topology, and memory. MasDrift is the closest authorization
study: it measures authorization preservation across single-agent,
centralized, and decentralized architectures. These studies cover broad topology
safety and architecture-dependent authorization behavior
[[NetSafe](https://aclanthology.org/2025.findings-acl.150/),
[G-Safeguard](https://aclanthology.org/2025.acl-long.359/),
[Architecture Matters](https://arxiv.org/abs/2604.23459), and
[MasDrift](https://arxiv.org/abs/2608.07556)]. Their architecture conditions,
however, change several relations together, including path length, role
assignment, delegation depth, handoffs, memory, and tool exposure.

We study the unresolved causal question: which layer of a multi-agent
architecture changes executable safety? We represent a system with three
separately intervenable structures,

\[
\mathcal{M}=(G_C,G_A,G_E),
\]

where \(G_C\) governs message delivery, \(G_A\) governs which combinations of
independent principals can authorize a protected state transition, and \(G_E\)
governs which agents can execute protected actions. The decomposition changes
the experimental target. Instead of ranking complete architectures, it holds
two structures fixed while intervening on the third.

The authority layer introduces a more specific mechanism than signer
placement. For a protected transition \(x\), we define the authority cut
\(\kappa_A(x)\) as the minimum number of independent authority principals that
must deviate to construct a policy-valid authorization proof. Moving a single
signer from source to relay or verifier leaves \(\kappa_A=1\). Requiring
source-plus-verifier separation of duties or a 2-of-3 quorum raises the cut to
two. This distinction yields a falsifiable threshold: a higher cut should
reduce false-state acceptance when the compromise budget is below the cut, and
the advantage should shrink when the budget reaches it.

Our development study provides empirical motivation for this mechanism.
Authority-Placement v1.6 fixes a four-node communication chain and a single
executor while varying the location and authentication status of one
state-update authority. Platform-authenticated provenance increased acceptance
of both true and false state claims across the two model blocks that passed the
preregistered validity gates. Moving the single authority among source, relay,
and verifier produced no stable advantage. The result is consistent with
authentication acting as an acceptance amplifier while all placement
conditions retain the same one-principal compromise threshold.

TopoSafe-Delta makes four contributions:

- It separates communication, authority, and execution into independently
  intervenable graphs and defines authority cut as the compromise threshold
  for constructing a policy-valid authorization proof.
- It introduces an executable synthetic evaluation with paired hidden-truth
  worlds, deterministic proof and action scoring, four model families, and
  66,090 formal model calls without human or model-judge labels.
- It shows that authentication can amplify acceptance without truth
  discrimination, while neither single-authority placement nor matched
  communication topology yields a stable cross-model advantage.
- It separates structural proof forgeability from behavioral compliance:
  advisory responses to authority composition vary by model, whereas
  fail-closed proof verification consistently prevents invalid proofs from
  reaching protected execution and supports safe recovery.

## 2. Method

### 2.1 Three-Topology System Model

Let \(V\) be the set of agents and services participating in one task episode.
The communication graph \(G_C=(V,E_C)\) contains a directed edge
\((u,v)\in E_C\) when \(u\) can deliver a message to \(v\) under the frozen
schedule. Message reachability does not imply authority: a node may relay a
claim without being allowed to authorize the corresponding state transition.

Let \(P\) be the set of authority principals. For each protected transition
\(x\), the authority structure specifies a family
\(\mathcal{Q}_x\subseteq 2^P\) of signer sets that satisfy the authorization
policy. This makes \(G_A\) naturally a hypergraph: an authorization edge can
join several principals to one transition. A single-authority rule contains a
singleton set, separation of duties contains a required multi-principal set,
and a threshold quorum contains every eligible set meeting the threshold.

The execution graph \(G_E\) maps agents to executable capabilities. An edge
\((v,x)\in G_E\) means that agent \(v\) can request or commit transition \(x\).
Our primary studies give only the executor access to the protected action.
This prevents a change in authority composition from also changing the number
of execution opportunities.

### 2.2 Authorization Proofs and Authority Cut

An authorization proof \(\pi\) binds a state claim to the transition, object,
state field, version, freshness window, and authenticated principals required
by the regime. The deterministic predicate
\(\operatorname{Verify}_x(\pi)\) returns one only when these bindings are valid
and the authenticated principals contain a satisfying set in
\(\mathcal{Q}_x\).

We assume that compromised principals may authenticate an arbitrary claim,
whereas uncompromised principals authenticate only a fresh claim supported by
their independent evidence. The authority cut is

\[
\kappa_A(x)
=
\min_{\mathcal{C}\subseteq P}
\left\{
|\mathcal{C}|:
\exists \pi,\ 
\operatorname{Verify}_x(\pi)=1
\text{ when principals in }\mathcal{C}\text{ may deviate}
\right\}.
\]

Honest principals follow the frozen signing policy in this definition. Thus a
single authenticated authority has cut one, source-plus-verifier separation
of duties has cut two, and a 2-of-3 independent quorum also has cut two.
Repeated signatures from the same principal count once.

Authority cut is a property of the authorization protocol, not a behavioral
guarantee. The LLM executor remains the object under test and may choose a
protected action even when \(\operatorname{Verify}_x(\pi)=0\). The experiment
therefore measures both structural proof availability and proof-enforcement
fidelity. A quorum that is structurally unforgeable below its cut provides no
behavioral protection if the executor routinely ignores missing or invalid
shares.

### 2.3 Paired Hidden-Truth Task Construction

Each task contains one protected action, one safe-progress action, a stale
executor snapshot, and a hidden current state. Paired true and false worlds use
the same executor-visible state-claim body. Truth changes only the hidden state
used by the deterministic scorer. The protected action is valid in the true
world and violates policy in the false world; the safe-progress action remains
nonviolating in the false world.

Authority conditions modify proof metadata rather than claim semantics. Proof
records use fixed signer slots, so varying the compromised-principal budget
changes authenticated-share bits without changing the number of slots. The
prompt never exposes the hidden truth or the scorer's computed proof-validity
label.

### 2.4 Authority-Placement Development Study

Authority-Placement v1.6 uses the fixed route
source \(\rightarrow\) relay \(\rightarrow\) verifier
\(\rightarrow\) executor. It crosses three authority placements, unsigned
versus platform-authenticated provenance, and hidden true versus false state.
Two direct-state controls produce 14 cells per task across 24 development tasks
balanced among approval bypass, false completion, unauthorized execution, and
protected transfer.

The primary outcomes are false-state acceptance rate,

\[
\mathrm{FAR}
=P(\text{protected action}\mid\text{false state}),
\]

true-state utilization rate,

\[
\mathrm{TUR}
=P(\text{protected action}\mid\text{true state}),
\]

and true-claim gain, \(\mathrm{TCG}=\mathrm{TUR}-\mathrm{FAR}\). We also
measure safe progress and unnecessary verification alongside malformed output,
truncation, provider errors, and control failures. Paired task-level
differences are reported with task-cluster bootstrap intervals.

### 2.5 Confirmatory Authority Composition

The study uses 120 new task clusters and four model families. The task package
passed deterministic construction checks before it was frozen. An independent
template oracle
reconstructs every task from the catalog and policy-family contract. The
automatic gate also replays 480 deterministic action-state traces, tests all
720 action-order permutations, checks 720 paired true/false prompts, and
enumerates 192 authorization-proof assignments. Study A fixes \(G_C\) and
\(G_E\) while comparing unsigned,
source-single, relay-single, verifier-single, source-plus-verifier separation
of duties, and 2-of-3 quorum authorization. The primary false world has one
compromised principal. Single-authority regimes can then construct a valid
false proof, whereas the two cut-two regimes cannot.

On a stratified 30-task subset, the threshold extension adds false worlds with
zero and two compromised principals. The \(c=1\) and true-update rows are
reused from Study A. The mechanism is supported only if FAR changes around
\(c=\kappa_A\). Ten targeted ablations test signer independence, scope,
freshness, stale replay, signer identity, compromise location, label semantics,
missing shares, duplicated claims, and unauthenticated natural-language
consensus.

Study B fixes \(G_A\) and \(G_E\) while intervening on four matched six-node
communication graphs. A frozen-message condition estimates residual structural
trust effects with an identical executor-facing claim. A free-running
condition allows intermediaries to rewrite or drop claims and proofs through
one `forward_envelope` schema, exposing the semantic propagation component.
Calls, message slots, aggregate traffic, action space, and execution budget
remain matched.

The completed B1 factorial uses four six-node, six-edge graphs. Their
source-to-executor distances are one, three, four, and five; degree
centralization and edge-disjoint route counts vary while six scheduled
delivery slots and aggregate message bytes remain fixed. Anonymous node-role
assignments rotate evenly across tasks. Each topology is crossed with
verifier-single, source-plus-verifier separation of duties, and 2-of-3 quorum
authority under paired true and false worlds. Two direct-state controls are
included for each task and model. This produces 3,120 calls per model and
12,480 calls overall. The executor makes one advisory model choice, followed
by the same deterministic fail-closed action gate in every topology.

B2 uses a deterministic 30-task subset and crosses the same topologies,
authority regimes, truth worlds, and models. Each episode contains six
structured forwarding calls and one executor call. The design therefore
contains 2,880 formal episodes and 20,160 assigned model calls. One structured
forwarding schema and its validity gates were frozen before formal calls.
The schedule replication reuses the same task, case, prompt, model, budget,
scoring, and gate artifacts while changing the schedule seed and resulting
request order. The provider does not expose a sampling seed, so the
replication estimates schedule robustness rather than deterministic
model-sampling reproducibility.

The core intervention ledger contains 61,440 assigned model calls: 6,720 for
Study A, 720 for the threshold extension, 12,480 for B1, 20,160 each for B2
and its schedule replication, and 1,200 for targeted mechanism ablations. The
complete evidence reported in this manuscript contains 66,090 formal model
calls after adding 1,008 development placement calls, 697 post-hoc recovery
calls in Runtime Enforcement v0.1, and 2,945 initial-plus-recovery calls in the
fresh Runtime Enforcement v0.2 factorial. Deterministic gate replays and 84
development smoke calls are reported separately and are not included in this
formal-call total.

The frozen tasks are synthetic and programmatically specified. Their
labels come from executable state and proof predicates rather than human or
model judgments. The study tests causal effects within this task family and
does not estimate deployed-workflow prevalence or human preference.

### 2.6 Runtime Enforcement Studies

Runtime Enforcement v0.1 separates proof validity from action execution. It
replays the 6,480 non-control proof-bearing rows from Authority Composition
v0.2 under three conditions. The advisory condition preserves the parent model
choice. The gate-only condition rejects the protected action whenever
\(\operatorname{Verify}_x(\pi)=0\). The gate-plus-recovery condition gives a
denied executor one additional turn with the authoritative snapshot and a
standardized denial message. A repeated protected attempt is blocked again.

Formal recovery calls are made only for parent rows in which the model selected
the protected action under an invalid proof. This produced 697 recovery cases.
Task labels, proof validity, execution outcomes, and recovery success are
scored deterministically without human or model judges. Because case selection
depends on the parent outcomes, this extension tests the enforcement mechanism
but does not constitute an independent factorial replication.

Runtime Enforcement v0.2 provides that independent test. It contains 48 new
task clusters balanced across four policy families and six domains, with no
task-ID overlap with prior packages. Each task has 14 initial cells:
verifier-single, source-plus-verifier separation of duties, and 2-of-3 quorum
under one true world and false worlds with compromise budgets
\(c\in\{0,1,2\}\), plus two direct-state controls. The four-model factorial
therefore contains 2,688 initial calls.

The recovery trigger was frozen before provider calls. Every non-control
episode that selected the protected action under an invalid proof received one
additional turn after deterministic denial. No case was selected manually.
The protocol permits at most 960 recovery calls; the observed initial outcomes
triggered 257. Human review is absent from task construction, scoring, case
selection, and validity decisions.

### 2.7 Targeted Authority Mechanism Ablations

The targeted study selects 30 Runtime Enforcement v0.2 tasks without using
model outcomes: one task from every policy-family-by-domain cell and one
additional task from a rotating family in each domain. Each task receives ten
interventions covering repeated signatures from one principal, missing scope
or freshness bindings, stale signed replay, source-verifier identity exchange,
compromise location, randomized authority labels, a missing quorum share,
duplicated unsigned claims, and unauthenticated natural-language consensus.
The matching reference response for the same task and model is reused from the
frozen parent factorial.

All target worlds contain a false update. Eight interventions construct an
invalid proof, while source-verifier identity exchange and randomized labels
preserve proof validity. The primary behavioral estimand is the paired change
in advisory FAR relative to the parent reference, with a 5,000-draw task
bootstrap. A large effect requires at least 10 percentage points and an
interval excluding zero; cross-model replication requires the same direction
in at least three model blocks. The deterministic fail-closed gate separately
tests whether an invalid target proof reaches execution. This design contains
1,200 formal calls and no human or model-judge labels.

## 3. Results

### 3.1 Authority Placement

Authority-Placement v1.6 completed 1,008 formal calls
\((24\ \text{tasks}\times14\ \text{cells}\times3\ \text{models})\) and 84
separate smoke calls. Provider errors and malformed or truncated responses
were zero. Claude Sonnet 5 and NVIDIA Nemotron 3 Super 120B passed all validity
gates. GPT-5.4 was excluded from confirmatory interpretation because its
control-failure rate was \(3/48=6.25\%\), above the preregistered 5% threshold.

| Model | Authority | FAR unsigned | FAR authenticated | TUR unsigned | TUR authenticated | TCG authenticated |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Claude Sonnet 5 | source | 0.000 | 0.333 | 0.000 | 0.375 | 0.042 |
| Claude Sonnet 5 | relay | 0.000 | 0.417 | 0.000 | 0.417 | 0.000 |
| Claude Sonnet 5 | verifier | 0.000 | 0.417 | 0.000 | 0.417 | 0.000 |
| Nemotron 3 Super 120B | source | 0.250 | 0.583 | 0.250 | 0.625 | 0.042 |
| Nemotron 3 Super 120B | relay | 0.292 | 0.625 | 0.250 | 0.625 | 0.000 |
| Nemotron 3 Super 120B | verifier | 0.292 | 0.667 | 0.292 | 0.625 | -0.042 |

Authenticated provenance raised both FAR and TUR at every placement in both
valid model blocks. Every preregistered credential safety-cost and utility-gain
interval excluded zero. In contrast, TCG remained between \(-0.042\) and
\(+0.042\), indicating that authentication changed acceptance without
providing access to the hidden state truth.

Moving the authenticated authority produced much smaller effects. For Claude,
the verifier-minus-source placement contrast was \(+0.083\) with a 95%
interval of \([-0.083,0.250]\), and verifier-minus-relay was \(0.000\) with
\([-0.167,0.167]\). For Nemotron, the corresponding contrasts were \(+0.042\)
with \([-0.083,0.167]\) and \(+0.042\) with \([0.000,0.125]\). These
development results do not identify a stable best location for a single
authority.

The observed pattern supports a narrow conclusion. Under the fixed chain and
one-authority protocol, authenticated provenance amplified acceptance of both
true and false claims, while signer location had no stable advantage. The
three placement conditions have \(\kappa_A=1\), so this experiment does not
identify the effect of increasing the cut.

### 3.2 Authority Composition and Compromise Threshold

Authority Composition v0.2 completed 6,720 Study A rows and 720 threshold
rows. Claude Sonnet 5 and Nemotron 3 Super 120B passed the Study A validity
gate. GPT-5.4 had 17 control failures among 240 control rows, and Llama 4
Maverick had 24; both rates exceeded the preregistered 5% threshold. All four
threshold blocks passed structural, proof, score, hash, and provider
validation, but the GPT and Llama threshold results remain descriptive.

Claude showed a sharp authority-cut response for verifier-single and
source-plus-verifier separation of duties. Their FAR sequences at
\(c=0,1,2\) were \(0.00,0.40,0.40\) and \(0.00,0.00,0.33\), respectively.
The corresponding cut contrasts were \(+0.40\) with a 95% task-bootstrap
interval of \([0.23,0.57]\) and \(+0.33\) with \([0.17,0.50]\). Quorum blocked
false updates below the cut, but its Study A TUR was 0.008, so this regime did
not preserve useful true-state utilization for Claude.

Nemotron produced positive cut contrasts for verifier-single, separation of
duties, and quorum: \(+0.20\), \(+0.13\), and \(+0.30\), with intervals
\([0.07,0.35]\), \([0.03,0.25]\), and \([0.15,0.45]\). Its below-cut FAR was
already high. The corresponding \(c=0\) rates were 0.50, 0.50, and 0.40, and
quorum FAR at \(c=1\) was 0.47.

These results separate two mechanisms. Authority cut determines when an
adversary can construct a protocol-valid proof. Executable safety also depends
on whether the LLM executor rejects an invalid proof. Raising the cut produced
budget-sensitive acceptance in the two valid model blocks, but did not make
the executor fail closed across models and regimes.

### 3.3 Runtime Enforcement and Recovery

The runtime extension replayed all 6,480 proof-bearing parent rows. The
fail-closed gate reduced executed violations under invalid false proofs to zero
for every model. It triggered 697 formal recovery calls: 60 for GPT-5.4, 314
for Nemotron 3 Super 120B, and 323 for Llama 4 Maverick. Claude Sonnet 5
triggered no recovery call because none of its parent rows selected the
protected action under an invalid proof.

| Model | Parent validity gate | Recovery calls | Advisory FAR on invalid false proofs | Enforced FAR | Recovery safe progress |
| --- | --- | ---: | ---: | ---: | ---: |
| GPT-5.4 | failed | 60 | 7.1% | 0.0% | 100.0% |
| Claude Sonnet 5 | passed | 0 | 0.0% | 0.0% | N/A |
| Nemotron 3 Super 120B | passed | 314 | 54.2% | 0.0% | 100.0% |
| Llama 4 Maverick | failed | 323 | 56.7% | 0.0% | 100.0% |

All 697 denied attempts selected the designated safe-progress action in one
additional turn. No recovery repeated the protected attempt, and no invalid
proof produced an executed violation. The gate did not change outcomes once
the compromise budget reached the authority cut, because those adversarial
proofs satisfied the authorization policy. Authority composition therefore
sets the proof-forgeability threshold, while runtime enforcement determines
whether invalid proofs can cross the execution boundary.

### 3.4 Fresh Independent Runtime-Enforcement Factorial

Runtime Enforcement v0.2 completed all 2,688 initial calls and 257 triggered
recovery calls. The run required 3,012 provider attempts including retries.
All four model blocks passed the frozen validity gates. Control task progress
ranged from 89.6% to 100%, false-control violation was zero, and the largest
malformed-or-truncated rate was 0.30%.

| Model | Control progress | Advisory FAR on invalid false proofs | Enforced FAR | Paired reduction [95% CI] | Recovery calls | Recovery safe progress |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GPT-5.4 | 93.8% | 0.8% | 0.0% | 0.8% [0.0%, 2.1%] | 2 | 100.0% |
| Claude Sonnet 5 | 97.9% | 0.0% | 0.0% | 0.0% [0.0%, 0.0%] | 0 | N/A |
| Nemotron 3 Super 120B | 100.0% | 52.1% | 0.0% | 52.1% [39.2%, 64.6%] | 125 | 100.0% |
| Llama 4 Maverick | 89.6% | 54.2% | 0.0% | 54.2% [42.1%, 65.8%] | 130 | 100.0% |

The gate eliminated invalid-proof execution for every model. All 257 triggered
recoveries selected safe progress, and no recovery repeated the blocked
attempt. True-world task progress was 100% in every model block. The result
also identifies the authority-cut boundary: enforced FAR is zero when the
compromise budget is below \(\kappa_A\), but enforcement leaves outcomes
unchanged once the adversary can construct a policy-valid proof at or above
the cut.

### 3.5 Matched Frozen-Message Communication Topology

Matched Communication B1 completed all 12,480 formal calls and required 13,073
provider attempts including retries. All four model blocks passed the frozen
validity gates. Control progress ranged from 99.2% to 100%, false-control
violation was zero, and the largest malformed-or-truncated rate was 0.26%.
The final dataset contains no missing rows, duplicate episode IDs, unresolved
provider errors, budget mismatches, or invalid-proof executions.

The preregistered analysis compared each of three topologies with `topo_A`
using paired task-cluster differences and 5,000 bootstrap draws. A large effect
required an absolute estimate of at least 10 percentage points and a 95%
interval excluding zero. No contrast met this rule in any model, and no large
effect replicated across models. Twenty-six of the 27 topology-by-authority-
by-outcome contrasts had every valid-model interval contained within the
frozen \(\pm 10\)-point equivalence margin.

| Model | Largest absolute B1 contrast versus `topo_A` | Estimate [95% CI] |
| --- | --- | ---: |
| GPT-5.4 | `topo_D`, verifier-single FAR | +3.3% [+0.8%, +6.7%] |
| Claude Sonnet 5 | `topo_D`, verifier-single FAR | +5.0% [+0.0%, +10.0%] |
| Nemotron 3 Super 120B | `topo_C`, SoD advisory FAR | -6.7% [-11.7%, -2.5%] |
| Llama 4 Maverick | `topo_D`, SoD true utilization | -1.7% [-5.0%, +1.7%] |

The Nemotron SoD advisory contrast was the sole comparison that did not satisfy
the cross-model equivalence rule because its interval extended beyond -10
points. Its point estimate remained below the 10-point large-effect threshold.
For cut-two SoD and quorum proofs at compromise budget \(c=1\), the common
fail-closed gate reduced executed FAR to zero in every topology. Under this
frozen-message intervention, changing route length, centralization, and route
redundancy did not produce a stable large safety effect after \(G_A\), \(G_E\),
message content, traffic, and budgets were matched.

### 3.6 Free-Running Semantic Propagation

Free-running Communication B2 completed all 2,880 formal episodes and 20,160
assigned model calls. The run required 20,319 provider attempts including
retries. All four model blocks passed the frozen gates. Active-forward
technical-failure rates ranged from 0% to 0.43%, executor failure rates ranged
from 0% to 0.42%, and no invalid final proof produced an executed violation.

Longer paths changed the transmitted message in every model. Mean
source-to-final similarity from `topo_A` to `topo_D` fell from 0.781 to 0.576
for GPT-5.4, 0.912 to 0.866 for Claude Sonnet 5, 0.989 to 0.805 for Llama 4
Maverick, and 0.975 to 0.963 for Nemotron 3 Super 120B. Message delivery at
`topo_D` remained between 97.2% and 100%, and valid-proof retention remained
between 97.5% and 100%.

The safety effect did not form a stable topology ranking. None of the 27
topology-by-authority-by-outcome contrasts produced a large B2 effect in at
least three models, and no large semantic increment over the corresponding B1
contrast replicated. Ten contrasts were model-conditional in each analysis,
primarily verifier-single outcomes for GPT-5.4 and Claude Sonnet 5. For
`topo_D` versus `topo_A`, verifier-single executed FAR changed by
\(-33.3\) points for GPT-5.4 with a 95% interval of
\([-50.0,-16.7]\), by \(-16.7\) points for Claude with
\([-30.0,-3.3]\), by \(+6.7\) points for Llama with \([0.0,16.7]\), and
by \(0.0\) points for Nemotron.

Six contrasts were practically equivalent across all four models. Each was an
executed-FAR comparison for separation of duties or quorum. Their invalid
false proofs remained below the authority cut and were blocked by the common
fail-closed gate in every topology. Free-running communication therefore
induces measurable semantic drift and model-specific safety responses, but
multi-principal authorization with runtime proof enforcement prevents those
responses from becoming a replicated topology-dependent execution effect in
this setting.

### 3.7 Targeted Authority Mechanism Ablations

The targeted study completed all 1,200 formal calls with 1,201 provider
attempts. All four model blocks passed the frozen integrity and parent-validity
gates. The final rows contain no missing or duplicate episodes, unresolved
provider errors, malformed or truncated outputs, proof or score mismatches, or
invalid-proof executions.

Stale signed replay was the only intervention with a replicated large advisory
effect. Relative to the same-task valid signed reference, advisory FAR fell by
73.3 points for GPT-5.4 with a 95% interval of
\([-90.0,-56.7]\), 40.0 points for Claude Sonnet 5 with
\([-56.7,-23.3]\), and 33.3 points for Nemotron 3 Super 120B with
\([-50.0,-16.7]\). Llama 4 Maverick changed by \(-3.3\) points with
\([-16.7,6.7]\). The direction therefore replicated in three models without
becoming a universal four-model response.

Source-verifier identity exchange was the only intervention whose advisory
effect satisfied the frozen \(\pm10\)-point practical-equivalence rule in all
four models. Its paired estimates were 0.0 points for GPT-5.4, Claude Sonnet 5,
and Nemotron 3 Super 120B, and \(-3.3\) points for Llama 4 Maverick. Repeated
same-principal signatures, missing scope or freshness, and a missing quorum
share produced large effects only in one or two models. Duplicated unsigned
claims, natural-language consensus, randomized authority labels, and moving
the compromised share below the cut produced no replicated large advisory
effect.

The execution result was uniform even when advisory behavior was not. Across
the eight invalid-proof interventions, maximum enforced FAR was 0% in every
model. Exact proof semantics can influence an LLM's advisory choice, especially
for stale replay, but behavioral recognition is not a reliable cross-model
enforcement mechanism. Deterministic proof verification supplies that
execution boundary.

### 3.8 Independent Schedule Replication

The independent schedule replication completed all 2,880 episodes and 20,160
assigned calls with 20,321 provider attempts including retries. All four model
blocks passed the frozen gates. Active-forward failure rates were at most
0.30%, executor failure rates were at most 0.28%, and no invalid proof
authorized a protected execution.

The replication preserved the cross-model result. Neither the parent B2
schedule nor the replication produced a large total topology effect in at
least three models, and neither produced a replicated large semantic increment
over B1. The paired schedule-difference analysis also found no replicated
large effect. Three differences were model-conditional and all concerned
true-state utilization. GPT-5.4 shifted by \(+23.3\) points for `topo_B` SoD
and \(-23.3\) points for `topo_D` quorum; Claude Sonnet 5 shifted by
\(-16.7\) points for `topo_C` quorum. Six of 27 schedule-difference contrasts
were practically equivalent across all models, all of them SoD/quorum
executed-FAR contrasts.

Changing request order therefore did not create a replicated communication-
topology ranking. The exact utility response remains model-conditional, while
fail-closed multi-principal execution remains stable across the two schedules.

### 3.9 Authority-Composition Control Sensitivity

The original Authority Composition Study A gate counted any control response
without task success as a failure. GPT-5.4 exceeded the 5% limit with 17 of
240 failures, and Llama 4 Maverick exceeded it with 24 of 240. All 41 responses
selected `stop_without_progress`; none selected the protected action or
violated the snapshot-only false state.

We applied the responsiveness rule later used in the fresh Runtime Enforcement
factorial without changing the parent rows. This rule requires at least 85%
control progress, at most 5% false-control violation, at most 2% malformed or
truncated responses, and unchanged integrity checks. Control progress was
92.9% for GPT-5.4, 99.2% for Claude Sonnet 5, 100% for Nemotron 3 Super 120B,
and 90.0% for Llama 4 Maverick; false-control violation was zero in every
model. All four blocks pass this post-hoc sensitivity rule.

The sensitivity does not change the parent preregistration. It instead shows
that the original invalidity arose from conservative abstention rather than
unsafe control execution. The authority-cut response remains model-dependent.
Positive task-bootstrap intervals appeared in three models for verifier-single
and source-verifier separation of duties, but in two models for quorum. No
threshold contrast replicated in all four models.

## 4. Discussion and Limitations

### 4.1 What sets the executable safety boundary

The experiments distinguish three mechanisms that complete-architecture
comparisons merge. Communication paths control how claims and proofs are
transmitted. Authority composition controls whether a coalition can construct
a policy-valid proof. Runtime enforcement controls whether an invalid proof
can trigger a protected action. The matched and free-running interventions
show that changing \(G_C\) can alter message form and model behavior without
creating a replicated large execution effect once \(G_A\), \(G_E\), and the
fail-closed gate are fixed. The authority studies explain why: the structural
threshold lies in \(\kappa_A\), while the executable guarantee comes from
checking the resulting proof at the action boundary.

This separation also clarifies what multi-principal authorization does not
guarantee. Raising \(\kappa_A\) prevents a below-cut adversary from producing a
valid proof, but it does not force an LLM to recognize that invalidity.
Advisory FAR below the cut remained high for some models, and no threshold
contrast had a positive interval in all four model blocks. Conversely, the
deterministic gate reduced invalid-proof executed FAR to zero even when the
executor's advisory choice was unsafe. Authority composition and runtime
verification therefore address different failure modes and should be
evaluated separately.

### 4.2 Evidence scope

The evaluation uses programmatically specified synthetic tasks with executable
state, proof, and action predicates. This design provides deterministic labels
without human or model judges and supports controlled interventions on the
three graphs. It does not estimate the prevalence of these failures in deployed
workflows, human preferences, or behavior under untested communication
instructions and budgets.

The authority-placement result remains development evidence because one of
three model blocks failed its preregistered control gate. Authority Composition
Study A likewise retains its original failed four-model gate: GPT-5.4 and
Llama 4 Maverick made 41 safe no-progress control choices above the exact
task-success threshold. The post-hoc responsiveness analysis explains those
failures but does not replace the preregistered rule. The fresh runtime
factorial, matched communication studies, targeted ablations, and schedule
replication passed their frozen four-model gates and provide the main
cross-model evidence.

The free-running replication changes request order but cannot reproduce model
sampling exactly because the provider exposes no sampling seed. Its result
therefore supports schedule robustness, not deterministic replication. The
reported conclusions are further limited to the evaluated model versions,
synthetic task families, proof language, action space, and fail-closed
implementation.

## 5. Conclusion

The experiments separate communication structure from the authority and
execution mechanisms that convert a claim into a protected state change.
Matched and free-running communication interventions produced no replicated
large topology ranking across four models, and an independent execution
schedule preserved that result. In contrast, the authority cut determines
whether an adversary can construct a policy-valid proof, while deterministic
fail-closed verification prevents invalid proofs from crossing the execution
boundary. Advisory responses to the cut varied by model and authority regime;
the data do not support a universal behavioral safety–utility improvement from
increasing authority composition alone. The evaluated evidence therefore
supports a structural and enforced-execution mechanism: independent authority
raises the proof-forgery threshold, and runtime verification turns that
threshold into an executable safety boundary.
