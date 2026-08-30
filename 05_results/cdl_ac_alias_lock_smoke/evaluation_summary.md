# CDL Profile Feature Controller Training

- Claim update: cdl-profile-heldout-physical-supported
- Held-out validation NMSE gain: 6.04858 dB
- Held-out validation delay/angle RMSE reduction: 0.0654373 / 0.00269975 bins
- Held-out physical broadside-angle RMSE reduction: 0.575806 deg
- Mean delay/angle alpha: 0.974873 / 0.12453
- Elapsed seconds: 16.06

## Evaluation summary

- research_question: Can a profile-trained controller improve held-out physical parameters before zero-shot profile testing?
- claim_update: cdl-profile-heldout-physical-supported
- baseline_relation: Held-out validation uses disjoint seeds and the unchanged grid comparator.
- failure_mode: Non-positive held-out NMSE, delay-bin reduction, or physical broadside-angle reduction.
- next_action: Freeze and test only on profiles omitted from training and validation.
- evidence_level: Profile training with disjoint-seed validation; omitted profiles remain untouched.
