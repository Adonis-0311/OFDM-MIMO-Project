# E12 3-D cyclic NOMP-inspired matched pilot

This pilot verifies comparator wiring and a fair paired metric contract. It is not a paper-scale claim.

| Method | NMSE (dB) | Gain vs grid (dB) | Joint bin RMSE | Within 0.5 bin | Median ms |
|---|---:|---:|---:|---:|---:|
| grid_fft_topk_plus_ls | -5.7380 | 0.0000 | 0.185553 | 0.6389 | 0.76 |
| deterministic_cartesian_local_refinement_plus_ls | -12.3247 | 6.5866 | 0.182351 | 0.7361 | 13.89 |
| fixed_source_trained_scalar_interpolation_plus_ls | -10.9779 | 5.2398 | 0.180826 | 0.7222 | 14.04 |
| tensor_nomp3d_known_order_v1 | -21.4895 | 15.7515 | 0.113905 | 0.8333 | 29.87 |

- All methods receive the same samples, known target count, and least-squares reconstruction contract.
- The fixed scalar is the mean source-trained G2 alpha and is not tuned on pilot truth.
- The 3-D cyclic NOMP-inspired comparator adapts detection/local-Newton/cyclic-feedback to a dense tensor; it is not an exact reproduction of the sparse-resource 2-D OFDM algorithm or CFAR stopping rule.
- This is a baseline verification pilot, not yet a paper-scale matched-accuracy result.
