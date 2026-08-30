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
- Elapsed seconds: `4.86`

## Interpretation

All cells recover at least 90% of the clean oracle top-k energy, but exact bin overlap remains weak where the requested support budget exceeds the resolvable CDL sparsity; retain exact recall as a limitation rather than promoting E1 to final physical-path evidence.

This is a dev-chain validation, not final paper-facing E1 evidence. It intentionally records bin-proxy delay/angle metrics so the next run can replace them with physical path RMSE without changing the output contract shape.

## Artifacts

- `05_results\sionna_cdl_profile_generalization_scaled\sionna_cdl_profile_generalization.csv`
- `05_results\sionna_cdl_profile_generalization_scaled\sionna_cdl_profile_generalization_samples.csv`
- `05_results\sionna_cdl_profile_generalization_scaled\run_manifest.json`
- `05_results\sionna_cdl_profile_generalization_scaled\evaluation_summary.md`
