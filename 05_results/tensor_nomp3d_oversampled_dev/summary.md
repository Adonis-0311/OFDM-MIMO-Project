# E12 3-D cyclic NOMP-inspired matched pilot

This pilot verifies comparator wiring and a fair paired metric contract. It is not a paper-scale claim.

| Method | NMSE (dB) | Gain vs grid (dB) | Joint bin RMSE | Within 0.5 bin | Median ms |
|---|---:|---:|---:|---:|---:|
| grid_fft_topk_plus_ls | -5.9911 | 0.0000 | 0.138297 | 0.7083 | 12.09 |
| deterministic_cartesian_local_refinement_plus_ls | -13.5225 | 7.5314 | 0.135659 | 0.8125 | 399.07 |
| fixed_source_trained_scalar_interpolation_plus_ls | -12.4253 | 6.4343 | 0.135553 | 0.8125 | 404.10 |
| tensor_nomp3d_known_order_v1 | -58.4920 | 52.5009 | 0.000036 | 1.0000 | 2799.40 |

- All methods receive the same samples, known target count, and least-squares reconstruction contract.
- The fixed scalar is the mean source-trained G2 alpha and is not tuned on pilot truth.
- The 3-D cyclic NOMP-inspired comparator adapts detection/local-Newton/cyclic-feedback to a dense tensor; it is not an exact reproduction of the sparse-resource 2-D OFDM algorithm or CFAR stopping rule.
- This is a baseline verification pilot, not yet a paper-scale matched-accuracy result.
