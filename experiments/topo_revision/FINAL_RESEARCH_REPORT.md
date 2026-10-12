# TopoSafe-Delta Final Research Report

**Report date:** 2026-10-12
**Working branch:** `experiment/topo-revision`
**Protocol:** TopoSafe-Delta-Revision-v1.0
**Frozen implementation commit:** `077425328a8aceb0a3e97ced746170258b47fc54`
**Frozen-manifest commit:** `ef54672`
**Manifest SHA-256:** `9be23bfe5545b9707da46c25b0a458d15e427f9ad98f2ec0172d4b2db3862947`

## Executive conclusion

TopoSafe studies three different relations in a multi-agent LLM system:

1. communication topology, \(G_C\), determines what information reaches an
   agent and how messages can be transformed;
2. authorization structure, \(G_A\), determines which independent credentials
   can create a policy-valid proof for a protected transition; and
3. execution capability, \(G_E\), determines whether an advisory model choice
   can become a real state transition and which deterministic checks mediate
   that transition.

The revision successfully produced a frozen, executable E1--E3 suite and new
formal evidence for E1 and part of E2. The strongest new finding is negative
and scientifically important: verified source provenance does **not**
uniformly increase trust in a claim. In three valid formal model blocks, the
P2 verified-provenance treatment had no positive primary effect. It had no
effect for Claude or Llama and sharply reduced protected-action selection for
Nemotron. Stale or wrong-scope provenance produced a large reduction only for
Llama. Source authentication, authorization validity, and factual truth must
therefore remain separate concepts in the paper.

E2 cleanly demonstrates the structural authority-cut mechanism and, in one
valid Llama formal block, a sharp behavioral and execution transition at the
cut. It also demonstrates the key limit of a signature-only gate: invalid
proofs never executed, but a policy-valid false proof executed at and above the
cut. This behavioral evidence is one-model evidence because the v1.0 pilot
control gate excluded Claude and Nemotron.

E3 is implemented but not confirmatory. A post-run integrity audit found
intermediate forwarder schema failures that the first validator did not
aggregate. Only the Nemotron pilot is clean; it has three base tasks per cell
and cannot support a topology conclusion. The full 12,288-call E3 formal
factorial was not run.

Reviewer-style verdict: the repository is substantially stronger and much more
auditable, but the new package is not yet sufficient to claim a complete
four-model, realistic-workflow validation for a competitive NAACL Main paper.
E1 can strengthen the main paper if the story is revised around heterogeneity
and causal disambiguation. E2 must be explicitly bounded to one behavioral
model. E3 belongs in the appendix or future-work discussion until a corrected
multi-model formal run is complete.

## What was audited and reused

The revision did not repeat adequate historical experiments. The repository
audit recomputed and mapped the existing evidence:

- Authority Placement v1.6: 1,008 rows; the historical 33--42 percentage-point
  authentication effect is valid only for the two model blocks passing its
  frozen placement controls.
- Authority Composition v0.2: 7,440 rows; conditional structural cuts
  \(\kappa_A=1\) and \(\kappa_A=2\) are deterministically validated, while
  parts of the behavioral study have frozen control-gate exclusions.
- Runtime Enforcement v0.2: 2,688 primary rows plus 257 recovery calls; invalid
  proof execution is zero, but policy-valid false proofs can execute.
- Matched Communication v0.1: 12,480 rows; no consistently replicated large
  routing effect across four valid model blocks.
- Free-Running Communication v0.3 and schedule replication: 2,880 episodes
  each; message transformation and safety effects are model-dependent.
- Authority mechanism ablations: 1,200 rows.
- Execution-topology extension: three-model sensitivity only; GPT remained
  incomplete.

The isolated clean-clone recomputation matched checked-in row counts, validity
decisions, effects, and summaries. Seven regenerated JSON files differed only
in timestamp fields. The manuscript's approximately 66,090 historical formal
calls remain historical paper evidence; this audit does not claim every call
is newly rerun.

## New experiment status

