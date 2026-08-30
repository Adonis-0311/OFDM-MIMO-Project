# Stage 3 Paper-Scale Kruskal Proxy

- Config hash: `stage3-paper-scale-kruskal-proxy-20260624`

## Metrics

- `tensor_shape`: `128x16x32`
- `paper_kruskal_bound`: `87`
- `l_values`: `[2, 4, 8, 16, 32, 64]`
- `max_bound_ratio`: 0.735632
- `min_kruskal_margin`: 23
- `max_kruskal_risk_factor`: 7.74291
- `min_support_recall`: 1
- `mean_nmse_db_all`: -57.8482
- `nmse_slope_vs_bound_ratio`: 19.7336
- `runtime_slope_vs_bound_ratio`: -0.000600087

## Notes

- Derived from the existing paper_scale_tensor_omp_g1 run; no new recovery samples are generated.
- Kruskal proxy bound uses floor((Nv + K + M - 2) / 2) for the paper-scale 128x16x32 tensor.
- This is on-grid FFT Tensor-OMP sanity evidence and must not be presented as off-grid or DeepMIMO validation.

## Artifacts

- `05_results\stage3_paper_scale_kruskal_proxy\stage3_paper_scale_kruskal_proxy.csv`
- `05_results\stage3_paper_scale_kruskal_proxy\run_manifest.json`
