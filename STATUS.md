# TopoSafe-Delta Status

Snapshot date: 2026-10-12

## Verified

- The anonymous NAACL/ARR-style manuscript and PDF are complete and
  evidence-frozen to the 2026-10-07 ledger.
- The manuscript reports 66,090 formal model calls and keeps failed model gates
  visible.
- Runtime proof enforcement, matched communication, free-running
  communication, authority-mechanism ablations, and independent-schedule
  replication packages are present with their frozen validation and analysis
  outputs.
- All TopoSafe experiment directories, including development failures,
  technical recoveries, and sensitivity analyses, are retained in this
  repository snapshot.

## Execution-topology extension

The new direct `G_E` experiment planned 5,760 formal calls over 60 new tasks,
four proposal roles, three authority regimes, paired true/false worlds, four
models, and seven deterministically recomposed execution layouts.

- Claude Sonnet 5: complete.
- Llama 4 Maverick: complete.
- Nemotron 3 Super 120B: parent block plus separately frozen technical
  recovery complete.
- GPT-5.4: incomplete after bounded 240-second and 600-second transport-timeout
  attempts.
- Three-model sensitivity analysis: complete and labeled non-confirmatory.
- Four-model cross-model replication claim: not allowed.
- Manuscript integration: not performed.

The bounded three-model result indicates that complete mediation is the strong
structural signal: guarded layouts had zero invalid-proof execution, while one
uncovered source or executor edge restored substantial risk for models that
proposed invalid protected actions. The result is not promoted to a formal
four-model paper conclusion.

## Topo revision package

The separately frozen `experiments/topo_revision/` package adds provenance,
authority-threshold, and realistic-workflow studies without modifying the
historical evidence.

- E1 provenance: 60 tasks and three valid 600-row formal model blocks. GPT-5.4
  failed its pilot endpoint gate and was not run formally.
- E1 conclusion: verified source identity did not uniformly increase
  protected-action selection. Nemotron decreased selection under P2; Claude
  remained conservative; Llama reacted mainly to stale/wrong-scope P3.
- E2 authority cut: deterministic proof thresholds passed. Only Llama passed
  the frozen pilot controls and completed the 976-row formal block.
- E2 conclusion: invalid proofs never committed, but policy-valid false proofs
  committed at and above the authority cut. Cross-model behavioral
  generalization remains untested.
- E3 workflow: the three-domain simulator and complete factorial are
  implemented. No formal run was executed. Strict post-run auditing found only
  the Nemotron pilot clean; Claude and Llama had intermediate forwarder schema
  failures.
- E4 defense comparison: not run.
- Revision spend estimate: USD 3.2816, or USD 3.9379 with the frozen
  conservative margin.

The full evidence boundary and proposed manuscript text are in
`experiments/topo_revision/FINAL_RESEARCH_REPORT.md`.

## Remaining work

1. Freeze a v1.1 neutral E1 metadata control and rerun the causal control
   comparison.
2. Replace E2's behavior-dependent pilot eligibility with technical
   provider/schema/proof validity and treat abstention as an outcome.
3. Repair and preflight E3's structured forwarder outputs across all model
   families before any formal workflow run.
4. Recheck the GPT-5.4 endpoint before assigning any new GPT block.
5. Update the manuscript only with results whose stated validity boundary is
   preserved.
6. Perform a separate public-release, licensing, anonymity, and raw-output
   review before changing this repository from private.