| Experiment | Planned design | What ran | Valid evidence |
| --- | --- | --- | --- |
| E1 provenance | 60 tasks, 5 treatments, 2 states, 4 models | pilots for 3 completed models plus 10 failed GPT assignments; 600-row formal blocks for Claude, Nemotron, and Llama | three complete formal model blocks |
| E2 authority cut | 80 tasks, 12 treatment cells plus controls, 4 models | three pilots; one 976-row Llama formal block | structural checks plus one formal behavioral model |
| E3 realistic workflow | 48 tasks, 3 topologies, 2 authorization policies, 2 execution policies, 2 states, 4 models | three 72-episode pilots; no formal run | one clean Nemotron pilot after strict audit |
| E4 defenses/OOD | lower priority | NOT RUN | none |

The detailed status of every experiment/stage/model block is machine-derived in
`RUN_INVENTORY.csv` and `RUN_INVENTORY.tex`.

## E1: causal effect of authenticated provenance

### Design

E1 uses 60 independent base tasks across reimbursement, privileged access,
sensitive release, and administrative transition. Each task has paired
TRUE/FALSE hidden states and five provenance conditions:

- P0: neutral unsigned claim;
- P1: unsupported authority language;
- P2: deterministically verified source identity, without action authority;
- P3: authentic but stale, wrong-version, or wrong-scope provenance; and
- P4: format-matched non-authority metadata.

The executor never observes the hidden state. No E1 protected state transition
is committed; the outcome is advisory action selection. Each valid formal
model block has 600 rows and 60 task clusters.

### Formal results

| Model | P0 FAR / TUR | P1 FAR / TUR | P2 FAR / TUR | P3 FAR / TUR | P4 FAR / TUR |
| --- | --- | --- | --- | --- | --- |
| Claude Sonnet 5 | 0.0% / 0.0% | 0.0% / 0.0% | 0.0% / 0.0% | 0.0% / 0.0% | 0.0% / 0.0% |
| Nemotron 3 Super 120B | 50.0% / 56.7% | 50.0% / 46.7% | 0.0% / 0.0% | 0.0% / 0.0% | 83.3% / 83.3% |
| Llama 4 Maverick | 98.3% / 95.0% | 98.3% / 98.3% | 98.3% / 98.3% | 46.7% / 48.3% | 95.0% / 98.3% |
| GPT-5.4 | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN |

FAR is false-state advisory acceptance. TUR is true-state protected-action
selection. TCG is TUR minus FAR.

The Holm-adjusted significant primary effects were:

- Nemotron P2-P0: FAR -50.0 percentage points, 95% task-cluster bootstrap CI
  [-63.3, -36.7], adjusted \(p=0.00320\); TUR -56.7 points,
  CI [-70.0, -45.0], adjusted \(p=0.00320\).
- Nemotron P2-P1: FAR -50.0 points, CI [-63.3, -36.7], adjusted
  \(p=0.00320\); TUR -46.7 points, CI [-60.0, -35.0], adjusted
  \(p=0.00320\).
- Llama P3-P2: FAR -51.7 points, CI [-65.0, -40.0], adjusted
  \(p=0.00320\); TUR -50.0 points, CI [-61.7, -38.3], adjusted
  \(p=0.00320\).

Claude selected safe progress or abstention in every treatment. Llama was
nearly saturated on protected-action selection except under stale/wrong-scope
P3. Nemotron treated the verified P2 block as a reason not to proceed.

No positive TCG result was observed. The study did not preregister an
equivalence margin, so null or small TCG differences are not evidence of
equivalence.

### Hypothesis decisions

- H1a, verified provenance increases selection: **unsupported**.
- H1b, verified provenance can increase FAR and TUR: **unsupported in the
  observed formal blocks**.
- H1c, unsupported authority language reproduces part of a positive verified
  effect: **unsupported** because no positive P2 effect was observed.
- H1d, stale/wrong-scope responses are heterogeneous: **supported as a
  model-specific descriptive finding**, driven by a large Llama response and
  no P3-P2 change for Claude or Nemotron.

