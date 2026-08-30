# v2.3R Paper Section Plan

Generated: 2026-06-25

## Control Sources

- `01_design_and_plan/ISAC_DeepUnfolding_TechnicalDesign_v2.3R.md`
- `05_results/v2_3r_paper_evidence_table/paper_evidence_table.md`
- `01_design_and_plan/V2_3R_PROGRESS_AUDIT_2026_06_25.md`
- `01_design_and_plan/V2_3R_STAGE3_CURRENT_BOARD.md`

## Story Spine

mmWave MIMO-OFDM ISAC joint estimation can be framed as sparse recovery over an angle-delay-Doppler tensor. A model-driven Tensor-OMP unfolding network with physically bounded off-grid refinement improves local off-grid estimation while preserving interpretability. The strongest current contribution is the bounded T-OMP-Net refinement path; the adaptive-depth story must be narrowed to high-L/platform early stopping for L>=32, and external validation remains blocked until DeepMIMO data/toolbox readiness changes.

## Claim-Evidence Map

| Claim ID | Main claim | Evidence | Section owner | Boundary |
|---|---|---|---|---|
| C1 | Joint channel/target estimation can be modeled as a 3D sparse tensor recovery problem. | v2.2/v2.3R model design; Kruskal proxy | System Model + Theory | Needs formal notation in draft; not an empirical performance claim. |
| C2 | T-OMP-Net bounded off-grid refinement improves local synthetic/off-grid NMSE over grid Tensor-OMP. | `05_results/stage2_torch_locked_scale_g2_seed_sweep/` | Method + Experiments | Local synthetic/off-grid only. |
| C3 | High-L plateau early stopping reduces depth/FLOPs for L>=32 with small NMSE gap. | `05_results/stage3_a4_cross_l_plateau_gate_seed_sweep/` | Method + Experiments/Analysis | Not global IA-AUD; L=16 is boundary-only. |
| C4a | Tensor model is not near the on-grid Kruskal proxy limit in the paper-scale scan. | `05_results/stage3_paper_scale_kruskal_proxy/` | Theory + Analysis | On-grid sanity only. |
| C4b | Local synthetic cross-scene alpha transfer is positive under controlled shifts. | `05_results/stage3_synthetic_cross_scene_generalization/` | Experiments/Appendix | Not DeepMIMO/CDL/ray-traced validation. |
| C4c | Analytic 5L FIM and single-target CRLB trend are numerically consistent. | `05_results/stage3_crlb_asymptotic_tightness/` | Theory + Analysis | Not full multi-target asymptotic efficiency. |
| C4d | A5/HIR-JL is not main-line ready. | `05_results/stage3_a5_combined_impairment_presmoke/` | Appendix + Limitations | Appendix/high-stress only. |
| C4e | DeepMIMO Set E is blocked. | `05_results/deepmimo_set_e_access_audit/` | Limitations + Appendix | No DeepMIMO performance claim. |

## Main-Text Display Program

| Display | Purpose | Source | Placement |
|---|---|---|---|
| Fig. 1 system/method schematic | Explain tensorization -> Tensor-OMP -> bounded refinement -> outputs. | Method design | Introduction or Method |
| Table 1 G2 local result | Establish main empirical improvement. | G2 seed sweep | Experiments |
| Table 2 A4 high-L early stopping | Establish narrowed adaptive-depth result. | A4 cross-L sweep | Experiments |
| Table 3 evidence boundary table | Prevent overclaiming and show maturity. | paper evidence table | Experiments or Limitations |
| Fig./Table CRLB trend | Validate analytic FIM and high-SNR trend. | CRLB audit | Theory/Analysis |
| Appendix tables | G2 seed cells, A4 per-L/per-seed cells, A5 stress, DeepMIMO audit. | result directories | Appendix |

## Section Jobs

### Abstract

Write last. Must mention:

- model-driven sparse tensor unfolding;
- bounded off-grid refinement;
- high-L early stopping only as a scoped efficiency result;
- local synthetic/off-grid validation;
- no unsupported DeepMIMO or hardware claim.

Avoid packing every metric into the abstract. Use one headline G2 number and one A4 efficiency number at most.

### 1. Introduction

Job: motivate joint channel/target estimation and introduce the four-element fusion gap.

Required content:

- mmWave MIMO-OFDM ISAC needs joint communication/sensing estimation;
- sparse angle-delay-Doppler tensor is a natural shared representation;
- prior work covers pieces, but not this exact combination of tensor OMP unfolding, bounded off-grid refinement, permutation-invariant joint loss, and scoped early stopping;
- contributions C1-C4 with claim boundaries.

Must not include:

