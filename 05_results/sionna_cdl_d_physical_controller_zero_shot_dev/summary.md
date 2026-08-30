# Sionna CDL Trained-Refinement Physical Evaluation

- Claim update: `trained-refinement-physical-transfer-refuted`
- Source alpha: `0.64192` from `05_results\stage2_torch_locked_scale_g2_seed_sweep\stage2_torch_locked_scale_g2_seed_sweep_seeds.csv`
- Mean applied delay/angle alpha: `1.08544` / `0.654558` (`source-trained-feature-controller`)
- Mean channel NMSE gain vs grid: `-1.09145` dB
- Mean physical delay RMSE: grid `675.59` ns -> trained `685.585` ns
- Mean projected-angle RMSE: grid `33.7992` deg -> trained `39.0288` deg
- Elapsed seconds: `0.96`

## Interpretation

The fixed source-trained bounded-refinement parameter fails to improve channel NMSE or either physical metric on the tested CDL cells.

## Evidence boundary

This closes the physical-metric evaluator for the accepted learned scalar bounded-refinement layer. It is not evidence for a deeper multi-parameter T-OMP-Net unless that architecture is implemented and evaluated separately.

## Artifacts

- `05_results\sionna_cdl_d_physical_controller_zero_shot_dev\sionna_cdl_trained_refinement.csv`
- `05_results\sionna_cdl_d_physical_controller_zero_shot_dev\sionna_cdl_trained_refinement_samples.csv`
- `05_results\sionna_cdl_d_physical_controller_zero_shot_dev\run_manifest.json`
- `05_results\sionna_cdl_d_physical_controller_zero_shot_dev\evaluation_summary.md`