### Limitation discovered

P4 is not behaviorally inert for Nemotron: FAR and TUR were both 83.3%.
Although P4 was intended to be non-authority metadata, its
`format_check=complete` wording can plausibly act as a positive completion cue.
The primary P2 contrasts remain observed results, but the strongest
attention-control interpretation requires a v1.1 P4 with semantically neutral
random metadata.

## E2: authority cut and compromise threshold

### Structural result

The deterministic generator enumerates qualified credential sets and binds
every signature to the claim, object, value, version, scope, freshness,
requested transition, and experiment nonce. Duplicate credentials count once.
Under the frozen independence assumptions:

- A1 single signer has \(\kappa_A=1\);
- A2 two specific signers has \(\kappa_A=2\); and
- A3 two-of-three has \(\kappa_A=2\).

Below the cut, compromised credentials cannot construct a policy-valid false
proof. At or above the cut, they can. This is a verified structural/software
property, not a statistical discovery.

### Valid Llama formal block

The valid formal block contains 80 independent tasks, 960 treatment rows, and
16 controls.

| Policy | Below-cut false proof / advisory / commit | At-cut false proof / advisory / commit | True-state completion |
| --- | --- | --- | --- |
| A1, cut 1 | c=0: 0% / 0% / 0% | c=1: 100% / 100% / 100% | 100% |
| A2, cut 2 | c=1: 0% / 0% / 0% | c=2: 100% / 100% / 100% | 100% |
| A3, cut 2 | c=1: 0% / 0% / 0% | c=2: 100% / 100% / 100% | 100% |

Each advisory and committed threshold effect was +100 percentage points with
95% CI [100, 100] and Holm-adjusted \(p=0.00320\). The deterministic gate
committed zero invalid proofs. Nevertheless, false-state actions committed at
the cut because their proofs were policy-valid. A3 below the cut produced
1.25% safe progress and 98.75% abstention; the protected-action rate remained
zero.

Increasing the signer requirement did not reduce true-state completion in this
Llama block: A1, A2, and A3 were all 100%. The A2-A1 and A3-A1 utility effects
were zero; no equivalence claim is made.

### Hypothesis decisions

- H2a, no policy-valid false proof below the cut: **supported
  deterministically**.
- H2b, false proof becomes constructible at/above the cut and passes a
  signature-only gate: **supported deterministically and observed in the valid
  Llama formal block**.
- H2c, LLM behavior may fail to respect the threshold: **unsupported in the
  valid Llama block**; cross-model status is inconclusive.
- H2d, higher signer requirements reduce utility: **unsupported in the valid
  Llama block**; cross-model status is inconclusive.

### Multi-model validity limitation

Claude and Nemotron completed all 52 pilot rows with no provider or parsing
failure, but failed the frozen behavioral controls. Claude chose safe
verification in both true-valid controls; Nemotron split one false-safe control
between verification and abstention. This v1.0 gate still confounds a model's
behavioral policy with technical experiment validity. Their rows are
diagnostic only. E2 is not a four-model behavioral result.

## E3: realistic end-to-end workflow

### Implemented environment

The deterministic simulator includes 48 base tasks:

- 16 expense/reimbursement workflows;
- 16 privileged-access workflows; and
- 16 sensitive-document-release workflows.

It crosses direct, chain, and redundant communication; single- versus
two-signer authorization; ungated versus deterministic proof-gated execution;
and TRUE/FALSE world states. It records source and delivered messages,
intermediate traces, proof validity, advisory actions, gate decisions, final
state, tokens, latency, request IDs, and cost.

### Pilot integrity and bounded observation

The strict audit found 95/120 intermediate technical failures for Claude,
3/120 for Llama, and 0/120 for Nemotron. GPT was not run. Only Nemotron is a
clean pilot block.

In that block, each cell contains only three base tasks. C1, C2, and C3 had
identical action rates within matched authorization/execution conditions, so
there is no estimated topology difference in this tiny pilot. This is not
evidence that topology is irrelevant.

