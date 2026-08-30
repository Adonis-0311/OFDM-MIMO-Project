# Paper-Scale Tensor-OMP G1 Scan

- Config hash: `fft-unitary-20260624`

## Metrics

- `tensor_shape`: `128x16x32`
- `snr_db`: 20
- `n_trials_per_l`: `12`
- `mean_nmse_db_all`: -57.8482
- `min_support_recall`: 1
- `mean_abs_nmse_crlb_gap_db`: 0.321266
- `wall_seconds`: 0.739719

## Notes

- Paper-scale scan follows the v2.3R Stage-1 target shape 128x16x32 and L in {2,4,8,16,32,64}.
- The unitary FFT tensor contract is equivalent to a normalized on-grid DFT dictionary and avoids materializing a 65536x65536 matrix.
- This remains an on-grid baseline scan; off-grid and final 5L CRLB validation are still pending.

## Artifacts

- `05_results\paper_scale_tensor_omp_g1\paper_scale_tensor_omp_g1.csv`
- `05_results\paper_scale_tensor_omp_g1\run_manifest.json`
