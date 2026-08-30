# Stage 3 A4 Cross-L Plateau Gate Seed Sweep

- Config hash: `stage3-a4-cross-l-plateau-gate-seed-sweep-20260625`

## Metrics

- `tensor_shape`: `128x16x32`
- `snr_db`: 20
- `seeds`: `[20260624, 20260625]`
- `l_values`: `[16, 32, 64]`
- `n_train`: `2`
- `n_test`: `2`
- `fixed_depth`: `8`
- `min_depth`: `3`
- `nmse_tolerance_db`: 0.5
- `threshold_candidates_db`: `[0.05, 0.1, 0.2, 0.35, 0.5, 0.75, 1.0]`
- `overall_mean_cell_depth_savings_percent`: 27.0833
- `overall_std_cell_depth_savings_percent`: 6.45497
- `overall_mean_cell_nmse_gap_db`: 0.363721
- `overall_max_cell_nmse_gap_db`: 0.547996
- `high_l_min_mean_depth_savings_percent`: 25
- `high_l_max_nmse_gap_db`: 0.40084
- `elapsed_seconds`: 174.214

## Notes

- Cross-L strengthening for the narrowed A4 plateau gate over L={16,32,64}.
- L=16 is boundary evidence; the paper-facing high-L claim should rely on L>=32.
- This remains local synthetic evidence and should not be promoted to a global IA-AUD claim.

## Artifacts

- `05_results\stage3_a4_cross_l_plateau_gate_seed_sweep\stage3_a4_cross_l_plateau_gate_seed_sweep_cells.csv`
- `05_results\stage3_a4_cross_l_plateau_gate_seed_sweep\stage3_a4_cross_l_plateau_gate_seed_sweep_samples.csv`
- `05_results\stage3_a4_cross_l_plateau_gate_seed_sweep\stage3_a4_cross_l_plateau_gate_seed_sweep_l_summary.csv`
- `05_results\stage3_a4_cross_l_plateau_gate_seed_sweep\run_manifest.json`
