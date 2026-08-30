# v2.3R A4 SNR-Aware Gate Diagnostic Table

| Policy | SNR (dB) | Mean savings (%) | Min savings (%) | Mean gap (dB) | Max gap (dB) | Sample pass rate | Paper use |
|---|---:|---:|---:|---:|---:|---:|---|
| snr_scalar_train | 10.0 | 31.2500 | 25.0000 | 0.4747 | 0.9986 | 0.7500 | SNR-indexed scalar threshold comparator |
| snr_scalar_train | 20.0 | 31.2500 | 25.0000 | 0.3648 | 0.4821 | 1.0000 | SNR-indexed scalar threshold comparator |
| snr_scalar_train | 30.0 | 31.2500 | 25.0000 | 0.5869 | 0.6558 | 0.2500 | SNR-indexed scalar threshold comparator |
| curve_feature_knn_train | 10.0 | 21.8750 | 12.5000 | 0.2026 | 0.3226 | 0.7500 | lightweight learned gate diagnostic |
| curve_feature_knn_train | 20.0 | 28.1250 | 25.0000 | 0.3177 | 0.4821 | 1.0000 | lightweight learned gate diagnostic |
| curve_feature_knn_train | 30.0 | 31.2500 | 25.0000 | 0.5869 | 0.6558 | 0.2500 | lightweight learned gate diagnostic |
| per_curve_quality_oracle | 10.0 | 28.1250 | 25.0000 | 0.3114 | 0.3454 | 1.0000 | diagnostic upper bound, not deployable |
| per_curve_quality_oracle | 20.0 | 31.2500 | 25.0000 | 0.3648 | 0.4821 | 1.0000 | diagnostic upper bound, not deployable |
| per_curve_quality_oracle | 30.0 | 21.8750 | 12.5000 | 0.2983 | 0.4906 | 0.7500 | diagnostic upper bound, not deployable |
