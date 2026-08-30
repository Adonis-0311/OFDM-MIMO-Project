# Stage 3 A4 High-L Plateau Gate Evaluation Summary

## Outcome Summary

This run tests a deployable high-L early-stop gate. A scalar threshold is selected on training curves, then evaluated on held-out L=32 curves against fixed K=8.

## evaluation_summary

- `research_question`: Can a lightweight plateau gate reach >=25% depth/FLOPs savings on high-L samples while staying near fixed-depth NMSE?
- `claim_update`: supported for narrowed high-L A4 gate evidence.
- `baseline_relation`: Fixed-depth K=8 is the comparator; the gate uses only sequential per-layer improvement and a trained scalar threshold.
- `failure_mode`: No execution failure; remaining limitation is L=32-only scope and small train/test sample count.
- `mechanism_note`: A simple trained threshold gate reaches the high-L >=25% depth-reduction target within the NMSE tolerance, so A4 remains viable as a narrowed high-L/platform gate.
- `next_action`: Implement the high-L gate as the A4 appendix or restricted mainline and avoid global IA-AUD claims.
- `evidence_level`: Stage-3 restricted A4 gate evidence.

## Key Metrics

- Selected threshold: 0.7500 dB
- Fixed depth: 8
- NMSE tolerance: 0.50 dB
- Test mean depth: 5.3333
- Test mean depth/FLOPs savings: 33.3333%
- Test mean NMSE gap vs fixed depth: 0.3643 dB
- Wall-clock elapsed time: 65.86 s
