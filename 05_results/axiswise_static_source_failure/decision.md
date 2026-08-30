# Static axiswise source-training decision

Generated: 2026-06-27

## Parent problem

The shared scalar source-alpha layer improves CDL channel NMSE and delay RMSE but worsens projected-angle RMSE. A delay-only diagnostic localizes the failure to shared-axis coupling.

## Tested source-only repairs

| Repair | Source geometry | Learned parameters | Local result | Decision |
|---|---|---|---|---|
| Three static axis alphas | 128x16x32 synthetic | angle 0.64152, delay 0.64222, Doppler 0.64222 | 5.7667 dB mean gain vs grid, but only 0.00135 dB vs shared alpha | Reject as functionally identical to shared alpha |
| Two static geometry-matched alphas | 64x4 synthetic; CDL SNR/L contract | delay 0.64008, angle 0.64131 | 4.0185 dB mean gain; axis separation -0.00123 | Reject static-global model family; geometry matching alone does not create axis selectivity |

Both are bounded smoke results, not paper-facing experiments. No Sionna CDL data or truth was used for training.

## Interpretation

The synthetic NMSE objective consistently prefers the same global interpolation scale on every axis. Adding parameter count without conditioning does not address the external angle failure. A five-seed static rerun is low-value because the route decision is already invariant to plausible seed noise: the learned scales differ by roughly 0.001 while the external diagnostic requires suppressing most angle refinement.

## Next route

Implement a feature-conditioned refinement controller that predicts per-sample delay and angle scales from estimator-internal observables (support budget, refinement displacement, peak/curvature or residual features). Train only on geometry-matched synthetic data with a combined channel-NMSE and Hungarian permutation-invariant parameter objective. Freeze the controller before a single unchanged Sionna CDL evaluation.

The next model must be rejected if it collapses to constant outputs, fails local held-out parameter/NMSE gates, or requires CDL-truth tuning.

