# DeepMIMO O1_60 G2 Evaluation Summary

## Outcome Summary

This E2 dev-run reads local DeepMIMO O1_60 raw ray files, synthesizes normalized OFDM frequency responses, adds AWGN, and evaluates grid FFT top-k, Stage-2 source-trained alpha transfer, full bounded refinement, and oracle-alpha diagnostics on the same clean/noisy channel tensors.

It is not yet the full Sensors E2 result: this run uses a raw MAT loader and delay/TX-bin proxy metrics, and transfers only the scalar Stage-2 alpha path rather than a full trained T-OMP-Net.

## evaluation_summary

- `research_question`: Can O1_60 ray-traced data be converted into reproducible OFDM channel tensors and evaluated with the existing Tensor-OMP-style metric contract?
- `claim_update`: dev-source-alpha-transfer-supported
- `transfer_proxy_classification`: weak
- `source_alpha`: 0.6419195571509573
- `baseline_relation`: Stage-2 source-trained alpha is compared against grid FFT top-k on the same noisy O1_60 synthesized channel tensor; full bounded refinement and oracle-alpha are diagnostic comparators.
- `failure_mode`: None if executable; limitation is raw-loader proxy metrics and small dev sample size.
- `mechanism_note`: The source-trained G2 alpha transfer proxy produced finite O1_60 metrics with positive mean gain and acceptable dominant-bin recall in this dev grid.
- `next_action`: Attach the full trained G2/T-OMP-Net path and scale to 5 seeds x 100 users x SNR {0,10,20,30}.
- `evidence_level`: E2 auxiliary/dev raw-loader and scalar source-alpha transfer validation.

## Key Metrics

- `claim_update`: `dev-source-alpha-transfer-supported`
- `transfer_proxy_classification`: `weak`
- `dataset`: `DeepMIMO O1_60 raw ray files`
- `rx_tag`: `r000`
- `tx_tags`: `t003,t004,t005,t006,t007,t008,t009,t010`
- `source_alpha`: 0.64192
- `source_alpha_source`: `05_results\stage2_torch_locked_scale_g2_seed_sweep\stage2_torch_locked_scale_g2_seed_sweep_seeds.csv`
- `candidate_alphas`: `0.0,0.2,0.4,0.6,0.8,1.0,1.2`
- `n_users`: 100
- `n_tx`: 8
- `num_subcarriers`: 64
- `snrs_db`: `0.0,10.0,20.0,30.0`
- `l_values`: `4,8,16`
- `row_count`: 12
- `sample_row_count`: 1200
- `min_mean_support_recall`: 0.825
- `mean_grid_channel_nmse_db_all`: -4.60287
- `mean_source_alpha_channel_nmse_db_all`: -5.93501
- `mean_source_alpha_gain_vs_grid_db`: 1.33214
- `min_source_alpha_gain_vs_grid_db`: 0.855446
- `mean_bounded_refine_channel_nmse_db_all`: -5.90661
- `mean_bounded_gain_vs_grid_db`: 1.30374
- `min_bounded_gain_vs_grid_db`: 0.882814
- `mean_oracle_alpha_channel_nmse_db_all`: -6.15924
- `mean_oracle_alpha_gain_vs_grid_db`: 1.55636
- `mean_source_alpha_gap_vs_oracle_db`: 0.224228
- `mean_oracle_alpha`: 0.792167
- `best_mean_grid_channel_nmse_db`: -7.35356
- `worst_mean_grid_channel_nmse_db`: -2.3738
- `mean_dominant_energy_recall_all`: 0.613295
- `rx_x_span_m`: 34.4
- `rx_y_span_m`: 543.4
- `finite_delay_truth_fraction`: 1
- `finite_power_truth_fraction`: 1
- `elapsed_seconds`: 13.5188
