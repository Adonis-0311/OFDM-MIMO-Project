# Stage 2 Axiswise T-OMP-Net Source Training

- Claim update: supported-local
- Mean learned angle/delay/Doppler alpha: 0.641522 / 0.642223 / 0.642219
- Mean/min gain vs grid: 5.76672 / 4.47323 dB
- Mean/min gain vs shared alpha: 0.00135218 / 0.000438958 dB
- Elapsed seconds: 8.06

## Evaluation summary

- research_question: Can source-only axiswise bounded refinement preserve local G2 gain while decoupling angle and delay for frozen external transfer?
- claim_update: supported-local
- baseline_relation: Grid and shared-alpha baselines use identical held-out synthetic samples.
- failure_mode: If axis alphas collapse together or local gain falls below 3 dB, the richer parameterization is not justified.
- next_action: Freeze mean source-trained angle/delay alphas and evaluate once on unchanged Sionna CDL.
- evidence_level: Source-domain multi-seed development evidence; external validity is not implied.
