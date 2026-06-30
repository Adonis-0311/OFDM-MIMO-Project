# Stage 3 A4 High-L Plateau Gate Seed Sweep

- Config hash: `stage3-a4-high-l-plateau-gate-seed-sweep-20260625`

## Metrics

- `tensor_shape`: `128x16x32`
- `snr_db`: 20
- `seeds`: `[20260624, 20260625, 20260626]`
- `n_targets`: `32`
- `n_train`: `4`
- `n_test`: `4`
- `fixed_depth`: `8`
- `min_depth`: `3`
- `nmse_tolerance_db`: 0.5
- `threshold_candidates_db`: `[0.05, 0.1, 0.2, 0.35, 0.5, 0.75, 1.0]`
- `mean_seed_depth_savings_percent`: 26.0417
- `std_seed_depth_savings_percent`: 3.60844
- `min_seed_depth_savings_percent`: 21.875
- `mean_seed_nmse_gap_db`: 0.333891
- `max_seed_nmse_gap_db`: 0.357777
- `elapsed_seconds`: 142.701

## Notes

- Multi-seed strengthening for the narrowed high-L A4 plateau gate.
- This remains L=32-only synthetic evidence and should not be promoted to a global IA-AUD claim.
- Depth is used as the FLOPs proxy because each refinement layer performs the same local-search kernel.

## Artifacts

- `05_results\stage3_a4_high_l_plateau_gate_seed_sweep\stage3_a4_high_l_plateau_gate_seed_sweep_seeds.csv`
- `05_results\stage3_a4_high_l_plateau_gate_seed_sweep\stage3_a4_high_l_plateau_gate_seed_sweep_samples.csv`
- `05_results\stage3_a4_high_l_plateau_gate_seed_sweep\run_manifest.json`
