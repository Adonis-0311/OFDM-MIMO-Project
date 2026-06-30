# Stage 2 Minimal T-OMP-Net Smoke Evaluation Summary

## Outcome Summary

The first Stage 2 smoke validates the Pack 3 execution path and shows a clear off-grid improvement signal at 20 dB. It is not a trained T-OMP-Net result and therefore does not yet prove G2.

## evaluation_summary

- `research_question`: Can the minimal T-OMP-Net path combine unfolded top-k selection, bounded off-grid refinement, LS amplitude update, and permutation-invariant loss reporting?
- `claim_update`: Supported for Stage 2 wiring and off-grid mechanism direction; inconclusive for full G2 trained-network superiority.
- `baseline_relation`: Compared against grid Tensor-OMP on the same off-grid samples.
- `failure_mode`: No execution failure. Remaining limitation is that this is a deterministic proxy, and coordinate permutation loss remains a diagnostic rather than a trained loss outcome.
- `next_action`: Implement a trainable or parameterized layer path and a cleaner target-coordinate assignment metric before claiming G2.
- `evidence_level`: Stage 2 minimum smoke evidence achieved; G2 remains pending.

## Key Metrics

- SNR: 20 dB
- Tensor shape: 128x16x32
- Mean gain over grid Tensor-OMP: 7.3263 dB
- Minimum L-cell gain: 6.2638 dB
- Controlled permutation loss delta: 0.0

