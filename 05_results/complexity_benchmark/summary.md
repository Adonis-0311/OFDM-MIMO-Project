# Complexity Benchmark

- Claim update: `complexity-comparator-table-ready`
- Tensor shape: `128x16x32`
- L values: `4,8,16`
- Implemented method rows: `15`
- Not-implemented comparator rows: `0`
- Min median wall-clock: `4.3793` ms
- Max median wall-clock: `1678.39` ms
- Max parameter count: `1`

## Interpretation

The repository now has executable complexity rows for the Tensor-OMP/T-OMP-Net proxy paths, separable forward-backward ESPRIT, and complex PARAFAC-ALS. Operation proxies are not profiler FLOPs, and comparator accuracy remains outside this timing-only evidence block.

## Artifacts

- `05_results\complexity_benchmark\complexity_benchmark.csv`
- `05_results\complexity_benchmark\run_manifest.json`
- `05_results\complexity_benchmark\evaluation_summary.md`
