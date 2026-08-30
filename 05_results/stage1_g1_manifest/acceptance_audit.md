# Stage 1 G1 Acceptance Audit

Date: 2026-06-24

## V2.3R Gate Text

G1 requires Tensor-OMP on Set A to achieve single/multi-target recovery RMSE close to CRLB, output NMSE / range / velocity / angle RMSE, and show high-SNR CRLB-consistent trend. If G1 fails, Stage 2 must not start.

DeepMIMO Set E is listed under G3, not G1. The local 5G Toolbox and DeepMIMO dataset gaps remain important external dependencies, but they do not block Stage 2 under the V2.3R gate definition.

## Requirement Audit

| Requirement | Evidence | Status |
|---|---|---|
| Set A Tensor-OMP executable path | `05_results/stage1_g1_smoke/` | pass |
| Single/multi-target recovery metrics | `05_results/stage1_g1_smoke/`, `05_results/paper_scale_tensor_omp_g1/` | pass |
| Paper-scale L scan | `05_results/paper_scale_tensor_omp_g1/` for L={2,4,8,16,32,64} | pass |
| Off-grid bounded refinement mechanism | `05_results/paper_scale_offgrid_stress_g1/` | pass |
| 5L FIM/CRLB implementation correctness | `05_results/crlb_5l_fim_validation/` | pass |
| High-SNR CRLB trend | `05_results/crlb_5l_monte_carlo/` | pilot-pass |
| Standards-aligned CDL/DeepMIMO | `05_results/stage1_dependency_audit/` | moved to G3/external-dependency tracker |

## Decision

G1 is accepted for V2.3R Stage 1 based on current local evidence. Stage 2 may begin with a bounded minimal T-OMP-Net smoke. This does not waive the later G3 DeepMIMO requirement.

