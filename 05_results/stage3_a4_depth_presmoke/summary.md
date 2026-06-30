# Stage 3 A4 IA-AUD Depth Pre-Smoke

- Config hash: `stage3-a4-depth-presmoke-20260624`

## Metrics

- `tensor_shape`: `128x16x32`
- `snr_db`: 20
- `seed`: `20260624`
- `l_values`: `[2, 8, 32]`
- `n_trials_per_l`: `2`
- `depth_values`: `[0, 1, 2, 3, 4, 5, 6, 7, 8]`
- `radii`: `[0.45, 0.28, 0.18, 0.11, 0.07, 0.045, 0.03, 0.02]`
- `search_points`: `3`
- `saturation_tolerance_db`: 0.5
- `saturation_depth_by_l`: `{2: 8, 8: 8, 32: 5}`
- `depth_spread`: `3`
- `mean_gain_k8_by_l`: `{2: 25.130514912000727, 8: 19.586505839355617, 32: 8.176434652575816}`
- `elapsed_seconds`: 16.7879

## Notes

- A4 pre-smoke uses repeated bounded off-grid refinement as the fixed-depth proxy.
- K=0 is grid Tensor-OMP support with LS amplitudes; K=1..8 applies progressively smaller local-search radii.
- This checks whether IA-AUD has a real depth-allocation opportunity before implementing a gating network.

## Artifacts

- `05_results\stage3_a4_depth_presmoke\stage3_a4_depth_presmoke.csv`
- `05_results\stage3_a4_depth_presmoke\stage3_a4_depth_presmoke_samples.csv`
- `05_results\stage3_a4_depth_presmoke\run_manifest.json`
