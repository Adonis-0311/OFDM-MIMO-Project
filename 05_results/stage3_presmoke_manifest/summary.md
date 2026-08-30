# Stage 3 Pre-Smoke Manifest

## Gate Status

| Gate item | Status | Evidence | Metric |
|---|---|---|---|
| A4 IA-AUD has real adaptive-depth opportunity | pre-smoke-supported / mechanism-direction-revised | `stage3_a4_depth_presmoke` | saturation depths {2:8, 8:8, 32:5}; depth spread = 3 |
| A4 IA-AUD meets >=25% average FLOPs/depth reduction at similar NMSE | oracle-upper-bound-inconclusive / global-target-not-met | `stage3_a4_oracle_earlystop` | overall oracle savings = 15.0%; L=32 savings = 27.5%; mean NMSE gap = 0.1820 dB |
| A4 high-L/platform gate meets >=25% depth reduction at similar NMSE | restricted-high-l-pass / global-claim-not-supported | `stage3_a4_high_l_plateau_gate` | held-out L=32 gate savings = 33.33%; NMSE gap = 0.3643 dB |
| A5 phase-noise-only HIR-JL has strong value | pre-smoke-downgrade | `stage3_a5_hirjl_presmoke` | degradation at 1 deg = 0.0000 dB; degradation at 2 deg = 0.0000 dB |
| A5 combined-impairment HIR-JL still needs one check | stress-only-supported / main-gate-downgrade | `stage3_a5_combined_impairment_presmoke` | v2.3R combined degradation = 4.4395 dB; high-stress degradation = 6.6036 dB |

## Decision

Stage 3 pre-smoke evidence supports a narrowed A4 narrative: adaptive-depth opportunity exists, the global >=25% average depth/FLOPs target is not proven, but a high-L plateau gate reaches 33.33% held-out depth savings within 0.3643 dB of fixed K=8. A4 should be framed as a high-L/platform-sample early-stop mechanism, not a global IA-AUD claim.

The combined-impairment check does not meet the 5 dB nominal v2.3R main-gate threshold, but high stress does expose a 6.6036 dB failure mode. Recommendation: remove A5 from the main Stage-3 gate and keep it as an appendix/high-stress robustness analysis.
