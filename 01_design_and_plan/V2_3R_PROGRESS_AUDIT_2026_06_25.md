# v2.3R Progress Audit and Experiment Steering

Generated: 2026-06-25

## Input Reports Used As Outline

- `01_design_and_plan/V2_3R_STEADY_EXECUTION_PLAN.md`
- `01_design_and_plan/V2_3R_STAGE1_CURRENT_BOARD.md`
- `01_design_and_plan/V2_3R_STAGE2_CURRENT_BOARD.md`
- `01_design_and_plan/V2_3R_STAGE3_CURRENT_BOARD.md`
- `05_results/stage3_g3_manifest/acceptance_audit.md`

## Executive Verdict

The project is no longer at a "can it run" stage. G1 is accepted, G2 is accepted locally and now has multi-seed strengthening, and Stage 3 has a usable but narrowed local evidence package. The correct paper posture is therefore not to keep expanding claims, but to align claims tightly with the evidence:

1. Main method evidence: T-OMP-Net bounded off-grid refinement beats grid Tensor-OMP at locked tensor scale under local synthetic/off-grid evaluation.
2. A4 evidence: support only a high-L/platform-sample early-stop mechanism, not a global IA-AUD adaptive-depth claim.
3. A5 evidence: keep as appendix/high-stress robustness analysis, not a main contribution.
4. External validation: DeepMIMO Set E remains blocked by missing scenario files and unavailable 5G Toolbox license, so no DeepMIMO performance claim is currently allowed.
5. CRLB evidence: supports analytic derivative correctness and single-target high-SNR trend consistency, not full multi-target asymptotic efficiency.

## Newly Added Experiments

### G2 multi-seed stability

Artifact: `05_results/stage2_torch_locked_scale_g2_seed_sweep/`

- Run id: `stage2_torch_locked_scale_g2_seed_sweep_20260625`
- Seeds: `{20260624, 20260625, 20260626, 20260627, 20260628}`
- Tensor shape: `128x16x32`
- L values: `{2,4,8}`
- Mean L-cell gain over grid Tensor-OMP: `6.1726 dB`
- Std. L-cell gain: `0.9071 dB`
- Minimum L-cell gain: `4.4735 dB`
- Minimum per-seed mean gain: `5.7428 dB`

Verdict: G2 is strengthened from a single-seed bounded local gate into more paper-usable local statistical evidence. It still does not replace external-channel validation.

### A4 high-L plateau gate seed sweep

Artifact: `05_results/stage3_a4_high_l_plateau_gate_seed_sweep/`

- Run id: `stage3_a4_high_l_plateau_gate_seed_sweep_20260625`
- Seeds: `{20260624, 20260625, 20260626}`
- Tensor shape: `128x16x32`
- L value: `32`
- Mean seed depth/FLOPs savings: `26.0417%`
- Std. seed depth/FLOPs savings: `3.6084%`
- Minimum seed depth/FLOPs savings: `21.8750%`
- Mean seed NMSE gap versus fixed K=8: `0.3339 dB`
- Maximum seed NMSE gap versus fixed K=8: `0.3578 dB`

Verdict: The narrowed A4 claim is supported as high-L/platform-sample early stopping. Because one seed falls below 25% savings, the aggregate result is the defensible wording; wording that implies every seed/sample passes the threshold is not supported.

### A4 cross-L plateau gate seed sweep

Artifact: `05_results/stage3_a4_cross_l_plateau_gate_seed_sweep/`

- Run id: `stage3_a4_cross_l_plateau_gate_seed_sweep_20260625`
- Seeds: `{20260624, 20260625}`
- Tensor shape: `128x16x32`
- L values: `{16,32,64}`
- High-L minimum mean depth/FLOPs savings for L>=32: `25.0000%`
- High-L maximum mean NMSE gap for L>=32: `0.4008 dB`
- Overall mean cell depth/FLOPs savings: `27.0833%`
- Overall mean cell NMSE gap: `0.3637 dB`

