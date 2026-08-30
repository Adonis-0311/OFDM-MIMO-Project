# IEEE TSP seventh-round revision execution

The seventh-round recommendations were treated as review advice; all numerical claims below come from executed repository artifacts.

## Main upgrades

- Replaced the profile-calibrated residual gate with a calibration-free projection rule, $\tau_\rho=0$.
- Implemented fitted-energy selection using selected FFT-bin energies for the grid route and the refined QR factor for Candan. The decision matches explicit residual comparison within $5.44\times10^{-15}$.
- Reduced complete selection runtime from 18.98 ms to 11.24 ms on the unified 1200-scene audit, a 40.75% reduction and only 1.57% above Candan alone.
- Replaced the old Cartesian stress ledger with a pure-Candan 48-cell audit. All 48 cells are positive; mean gain is 10.459 dB [9.908, 11.011] and the minimum cell is 6.293 dB [4.440, 8.146].
- Added a 9000-scene physical replay: delay RMSE 428.45 to 413.52 ns, joint quarter-bin hit 7.46% to 18.84%, and joint tenth-bin hit 4.35% to 9.36%.
- Closed the quotient-stability loop: $\zeta$ is now reported as an observable clipping/stability diagnostic, with A/C/D clipping correlations of -0.525/-0.508/-0.506.
- Strengthened theory with exact separable triplet factorization, the finite-$N$ Candan map, an explicit Dirichlet/dynamic-range/SNR Gaussian quotient bound, and steering-Jacobian propagation to joint LS.
- Added the closest verified 2024--2026 IEEE TSP references, including Kronecker off-grid Bayesian estimation and off-grid Tucker channel estimation.
- Rebuilt all active manuscript figures from MATLAB sources using the IEEE-style color and export contract.

## Protocol decisions

The A/C-only calibrated audit produced no resolved zero-shot D improvement: 0.0020 dB with 95% interval [-0.0027, 0.0067]. It is therefore not used as a paper claim. A leakage-free two-fold predictive audit was also executed but did not improve aggregate performance. The final paper uses the stronger analytic zero-threshold projection rule and reports its paired seed-level increments directly.

## Registered artifacts

- `05_results/tsp_candan_gate_protocol_seventh_round`
- `05_results/tsp_projection_gate_runtime_seventh_round`
- `05_results/tsp_crossfit_predictive_gate_seventh_round`
- `05_results/tsp_candan_stress_zeta_audit_paper`
- `05_results/tsp_candan_physical_zeta_audit_paper`
- `05_results/tsp_candan_zeta_closed_loop_paper`

Every result directory contains the command, configuration, environment, seed ledger, manifest, and CSV/JSON evidence required to reproduce its claims.
