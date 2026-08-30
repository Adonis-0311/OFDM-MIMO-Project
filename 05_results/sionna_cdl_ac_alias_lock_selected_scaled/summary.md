# Sionna CDL Trained-Refinement Physical Evaluation

- Claim update: `trained-refinement-physical-transfer-supported-scaled`
- Source alpha: `0.64192` from `05_results\stage2_torch_locked_scale_g2_seed_sweep\stage2_torch_locked_scale_g2_seed_sweep_seeds.csv`
- Mean applied delay/angle alpha: `1.11779` / `0.233344` (`source-trained-feature-controller`)
- Mean channel NMSE gain vs grid: `6.22855` dB
- Mean physical delay RMSE: grid `323.526` ns -> trained `313.402` ns
- Mean projected-angle RMSE: grid `28.2923` deg -> trained `27.7647` deg
- Elapsed seconds: `36.71`

## Interpretation

The frozen trained bounded-refinement estimator improves channel NMSE and both CIR-grounded physical RMSE metrics on the tested CDL cells.

## Evidence boundary

This records the physical-metric result for the frozen trained bounded-refinement estimator. It is not evidence for a deeper multi-parameter T-OMP-Net unless that architecture is implemented and evaluated separately.

## Artifacts

- `05_results\sionna_cdl_ac_alias_lock_selected_scaled\sionna_cdl_trained_refinement.csv`
- `05_results\sionna_cdl_ac_alias_lock_selected_scaled\sionna_cdl_trained_refinement_samples.csv`
- `05_results\sionna_cdl_ac_alias_lock_selected_scaled\run_manifest.json`
- `05_results\sionna_cdl_ac_alias_lock_selected_scaled\evaluation_summary.md`
