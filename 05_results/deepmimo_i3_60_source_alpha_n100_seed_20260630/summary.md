# DeepMIMO I3_60 Cross-Domain Dev Run

- Claim update: `partial-source-alpha-transfer`
- Transfer proxy classification: `partial`
- BS indices: `1,2`
- Source alpha: `0.64192` from `05_results\stage2_torch_locked_scale_g2_seed_sweep\stage2_torch_locked_scale_g2_seed_sweep_seeds.csv`
- Users: `100`
- SNRs: `0.0,10.0,20.0,30.0` dB
- L values: `4,8,16`
- Aggregated rows: `12`
- Sample rows: `1200`
- Minimum mean support recall: `0.30625`
- Mean grid channel NMSE across cells: `-14.0941` dB
- Mean source-alpha channel NMSE across cells: `-20.7367` dB
- Mean source-alpha gain vs grid: `6.64263` dB
- Mean bounded refinement channel NMSE across cells: `-20.3822` dB
- Mean bounded gain vs grid: `6.28812` dB
- Mean source-alpha gap vs oracle-alpha: `0.980647` dB
- Mean dominant energy recall: `0.971693`
- Mean path count: `14.120`
- RX x/y span: `9.117` m / `8.233` m
- Elapsed seconds: `10.53`

## Interpretation

The source-trained G2 alpha improves mean I3_60 NMSE, but at least one cell has weak dominant-bin recall.

This is a raw-loader and scalar source-alpha transfer validation, not final Sensors E3 evidence. It proves the I3_60 local CIR files can be converted into reproducible OFDM channel tensors and scored under a direct Stage-2 alpha transfer proxy.

## Artifacts

- `05_results\deepmimo_i3_60_source_alpha_n100_seed_20260630\deepmimo_i3_60_crossdomain.csv`
- `05_results\deepmimo_i3_60_source_alpha_n100_seed_20260630\deepmimo_i3_60_crossdomain_samples.csv`
- `05_results\deepmimo_i3_60_source_alpha_n100_seed_20260630\run_manifest.json`
- `05_results\deepmimo_i3_60_source_alpha_n100_seed_20260630\evaluation_summary.md`