L-specific summary:

| L | Mean savings | Min savings | Mean gap | Max gap | Paper use |
|---|---:|---:|---:|---:|---|
| 16 | `28.1250%` | `18.7500%` | `0.4220 dB` | `0.5480 dB` | boundary/diagnostic only |
| 32 | `28.1250%` | `25.0000%` | `0.3769 dB` | `0.4008 dB` | high-L support |
| 64 | `25.0000%` | `25.0000%` | `0.2922 dB` | `0.3297 dB` | high-L support |

Verdict: A4 is now stronger as a high-L/platform early-stop mechanism for L>=32. The result still does not support a global IA-AUD claim, and L=16 remains boundary/diagnostic evidence rather than part of the positive main claim.

### A4 SNR plateau gate seed sweep

Artifact: `05_results/stage3_a4_snr_plateau_gate_seed_sweep/`

- Run id: `stage3_a4_snr_plateau_gate_seed_sweep_20260625`
- Seeds: `{20260624, 20260625}`
- Tensor shape: `128x16x32`
- L value: `32`
- SNR values: `{10,20,30} dB`
- Minimum SNR-cell mean depth/FLOPs savings: `21.8750%`
- Maximum SNR-cell mean NMSE gap versus fixed K=8: `0.6834 dB`
- Overall mean cell depth/FLOPs savings: `29.1667%`
- Overall mean cell NMSE gap: `0.4192 dB`

SNR-specific summary:

| SNR | Mean savings | Min savings | Mean gap | Max gap | Paper use |
|---:|---:|---:|---:|---:|---|
| 10 dB | `31.2500%` | `25.0000%` | `0.4772 dB` | `0.6834 dB` | boundary: gap exceeds tolerance |
| 20 dB | `34.3750%` | `31.2500%` | `0.4555 dB` | `0.5161 dB` | boundary for SNR sweep; cross-L run remains core 20 dB support |
| 30 dB | `21.8750%` | `18.7500%` | `0.3250 dB` | `0.4045 dB` | boundary: savings below target |

Verdict: The scalar plateau gate does not support a broad SNR-robust early-stop claim. Keep the positive A4 statement restricted to the existing SNR=20 dB high-L evidence and report this sweep as appendix/boundary sensitivity.

### A4 SNR threshold-frontier diagnostic

Artifact: `05_results/stage3_a4_snr_threshold_frontier/`

- Run id: `stage3_a4_snr_threshold_frontier_20260625`
- Seeds: `{20260624, 20260625}`
- Tensor shape: `128x16x32`
- L value: `32`
- SNR values: `{10,20,30} dB`
- Standard train-selected minimum SNR mean depth/FLOPs savings: `15.6250%`
- Standard train-selected maximum SNR mean NMSE gap: `0.6691 dB`
- Test-oracle frontier minimum SNR mean depth/FLOPs savings: `0.0000%`
- Test-oracle frontier maximum SNR mean NMSE gap: `0.4554 dB`

Verdict: The SNR-axis failure is not only a coarse threshold-grid artifact. Even a diagnostic test-oracle scalar-threshold frontier does not clear the SNR-axis savings/gap gate across all tested SNR cells. Stop widening A4 through scalar-threshold tuning; a future A4 expansion needs a learned SNR-aware or uncertainty-aware gate.

### A4 SNR-aware gate diagnostic

Artifact: `05_results/stage3_a4_snr_aware_gate_diagnostic/`

- Run id: `stage3_a4_snr_aware_gate_diagnostic_20260625`
- Seeds: `{20260624, 20260625}`
- Tensor shape: `128x16x32`
- L value: `32`
- SNR values: `{10,20,30} dB`
- SNR/curve-feature kNN minimum SNR mean depth/FLOPs savings: `21.8750%`
- SNR/curve-feature kNN maximum SNR mean NMSE gap: `0.6558 dB`
- Per-curve quality-oracle minimum SNR mean depth/FLOPs savings: `21.8750%`
- Per-curve quality-oracle maximum SNR mean NMSE gap: `0.4906 dB`

