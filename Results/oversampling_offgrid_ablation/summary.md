# Oversampling and Off-Grid Ablation

This lightweight experiment supports TechnicalDesign v2.2 Section 6.5.13. It isolates one rank-1 angle-delay-Doppler component and compares coarse grid matching with bounded local off-grid refinement.

- Seed: `20260623`
- Trials per condition: `24`
- SNR: `20 dB`
- Tensor size: `32 x 16 x 16`

The run is a smoke/ablation experiment, not the final learned T-OMP-Net result.

## Result Table

| scan | rho | atoms | theta grid | theta offgrid | tau grid | tau offgrid | doppler grid | doppler offgrid | NMSE grid | NMSE offgrid |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| theta | 1 | 32768 | 1.021 | 0.002901 | 0.8973 | 0.003703 | 10.77 | 0.02667 | -5.648 | -53.76 |
| theta | 2 | 65536 | 0.5961 | 0.002574 | 0.9378 | 0.002702 | 10.08 | 0.03143 | -7.773 | -56.05 |
| theta | 4 | 131072 | 0.2981 | 0.001756 | 0.9977 | 0.002916 | 9.341 | 0.03357 | -8.856 | -57.2 |
| theta | 8 | 262144 | 0.1305 | 0.002022 | 0.9412 | 0.002672 | 9.803 | 0.03012 | -9.545 | -56.64 |
| tau | 1 | 32768 | 0.6085 | 0.001962 | 1.727 | 0.005222 | 10.34 | 0.02353 | -5.276 | -53.85 |
| tau | 2 | 65536 | 0.5366 | 0.00167 | 0.7801 | 0.002689 | 9.001 | 0.0237 | -8.824 | -56.81 |
| tau | 4 | 131072 | 0.5306 | 0.002442 | 0.498 | 0.002895 | 8.515 | 0.02982 | -10.29 | -55.17 |
| tau | 8 | 262144 | 0.6032 | 0.002412 | 0.2518 | 0.002714 | 9.109 | 0.01951 | -9.948 | -55.64 |
| nu | 1 | 32768 | 0.564 | 0.001802 | 1.005 | 0.003602 | 15.66 | 0.05073 | -6.978 | -53.55 |
| nu | 2 | 65536 | 0.4705 | 0.002842 | 0.9508 | 0.003085 | 8.899 | 0.0304 | -9.02 | -54.98 |
| nu | 4 | 131072 | 0.5644 | 0.001911 | 0.8731 | 0.003028 | 4.539 | 0.02691 | -9.768 | -55.86 |
| nu | 8 | 262144 | 0.584 | 0.002213 | 0.9 | 0.003441 | 2.51 | 0.03136 | -9.585 | -54.67 |
