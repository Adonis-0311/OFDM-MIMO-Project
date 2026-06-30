# Stage 3 / G3 Manifest

## Gate Status

| Gate item | Status | Evidence | Metric |
|---|---|---|---|
| A4 IA-AUD FLOPs/depth reduction | restricted-high-l-pass / global-claim-not-supported | `stage3_a4_high_l_plateau_gate` | held-out L=32 gate savings = 33.33%; NMSE gap = 0.3643 dB |
| A5 HIR-JL robustness value | main-gate-downgrade / appendix-high-stress-only | `stage3_a5_combined_impairment_presmoke` | nominal combined degradation = 4.4395 dB; high-stress degradation = 6.6036 dB |
| Paper-scale Kruskal identifiability sanity | on-grid-proxy-pass | `stage3_paper_scale_kruskal_proxy` | Kruskal proxy bound = 87; max L/Lmax = 0.7356; min support recall = 1.0 |
| Synthetic cross-scene generalization fallback | local-synthetic-pass / not-deepmimo | `stage3_synthetic_cross_scene_generalization` | min target gain vs grid = 5.8504 dB; max gap vs target oracle = 0.4077 dB |
| 5L CRLB asymptotic tightness | supported-pilot / single-target-pilot | `stage3_crlb_asymptotic_tightness` | max FIM relative error = 5.7304e-10; 30 dB mean RMSE/CRLB ratio = 1.0067; mean slope error = 0.0067 |
| DeepMIMO Set E external validation | access-ready / o1-weak / i3-partial | `deepmimo_source_alpha_seed_campaign` | readiness = ready_open_source; dataset files = 4188; O1 five-seed gain = 1.3235 dB; I3 five-seed gain = 6.7014 dB; I3 min cell = -0.2412 dB |

## Decision

Stage 3 has enough local evidence to support a restricted A4 high-L early-stop mechanism and an on-grid paper-scale Kruskal sanity row. A5 should be downgraded from the main gate and retained only as high-stress robustness appendix evidence.

The synthetic cross-scene fallback supports local portability of the source-trained bounded off-grid alpha under controlled synthetic shifts, but it is not ray-traced, not standards-aligned CDL, and not DeepMIMO Set E evidence.

The 5L CRLB asymptotic tightness audit supports analytic derivative correctness and single-target high-SNR trend consistency. It remains pilot evidence, not a full multi-target efficiency proof.

DeepMIMO access is ready and the five-seed x 100-user scalar source-alpha proxy campaign records weak O1_60 support and partial I3_60 support. This removes the data-access blocker but does not establish final Set E performance; the full trained estimator and physical angle/delay metrics remain required.

Acceptance audit: `05_results/stage3_g3_manifest/acceptance_audit.md`.
