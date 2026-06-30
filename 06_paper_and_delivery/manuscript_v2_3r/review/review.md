# Independent Manuscript Review — v2.3R

Generated: 2026-06-29

## Review mode

- `review_followup_policy`: auto-execute writing, evidence-map, and figure corrections; preserve expensive experiments as explicit TODOs.
- `manuscript_edit_mode`: LaTeX required.
- `manuscript_source_status`: reviewable eight-page IEEEtran draft, not submission-ready.

## Summary

The draft has a disciplined claim boundary, reproducible manifests, positive local off-grid evidence, and a useful held-out CDL-A/C result with a visible CDL-D failure boundary. Its current rejection risk is nevertheless high because the manuscript presents several separately implemented mechanisms as one integrated deep-unfolding estimator. The code and run manifests show three distinct paths: a one-parameter interpolation layer for local G2, a deterministic repeated-refinement curve for A4, and a 210-parameter feature controller for CDL. The scaled CDL manifest explicitly states that it is not evidence for a deeper full T-OMP-Net.

Overall judgment: major revision. The paper can become defensible through immediate claim/nomenclature correction and better mathematical specification. Retaining a “deep unfolding T-OMP-Net” headline requires a new integrated implementation and matched evaluation, not prose.

Top rejection risks:

1. Method identity and evidence provenance mismatch.
2. Insufficient formal system/method/theory specification for an algorithm paper.
3. Thin comparator accuracy and small-sample evidence relative to the breadth of the headline.

## Strengths

- Honest profile boundary: CDL-A/C is positive in aggregate, while zero-shot CDL-D is retained as a failure.
- Strong reproducibility surface: commands, seeds, environments, checkpoints, CSVs, and manifests are durable.
- Useful physical metric discipline: CIR-grounded delay and identifiable projected broadside angle are distinguished from bin proxies.
- Related Work now names DDA-Net, NOMP-OFDM-ISAC, unified tensor ISAC, and PLAIN rather than claiming single-component novelty.
- The final figure set uses vector exports and a restrained visual language.

## Weaknesses

- `TorchOffgridRefinementLayer` learns one scalar interpolation coefficient; it is not by itself a deep network.
- The CDL controller is trained and evaluated as a post-support two-axis controller and is explicitly not a deeper full T-OMP-Net.
- A4 repeats deterministic local searches with a radius schedule; it is not an adaptive-depth result from the trained CDL controller.
- The theory section contains prose summaries but no formal lemma statements, assumptions, bounds, or derivations.
- G2 uses only 2 training and 3 test samples per L per seed; A4 cross-L uses two seeds and two test curves per cell.
- ESPRIT/PARAFAC appear only in a complexity table; no matched accuracy comparison exists.
- The claim ledger is stale: it omits the selected scaled controller result and still lists resolved bibliography/figure/E4 blockers.

## Key issues

### REV-001 — Method identity mismatch

- Risk: critical.
- Evidence: `03_active_modules/tompnet/torch_layer.py`, `03_active_modules/tompnet/feature_controller.py`, `05_results/sionna_cdl_ac_alias_lock_selected_scaled/run_manifest.json` notes, and the original Fig. 2.
- Required route: immediate claim downgrade and figure correction; integrated-network experiment if the deep-unfolding headline is retained.
- Acceptance criterion: every result is attributed to its actual executable path, and no figure implies that the CDL controller was evaluated inside a K-stage network.

### REV-002 — Missing mathematical contract

- Risk: high.
- Evidence: `latex/sections/03_system_model.tex`, `04_method.tex`, and `05_theory.tex` contain almost no displayed mathematical definitions.
- Required route: add the implemented interpolation/controller equations, LS reconstruction, assignment-aware loss, and explicit conditional theory statements. Do not invent a proof stronger than the design document or experiments support.
- Acceptance criterion: a reviewer can reproduce the estimator mapping and understand every bounded claim without reading the code.

### REV-003 — Evidence breadth exceeds sample/comparator depth

