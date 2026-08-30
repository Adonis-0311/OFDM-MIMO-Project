# Stage 3 Synthetic Cross-Scene Generalization

- Config hash: `stage3-synthetic-cross-scene-generalization-20260624`

## Metrics

- `tensor_shape`: `128x16x32`
- `seed`: `20260624`
- `source_scene`: `source_l8_snr20_offset035`
- `source_train_count`: `3`
- `candidate_alphas`: `[0.0, 0.19999999999999998, 0.39999999999999997, 0.6, 0.7999999999999999, 0.9999999999999999, 1.2]`
- `source_alpha`: 0.8
- `source_train_nmse_db`: -12.0909
- `min_target_gain_vs_grid_db`: 5.85036
- `max_target_gap_vs_oracle_db`: 0.4077
- `claim_update`: `local-synthetic-pass`
- `elapsed_seconds`: 28.3091

## Notes

- Local synthetic cross-scene fallback only; not DeepMIMO or ray-traced channel evidence.
- Source alpha is fitted once on the source scene and reused unchanged on all target scenes.
- Target-oracle alpha is retuned on target train samples and reported only as a diagnostic upper bound.

## Artifacts

- `05_results\stage3_synthetic_cross_scene_generalization\stage3_synthetic_cross_scene_generalization.csv`
- `05_results\stage3_synthetic_cross_scene_generalization\stage3_synthetic_cross_scene_generalization_samples.csv`
- `05_results\stage3_synthetic_cross_scene_generalization\run_manifest.json`
