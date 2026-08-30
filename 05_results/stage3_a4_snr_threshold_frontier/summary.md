# Stage 3 A4 SNR Threshold Frontier

- Config hash: `stage3-a4-snr-threshold-frontier-20260625`

## Metrics

- `tensor_shape`: `128x16x32`
- `n_targets`: `32`
- `snr_values_db`: `[10.0, 20.0, 30.0]`
- `seeds`: `[20260624, 20260625]`
- `n_train`: `2`
- `n_test`: `2`
- `fixed_depth`: `8`
- `min_depth`: `3`
- `nmse_tolerance_db`: 0.5
- `guarded_train_tolerance_db`: 0.35
- `threshold_candidates_db`: `[0.005, 0.01, 0.02, 0.035, 0.05, 0.075, 0.1, 0.15, 0.2, 0.25, 0.35, 0.5, 0.75, 1.0]`
- `standard_min_snr_mean_depth_savings_percent`: 15.625
- `standard_max_snr_nmse_gap_db`: 0.6691
- `guarded_min_snr_mean_depth_savings_percent`: 9.375
- `guarded_max_snr_nmse_gap_db`: 0.34422
- `oracle_min_snr_mean_depth_savings_percent`: 0
- `oracle_max_snr_nmse_gap_db`: 0.455448
- `elapsed_seconds`: 146.695

## Notes

- Diagnostic frontier for the A4 SNR boundary; test-oracle rows are not deployable evidence.
- Standard-train selection maximizes train savings under the 0.5 dB mean-gap tolerance.
- Guarded-train selection uses a stricter 0.35 dB train mean-gap guard.

## Artifacts

- `05_results\stage3_a4_snr_threshold_frontier\stage3_a4_snr_threshold_frontier_policy_cells.csv`
- `05_results\stage3_a4_snr_threshold_frontier\stage3_a4_snr_threshold_frontier_thresholds.csv`
- `05_results\stage3_a4_snr_threshold_frontier\stage3_a4_snr_threshold_frontier_summary.csv`
- `05_results\stage3_a4_snr_threshold_frontier\run_manifest.json`
