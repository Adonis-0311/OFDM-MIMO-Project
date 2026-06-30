# v2.3R Paper Evidence Table

- Config hash: `v2-3r-paper-evidence-table-20260627`

## Metrics

- `n_rows`: `19`
- `supported_local_rows`: `6`
- `blocked_rows`: `0`
- `downgraded_rows`: `1`
- `g2_mean_gain_db`: 5.89563
- `a4_high_l_min_savings_percent`: 26.5
- `a4_snr_min_savings_percent`: 21.875
- `a4_snr_max_gap_db`: 0.683446
- `a4_frontier_standard_min_savings_percent`: 15.625
- `a4_frontier_oracle_min_savings_percent`: 0
- `a4_frontier_oracle_max_gap_db`: 0.455448
- `a4_snr_aware_knn_min_savings_percent`: 21.875
- `a4_snr_aware_knn_max_gap_db`: 0.655772
- `a4_snr_aware_oracle_min_savings_percent`: 21.875
- `a4_snr_aware_oracle_max_gap_db`: 0.490573
- `sionna_cdl_claim_update`: `executable-but-weak-support`
- `sionna_cdl_min_mean_support_recall`: 0.171875
- `sionna_cdl_mean_channel_nmse_db`: -12.8145
- `sionna_cdl_scaled_claim_update`: `energy-supported-exact-bin-weak`
- `sionna_cdl_scaled_seed_count`: 5
- `sionna_cdl_scaled_samples_per_profile_seed`: 50
- `sionna_cdl_scaled_mean_channel_nmse_db`: -11.4399
- `sionna_cdl_scaled_min_mean_support_recall`: 0.41875
- `sionna_cdl_scaled_min_topk_energy_efficiency`: 0.988554
- `sionna_cdl_scaled_min_delay_support_recall`: 0.45125
- `sionna_cdl_scaled_min_angle_support_recall`: 0.6225
- `sionna_cdl_physical_metric_status`: `cir-grounded-grid-baseline-and-clean-floor-recorded`
- `sionna_cdl_physical_mean_delay_rmse_ns`: 180.229
- `sionna_cdl_physical_mean_delay_rmse_ns_snr_ge_20`: 141.32
- `sionna_cdl_physical_clean_grid_delay_floor_ns`: 141.323
- `sionna_cdl_physical_mean_projected_angle_rmse_deg`: 28.6253
- `sionna_cdl_physical_clean_grid_projected_angle_floor_deg`: 28.4459
- `deepmimo_o1_claim_update`: `dev-source-alpha-transfer-supported`
- `deepmimo_o1_transfer_proxy_classification`: `weak`
- `deepmimo_o1_source_alpha`: 0.64192
- `deepmimo_o1_min_mean_support_recall`: 0.808594
- `deepmimo_o1_mean_grid_channel_nmse_db`: -4.3252
- `deepmimo_o1_mean_source_alpha_channel_nmse_db`: -5.70565
- `deepmimo_o1_mean_source_alpha_gain_vs_grid_db`: 1.38045
- `deepmimo_o1_min_source_alpha_gain_vs_grid_db`: 0.924413
- `deepmimo_o1_mean_bounded_refine_channel_nmse_db`: -5.70396
- `deepmimo_o1_mean_bounded_gain_vs_grid_db`: 1.37877
- `deepmimo_o1_min_bounded_gain_vs_grid_db`: 0.913456
- `deepmimo_o1_mean_source_alpha_gap_vs_oracle_db`: 0.185169
- `deepmimo_i3_claim_update`: `partial-source-alpha-transfer`
- `deepmimo_i3_transfer_proxy_classification`: `partial`
- `deepmimo_i3_source_alpha`: 0.64192
- `deepmimo_i3_min_mean_support_recall`: 0.332031
- `deepmimo_i3_mean_grid_channel_nmse_db`: -13.9115
- `deepmimo_i3_mean_source_alpha_channel_nmse_db`: -20.6868
- `deepmimo_i3_mean_source_alpha_gain_vs_grid_db`: 6.77532
- `deepmimo_i3_min_source_alpha_gain_vs_grid_db`: -0.146942
- `deepmimo_i3_mean_bounded_refine_channel_nmse_db`: -20.2101
- `deepmimo_i3_mean_bounded_gain_vs_grid_db`: 6.2986
- `deepmimo_i3_min_bounded_gain_vs_grid_db`: -0.261577
- `deepmimo_i3_mean_source_alpha_gap_vs_oracle_db`: 1.06062
- `deepmimo_campaign_n_seeds`: `5`
- `deepmimo_campaign_n_users_per_seed`: `100`
- `deepmimo_campaign_o1_classification`: `weak`
- `deepmimo_campaign_o1_mean_gain_db`: 1.32345
- `deepmimo_campaign_o1_gain_ci95_low_db`: 1.25385
- `deepmimo_campaign_o1_gain_ci95_high_db`: 1.39306
- `deepmimo_campaign_o1_min_cell_gain_db`: 0.855446
- `deepmimo_campaign_i3_classification`: `partial`
- `deepmimo_campaign_i3_mean_gain_db`: 6.70143
- `deepmimo_campaign_i3_gain_ci95_low_db`: 6.46602
- `deepmimo_campaign_i3_gain_ci95_high_db`: 6.93685
- `deepmimo_campaign_i3_min_cell_gain_db`: -0.241151
- `complexity_claim_update`: `complexity-comparator-table-ready`
- `complexity_implemented_rows`: 15
- `complexity_not_implemented_rows`: 0
- `complexity_max_median_wall_clock_ms`: 1678.39
- `deepmimo_status`: `ready_open_source`
- `deepmimo_dataset_files`: `4188`

## Notes

- Generated manuscript-facing evidence map from current run manifests.
- The table preserves claim boundaries so local evidence is not promoted to external validation.
- Regenerate this table after rerunning G2, A4, DeepMIMO, A5, Kruskal, synthetic, or CRLB evidence.

## Artifacts

- `05_results\v2_3r_paper_evidence_table\paper_evidence_table.csv`
- `05_results\v2_3r_paper_evidence_table\paper_evidence_table.md`
- `05_results\v2_3r_paper_evidence_table\run_manifest.json`
