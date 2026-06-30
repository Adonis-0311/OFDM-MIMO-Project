# Paper-Scale Off-Grid Stress Evaluation Summary

## Outcome Summary

The paper-scale off-grid stress test shows that bounded local refinement improves measurement-domain NMSE over coarse grid Tensor-OMP picks on the 128x16x32 tensor. This supports the V2.3R expectation that off-grid refinement is a real mechanism rather than decorative complexity.

## evaluation_summary

- `research_question`: Does bounded local refinement reduce off-grid mismatch on paper-scale angle-delay-Doppler tensors?
- `claim_update`: Supported for L in {2,4,8,16} at 20 dB with offset radius 0.35 bins; not yet tested for L=32/64 due to current local-search cost.
- `baseline_relation`: Builds on the on-grid paper-scale Tensor-OMP scan and tests the expected off-grid failure mode directly.
- `failure_mode`: No execution failure; scope remains bounded to measurement-domain NMSE and deterministic local search.
- `next_action`: Extend off-grid stress to faster batched refinement or a selected L=32/64 stress subset.
- `evidence_level`: Solid for low-to-mid target-count off-grid mechanism, partial for full high-L paper-scale coverage.

## Key Metrics

- Mean coarse grid NMSE: -5.4308 dB
- Mean refined NMSE: -12.9676 dB
- Mean refinement gain: 7.5368 dB
- Minimum L-cell refinement gain: 6.9946 dB
- Tensor shape: 128x16x32

