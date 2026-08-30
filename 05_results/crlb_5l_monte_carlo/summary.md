# 5L CRLB Monte Carlo

- Config hash: `5l-mc-20260624`

## Metrics

- `tensor_shape`: `128x16x32`
- `n_trials_per_snr`: `8`
- `snr_points`: `10,20,30`
- `mean_ratio_at_30db`: 1.0067
- `max_ratio_at_30db`: 1.50087
- `angle_rmse_drop_10db_to_30db`: 9.928

## Notes

- Monte Carlo uses a single off-grid target and ML-style multiresolution local search initialized by FFT Tensor-OMP.
- The run checks estimator RMSE scaling against the analytic 5L CRLB; it is a pilot, not yet a large-sample efficiency proof.
- Ratios above 1 are expected because the search grid is finite and n_trials is intentionally small for Stage-1 turnaround.

## Artifacts

- `05_results\crlb_5l_monte_carlo\crlb_5l_monte_carlo.csv`
- `05_results\crlb_5l_monte_carlo\run_manifest.json`
