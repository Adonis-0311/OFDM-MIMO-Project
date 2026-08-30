# Stage 3 A5 HIR-JL Phase-Noise Pre-Smoke Evaluation Summary

## Outcome Summary

This pre-smoke trains the bounded off-grid refinement alpha on clean samples, then evaluates the same path under phase-noise stress. It also reports an oracle-retuned alpha per sigma to separate clean-model fragility from simple one-parameter recalibration.

## evaluation_summary

- `research_question`: Does phase noise create enough NMSE degradation to justify HIR-JL robust training?
- `claim_update`: downgrade for A5/HIR-JL problem-existence evidence.
- `baseline_relation`: Clean-trained bounded refinement is compared against its clean sigma=0 performance, grid Tensor-OMP under the same impairment, and oracle-retuned alpha per sigma.
- `failure_mode`: No execution failure; remaining limitation is phase-noise-only impairment and small pre-smoke sample count.
- `mechanism_note`: sigma_phi up to 2 degrees barely degrades the clean-trained path, so HIR-JL should be downgraded.
- `next_action`: Do not invest in phase-noise-only HIR-JL; run one mutual-coupling/IQ stress check before deciding whether any A5 robust-training line remains.
- `evidence_level`: Stage-3 pre-smoke evidence only.

## Key Metrics

- Clean-trained degradation at sigma_phi=1 degree: 0.0000 dB
- Clean-trained degradation at sigma_phi=2 degrees: 0.0000 dB
- Oracle retuning recovery at sigma_phi=2 degrees: 0.0000 dB
- Wall-clock elapsed time: 27.84 s
