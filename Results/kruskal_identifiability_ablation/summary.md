# Kruskal Identifiability Ablation

This lightweight experiment supports TechnicalDesign v2.2 Section 6.5.13(b,c). It uses on-grid multi-target tensors and a Tensor-OMP style greedy solver to measure degradation as target count L grows.
Because this smoke run is on-grid and high-SNR, P_d is expected to remain strong; the more useful early indicators are NMSE, exact-support rate, and runtime growth.

- Seed: `20260623`
- Trials per condition: `6`
- SNR: `20 dB`
- Tensor size: `32 x 16 x 16`
- Oversampling ratio: `2`
- Local Kruskal bound: `floor((32 + 16 + 16 - 2) / 2) = 31`
- Paper-scale Kruskal bound from v2.2: `floor((128 + 16 + 32 - 2) / 2) = 87`

The local bound is lower than the paper-scale bound because this smoke run uses a compact tensor for fast desktop reproducibility.

## Result Table

| L | L/Lmax | P_d | exact support rate | NMSE (dB) | residual energy (dB) | runtime (s) |
|---:|---:|---:|---:|---:|---:|---:|
| 2 | 0.065 | 0.917 | 0.833 | -57.362 | -20.049 | 0.0065 |
| 4 | 0.129 | 0.917 | 0.667 | -53.027 | -20.032 | 0.0057 |
| 8 | 0.258 | 0.979 | 0.833 | -50.900 | -20.022 | 0.0122 |
| 16 | 0.516 | 0.938 | 0.167 | -47.515 | -20.058 | 0.0358 |
| 24 | 0.774 | 0.972 | 0.667 | -45.468 | -20.071 | 0.0635 |
| 32 | 1.032 | 0.927 | 0.167 | -40.598 | -19.815 | 0.1141 |
