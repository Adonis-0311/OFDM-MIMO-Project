# Stage 1 G1 Gate Manifest

## Gate Status

| Gate item | Status | Evidence | Metric |
|---|---|---|---|
| Set A -> Tensor-OMP -> metrics -> manifest wiring | pass | `stage1_g1_smoke` | support recall at 30 dB = 1.0; mean NMSE at 30 dB = -56.8796 dB |
| Paper-scale on-grid Tensor-OMP scan | pass | `paper_scale_tensor_omp_g1` | shape 128x16x32; L={2,4,8,16,32,64}; min support recall = 1.0 |
| Paper-scale off-grid bounded refinement stress | pass | `paper_scale_offgrid_stress_g1` | mean refinement gain = 7.5368 dB; minimum L-cell gain = 6.9946 dB |
| 5L analytic FIM/CRLB implementation validation | pass | `crlb_5l_fim_validation` | max analytic-vs-finite-difference FIM relative error = 5.7304e-10 |
| Standards-aligned CDL/DeepMIMO wrapper validation | tracked-for-g3 | `stage1_dependency_audit` | not a V2.3R G1 blocker; 5G Toolbox license = false; DeepMIMO dataset files = 0 |
| Final estimator-efficiency Monte Carlo against 5L CRLB | pilot-pass | `crlb_5l_monte_carlo` | 30 dB mean RMSE/CRLB ratio = 1.0067; angle RMSE drops 9.928x from 10 to 30 dB |

## Decision

G1 is accepted under the V2.3R gate definition. Standards-aligned CDL/DeepMIMO remains tracked for G3 and external-dependency planning.

Stage 2 / Pack 3 may begin with bounded minimal T-OMP-Net smoke runs.
