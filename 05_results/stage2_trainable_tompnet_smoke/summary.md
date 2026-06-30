# Stage 2 Trainable T-OMP-Net Smoke

- Config hash: `stage2-trainable-alpha-20260624`

## Metrics

- `tensor_shape`: `128x16x32`
- `snr_db`: 20
- `n_train_per_l`: `5`
- `n_test_per_l`: `6`
- `mean_test_gain_vs_grid_db`: 6.92933
- `min_test_gain_vs_grid_db`: 5.8605
- `mean_abs_gap_vs_full_refine_db`: 0.328759

## Notes

- NumPy trainable smoke learns a bounded off-grid interpolation alpha over curriculum L values.
- This is a parameterized/training-path proof of wiring because PyTorch is unavailable in the current environment.
- Full G2 still requires the planned trainable T-OMP-Net layer/curriculum implementation once PyTorch is installed.

## Artifacts

- `05_results\stage2_trainable_tompnet_smoke\stage2_trainable_tompnet_smoke.csv`
- `05_results\stage2_trainable_tompnet_smoke\run_manifest.json`
