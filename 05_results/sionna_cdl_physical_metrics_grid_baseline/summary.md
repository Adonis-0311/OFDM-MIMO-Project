# Sionna CDL Profile Generalization

- Claim update: `energy-supported-exact-bin-weak`
- Profiles: `A,C,D`
- SNRs: `0.0,10.0,20.0,30.0` dB
- L values: `4,8,16`
- Aggregated rows: `180`
- Sample rows: `9000`
- Minimum mean support recall: `0.41875`
- Mean channel NMSE across cells: `-11.4399` dB
- Mean dominant energy recall: `0.880173`
- Minimum mean top-k energy efficiency: `0.988554`
- Minimum mean delay support recall: `0.45125`
- Minimum mean angle support recall: `0.6225`
- Mean effective 95% / 99% support size: `20.104` / `86.8827`
- Mean physical delay RMSE: `180.229` ns
- Mean projected broadside-angle RMSE: `28.6253` deg
- SNR>=20 dB physical delay / projected-angle RMSE: `141.32` ns / `28.4935` deg
- Clean-grid physical delay / projected-angle RMSE floor: `141.323` ns / `28.4459` deg
- Noisy physical RMSE gap vs clean-grid floor: `38.9053` ns / `0.179391` deg
- Elapsed seconds: `11.12`

## Interpretation

All cells recover at least 90% of the clean oracle top-k energy, but exact bin overlap remains weak where the requested support budget exceeds the resolvable CDL sparsity; retain exact recall as a limitation rather than promoting E1 to final physical-path evidence.

This is a CIR-grounded physical-metric grid baseline, not final paper-facing trained-estimator E1 evidence. Delay is measured against Sionna tau; angle is the effective projected broadside quantity identifiable by the 1-D half-wavelength ULA.

## Artifacts

- `05_results\sionna_cdl_physical_metrics_grid_baseline\sionna_cdl_profile_generalization.csv`
- `05_results\sionna_cdl_physical_metrics_grid_baseline\sionna_cdl_profile_generalization_samples.csv`
- `05_results\sionna_cdl_physical_metrics_grid_baseline\run_manifest.json`
- `05_results\sionna_cdl_physical_metrics_grid_baseline\evaluation_summary.md`
