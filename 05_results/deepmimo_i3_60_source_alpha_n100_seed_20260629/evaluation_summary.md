# DeepMIMO I3_60 Cross-Domain Dev Summary

## Outcome Summary

This E3 dev-run reads local DeepMIMO I3_60 CIR MAT files, synthesizes normalized OFDM frequency responses, adds AWGN, and evaluates grid FFT top-k, Stage-2 source-trained alpha transfer, full bounded refinement, and oracle-alpha diagnostics.

It is not yet the full cross-domain G2/T-OMP-Net result: the transferred object is the scalar Stage-2 alpha path rather than a full network, and delay/TX metrics remain dominant-bin proxy metrics.

## evaluation_summary

- `research_question`: Can I3_60 indoor ray-traced CIR data be converted into reproducible OFDM channel tensors and assigned a weak/partial/fail proxy classification under the current Tensor-OMP-style metric contract?
- `claim_update`: partial-source-alpha-transfer
- `transfer_proxy_classification`: partial
- `source_alpha`: 0.6419195571509573
- `baseline_relation`: Stage-2 source-trained alpha is compared against grid FFT top-k on the same noisy I3_60 synthesized channel tensor; full bounded refinement and oracle-alpha are diagnostic comparators.
- `failure_mode`: None if executable; limitation is raw-loader proxy metrics, two-BS channel width, and scalar-alpha rather than full trained cross-domain model transfer.
- `mechanism_note`: The source-trained G2 alpha improves mean I3_60 NMSE, but at least one cell has weak dominant-bin recall.
- `next_action`: Attach the trained locked-scale G2/T-OMP-Net path or train an I3-compatible adapter, then rerun I3_60 with physical angle/delay metrics.
- `evidence_level`: E3 auxiliary/dev raw-loader and proxy cross-scenario classification.

## Key Metrics

- `claim_update`: `partial-source-alpha-transfer`
- `transfer_proxy_classification`: `partial`
- `dataset`: `DeepMIMO I3_60_v1 CIR files`
- `bs_indices`: `1,2`
- `source_alpha`: 0.64192
- `source_alpha_source`: `05_results\stage2_torch_locked_scale_g2_seed_sweep\stage2_torch_locked_scale_g2_seed_sweep_seeds.csv`
- `candidate_alphas`: `0.0,0.2,0.4,0.6,0.8,1.0,1.2`
- `n_users`: 100
- `n_bs`: 2
- `num_subcarriers`: 64
- `snrs_db`: `0.0,10.0,20.0,30.0`
- `l_values`: `4,8,16`
- `row_count`: 12
- `sample_row_count`: 1200
- `min_mean_support_recall`: 0.31875
- `mean_grid_channel_nmse_db_all`: -13.8074
- `mean_source_alpha_channel_nmse_db_all`: -20.6861
- `mean_source_alpha_gain_vs_grid_db`: 6.87868
- `min_source_alpha_gain_vs_grid_db`: -0.132838
- `mean_bounded_refine_channel_nmse_db_all`: -20.2845
- `mean_bounded_gain_vs_grid_db`: 6.47707
- `min_bounded_gain_vs_grid_db`: -0.1819
- `mean_oracle_alpha_channel_nmse_db_all`: -21.7321
- `mean_oracle_alpha_gain_vs_grid_db`: 7.92471
- `mean_source_alpha_gap_vs_oracle_db`: 1.04603
- `mean_oracle_alpha`: 0.805667
- `mean_dominant_energy_recall_all`: 0.968654
- `mean_path_count`: 14.135
- `min_path_count`: 9
- `max_path_count`: 21
- `rx_x_span_m`: 9.1266
- `rx_y_span_m`: 8.34398
- `finite_delay_truth_fraction`: 1
- `finite_power_truth_fraction`: 1
- `elapsed_seconds`: 10.4025
