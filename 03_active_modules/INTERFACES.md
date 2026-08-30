# Active Module Interfaces

## Common

- `common.config.ExperimentConfig`: frozen dataclass for seed, SNR, trial count, target count, and tensor grid dimensions.
- `common.seed.seed_all(seed)`: seeds Python `random`, NumPy, and Torch when Torch is installed; returns a NumPy generator.
- `common.manifest.write_run_manifest(...)`: writes a JSON manifest containing command, config, metrics, environment, and notes.

## Data

- `data.set_a_generator.GridConfig`: angle-delay-Doppler grid dimensions.
- `data.set_a_generator.SetASample`: measurement vector, dictionary matrix, truth coefficients, noise variance, SNR, and grid metadata.
- `data.set_a_generator.generate_set_a_sample(...)`: produces one synthetic sparse tensor Set A sample using a normalized tensor DFT dictionary.
- `data.impairments`: phase noise, IQ imbalance, and physical two-parameter mutual coupling utilities for later HIR-JL smoke gates.
- `data.offgrid_tensor`: continuous-bin angle-delay-Doppler tensor synthesis, grid projection, bounded local refinement, and measurement-domain NMSE.
- `data.offgrid_tensor.estimate_single_target_multiresolution(...)`: single-target ML-style local search initialized from FFT Tensor-OMP.

## Baseline

- `baseline.sparse_recovery.omp(...)`: classical OMP over a supplied dictionary and complex measurement.
- `baseline.tensor_omp.run_tensor_omp(sample, max_iters=None)`: Tensor-OMP stage-1 wrapper using the Set A sample contract.
- `baseline.tensor_omp.evaluate_tensor_omp(sample, result)`: emits NMSE, support recall, angle/delay/Doppler RMSE in grid bins, and residual norm.
- `baseline.tensor_fft_omp.recover_topk_fft(sample, n_targets)`: implicit unitary FFT Tensor-OMP path for paper-scale on-grid DFT dictionaries.
- `baseline.crlb_5l.coefficient_crlb_proxy(sample)`: coefficient-recovery CRLB proxy for stage-1 wiring only; this is not the final 5L joint ISAC CRLB.
- `baseline.crlb_5l.five_param_fim_crlb(...)`: analytic 5-parameter FIM/CRLB with central finite-difference validation.

## T-OMP-Net

- `tompnet.layer.run_minimal_tompnet_smoke(...)`: deterministic Stage-2 smoke/proxy for unfolded top-k selection plus optional bounded off-grid refinement.
- `tompnet.hungarian_loss.permutation_invariant_mse(...)`: brute-force permutation-invariant loss for small smoke tests.
- `tompnet.trainable.train_alpha_grid(...)`: NumPy trainable/calibrated Stage-2 smoke path for bounded off-grid interpolation when PyTorch is unavailable.
- `tompnet.torch_layer.TorchOffgridRefinementLayer`: PyTorch `nn.Module` smoke layer for trainable bounded off-grid refinement.

## Experiment Entrypoint

- `04_experiments/eval/run_stage1_g1_smoke.py`: reproducible Pack 0/1/2 smoke run producing CSV, summary, and run manifest under `05_results/stage1_g1_smoke/`.
- `04_experiments/eval/run_paper_scale_tensor_omp_g1.py`: paper-scale on-grid Tensor-OMP scan for shape 128x16x32 and L in {2,4,8,16,32,64}.
- `04_experiments/eval/run_paper_scale_offgrid_stress_g1.py`: paper-scale off-grid stress and bounded local refinement scan.
- `04_experiments/eval/run_5l_crlb_fim_validation.py`: analytic-vs-numeric 5L FIM/CRLB validation.
- `04_experiments/eval/run_5l_crlb_monte_carlo.py`: pilot estimator-efficiency Monte Carlo against the analytic 5L CRLB.
- `04_experiments/eval/run_stage1_dependency_audit.py`: reproducible local dependency audit for CDL/DeepMIMO readiness.
- `04_experiments/eval/run_stage2_minimal_tompnet_smoke.py`: bounded Stage-2 minimal T-OMP-Net smoke/proxy comparison against grid Tensor-OMP.
- `04_experiments/eval/run_stage2_trainable_tompnet_smoke.py`: trainable alpha-calibration smoke with train/test split and curriculum L values.
- `04_experiments/eval/run_stage2_torch_tompnet_smoke.py`: PyTorch CPU trainable T-OMP-Net smoke with Adam and held-out evaluation.
- `04_experiments/eval/aggregate_stage2_g2_manifest.py`: Stage-2/G2 gate aggregation for proxy-pass versus pending trained-network evidence.
