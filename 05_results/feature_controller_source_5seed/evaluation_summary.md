# Feature-Conditioned Refinement Controller Source Training

- Claim update: feature-controller-source-supported
- Mean delay alpha/std: 0.868964 / 0.124551
- Mean angle alpha/std: 0.876252 / 0.138266
- Mean NMSE gain: 4.80135 dB
- Delay/angle bin-RMSE reduction: -0.0134852 / 0.0162339
- Local-support delay/angle bin-RMSE reduction: 0.114407 / 0.115659
- Elapsed seconds: 32.83

## Evaluation summary

- research_question: Can estimator-internal features predict non-collapsed per-sample delay/angle refinement scales?
- claim_update: feature-controller-source-supported
- baseline_relation: Grid and controller use identical held-out synthetic samples.
- failure_mode: Non-positive NMSE or either-axis local-support RMSE reduction, or output collapse below 0.01 std.
- next_action: Freeze the source ensemble for one unchanged Sionna CDL run only if supported.
- evidence_level: Source-only development gate.
