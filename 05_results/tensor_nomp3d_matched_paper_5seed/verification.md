# E12 matched-accuracy verification

Verdict: `trusted_with_caveats` for a comparison-ready 3-D cyclic NOMP-inspired baseline.

- Paired paper-scale samples: 1200
- Minimum NOMP-inspired gain over grid: 24.6422 dB
- Maximum normalized joint-bin RMSE: 0.263217
- Minimum all-axis half-bin hit fraction: 0.6250
- Median runtime ratio versus fixed scalar path: 8.106x

## Per-target-count NOMP-inspired result

| L | n | Mean NMSE (dB) | Median NMSE (dB) | Min gain vs grid (dB) | Max joint-bin RMSE | Half-bin hit | Median ms |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 400 | -56.5333 | -57.5017 | 29.2867 | 0.00141642 | 1.0000 | 1164.49 |
| 4 | 400 | -53.4656 | -53.5502 | 26.3934 | 0.263217 | 0.9994 | 3513.99 |
| 8 | 400 | -50.1715 | -48.6952 | 24.6422 | 0.188053 | 0.9981 | 12042.21 |

## Paired NMSE comparisons

- `grid_fft_topk_plus_ls`: NOMP advantage mean 47.9602 dB; median 48.2631 dB; minimum 24.6422 dB; win fraction 1.0000; seed-mean 95% CI [47.8090, 48.1113] dB.
- `deterministic_cartesian_local_refinement_plus_ls`: NOMP advantage mean 40.6555 dB; median 41.0102 dB; minimum 17.4574 dB; win fraction 1.0000; seed-mean 95% CI [40.5175, 40.7935] dB.
- `fixed_source_trained_scalar_interpolation_plus_ls`: NOMP advantage mean 42.1756 dB; median 42.6541 dB; minimum 19.0538 dB; win fraction 1.0000; seed-mean 95% CI [42.0140, 42.3372] dB.

## Scope boundary

- The comparator uses known target count, dense tensor measurements, and a matched sinusoidal generator.
- It is a 3-D mechanism adaptation, not a reproduction of sparse-resource 2-D NOMP-OFDM-ISAC or its CFAR rule.
- The result refutes any accuracy-superiority claim for the current learned scalar in the matched synthetic regime.
- The remaining defensible question is whether learning can amortize continuous refinement cost or improve shifted/external regimes.
- Per-SNR/per-L seed-mean confidence intervals and runtime ratios are retained in `per_snr_l_comparisons.csv`.