Verdict: A lightweight learned SNR/curve-feature gate also fails to rescue the broad A4 SNR-axis claim. Because even the per-curve quality oracle misses the 25% minimum mean savings target in one SNR cell, the current refinement-curve family appears to lack enough cross-SNR early-stop room under this contract. Future A4 expansion should redesign the refinement schedule or training objective before retesting cross-SNR early stopping.

### Manuscript-facing evidence table

Artifact: `05_results/v2_3r_paper_evidence_table/`

- Run id: `v2_3r_paper_evidence_table_20260625`
- Rows: `10`
- Supported local rows: `4`
- Downgraded rows: `1`
- Blocked rows: `1`
- Key entries: G2 main local result, A4 L>=32 early-stop result, A4 SNR sensitivity boundary, A4 SNR threshold-frontier diagnostic, A4 SNR-aware gate diagnostic, Kruskal on-grid proxy, synthetic cross-scene fallback, 5L CRLB pilot, A5 appendix downgrade, DeepMIMO external-data blocker.

Verdict: This is now the preferred source for paper-table drafting and claim discipline. Regenerate it whenever G2, A4, A5, Kruskal, synthetic cross-scene, CRLB, or DeepMIMO evidence changes.

### v2.3R main technical design and section plan

Artifacts:

- `01_design_and_plan/ISAC_DeepUnfolding_TechnicalDesign_v2.3R.md`
- `06_paper_and_delivery/paper_notes/v2_3r_section_plan.md`

Verdict: The project now has a paper-facing v2.3R technical design anchored to the evidence table and a section-by-section manuscript plan. The v2.3R document explicitly lists forbidden overclaims; string searches for phrases such as "DeepMIMO 外部验证已完成" or "全局 IA-AUD 最优深度" match those forbidden-claim guardrails, not positive claims.

### v2.3R manuscript workspace

Artifacts:

- `06_paper_and_delivery/manuscript_v2_3r/main.md`
- `06_paper_and_delivery/manuscript_v2_3r/sections/`
- `06_paper_and_delivery/manuscript_v2_3r/appendix/README.md`
- `06_paper_and_delivery/manuscript_v2_3r/paper_experiment_matrix.md`
- `06_paper_and_delivery/manuscript_v2_3r/claim_evidence_ledger.json`

Verdict: A sectioned manuscript scaffold now exists. It includes first-pass Introduction, Related Work, System Model, Method, Theory, Experiments, Limitations, and Conclusion sections; an appendix plan; a claim-evidence ledger; and a paper experiment matrix. The ledger parses as valid JSON. Searches for DeepMIMO/global/adaptive-depth phrases find only boundary, limitation, or "must not claim" contexts.

### v2.3R citation sprint

Artifacts:

- `02_literature_and_refs/v2_3r_literature_sprint_2026_06_25.md`
- `02_literature_and_refs/v2_3r_references.bib`
- `06_paper_and_delivery/manuscript_v2_3r/sections/02_related_work.md`

Verdict: The first compact Related Work citation sprint is now in place. It verifies the core tensor-ISAC, JCAS deep-unfolding, Radar-CEnet, deep-unfolding survey, AI-ISAC tutorial, DeepMIMO, and off-grid sparse Bayesian anchor references needed for the Related Work section. This does not make the bibliography submission-complete; it only removes the immediate blocker that prevented section drafting.

Update: The bibliography has now been expanded from 8 to 26 entries. The added core set covers classical OMP/MMV sparse recovery, tensor factorization and uniqueness, sparse mmWave MIMO channel modeling, OFDM/OTFS/ISAC context, Hungarian assignment, estimation-theory grounding for the CRLB check, and hardware-impairment boundary references. This materially improves the manuscript's literature spine, while the final venue-facing bibliography still needs target-template metadata polish and likely expansion toward 30-50 verified references.

