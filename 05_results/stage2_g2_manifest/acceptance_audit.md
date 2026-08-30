# Stage 2 G2 Acceptance Audit

Generated: 2026-06-24

## Scope

This audit evaluates the V2.3R Stage-2 G2 gate under the bounded local experiment contract. It does not claim a broad paper-scale statistical campaign; it decides whether the old Stage-2 blocker is removed enough to start Stage-3 A4/A5 pre-smoke work.

## Gate Verdict

G2 is accepted for the bounded local Stage-2 gate.

## Requirement Checks

| Requirement | Evidence | Verdict | Notes |
|---|---|---|---|
| T-OMP-Net at SNR=20 dB improves over Tensor-OMP by at least 3 dB | `05_results/stage2_torch_locked_scale_g2/` | pass | PyTorch locked-scale mean held-out gain is 6.3646 dB; minimum L-cell gain is 5.1624 dB. |
| Permutation-invariant loss/RMSE consistency | `tests/test_stage1_modules.py`, `05_results/stage2_minimal_tompnet_smoke/` | pass-for-loss / estimator-diagnostic-open | Controlled permutation loss delta is zero; coordinate assignment error remains a diagnostic rather than a blocking G2 metric. |
| Off-grid refinement lowers NMSE by at least 5 dB | `05_results/stage2_torch_locked_scale_g2/`, `05_results/paper_scale_offgrid_stress_g1/` | pass | PyTorch locked-scale mean gain is 6.3646 dB and Stage-1 off-grid stress gain is 7.5368 dB. |
| Trainable layer/curriculum path exists at locked Stage-2 scale | `05_results/stage2_torch_locked_scale_g2/`, `05_results/stage2_curriculum_tompnet_g2/` | pass | A PyTorch `nn.Module` + Adam run completed at 128x16x32 over L={2,4,8}; elapsed time is 8.03 s after equivalent normal-equation loss optimization. |

## Evidence Integrity

- The optimized PyTorch loss is validated against the original slow `forward` + `torch.linalg.lstsq` estimator in `test_torch_fast_loss_matches_forward_estimate`.
- The locked-scale PyTorch run records command, config, seed, environment, metrics, CSV outputs, training history, and evaluation summary.
- The comparison baseline remains grid Tensor-OMP on the same held-out samples.
- Metrics are finite and exceed the G2 threshold in every tested L cell.

## Boundary

This is a bounded local acceptance, not a full statistical campaign. The locked-scale PyTorch run uses one seed, two train samples per L, two held-out samples per L, and L={2,4,8}. Broader seeds, larger held-out counts, or L={16,32,64} should be treated as paper-strengthening analysis, not as a blocker for starting Stage 3 pre-smokes.

## Decision

Stage 3 A4/A5 pre-smoke may start. The next recommended action is:

1. A4 pre-smoke: fixed-depth T-OMP-Net NMSE vs depth for L={2,8,32}.
2. A5 pre-smoke: clean-trained model tested under phase noise sigma_phi={0.5,1,2,3} degrees.
