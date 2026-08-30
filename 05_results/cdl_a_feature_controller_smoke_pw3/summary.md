# CDL-A Feature Controller Training

- Claim update: cdl-a-training-inconclusive
- Held-out A NMSE gain: 6.76861 dB
- Held-out A delay/angle RMSE reduction: 0.0136618 / -0.00284104 bins
- Mean delay/angle alpha: 0.947259 / 0.0595828
- Elapsed seconds: 12.83

## Evaluation summary

- research_question: Can an A-trained controller improve held-out A physical parameters before zero-shot C/D testing?
- claim_update: cdl-a-training-inconclusive
- baseline_relation: Held-out A uses disjoint seeds and the unchanged grid comparator.
- failure_mode: Non-positive held-out A NMSE or either physical-bin RMSE reduction.
- next_action: Freeze and test zero-shot on CDL-C/D only if held-out A passes.
- evidence_level: Profile-A training/held-out validation; C/D untouched.
