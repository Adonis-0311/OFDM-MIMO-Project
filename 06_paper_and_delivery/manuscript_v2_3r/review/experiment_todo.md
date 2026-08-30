# Review-Driven Experiment TODOs

Generated: 2026-06-29

## EXP-R1 — Integrated estimator identity gate

- Source issue: REV-001/REV-003.
- Matrix id: E11.
- Tier: main required if the paper retains “deep unfolding” or T-OMP-Net naming.
- Why current evidence is insufficient: the evaluated G2 layer has one scalar parameter, A4 is a deterministic radius schedule, and CDL uses a separate post-support controller.
- Minimum task: implement a K-stage estimator whose stage mapping is actually used in training and inference; attach the feature controller only if it participates in that executable path.
- Metrics: matched grid Tensor-OMP, bounded deterministic refinement, scalar layer, integrated K-stage model; NMSE, delay RMSE, projected-angle RMSE, parameters, operation count, CPU/GPU time.
- Success criterion: positive held-out gain over grid and scalar layer on at least one locked local and one CDL-A/C contract without hiding negative cells.
- Placement: main text.

## EXP-R2 — Matched classical accuracy comparators

- Source issue: REV-003.
- Matrix id: E12.
- Tier: main required for an NMSE--complexity Pareto claim; otherwise appendix optional.
- Why current evidence is insufficient: ESPRIT/PARAFAC rows are timing-only and use no matched physical accuracy contract.
- Minimum task: evaluate NOMP or reviewed continuous refinement, separable ESPRIT, and PARAFAC-ALS on the same identifiable parameter contract where mathematically applicable.
- Metrics: channel NMSE, delay/angle RMSE, failure rate, operation proxy/profiler FLOPs, wall-clock.
- Success criterion: fair matched input, target budget, and stopping budget; report failures rather than dropping them.
- Placement: main or appendix depending on claim.

## EXP-R3 — Statistical strengthening

- Source issue: REV-003.
- Matrix id: E13.
- Tier: main required before submission.
- Minimum task: increase G2 held-out samples per L/seed and A4 cross-L seeds/samples; retain the same locked configuration and report seed- and sample-level uncertainty.
- Metrics: gain distribution, confidence interval, minimum cell, A4 savings/gap distribution.
- Success criterion: claim-direction confidence intervals remain positive for G2 and the scoped A4 gate remains inside its stated tolerance for L>=32 at 20 dB.
- Placement: main/appendix.

## EXP-R4 — DeepMIMO trained physical evaluation

- Source issue: external validity.
- Matrix id: E14.
- Tier: main optional after EXP-R1; appendix otherwise.
- Minimum task: run the selected integrated or explicitly named post-support controller on O1_60 with physical delay/angle truth and disjoint users.
- Metrics: channel NMSE, physical delay/angle RMSE, cell failures, support diagnostics.
- Success criterion: no proxy language; the exact trained path must match the manuscript method name.
- Placement: main if positive and comparable, otherwise limitation/appendix.

