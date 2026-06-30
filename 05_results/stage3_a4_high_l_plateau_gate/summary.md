# Stage 3 A4 High-L Plateau Gate

- Config hash: `stage3-a4-high-l-plateau-gate-20260624`

## Metrics

- `tensor_shape`: `128x16x32`
- `snr_db`: 20
- `seed`: `20260624`
- `n_targets`: `32`
- `n_train`: `6`
- `n_test`: `6`
- `fixed_depth`: `8`
- `min_depth`: `3`
- `radii`: `[0.45, 0.28, 0.18, 0.11, 0.07, 0.045, 0.03, 0.02]`
- `search_points`: `3`
- `threshold_candidates_db`: `[0.05, 0.1, 0.2, 0.35, 0.5, 0.75, 1.0]`
- `selected_threshold_db`: 0.75
- `nmse_tolerance_db`: 0.5
- `train_metrics`: `{'mean_depth': 5.833333333333333, 'mean_nmse_gap_db': 0.37201306988396016, 'mean_depth_savings_percent': 27.083333333333332, 'min_depth_savings_percent': 12.5, 'max_depth_savings_percent': 37.5}`
- `test_metrics`: `{'mean_depth': 5.333333333333333, 'mean_nmse_gap_db': 0.3643202083828558, 'mean_depth_savings_percent': 33.333333333333336, 'min_depth_savings_percent': 25.0, 'max_depth_savings_percent': 37.5}`
- `elapsed_seconds`: 65.8615

## Notes

- This is a narrowed high-L A4 gate test, not a global IA-AUD claim.
- The gate stops when the incremental NMSE improvement falls below a trained scalar threshold after a minimum depth.
- Depth is used as the FLOPs proxy because each refinement layer performs the same local-search kernel.

## Artifacts

- `05_results\stage3_a4_high_l_plateau_gate\stage3_a4_high_l_plateau_gate_thresholds.csv`
- `05_results\stage3_a4_high_l_plateau_gate\stage3_a4_high_l_plateau_gate_samples.csv`
- `05_results\stage3_a4_high_l_plateau_gate\run_manifest.json`
