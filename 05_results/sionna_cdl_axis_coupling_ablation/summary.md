# Sionna CDL Trained-Refinement Physical Evaluation

- Claim update: `diagnostic-trained-refinement-physical-transfer-supported-dev`
- Source alpha: `0.64192` from `05_results\stage2_torch_locked_scale_g2_seed_sweep\stage2_torch_locked_scale_g2_seed_sweep_seeds.csv`
- Applied delay/angle alpha: `0.64192` / `0` (`axis-ablation-not-paper-estimator`)
- Mean channel NMSE gain vs grid: `3.18712` dB
- Mean physical delay RMSE: grid `461.138` ns -> trained `456.308` ns
- Mean projected-angle RMSE: grid `30.0077` deg -> trained `29.9478` deg
- Elapsed seconds: `2.15`

## Interpretation

Axis-coupling diagnostic only: The fixed source-trained bounded-refinement parameter improves channel NMSE and both CIR-grounded physical RMSE metrics on the tested CDL cells. The override is not a trained paper estimator and is used only to route the next model design.

## Evidence boundary

This is a diagnostic axis-coupling ablation and is not a trained paper estimator. It is not evidence for a deeper multi-parameter T-OMP-Net unless that architecture is implemented and evaluated separately.

## Artifacts

- `05_results\sionna_cdl_axis_coupling_ablation\sionna_cdl_trained_refinement.csv`
- `05_results\sionna_cdl_axis_coupling_ablation\sionna_cdl_trained_refinement_samples.csv`
- `05_results\sionna_cdl_axis_coupling_ablation\run_manifest.json`
- `05_results\sionna_cdl_axis_coupling_ablation\evaluation_summary.md`
