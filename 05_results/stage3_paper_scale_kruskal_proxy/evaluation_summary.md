# Stage 3 Paper-Scale Kruskal Proxy Evaluation Summary

## Outcome Summary

This run converts the existing paper-scale Tensor-OMP scan into a Kruskal identifiability proxy table. It uses the 128x16x32 tensor and L={2,4,8,16,32,64} on-grid FFT contract, then records bound ratios, Kruskal risk factors, NMSE trend, support recall, and runtime trend.

## evaluation_summary

- `research_question`: Does the paper-scale on-grid Tensor-OMP scan remain inside the Kruskal-identifiable regime and recover supports reliably?
- `claim_update`: supported for paper-scale on-grid Kruskal proxy evidence.
- `baseline_relation`: Derived from `paper_scale_tensor_omp_g1`, which already validates the 128x16x32 on-grid Tensor-OMP baseline.
- `failure_mode`: No execution failure; remaining limitation is that this is an on-grid FFT proxy, not off-grid, CDL, or DeepMIMO validation.
- `mechanism_note`: All tested L values remain below the paper-scale Kruskal proxy bound and recover support exactly in the on-grid FFT contract. NMSE degrades smoothly as L/Lmax increases, and runtime remains finite at this FFT-proxy scale.
- `next_action`: Use this as the paper-scale on-grid Kruskal sanity row; do not present it as DeepMIMO or off-grid proof.
- `evidence_level`: Stage-3 paper-scale sanity evidence.

## Key Metrics

- Paper-scale Kruskal proxy bound: 87
- Max tested L/Lmax: 0.7356
- Minimum support recall: 1.0000
- NMSE slope vs L/Lmax: 19.7336 dB per bound-ratio unit
- Runtime slope vs L/Lmax: -0.000600 s per bound-ratio unit
