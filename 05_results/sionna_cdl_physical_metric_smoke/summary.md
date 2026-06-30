# Sionna CDL Profile Generalization

- Claim update: `dev-chain-supported`
- Profiles: `A,C,D`
- SNRs: `0.0,20.0` dB
- L values: `4,16`
- Aggregated rows: `12`
- Sample rows: `24`
- Minimum mean support recall: `0.53125`
- Mean channel NMSE across cells: `-11.2737` dB
- Mean dominant energy recall: `0.889462`
- Minimum mean top-k energy efficiency: `0.988895`
- Minimum mean delay support recall: `0.625`
- Minimum mean angle support recall: `0.59375`
- Mean effective 95% / 99% support size: `20.3333` / `90.6667`
- Mean physical delay RMSE: `153.15` ns
- Mean projected broadside-angle RMSE: `27.6141` deg
- SNR>=20 dB physical delay / projected-angle RMSE: `134.465` ns / `28.5524` deg
- Clean-grid physical delay / projected-angle RMSE floor: `125.378` ns / `27.9149` deg
- Noisy physical RMSE gap vs clean-grid floor: `27.772` ns / `-0.300744` deg
- Elapsed seconds: `0.08`

## Interpretation

All CDL-A/C/D profile cells ran with finite channel NMSE and at least half of dominant delay-angle FFT bins recovered in every aggregated cell.

This is a CIR-grounded physical-metric grid baseline, not final paper-facing trained-estimator E1 evidence. Delay is measured against Sionna tau; angle is the effective projected broadside quantity identifiable by the 1-D half-wavelength ULA.

## Artifacts

- `05_results\sionna_cdl_physical_metric_smoke\sionna_cdl_profile_generalization.csv`
- `05_results\sionna_cdl_physical_metric_smoke\sionna_cdl_profile_generalization_samples.csv`
- `05_results\sionna_cdl_physical_metric_smoke\run_manifest.json`
- `05_results\sionna_cdl_physical_metric_smoke\evaluation_summary.md`
