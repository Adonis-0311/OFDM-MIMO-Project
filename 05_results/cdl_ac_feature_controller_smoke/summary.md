# CDL Profile Feature Controller Training

- Claim update: cdl-a-heldout-supported-angle-noninferior
- Held-out validation NMSE gain: 5.76352 dB
- Held-out validation delay/angle RMSE reduction: 0.0623884 / -0.000242518 bins
- Mean delay/angle alpha: 0.738728 / 0.0242347
- Elapsed seconds: 11.93

## Evaluation summary

- research_question: Can a profile-trained controller improve held-out physical parameters before zero-shot profile testing?
- claim_update: cdl-a-heldout-supported-angle-noninferior
- baseline_relation: Held-out validation uses disjoint seeds and the unchanged grid comparator.
- failure_mode: Non-positive held-out A NMSE/delay reduction or angle degradation beyond the explicit 0.01-bin noninferiority margin.
- next_action: Freeze and test only on profiles omitted from training and validation.
- evidence_level: Profile training with disjoint-seed validation; omitted profiles remain untouched.
