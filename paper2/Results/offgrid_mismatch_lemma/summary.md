# Off-Grid Mismatch Lemma Validation

This lightweight experiment supports TechnicalDesign v2.2 Section 5.1.1 and Phase 3.
It measures ULA steering-vector mismatch for small angular offsets and fits `epsilon_grid ~= beta * delta_theta^2`.

- Seed: `20260623`
- Virtual apertures: `[16 32 64 128]`
- Angle centers (deg): `[-45 -20 0 20 45]`
- Grid step: `0.5 deg`
- Simulated learned residual scale after correction: `0.1 x delta_theta`

Median fitted/reference beta ratio: `0.4978`.
Median corrected/grid beta ratio: `0.01003`, close to the expected squared residual scale `0.01`.

The reference beta uses the Lemma 1 scale `(pi^2/12) * Nv^2 * cos(theta)^2`. Because the measured mismatch is `1 - |a(theta_g)^H a(theta*)|`, the coefficient is used as a scaling reference rather than an exact equality.

## Summary Table

| Nv | theta | beta grid | beta corrected | beta ref | grid/ref | corrected/grid |
|---:|---:|---:|---:|---:|---:|---:|
| 16 | -45 | 52.42 | 0.5243 | 105.3 | 0.4979 | 0.01 |
| 16 | -20 | 92.56 | 0.926 | 185.9 | 0.4978 | 0.01 |
| 16 | 0 | 104.8 | 1.049 | 210.6 | 0.4978 | 0.01 |
| 16 | 20 | 92.56 | 0.926 | 185.9 | 0.4978 | 0.01 |
| 16 | 45 | 52.42 | 0.5243 | 105.3 | 0.4979 | 0.01 |
| 32 | -45 | 210.2 | 2.103 | 421.1 | 0.4991 | 0.01001 |
| 32 | -20 | 370.9 | 3.715 | 743.7 | 0.4987 | 0.01002 |
| 32 | 0 | 419.9 | 4.207 | 842.2 | 0.4986 | 0.01002 |
| 32 | 20 | 370.9 | 3.715 | 743.7 | 0.4987 | 0.01002 |
| 32 | 45 | 210.2 | 2.103 | 421.1 | 0.4991 | 0.01001 |
| 64 | -45 | 839 | 8.42 | 1684 | 0.4981 | 0.01004 |
| 64 | -20 | 1478 | 14.87 | 2975 | 0.4967 | 0.01006 |
| 64 | 0 | 1672 | 16.84 | 3369 | 0.4963 | 0.01007 |
| 64 | 20 | 1478 | 14.87 | 2975 | 0.4967 | 0.01006 |
| 64 | 45 | 839 | 8.42 | 1684 | 0.4981 | 0.01004 |
| 128 | -45 | 3320 | 33.68 | 6738 | 0.4928 | 0.01014 |
| 128 | -20 | 5800 | 59.48 | 1.19e+04 | 0.4874 | 0.01025 |
| 128 | 0 | 6546 | 67.35 | 1.348e+04 | 0.4858 | 0.01029 |
| 128 | 20 | 5800 | 59.48 | 1.19e+04 | 0.4874 | 0.01025 |
| 128 | 45 | 3320 | 33.68 | 6738 | 0.4928 | 0.01014 |
