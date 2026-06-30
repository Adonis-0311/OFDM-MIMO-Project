# Stage 3 A4 High-L Plateau Gate Seed Sweep Evaluation Summary

## Outcome Summary

This run repeats the deployable high-L plateau early-stop gate across multiple seeds for L=32 at tensor shape `128x16x32`. It tests whether the narrowed A4 claim is stable beyond the first single-seed gate run.

## evaluation_summary

- `research_question`: Does the narrowed high-L plateau gate keep >=25% depth/FLOPs savings within the NMSE tolerance across seeds?
- `claim_update`: supported for narrowed multi-seed A4 high-L gate evidence.
- `baseline_relation`: Fixed-depth K=8 repeated off-grid refinement is the comparator; each seed trains only a scalar plateau threshold.
- `failure_mode`: No execution failure if complete; remaining limitation is synthetic L=32-only evidence.
- `mechanism_note`: The high-L plateau gate remains above the 25% depth-saving target across the seed sweep while staying within the NMSE tolerance.
- `next_action`: Promote A4 only as a narrowed high-L/platform-sample early-stop mechanism and avoid global adaptive-depth claims.
- `evidence_level`: Multi-seed local high-L A4 strengthening, not a global IA-AUD proof.

## Key Metrics

- Seeds: [20260624, 20260625, 20260626]
- Mean seed depth/FLOPs savings: 26.0417%
- Std. seed depth/FLOPs savings: 3.6084%
- Minimum seed depth/FLOPs savings: 21.8750%
- Mean seed NMSE gap vs fixed depth: 0.3339 dB
- Maximum seed NMSE gap vs fixed depth: 0.3578 dB
- Wall-clock elapsed time: 142.70 s
