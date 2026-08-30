# Stage 3 A4 SNR Threshold Frontier Evaluation Summary

## Outcome Summary

This diagnostic compares the existing train-selected scalar plateau gate with a guarded train selection and a test-oracle threshold frontier for each SNR cell.

## evaluation_summary

- `research_question`: Is the A4 SNR failure caused by the scalar plateau feature itself or by threshold calibration?
- `baseline_relation`: Fixed-depth K=8 repeated off-grid refinement remains the quality comparator.
- `evidence_level`: Diagnostic local synthetic frontier; the test-oracle row is an upper bound, not deployable evidence.
- `mechanism_note`: Even the test-frontier diagnostic does not clear the SNR-axis gate, so a scalar plateau threshold is too weak for a broad SNR claim under this contract.
- `next_action`: If only the oracle clears the gate, replace the scalar rule with a learned/calibrated SNR-aware gate before widening A4.

## Key Metrics

- Seeds: [20260624, 20260625]
- SNR values: [10.0, 20.0, 30.0]
- Standard-train minimum SNR mean savings: 15.6250%
- Standard-train maximum SNR mean gap: 0.6691 dB
- Test-oracle minimum SNR mean savings: 0.0000%
- Test-oracle maximum SNR mean gap: 0.4554 dB
- Wall-clock elapsed time: 146.70 s

## Policy/SNR Summary

| Policy | SNR (dB) | Mean savings (%) | Min savings (%) | Mean gap (dB) | Max gap (dB) | Pass rate |
|---|---:|---:|---:|---:|---:|---:|
| standard_train | 10.0 | 31.2500 | 31.2500 | 0.6468 | 0.6691 | 0.0000 |
| standard_train | 20.0 | 15.6250 | 12.5000 | 0.2147 | 0.2758 | 0.0000 |
| standard_train | 30.0 | 25.0000 | 25.0000 | 0.2941 | 0.3442 | 1.0000 |
| guarded_train | 10.0 | 9.3750 | 6.2500 | 0.0777 | 0.1141 | 0.0000 |
| guarded_train | 20.0 | 12.5000 | 12.5000 | 0.1291 | 0.1535 | 0.0000 |
| guarded_train | 30.0 | 18.7500 | 12.5000 | 0.2245 | 0.3442 | 0.5000 |
| test_oracle_frontier | 10.0 | 12.5000 | 0.0000 | 0.1781 | 0.3562 | 0.5000 |
| test_oracle_frontier | 20.0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| test_oracle_frontier | 30.0 | 28.1250 | 25.0000 | 0.3998 | 0.4554 | 1.0000 |
