# Stage 2 Curriculum T-OMP-Net G2 Evaluation Summary

## Outcome Summary

The locked-scale curriculum validation keeps the Stage-2 tensor shape at `128x16x32` and trains one shared bounded off-grid refinement alpha across `L={2,4,8}`. It is a stronger scale/curriculum check than the earlier single-smoke runs, while still remaining a NumPy/LS proxy rather than the final full neural T-OMP-Net campaign.

## evaluation_summary

- `research_question`: Does a shared curriculum-trained bounded off-grid refinement improve held-out SNR=20 dB samples at the locked Stage-2 scale?
- `claim_update`: supported for locked-scale curriculum proxy evidence; PyTorch locked-scale evidence remains resource-limited.
- `baseline_relation`: Compared against grid Tensor-OMP on the same held-out samples for each seed and L cell.
- `failure_mode`: PyTorch locked-scale prototype exceeded the local CPU timeout budget of 180 seconds; NumPy cached validation completed.
- `next_action`: Optimize or batch the PyTorch training path before promoting G2 from strong proxy support to full acceptance.
- `evidence_level`: Solid locked-scale curriculum proxy; full PyTorch/curriculum acceptance still pending.

## Key Metrics

- Tensor shape: 128x16x32
- L curriculum: {2,4,8}
- Mean held-out gain over grid Tensor-OMP: 7.4964 dB
- Minimum held-out L/seed-cell gain: 5.0464 dB
- Mean shared curriculum alpha: 0.9000