### v2.3R paper display candidates

Artifacts:

- `06_paper_and_delivery/manuscript_v2_3r/displays/figures/v2_3r_evidence_summary.png`
- `06_paper_and_delivery/manuscript_v2_3r/displays/figures/v2_3r_evidence_summary.pdf`
- `06_paper_and_delivery/manuscript_v2_3r/displays/tables/v2_3r_main_result_table.md`
- `06_paper_and_delivery/manuscript_v2_3r/displays/tables/v2_3r_a4_snr_sensitivity_table.md`
- `06_paper_and_delivery/manuscript_v2_3r/displays/captions.md`
- `06_paper_and_delivery/manuscript_v2_3r/displays/figure_catalog.json`

Verdict: The project now has a first paper-facing display bundle. The figure was rendered and visually inspected; the first draft had oversized typography, so it was revised to smaller paper-scale labels and explicit pass/fail reference lines. Treat it as a manuscript candidate, not final camera-ready artwork.

### v2.3R evidence-led manuscript rewrite

Artifacts:

- `06_paper_and_delivery/manuscript_v2_3r/sections/01_introduction.md`
- `06_paper_and_delivery/manuscript_v2_3r/sections/02_related_work.md`
- `06_paper_and_delivery/manuscript_v2_3r/sections/03_system_model.md`
- `06_paper_and_delivery/manuscript_v2_3r/sections/04_method.md`
- `06_paper_and_delivery/manuscript_v2_3r/sections/05_theory.md`
- `06_paper_and_delivery/manuscript_v2_3r/sections/06_experiments.md`
- `06_paper_and_delivery/manuscript_v2_3r/sections/07_limitations.md`
- `06_paper_and_delivery/manuscript_v2_3r/sections/08_conclusion.md`
- `06_paper_and_delivery/manuscript_v2_3r/main.md`
- `06_paper_and_delivery/manuscript_v2_3r/README.md`

Verdict: Abstract, Introduction, Related Work, System Model, Method, Theory, Experiments, Limitations, and Conclusion now have evidence-led draft text. The Abstract uses one G2 headline result and one scoped A4 high-load efficiency result, then explicitly narrows the adaptive-depth claim. The Introduction opens with the tensor sparse-recovery problem, bounded off-grid unfolding idea, G2 headline evidence, and A4 boundary. Related Work names the closest tensor-ISAC, JCAS deep-unfolding, sensing-assisted channel-estimation, off-grid sparse-recovery, and DeepMIMO benchmark references while keeping the novelty boundary scoped. The System Model aligns the observation tensor, support, off-grid target, FDMA scope, and evaluation regimes with the Method section. The Method section explains the Tensor-OMP scaffold, bounded refinement, Hungarian supervision, and restricted plateau gate as a connected mechanism. The Theory section states support-conditioned off-grid reasoning, the depth-identifiability trade-off, and single-target CRLB consistency without overclaiming. The Experiments section now follows a reviewer-facing structure: protocol, G2 main result, A4 high-L trade-off, A4 SNR sensitivity boundary, threshold-frontier diagnostic, and supporting/negative evidence. Limitations state the external-validation, adaptive-depth, impairment-robustness, and CRLB-scope boundaries in manuscript prose. The Conclusion closes on the same scoped evidence boundary. A generic-article LaTeX checkpoint now compiles to PDF; bibliography expansion and target-venue template replacement remain open.

### v2.3R LaTeX draft package

Artifacts:

- `06_paper_and_delivery/manuscript_v2_3r/latex/main.tex`
- `06_paper_and_delivery/manuscript_v2_3r/latex/sections/`
- `06_paper_and_delivery/manuscript_v2_3r/latex/appendix/`
- `06_paper_and_delivery/manuscript_v2_3r/latex/main.pdf`
- `06_paper_and_delivery/manuscript_v2_3r/latex/build_report.md`

