# Stage 2 PyTorch Locked-Scale G2 Run

- Config hash: `stage2-torch-locked-scale-g2-20260624`

## Metrics

- `tensor_shape`: `128x16x32`
- `snr_db`: 20
- `torch_version`: `2.8.0+cpu`
- `seed`: `20260624`
- `l_values`: `[2, 4, 8]`
- `n_train_per_l`: `2`
- `n_test_per_l`: `2`
- `epochs`: `6`
- `lr`: 0.08
- `alpha`: 0.641861
- `mean_test_gain_vs_grid_db`: 6.36462
- `min_test_gain_vs_grid_db`: 5.16242
- `mean_train_improvement_db`: 1.08626
- `elapsed_seconds`: 8.02689

## Notes

- Locked-scale PyTorch run uses nn.Module + Adam at 128x16x32 across L={2,4,8}.
- The fast loss is algebraically equivalent to the LS reconstruction loss but solves LxL normal equations instead of a tall 65536xL least-squares problem.
- This run addresses the previous PyTorch locked-scale CPU blocker; sample count remains deliberately small for a bounded local G2 gate run.

## Artifacts

- `05_results\stage2_torch_locked_scale_g2\stage2_torch_locked_scale_g2.csv`
- `05_results\stage2_torch_locked_scale_g2\train_history.csv`
- `05_results\stage2_torch_locked_scale_g2\run_manifest.json`
