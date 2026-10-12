# Responsible NLP Checklist Draft

This is an author-preparation draft for the NAACL 2027 submission form. It is
not a submitted checklist.

## A. Every submission

- **A1 limitations discussed:** Yes. The paper limits conclusions to synthetic
  tasks, evaluated proof semantics, model versions, prompts, and the
  deterministic verifier.
- **A2 risks discussed:** Yes. Ethical Considerations covers dual use,
  credential/private-log removal, and conditionality of the enforcement result.

## B. Artifacts and models

- **B1 creators cited:** Partially. The exact managed endpoint identifiers and
  model providers are reported. Stable archival model papers are not available
  for every evaluated proprietary endpoint; explain this in the form rather
  than checking an unqualified Yes.
- **B2 licenses/terms discussed:** No in the current manuscript. The endpoints
  were accessed under provider terms; the synthetic task and code release
  license remains pending author and venue-policy review.
- **B3 intended use:** Yes. The paper limits the artifacts to synthetic,
  mechanism-level defensive evaluation and discusses misuse risk.
- **B4 personal or offensive data checks:** Not applicable. Tasks are generated
  synthetic records and use no human-subject or personal dataset.
- **B5 artifact documentation:** Yes. Task coverage, proof fields, model
  endpoints, scoring predicates, validity gates, and call accounting appear in
  the framework and appendix.
- **B6 data statistics:** Yes. The paper reports task counts, model blocks,
  experimental cells, calls, failures, recoveries, and balance checks.
- **Release status:** Pending. No artifact release or upload has been
  authorized.

## C. Experiments

- **C1 parameters, budget, and infrastructure:** Partially. Exact endpoint
  identifiers, region, formal-call counts, output-token limits, workers, and
  retry policy are reported. Proprietary parameter counts, provider-side GPU
  hours, energy use, and exact monetary cost are unavailable.
- **C2 setup and hyperparameters:** Yes. Response modes, temperature/top-p
  settings, token limits, task construction, model selection, and the absence
  of a hyperparameter search are documented.
- **C3 descriptive statistics:** Yes. The paper reports per-model estimates,
  task-cluster bootstrap intervals, equivalence margins, validity gates, and
  replication rules.
- **C4 software/packages:** Partially. Custom experimental logic and plotting
  sources are prepared, but a release-time environment lock and license remain
  pending.
- **Reproducibility boundary:** The provider exposes no sampling seed. The
  paper states what was frozen and does not claim bitwise reproducibility.

## D. Human annotators or participants

- **D1 instructions:** Not applicable.
- **D2 recruitment/payment:** Not applicable.
- **D3 consent:** Not applicable.
- **D4 ethics board:** Not applicable.
- **D5 demographics/geography:** Not applicable.
- No human review is used as evidence. Labels and validity gates are
  deterministic and programmatic.

## E. AI assistants

- **E1 AI-assistant use disclosed:** Yes. Codex was used for manuscript drafting
  and revision, literature-retrieval assistance, LaTeX preparation, and figure
  code. The authors remain responsible for the paper and manually verified the
  experimental claims, calculations, citations, source mappings, and rendered
  PDF. Generative AI did not supply task labels, validity decisions, model
  outputs, or experimental results.

## Camera-ready disclosure text

If the paper is accepted, add an acknowledgments disclosure consistent with the
submission checklist:

> Codex was used for writing and coding assistance. The authors verified all
> claims, citations, numerical results, and final artifacts and take full
> responsibility for the paper.
