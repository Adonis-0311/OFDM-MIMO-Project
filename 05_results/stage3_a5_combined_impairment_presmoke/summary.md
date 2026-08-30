# Stage 3 A5 Combined-Impairment Pre-Smoke

- Config hash: `stage3-a5-combined-impairment-presmoke-20260624`

## Metrics

- `tensor_shape`: `128x16x32`
- `snr_db`: 20
- `seed`: `20260624`
- `n_targets`: `8`
- `n_train`: `4`
- `n_test`: `5`
- `profiles`: `[{'name': 'clean', 'sigma_phi_degrees': 0.0, 'iq_gain': 1.0, 'iq_phase_degrees': 0.0, 'coupling_rho': 0.0, 'coupling_phi0_degrees': 0.0}, {'name': 'phase_only_2deg', 'sigma_phi_degrees': 2.0, 'iq_gain': 1.0, 'iq_phase_degrees': 0.0, 'coupling_rho': 0.0, 'coupling_phi0_degrees': 0.0}, {'name': 'iq_coupling_medium', 'sigma_phi_degrees': 0.0, 'iq_gain': 1.05, 'iq_phase_degrees': 3.0, 'coupling_rho': 0.2, 'coupling_phi0_degrees': 5.0}, {'name': 'combined_v23r', 'sigma_phi_degrees': 2.0, 'iq_gain': 1.05, 'iq_phase_degrees': 3.0, 'coupling_rho': 0.2, 'coupling_phi0_degrees': 5.0}, {'name': 'combined_high', 'sigma_phi_degrees': 3.0, 'iq_gain': 1.1, 'iq_phase_degrees': 5.0, 'coupling_rho': 0.3, 'coupling_phi0_degrees': 10.0}]`
- `candidate_alphas`: `[0.0, 0.19999999999999998, 0.39999999999999997, 0.6, 0.7999999999999999, 0.9999999999999999, 1.2]`
- `clean_trained_alpha`: 0.8
- `clean_train_nmse_db`: -13.3129
- `degradation_by_profile_db`: `{'clean': 0.0, 'phase_only_2deg': 3.619806600596576e-05, 'iq_coupling_medium': 4.443735345160793, 'combined_v23r': 4.439537092767866, 'combined_high': 6.60364902305442}`
- `oracle_recovery_by_profile_db`: `{'clean': 0.0, 'phase_only_2deg': 0.0, 'iq_coupling_medium': 0.0, 'combined_v23r': 0.0, 'combined_high': 0.0}`
- `oracle_alpha_by_profile`: `{'clean': 0.7999999999999999, 'phase_only_2deg': 0.7999999999999999, 'iq_coupling_medium': 0.7999999999999999, 'combined_v23r': 0.7999999999999999, 'combined_high': 0.7999999999999999}`
- `elapsed_seconds`: 28.1613

## Notes

- Combined-impairment pre-smoke checks whether A5 remains valuable after phase-noise-only stress was weak.
- Profiles apply phase noise, IQ imbalance, and physical mutual coupling directly to the measured tensor.
- Oracle-retuned alpha per profile is diagnostic only; it is not a robust-training result.

## Artifacts

- `05_results\stage3_a5_combined_impairment_presmoke\stage3_a5_combined_impairment_presmoke.csv`
- `05_results\stage3_a5_combined_impairment_presmoke\stage3_a5_combined_impairment_presmoke_samples.csv`
- `05_results\stage3_a5_combined_impairment_presmoke\run_manifest.json`
