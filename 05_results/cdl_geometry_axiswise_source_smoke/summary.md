# CDL-Geometry Axiswise Synthetic Source Training

- Claim update: supported-source
- Mean delay/angle alpha: 0.64008 / 0.641313
- Mean axis separation: -0.0012334
- Mean/min cell gain vs grid: 4.01852 / 1.10655 dB
- Elapsed seconds: 0.54

## Evaluation summary

- research_question: Does source-only training at the external observation geometry learn a defensible frozen delay/angle refinement layer?
- claim_update: supported-source
- baseline_relation: Grid baseline and axiswise layer use identical held-out synthetic samples.
- failure_mode: Weak axis separation or negative cells indicate geometry matching alone is insufficient.
- next_action: Freeze mean alphas and evaluate once on Sionna CDL only if the source gate is credible.
- evidence_level: Synthetic geometry-matched source training; no external performance claim.
