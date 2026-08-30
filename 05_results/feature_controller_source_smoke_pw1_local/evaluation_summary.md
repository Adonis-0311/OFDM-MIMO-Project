# Feature-Conditioned Refinement Controller Source Training

- Claim update: feature-controller-source-supported
- Mean delay alpha/std: 0.813762 / 0.210566
- Mean angle alpha/std: 0.824259 / 0.271523
- Mean NMSE gain: 4.69309 dB
- Delay/angle bin-RMSE reduction: -0.0154645 / 0.00669949
- Local-support delay/angle bin-RMSE reduction: 0.120586 / 0.0942491
- Elapsed seconds: 3.56

## Evaluation summary

- research_question: Can estimator-internal features predict non-collapsed per-sample delay/angle refinement scales?
- claim_update: feature-controller-source-supported
- baseline_relation: Grid and controller use identical held-out synthetic samples.
- failure_mode: Non-positive NMSE or either-axis local-support RMSE reduction, or output collapse below 0.01 std.
- next_action: Freeze the source ensemble for one unchanged Sionna CDL run only if supported.
- evidence_level: Source-only development gate.
