# Stage 1 G1 Smoke Evaluation Summary

## Outcome Summary

The stage-1 Python path is executable and comparable for bounded smoke, paper-scale on-grid, paper-scale off-grid, and analytic 5L FIM validation settings. It supports the v2.3R expectation that Stage 1 mechanics are real enough to keep advancing, while Pack 3 remains gated.

## evaluation_summary

- `research_question`: Can the v2.3R Stage 1 Python infrastructure generate Set A samples, run Tensor-OMP, emit required recovery metrics, and preserve a manifest?
- `claim_update`: Supported for smoke-level wiring, baseline comparability, on-grid paper-scale Tensor-OMP recovery, low/mid-L off-grid bounded refinement, analytic 5L FIM correctness, and single-target estimator-efficiency pilot; inconclusive for full G1 because realistic channel wrappers remain pending.
- `baseline_relation`: This run creates a Python Tensor-OMP baseline path and does not replace the existing v2.2 MATLAB supplemental evidence.
- `failure_mode`: None for final executed local scans. Remaining issue is external dependency readiness: 5G Toolbox license is unavailable and DeepMIMO scenario dataset files are absent.
- `next_action`: Begin bounded Stage 2 / Pack 3 minimal T-OMP-Net smoke while tracking CDL/DeepMIMO dependencies for G3.
- `evidence_level`: G1 accepted under the V2.3R gate definition; G2 remains unproven.

## Key Metrics

- Mean NMSE over all smoke cells: -47.4387 dB
- Mean support recall over all smoke cells: 0.999074
- Mean NMSE at 30 dB: -56.8796 dB
- Mean support recall at 30 dB: 1.0
- Max delay RMSE at 30 dB: 0 grid bins
- Paper-scale shape: 128x16x32
- Paper-scale L scan: {2, 4, 8, 16, 32, 64}
- Paper-scale minimum support recall: 1.0
- Paper-scale mean NMSE: -57.8482 dB
- Paper-scale mean absolute NMSE-vs-CRLB-proxy gap: 0.3213 dB
- Off-grid mean refinement gain: 7.5368 dB
- Off-grid minimum L-cell refinement gain: 6.9946 dB
- Max 5L analytic-vs-numeric FIM relative error: 5.7304e-10
- 5L Monte Carlo mean RMSE/CRLB ratio at 30 dB: 1.0067
- 5L Monte Carlo angle RMSE drop from 10 dB to 30 dB: 9.928x