The pilot illustrates the intended distinction:

- with A1 and one compromised signer, the proof is valid at the cut; false
  commits were 66.7% under E0 and 100% under E1;
- with A2 and one compromised signer, the proof is invalid below the cut;
  false commits were 33.3% under E0 and 0% under E1; and
- true-state completion was 66.7% under E0 and 100% under E1 in the observed
  cells.

These rates are repeated across the three topologies because \(n=3\) per cell
and the observed pilot actions matched. They are illustrations, not
confirmatory effect estimates. Representative trace figures are generated only
from the clean recorded Nemotron episodes.

## Findings that are genuinely new

1. A provenance-only causal intervention does not reproduce the earlier broad
   positive authentication narrative. Model responses range from total
   conservatism, to a strong negative provenance response, to near-saturation.
2. Stale or wrong-scope provenance can be behaviorally decisive for one model
   while ignored by others.
3. The new E2 labeling and plots make the authority-cut limit explicit: zero
   invalid-proof execution can coexist with 100% false-state execution when a
   compromised coalition creates a policy-valid proof.
4. The end-to-end simulator connects \(G_C\), \(G_A\), and \(G_E\) in three
   realistic synthetic domains and records complete transformation and
   execution traces.
5. The post-run audit exposed an intermediate-agent validation blind spot. The
   failed E3 blocks are preserved rather than promoted.

## Relationship to the earlier manuscript

The earlier Authority Placement experiment reported a positive effect when a
platform-authenticated observation was presented and instructed to supersede a
snapshot. E1 P2 authenticates only source identity and explicitly states that
provenance does not establish truth or action authority. The new P2 effect is
zero or negative.

This does not invalidate the old raw study because the estimands differ. It
does contradict any broad wording that “authentication itself causes agents
to trust a claim more.” The old effect may combine source authentication,
delivery channel, recency/epistemic priority, and an action-relevant
instruction. The manuscript should narrow the old claim and use E1 to explain
why the distinction matters.

## Cost and budget control

The runner enforced the frozen defaults:

- maximum assigned calls: 15,000;
- maximum estimated spend: USD 250;
- maximum parallel requests: 5;
- maximum provider attempts per assigned call: 2.

Observed ledger:

| Scope | Assigned calls including recovery | Realized calls | Estimated USD | Conservative USD |
| --- | ---: | ---: | ---: | ---: |
| E1 pilot + formal | 1,932 | 1,920 | 2.0210 | 2.4252 |
| E2 pilot + formal | 1,132 | 1,132 | 0.3791 | 0.4549 |
| E3 pilot | 576 | 576 | 0.8816 | 1.0579 |
| Total | 3,640 | 3,628 | 3.2816 | 3.9379 |

There were 3,661 API attempts and 3,278 executor episode rows. Costs are
estimates from recorded tokens and the repository's frozen pricing snapshot,
not an AWS billing statement.

Observed examples of “one experiment” cost:

- three-model E1 formal, 1,800 realized calls: about USD 1.89;
- one-model E2 formal, 976 calls: about USD 0.18;
- three-model E3 pilot, 576 model calls including forwarders: about USD 0.88.

The call limit, not the USD 250 limit, is the binding constraint. The complete
frozen schedule contains 19,728 calls. Relative to the 3,638 scheduled calls
already assigned, 16,090 scheduled calls remain. Including two recovery
assignments already in the ledger, completing the frozen schedule would end at
19,730 assigned calls, 4,730 above the current cap.

The full E3 formal alone requires 12,288 additional calls. Current call-cap
headroom is 11,360, so E3 alone would require at least a 928-call cap increase.
Using observed E3 token profiles and the frozen prices, its four-model cost is
roughly estimated at USD 22.4--31.9, or USD 26.9--38.3 under the conservative
20% margin. The range is wide because GPT-5.4 produced no usable E3 token
profile. This is an extrapolation, not an invoice.