Verdict: A compilable LaTeX draft checkpoint now exists. Because the repository does not contain a target venue template, the package uses a generic `article` class with minimal dependencies available in the current MiKTeX environment. The build resolves citations and cross-references, produces an 11-page PDF, and records only layout-polish warnings. This is a manuscript checkpoint, not a final submission package.

## Paper-Level Readiness

| Component | Current readiness | Paper use |
|---|---|---|
| G1 Tensor-OMP/off-grid/CRLB infrastructure | accepted | Methods and baseline validation |
| G2 T-OMP-Net bounded off-grid refinement | accepted + seed-strengthened | Main result candidate |
| A4 IA-AUD/adaptive depth | narrowed cross-L pass for L>=32 at SNR=20 dB; SNR sweep and scalar threshold frontier fail to support broad SNR-axis stability | Main or secondary result only under core-SNR high-L/platform-sample wording |
| A5 HIR-JL | downgraded | Appendix/high-stress failure-mode analysis |
| Kruskal paper-scale proxy | local on-grid pass | Sanity row, not external validation |
| Synthetic cross-scene fallback | local pass | Fallback portability row, not DeepMIMO/CDL |
| DeepMIMO Set E | blocked | Do not claim performance |
| 5L CRLB trend | pilot supported | Single-target high-SNR trend row |

## Main Risks To High-Level Paper Standard

1. Claim inflation risk: A4 and A5 cannot be described with the original broad v2.3R gate language.
2. SNR-axis risk: the A4 SNR sweep and threshold-frontier diagnostic fail to support broad scalar-gate stability, so the early-stop claim must remain restricted to the core-SNR high-load setting.
3. External validity risk: DeepMIMO/CDL remains unresolved; Sensors/Systems may tolerate a clear limitation better than an unsupported claim.
4. Statistical breadth risk: local evidence is now better, but still CPU-small. Paper wording should say "local synthetic/off-grid evaluation" unless larger runs are added.
5. Tooling risk: `pytest` is absent from the current Python environment; scripts ran, but unit-test automation cannot be invoked until the test dependency is installed.

## Next Experiment Steering

Priority 1: replace the generic LaTeX class with the target venue template, then polish bibliography metadata and figure/table placement under that template. The draft now has all major body sections, an evidence-bound abstract, a 26-entry core bibliography, and a compilable PDF checkpoint.

Priority 2: polish paper displays under the target template. If A4 is expanded experimentally, redesign the refinement schedule or training objective before retesting cross-SNR early stopping; the lightweight SNR-aware gate diagnostic did not rescue the current curves.

Priority 3: unblock or formally waive DeepMIMO Set E. If data/toolbox access cannot be resolved, write the limitation explicitly and keep synthetic cross-scene as a fallback rather than pretending it is external validation.

Priority 4: install or vendor test tooling (`pytest`) so unit-test automation can run in the same environment as the experiment scripts.

Priority 5: continue bibliography expansion only after the target venue and exact paper scope are fixed. The current 26-entry core set covers the previously missing classic OMP/MMV, tensor CPD, sparse mmWave channel estimation, OFDM/OTFS/ISAC, CRLB/estimation-theory, Hungarian matching, and hardware-impairment categories; a high-level manuscript still needs final comparator breadth, metadata polish, and venue-style consistency.

## Current Recommended Claim Set

- Claim C1/C2: supported locally with accepted G1/G2 evidence.
- Claim C3: supported only as bounded off-grid T-OMP-Net plus Hungarian/loss infrastructure and high-L early-stop evidence at SNR=20 dB; avoid global adaptive-depth optimality and avoid SNR-axis stability wording.
- Claim C4: split into local robustness/portability evidence and explicit external validation blocker; keep A5 as appendix.
- Theory: Lemma 1 and Lemma 2 must use the corrected support-condition and trade-off wording from v2.3R.

## Verification Notes

