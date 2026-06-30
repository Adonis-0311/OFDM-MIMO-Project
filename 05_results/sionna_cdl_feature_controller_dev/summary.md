# Sionna CDL Trained-Refinement Physical Evaluation

- Claim update: `trained-refinement-physical-transfer-mixed`
- Source alpha: `0.64192` from `05_results\stage2_torch_locked_scale_g2_seed_sweep\stage2_torch_locked_scale_g2_seed_sweep_seeds.csv`
- Mean applied delay/angle alpha: `0.685768` / `0.739323` (`source-trained-feature-controller`)
- Mean channel NMSE gain vs grid: `3.72503` dB
- Mean physical delay RMSE: grid `461.138` ns -> trained `455.283` ns
- Mean projected-angle RMSE: grid `30.0077` deg -> trained `35.7289` deg
- Elapsed seconds: `2.25`

## Interpretation

The fixed source-trained bounded-refinement parameter improves channel NMSE and one physical metric, but the other physical metric does not improve; retain this as mixed dev evidence.

## Evidence boundary

This closes the physical-metric evaluator for the accepted learned scalar bounded-refinement layer. It is not evidence for a deeper multi-parameter T-OMP-Net unless that architecture is implemented and evaluated separately.

## Artifacts

- `05_results\sionna_cdl_feature_controller_dev\sionna_cdl_trained_refinement.csv`
- `05_results\sionna_cdl_feature_controller_dev\sionna_cdl_trained_refinement_samples.csv`
- `05_results\sionna_cdl_feature_controller_dev\run_manifest.json`
- `05_results\sionna_cdl_feature_controller_dev\evaluation_summary.md`
