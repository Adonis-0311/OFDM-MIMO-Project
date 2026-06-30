# Sionna CDL Profile Generalization Evaluation Summary

## Outcome Summary

This E1 dev-run validates the open-source Sionna CDL-A/C/D channel path and a delay-angle FFT sparse-recovery evaluation schema on small batches.

It is not yet the full Sensors E1 evidence package: angle/delay metrics are grid-bin proxy metrics from dominant FFT bins, not final physical parameter RMSE.

## evaluation_summary

- `research_question`: Can the Sionna CDL-A/C/D channel generator feed a reproducible Tensor-OMP-style delay-angle sparse recovery evaluation across SNR and sparsity budgets?
- `claim_update`: dev-chain-supported
- `baseline_relation`: The comparator is a grid FFT top-k Tensor-OMP proxy applied to the same noisy CDL frequency-response tensor as the clean-channel target.
- `failure_mode`: None if status is dev-chain-supported/executable; limitation is metric fidelity and small dev sample size.
- `mechanism_note`: All CDL-A/C/D profile cells ran with finite channel NMSE and at least half of dominant delay-angle FFT bins recovered in every aggregated cell.
- `next_action`: Promote this schema to the Sensors E1 run by increasing seeds/samples, adding CDL-C/D tables, and replacing bin-proxy angle/delay metrics with physical-path RMSE where possible.
- `evidence_level`: E1 auxiliary/dev chain validation.

## Key Metrics

- `claim_update`: `dev-chain-supported`
- `profiles`: `A,C,D`
- `snrs_db`: `0.0,20.0`
- `l_values`: `4,16`
- `seed_count`: 1
- `samples_per_profile_seed`: 2
- `row_count`: 12
- `sample_row_count`: 24
- `min_mean_support_recall`: 0.53125
- `mean_channel_nmse_db_all`: -11.2737
- `best_mean_channel_nmse_db`: -21.007
- `worst_mean_channel_nmse_db`: -5.39062
- `mean_dominant_energy_recall_all`: 0.889462
- `min_mean_topk_energy_efficiency`: 0.988895
- `mean_topk_energy_efficiency_all`: 0.997556
- `min_mean_delay_support_recall`: 0.34375
- `min_mean_angle_support_recall`: 0.28125
- `mean_effective_support_95_all`: 20.3333
- `mean_effective_support_99_all`: 90.6667
- `elapsed_seconds`: 0.0528873
