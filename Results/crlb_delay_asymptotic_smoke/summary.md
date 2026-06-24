# CRLB Delay Asymptotic Smoke Experiment

This lightweight experiment supports TechnicalDesign v2.2 Section 5.2 and Section 6.5.5.
It estimates one path delay with unknown complex gain and compares ML/NLS RMSE against the nuisance-aware CRLB.

- Seed: `20260623`
- Subcarriers: `128`
- Bandwidth: `300 MHz`
- True delay: `37 ns`
- Trials per SNR: `96`
- SNR grid: `[0 5 10 15 20 25 30] dB`

Mean RMSE/sqrt(CRLB) ratio for SNR >= 20 dB: `1.023`.

## Result Table

| SNR | RMSE (ns) | sqrt(CRLB) (ns) | Ratio | Bias (ns) | Runtime (s) |
|---:|---:|---:|---:|---:|---:|
| 0 | 0.11727 | 0.11486 | 1.021 | -0.00923 | 0.00834 |
| 5 | 0.06349 | 0.06459 | 0.983 | 0.00773 | 0.00819 |
| 10 | 0.03658 | 0.03632 | 1.007 | 0.00298 | 0.00811 |
| 15 | 0.02083 | 0.02043 | 1.020 | 0.00036 | 0.00829 |
| 20 | 0.01292 | 0.01149 | 1.125 | -0.00009 | 0.00844 |
| 25 | 0.00577 | 0.00646 | 0.894 | -0.00084 | 0.00876 |
| 30 | 0.00381 | 0.00363 | 1.050 | -0.00062 | 0.00842 |

## Interpretation Boundary

This is a single-delay smoke validation, not the final 5L joint range-velocity-angle CRLB. It validates the expected high-SNR tightening behavior and the plotting/reporting scaffold for the final CRLB experiment.