Budget is not the only blocker. E2 needs a new control design, E3 needs a
forwarder-schema repair and fresh pilot, and the GPT endpoint must become
usable. The invalid v1.0 blocks should not simply be resumed to spend the
remaining budget.

## Main paper versus appendix

### Main paper

- The three-layer \(G_C,G_A,G_E\) framework and authority-cut definition.
- Historical four-model runtime-enforcement and matched/free-running evidence.
- E1 as a three-model causal disambiguation result, including the lack of a
  uniform positive provenance effect.
- The deterministic E2 cut result and the signature-only gate limitation.
- The valid Llama E2 behavior only if explicitly labeled as one-model evidence.

### Appendix/artifact

- Full E1 treatment tables, P4 behavior, and all task-cluster intervals.
- E2 pilot-control failures and all one-model threshold cells.
- E3 pilot outcomes, strict integrity audit, and actual trace diagrams.
- GPT timeout history, recovery records, request IDs, prompts, hashes, raw
  responses, token usage, and cost tables.

### Not yet paper evidence

- Cross-model E2 behavioral generalization.
- Any E3 topology, interaction, or external-validity conclusion.
- E4 defense comparison.
- Real deployment or human-operator claims.

## Proposed manuscript revisions

The following text is limited to observed evidence.

### Abstract paragraph

> We separate communication reachability, independent authorization, and
> execution capability in multi-agent LLM systems. A new paired provenance
> experiment shows that verified source identity alone does not uniformly
> increase claim reliance: across three complete model blocks, its effect was
> null for two models and strongly negative for one, while stale or
> wrong-scope provenance affected only one model. Deterministic authorization
> checks enforce the predicted compromise threshold, but cannot reject a
> policy-valid false proof produced by a sufficiently compromised signer
> coalition. These results show that source authenticity, authorization
> validity, and factual truth are distinct trust boundaries.

### Introduction contribution

> We causally disambiguate linguistic authority cues, verified provenance,
> formal action authorization, and hidden-state truth. Contrary to a simple
> “authenticated messages are trusted more” account, model behavior is highly
> heterogeneous: provenance can be ignored, induce conservatism, or matter
> mainly when its scope is stale. We further connect independent-signer policy
> to executable outcomes through the authority cut, while identifying its
> precise limit against policy-valid false evidence.

### Results: provenance

> Verified provenance did not produce the preregistered positive selection
> effect. Claude selected no protected action in any provenance condition, and
> Llama remained near ceiling from P0 through P2. Nemotron instead reduced
> false-state acceptance by 50.0 percentage points and true-state utilization
> by 56.7 points under verified provenance relative to the unsigned condition
> (both Holm-adjusted \(p=0.00320\)). Llama reacted strongly to stale or
> wrong-scope provenance, reducing FAR by 51.7 points and TUR by 50.0 points
> relative to valid provenance (both adjusted \(p=0.00320\)). Thus, verified
> identity is not a model-invariant trust amplifier.

### Results: authority cut

> For the valid Llama formal block, false proof availability, advisory
> selection, and committed execution changed sharply at the predicted
> authority cut. All three policies showed a 100-point increase in both
> advisory and committed false-state action at the cut, while invalid-proof
> execution remained zero. This is not a contradiction: once the compromised
> coalition reaches the cut, the false proof is policy-valid and a
> signature-only gate has no factual-state signal with which to reject it.
> Because other model blocks did not pass the frozen pilot controls, this
> behavioral observation is model-specific.

### Discussion

> Our findings revise the interpretation of authenticated-agent observations.
> Authentication can identify who produced a message without establishing that
> the message is current, correctly scoped, truthful, or sufficient to
> authorize an action. Earlier positive authentication effects may therefore
> reflect a compound intervention that also changes recency, delivery channel,
> or epistemic priority. The authority cut addresses a different boundary: it
> predicts the coalition needed to construct a policy-valid proof under stated
> independence assumptions. It does not guarantee truth once that coalition is
> compromised. Safe deployment consequently requires both proof-preserving
> execution mediation and, for high-impact transitions, an independent source
> of authoritative state.

