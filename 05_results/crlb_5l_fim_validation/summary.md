# 5L CRLB FIM Validation

- Config hash: `5l-fim-20260624`

## Metrics

- `tensor_shape`: `128x16x32`
- `max_relative_fim_error`: 5.73037e-10
- `angle_std_drop_0db_to_30db`: 31.6228
- `mean_relative_fim_error`: 5.73037e-10
- `snr_points`: `0,10,20,30`

## Notes

- 5L parameter vector is [angle_bin, delay_bin, doppler_bin, gain_real, gain_imag].
- Complex Gaussian FIM uses 2/sigma^2 Re{dmu_i^H dmu_j}.
- This validates analytic derivatives against central finite differences; it is the Stage-1 FIM/CRLB implementation gate, not a Monte Carlo estimator-efficiency claim.

## Artifacts

- `05_results\crlb_5l_fim_validation\crlb_5l_fim_validation.csv`
- `05_results\crlb_5l_fim_validation\run_manifest.json`
