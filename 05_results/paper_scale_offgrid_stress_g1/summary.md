# Paper-Scale Off-Grid Stress G1

- Config hash: `offgrid-local-20260624`

## Metrics

- `tensor_shape`: `128x16x32`
- `snr_db`: 20
- `offset_radius_bins`: 0.35
- `n_trials_per_l`: `4`
- `mean_grid_nmse_db`: -5.4308
- `mean_refined_nmse_db`: -12.9676
- `mean_refinement_gain_db`: 7.53682
- `min_refinement_gain_db`: 6.99464
- `wall_seconds`: 9.59363

## Notes

- Paper-scale off-grid stress uses continuous angle-delay-Doppler bins on shape 128x16x32.
- Metric is measurement-domain NMSE against the noiseless off-grid tensor, so it is not a sparse-grid coefficient NMSE.
- Bounded local refinement is a deterministic oracle-free search around Tensor-OMP grid picks and supports the v2.3R off-grid mechanism gate.

## Artifacts

- `05_results\paper_scale_offgrid_stress_g1\paper_scale_offgrid_stress_g1.csv`
- `05_results\paper_scale_offgrid_stress_g1\run_manifest.json`
