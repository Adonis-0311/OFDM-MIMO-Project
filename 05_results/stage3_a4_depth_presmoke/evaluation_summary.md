# Stage 3 A4 IA-AUD Depth Pre-Smoke Evaluation Summary

## Outcome Summary

This pre-smoke tests whether fixed-depth repeated off-grid refinement has different saturation depths across target counts. It is a problem-existence check for IA-AUD, not the final gating-network experiment.

## evaluation_summary

- `research_question`: Do simple and difficult target-count regimes show different NMSE-vs-depth saturation behavior?
- `claim_update`: supported for IA-AUD problem-existence evidence.
- `baseline_relation`: K=0 is grid Tensor-OMP support with LS amplitudes; K=1..8 adds repeated bounded off-grid refinement layers.
- `failure_mode`: No execution failure; remaining limitation is pre-smoke sample count and proxy depth definition.
- `mechanism_note`: The observed direction differs from the simple illustrative hypothesis: L=32 saturates earlier than L=2/L=8, consistent with a possible support/interference floor rather than unlimited benefit from deeper refinement.
- `next_action`: If supported, implement A4 gating/FLOPs experiment; if inconclusive, avoid full IA-AUD investment until a stronger depth signal is found.
- `evidence_level`: Stage-3 pre-smoke evidence only.

## Key Metrics

- Saturation depths: {2: 8, 8: 8, 32: 5}
- K=8 mean gains over K=0: {2: 25.130514912000727, 8: 19.586505839355617, 32: 8.176434652575816}
- Saturation-depth spread: 3
- Wall-clock elapsed time: 16.79 s
