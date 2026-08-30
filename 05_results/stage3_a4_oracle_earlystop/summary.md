# Stage 3 A4 IA-AUD Oracle Early-Stop

- Config hash: `stage3-a4-oracle-earlystop-20260624`

## Metrics

- `tensor_shape`: `128x16x32`
- `snr_db`: 20
- `seed`: `20260624`
- `l_values`: `[2, 8, 32]`
- `n_trials_per_l`: `5`
- `fixed_depth`: `8`
- `depth_values`: `[0, 1, 2, 3, 4, 5, 6, 7, 8]`
- `radii`: `[0.45, 0.28, 0.18, 0.11, 0.07, 0.045, 0.03, 0.02]`
- `search_points`: `3`
- `nmse_tolerance_db`: 0.5
- `mean_oracle_depth`: 6.8
- `mean_nmse_gap_vs_fixed_db`: 0.182018
- `mean_depth_savings_percent`: 15
- `min_depth_savings_percent`: 0
- `max_depth_savings_percent`: 37.5
- `elapsed_seconds`: 39.6045

## Notes

- This is an oracle upper-bound run for IA-AUD early stopping, not a trained gating model.
- Depth is used as the FLOPs proxy because each refinement layer performs the same local-search kernel.
- The oracle stop chooses the earliest K within 0.5 dB of the fixed K=8 NMSE on the same sample.

## Artifacts

- `05_results\stage3_a4_oracle_earlystop\stage3_a4_oracle_earlystop.csv`
- `05_results\stage3_a4_oracle_earlystop\stage3_a4_oracle_earlystop_samples.csv`
- `05_results\stage3_a4_oracle_earlystop\run_manifest.json`
