# CDL Profile Generalization Smoke Experiment

This lightweight experiment supports TechnicalDesign v2.2 Section 6.2 Set B-D.
It uses a compact CDL-like generator for CDL-A/CDL-C/CDL-D communication-side channel NMSE checks. It is not a full 3GPP TR 38.901 implementation.

- Seed: `20260623`
- Channel size: `Nr=8, Nt=4, K=128`
- Trials per profile/SNR: `32`
- SNR grid: `[0 5 10 15 20] dB`
- Delay-sparse kept taps: `20`

## Result Table

| Profile | SNR | LS NMSE | Delay-sparse NMSE | Gain | Runtime (s) |
|---|---:|---:|---:|---:|---:|
| CDL-A | 0 | 0.009 | -7.148 | 7.157 | 0.00046 |
| CDL-A | 5 | -5.006 | -11.864 | 6.858 | 0.00011 |
| CDL-A | 10 | -10.000 | -15.771 | 5.771 | 0.00012 |
| CDL-A | 15 | -14.995 | -17.752 | 2.757 | 0.00012 |
| CDL-A | 20 | -19.992 | -18.714 | -1.278 | 0.00012 |
| CDL-C | 0 | 0.008 | -6.924 | 6.932 | 0.00012 |
| CDL-C | 5 | -4.987 | -10.684 | 5.698 | 0.00012 |
| CDL-C | 10 | -10.007 | -13.177 | 3.170 | 0.00012 |
| CDL-C | 15 | -14.985 | -13.955 | -1.030 | 0.00011 |
| CDL-C | 20 | -20.014 | -15.081 | -4.933 | 0.00011 |
| CDL-D | 0 | -0.009 | -7.076 | 7.067 | 0.00009 |
| CDL-D | 5 | -5.027 | -12.208 | 7.181 | 0.00010 |
| CDL-D | 10 | -9.984 | -17.091 | 7.108 | 0.00011 |
| CDL-D | 15 | -15.003 | -22.035 | 7.032 | 0.00014 |
| CDL-D | 20 | -19.975 | -26.589 | 6.614 | 0.00014 |

## Interpretation Boundary

This smoke run validates the evaluation scaffold and profile-specific reporting. Delay-sparse denoising is expected to help in low-to-mid SNR, while a truncation bias floor can appear for wider NLOS profiles at high SNR. The final paper experiment should replace this generator with a standards-aligned 3GPP CDL or MATLAB 5G Toolbox pipeline and add trained T-OMP-Net inference.