- “first ever” phrasing;
- DeepMIMO performance;
- global IA-AUD optimality.

### 2. Related Work

Job: establish novelty boundary without overreach.

Subsections:

1. Sparse and tensor-based mmWave/ISAC estimation.
2. Deep unfolding for wireless estimation.
3. Off-grid sparse recovery and physical refinement.
4. ISAC learning objectives and permutation-invariant multi-target losses.

Open task: add verified 2024-2026 citations and BibTeX. Current table is structural only.

### 3. System Model

Job: define the benchmark and problem enough that results are interpretable.

Required content:

- MIMO-OFDM ISAC signal model;
- FDMA virtual array assumption and spectral-efficiency trade-off;
- angle-delay-Doppler tensor dictionary;
- target/channel parameter extraction;
- dataset/evaluation regimes: local synthetic Set A and blocked external Set E.

Appendix bridge: detailed FDMA/DDM/TDM trade-off table can move to appendix if main text becomes crowded.

### 4. Proposed Method

Job: teach the estimator and why it preserves interpretability.

Subsections:

1. Tensor-OMP baseline.
2. T-OMP-Net unfolding.
3. Bounded off-grid refinement.
4. Hungarian permutation-invariant joint loss.
5. High-L plateau early stopping.

Required wording:

- A4 gate is “high-L/platform early stopping for L>=32”.
- The gate uses depth as FLOPs proxy because local-search kernel is repeated each layer.

### 5. Theory

Job: provide modest, correct, defensible theory.

Subsections:

1. Off-grid mismatch lemma under support condition.
2. Depth-identifiability trade-off, not closed-form optimal depth.
3. 5L FIM/CRLB formulation and numerical validation bridge.

Must not include:

- old v2.3 closed-form `K*(L)`;
- asymptotic efficiency for all multi-target settings.

### 6. Experiments

Job: show the main pattern and its boundaries.

Recommended order:

1. Setup and metrics.
2. G2 bounded off-grid refinement result.
3. A4 high-L early stopping result.
4. Kruskal/CRLB support.
5. Synthetic cross-scene fallback.
6. Boundary results: A5 downgrade and DeepMIMO blocker.

Each result block should answer:

- what question this block tests;
- what metric proves or limits it;
- what exact scope the result supports.

### 7. Limitations and Future Work

Job: convert known weaknesses into credible scope control.

Must include:

- DeepMIMO Set E blocked by missing scenario data and 5G Toolbox license;
- A5/HIR-JL not main-line ready;
- no hardware validation;
- local synthetic/off-grid sample budget;
- no full multi-target CRLB efficiency proof;
- possible next work: A4 SNR sweep, true DeepMIMO run, robust-training HIR-JL, DDM/TDM extension.

### 8. Conclusion

Job: restate what is supported, not what was originally planned.

Allowed:

- T-OMP-Net bounded off-grid refinement improves local estimation;
- high-L early stopping reduces depth for L>=32;
- supporting theory/evidence bounds the method.

Not allowed:

- “validated on DeepMIMO”;
- “global adaptive depth”;
- “robust to hardware impairments” without qualifier.

## Appendix Jobs

| Appendix | Job | Evidence |
|---|---|---|
| A | Reproducibility manifest and script map | `05_results/v2_3r_paper_evidence_table/` |
| B | G2 seed/cell table | `stage2_torch_locked_scale_g2_seed_sweep` |
| C | A4 cross-L and L=16 boundary | `stage3_a4_cross_l_plateau_gate_seed_sweep` |
| D | Lemma 1 proof details | v2.3R theory |
| E | Lemma 2 trade-off and `J(K)` | v2.3R theory |
| F | A5 stress and downgrade | `stage3_a5_combined_impairment_presmoke` |
| G | DeepMIMO access audit | `deepmimo_set_e_access_audit` |

## Writing-Blocking Gaps

| Gap | Blocks submission? | Action |
|---|---:|---|
| 2024-2026 verified citations/BibTeX | yes | Literature sprint before final manuscript. |
| DeepMIMO Set E data/toolbox | no for narrowed local paper; yes for original G3 | State blocker or resolve externally. |
| A4 SNR sweep | no | Optional strengthening. |
| `pytest` unavailable | no for manuscript text; yes for clean reproducibility | Install dependency or document environment. |
| Figures not rendered | yes for submission package | Create at least system schematic and result tables/plots. |

## Current Decision

Proceed to section drafting using the narrowed v2.3R claim set. Do not spend more work on A5 main-line claims unless a new robust-training experiment is deliberately selected. Do not wait for DeepMIMO if the target is a local-evidence Sensors-style submission; keep DeepMIMO as a transparent limitation and future validation item.
