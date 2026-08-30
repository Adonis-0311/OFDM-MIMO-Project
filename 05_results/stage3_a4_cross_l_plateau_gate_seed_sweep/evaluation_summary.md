# Stage 3 A4 Cross-L Plateau Gate Seed Sweep Evaluation Summary

## Outcome Summary

This run extends the narrowed A4 plateau early-stop evidence from L=32 to L={16,32,64}. It tests whether the deployable scalar plateau gate behaves like a high-L/platform mechanism rather than a single-L artifact.

## evaluation_summary

- `research_question`: Does the narrowed A4 plateau gate remain useful across L={16,32,64}, especially for L>=32?
- `claim_update`: supported for cross-L high-L A4 evidence.
- `baseline_relation`: Fixed-depth K=8 repeated off-grid refinement is the comparator for each seed and L cell.
- `failure_mode`: No execution failure if complete; remaining limitation is a deliberately small CPU-feasible seed/sample count.
- `mechanism_note`: The plateau gate keeps the high-L mean savings above 25% for L>=32 while remaining within the NMSE tolerance. L=16 should be treated as boundary evidence.
- `next_action`: Use A4 as a high-L/platform early-stop result and aggregate it into the paper evidence table.
- `evidence_level`: Cross-L local synthetic strengthening, not a global IA-AUD proof.

## Key Metrics

- Seeds: [20260624, 20260625]
- L values: [16, 32, 64]
- High-L minimum mean depth/FLOPs savings: 25.0000%
- High-L maximum mean NMSE gap: 0.4008 dB
- Overall mean cell depth/FLOPs savings: 27.0833%
- Overall mean cell NMSE gap: 0.3637 dB
- Wall-clock elapsed time: 174.21 s

## L Summary

| L | Mean savings (%) | Min savings (%) | Mean gap (dB) | Max gap (dB) |
|---|---:|---:|---:|---:|
| 16 | 28.1250 | 18.7500 | 0.4220 | 0.5480 |
| 32 | 28.1250 | 25.0000 | 0.3769 | 0.4008 |
| 64 | 25.0000 | 25.0000 | 0.2922 | 0.3297 |
