# E12 Matched Accuracy and Runtime

| Method | NMSE (dB; seed-mean 95% CI) | Median ms | Within half bin | Availability |
|---|---:|---:|---:|---|
| Grid FFT top-k + LS | -5.430 [-5.527, -5.333] | 20.20 | 0.719 | matched accuracy |
| Deterministic local refinement | -12.735 [-12.814, -12.655] | 434.79 | 0.796 | matched accuracy |
| Learned scalar refinement | -11.215 [-11.340, -11.089] | 433.48 | 0.791 | matched accuracy |
| NOMP-inspired refinement | -53.390 [-53.472, -53.308] | 3513.99 | 0.999 | matched accuracy |
| Complex PARAFAC-ALS | -16.855 [-17.900, -15.810] | 32.57 | 0.524 | matched accuracy |
| Separable FB-ESPRIT | -- | see E4 timing table | -- | timing-only: no cross-axis pairing |
