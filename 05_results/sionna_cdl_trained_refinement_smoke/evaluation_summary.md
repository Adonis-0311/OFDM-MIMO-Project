# Sionna CDL Trained-Refinement Physical Evaluation

## Outcome Summary

The fixed source-trained bounded-refinement parameter improves channel NMSE and both CIR-grounded physical RMSE metrics on the tested CDL cells.

This run transfers the fixed alpha learned by the accepted Stage-2 five-seed bounded-refinement layer. It evaluates the layer's continuous delay/angle bins with CIR-grounded Hungarian matching; it does not claim a deeper multi-parameter T-OMP-Net architecture.

## evaluation_summary

- `research_question`: Does the Stage-2 source-trained bounded-refinement layer improve CDL channel NMSE and CIR-grounded delay/projected-angle RMSE over grid FFT top-k?
- `claim_update`: trained-refinement-physical-transfer-supported-dev
- `baseline_relation`: Grid and trained refinement use identical noisy CDL samples, support budgets, truth paths, and Hungarian physical-metric contract.
- `failure_mode`: A mixed or negative physical result means synthetic-source scalar transfer is insufficient; no test-truth alpha tuning is permitted.
- `mechanism_note`: The fixed source-trained bounded-refinement parameter improves channel NMSE and both CIR-grounded physical RMSE metrics on the tested CDL cells.
- `next_action`: If supported, scale the unchanged contract; if mixed/refuted, preserve the negative result and implement a genuinely richer trained refinement model before another external run.
- `evidence_level`: E1 auxiliary/dev trained-refinement physical transfer evidence.

## Key Metrics

- `profiles`: `A`
- `snrs_db`: `20.0`
- `l_values`: `4`
- `seed_count`: 1
- `samples_per_profile_seed`: 2
- `row_count`: 1
- `sample_row_count`: 2
- `source_alpha`: 0.64192
- `source_alpha_source`: `05_results\stage2_torch_locked_scale_g2_seed_sweep\stage2_torch_locked_scale_g2_seed_sweep_seeds.csv`
- `mean_grid_channel_nmse_db`: -7.88777
- `mean_trained_refinement_channel_nmse_db`: -16.645
- `mean_trained_refinement_gain_vs_grid_db`: 8.75723
- `min_cell_trained_refinement_gain_vs_grid_db`: 8.75723
- `mean_grid_physical_delay_rmse_ns`: 101.29
- `mean_trained_refinement_physical_delay_rmse_ns`: 87.3105
- `mean_physical_delay_rmse_reduction_vs_grid_ns`: 13.979
- `mean_grid_projected_broadside_angle_rmse_deg`: 32.5943
- `mean_trained_refinement_projected_broadside_angle_rmse_deg`: 29.1385
- `mean_projected_angle_rmse_reduction_vs_grid_deg`: 3.45582
- `min_cell_physical_delay_rmse_reduction_vs_grid_ns`: 13.979
- `min_cell_projected_angle_rmse_reduction_vs_grid_deg`: 3.45582
- `delay_resolution_ns`: 130.208
- `elapsed_seconds`: 0.0267957
- `claim_update`: `trained-refinement-physical-transfer-supported-dev`
