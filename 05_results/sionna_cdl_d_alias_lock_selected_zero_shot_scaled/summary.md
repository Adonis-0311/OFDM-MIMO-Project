# Sionna CDL Trained-Refinement Physical Evaluation

- Claim update: `trained-refinement-physical-transfer-inconclusive`
- Source alpha: `0.64192` from `05_results\stage2_torch_locked_scale_g2_seed_sweep\stage2_torch_locked_scale_g2_seed_sweep_seeds.csv`
- Mean applied delay/angle alpha: `1.09755` / `0.269528` (`source-trained-feature-controller`)
- Mean channel NMSE gain vs grid: `-1.48616` dB
- Mean physical delay RMSE: grid `654.443` ns -> trained `669.025` ns
- Mean projected-angle RMSE: grid `33.5824` deg -> trained `32.6173` deg
- Elapsed seconds: `19.09`

## Interpretation

The channel and physical metrics move in conflicting directions, so the transfer claim remains inconclusive.

## Evidence boundary

This records the physical-metric result for the frozen trained bounded-refinement estimator. It is not evidence for a deeper multi-parameter T-OMP-Net unless that architecture is implemented and evaluated separately.

## Artifacts

- `05_results\sionna_cdl_d_alias_lock_selected_zero_shot_scaled\sionna_cdl_trained_refinement.csv`
- `05_results\sionna_cdl_d_alias_lock_selected_zero_shot_scaled\sionna_cdl_trained_refinement_samples.csv`
- `05_results\sionna_cdl_d_alias_lock_selected_zero_shot_scaled\run_manifest.json`
- `05_results\sionna_cdl_d_alias_lock_selected_zero_shot_scaled\evaluation_summary.md`
