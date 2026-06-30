# CDL Profile Feature Controller Training

- Claim update: cdl-profile-heldout-physical-supported
- Held-out validation NMSE gain: 5.95026 dB
- Held-out validation delay/angle RMSE reduction: 0.0601729 / 0.0058083 bins
- Held-out physical broadside-angle RMSE reduction: 3.58912 deg
- Mean delay/angle alpha: 0.906946 / 0.416957
- Elapsed seconds: 14.15

## Evaluation summary

- research_question: Can a profile-trained controller improve held-out physical parameters before zero-shot profile testing?
- claim_update: cdl-profile-heldout-physical-supported
- baseline_relation: Held-out validation uses disjoint seeds and the unchanged grid comparator.
- failure_mode: Non-positive held-out NMSE, delay-bin reduction, or physical broadside-angle reduction.
- next_action: Freeze and test only on profiles omitted from training and validation.
- evidence_level: Profile training with disjoint-seed validation; omitted profiles remain untouched.
