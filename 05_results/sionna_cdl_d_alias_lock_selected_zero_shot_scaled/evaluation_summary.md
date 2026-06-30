# Sionna CDL Trained-Refinement Physical Evaluation

## Outcome Summary

The channel and physical metrics move in conflicting directions, so the transfer claim remains inconclusive.

This run transfers a frozen source-trained bounded-refinement estimator. It evaluates continuous delay/angle bins with CIR-grounded Hungarian matching; it does not claim a deeper multi-parameter T-OMP-Net architecture.

## evaluation_summary

- `research_question`: Does the Stage-2 source-trained bounded-refinement layer improve CDL channel NMSE and CIR-grounded delay/projected-angle RMSE over grid FFT top-k?
- `claim_update`: trained-refinement-physical-transfer-inconclusive
- `baseline_relation`: Grid and trained refinement use identical noisy CDL samples, support budgets, truth paths, and Hungarian physical-metric contract.
- `failure_mode`: A mixed or negative physical result means the frozen estimator is insufficient for that profile/setting; no test-truth tuning is permitted.
- `mechanism_note`: The channel and physical metrics move in conflicting directions, so the transfer claim remains inconclusive.
- `next_action`: If supported, scale the unchanged contract; if mixed/refuted, preserve the negative result and implement a genuinely richer trained refinement model before another external run.
- `evidence_level`: E1 auxiliary/dev trained-refinement physical transfer evidence.

## Key Metrics

- `profiles`: `D`
- `snrs_db`: `0.0,10.0,20.0,30.0`
- `l_values`: `4,8,16`
- `seed_count`: 5
- `samples_per_profile_seed`: 50
- `row_count`: 60
- `sample_row_count`: 3000
- `source_alpha`: 0.64192
- `source_alpha_source`: `05_results\stage2_torch_locked_scale_g2_seed_sweep\stage2_torch_locked_scale_g2_seed_sweep_seeds.csv`
- `delay_alpha`: 1.09755
- `angle_alpha`: 0.269528
- `estimator_mode`: `source-trained-feature-controller`
- `controller_checkpoint`: `05_results\cdl_ac_alias_lock_3seed\selected_controller_checkpoint.pt`
- `controller_ensemble_size`: 1
- `mean_grid_channel_nmse_db`: -18.3895
- `mean_trained_refinement_channel_nmse_db`: -16.9033
- `mean_trained_refinement_gain_vs_grid_db`: -1.48616
- `min_cell_trained_refinement_gain_vs_grid_db`: -4.3836
- `mean_grid_physical_delay_rmse_ns`: 654.443
- `mean_trained_refinement_physical_delay_rmse_ns`: 669.025
- `mean_physical_delay_rmse_reduction_vs_grid_ns`: -14.582
- `mean_grid_projected_broadside_angle_rmse_deg`: 33.5824
- `mean_trained_refinement_projected_broadside_angle_rmse_deg`: 32.6173
- `mean_projected_angle_rmse_reduction_vs_grid_deg`: 0.965149
- `min_cell_physical_delay_rmse_reduction_vs_grid_ns`: -30.2453
- `min_cell_projected_angle_rmse_reduction_vs_grid_deg`: -3.14925
- `delay_resolution_ns`: 130.208
- `elapsed_seconds`: 19.0898
- `claim_update`: `trained-refinement-physical-transfer-inconclusive`
