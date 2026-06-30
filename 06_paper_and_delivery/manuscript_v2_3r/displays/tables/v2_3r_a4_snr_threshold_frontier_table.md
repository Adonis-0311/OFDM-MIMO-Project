# v2.3R A4 SNR Threshold Frontier Table

| Policy | SNR (dB) | Mean savings (%) | Min savings (%) | Mean gap (dB) | Max gap (dB) | Pass rate | Paper use |
|---|---:|---:|---:|---:|---:|---:|---|
| standard_train | 10.0 | 31.2500 | 31.2500 | 0.6468 | 0.6691 | 0.0000 | train-selected scalar threshold diagnostic |
| standard_train | 20.0 | 15.6250 | 12.5000 | 0.2147 | 0.2758 | 0.0000 | train-selected scalar threshold diagnostic |
| standard_train | 30.0 | 25.0000 | 25.0000 | 0.2941 | 0.3442 | 1.0000 | train-selected scalar threshold diagnostic |
| guarded_train | 10.0 | 9.3750 | 6.2500 | 0.0777 | 0.1141 | 0.0000 | conservative scalar threshold diagnostic |
| guarded_train | 20.0 | 12.5000 | 12.5000 | 0.1291 | 0.1535 | 0.0000 | conservative scalar threshold diagnostic |
| guarded_train | 30.0 | 18.7500 | 12.5000 | 0.2245 | 0.3442 | 0.5000 | conservative scalar threshold diagnostic |
| test_oracle_frontier | 10.0 | 12.5000 | 0.0000 | 0.1781 | 0.3562 | 0.5000 | diagnostic upper bound, not deployable |
| test_oracle_frontier | 20.0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | diagnostic upper bound, not deployable |
| test_oracle_frontier | 30.0 | 28.1250 | 25.0000 | 0.3998 | 0.4554 | 1.0000 | diagnostic upper bound, not deployable |
