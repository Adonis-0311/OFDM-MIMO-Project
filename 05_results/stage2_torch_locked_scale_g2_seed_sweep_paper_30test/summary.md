# Stage 2 PyTorch Locked-Scale G2 Seed Sweep

- Config hash: `stage2-torch-locked-scale-g2-seed-sweep-20260625`

## Metrics

- `tensor_shape`: `128x16x32`
- `snr_db`: 20
- `torch_version`: `2.12.1+cpu`
- `seeds`: `[20260624, 20260625, 20260626, 20260627, 20260628]`
- `l_values`: `[2, 4, 8]`
- `n_train_per_l`: `2`
- `n_test_per_l`: `30`
- `epochs`: `6`
- `lr`: 0.08
- `mean_l_cell_gain_vs_grid_db`: 5.89563
- `std_l_cell_gain_vs_grid_db`: 0.359509
- `min_l_cell_gain_vs_grid_db`: 5.38635
- `max_l_cell_gain_vs_grid_db`: 6.82772
- `min_seed_mean_gain_vs_grid_db`: 5.81126
- `seed_mean_gain_ci95_low_db`: 5.78297
- `seed_mean_gain_ci95_high_db`: 6.00829
- `mean_train_improvement_db`: 1.18706
- `elapsed_seconds`: 229.731

## Notes

- Multi-seed strengthening for the bounded local G2 gate; it does not replace external-channel validation.
- The baseline remains grid Tensor-OMP on the same held-out samples for every seed and L cell.
- Sample count is deliberately modest so the run stays CPU-feasible while testing seed stability.

## Artifacts

- `05_results\stage2_torch_locked_scale_g2_seed_sweep_paper_30test\stage2_torch_locked_scale_g2_seed_sweep_cells.csv`
- `05_results\stage2_torch_locked_scale_g2_seed_sweep_paper_30test\stage2_torch_locked_scale_g2_seed_sweep_seeds.csv`
- `05_results\stage2_torch_locked_scale_g2_seed_sweep_paper_30test\run_manifest.json`
