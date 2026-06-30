# Stage 2 Curriculum T-OMP-Net G2 Validation

- Config hash: `stage2-curriculum-g2-20260624`

## Metrics

- `tensor_shape`: `128x16x32`
- `snr_db`: 20
- `seeds`: `[20260624, 20260625]`
- `l_values`: `[2, 4, 8]`
- `n_train_per_l`: `2`
- `n_test_per_l`: `3`
- `candidate_alphas`: `[0.0, 0.19999999999999998, 0.39999999999999997, 0.6, 0.7999999999999999, 0.9999999999999999, 1.2]`
- `mean_shared_alpha`: 0.9
- `mean_test_gain_vs_grid_db`: 7.4964
- `min_test_gain_vs_grid_db`: 5.04638
- `num_l_seed_cells`: `6`
- `torch_locked_scale_timeout_seconds`: `180`

## Notes

- Locked-scale curriculum proxy trains one shared bounded off-grid alpha across L={2,4,8}.
- Cached local-refinement bins avoid repeating the expensive 3-D local search for every candidate alpha.
- This strengthens G2 scale/curriculum evidence, but it is still not the final full PyTorch T-OMP-Net training campaign.
- A direct PyTorch locked-scale prototype exceeded the local CPU timeout budget and remains an explicit resource blocker.

## Artifacts

- `05_results\stage2_curriculum_tompnet_g2\stage2_curriculum_tompnet_g2.csv`
- `05_results\stage2_curriculum_tompnet_g2\stage2_curriculum_tompnet_g2_samples.csv`
- `05_results\stage2_curriculum_tompnet_g2\run_manifest.json`
