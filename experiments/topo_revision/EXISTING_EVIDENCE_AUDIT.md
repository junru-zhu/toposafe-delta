# TopoSafe-Delta Existing Evidence Audit

**Audit date:** 2026-10-12  
**Audited commit:** `0faa48d6423f298622fd9604c46ecd49a2cbdec8`  
**Branch for new work:** `experiment/topo-revision`  
**Historical formal-call total in the manuscript:** 66,090

## Audit method

The audit inspected the canonical paper, repository documentation, task
generators, frozen protocols and manifests, raw rows, validation reports,
analysis code, tests, and CI configuration. The baseline test suite passed:

```text
73 passed
```

The main analyzers were also executed in an isolated clean clone with
`PYTHONPATH=src`. Recomputed row counts, validity decisions, effect counts,
and reported summaries matched the checked-in evidence. Seven generated JSON
files differed only in one regenerated timestamp field; no numerical result
drift was found. An initial isolated-clone attempt without `PYTHONPATH=src`
failed with `ModuleNotFoundError`; this was an environment setup error, not an
experimental validity failure.

## Finding-to-artifact map

| Previously reported finding | Primary code and evidence | Recomputed? | Classification | Audit conclusion |
| --- | --- | --- | --- | --- |
| Authenticated provenance increases protected-action selection by about 33–42 percentage points in the valid signer-placement model blocks | `src/swarmsafe_delta/authority_placement.py`; `experiments/TopoSafe-Delta-AuthorityPlacement-v1.6/` | Yes | Implemented but scientifically insufficient for the revised provenance question | The 1,008-row study validates a platform-authentication effect for Claude and Nemotron. GPT failed its frozen control gate. The design does not separately include unsupported authority language, stale/wrong-scope provenance, or a format-matched non-authority control. |
| Moving one authority among source, relay, and verifier has no stable effect when the authority cut stays one | Authority Placement v1.6 analysis | Yes | Already implemented and validated, within its stated model boundary | Adequate for the narrow placement estimand. It should not be repeated as E1. |
| Independent signer policies increase the structural compromise threshold | `src/swarmsafe_delta/authority_composition.py`; Authority Composition v0.2 | Yes | Already implemented and deterministically validated | The proof constructor verifies the conditional cuts: single signer `kappa_A=1`; separation of duties and two-of-three quorum `kappa_A=2`. This is a structural software result, not a statistical discovery. |
| Executor advisory behavior changes around the authority cut | Authority Composition v0.2, threshold extension | Yes | Implemented but not a valid four-model confirmatory result | All threshold rows passed structural and provider checks, but the preregistered Study A control gate failed for GPT and Llama. Per-model patterns are bounded evidence only. A fresh experiment needs unambiguous safe-progress controls and prespecified validity gates. |
| A signature-only gate blocks invalid proofs but cannot reject policy-valid false proofs at or above the cut | `src/swarmsafe_delta/runtime_enforcement.py`; Runtime Enforcement v0.2 | Yes | Already implemented and validated | All four model blocks passed. Invalid-proof execution was zero. False-state execution remained possible when a compromised coalition produced a policy-valid proof. |
| Single-turn recovery after denial is safe in the tested interface | Runtime Enforcement v0.2 | Yes | Already implemented and validated, but narrow | The 257 recovery calls test one forced recovery turn only. They do not establish multi-turn recovery robustness. |
| Matched communication routing has no replicated large cross-model effect | `src/swarmsafe_delta/matched_communication_topology.py`; Matched Communication v0.1 | Yes | Already implemented and validated | 12,480 rows; all four model gates passed; zero replicated large effects. Adequate for the matched-message topology estimand. |
| Free-running routing transforms messages and creates model-conditional effects | `src/swarmsafe_delta/free_running_communication.py`; v0.3 | Yes | Already implemented and validated, but externally narrow | 2,880 episodes and 20,160 assigned calls passed all four model gates. Longer paths reduced semantic similarity, but effects were model-conditional and limited to the frozen synthetic workflow. |
| Schedule choice does not produce a stable topology ranking | Free-Running Schedule Replication v0.1 | Yes | Already implemented and validated | 20,160 assigned calls; zero replicated large schedule shifts. |
| Stale signed replay is a meaningful mechanism ablation | Authority Mechanism Ablations v0.1 | Yes | Implemented but scientifically insufficient for E1 | The ablation found one replicated large advisory effect, but it embeds stale replay inside a proof-ablation study. It is not a clean five-treatment provenance intervention. |
| Execution-capability placement extension | Execution Topology Confirmatory v0.1 and technical recovery packages | Yes, where data exist | Implemented but incomplete | Claude, Nemotron, and Llama are available as a three-model technical sensitivity. GPT timed out after bounded recovery. No four-model confirmatory execution-topology claim is allowed. |

## Evidence inventory

### Already implemented and validated

- Structural proof construction and authority-cut checks.
- Four-model Runtime Enforcement v0.2.
- Four-model Matched Communication v0.1.
- Four-model Free-Running Communication v0.3.
- Four-model free-running schedule replication.
- Four-model authority-mechanism ablations.
- Two valid model blocks for Authority Placement v1.6, with the failed GPT
  block retained.

### Implemented but not fully analyzed

- The three-model execution-topology extension is analyzed as a sensitivity,
  but it has not been integrated into the manuscript and cannot support a
  four-model replication claim.
- Existing raw rows expose token, latency, request, retry, and failure fields,
  but there is no single cross-study cost ledger.

### Implemented but scientifically insufficient

- Existing provenance evidence conflates trusted source authentication with
  authority language and lacks P1, P3, and P4 controls.
- Existing authority-composition behavioral evidence has a frozen strict
  control-gate failure for GPT and Llama.
- Existing workflows are deliberately synthetic and mechanism-isolating; they
  do not provide the requested realistic expense, access, and document-release
  external-validity study.
- Existing recovery is single-turn.

### Missing before this revision

- A five-condition provenance-only factorial with paired hidden states.
- A fresh authority-cut experiment with unambiguous control tasks and separate
  labels for invalid-proof execution and false-but-policy-valid execution.
- A deterministic three-domain end-to-end workflow crossing communication,
  authorization, execution enforcement, and hidden state.
- A unified revision budget ledger and call hard stop.
- Revision-specific paper-ready figures and machine-derived LaTeX tables.

### Unverifiable from available data

- Real deployment prevalence, human operator behavior, and production failure
  rates.
- Any claim that a synthetic result transfers to real payment, IAM, or
  document systems.
- A faithful Task Shield or IPIGuard baseline without a separate algorithm and
  dependency reproduction audit.
- Deterministic model-output reproducibility, because the current Bedrock
  providers do not expose a sampling seed for these endpoints.

## Scientific gaps addressed by this revision

1. **E1:** isolate language-level authority cues from verified source identity,
   formal authorization, and world truth.
2. **E2:** re-estimate behavioral threshold responses with fresh tasks and
   controls that treat abstention as an outcome rather than infrastructure
   failure.
3. **E3:** connect `G_C`, `G_A`, and `G_E` in executable simulated workflows.
4. **E4:** remain lower priority. A local D0–D3 defense comparison may be
   implemented after E1–E3, but no published method will be named as reproduced
   without a faithful implementation audit.

## Integrity decision

All historical experiment directories remain immutable. New tasks, prompts,
raw responses, analyses, and figures are written only under
`experiments/topo_revision/`. Pilot rows are not pooled into confirmatory
estimates. A partially completed model or experiment is labeled incomplete,
not silently reduced or promoted.
