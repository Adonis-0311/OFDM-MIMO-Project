# Feature-Conditioned Refinement Controller Source Training

- Claim update: feature-controller-source-inconclusive
- Mean delay alpha/std: 0.80153 / 0.178614
- Mean angle alpha/std: 0.888057 / 0.200759
- Mean NMSE gain: 4.90555 dB
- Delay/angle bin-RMSE reduction: -0.0117478 / 0.00504191
- Elapsed seconds: 2.76

## Evaluation summary

- research_question: Can estimator-internal features predict non-collapsed per-sample delay/angle refinement scales?
- claim_update: feature-controller-source-inconclusive
- baseline_relation: Grid and controller use identical held-out synthetic samples.
- failure_mode: Non-positive NMSE or either-axis RMSE reduction, or output collapse below 0.01 std.
- next_action: Freeze the source ensemble for one unchanged Sionna CDL run only if supported.
- evidence_level: Source-only development gate.
