# E12 matched-accuracy verification

Verdict: `trusted_with_caveats` for a comparison-ready 3-D cyclic NOMP-inspired baseline.

- Paired paper-scale samples: 30
- Minimum NOMP-inspired gain over grid: 47.1827 dB
- Maximum normalized joint-bin RMSE: 0.000129528
- Minimum all-axis half-bin hit fraction: 1.0000
- Median runtime ratio versus fixed scalar path: 7.584x

## Per-target-count NOMP-inspired result

| L | n | Mean NMSE (dB) | Median NMSE (dB) | Min gain vs grid (dB) | Max joint-bin RMSE | Half-bin hit | Median ms |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 10 | -61.7273 | -62.7459 | 51.0903 | 5.89585e-05 | 1.0000 | 949.99 |
| 4 | 10 | -58.6238 | -58.5295 | 48.6197 | 6.59888e-05 | 1.0000 | 2711.47 |
| 8 | 10 | -55.4277 | -55.1525 | 47.1827 | 0.000129528 | 1.0000 | 8996.64 |

## Paired NMSE comparisons

- `grid_fft_topk_plus_ls`: NOMP advantage mean 53.1810 dB; median 52.3266 dB; minimum 47.1827 dB; win fraction 1.0000; seed-mean 95% CI [52.0822, 54.2798] dB.
- `deterministic_cartesian_local_refinement_plus_ls`: NOMP advantage mean 46.0875 dB; median 46.5237 dB; minimum 38.2998 dB; win fraction 1.0000; seed-mean 95% CI [44.4496, 47.7253] dB.
- `fixed_source_trained_scalar_interpolation_plus_ls`: NOMP advantage mean 47.1872 dB; median 47.0630 dB; minimum 41.4875 dB; win fraction 1.0000; seed-mean 95% CI [46.0935, 48.2809] dB.

## Scope boundary

- The comparator uses known target count, dense tensor measurements, and a matched sinusoidal generator.
- It is a 3-D mechanism adaptation, not a reproduction of sparse-resource 2-D NOMP-OFDM-ISAC or its CFAR rule.
- The result refutes any accuracy-superiority claim for the current learned scalar in the matched synthetic regime.
- The remaining defensible question is whether learning can amortize continuous refinement cost or improve shifted/external regimes.
