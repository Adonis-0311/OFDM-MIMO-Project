# Stage 3 A4 SNR-Aware Gate Diagnostic

## Outcome Summary

This diagnostic tests whether replacing a scalar plateau threshold with an SNR- and curve-feature-aware sequential policy can rescue the A4 SNR-axis early-stop claim.

## evaluation_summary

- `research_question`: Can an SNR/curve-feature-aware gate meet the >=25% depth-savings and <=0.5 dB gap contract across SNR={10,20,30} dB at L=32?
- `claim_update`: refuted-under-current-curves.
- `baseline_relation`: Fixed-depth K=8 repeated off-grid refinement remains the quality comparator; scalar threshold and per-curve quality oracle are diagnostic comparators.
- `failure_mode`: No execution failure if complete; any negative result is methodological under this local synthetic contract.
- `mechanism_note`: Even the per-curve quality oracle cannot clear the tested SNR cells, so this A4 contract lacks enough early-stop room under the current curves.
- `next_action`: Do not widen A4 across SNR; keep it restricted to the high-L core-SNR result or redesign the refinement schedule.
- `evidence_level`: Writing-facing A4 boundary diagnostic, not a deployment-ready learned policy.

## Key Metrics

- SNR-aware kNN min SNR mean savings: 21.8750%
- SNR-aware kNN max SNR gap: 0.6558 dB
- SNR-scalar min SNR mean savings: 31.2500%
- SNR-scalar max SNR gap: 0.9986 dB
- Per-curve oracle min SNR mean savings: 21.8750%
- Per-curve oracle max SNR gap: 0.4906 dB
- Selected k: 1
- Selected vote threshold: 0.3500
- Wall-clock elapsed time: 149.43 s

## Policy/SNR Summary

| Policy | SNR (dB) | Mean savings (%) | Min savings (%) | Mean gap (dB) | Max gap (dB) | Sample pass rate |
|---|---:|---:|---:|---:|---:|---:|
| snr_scalar_train | 10.0 | 31.2500 | 25.0000 | 0.4747 | 0.9986 | 0.7500 |
| snr_scalar_train | 20.0 | 31.2500 | 25.0000 | 0.3648 | 0.4821 | 1.0000 |
| snr_scalar_train | 30.0 | 31.2500 | 25.0000 | 0.5869 | 0.6558 | 0.2500 |
| curve_feature_knn_train | 10.0 | 21.8750 | 12.5000 | 0.2026 | 0.3226 | 0.7500 |
| curve_feature_knn_train | 20.0 | 28.1250 | 25.0000 | 0.3177 | 0.4821 | 1.0000 |
| curve_feature_knn_train | 30.0 | 31.2500 | 25.0000 | 0.5869 | 0.6558 | 0.2500 |
| per_curve_quality_oracle | 10.0 | 28.1250 | 25.0000 | 0.3114 | 0.3454 | 1.0000 |
| per_curve_quality_oracle | 20.0 | 31.2500 | 25.0000 | 0.3648 | 0.4821 | 1.0000 |
| per_curve_quality_oracle | 30.0 | 21.8750 | 12.5000 | 0.2983 | 0.4906 | 0.7500 |
