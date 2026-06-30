# v2.3R Stage 1 Current Board

Generated: 2026-06-24

## Current Mainline

V2.3R is the active execution version. Stage 1 G1 is accepted under the original V2.3R gate definition, and the project may enter Stage 2 with bounded minimal T-OMP-Net smoke runs. Stage 3 A4/A5 modules remain gated behind G2.

## Trusted Reusable Assets

- `05_results/v2_2_supplemental_manifest.md`: trusted as lightweight v2.2 supplemental evidence and direction validation, not as final full-scale T-OMP-Net evidence.
- `01_design_and_plan/V2_3R_STEADY_EXECUTION_PLAN.md`: trusted active plan and gate contract.
- `05_results/stage1_g1_smoke/`: trusted as a new local Pack 0/1/2 smoke artifact with command, config, CSV, and manifest.
- `05_results/paper_scale_tensor_omp_g1/`: trusted as paper-scale on-grid Tensor-OMP evidence for shape 128x16x32 and L in {2,4,8,16,32,64}.
- `05_results/paper_scale_offgrid_stress_g1/`: trusted as paper-scale off-grid bounded refinement evidence for L in {2,4,8,16}.
- `05_results/crlb_5l_fim_validation/`: trusted as analytic-vs-numeric 5L FIM/CRLB derivative validation.
- `05_results/crlb_5l_monte_carlo/`: trusted as a single-target estimator-efficiency pilot against the 5L CRLB.
- `05_results/stage1_dependency_audit/`: trusted as the current external dependency audit for standards-aligned CDL/DeepMIMO validation.
- `05_results/stage1_g1_manifest/`: trusted as the current G1 gate aggregation surface.

## Latest Decisive Result

`crlb_5l_monte_carlo_20260624` closes the estimator-efficiency pilot gap. At 30 dB, the single-target estimator has mean RMSE/CRLB ratio 1.0067 and max ratio 1.5009; angle RMSE drops 9.928x from 10 dB to 30 dB. Off-grid bounded refinement also improves measurement-domain NMSE by 7.5368 dB on average, and analytic 5L FIM matches finite differences with maximum relative error 5.7304e-10.

## Active Blocker

No remaining G1 blocker. Standards-aligned CDL/DeepMIMO remains an external-dependency risk for G3: current audit shows `license('test','5G_Toolbox') = 0` and DeepMIMO dataset files = 0.

## Stale Routes To Ignore

- V2.3 Lemma 2 closed-form optimal-depth derivation.
- A6/MAML as a main contribution.
- Exact MOMPnet/DDA-Net reproduction as a main-figure dependency.

## Next Decision Scope

Start Stage 2 / Pack 3 with a bounded minimal T-OMP-Net smoke: layer skeleton, bounded off-grid module, permutation-invariant loss, and comparison against Tensor-OMP at SNR=20 dB.

## Budget Class

Development smoke evidence is complete for the Python path, on-grid paper-scale Tensor-OMP, off-grid bounded refinement, analytic 5L FIM/CRLB validation, and single-target estimator-efficiency pilot. G1 is accepted; G2 remains unproven.
