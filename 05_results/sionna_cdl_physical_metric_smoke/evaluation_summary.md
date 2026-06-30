# Sionna CDL Profile Generalization Evaluation Summary

## Outcome Summary

This E1 run validates the open-source Sionna CDL-A/C/D channel path and a delay-angle FFT sparse-recovery schema with 1 seeds and 2 samples per profile and seed.

The run records CIR-grounded delay RMSE in nanoseconds and effective projected ULA broadside-angle RMSE in degrees. It remains a grid FFT top-k baseline, not the full trained estimator result.

## evaluation_summary

- `research_question`: Can the Sionna CDL-A/C/D channel generator feed a reproducible Tensor-OMP-style delay-angle sparse recovery evaluation across SNR and sparsity budgets?
- `claim_update`: dev-chain-supported
- `baseline_relation`: The comparator is a grid FFT top-k Tensor-OMP proxy applied to the same noisy CDL frequency-response tensor as the clean-channel target.
- `failure_mode`: Exact-bin support is weak in over-budgeted low-SNR CDL-D cells even when oracle top-k energy efficiency remains high; the physical metrics are cluster-effective ULA quantities rather than separate AoD/ZoD.
- `mechanism_note`: All CDL-A/C/D profile cells ran with finite channel NMSE and at least half of dominant delay-angle FFT bins recovered in every aggregated cell.
- `next_action`: Attach the full trained estimator and compare its CIR-grounded delay/projected-angle RMSE against this grid baseline before promoting E1.
- `paper_role`: E1 supporting external-channel robustness and limitation evidence.
- `section_id`: 06_experiments; 07_limitations.
- `item_id`: E8.
- `claim_links`: C4.
- `main_or_appendix`: Appendix/supporting until the trained estimator is evaluated with the same physical metrics.
- `evidence_level`: E1 auxiliary/dev chain validation.

## Key Metrics

- `claim_update`: `dev-chain-supported`
- `physical_metric_status`: `cir-grounded-grid-baseline-and-clean-floor-recorded`
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
- `min_mean_delay_support_recall`: 0.625
- `min_mean_angle_support_recall`: 0.59375
- `mean_effective_support_95_all`: 20.3333
- `mean_effective_support_99_all`: 90.6667
- `mean_physical_delay_rmse_ns_all`: 153.15
- `mean_projected_broadside_angle_rmse_deg_all`: 27.6141
- `mean_physical_delay_rmse_ns_snr_ge_20`: 134.465
- `mean_projected_broadside_angle_rmse_deg_snr_ge_20`: 28.5524
- `mean_clean_grid_physical_delay_rmse_ns_all`: 125.378
- `mean_clean_grid_projected_broadside_angle_rmse_deg_all`: 27.9149
- `mean_physical_delay_rmse_gap_vs_clean_grid_ns_all`: 27.772
- `mean_projected_angle_rmse_gap_vs_clean_grid_deg_all`: -0.300744
- `max_mean_physical_delay_rmse_ns`: 431.975
- `max_mean_projected_broadside_angle_rmse_deg`: 51.5742
- `delay_resolution_ns`: 65.1042
- `projected_angle_definition`: `effective ULA broadside angle from oversampled clean per-cluster CIR; endfire alias handled in spatial-frequency matching`
- `elapsed_seconds`: 0.0817163
