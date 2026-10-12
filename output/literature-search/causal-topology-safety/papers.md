# Closest-Work Audit: Authority Topology in Multi-Agent Safety

**Search date:** 2026-10-06  
**Purpose:** Ground the TopoSafe-Delta research gap and experiment design.  
**Source policy:** Primary arXiv, OpenReview and ACL Anthology pages; no
policy-excluded sources.

## Verdict

The broad topic is covered. Existing work already shows that communication
architecture, topology, roles, memory, delegation depth and attacker position
can change multi-agent safety or authorization behavior.

The defensible opportunity is narrower:

> Causally separate communication topology, authority topology and execution
> topology under matched messages, resources and executable outcomes.

The strongest closest work is MasDrift. It directly studies authorization
preservation across multi-agent architectures, but its architecture conditions
jointly change delegation depth, agent count, handoffs and tool exposure.
Architecture Matters is the strongest broad empirical architecture comparison.
Neither work models the communication, authorization and execution relations as
three separately intervenable graphs.

## Closest Papers

| Paper | Status | What it establishes | Remaining difference for TopoSafe-Delta |
| --- | --- | --- | --- |
| [MasDrift: Benchmarking Authorization Preservation Across Multi-Agent Architectures](https://arxiv.org/abs/2608.07556) | arXiv preprint, submitted 2026-08 | Evaluates authorization drift across centralized, decentralized and hybrid architectures; compares chain propagation with source re-anchoring | Scale-up conditions bundle delegation depth, agent count, handoffs and tool exposure; does not separately intervene on communication, authority and execution graphs or use paired hidden state truth |
| [Architecture Matters for Multi-Agent Security](https://openreview.net/forum?id=1BKKFT4glq) | ICML 2026 | Studies security and task performance across configurations varying role, communication topology and memory | Establishes configuration dependence, but multiple architectural factors vary and authority proofs are not isolated as a separate graph |
| [NetSafe: Exploring the Topological Safety of Multi-agent Systems](https://aclanthology.org/2025.findings-acl.150/) | Findings of ACL 2025 | Compares multi-agent safety behavior under multiple graph structures and harmful-information settings | Canonical graph comparisons change path, degree, exposure and centrality together; endpoint is not paired executable false-state acceptance |
| [G-Safeguard: A Topology-Guided Security Lens and Treatment on LLM-based Multi-agent Systems](https://aclanthology.org/2025.acl-long.359/) | ACL 2025 | Constructs utterance graphs, detects malicious nodes and performs topology-guided remediation | Defense after anomaly detection, not causal decomposition of routing, authorization and execution |
| [From Spark to Fire: Modeling and Mitigating Error Cascades in LLM-Based Multi-Agent Collaboration](https://arxiv.org/abs/2603.04474) | arXiv preprint, submitted 2026-03 | Models error propagation as a function of graph influence and role-conditioned susceptibility | Cascade model does not identify who is authorized to mutate protected state or test authority-cut thresholds |
| [MASTER: Multi-Agent Security Through Exploration of Roles and Topological Structures](https://aclanthology.org/2025.findings-emnlp.917/) | Findings of EMNLP 2025 | Jointly uses role and topology information for attacks and defenses | Does not balance authority-to-node placement or use deterministic protected-state outcomes |
| [Don't Trust Your Upstream: Exploiting LLM Multi-Agent System via Topology-Guided Adversarial Propagation](https://arxiv.org/abs/2512.04129) | arXiv preprint, submitted 2025-12 | Routes adversarial content through multi-hop agent paths toward downstream agents | Attack-specific propagation study; does not estimate normal-operation authority or matched routing effects |

## What Is Already Covered

- Canonical topology comparisons.
- Role- and topology-aware attacks.
- Topology-aware monitoring and defense.
- Authorization drift across architecture families.
- Multi-hop prompt-injection propagation.
- Graph-based cascade modeling.

Another star-versus-chain ranking is not a sufficient paper contribution.

## Remaining Joint Gap

No inspected work was identified that jointly provides:

1. three explicit structures:
   - communication graph \(G_C\);
   - authority graph or hypergraph \(G_A\);
   - execution graph \(G_E\);
2. matched interventions changing only one structure;
3. byte-identical executor-facing state-claim bodies across paired true/false
   worlds;
4. hidden executable ground truth;
5. deterministic protected-state outcomes;
6. FAR, TUR, TCG and safe-progress measurement;
7. single authority versus separation-of-duty/quorum comparison;
8. a compromised-principal threshold test.

The novelty claim must remain conditional:

> Within the inspected public literature, no study was identified that
> causally separates communication, authority and execution topology under a
> matched executable-state protocol.

## Mechanism Opportunity

Define the authority cut \(\kappa_A(x)\) of protected transition \(x\) as the
minimum number of independent compromised principals required to produce a
policy-valid authorization proof for \(x\).

This creates a discriminating prediction:

- moving a single authority changes placement but leaves
  \(\kappa_A=1\);
- independent 2-of-2 or 2-of-3 authorization raises \(\kappa_A\);
- the safety benefit should exist when adversary budget
  \(c<\kappa_A\);
- the benefit should disappear when \(c\ge\kappa_A\).

This threshold behavior distinguishes a real authority-structure mechanism from
prompt wording, majority-language preference or duplicated signatures.

## Positioning Against the Two Closest Papers

### Versus MasDrift

MasDrift asks whether authorization is preserved across architecture families.
TopoSafe-Delta asks which layer of architecture causes the change.

The required differentiators are:

- fixed task and action space;
- fixed communication and execution graphs when changing authority;
- fixed authority and execution graphs when changing communication;
- paired hidden truth;
- exact message-body matching;
- executable FAR/TUR outcomes;
- authority-cut threshold ablation.

### Versus Architecture Matters

Architecture Matters establishes that role, topology and memory configurations
matter. TopoSafe-Delta is not another broad architecture sweep. It identifies a
specific confounding problem and estimates three separate graph effects.

## Baseline Implications

A credible paper should include:

- unmatched canonical topology ranking;
- matched topology ranking;
- unsigned claim;
- identity-only single authority;
- central verifier;
- source re-anchoring;
- scoped capability;
- separation of duties;
- independent quorum;
- topology-aware guard.

The paper should compare structural safety primitives rather than claim a
universal best graph.

## Search Boundary and Refresh Risk

- Recent 2026 preprints may change title, scope or publication status.
- Metadata correction on 2026-10-07: arXiv:2609.12113 and arXiv:2509.18415
  were unrelated papers and were removed. The topology-guided attack row now
  points to the verified arXiv:2512.04129 record.
- The search supports a medium-high-confidence joint gap, not an absolute first
  claim.
- MasDrift and any new work using terms such as authorization graph, delegation
  graph, capability topology, threshold authorization or agent provenance must
  be rechecked before submission.
