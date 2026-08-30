# Sionna CDL Profile Generalization Evaluation Summary

## Outcome Summary

This E1 dev-run validates the open-source Sionna CDL-A/C/D channel path and a delay-angle FFT sparse-recovery evaluation schema on small batches.

It is not yet the full Sensors E1 evidence package: angle/delay metrics are grid-bin proxy metrics from dominant FFT bins, not final physical parameter RMSE.

## evaluation_summary

- `research_question`: Can the Sionna CDL-A/C/D channel generator feed a reproducible Tensor-OMP-style delay-angle sparse recovery evaluation across SNR and sparsity budgets?
- `claim_update`: executable-but-weak-support
- `baseline_relation`: The comparator is a grid FFT top-k Tensor-OMP proxy applied to the same noisy CDL frequency-response tensor as the clean-channel target.
- `failure_mode`: None if status is dev-chain-supported/executable; limitation is metric fidelity and small dev sample size.
- `mechanism_note`: All CDL-A/C/D profile cells ran with finite metrics, but the dominant-bin recall is weak in at least one cell; E1 needs stronger estimator tuning before paper use.
- `next_action`: Promote this schema to the Sensors E1 run by increasing seeds/samples, adding CDL-C/D tables, and replacing bin-proxy angle/delay metrics with physical-path RMSE where possible.
- `evidence_level`: E1 auxiliary/dev chain validation.

## Key Metrics

- `claim_update`: `executable-but-weak-support`
- `profiles`: `A,C,D`
- `snrs_db`: `0.0,10.0,20.0,30.0`
- `l_values`: `4,8,16`
- `seed_count`: 2
- `samples_per_profile_seed`: 4
- `row_count`: 72
- `sample_row_count`: 288
- `min_mean_support_recall`: 0.171875
- `mean_channel_nmse_db_all`: -12.8145
- `best_mean_channel_nmse_db`: -28.6785
- `worst_mean_channel_nmse_db`: -5.79429
- `mean_dominant_energy_recall_all`: 0.930394
- `elapsed_seconds`: 0.162714
