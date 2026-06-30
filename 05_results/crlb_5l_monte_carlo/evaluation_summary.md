# 5L CRLB Monte Carlo Evaluation Summary

## Outcome Summary

The single-target 5L estimator-efficiency pilot supports the expected CRLB trend on the paper-scale tensor. After multiresolution search refinement, high-SNR RMSE is close to the analytic 5L CRLB and the RMSE decreases at the expected order as SNR increases.

## evaluation_summary

- `research_question`: Does an FFT-initialized off-grid estimator show RMSE scaling consistent with the analytic 5L CRLB?
- `claim_update`: Supported as a pilot for single-target estimator efficiency; not yet a large-sample or multi-target CRLB tightness proof.
- `baseline_relation`: Extends analytic FIM validation into Monte Carlo estimator evidence.
- `failure_mode`: The first pilot was search-grid limited; the final recorded run uses finer multiresolution search and removes that quantization bottleneck.
- `next_action`: Keep Pack 3 gated until CDL/DeepMIMO wrapper validation is complete, or explicitly waive that remaining G1 item.
- `evidence_level`: Solid pilot evidence for 5L CRLB trend; partial for full G1.

## Key Metrics

- Mean RMSE/CRLB ratio at 30 dB: 1.0067
- Max RMSE/CRLB ratio at 30 dB: 1.5009
- Angle RMSE drop from 10 dB to 30 dB: 9.928x
- Trials per SNR: 8

