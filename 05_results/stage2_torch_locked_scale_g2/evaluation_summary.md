# Stage 2 PyTorch Locked-Scale G2 Evaluation Summary

## Outcome Summary

The locked-scale PyTorch G2 run trains a real `nn.Module` bounded off-grid refinement layer with Adam at tensor shape `128x16x32` across the curriculum `L={2,4,8}`. The optimized loss keeps the same LS-estimator objective but uses normal equations so CPU execution is feasible.

## evaluation_summary

- `research_question`: Can the PyTorch trainable T-OMP-Net refinement path run at the locked Stage-2 scale and beat grid Tensor-OMP on held-out SNR=20 dB samples?
- `claim_update`: supported for locked-scale PyTorch G2 evidence.
- `baseline_relation`: Compared against grid Tensor-OMP on the same held-out samples for each L cell.
- `failure_mode`: No execution failure in the optimized normal-equation PyTorch path; remaining limitation is small CPU sample count.
- `next_action`: Run a G2 acceptance audit or expand seeds/test counts if stronger statistical evidence is required before Stage 3.
- `evidence_level`: Locked-scale PyTorch trainable evidence achieved; broader statistical campaign remains optional polish.

## Key Metrics

- Tensor shape: 128x16x32
- L curriculum: {2,4,8}
- Mean held-out gain over grid Tensor-OMP: 6.3646 dB
- Minimum held-out L-cell gain: 5.1624 dB
- Mean train NMSE improvement: 1.0863 dB
- Wall-clock elapsed time: 8.03 s
