# Claim–evidence matrix

| Manuscript claim | Executed evidence | Numerical support | Location |
|---|---|---|---|
| Axis-wise Candan is the strongest non-iterative fixed-support route under the common tensor contract | 1200 identical scenes for grid, quadratic, Candan, Newton, and Cartesian estimators | Gain: Candan 24.26 dB; Cartesian 7.30 dB; Newton 2.28 dB | Fig. 3; Supplement local-family table |
| Projection selection removes the old two-LS overhead | 1200 scenes, one thread, complex128, three timed repetitions; 60 identity scenes | Candan 11.07 ms; projection-selected 11.24 ms; explicit two-residual 18.98 ms; maximum decision discrepancy $5.44\times10^{-15}$ | Section VI-B; Supplement runtime table |
| The improvement covers the complete fractional-bin interval | 1200 scenes with offsets uniform on $[-0.49,0.49]$ | Candan gain 14.45 dB; half-bin rate 0.652 versus 0.520 for grid | Section VI-C; Supplement full-offset table |
| Candan remains effective under controlled component interaction | 48 cells from four separations, three dynamic ranges, and four SNRs | Mean gain 10.46 dB; minimum cell gain 6.29 dB; per-component hit rate 0.515 to 0.689 | Fig. 4; Supplement stress ledger |
| The headline gain is implementation-independent | Separately written MATLAB generator, three-sample update, and joint LS on five seeds | 1200 scenes; 23.36 dB gain, 95% interval [22.67, 24.06] dB | Section VI-C; `candan_independent_summary.csv` |
| Calibration-free projection selection improves the CDL aggregate | Five test seeds for CDL-A/C/D; $\tau_\rho=0$ fixed analytically | Increment 0.141 dB, paired 95% interval [0.097, 0.186]; selected gain 5.280 dB | Fig. 5; Table II |
| The same zero threshold adapts across CDL profiles | 9000 test scenes with no profile calibration | A/C/D selected gains 10.220/4.907/0.712 dB; return rates 99.8/93.9/52.2% | Fig. 5; Table II |
| Projection selection concentrates deployment on beneficial updates | Per-scene gain classification | Beneficial retention 0.929; harmful rejection 0.757; return rate 0.820 | Section VI-E; Supplement protocol audit |
| Physical accuracy accompanies channel-NMSE improvement | 9000-scene route-exact physical replay | Delay RMSE 428.45 to 413.52 ns; quarter-bin joint hit 7.46% to 18.84%; tenth-bin 4.35% to 9.36% | Section VI-E; Supplement physical table |
| Quotient stability is auditable from the received data | Stored $\zeta$, clipping, residuals, design conditions, and matched physical errors | $\zeta$--clipping Spearman A/C/D: -0.525/-0.508/-0.506 | Proposition 2; physical/$\zeta$ artifact |
