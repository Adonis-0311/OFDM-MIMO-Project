# Sionna CDL Profile Generalization Evaluation Summary

## Outcome Summary

This E1 run validates the open-source Sionna CDL-A/C/D channel path and a delay-angle FFT sparse-recovery schema with 5 seeds and 50 samples per profile and seed.

The run records CIR-grounded delay RMSE in nanoseconds and effective projected ULA broadside-angle RMSE in degrees. It remains a grid FFT top-k baseline, not the full trained estimator result.

## evaluation_summary

- `research_question`: Can the Sionna CDL-A/C/D channel generator feed a reproducible Tensor-OMP-style delay-angle sparse recovery evaluation across SNR and sparsity budgets?
- `claim_update`: energy-supported-exact-bin-weak
- `baseline_relation`: The comparator is a grid FFT top-k Tensor-OMP proxy applied to the same noisy CDL frequency-response tensor as the clean-channel target.
- `failure_mode`: Exact-bin support is weak in over-budgeted low-SNR CDL-D cells even when oracle top-k energy efficiency remains high; the physical metrics are cluster-effective ULA quantities rather than separate AoD/ZoD.
- `mechanism_note`: All cells recover at least 90% of the clean oracle top-k energy, but exact bin overlap remains weak where the requested support budget exceeds the resolvable CDL sparsity; retain exact recall as a limitation rather than promoting E1 to final physical-path evidence.
- `next_action`: Attach the full trained estimator and compare its CIR-grounded delay/projected-angle RMSE against this grid baseline before promoting E1.
- `paper_role`: E1 supporting external-channel robustness and limitation evidence.
- `section_id`: 06_experiments; 07_limitations.
- `item_id`: E8.
- `claim_links`: C4.
- `main_or_appendix`: Appendix/supporting until the trained estimator is evaluated with the same physical metrics.
- `evidence_level`: E1 scaled supporting evidence.

## Key Metrics

- `claim_update`: `energy-supported-exact-bin-weak`
- `physical_metric_status`: `cir-grounded-grid-baseline-and-clean-floor-recorded`
- `profiles`: `A,C,D`
- `snrs_db`: `0.0,10.0,20.0,30.0`
- `l_values`: `4,8,16`
- `seed_count`: 5
- `samples_per_profile_seed`: 50
- `row_count`: 180
- `sample_row_count`: 9000
- `min_mean_support_recall`: 0.41875
- `mean_channel_nmse_db_all`: -11.4399
- `best_mean_channel_nmse_db`: -22.0728
- `worst_mean_channel_nmse_db`: -5.273
- `mean_dominant_energy_recall_all`: 0.880173
- `min_mean_topk_energy_efficiency`: 0.988554
- `mean_topk_energy_efficiency_all`: 0.998786
- `min_mean_delay_support_recall`: 0.45125
- `min_mean_angle_support_recall`: 0.6225
- `mean_effective_support_95_all`: 20.104
- `mean_effective_support_99_all`: 86.8827
- `mean_physical_delay_rmse_ns_all`: 180.229
- `mean_projected_broadside_angle_rmse_deg_all`: 28.6253
- `mean_physical_delay_rmse_ns_snr_ge_20`: 141.32
- `mean_projected_broadside_angle_rmse_deg_snr_ge_20`: 28.4935
- `mean_clean_grid_physical_delay_rmse_ns_all`: 141.323
- `mean_clean_grid_projected_broadside_angle_rmse_deg_all`: 28.4459
- `mean_physical_delay_rmse_gap_vs_clean_grid_ns_all`: 38.9053
- `mean_projected_angle_rmse_gap_vs_clean_grid_deg_all`: 0.179391
- `max_mean_physical_delay_rmse_ns`: 1017.43
- `max_mean_projected_broadside_angle_rmse_deg`: 55.7
- `delay_resolution_ns`: 65.1042
- `projected_angle_definition`: `effective ULA broadside angle from oversampled clean per-cluster CIR; endfire alias handled in spatial-frequency matching`
- `elapsed_seconds`: 11.1174
