# 5L CRLB FIM Evaluation Summary

## Outcome Summary

The analytic 5-parameter FIM/CRLB implementation is validated against central finite differences on the paper-scale tensor shape. This supports the V2.3R G1 requirement that CRLB machinery exists and has numerically checked derivatives.

## evaluation_summary

- `research_question`: Does the 5L FIM/CRLB implementation correctly model [angle, delay, Doppler, gain real, gain imag] under complex Gaussian observations?
- `claim_update`: Supported for analytic derivative correctness; inconclusive for estimator-efficiency tightness because Monte Carlo RMSE/sqrt(CRLB) is not yet run.
- `baseline_relation`: Upgrades the previous single-delay CRLB smoke to a 5-parameter FIM implementation.
- `failure_mode`: None for derivative validation.
- `next_action`: Add Monte Carlo estimator-efficiency validation against the 5L CRLB after the estimator path is finalized.
- `evidence_level`: Solid for FIM implementation, partial for full G1.

## Key Metrics

- Max analytic-vs-numeric FIM relative error: 5.7304e-10
- Angle standard deviation drop from 0 dB to 30 dB: 31.6228x
- SNR points: 0, 10, 20, 30 dB

