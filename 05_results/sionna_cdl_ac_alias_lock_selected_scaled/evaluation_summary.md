# Sionna CDL Trained-Refinement Physical Evaluation

## Outcome Summary

The frozen trained bounded-refinement estimator improves channel NMSE and both CIR-grounded physical RMSE metrics on the tested CDL cells.

This run transfers a frozen source-trained bounded-refinement estimator. It evaluates continuous delay/angle bins with CIR-grounded Hungarian matching; it does not claim a deeper multi-parameter T-OMP-Net architecture.

## evaluation_summary

- `research_question`: Does the Stage-2 source-trained bounded-refinement layer improve CDL channel NMSE and CIR-grounded delay/projected-angle RMSE over grid FFT top-k?
- `claim_update`: trained-refinement-physical-transfer-supported-scaled
- `baseline_relation`: Grid and trained refinement use identical noisy CDL samples, support budgets, truth paths, and Hungarian physical-metric contract.
- `failure_mode`: A mixed or negative physical result means the frozen estimator is insufficient for that profile/setting; no test-truth tuning is permitted.
- `mechanism_note`: The frozen trained bounded-refinement estimator improves channel NMSE and both CIR-grounded physical RMSE metrics on the tested CDL cells.
- `next_action`: If supported, scale the unchanged contract; if mixed/refuted, preserve the negative result and implement a genuinely richer trained refinement model before another external run.
- `evidence_level`: E1 auxiliary/dev trained-refinement physical transfer evidence.

## Key Metrics

- `profiles`: `A,C`
- `snrs_db`: `0.0,10.0,20.0,30.0`
- `l_values`: `4,8,16`
- `seed_count`: 5
- `samples_per_profile_seed`: 50
- `row_count`: 120
- `sample_row_count`: 6000
- `source_alpha`: 0.64192
- `source_alpha_source`: `05_results\stage2_torch_locked_scale_g2_seed_sweep\stage2_torch_locked_scale_g2_seed_sweep_seeds.csv`
- `delay_alpha`: 1.11779
- `angle_alpha`: 0.233344
- `estimator_mode`: `source-trained-feature-controller`
- `controller_checkpoint`: `05_results\cdl_ac_alias_lock_3seed\selected_controller_checkpoint.pt`
- `controller_ensemble_size`: 1
- `mean_grid_channel_nmse_db`: -9.88603
- `mean_trained_refinement_channel_nmse_db`: -16.1146
- `mean_trained_refinement_gain_vs_grid_db`: 6.22855
- `min_cell_trained_refinement_gain_vs_grid_db`: 0.754789
- `mean_grid_physical_delay_rmse_ns`: 323.526
- `mean_trained_refinement_physical_delay_rmse_ns`: 313.402
- `mean_physical_delay_rmse_reduction_vs_grid_ns`: 10.1241
- `mean_grid_projected_broadside_angle_rmse_deg`: 28.2923
- `mean_trained_refinement_projected_broadside_angle_rmse_deg`: 27.7647
- `mean_projected_angle_rmse_reduction_vs_grid_deg`: 0.527685
- `min_cell_physical_delay_rmse_reduction_vs_grid_ns`: -15.5423
- `min_cell_projected_angle_rmse_reduction_vs_grid_deg`: -1.1624
- `delay_resolution_ns`: 130.208
- `elapsed_seconds`: 36.7145
- `claim_update`: `trained-refinement-physical-transfer-supported-scaled`
