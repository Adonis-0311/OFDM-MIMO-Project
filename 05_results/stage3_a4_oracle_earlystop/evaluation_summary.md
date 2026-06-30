# Stage 3 A4 IA-AUD Oracle Early-Stop Evaluation Summary

## Outcome Summary

This run estimates the best-case depth savings available to an adaptive-depth IA-AUD gate. For each sample, it observes the K=0..8 NMSE curve and chooses the earliest depth whose NMSE is within 0.50 dB of fixed K=8.

## evaluation_summary

- `research_question`: Can oracle early stopping reduce average unfolding depth by at least 25% while matching fixed-depth NMSE?
- `claim_update`: inconclusive for A4 FLOPs/depth-reduction evidence.
- `baseline_relation`: Fixed-depth K=8 repeated off-grid refinement is the comparator; oracle early-stop uses the same per-sample curve.
- `failure_mode`: No execution failure; remaining limitation is that oracle early-stop is an upper bound, not a trained gate.
- `mechanism_note`: Even oracle early stopping does not yet prove the >=25% depth-reduction target under the current tolerance/sample contract, so the full IA-AUD gate should not be claimed without stronger evidence.
- `next_action`: Either broaden the oracle sweep/tolerance analysis or downgrade IA-AUD to a cautious trade-off/appendix result.
- `evidence_level`: Stage-3 A4 upper-bound evidence, not final gating-network evidence.

## Key Metrics

- Fixed depth: 8
- NMSE tolerance: 0.50 dB
- Mean oracle depth: 6.8000
- Mean depth/FLOPs savings: 15.0000%
- Mean NMSE gap vs fixed depth: 0.1820 dB
- Wall-clock elapsed time: 39.60 s
