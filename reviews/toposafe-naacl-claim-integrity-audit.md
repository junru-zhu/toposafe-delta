# TopoSafe-Delta NAACL Claim Integrity Audit

**Mode:** Final manuscript claim, format, citation, and visual audit  
**Audit date:** 2026-10-07  
**Manuscript:** `manuscript/naacl2027/main.tex`  
**Final status:** PASS for an anonymous NAACL/ARR draft. No blocking
claim-evidence or build error remains. The paper has not been submitted.

## Claim and number checks

- The complete formal-call ledger recomputes to 66,090.
- The 61,440 core-intervention total is not presented as the full paper total.
- Authentication amplification is limited to the two placement-study model
  blocks that passed the frozen validity gate.
- Single-authority placement is reported as having no stable advantage, not as
  a theorem that location never matters.
- Authority cut is described as a structural proof-forgery threshold.
- Advisory authority-cut behavior remains model- and regime-dependent.
- Runtime enforcement is limited to invalid proofs, the evaluated verifier,
  and the synthetic task family.
- Communication topology is not called irrelevant; the paper reports language
  drift and model-conditional effects while rejecting a stable cross-model
  ranking.
- No human or model judge supplies labels, scoring, case selection, or
  experiment-validity decisions.

## Citation audit

- All 13 citation keys resolve to exactly 13 bibliography entries; there are no
  missing or uncited entries.
- ACL papers were checked against ACL Anthology records.
- arXiv papers were checked against their primary arXiv records.
- The previous mappings of `2609.12113` and `2509.18415` were unrelated papers;
  they were removed from the literature matrix and are not cited.
- Reliance-cue language was narrowed: uncertainty expressions may fail to
  calibrate reliance, while interactional cues may increase it.
- The novelty statement remains conditional on inspected public work.

## NAACL and ARR format audit

- Official ACL review style is used; the local style and bibliography files
  match the official repository snapshot hashes.
- Abstract length: 186 words.
- Main content ends on page 7, below the eight-page long-paper limit.
- Total PDF length: 9 pages, including references and a two-page appendix.
- Limitations and Ethical Considerations appear before References.
- Anonymous author metadata is used and no acknowledgments appear.
- A plain-text metadata abstract is prepared separately.
- The Responsible NLP checklist draft includes limitations, dual-use risks,
  reproducibility boundaries, no-human-participant status, and generative-AI
  assistance disclosure.

## Build and visual audit

- Tectonic compilation: PASS.
- Undefined citations/references: none.
- Duplicate bibliography-style commands: none.
- Overfull boxes: none.
- PDF syntax and streams: PASS under `qpdf --check`.
- Ghostscript page rendering: PASS for all 9 pages.
- Page size: A4.
- Figure 1, Figure 2, the study table, formula, references, and appendix were
  visually inspected in rendered pages.
- Figure 2 legend and annotation overlap was repaired without changing values.

The remaining TeX messages are underfull-box advisories plus a non-rendering
Tectonic `lineno.sty` byte warning. Neither produced missing text, clipping, or
an invalid PDF in the rendered inspection.

## Regression record

- Relevant TopoSafe unit suite: 56 passed.
- `ccfa.yaml`: parsed successfully.
- Internal links in the new NAACL package: passed.
- Formal-call arithmetic: passed.
- Bibliography key equality: 13/13 passed.

## Remaining external gates

1. Confirm and freeze the complete author list and OpenReview profiles.
2. Register all authors for reviewing and satisfy ARR service requirements.
3. Transfer the prepared Responsible NLP answers into the submission form.
4. Decide artifact-release scope; no release is authorized.
5. Perform the final live policy/anonymity check before upload.
6. Upload or submit only after explicit user authorization.
