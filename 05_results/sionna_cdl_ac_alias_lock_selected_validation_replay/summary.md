# Sionna CDL Trained-Refinement Physical Evaluation

- Claim update: `trained-refinement-physical-transfer-supported-dev`
- Source alpha: `0.64192` from `05_results\stage2_torch_locked_scale_g2_seed_sweep\stage2_torch_locked_scale_g2_seed_sweep_seeds.csv`
- Mean applied delay/angle alpha: `1.11929` / `0.19599` (`source-trained-feature-controller`)
- Mean channel NMSE gain vs grid: `6.58423` dB
- Mean physical delay RMSE: grid `328.379` ns -> trained `321.597` ns
- Mean projected-angle RMSE: grid `27.3709` deg -> trained `27.2811` deg
- Elapsed seconds: `2.75`

## Interpretation

The fixed source-trained bounded-refinement parameter improves channel NMSE and both CIR-grounded physical RMSE metrics on the tested CDL cells.

## Evidence boundary

This closes the physical-metric evaluator for the accepted learned scalar bounded-refinement layer. It is not evidence for a deeper multi-parameter T-OMP-Net unless that architecture is implemented and evaluated separately.

## Artifacts

- `05_results\sionna_cdl_ac_alias_lock_selected_validation_replay\sionna_cdl_trained_refinement.csv`
- `05_results\sionna_cdl_ac_alias_lock_selected_validation_replay\sionna_cdl_trained_refinement_samples.csv`
- `05_results\sionna_cdl_ac_alias_lock_selected_validation_replay\run_manifest.json`
- `05_results\sionna_cdl_ac_alias_lock_selected_validation_replay\evaluation_summary.md`
