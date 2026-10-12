# TopoSafe-Delta Revision Ledger

## 2026-10-07: claim-integrity audit and evidence-frozen manuscript

- Renamed the canonical manuscript from `toposafe-delta-draft.md` to
  `toposafe-delta.md`.
- Reframed the title around authority cut and the decoupling of communication,
  authorization, and execution.
- Added a 195-word evidence-grounded abstract.
- Removed the experiment-status block from the opening and consolidated nine
  process-oriented contribution bullets into four scientific contributions.
- Replaced the unavailable Architecture Matters OpenReview URL with the
  verified arXiv primary page.
- Corrected the MasDrift architecture list from `centralized, decentralized,
  and hybrid` to `single-agent, centralized, and decentralized`.
- Clarified call accounting: 61,440 assigned calls in the core intervention
  ledger and 66,090 formal model calls across all evidence reported in the
  manuscript.
- Corrected Llama 4 Maverick B2 `topo_A` mean similarity from 0.990 to 0.989.
- Replaced `Current Evidence Boundary` with a scientific Discussion and
  Limitations section organized around executable-safety mechanisms and
  evidence scope.
- Preserved the failed preregistered gates for Authority Placement GPT-5.4 and
  Authority Composition GPT-5.4/Llama 4 Maverick.
- Narrowed the authority-composition claim: authority cut sets structural proof
  forgeability, while advisory threshold responses remain model-dependent.
- Removed project-management language about whether more calls are required
  from the paper conclusion.
- Updated `ccfa.yaml`, project READMEs, and the paper plan to point to the
  evidence-frozen manuscript and audit record.

Validation details are recorded in
`reviews/toposafe-claim-integrity-audit.md`.

## 2026-10-12: TopoSafe revision experiments

- Audited the existing paper evidence in a clean clone and preserved all
  historical frozen experiment directories.
- Added and froze TopoSafe-Delta-Revision-v1.0 with 60 E1 tasks, 80 E2 tasks,
  48 E3 tasks, deterministic proof logic, validity gates, analysis, and
  plotting code.
- Completed E1 formal runs for Claude Sonnet 5, Nemotron 3 Super 120B, and
  Llama 4 Maverick. GPT-5.4 failed the pilot endpoint gate and was not promoted.
- Observed no uniform positive verified-provenance effect; retained the
  contradictory and model-heterogeneous outcomes.
- Completed the valid Llama E2 formal block and preserved failed Claude and
  Nemotron pilot controls as diagnostic evidence.
- Implemented and piloted E3, then invalidated Claude and Llama pilot evidence
  after discovering intermediate forwarder schema failures omitted by the
  original generic validator. Only Nemotron remains a clean pilot block.
- Generated raw-data-derived CSV/LaTeX tables, PDF/PNG figures, run inventory,
  cost ledger, post-run integrity audit, and final reviewer-style report.
- Did not edit the evidence-frozen manuscript, claim a four-model revision
  result, run E4, merge the experimental branch, or make the repository public.
