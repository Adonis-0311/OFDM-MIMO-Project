# Learned Bounded Off-Grid Refinement for Sparse Tensor-OMP in mmWave MIMO-OFDM ISAC

> Canonical manuscript: `latex/main.tex` and `latex/main.pdf`.
> Identity-corrected checkpoint: 2026-06-29.
> Evidence boundary: `claim_evidence_ledger.json` and `paper_experiment_matrix.md`.

## Abstract

Sparse tensor recovery is a natural model for mmWave MIMO-OFDM integrated sensing and communication, but dictionary quantization limits physically interpretable parameter estimates. We study learned bounded interpolation between Tensor-OMP grid supports and deterministic local-refinement candidates. The local three-dimensional implementation learns one scalar and improves measurement-domain NMSE over grid Tensor-OMP by 6.1726 dB on average across L={2,4,8} in a five-seed synthetic study. A separate 210-parameter feature controller for two-dimensional CDL measurements predicts delay and angle interpolation scales and is trained with permutation-invariant, alias-aware physical supervision. On frozen held-out CDL-A/C evaluation it yields gains of 6.2286 dB in channel NMSE, 10.1241 ns in delay RMSE, and 0.5277 degrees in projected-angle RMSE. Zero-shot CDL-D degrades channel and delay estimates. A separate deterministic repeated-refinement diagnostic supports a restricted high-load result at 20 dB but not an SNR-robust stopping claim. These results support bounded post-support refinement, not a fully integrated deep-unfolded network.

## Canonical sections

The active section sources are under `latex/sections/`. The Markdown files under `sections/` are historical drafting snapshots and must not be used as current claim text.

## Current hard boundaries

- The local scalar, CDL controller, and A4 depth diagnostic are distinct implementations.
- G2 and A4 are diagnostic-scale statistical studies.
- CDL-A/C is held-out but profile-scoped; CDL-D is a zero-shot channel/delay failure.
- E10 is a complexity table, not a matched-accuracy Pareto comparison.
- A T-OMP-Net/deep-unfolding title requires a new integrated multi-stage implementation and evaluation.
