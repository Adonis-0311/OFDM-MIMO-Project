# Stage 2 PyTorch Locked-Scale G2 Seed Sweep Evaluation Summary

## Outcome Summary

This run repeats the locked-scale PyTorch trainable refinement gate across multiple random seeds at tensor shape `128x16x32` and L={2,4,8}. It is a paper-strengthening statistical check for the already accepted bounded G2 gate.

## evaluation_summary

- `research_question`: Is the locked-scale PyTorch T-OMP-Net gain over grid Tensor-OMP stable across seeds at SNR=20 dB?
- `claim_update`: supported for multi-seed locked-scale G2 stability.
- `baseline_relation`: Compared against grid Tensor-OMP on the same held-out samples for every seed and L cell.
- `failure_mode`: No execution failure if the run completes; remaining limitation is still CPU-scale synthetic sample count.
- `next_action`: Use this as paper-strengthening evidence for G2, then prioritize narrowed A4 high-L validation or manuscript claim alignment.
- `evidence_level`: Multi-seed local statistical strengthening, not external-channel validation.

## Key Metrics

- Seeds: [20260624, 20260625, 20260626, 20260627, 20260628]
- Mean L-cell gain over grid Tensor-OMP: 6.1726 dB
- Std. L-cell gain over grid Tensor-OMP: 0.9071 dB
- Minimum L-cell gain over grid Tensor-OMP: 4.4735 dB
- Minimum per-seed mean gain: 5.7428 dB
- Mean train NMSE improvement: 1.1996 dB
- Wall-clock elapsed time: 37.17 s
