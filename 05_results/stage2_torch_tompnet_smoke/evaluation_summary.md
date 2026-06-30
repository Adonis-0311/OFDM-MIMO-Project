# Stage 2 PyTorch T-OMP-Net Smoke Evaluation Summary

## Outcome Summary

The PyTorch CPU smoke validates a real `nn.Module` + Adam training path for bounded off-grid refinement. On held-out samples, the trained smoke layer improves over grid Tensor-OMP by more than the G2 directional threshold, while remaining explicitly smaller than the final full T-OMP-Net training campaign.

## evaluation_summary

- `research_question`: Can a PyTorch-backed trainable T-OMP-Net smoke learn a bounded off-grid refinement parameter and improve held-out SNR=20 dB samples?
- `claim_update`: Supported for PyTorch trainable smoke and G2-directional improvement; inconclusive for full paper-scale neural T-OMP-Net training.
- `baseline_relation`: Compared against grid Tensor-OMP on the same held-out samples.
- `failure_mode`: No execution failure after reducing CPU smoke size. Remaining limitation is scale: tensor shape is 32x4x8 and L is {2,4}.
- `next_action`: Expand to the locked Stage-2 scale and add curriculum/layer-depth experiments before promoting G2 to fully accepted.
- `evidence_level`: PyTorch smoke evidence achieved; full G2 remains pending at larger scale.

## Key Metrics

- PyTorch version: 2.8.0+cpu
- Tensor shape: 32x4x8
- Mean held-out gain over grid Tensor-OMP: 8.0954 dB
- Minimum L-cell held-out gain: 7.5678 dB
- Mean train NMSE improvement: 2.1746 dB
- Epochs: 8

