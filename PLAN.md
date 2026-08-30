# Active Plan — v2.3R IEEE submission packaging

## Current anchor (2026-06-30)

The matched-Pareto reframe is complete. Paper-scale E12 covers five seeds, four SNRs, three target counts, and 20 paired scenes per cell; G2 uses 30 held-out scenes per L/seed; A4 uses five seeds and five test curves per cell. The active anchor is IEEE submission packaging and skeptical re-audit. Integrated K-stage estimation and trained DeepMIMO physical evaluation are deferred future work for this submission.

## Immediate route

1. Correct method identity and figure provenance in the paper.
2. Add the implemented mathematical mapping instead of prose-only theory.
3. Regenerate Fig. 2 and Fig. 3 for evidence fidelity and scientific readability.
4. Synchronize the claim ledger and experiment matrix.
5. Prepare a review branch and publish after validation; GitHub authentication is required for push/PR.

## Next experimental gate

If the title retains “deep unfolding” or T-OMP-Net, implement and evaluate an actual K-stage integrated estimator. Otherwise keep the current paper framed as learned bounded refinement after Tensor-OMP support selection. Matched classical accuracy comparators and larger-sample strengthening follow that identity decision.

## Historical E1 plan

## Selected idea

Transfer the Stage-2 learned bounded-refinement parameter into the Sionna CDL-A/C/D evaluator, then score the resulting continuous delay/angle bins against CIR-grounded physical truth with Hungarian matching. This is a trained one-parameter refinement layer, not a claim of a deeper full T-OMP-Net.

## Run contract

- Research question: does source-trained bounded refinement improve channel NMSE and physical delay/projected-angle RMSE over grid FFT top-k on identical CDL samples?
- Null: transferred refinement does not improve the aggregate physical metrics over grid.
- Alternative: transferred refinement improves channel NMSE and at least one physical RMSE without materially degrading the other.
- Baseline: existing grid FFT top-k output in `run_sionna_cdl_profile_generalization.py`.
- Source model: mean learned alpha from the accepted five-seed Stage-2 G2 sweep.
- Dataset: Sionna CDL-A/C/D; unchanged channel generation and truth definitions.
- Required metrics: grid and trained-refinement channel NMSE, physical delay RMSE (ns), projected broadside-angle RMSE (deg), deltas, exact configuration, seeds, environment.
- Minimum evidence: one-profile/one-seed smoke produces finite and internally consistent metrics.
- Solid evidence: A/C/D multi-seed dev run with all required metrics and honest supported/inconclusive/refuted verdict.
- Maximum evidence: 5 seeds x 50 samples only after the dev result justifies the compute.
- Stop condition: durable CSV, manifest, evaluation summary, and claim boundary exist.
- Abandonment condition: unit/mapping inconsistency or systematic degradation invalidates transfer; record the negative result rather than tuning on test truth.

## Minimal code-change map

1. Add source-alpha loading and continuous 2-D bounded refinement to the existing Sionna evaluator.
2. Generalize physical matching from integer FFT support to continuous delay/angle bins.
3. Record paired grid/refinement metrics and a transfer-specific verdict.
4. Add focused unit tests for continuous-bin physical conversion and alpha interpolation.

## Follow-up analysis after mixed dev result

- Parent result: `05_results/sionna_cdl_trained_refinement_dev/`.
- Observed boundary: mean NMSE improves 3.54 dB and delay RMSE improves 5.27 ns, while projected-angle RMSE worsens 5.60 deg; CDL-D is negative overall and all 24 L=16 cells worsen in angle.
- Evidence question: is the angle failure mainly caused by applying the same learned alpha to both axes?
- Single diagnostic slice: keep delay alpha fixed at the source-trained value and set angle alpha to zero on the identical A/C/D dev contract.
- Fixed conditions: channel draws, seeds, SNRs, L values, support selection, matching, and metrics.
- Interpretation boundary: this is an axis-coupling ablation, not a trained paper estimator and not permission to tune on CDL truth.
- Execution envelope: CPU-only; Sionna/scipy/torch available; parent run is ~2 s and the one-slice replay is inexpensive.
- Stop condition: record whether angle degradation contracts and route either to a genuinely axis-specific trained model or away from refinement transfer.

## Axiswise source-training experiment

- Research question: can three independently bounded source-trained scales preserve local G2 gain and provide a legitimate frozen angle/delay transfer model?
- Null: axiswise training is locally unstable or offers no meaningful distinction from the shared-alpha model.
- Alternative: all held-out L cells retain at least 3 dB gain over grid and the learned axis parameters are reproducible enough to freeze without CDL tuning.
- Source data: the existing synthetic off-grid generator at 128x16x32, SNR 20 dB, L={2,4,8}; no CDL samples or truth enter training.
- External test: unchanged Sionna A/C/D physical contract, using source mean angle and delay alpha exactly once.
- Minimum: focused tests plus a 1-seed smoke.
- Solid: five source seeds with paired grid/shared-alpha comparisons, followed by the unchanged two-seed CDL dev contract.
- Stop: record supported, mixed, or refuted external result and update the paper evidence boundary.

## Static-axis outcome and model-class escalation

- Three static 3-D alphas collapsed to 0.6415/0.6422/0.6422 and improved only 0.00135 dB over shared alpha.
- Geometry-matched 64x4 static alphas also collapsed (delay 0.6401, angle 0.6413; separation -0.00123).
- Decision: do not spend on multi-seed static scaling or external replay; the global-constant model family is refuted for the coupling problem.
- Next hypothesis: estimator-internal sample features can identify when angle refinement is unsafe while retaining useful delay refinement.
- Next implementation: a small feature-conditioned controller with bounded delay/angle outputs, trained on 64x4 synthetic data using channel NMSE plus Hungarian permutation-invariant parameter loss.
- Acceptance: non-collapsed outputs, held-out NMSE gain, held-out physical-bin improvement on both axes, and no external truth in training/model selection.
