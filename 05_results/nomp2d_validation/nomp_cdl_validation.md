# NOMP-2D validation note (T2.1 gate)

Method: `03_active_modules/baseline/tensor_nomp2d.py` — known-order 2-D
(delay-angle) adaptation of the 3-D NOMP-inspired path: FFT residual detection,
5x5 oversampled init (radius 0.5), safeguarded analytic Newton (2x2
grad/Hessian), cyclic re-refinement, joint-LS accept/reject.

Controlled validation (matched synthetic 64x4 generator, offsets U(-0.35,0.35),
L in {1,2,4}, SNR in {10,20,30} dB, 10 trials/cell, seed 20260703):

- mean NMSE: deterministic local refinement -15.2 dB vs NOMP-2D -38.6 dB
  -> mean advantage 23.3 dB (acceptance gate: >15 dB) PASS
- single-target offset recovery: p95 max-axis bin error 0.011 (gate <0.05) PASS

Verdict: validated for use on CDL observations as an accuracy-oriented
comparator. Boundaries: known target count, no CFAR stopping, dense 64x4
measurement; identical to the 3-D comparator's disclosed scope.
Backing data: 05_results/nomp2d_validation/summary.json.
