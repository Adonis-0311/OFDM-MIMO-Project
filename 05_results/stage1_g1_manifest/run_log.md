# Stage 1 G1 Run Log

Date: 2026-06-24

## Commands

```powershell
python 04_experiments/eval/run_stage1_g1_smoke.py
python 04_experiments/eval/run_paper_scale_tensor_omp_g1.py
python 04_experiments/eval/run_paper_scale_offgrid_stress_g1.py
python 04_experiments/eval/run_5l_crlb_fim_validation.py
python 04_experiments/eval/run_5l_crlb_monte_carlo.py
python 04_experiments/eval/run_stage1_dependency_audit.py
python 04_experiments/eval/aggregate_stage1_g1_manifest.py
```

## Verification

```powershell
python -m compileall 03_active_modules 04_experiments/eval tests/test_stage1_modules.py
```

The local machine lacks `pytest`, so test functions were executed through Python import discovery. The latest test pass covered 9 functions in `tests/test_stage1_modules.py`.

## Gate Decision

Stage 1 local mechanics are strongly supported. Pack 3 remains gated because standards-aligned CDL/DeepMIMO evidence depends on unavailable local external resources: 5G Toolbox license is false and DeepMIMO dataset files are absent.

