# v2.3R E12 Route Decision — 2026-06-29

## Verdict

- Canonical action: `branch`
- Branch from: learned bounded refinement as an accuracy contribution over grid Tensor-OMP.
- Branch to: learned/amortized bounded refinement as a computation--accuracy trade-off relative to a strong continuous optimizer, with external-distribution robustness as the second possible value axis.
- Paper status: active research draft, not submission-ready.

## Decisive evidence

The accepted comparison-ready baseline is the known-order, oversampled 3-D cyclic NOMP-inspired implementation in `03_active_modules/baseline/tensor_nomp.py`. Its contract explicitly records the dense-3-D and known-order deviations from the cited NOMP algorithms.

On 30 paired held-out samples at tensor shape `128x16x32`, SNR 20 dB, and `L={2,4,8}`:

- NOMP-inspired minimum gain over grid: `47.1827 dB`.
- NOMP-inspired minimum paired advantage over the fixed learned scalar: `41.4875 dB`.
- Maximum normalized joint-bin RMSE: `1.2953e-4`.
- All-axis half-bin hit fraction: `1.0` on every sample.
- Median runtime ratio relative to the fixed scalar path: `7.5838x`.
- Per-L median NOMP time: `0.950 / 2.711 / 8.997 s` for `L=2/4/8`.

Evidence:

- `05_results/tensor_nomp3d_baseline/json/metric_contract.json`
- `05_results/tensor_nomp3d_baseline/json/baseline_acceptance.json`
- `05_results/tensor_nomp3d_oversampled_paper_scale_5seed/verification.md`
- `05_results/tensor_nomp3d_oversampled_paper_scale_5seed/run_manifest.json`

## Interpretation

The matched synthetic generator is exactly a sum of separable continuous sinusoids, so an oversampled continuous optimizer is expected to approach the projection/noise floor once it enters the correct basin. The result is therefore scientifically plausible rather than an accuracy anomaly. It also shows that comparing only against the grid estimator materially overstates the strength of the learned scalar result.

The current scalar path is not an amortized estimator: it first pays for the deterministic Cartesian candidate search and then scales that candidate. In the same campaign, deterministic full refinement has better mean NMSE than the learned scalar at comparable runtime. Thus neither accuracy nor compute currently justifies the scalar as the central algorithmic contribution.

## Rejected routes

1. `continue` the old T-OMP-Net/deep-unfolding accuracy story — rejected because the integrated network is absent and the strong continuous comparator dominates.
2. Hide NOMP-inspired in supplementary material — rejected because it is the closest mechanism comparator and changes the central claim.
3. Stop the whole project — rejected because the 7.58x runtime gap and held-out CDL controller result leave two testable value axes: amortized compute and shifted/external robustness.
4. Tune more scalar interpolation coefficients — rejected because the bottleneck is candidate construction and continuous optimization, not scalar calibration.

## Next direction

Enter `idea` with two structurally distinct candidate families:

1. **Amortized offset prediction:** predict bounded continuous offsets directly from a small local FFT/residual patch, eliminating the Cartesian candidate search. Gate on accuracy versus runtime against NOMP-inspired and deterministic local search.
2. **Warm-started truncated Newton:** predict an initialization or per-axis step, then run one safeguarded Newton/cyclic pass. Gate on retaining most NOMP accuracy at materially lower runtime and test whether the warm start remains useful on CDL/DeepMIMO shifts.

Do not resume the old headline unless a candidate clears a comparator-inclusive Pareto gate. A proposed paper-facing gate is:

- positive paired NMSE improvement over grid on every evaluated cell;
- median runtime at most `0.35x` of oversampled NOMP-inspired;
- median NMSE gap to NOMP-inspired at most `3 dB`, or a clearly documented external-shift advantage that NOMP does not retain;
- no truth-tuned test-time parameters;
- five-seed paper-scale evaluation with failure cells retained.
