# Sionna CDL Trained-Refinement Physical Evaluation

## Outcome Summary

The fixed source-trained bounded-refinement parameter improves channel NMSE and one physical metric, but the other physical metric does not improve; retain this as mixed dev evidence.

This run transfers the fixed alpha learned by the accepted Stage-2 five-seed bounded-refinement layer. It evaluates the layer's continuous delay/angle bins with CIR-grounded Hungarian matching; it does not claim a deeper multi-parameter T-OMP-Net architecture.

## evaluation_summary

- `research_question`: Does the Stage-2 source-trained bounded-refinement layer improve CDL channel NMSE and CIR-grounded delay/projected-angle RMSE over grid FFT top-k?
- `claim_update`: trained-refinement-physical-transfer-mixed
- `baseline_relation`: Grid and trained refinement use identical noisy CDL samples, support budgets, truth paths, and Hungarian physical-metric contract.
- `failure_mode`: A mixed or negative physical result means synthetic-source scalar transfer is insufficient; no test-truth alpha tuning is permitted.
- `mechanism_note`: The fixed source-trained bounded-refinement parameter improves channel NMSE and one physical metric, but the other physical metric does not improve; retain this as mixed dev evidence.
- `next_action`: If supported, scale the unchanged contract; if mixed/refuted, preserve the negative result and implement a genuinely richer trained refinement model before another external run.
- `evidence_level`: E1 auxiliary/dev trained-refinement physical transfer evidence.

## Key Metrics

- `profiles`: `A,C,D`
- `snrs_db`: `0.0,10.0,20.0,30.0`
- `l_values`: `4,8,16`
- `seed_count`: 2
- `samples_per_profile_seed`: 4
- `row_count`: 72
- `sample_row_count`: 288
- `source_alpha`: 0.64192
- `source_alpha_source`: `05_results\stage2_torch_locked_scale_g2_seed_sweep\stage2_torch_locked_scale_g2_seed_sweep_seeds.csv`
- `mean_grid_channel_nmse_db`: -12.8145
- `mean_trained_refinement_channel_nmse_db`: -16.3588
- `mean_trained_refinement_gain_vs_grid_db`: 3.54428
- `min_cell_trained_refinement_gain_vs_grid_db`: -2.14276
- `mean_grid_physical_delay_rmse_ns`: 461.138
- `mean_trained_refinement_physical_delay_rmse_ns`: 455.872
- `mean_physical_delay_rmse_reduction_vs_grid_ns`: 5.26524
- `mean_grid_projected_broadside_angle_rmse_deg`: 30.0077
- `mean_trained_refinement_projected_broadside_angle_rmse_deg`: 35.6084
- `mean_projected_angle_rmse_reduction_vs_grid_deg`: -5.60071
- `min_cell_physical_delay_rmse_reduction_vs_grid_ns`: -22.1246
- `min_cell_projected_angle_rmse_reduction_vs_grid_deg`: -27.6393
- `delay_resolution_ns`: 130.208
- `elapsed_seconds`: 1.98439
- `claim_update`: `trained-refinement-physical-transfer-mixed`
