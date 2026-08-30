# Stage 3 / G3 Local Evidence Acceptance Audit

Generated: 2026-06-27

## Scope

This audit evaluates the current V2.3R Stage-3/G3 evidence package against the planned gate. It separates complete local evidence, scaled external proxy evidence, and work still needed for final external validation. It does not claim final DeepMIMO Set E performance.

## Gate Verdict

G3 is partially accepted as a local evidence package, not fully accepted as the original full G3 gate.

## Requirement Checks

| Requirement | Evidence | Verdict | Notes |
|---|---|---|---|
| IA-AUD reduces average FLOPs/depth by at least 25% at similar NMSE | `05_results/stage3_a4_high_l_plateau_gate/`, `05_results/stage3_a4_oracle_earlystop/` | restricted-pass / global-not-supported | High-L L=32 plateau gate saves 33.33% depth with 0.3643 dB NMSE gap. Global oracle upper-bound saves only 15.0%, so no global IA-AUD claim is supported. |
| HIR-JL improves robustness under sigma_phi=2 degrees by at least 5 dB | `05_results/stage3_a5_hirjl_presmoke/`, `05_results/stage3_a5_combined_impairment_presmoke/` | main-gate-downgrade | Phase-noise-only degradation is effectively zero at 1 and 2 degrees. Nominal combined stress degrades by 4.4395 dB, below the 5 dB main-gate threshold. High stress degrades by 6.6036 dB, so A5 can remain appendix/high-stress evidence only. |
| Paper-scale 128x16x32 scan for L={2,4,8,16,32,64} | `05_results/stage3_paper_scale_kruskal_proxy/`, `05_results/paper_scale_tensor_omp_g1/` | pass-for-on-grid-proxy | Paper-scale Kruskal proxy bound is 87, max tested L/Lmax is 0.7356, and minimum support recall is 1.0. This supports on-grid paper-scale sanity, not off-grid or DeepMIMO proof. |
| Synthetic cross-scene generalization fallback | `05_results/stage3_synthetic_cross_scene_generalization/` | local-synthetic-pass / not-deepmimo | Source-trained bounded off-grid alpha transfers across controlled synthetic shifts with minimum target gain versus grid of 5.8504 dB and maximum target gap versus target-oracle of 0.4077 dB. This is useful fallback evidence, but it is not ray-traced DeepMIMO validation. |
| 5L CRLB high-SNR asymptotic trend | `05_results/stage3_crlb_asymptotic_tightness/`, `05_results/crlb_5l_fim_validation/`, `05_results/crlb_5l_monte_carlo/` | supported-pilot / single-target-only | Analytic-vs-numeric FIM relative error is 5.7304e-10, 30 dB mean RMSE/CRLB ratio is 1.0067, and mean absolute RMSE slope error versus the expected -0.05 per dB scaling is 0.0067. This supports single-target trend consistency, not multi-target efficiency proof. |
| DeepMIMO Set E channel NMSE plus angle/delay RMSE | `05_results/deepmimo_set_e_access_audit/`, `05_results/deepmimo_source_alpha_seed_campaign/` | access-ready / O1-weak / I3-partial | The open-source path finds 4188 files. Five 100-user seeds give O1 scalar-alpha gain 1.3235 dB [95% CI 1.2538, 1.3931] with min cell 0.8554 dB, while I3 gives 6.7014 dB [6.4660, 6.9368] but min cell -0.2412 dB. This is a scalar-alpha proxy, not full trained channel-plus-physical-parameter evidence. |

## Evidence Integrity

- Every accepted or downgraded claim points to a run directory with a CSV, summary, run manifest, and evaluation summary; DeepMIMO additionally retains a separate access audit.
- A4 uses depth as a FLOPs proxy because each refinement layer runs the same local-search kernel.
- A5 high-stress robustness is not promoted to a main result because nominal v2.3R stress falls below the planned threshold.
- Kruskal evidence is bounded to on-grid FFT Tensor-OMP and should not be used as external generalization evidence.
- Synthetic cross-scene evidence is bounded to controlled local off-grid simulation and should not be used as DeepMIMO, CDL, or real-channel evidence.
- CRLB tightness evidence is bounded to single-target high-SNR trend consistency and analytic derivative validation.
- DeepMIMO data access is no longer blocked. O1 has weak scaled scalar-alpha proxy support; I3 is partial because a negative-gain cell and weak support recall remain visible.

## Current Claim Package

Supported local claims:

1. G2 is accepted for the bounded local Stage-2 gate.
2. A4 is viable only as a restricted high-L/platform early-stop mechanism.
3. A5 should be downgraded from main gate to appendix/high-stress robustness.
4. Paper-scale on-grid Kruskal sanity is supported for 128x16x32 and L up to 64.
5. Source-trained bounded off-grid alpha has local synthetic cross-scene portability under controlled shifts.
6. Analytic 5L FIM and single-target high-SNR CRLB trend consistency are supported as pilot evidence.
7. DeepMIMO O1_60 has weak scaled scalar-alpha proxy support across five 100-user seeds; I3_60 has partial support with an explicit local failure boundary.

Unsupported or blocked claims:

1. Global IA-AUD FLOPs reduction across L={2,8,32}.
2. Phase-noise-only HIR-JL as a main contribution.
3. Full nominal-v2.3R HIR-JL main-gate robustness.
4. Treating synthetic cross-scene portability as external channel validation.
5. Full multi-target 5L CRLB asymptotic efficiency.
6. Final DeepMIMO Set E performance from the full trained estimator with physical angle/delay RMSE.

## Decision

Proceed with the narrowed Stage-3 evidence package and the scaled DeepMIMO proxy only if the manuscript preserves the weak/partial classifications. To fully satisfy the original G3 gate, attach the full trained estimator and record physical angle/delay RMSE; data/toolbox readiness is no longer the blocker.
