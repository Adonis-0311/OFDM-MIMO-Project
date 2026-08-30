# Feature-Conditioned Refinement Controller Source Training

- Claim update: feature-controller-source-inconclusive
- Mean delay alpha/std: 0.813762 / 0.210566
- Mean angle alpha/std: 0.824259 / 0.271523
- Mean NMSE gain: 4.69309 dB
- Delay/angle bin-RMSE reduction: -0.0154645 / 0.00669949
- Elapsed seconds: 2.87

## Evaluation summary

- research_question: Can estimator-internal features predict non-collapsed per-sample delay/angle refinement scales?
- claim_update: feature-controller-source-inconclusive
- baseline_relation: Grid and controller use identical held-out synthetic samples.
- failure_mode: Non-positive NMSE or either-axis RMSE reduction, or output collapse below 0.01 std.
- next_action: Freeze the source ensemble for one unchanged Sionna CDL run only if supported.
- evidence_level: Source-only development gate.
