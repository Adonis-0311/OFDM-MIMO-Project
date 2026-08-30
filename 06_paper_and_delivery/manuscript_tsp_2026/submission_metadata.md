# IEEE TSP Submission Metadata

## Article

Type: Regular Paper

Title: Projection-Selected Multidimensional Candan Refinement after FFT Tensor Support Selection

Authors: Yuhui Liu; Hangcheng Han

Corresponding author: Hangcheng Han

Keywords: MIMO-OFDM; off-grid estimation; DFT interpolation; projection selection; FFT tensor estimation; channel estimation

## Suggested Unified EDICS

Primary:

- `TM-SSP-ESTI` — Estimation

Secondary candidates:

- `TM-MAT-TENS` — Tensor-based signal processing
- `SC-SAM-MIMO` — MIMO and massive MIMO array processing
- `SC-COM-CHAN` — Channel modeling and estimation

These codes are taken from the Unified EDICS list approved in April 2026. The corresponding author should choose the smallest portal set that best reflects the final manuscript.

## Abstract

A multidimensional fast Fourier transform (FFT) followed by top-$L$ selection gives explicit coarse neighborhoods for sparse MIMO-OFDM estimation, while physical coordinates remain off grid. We develop a non-iterative refinement that applies Candan's finite-length-corrected complex three-sample update along every active tensor axis and refits all amplitudes jointly. A calibration-free projection rule returns the refined result whenever its fitted subspace captures at least as much received energy as the grid subspace. The update reads exactly $3DL$ complex FFT samples for $D$ axes and $L$ neighborhoods. We prove that separability reduces every isolated axis triplet exactly to the one-dimensional Candan quotient, then bound multi-component interference and Gaussian noise through explicit Dirichlet-coherence, dynamic-range, SNR, and joint-fit terms. On 1200 common three-dimensional scenes, the local Candan stage improves measurement normalized mean-square error by 24.26 dB at 11.07 ms; the complete projection-selected estimator costs 11.24 ms, only 1.57% more. The local gain remains 14.45 dB over the complete $[-0.49,0.49]$ fractional-bin interval and is positive in all 48 controlled separation--near--far cells. On 9000 clustered-delay-line tests, projection selection raises aggregate gain from 5.14 to 5.28 dB and CDL-D gain from 0.28 to 0.71 dB. Aggregate delay RMSE falls from 428.45 to 413.52 ns and joint quarter-bin accuracy rises from 7.46% to 18.84%.

## Upload Descriptions

- Main manuscript: complete self-contained Regular Paper in IEEE double-column format.
- Supplementary material: expanded estimator ledgers, implementation definitions, numerical identity checks, physical-parameter tables, and reproducibility map for specialist inspection.
- Cover letter: contribution, evidence, venue fit, originality, and prior-submission status.
- Prior-submission disclosure: scope-only editorial prescreen decision and the signal-processing basis of the present submission.
