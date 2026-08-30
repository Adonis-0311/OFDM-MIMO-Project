# DeepMIMO Source-Alpha Multi-Seed Campaign

The campaign varies only user sampling and AWGN seed. Dataset construction, SNR/L cells, grid baseline, Stage-2 source alpha, refinement search, and metric definitions remain fixed.

| Dataset | Class | Seeds x users | Grid NMSE (dB) | Source-alpha NMSE (dB) | Gain vs grid, mean [95% CI] (dB) | Min cell gain (dB) | Min support recall | Oracle gap (dB) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| DeepMIMO O1_60 | weak | 5 x 100 | -4.6225 | -5.9459 | 1.3235 [1.2538, 1.3931] | 0.8554 | 0.8250 | 0.2120 |
| DeepMIMO I3_60 | partial | 5 x 100 | -13.9809 | -20.6823 | 6.7014 [6.4660, 6.9368] | -0.2412 | 0.3063 | 0.9973 |

## Claim Boundary

These results strengthen the reproducibility and sampling-robustness of the scalar source-alpha transfer proxy. They do not establish full trained G2/T-OMP-Net performance or physical angle/delay RMSE on DeepMIMO.
