# Stage 3 A4 SNR Plateau Gate Seed Sweep

- Config hash: `stage3-a4-snr-plateau-gate-seed-sweep-20260625`

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
- `threshold_candidates_db`: `[0.05, 0.1, 0.2, 0.35, 0.5, 0.75, 1.0]`
- `overall_mean_cell_depth_savings_percent`: 29.1667
- `overall_std_cell_depth_savings_percent`: 7.56913
- `overall_mean_cell_nmse_gap_db`: 0.419203
- `overall_max_cell_nmse_gap_db`: 0.683446
- `min_snr_mean_depth_savings_percent`: 21.875
- `max_snr_nmse_gap_db`: 0.683446
- `elapsed_seconds`: 148.924

## Notes

- SNR-axis strengthening for the narrowed A4 plateau gate at L=32.
- This remains local synthetic evidence and should not be promoted to a global IA-AUD claim.
- Depth is used as the FLOPs proxy because each refinement layer performs the same local-search kernel.

## Artifacts

- `05_results\stage3_a4_snr_plateau_gate_seed_sweep\stage3_a4_snr_plateau_gate_seed_sweep_cells.csv`
- `05_results\stage3_a4_snr_plateau_gate_seed_sweep\stage3_a4_snr_plateau_gate_seed_sweep_samples.csv`
- `05_results\stage3_a4_snr_plateau_gate_seed_sweep\stage3_a4_snr_plateau_gate_seed_sweep_snr_summary.csv`
- `05_results\stage3_a4_snr_plateau_gate_seed_sweep\run_manifest.json`
