# DeepMIMO O1_60 G2 Dev Run

- Claim update: `dev-source-alpha-transfer-supported`
- Transfer proxy classification: `weak`
- TX tags: `t003,t004,t005,t006,t007,t008,t009,t010`
- RX tag: `r000`
- Source alpha: `0.64192` from `05_results\stage2_torch_locked_scale_g2_seed_sweep\stage2_torch_locked_scale_g2_seed_sweep_seeds.csv`
- Users: `16`
- SNRs: `0.0,10.0,20.0,30.0` dB
- L values: `4,8,16`
- Aggregated rows: `12`
- Sample rows: `192`
- Minimum mean support recall: `0.808594`
- Mean grid channel NMSE across cells: `-4.3252` dB
- Mean source-alpha channel NMSE across cells: `-5.70565` dB
- Mean source-alpha gain vs grid: `1.38045` dB
- Mean bounded refinement channel NMSE across cells: `-5.70396` dB
- Mean bounded gain vs grid: `1.37877` dB
- Mean source-alpha gap vs oracle-alpha: `0.185169` dB
- Mean dominant energy recall: `0.585577`
- RX x/y span: `24.200` m / `480.400` m
- Elapsed seconds: `5.39`

## Interpretation

The source-trained G2 alpha transfer proxy produced finite O1_60 metrics with positive mean gain and acceptable dominant-bin recall in this dev grid.

This is a raw-loader and scalar source-alpha transfer validation, not final Sensors E2 evidence. It proves the O1_60 local ray files can be converted into reproducible OFDM channel tensors and scored under a direct Stage-2 alpha transfer proxy.

## Artifacts

- `05_results\deepmimo_o1_60_g2\deepmimo_o1_60_g2.csv`
- `05_results\deepmimo_o1_60_g2\deepmimo_o1_60_g2_samples.csv`
- `05_results\deepmimo_o1_60_g2\run_manifest.json`
- `05_results\deepmimo_o1_60_g2\evaluation_summary.md`
