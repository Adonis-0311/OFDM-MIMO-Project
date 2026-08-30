# Stage 2 Trainable T-OMP-Net Smoke Evaluation Summary

## Outcome Summary

The NumPy trainable smoke learns a bounded off-grid interpolation parameter on training samples and preserves strong held-out gains over grid Tensor-OMP. This advances Stage 2 beyond a deterministic proxy, while still falling short of the planned PyTorch T-OMP-Net training campaign.

## evaluation_summary

- `research_question`: Can a trainable/parameterized T-OMP-Net smoke learn an off-grid refinement control that improves held-out SNR=20 dB samples?
- `claim_update`: Supported for parameterized train/test wiring and G2-directional off-grid gain; inconclusive for full trained neural T-OMP-Net G2.
- `baseline_relation`: Compared against grid Tensor-OMP on the same held-out samples.
- `failure_mode`: PyTorch is unavailable in the current environment, so the result uses a NumPy alpha-calibration surrogate.
- `next_action`: Install PyTorch or add a pure-NumPy differentiable layer surrogate if full PyTorch remains unavailable.
- `evidence_level`: Stage 2 trainable smoke evidence achieved; full G2 remains pending.

## Key Metrics

- Mean held-out gain over grid Tensor-OMP: 6.9293 dB
- Minimum L-cell held-out gain: 5.8605 dB
- Mean absolute gap to full local refinement: 0.3288 dB
- Train samples per L: 5
- Test samples per L: 6

