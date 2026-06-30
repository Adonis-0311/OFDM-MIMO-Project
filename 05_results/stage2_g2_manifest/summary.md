# Stage 2 G2 Gate Manifest

## Gate Status

| Gate item | Status | Evidence | Metric |
|---|---|---|---|
| T-OMP-Net at SNR=20 dB improves over Tensor-OMP by >=3 dB | locked-scale-pytorch-pass | `stage2_torch_locked_scale_g2 plus stage2_curriculum_tompnet_g2` | PyTorch locked-scale mean gain = 6.3646 dB; min L-cell gain = 5.1624 dB |
| Permutation-invariant loss/RMSE consistency | unit-pass / estimator-pending | `tests/test_stage1_modules.py and stage2_minimal_tompnet_smoke` | controlled permutation loss delta = 0; coordinate assignment error remains diagnostic |
| Off-grid ablation at rho_theta=2 lowers NMSE by >=5 dB | locked-scale-pytorch-pass | `stage2_torch_locked_scale_g2 plus paper_scale_offgrid_stress_g1` | PyTorch locked-scale mean gain = 6.3646 dB; Stage-1 off-grid stress gain = 7.5368 dB |
| Trainable T-OMP-Net layer/curriculum path | locked-scale-pytorch-pass / broader-statistics-optional | `stage2_torch_locked_scale_g2 and stage2_curriculum_tompnet_g2` | nn.Module + Adam at 128x16x32, L={2,4,8}; elapsed = 8.03 s after equivalent normal-equation loss optimization |

## Decision

Stage 2 has passed the minimum wiring/proxy smoke, NumPy parameterized train/test smoke, PyTorch CPU trainable smoke, locked-scale curriculum proxy, and locked-scale PyTorch trainable run at 128x16x32 with L={2,4,8}. G2 is accepted for the bounded local Stage-2 gate: the PyTorch run exceeds the >=3 dB target with mean gain 6.3646 dB and minimum L-cell gain 5.1624 dB.

Stage 3 A4/A5 may start after a short G2 acceptance audit records the small-sample boundary; broader seed/test expansion is optional polish rather than a blocker.

Acceptance audit: `05_results/stage2_g2_manifest/acceptance_audit.md`.
