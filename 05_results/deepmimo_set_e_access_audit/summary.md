# DeepMIMO Set E Access Audit

This audit supports v2.3R Sensors Phase-Next E0. It checks whether local DeepMIMO assets are sufficient to start the open-source Python validation route.

- Reference root: `D:\E\OFDM-MIMO_Radar_Estimation\90_archive\2025_thesis_materials\参考`
- Readiness: `ready_open_source`
- Dataset files found: `4188`
- O1/O1_60 asset hits: `4161`
- I3/I3_60 asset hits: `27`
- DeepMIMO Python package importable: `True`
- Sionna Python package importable: `True`
- SciPy MAT reader importable: `True`
- h5py MAT/HDF5 reader importable: `True`

## Audit Table

| Item | Value | Status | Evidence |
|---|---:|---|---|
| DeepMIMO MATLAB package | True | ok | `D:\E\OFDM-MIMO_Radar_Estimation\90_archive\2025_thesis_materials\参考\DeepMIMO-matlab-master` |
| DeepMIMO 5GNR package | True | ok | `D:\E\OFDM-MIMO_Radar_Estimation\90_archive\2025_thesis_materials\参考\DeepMIMO-5GNR` |
| DeepMIMO 5GNR dataset folder | True | ok | `D:\E\OFDM-MIMO_Radar_Estimation\90_archive\2025_thesis_materials\参考\DeepMIMO-5GNR\DeepMIMO_dataset` |
| O1_60 dataset folder | True | ok | `D:\E\OFDM-MIMO_Radar_Estimation\90_archive\2025_thesis_materials\参考\DeepMIMO-5GNR\DeepMIMO_dataset\o1_60` |
| I3_60 dataset folder | True | ok | `D:\E\OFDM-MIMO_Radar_Estimation\90_archive\2025_thesis_materials\参考\DeepMIMO-5GNR\DeepMIMO_dataset\I3_60_v1` |
| Dataset file count | 4188 | ok | `D:\E\OFDM-MIMO_Radar_Estimation\90_archive\2025_thesis_materials\参考\DeepMIMO-5GNR\DeepMIMO_dataset` |
| O1/O1_60 local asset hits | 4161 | ok | `D:\E\OFDM-MIMO_Radar_Estimation\90_archive\2025_thesis_materials\参考\DeepMIMO-5GNR\DeepMIMO_dataset\o1_60\aoa_az_t003_tx000_r000.mat; D:\E\OFDM-MIMO_Radar_Estimation\90_archive\2025_thesis_materials\参考\DeepMIMO-5GNR\DeepMIMO_dataset\o1_60\aoa_az_t003_tx000_r001.mat; D:\E\OFDM-MIMO_Radar_Estimation\90_archive\2025_thesis_materials\参考\DeepMIMO-5GNR\DeepMIMO_dataset\o1_60\aoa_az_t003_tx000_r002.mat; D:\E\OFDM-MIMO_Radar_Estimation\90_archive\2025_thesis_materials\参考\DeepMIMO-5GNR\DeepMIMO_dataset\o1_60\aoa_az_t003_tx000_r003.mat` |
| I3/I3_60 local asset hits | 27 | ok | `D:\E\OFDM-MIMO_Radar_Estimation\90_archive\2025_thesis_materials\参考\DeepMIMO-5GNR\DeepMIMO_dataset\I3_60_v1\I3_60.1.CIR.BSBS.mat; D:\E\OFDM-MIMO_Radar_Estimation\90_archive\2025_thesis_materials\参考\DeepMIMO-5GNR\DeepMIMO_dataset\I3_60_v1\I3_60.1.CIR.mat; D:\E\OFDM-MIMO_Radar_Estimation\90_archive\2025_thesis_materials\参考\DeepMIMO-5GNR\DeepMIMO_dataset\I3_60_v1\I3_60.1.DoA.BSBS.mat; D:\E\OFDM-MIMO_Radar_Estimation\90_archive\2025_thesis_materials\参考\DeepMIMO-5GNR\DeepMIMO_dataset\I3_60_v1\I3_60.1.DoA.mat` |
| DeepMIMO Python package | True | ok | `DeepMIMOv3 or DeepMIMO import` |
| Sionna Python package | True | ok | `sionna import` |
| SciPy MAT reader | True | ok | `scipy import` |
| h5py MAT/HDF5 reader | True | ok | `h5py import` |
| MATLAB 5G Toolbox dependency | retired | ok | `Sensors rev.1 open-source route uses Sionna/DeepMIMO/QuaDRiGa` |

## Interpretation

O1_60 and I3_60 local assets are present under the DeepMIMO 5GNR dataset folder, so the former data-access blocker is cleared for the Sensors open-source route.

5G Toolbox is no longer treated as a dependency for this study. The Python package gate is installed for the current interpreter; the next E0 checks can run the DeepMIMO loader smoke and a Sionna CDL smoke.

This audit does not validate final Set E performance; it only verifies that the local asset layer is ready for E2/E3 loader implementation.
