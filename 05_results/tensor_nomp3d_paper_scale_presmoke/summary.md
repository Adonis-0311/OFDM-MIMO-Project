# E12 3-D cyclic NOMP-inspired matched pilot

This pilot verifies comparator wiring and a fair paired metric contract. It is not a paper-scale claim.

| Method | NMSE (dB) | Gain vs grid (dB) | Joint bin RMSE | Within 0.5 bin | Median ms |
|---|---:|---:|---:|---:|---:|
| grid_fft_topk_plus_ls | -4.4498 | 0.0000 | 0.196548 | 0.5833 | 10.59 |
| deterministic_cartesian_local_refinement_plus_ls | -11.6480 | 7.1982 | 0.197433 | 0.7500 | 373.81 |
| fixed_source_trained_scalar_interpolation_plus_ls | -9.4993 | 5.0495 | 0.196799 | 0.7500 | 425.10 |
| tensor_nomp3d_known_order_v1 | -9.9348 | 5.4850 | 0.167149 | 0.7917 | 2597.26 |

- All methods receive the same samples, known target count, and least-squares reconstruction contract.
- The fixed scalar is the mean source-trained G2 alpha and is not tuned on pilot truth.
- The 3-D cyclic NOMP-inspired comparator adapts detection/local-Newton/cyclic-feedback to a dense tensor; it is not an exact reproduction of the sparse-resource 2-D OFDM algorithm or CFAR stopping rule.
- This is a baseline verification pilot, not yet a paper-scale matched-accuracy result.
