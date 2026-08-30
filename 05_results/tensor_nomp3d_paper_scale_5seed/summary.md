# E12 3-D cyclic NOMP-inspired matched pilot

This pilot verifies comparator wiring and a fair paired metric contract. It is not a paper-scale claim.

| Method | NMSE (dB) | Gain vs grid (dB) | Joint bin RMSE | Within 0.5 bin | Median ms |
|---|---:|---:|---:|---:|---:|
| grid_fft_topk_plus_ls | -5.4119 | 0.0000 | 0.152445 | 0.6958 | 10.69 |
| deterministic_cartesian_local_refinement_plus_ls | -12.5055 | 7.0935 | 0.150514 | 0.7833 | 379.26 |
| fixed_source_trained_scalar_interpolation_plus_ls | -11.4057 | 5.9938 | 0.150349 | 0.7500 | 380.08 |
| tensor_nomp3d_known_order_v1 | -26.8631 | 21.4512 | 0.070458 | 0.8833 | 2237.93 |

- All methods receive the same samples, known target count, and least-squares reconstruction contract.
- The fixed scalar is the mean source-trained G2 alpha and is not tuned on pilot truth.
- The 3-D cyclic NOMP-inspired comparator adapts detection/local-Newton/cyclic-feedback to a dense tensor; it is not an exact reproduction of the sparse-resource 2-D OFDM algorithm or CFAR stopping rule.
- This is a baseline verification pilot, not yet a paper-scale matched-accuracy result.
