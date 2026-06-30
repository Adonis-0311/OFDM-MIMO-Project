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
- Minimum mean delay support recall: `0.34375`
- Minimum mean angle support recall: `0.28125`
- Mean effective 95% / 99% support size: `20.3333` / `90.6667`
- Elapsed seconds: `0.05`

## Interpretation

All CDL-A/C/D profile cells ran with finite channel NMSE and at least half of dominant delay-angle FFT bins recovered in every aggregated cell.

This is a dev-chain validation, not final paper-facing E1 evidence. It intentionally records bin-proxy delay/angle metrics so the next run can replace them with physical path RMSE without changing the output contract shape.

## Artifacts

- `05_results\sionna_cdl_support_diagnostic_smoke\sionna_cdl_profile_generalization.csv`
- `05_results\sionna_cdl_support_diagnostic_smoke\sionna_cdl_profile_generalization_samples.csv`
- `05_results\sionna_cdl_support_diagnostic_smoke\run_manifest.json`
- `05_results\sionna_cdl_support_diagnostic_smoke\evaluation_summary.md`
