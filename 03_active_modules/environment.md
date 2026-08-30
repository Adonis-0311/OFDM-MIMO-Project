# Active Modules Environment

This stage-1 implementation currently runs on the local machine with:

- Python: 3.9.13
- Core runtime dependency used by the smoke path: NumPy
- Optional dependencies: PyYAML for YAML config loading, PyTorch for future T-OMP-Net training, pytest for normal test discovery

The v2.3R plan still targets Python 3.11+ and PyTorch >= 2.3 for the full training campaign. The present code is kept Python 3.9-compatible so Pack 0/1/2 smoke evidence can be generated immediately on this workstation.

## Verification Commands

```powershell
python -m compileall 03_active_modules 04_experiments/eval/run_stage1_g1_smoke.py tests/test_stage1_modules.py
python 04_experiments/eval/run_stage1_g1_smoke.py
python 04_experiments/eval/run_paper_scale_tensor_omp_g1.py
python 04_experiments/eval/run_paper_scale_offgrid_stress_g1.py
python 04_experiments/eval/run_5l_crlb_fim_validation.py
python 04_experiments/eval/run_5l_crlb_monte_carlo.py
python 04_experiments/eval/run_stage1_dependency_audit.py
python 04_experiments/eval/run_stage2_minimal_tompnet_smoke.py
python 04_experiments/eval/run_stage2_trainable_tompnet_smoke.py
python 04_experiments/eval/run_stage2_torch_tompnet_smoke.py
python 04_experiments/eval/aggregate_stage2_g2_manifest.py
```

When pytest is installed:

```powershell
python -m pytest tests/test_stage1_modules.py -q
```
