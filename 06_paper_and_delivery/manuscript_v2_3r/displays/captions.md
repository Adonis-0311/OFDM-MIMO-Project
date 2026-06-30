# v2.3R Display Captions

## Figure 1

FDMA MIMO-OFDM ISAC observation model. A small set of paths or targets couples the transmit subarrays and receive ULA. Matched filtering and stacking preserve a separable angle-delay-Doppler tensor whose sparse atoms retain physical meaning.

## Figure 2

Implemented refinement paths and evidence scope. The local three-dimensional experiment learns one scalar interpolation parameter. The CDL experiment uses a separate 10--16--2 feature controller. A4 repeats deterministic local searches and applies a scalar plateau gate; it is a depth diagnostic, not controller or network depth.

## Figure 3

Evidence summary for the v2.3R local evaluation. (a) Bounded off-grid refinement improves measurement-domain NMSE over grid Tensor-OMP for L={2,4,8}; all evaluated target counts remain above the 3 dB gain gate. (b) At SNR=20 dB, the plateau early-stop rule supports a narrowed high-load claim for L>=32, while L=16 is boundary evidence because its maximum gap exceeds the tolerance. (c) The same scalar gate is inconclusive across SNR={10,20,30} dB at L=32, preventing a broad SNR-axis early-stop claim.

## Figure 4

Scaled CDL physical evaluation versus grid Tensor-OMP. Five seed means and profile averages show aggregate positive CDL-A/C evidence and the zero-shot CDL-D channel/delay failure boundary.

## Graphical Abstract

Sparse angle-delay-Doppler observations enter learned bounded post-support refinement and produce channel and physical parameter estimates. The local scalar and CDL feature controller are distinct paths; held-out CDL-A/C gains and the CDL-D profile-shift boundary are shown together.

## Table 1

Main local result summary. The table reports G2 bounded-refinement gain by target count and A4 cross-L early-stop savings/gap at the core 20 dB setting. Positive A4 interpretation is restricted to L>=32.

## Table 2

A4 SNR sensitivity boundary. The scalar plateau gate is evaluated at L=32 for SNR={10,20,30} dB. The sweep is treated as appendix or limitation evidence because at least one SNR cell violates the planned savings or gap criterion.

## Table 3

A4 SNR threshold-frontier diagnostic. Standard train-selected, guarded train-selected, and test-oracle scalar thresholds are compared at L=32 across SNR={10,20,30} dB. The test-oracle row is a diagnostic upper bound, not a deployable policy; its failure to clear all SNR cells supports replacing scalar-threshold tuning with a learned SNR-aware gate if the adaptive-depth claim is expanded.

## Table 4

A4 SNR-aware gate diagnostic. An SNR-indexed scalar threshold, a lightweight SNR/curve-feature kNN gate, and a per-curve quality oracle are compared at L=32 across SNR={10,20,30} dB. The kNN gate still misses the cross-SNR savings/gap contract, and the per-curve oracle falls below the minimum savings target in one SNR cell; this shifts future work from simple gate replacement toward refinement-schedule or training-objective redesign.