- `python -m py_compile` passed for the two newly added seed-sweep scripts.
- `python 04_experiments/eval/run_stage2_torch_locked_scale_g2_seed_sweep.py` completed and wrote manifest/CSV/summary/evaluation files.
- `python 04_experiments/eval/run_stage3_a4_high_l_plateau_gate_seed_sweep.py` completed and wrote manifest/CSV/summary/evaluation files.
- `python 04_experiments/eval/run_stage3_a4_cross_l_plateau_gate_seed_sweep.py` completed and wrote manifest/CSV/summary/evaluation files.
- `python 04_experiments/eval/run_stage3_a4_snr_plateau_gate_seed_sweep.py` completed and wrote manifest/CSV/summary/evaluation files. A first attempt with a 124 s timeout was killed before outputs; the successful rerun completed with a longer 420 s window.
- `python 04_experiments/eval/run_stage3_a4_snr_threshold_frontier.py` completed and wrote manifest/CSV/summary/evaluation files; it shows that scalar-threshold frontier tuning does not rescue the A4 SNR-axis claim.
- `python 04_experiments/eval/run_stage3_a4_snr_aware_gate_diagnostic.py` completed and wrote manifest/CSV/summary/evaluation files; it shows that a lightweight SNR/curve-feature gate and even the per-curve quality oracle do not clear the current cross-SNR savings/gap contract.
- `python 04_experiments/eval/aggregate_v2_3r_paper_evidence_table.py` completed and wrote manuscript-facing CSV/Markdown evidence tables.
- `python 06_paper_and_delivery/manuscript_v2_3r/displays/scripts/build_v2_3r_paper_displays.py` completed and wrote first paper-facing PNG/PDF figure plus Markdown/CSV display tables.
- `06_paper_and_delivery/manuscript_v2_3r/sections/01_introduction.md` and `06_paper_and_delivery/manuscript_v2_3r/sections/06_experiments.md` were rewritten around the current figure/table evidence package.
- `06_paper_and_delivery/manuscript_v2_3r/sections/04_method.md` and `06_paper_and_delivery/manuscript_v2_3r/sections/05_theory.md` were rewritten to explain the mechanism and theory boundary without expanding the supported claims.
- `06_paper_and_delivery/manuscript_v2_3r/sections/03_system_model.md` and `06_paper_and_delivery/manuscript_v2_3r/sections/08_conclusion.md` were rewritten to align notation, FDMA/evaluation scope, and final claims with the evidence boundary.
- `06_paper_and_delivery/manuscript_v2_3r/sections/02_related_work.md` and `06_paper_and_delivery/manuscript_v2_3r/sections/07_limitations.md` were rewritten from control-document wording into manuscript-facing prose.
- `06_paper_and_delivery/manuscript_v2_3r/main.md` now includes an evidence-bound abstract draft.
- `06_paper_and_delivery/manuscript_v2_3r/latex/main.tex` was built with `pdflatex`/`bibtex` and produced `06_paper_and_delivery/manuscript_v2_3r/latex/main.pdf` with resolved citations and cross-references; residual warnings are layout polish only.
- `01_design_and_plan/ISAC_DeepUnfolding_TechnicalDesign_v2.3R.md` and `06_paper_and_delivery/paper_notes/v2_3r_section_plan.md` were written as paper-facing control documents.
- `06_paper_and_delivery/manuscript_v2_3r/` was created with sectioned draft files, appendix plan, experiment matrix, and claim-evidence ledger.
- `python -m json.tool 06_paper_and_delivery/manuscript_v2_3r/claim_evidence_ledger.json` passed.
- `python -m pytest -q` could not run because the current Python environment has no `pytest` module installed.
- `02_literature_and_refs/v2_3r_references.bib` and `02_literature_and_refs/v2_3r_literature_sprint_2026_06_25.md` were expanded into a 26-entry core bibliography; final venue-scale metadata polish and any scope-driven expansion remain open.
