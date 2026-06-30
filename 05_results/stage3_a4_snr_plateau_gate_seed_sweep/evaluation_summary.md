# Stage 3 A4 SNR Plateau Gate Seed Sweep Evaluation Summary

## Outcome Summary

This run tests whether the narrowed high-L plateau early-stop gate remains stable across SNR={10,20,30} dB at L=32 and tensor shape `128x16x32`.

## evaluation_summary

- `research_question`: Does the A4 plateau gate keep useful depth/FLOPs savings across SNR={10,20,30} dB for L=32?
- `claim_update`: inconclusive for SNR-sweep A4 robustness evidence.
- `baseline_relation`: Fixed-depth K=8 repeated off-grid refinement is the comparator for each seed and SNR cell.
- `failure_mode`: No execution failure if complete; remaining limitation is small local synthetic sample count.
- `mechanism_note`: The SNR sweep exposes a boundary for the scalar plateau gate under the current small-sample contract.
- `next_action`: Keep A4 narrowed and report the failing SNR cells instead of claiming SNR-robust early stopping.
- `evidence_level`: SNR-axis local synthetic strengthening, not a global IA-AUD proof.

## Key Metrics

- Seeds: [20260624, 20260625]
- SNR values: [10.0, 20.0, 30.0]
- Minimum mean depth/FLOPs savings over SNR cells: 21.8750%
- Maximum mean NMSE gap over SNR cells: 0.6834 dB
- Overall mean cell depth/FLOPs savings: 29.1667%
- Overall mean cell NMSE gap: 0.4192 dB
- Wall-clock elapsed time: 148.92 s

## SNR Summary

| SNR (dB) | Mean savings (%) | Min savings (%) | Mean gap (dB) | Max gap (dB) |
|---:|---:|---:|---:|---:|
| 10.0 | 31.2500 | 25.0000 | 0.4772 | 0.6834 |
| 20.0 | 34.3750 | 31.2500 | 0.4555 | 0.5161 |
| 30.0 | 21.8750 | 18.7500 | 0.3250 | 0.4045 |