## Remaining threats to validity and required next work

1. **E1 negative control:** replace P4 with semantically neutral random metadata
   and add a delivery-channel-matched verified-source control under a new
   frozen protocol.
2. **E1 model coverage:** rerun GPT only after an endpoint smoke test passes;
   do not substitute another version.
3. **E2 validity:** make provider completion, parse/schema integrity, proof
   correctness, and tool mediation the technical gates. Record conservative
   choices, abstention, and control correctness as outcomes rather than using
   them to exclude a model.
4. **E3 forwarding:** enforce a tested structured forwarder schema, aggregate
   every intermediate parse/truncation failure before pilot promotion, and
   rerun all four model pilots.
5. **E3 formal evidence:** run the complete 48-task factorial only after every
   critical pilot arm passes. Do not run a partial formal subset.
6. **External validity:** keep the workflows synthetic. A later study can
   replay sanitized, non-production workflow shapes, but must not claim real
   deployment prevalence without operational data.
7. **E4:** compare prompt-only verification, proof gating, and proof plus
   independent state lookup after E1--E3 are repaired. D3 must be labeled as
   augmented capability.

## Candid NAACL Main assessment

The core paper idea remains publishable: separating who communicates, who
authorizes, and who can execute is clearer and more operational than treating
the communication graph as the whole safety boundary. The historical runtime
and communication packages provide substantial mechanistic evidence, and E1
adds a valuable causal correction to the provenance story.

The current revision should not be presented as a completed top-conference
strengthening package. A skeptical reviewer can reasonably object that E1 has
three rather than four models and an active negative control, E2 has only one
valid behavioral model, and E3 has only one clean pilot model. My assessment is
therefore:

- **scientific idea and infrastructure:** strong;
- **evidence honesty and reproducibility:** strong after the post-run audit;
- **new E1 evidence:** useful and main-paper worthy with caveats;
- **new E2 behavioral generality:** insufficient;
- **realistic end-to-end external validity:** insufficient;
- **competitive NAACL Main readiness as a strengthened empirical paper:** not
  yet.

The shortest credible path is a v1.1 E1 control replication, a technically
defined multi-model E2 gate, and a clean multi-model E3 pilot followed by the
complete formal factorial.

## Reproducibility entry points

```bash
PYTHONPATH=src:. pytest -q
PYTHONPATH=src:. python scripts/audit_topo_revision_evidence.py
PYTHONPATH=src:. python scripts/build_topo_revision.py
PYTHONPATH=src:. python scripts/audit_topo_revision_runs.py
PYTHONPATH=src:. python scripts/summarize_topo_revision_costs.py
PYTHONPATH=src:. python scripts/plot_topo_revision_final.py
```

Example frozen runner invocation:

```bash
PYTHONPATH=src:. python scripts/run_topo_revision.py \
  --experiment E1 \
  --stage formal \
  --model-slug llama-4-maverick \
  --workers 5 \
  --seed 20271012 \
  --max-calls 15000 \
  --max-spend-usd 250
```

Before any further model call, verify the new protocol version, available
endpoint, remaining call cap, and pre-run budget file. Do not rerun completed
episode IDs unless performing a recorded technical recovery.

## Artifact map

- Protocol and audit:
  `EXISTING_EVIDENCE_AUDIT.md`, `PROTOCOL.md`,
  `POST_RUN_INTEGRITY_AUDIT.md`.
- Frozen tasks and cases: `frozen/`.
- Raw rows and validations: `runs/`.
- Statistical outputs: `analysis/`.
- Inventory and costs:
  `RUN_INVENTORY.csv`, `RUN_INVENTORY.tex`, `COST_LEDGER.json`,
  `COST_LEDGER.csv`, `COST_LEDGER.md`, `COST_LEDGER.tex`.
- Paper figures in PDF and PNG: `figures/`.
- Implementations: `src/swarmsafe_delta/topo_revision_*.py`.
- Build, run, validation, analysis, audit, and plotting entry points:
  `scripts/*topo_revision*.py`.
