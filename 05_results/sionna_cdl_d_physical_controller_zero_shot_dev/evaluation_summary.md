# Sionna CDL Trained-Refinement Physical Evaluation

## Outcome Summary

The fixed source-trained bounded-refinement parameter fails to improve channel NMSE or either physical metric on the tested CDL cells.

This run transfers a frozen source-trained bounded-refinement estimator. It evaluates continuous delay/angle bins with CIR-grounded Hungarian matching; it does not claim a deeper multi-parameter T-OMP-Net architecture.

## evaluation_summary

- `research_question`: Does the Stage-2 source-trained bounded-refinement layer improve CDL channel NMSE and CIR-grounded delay/projected-angle RMSE over grid FFT top-k?
- `claim_update`: trained-refinement-physical-transfer-refuted
- `baseline_relation`: Grid and trained refinement use identical noisy CDL samples, support budgets, truth paths, and Hungarian physical-metric contract.
- `failure_mode`: A mixed or negative physical result means synthetic-source scalar transfer is insufficient; no test-truth alpha tuning is permitted.
- `mechanism_note`: The fixed source-trained bounded-refinement parameter fails to improve channel NMSE or either physical metric on the tested CDL cells.
- `next_action`: If supported, scale the unchanged contract; if mixed/refuted, preserve the negative result and implement a genuinely richer trained refinement model before another external run.
- `evidence_level`: E1 auxiliary/dev trained-refinement physical transfer evidence.

## Key Metrics

- `profiles`: `D`
- `snrs_db`: `0.0,10.0,20.0,30.0`
- `l_values`: `4,8,16`
- `seed_count`: 2
- `samples_per_profile_seed`: 4
- `row_count`: 24
- `sample_row_count`: 96
- `source_alpha`: 0.64192
- `source_alpha_source`: `05_results\stage2_torch_locked_scale_g2_seed_sweep\stage2_torch_locked_scale_g2_seed_sweep_seeds.csv`
- `delay_alpha`: 1.08544
- `angle_alpha`: 0.654558
- `estimator_mode`: `source-trained-feature-controller`
- `controller_checkpoint`: `05_results\cdl_ac_physical_angle_3seed\controller_checkpoint.pt`
- `controller_ensemble_size`: 3
- `mean_grid_channel_nmse_db`: -18.2363
- `mean_trained_refinement_channel_nmse_db`: -17.1448
- `mean_trained_refinement_gain_vs_grid_db`: -1.09145
- `min_cell_trained_refinement_gain_vs_grid_db`: -2.96276
- `mean_grid_physical_delay_rmse_ns`: 675.59
- `mean_trained_refinement_physical_delay_rmse_ns`: 685.585
- `mean_physical_delay_rmse_reduction_vs_grid_ns`: -9.99528
- `mean_grid_projected_broadside_angle_rmse_deg`: 33.7992
- `mean_trained_refinement_projected_broadside_angle_rmse_deg`: 39.0288
- `mean_projected_angle_rmse_reduction_vs_grid_deg`: -5.22961
- `min_cell_physical_delay_rmse_reduction_vs_grid_ns`: -35.7997
- `min_cell_projected_angle_rmse_reduction_vs_grid_deg`: -29.9173
- `delay_resolution_ns`: 130.208
- `elapsed_seconds`: 0.960163
- `claim_update`: `trained-refinement-physical-transfer-refuted`
