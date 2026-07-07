# Analytic per-scene FLOP model (T1.1)

Implementation-independent operation counts for every matched-campaign method.
Conventions: one complex multiply = 6 real FLOPs, one complex add = 2; atom
synthesis (complex-exponential recurrence + scaling) = `C_ATOM = 8` real
FLOPs/sample; `N = Na·Nτ·Nν` (local 3-D: 128·16·32 = 65 536); split-radix FFT
= `5N log2 N`; complex LS with k columns (QR) = `8Nk² + (8/3)k³`.
Executable form: `04_experiments/matlab/common/flops_model.m`. Plug-in values:
`05_results/matlab_taes_supplement/complexity_table.csv` (MATLAB campaign) and
`flops_paper_pareto.csv` (paper five-seed campaign axes).

## Formulas

**Grid Tensor-OMP** (FFT support + one joint LS):
`C_grid = 5N log2 N + L·C_ATOM·N + LS(L)`

**Deterministic local refinement** (P=5 points/axis, separable contraction per component):
`C_search = P·C_ATOM·Na + P·2N + P²(C_ATOM·Nτ + 2NτNν) + P³(C_ATOM·Nν + 2Nν)`
`C_det = C_grid + L·C_search + LS(L)`

**Learned scalar** (bounded interpolation + LS rebuild):
`C_scalar = C_det + 1 + 6L + L·C_ATOM·N + LS(L)`
Inference cost of the learned parameter itself: **1 FLOP**.

**Learned CDL controller** (10→16→2 MLP):
`C_ctrl = C_det + C_features + 2(10·16 + 16·2) + 6L + L·C_ATOM·N + LS(L)`
Inference cost of the controller: **≈ 384 FLOPs/scene** — 4–7 orders of
magnitude below the classical support-selection and refinement stages it
augments.

**NOMP-inspired path** (detect → safeguarded Newton → cyclic, LS-gated):
gradient/Hessian evaluation `C_ghe = 3(C_ATOM·Na + 2N) + 9·2NτNν + 54Nν`
(ten separable weighted contractions; the three angle-stage contractions dominate),
`C_NOMP = Σ_{t=1..L} [5N log2 N + P³·2N + R·(C_ghe·(1+B) + C_pinv) + R·LS(t) + t·C_ATOM·N]`
with `R` = accepted Newton updates per target (measured from executed runs),
`B ≈ 1.5` mean backtracking evaluations, `C_pinv ≈ 200` (3×3 pseudo-inverse).
Accuracy therefore scales with an iteration count whose cost multiplies both
`C_ghe` and a growing `LS(t)` — this is the structural origin of the
compute–accuracy trade, not an implementation artifact.

**PARAFAC-ALS** (S = 10 fixed sweeps):
`C_ALS = S·Σ_d [ (N/nd)·L·6 + 8·nd·(N/nd)·L + 48L² + (8/3)L³ + 8·nd·L² ] + 8NL`

## Plug-in result (128×16×32, P=5, measured R)

| Method | mean FLOPs (L∈{2,4,8}) | ratio vs Local |
|---|---|---|
| Grid | 2.24×10⁷ | 0.55× |
| Local (deterministic) | 4.05×10⁷ | 1× |
| Learned scalar | 5.76×10⁷ | 1.42× |
| PARAFAC-ALS | 7.82×10⁷ | 1.93× |
| NOMP-inspired | 2.87×10⁸ | **7.1×** |

The analytic 7.1× NOMP/Local ratio reproduces the measured 8.1× median
wall-clock ratio ordering (same campaign), which validates the model at the
level used in the paper: ordering and order-of-magnitude, not cycle accuracy.

## What the model surfaces

1. The learned-inference increment (1 FLOP scalar; 384 FLOP controller) is
   negligible against every classical stage — "learning" adds adaptivity at
   near-zero marginal compute.
2. The learned path's extra cost over the deterministic candidate is one LS
   rebuild + L atom evaluations (≈1.4×), not the learning itself.
3. NOMP's accuracy is bought with per-target Newton iterations whose LS gate
   grows with the active support: cost scales superlinearly in L.
