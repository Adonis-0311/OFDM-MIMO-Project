# Stage 3 5L CRLB Asymptotic Tightness

- Config hash: `stage3-crlb-asymptotic-tightness-20260624`

## Metrics

- `source_fim_csv`: `05_results\crlb_5l_fim_validation\crlb_5l_fim_validation.csv`
- `source_monte_carlo_csv`: `05_results\crlb_5l_monte_carlo\crlb_5l_monte_carlo.csv`
- `claim_update`: `supported-pilot`
- `max_relative_fim_error`: 5.73037e-10
- `mean_ratio_at_30db`: 1.0067
- `max_ratio_at_30db`: 1.50087
- `mean_abs_rmse_slope_error_vs_expected`: 0.00672046
- `mean_abs_crlb_slope_error_vs_expected`: 2.63678e-17
- `expected_log10_slope_per_db`: -0.05
- `elapsed_seconds`: 0.001146

## Notes

- This is a Stage-3 audit of existing 5L CRLB evidence, not a fresh large-sample Monte Carlo.
- The evidence supports single-target high-SNR trend consistency and analytic derivative correctness.
- Small-sample ratios below 1 at lower SNR are treated as a pilot limitation, not as a CRLB violation claim.

## Artifacts

- `05_results\stage3_crlb_asymptotic_tightness\stage3_crlb_asymptotic_tightness.csv`
- `05_results\stage3_crlb_asymptotic_tightness\run_manifest.json`
