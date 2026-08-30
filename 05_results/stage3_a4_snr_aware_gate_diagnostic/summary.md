# Stage 3 A4 SNR-Aware Gate Diagnostic

- Config hash: `stage3-a4-snr-aware-gate-diagnostic-20260625`

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
- `threshold_candidates_db`: `[0.005, 0.01, 0.02, 0.035, 0.05, 0.075, 0.1, 0.15, 0.2, 0.25, 0.35, 0.5, 0.75, 1.0]`
- `scalar_thresholds_by_snr`: `{10.0: 0.75, 20.0: 0.75, 30.0: 1.0}`
- `selected_knn_k`: `1`
- `selected_knn_vote_threshold`: 0.35
- `knn_train_mean_savings_percent`: 23.9583
- `knn_train_max_gap_db`: 0.491919
- `knn_train_feasible`: 1
- `knn_min_snr_mean_depth_savings_percent`: 21.875
- `knn_max_snr_nmse_gap_db`: 0.655772
- `scalar_min_snr_mean_depth_savings_percent`: 31.25
- `scalar_max_snr_nmse_gap_db`: 0.998554
- `oracle_min_snr_mean_depth_savings_percent`: 21.875
- `oracle_max_snr_nmse_gap_db`: 0.490573
- `elapsed_seconds`: 149.431

## Notes

- Writing-facing A4 diagnostic after scalar-threshold frontier failure.
- The learned gate is a lightweight kNN sequential stopping policy using SNR, depth, recent improvement, and cumulative gain features.
- The per-curve quality oracle is a diagnostic upper bound that can use fixed-depth quality after the fact; it is not deployable.

## Artifacts

- `05_results\stage3_a4_snr_aware_gate_diagnostic\stage3_a4_snr_aware_gate_policy_samples.csv`
- `05_results\stage3_a4_snr_aware_gate_diagnostic\stage3_a4_snr_aware_gate_curves.csv`
- `05_results\stage3_a4_snr_aware_gate_diagnostic\stage3_a4_snr_aware_gate_summary.csv`
- `05_results\stage3_a4_snr_aware_gate_diagnostic\run_manifest.json`
