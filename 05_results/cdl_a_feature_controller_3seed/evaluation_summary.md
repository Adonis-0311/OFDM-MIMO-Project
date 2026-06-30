# CDL-A Feature Controller Training

- Claim update: cdl-a-heldout-supported-angle-noninferior
- Held-out A NMSE gain: 6.38708 dB
- Held-out A delay/angle RMSE reduction: 0.0240909 / -0.00437907 bins
- Mean delay/angle alpha: 0.860611 / 0.121961
- Elapsed seconds: 56.43

## Evaluation summary

- research_question: Can an A-trained controller improve held-out A physical parameters before zero-shot C/D testing?
- claim_update: cdl-a-heldout-supported-angle-noninferior
- baseline_relation: Held-out A uses disjoint seeds and the unchanged grid comparator.
- failure_mode: Non-positive held-out A NMSE/delay reduction or angle degradation beyond the explicit 0.01-bin noninferiority margin.
- next_action: Freeze and test zero-shot on CDL-C/D only if held-out A passes.
- evidence_level: Profile-A training/held-out validation; C/D untouched.
