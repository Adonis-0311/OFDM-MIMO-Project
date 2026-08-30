# Complexity Benchmark Evaluation Summary

## Outcome Summary

This E4 dev-run establishes a reproducible complexity and wall-clock table for all selected estimator families.

The separable forward-backward ESPRIT row is a complexity comparator without cross-axis pairing; it is not labeled as full Unitary ESPRIT. PARAFAC uses a fixed-iteration complex ALS implementation.

## evaluation_summary

- `research_question`: What are the parameter count, operation-proxy, CPU wall-clock, and memory footprints of the implemented Tensor-OMP/T-OMP-Net paths?
- `claim_update`: complexity-comparator-table-ready
- `baseline_relation`: Grid FFT top-k is the reference baseline; bounded refinement and Torch alpha layer are measured on matching synthetic tensor scale.
- `failure_mode`: Operation counts are analytical proxies rather than profiler FLOPs, and timing depends on this CPU/software environment.
- `mechanism_note`: ESPRIT forms three axis-wise forward-backward covariance eigensystems; PARAFAC performs fixed-sweep complex ALS updates.
- `next_action`: Keep estimation-accuracy claims separate until matched comparator accuracy experiments are reviewed.
- `evidence_level`: E4 auxiliary/dev complexity evidence.

## Key Metrics

- Implemented method rows: 15.0
- Not-implemented comparator rows: 0.0
- Fastest implemented method: grid_fft_topk_tensor_omp at 4.3793 ms
- Slowest implemented method: bounded_local_refinement_lstsq at 1678.3922 ms
- Max parameter count: 1
