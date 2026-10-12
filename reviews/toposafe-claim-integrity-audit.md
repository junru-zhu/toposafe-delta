# TopoSafe-Delta Claim Integrity Audit

**Mode:** Full claim, numeric, terminology, and existing-citation audit.  
**Audit date:** 2026-10-07.  
**Manuscript:** `manuscript/toposafe-delta.md`.  
**Final status:** PASS after repairs. No blocking claim-evidence mismatch remains.

## Artifacts checked

- Authority Placement v1.6 frozen report and validation output.
- Authority Composition v0.2 Study A and threshold results.
- Runtime Enforcement v0.1 and v0.2 results.
- Matched Communication B1 and Free-Running Communication B2 results.
- Targeted Authority Mechanism Ablations results.
- Free-Running Schedule Replication results.
- Authority Composition Control Sensitivity results.
- `docs/toposafe-authority-topology-paper-plan.md`.
- `ccfa.yaml`.
- The four works already cited in the manuscript, checked against their
  ACL Anthology or arXiv primary pages.

## Claim-evidence matrix

| Claim | Evidence | Audit status |
| --- | --- | --- |
| Communication, authority, and execution must be intervened on separately to identify their safety effects. | Three-graph design; matched B1 and free-running B2 interventions. | Supported in the evaluated synthetic design. |
| Authentication can raise both FAR and TUR without improving hidden-truth discrimination. | Authority Placement v1.6; Claude and Nemotron passed the frozen validity gate; TCG remained between -0.042 and +0.042. | Supported as development evidence in two valid model blocks. |
| Moving one authenticated authority has no stable advantage when the cut remains one. | Authority-placement interaction contrasts for Claude and Nemotron. | Supported as development evidence, not a universal placement theorem. |
| Authority cut identifies the compromise threshold at which a false proof becomes policy-valid. | Proof construction and deterministic verification across compromise budgets \(c=0,1,2\). | Structurally supported. |
| LLM advisory behavior follows the authority-cut threshold uniformly. | Authority Composition v0.2 and the zero-call sensitivity analysis. | Unsupported as a universal claim; no threshold contrast has a positive interval in all four models. Excluded from the final claim. |
| Fail-closed verification prevents invalid proofs from reaching protected execution. | Runtime Enforcement v0.2 fresh factorial; all four model gates passed; enforced FAR on invalid false proofs was 0%. | Supported in the evaluated task family. |
| Denied invalid-proof attempts can recover to safe progress. | Runtime Enforcement v0.1: 697/697; v0.2: 257/257 triggered recoveries selected safe progress. | Supported for the designated one-turn recovery protocol. |
| Frozen-message topology has no stable large effect after authority, execution, content, traffic, and budgets are matched. | B1: zero preregistered large effects; 26/27 contrasts met the cross-model practical-equivalence rule. | Supported in the evaluated synthetic task family. |
| Free-running topology changes message form without a replicated large safety ranking. | B2: semantic drift in all models; zero cross-model replicated large topology effects or semantic increments. | Supported; model-conditional effects remain. |
| The topology result is robust to the tested request schedule. | Schedule replication: zero replicated large total, semantic-increment, or schedule-difference effect; 6/27 schedule differences equivalent. | Supported as schedule robustness, not deterministic sampling replication. |
| Exact proof defects affect advisory behavior inconsistently, while deterministic verification blocks invalid execution. | Ten targeted ablations; stale replay replicated in three models; all invalid-proof enforced FAR values were 0%. | Supported. |
| The two invalid Study A blocks failed through unsafe control execution. | Control sensitivity audit of all 41 exact failures. | Contradicted by the rows: all 41 were safe no-progress choices with zero false-control violations. The final manuscript states the corrected interpretation. |

## Numeric consistency findings

The six-component core intervention ledger is:

\[
6{,}720 + 720 + 12{,}480 + 20{,}160 + 20{,}160 + 1{,}200
= 61{,}440.
\]

The complete formal-call total reported by the manuscript is:

\[
61{,}440 + 1{,}008 + 697 + 2{,}688 + 257
= 66{,}090.
\]

The 61,440 count excludes the Authority Placement development study and both
runtime-enforcement extensions. The manuscript now labels it as the core
intervention ledger rather than the full paper total. It also excludes 6,480
deterministic gate replays and 84 development smoke calls from the formal model
call count.

All result-table values, control-failure counts, equivalence counts, recovery
counts, provider-attempt counts, and confidence intervals checked against the
frozen result JSON/Markdown files. One rounding mismatch was repaired:
Llama 4 Maverick B2 `topo_A` mean similarity is 0.989, not 0.990.

## Existing-citation findings

- NetSafe resolves to the ACL 2025 Findings paper and supports the statement
  that canonical multi-agent communication topologies are compared for
  harmful-information propagation.
- G-Safeguard resolves to the ACL 2025 paper and supports the statement that
  utterance graphs are used for topology-guided detection and intervention.
- Architecture Matters resolves to arXiv:2604.23459 and supports the statement
  that communication topology, roles, and memory organization are studied
  jointly. The previous OpenReview URL was unavailable and was replaced by the
  stable arXiv primary page.
- MasDrift resolves to arXiv:2608.07556 and supports the statement that
  authorization preservation is evaluated across single-agent, centralized,
  and decentralized architectures. The manuscript's earlier `hybrid` wording
  was corrected during the audit.

The manuscript uses these works to establish a conditional joint gap. It does
not claim absolute priority.

## Validity and terminology findings

- `authority cut` consistently denotes a structural property of the
  authorization protocol, not an LLM behavioral guarantee.
- `advisory FAR` and `executed FAR` are kept separate.
- Authority Placement v1.6 remains development evidence because GPT-5.4 failed
  its preregistered control gate.
- Authority Composition Study A remains a failed four-model confirmatory gate;
  the post-hoc responsiveness analysis does not replace the preregistered rule.
- No human review or model judge supplies task labels, scores, case selection,
  or experiment-validity decisions.
- The evaluated scope is synthetic executable tasks; deployed prevalence and
  human preference are not estimated.

## Validation record

- Relevant TopoSafe test suite: 56 passed.
- Full repository regression: 216 passed and 2 unrelated legacy SwarmSafe
  packaging tests failed. One requires the absent external file
  a local reviewer response file that is not included here; the other reports a
  nested Phase 3D.3 ZIP reproduction-hash mismatch. Neither test reads the
  TopoSafe manuscript or result packages changed in this audit.
- Python source and analysis scripts: compilation passed.
- Frozen validators reproduced 1,008/1,008 placement rows and the expected
  GPT-5.4 control-gate failure.
- Frozen validators reproduced 6,720/6,720 Study A rows and the expected GPT
  and Llama control-gate failures.
- Threshold, Runtime Enforcement v0.1, Runtime Enforcement v0.2 initial and
  recovery, B1, B2, targeted ablations, and schedule replication validators all
  passed with complete expected row counts.
- Abstract audit: one paragraph, 195 words, no warnings.
- Manuscript prose audit: 4,412 prose words, no em dashes; two non-blocking
  rhythm/punctuation advisories.
- YAML parsing and current internal Markdown links passed.

## Severity and disposition

Before repair, the audit found one major reporting ambiguity (61,440 described
as the full-study total), one stale citation URL, one citation-context category
mismatch, one numeric rounding mismatch, and a manuscript structure that still
read as a project status report. All were repaired in the canonical
manuscript. No raw result, protocol, or frozen experimental artifact was
changed to obtain the pass.

## No-invention status

No result, citation, model behavior, confidence interval, or experiment status
was invented. Unsupported universal advisory-response language was removed
rather than repaired by extrapolation.
