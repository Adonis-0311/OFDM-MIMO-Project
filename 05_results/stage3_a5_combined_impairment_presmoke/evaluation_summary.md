# Stage 3 A5 Combined-Impairment Pre-Smoke Evaluation Summary

## Outcome Summary

This pre-smoke tests whether phase noise, IQ imbalance, and physical mutual coupling together create a large enough failure mode to justify HIR-JL robust training after phase-noise-only stress showed negligible degradation.

## evaluation_summary

- `research_question`: Do combined hardware impairments create enough NMSE degradation to keep A5/HIR-JL in the main Stage-3 line?
- `claim_update`: stress-only-supported for A5/HIR-JL combined-impairment evidence.
- `baseline_relation`: Clean-trained bounded refinement is compared against clean performance, impaired grid Tensor-OMP, and oracle-retuned alpha per profile.
- `failure_mode`: No execution failure; remaining limitation is synthetic impairment profile realism and small pre-smoke sample count.
- `mechanism_note`: nominal v2.3R combined stress is weak, but high stress exposes a failure mode; A5 should be appendix or stress-analysis rather than a main gate.
- `next_action`: Downgrade A5 from the main gate, but keep a high-stress appendix robustness check.
- `evidence_level`: Stage-3 pre-smoke evidence only.

## Key Metrics

- v2.3R combined degradation: 4.4395 dB
- high-stress combined degradation: 6.6036 dB
- v2.3R oracle-retune recovery: 0.0000 dB
- Wall-clock elapsed time: 28.16 s
