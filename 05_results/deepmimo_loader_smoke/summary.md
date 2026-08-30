# DeepMIMO Loader Smoke

- Status: `ok`
- Dataset root: `D:\E\OFDM-MIMO_Radar_Estimation\90_archive\2025_thesis_materials\参考\DeepMIMO-5GNR\DeepMIMO_dataset`

## Package Status

- `DeepMIMOv3`: `True`
- `DeepMIMO`: `False`
- `deepmimo`: `True`
- `scipy`: `True`
- `h5py`: `True`

## MAT Entry Points

| Entry | Status | Reader | Bytes | Path |
|---|---|---|---:|---|
| O1_60 delay ray file | ok | scipy | 35851224 | `D:\E\OFDM-MIMO_Radar_Estimation\90_archive\2025_thesis_materials\参考\DeepMIMO-5GNR\DeepMIMO_dataset\o1_60\delay_t003_tx000_r000.mat` |
| O1_60 power ray file | ok | scipy | 35851224 | `D:\E\OFDM-MIMO_Radar_Estimation\90_archive\2025_thesis_materials\参考\DeepMIMO-5GNR\DeepMIMO_dataset\o1_60\power_t003_tx000_r000.mat` |
| O1_60 phase ray file | ok | scipy | 35851224 | `D:\E\OFDM-MIMO_Radar_Estimation\90_archive\2025_thesis_materials\参考\DeepMIMO-5GNR\DeepMIMO_dataset\o1_60\phase_t003_tx000_r000.mat` |
| I3_60 CIR file | ok | scipy | 18412953 | `D:\E\OFDM-MIMO_Radar_Estimation\90_archive\2025_thesis_materials\参考\DeepMIMO-5GNR\DeepMIMO_dataset\I3_60_v1\I3_60.1.CIR.mat` |

## Interpretation

The local O1_60 and I3_60 MAT entry points were read successfully with SciPy. Later E2/E3 should wrap these ray/CIR entry points into channel tensors aligned with the T-OMP-Net interface.