- Risk: high.
- Evidence: Stage-2 G2 manifest (`n_train=2`, `n_test=3` per L/seed), A4 cross-L manifest (two seeds, two test samples/cell), and E4 complexity-only boundary.
- Required route: narrow the current paper claim; then run an integrated estimator comparison or a substantially strengthened local experiment before submission.
- Acceptance criterion: either the title/abstract state “learned bounded refinement” or an integrated K-stage model is implemented and evaluated against matched NOMP/ESPRIT/PARAFAC accuracy baselines.

### REV-004 — Figure 3 scientific readability

- Risk: medium.
- Evidence: the original figure was a single-column, three-panel chart with two dual-axis panels.
- Required route: replace dual axes with an admissible-region trade-off plane and show seed points directly.
- Acceptance criterion: the positive and failed cells are visible without switching between two y-axes or reading tiny legends.

### REV-005 — Stale durable state

- Risk: medium.
- Evidence: `claim_evidence_ledger.json`, `PLAN.md`, and the 2026-06-27 steering scorecard retain pre-closure blockers.
- Required route: synchronize the current scaled CDL result, E4 status, figure/reference status, and current next anchor.

## Experiment inventory

| Evidence block | Artifact status | Manuscript status | Review classification |
|---|---|---|---|
| Local scalar bounded refinement (G2) | complete, 5 seeds, very small per-cell sample count | written as main mechanism | completed and written; headline must say scalar/local |
| A4 repeated-radius plateau gate | complete, 2 seeds x 2 test curves/cell | written as scoped efficiency result | completed and written; deterministic diagnostic, not trained-controller depth |
| CDL-A/C feature controller | complete, 5 held-out seeds x 50 samples/profile/seed | written as main external result | completed and written; profile-trained post-support controller |
| CDL-D zero-shot | complete at matching scale | written as limitation | completed and written, negative boundary |
| E4 ESPRIT/PARAFAC timing | complete, 15 executable rows | appendix | completed and written; accuracy absent |
| CRLB | finite-difference + single-target trend | prose only | completed but under-specified mathematically |
| DeepMIMO | scalar-alpha proxies only | limitation | incomplete for trained physical evaluation |
| Integrated K-stage network | no executable evidence found | implied by title/original architecture | written but not evidenced |

Unsupported-claim risk: manuscript overclaim, not fabrication. The underlying artifacts are transparent; the problem is that the narrative fuses them into a stronger architecture than was evaluated.

## Novelty and literature benchmark

| Comparator | What it establishes | Implication for this paper |
|---|---|---|
| DDA-Net | actual 3-D ADMM unfolding with external QuaDRiGa/CDL channel evidence | “deep unfolding” needs an implemented multi-stage network, not only a scalar layer |
| NOMP-OFDM-ISAC | OMP plus continuous Newton refinement and measurement validation | bounded learned refinement must be compared on accuracy or framed as a scoped alternative |
| Unified tensor ISAC | classical joint channel/target tensor formulation | tensor formulation is an anchor, not standalone novelty |
| PLAIN | scalable tensor/subspace/CS estimation and fusion | complexity and multidimensional pairing are active baselines |
| DL-CPALS | learning-assisted tensor decomposition | learned tensor estimation is broader than unfolded OMP |

Residual defensible value: a compact, evidence-bounded study of learned local refinement after Tensor-OMP support selection, with permutation-aware physical supervision, standards-aligned CDL-A/C evaluation, and explicit failure boundaries.

## Priority revision plan

1. Correct the method identity in title, abstract, figures, contribution list, closest-work table, and conclusion.
2. Replace Fig. 2 with an evidence-aligned two-path diagram and Fig. 3 with seed-aware, no-dual-axis plots.
3. Add implemented equations and explicit conditional theory statements.
4. Synchronize ledger/plan/evidence matrices.
5. Treat integrated K-stage evaluation and matched comparator accuracy as the next experiment gate before submission.

## Internal score

- Current: 5/10, major revision.
- After claim/figure/math correction: 6.5/10, defensible draft checkpoint.
- Submission target: 7.5/10 after integrated-estimator or matched-comparator evidence is added.

