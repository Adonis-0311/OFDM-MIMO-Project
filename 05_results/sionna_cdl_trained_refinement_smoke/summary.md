# Sionna CDL Trained-Refinement Physical Evaluation

- Claim update: `trained-refinement-physical-transfer-supported-dev`
- Source alpha: `0.64192` from `05_results\stage2_torch_locked_scale_g2_seed_sweep\stage2_torch_locked_scale_g2_seed_sweep_seeds.csv`
- Mean channel NMSE gain vs grid: `8.75723` dB
- Mean physical delay RMSE: grid `101.29` ns -> trained `87.3105` ns
- Mean projected-angle RMSE: grid `32.5943` deg -> trained `29.1385` deg
- Elapsed seconds: `0.03`

## Interpretation

The fixed source-trained bounded-refinement parameter improves channel NMSE and both CIR-grounded physical RMSE metrics on the tested CDL cells.

## Evidence boundary

This closes the physical-metric evaluator for the accepted learned scalar bounded-refinement layer. It is not evidence for a deeper multi-parameter T-OMP-Net unless that architecture is implemented and evaluated separately.

## Artifacts

- `05_results\sionna_cdl_trained_refinement_smoke\sionna_cdl_trained_refinement.csv`
- `05_results\sionna_cdl_trained_refinement_smoke\sionna_cdl_trained_refinement_samples.csv`
- `05_results\sionna_cdl_trained_refinement_smoke\run_manifest.json`
- `05_results\sionna_cdl_trained_refinement_smoke\evaluation_summary.md`
