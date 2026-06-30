# Stage 1 G1 Smoke

- Config hash: `b10b16fe478c`

## Metrics

- `mean_nmse_db_all`: -47.4387
- `mean_support_recall_all`: 0.999074
- `mean_nmse_db_snr30`: -56.8796
- `mean_support_recall_snr30`: 1
- `mean_nmse_minus_crlb_proxy_db_snr30`: -0.69695
- `max_delay_rmse_bins_snr30`: 0

## Notes

- Stage-1 smoke uses an orthonormal tensor DFT dictionary to verify the Set A -> Tensor-OMP -> metric path.
- The CRLB value is a coefficient-recovery proxy, not the final 5L joint ISAC CRLB required by the paper.
- This run supports G1 wiring and comparability checks; full paper-scale G1 remains pending.

## Artifacts

- `05_results\stage1_g1_smoke\stage1_g1_smoke.csv`
- `05_results\stage1_g1_smoke\run_manifest.json`
