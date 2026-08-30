# Stage 3 A5 HIR-JL Phase-Noise Pre-Smoke

- Config hash: `stage3-a5-hirjl-presmoke-20260624`

## Metrics

- `tensor_shape`: `128x16x32`
- `snr_db`: 20
- `seed`: `20260624`
- `n_targets`: `8`
- `n_train`: `4`
- `n_test`: `5`
- `sigma_phi_degrees`: `[0.0, 0.5, 1.0, 2.0, 3.0]`
- `candidate_alphas`: `[0.0, 0.19999999999999998, 0.39999999999999997, 0.6, 0.7999999999999999, 0.9999999999999999, 1.2]`
- `clean_trained_alpha`: 0.8
- `clean_train_nmse_db`: -13.3129
- `degradation_by_sigma_db`: `{0.0: 0.0, 0.5: -1.9049101585011385e-06, 1.0: 3.7041473124332924e-06, 2.0: 1.1683922428673554e-05, 3.0: 0.000171920386792479}`
- `oracle_recovery_by_sigma_db`: `{0.0: 0.0, 0.5: 0.0, 1.0: 0.0, 2.0: 0.0, 3.0: 0.0}`
- `oracle_alpha_by_sigma`: `{0.0: 0.7999999999999999, 0.5: 0.7999999999999999, 1.0: 0.7999999999999999, 2.0: 0.7999999999999999, 3.0: 0.7999999999999999}`
- `elapsed_seconds`: 27.8399

## Notes

- A5 pre-smoke isolates phase-noise stress before full HIR-JL robust training.
- Clean-trained alpha is fitted only at sigma_phi=0 and reused under all phase-noise levels.
- Oracle-retuned alpha per sigma is reported as a diagnostic; it is not a deployable robust-training result.

## Artifacts

- `05_results\stage3_a5_hirjl_presmoke\stage3_a5_hirjl_presmoke.csv`
- `05_results\stage3_a5_hirjl_presmoke\stage3_a5_hirjl_presmoke_samples.csv`
- `05_results\stage3_a5_hirjl_presmoke\run_manifest.json`
