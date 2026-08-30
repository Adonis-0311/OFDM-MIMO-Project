# Stage 2 Minimal T-OMP-Net Smoke

- Config hash: `stage2-minimal-tompnet-20260624`

## Metrics

- `tensor_shape`: `128x16x32`
- `snr_db`: 20
- `n_trials_per_l`: `6`
- `mean_gain_db`: 7.32634
- `min_gain_db`: 6.26376
- `mean_permutation_loss`: 48.5994
- `controlled_permutation_loss_delta`: 0

## Notes

- This is a minimal deterministic T-OMP-Net smoke/proxy, not a trained neural network.
- It validates Pack 3 wiring: unfolded top-k layer shape, bounded off-grid refinement, LS amplitude update, and permutation-invariant loss.
- The mean permutation loss is a coordinate-error diagnostic; controlled_permutation_loss_delta verifies order invariance separately.
- G2 remains unproven until a trained T-OMP-Net achieves the required comparison under the locked metric contract.

## Artifacts

- `05_results\stage2_minimal_tompnet_smoke\stage2_minimal_tompnet_smoke.csv`
- `05_results\stage2_minimal_tompnet_smoke\run_manifest.json`
