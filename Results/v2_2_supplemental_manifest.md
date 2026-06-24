# v2.2 Supplemental Experiment Manifest

This manifest summarizes the lightweight experiments added against `ISAC_DeepUnfolding_TechnicalDesign_v2.2.md`.
The runs are desktop reproducibility checks and early paper-upgrade evidence, not the final full-scale T-OMP-Net training campaign.

## Reproduction Command

```matlab
run('eval/run_all_v2_2_supplemental_experiments.m')
```

## Run Table

| Experiment | Outline target | Status | Runtime (s) | Summary |
|---|---|---:|---:|---|
| Oversampling/off-grid ablation | Section 6.5.13(a) | ok | 38.68 | `Results/oversampling_offgrid_ablation/summary.md` |
| Kruskal identifiability ablation | Section 6.5.13(b,c) | ok | 4.31 | `Results/kruskal_identifiability_ablation/summary.md` |
| Off-grid mismatch lemma validation | Section 5.1.1 / Phase 3 | ok | 4.84 | `Results/offgrid_mismatch_lemma/summary.md` |
| CDL profile generalization smoke | Section 6.2 Set B-D | ok | 4.10 | `Results/cdl_profile_generalization_smoke/summary.md` |
| CRLB delay asymptotic smoke | Section 5.2 / Section 6.5.5 | ok | 7.23 | `Results/crlb_delay_asymptotic_smoke/summary.md` |

## Key Evidence

- Oversampling/off-grid: at `rho=2`, bounded off-grid improves mean NMSE from `-8.54 dB` to `-55.95 dB` across the three scans.
- Kruskal/target-count: as `L` rises from `2` to `32`, NMSE changes from `-57.36 dB` to `-40.60 dB`, and runtime from `0.0066 s` to `0.1158 s`.
- Off-grid mismatch lemma: median fitted/reference beta ratio is `0.4978`; median corrected/grid beta ratio is `0.01003`.
- CDL profile smoke: at `10 dB`, delay-sparse denoising improves NMSE by a mean `5.35 dB` across CDL-A/C/D-like profiles.
- CRLB delay smoke: for `SNR >= 20 dB`, mean RMSE/sqrt(CRLB) ratio is `1.023`.

## Remaining Gaps

- Full-size Tensor-OMP/T-OMP-Net training and inference pipeline is still pending.
- Standards-aligned CDL-A/C/D and DeepMIMO Set E cross-scene validation are still pending.
- Full 5L joint ISAC CRLB is still pending; the current CRLB result is a single-delay smoke validation.
- FLOPs/latency should be measured on the final implementation, not only the lightweight smoke scripts.
- GitHub remote upload still requires an authenticated GitHub CLI session or a provided remote URL.
