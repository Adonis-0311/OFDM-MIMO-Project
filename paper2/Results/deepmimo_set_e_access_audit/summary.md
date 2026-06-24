# DeepMIMO Set E Access Audit

This audit supports TechnicalDesign v2.2 Section 6.2 Set E. It checks whether local DeepMIMO assets are sufficient for channel NMSE and angle-delay cross-scene validation.

- Reference root: `D:\E\OFDM-MIMO_Radar_Estimation\2025刘雨辉毕设\参考`
- Readiness: `partial`
- Dataset files found: `0`
- O1/O1_60 asset hits: `0`
- O1/O1_60 parameter references: `5`
- I3/I3_60 asset hits: `0`
- I3/I3_60 parameter references: `0`

## Audit Table

| Item | Value | Status | Evidence |
|---|---:|---|---|
| DeepMIMO MATLAB package | yes | ok | `D:\E\OFDM-MIMO_Radar_Estimation\2025刘雨辉毕设\参考\DeepMIMO-matlab-master` |
| DeepMIMO 5GNR package | yes | ok | `D:\E\OFDM-MIMO_Radar_Estimation\2025刘雨辉毕设\参考\DeepMIMO-5GNR` |
| DeepMIMO 5GNR dataset folder | yes | ok | `D:\E\OFDM-MIMO_Radar_Estimation\2025刘雨辉毕设\参考\DeepMIMO-5GNR\DeepMIMO_dataset` |
| Legacy generator | yes | ok | `D:\E\OFDM-MIMO_Radar_Estimation\2025刘雨辉毕设\参考\DeepMIMO-matlab-master\DeepMIMO_Dataset_Generator.m` |
| 5GNR generator | yes | ok | `D:\E\OFDM-MIMO_Radar_Estimation\2025刘雨辉毕设\参考\DeepMIMO-5GNR\DeepMIMO_Dataset_Generator.m` |
| Legacy parameters | yes | ok | `D:\E\OFDM-MIMO_Radar_Estimation\2025刘雨辉毕设\参考\DeepMIMO-matlab-master\parameters.m` |
| 5GNR parameters | yes | ok | `D:\E\OFDM-MIMO_Radar_Estimation\2025刘雨辉毕设\参考\DeepMIMO-5GNR\parameters.m` |
| Dataset file count | 0 | missing | `D:\E\OFDM-MIMO_Radar_Estimation\2025刘雨辉毕设\参考\DeepMIMO-5GNR\DeepMIMO_dataset` |
| O1/O1_60 local asset hits | 0 | missing | `` |
| I3/I3_60 local asset hits | 0 | missing | `` |
| O1/O1_60 parameter references | 5 | ok | `D:\E\OFDM-MIMO_Radar_Estimation\2025刘雨辉毕设\参考\DeepMIMO-5GNR\parameters.m; D:\E\OFDM-MIMO_Radar_Estimation\2025刘雨辉毕设\参考\DeepMIMO-5GNR\DeepMIMO_functions\default_parameters.m; D:\E\OFDM-MIMO_Radar_Estimation\2025刘雨辉毕设\参考\DeepMIMO-matlab-master\parameters.m; D:\E\OFDM-MIMO_Radar_Estimation\2025刘雨辉毕设\参考\DeepMIMO-matlab-master\DeepMIMO_functions\parameters\default_parameters.m; D:\E\OFDM-MIMO_Radar_Estimation\2025刘雨辉毕设\参考\DeepMIMO-matlab-master\Examples\Example1_params.m` |
| I3/I3_60 parameter references | 0 | missing | `` |
| MATLAB 5G Toolbox license | no | missing | `license('test', '5G_Toolbox')` |
| nrCDLChannel availability | yes | ok | `D:\E\MATLAB\toolbox\5g\5g\nrCDLChannel.m` |

## Interpretation

Local DeepMIMO code is present, but scenario data/toolbox readiness is incomplete. Next step: download/install the required O1/I3 scenario data and verify MATLAB 5G Toolbox support before claiming Set E performance.

This audit does not validate velocity RMSE, consistent with v2.2: DeepMIMO Set E is for channel NMSE, angle RMSE, delay RMSE, and cross-scene generalization only.
