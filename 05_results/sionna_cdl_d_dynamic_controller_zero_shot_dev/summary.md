# Sionna CDL Trained-Refinement Physical Evaluation

- Claim update: `trained-refinement-physical-transfer-refuted`
- Source alpha: `0.64192` from `05_results\stage2_torch_locked_scale_g2_seed_sweep\stage2_torch_locked_scale_g2_seed_sweep_seeds.csv`
- Mean applied delay/angle alpha: `0.988347` / `0.346005` (`source-trained-feature-controller`)
- Mean channel NMSE gain vs grid: `-0.942363` dB
- Mean physical delay RMSE: grid `675.59` ns -> trained `683.542` ns
- Mean projected-angle RMSE: grid `33.7992` deg -> trained `40.7266` deg
- Elapsed seconds: `0.93`

## Interpretation

The fixed source-trained bounded-refinement parameter fails to improve channel NMSE or either physical metric on the tested CDL cells.

## Evidence boundary

This closes the physical-metric evaluator for the accepted learned scalar bounded-refinement layer. It is not evidence for a deeper multi-parameter T-OMP-Net unless that architecture is implemented and evaluated separately.

## Artifacts

- `05_results\sionna_cdl_d_dynamic_controller_zero_shot_dev\sionna_cdl_trained_refinement.csv`
- `05_results\sionna_cdl_d_dynamic_controller_zero_shot_dev\sionna_cdl_trained_refinement_samples.csv`
- `05_results\sionna_cdl_d_dynamic_controller_zero_shot_dev\run_manifest.json`
- `05_results\sionna_cdl_d_dynamic_controller_zero_shot_dev\evaluation_summary.md`
