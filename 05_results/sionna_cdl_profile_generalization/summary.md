# Sionna CDL Profile Generalization

- Claim update: `executable-but-weak-support`
- Profiles: `A,C,D`
- SNRs: `0.0,10.0,20.0,30.0` dB
- L values: `4,8,16`
- Aggregated rows: `72`
- Sample rows: `288`
- Minimum mean support recall: `0.171875`
- Mean channel NMSE across cells: `-12.8145` dB
- Mean dominant energy recall: `0.930394`
- Elapsed seconds: `0.16`

## Interpretation

All CDL-A/C/D profile cells ran with finite metrics, but the dominant-bin recall is weak in at least one cell; E1 needs stronger estimator tuning before paper use.

This is a dev-chain validation, not final paper-facing E1 evidence. It intentionally records bin-proxy delay/angle metrics so the next run can replace them with physical path RMSE without changing the output contract shape.

## Artifacts

- `05_results\sionna_cdl_profile_generalization\sionna_cdl_profile_generalization.csv`
- `05_results\sionna_cdl_profile_generalization\sionna_cdl_profile_generalization_samples.csv`
- `05_results\sionna_cdl_profile_generalization\run_manifest.json`
- `05_results\sionna_cdl_profile_generalization\evaluation_summary.md`
