# 5. Theoretical Analysis

The theory layer supports the method by clarifying when the proposed operations are meaningful. It does not prove that the learned estimator is globally optimal, and it does not turn the local synthetic evidence into external-channel validation. The useful theoretical message is narrower: local off-grid refinement is justified when coarse support is near-correct, unfolding depth trades reconstruction quality against computation, and the CRLB implementation is numerically consistent in a single-target high-SNR regime.

## 5.1 Support-Conditioned Off-Grid Mismatch

Grid sparse recovery separates the estimation problem into two coupled decisions: select the support and fit the coefficients. Bounded off-grid refinement acts on the second stage after coarse support selection. Its validity therefore depends on a support-correct or near-support-correct event. Denote this event by

```text
E_supp = { S_hat contains S* or d_H(S_hat, S*) <= 1 }.
```

On this event, the nearest grid atom is already associated with the correct physical component or a nearby component. A local Taylor expansion of the steering response then gives a quadratic mismatch term in the grid offset. Bounded refinement can reduce this grid-dominated term by searching within a local physical neighborhood, leaving residual error controlled by refinement error and noise.

The condition is part of the claim. If the coarse support is wrong, local off-grid refinement has no reason to recover the missing physical target by itself. This is why the method remains tied to Tensor-OMP support quality and why the manuscript reports Kruskal/on-grid sanity as supporting evidence rather than as a universal guarantee.

## 5.2 Depth-Identifiability Trade-Off

Unfolding depth creates a second trade-off. More refinement layers can reduce residual mismatch, but depth cannot remove identifiability limits or the noise floor. A conservative support-conditioned bound has the form

```text
E[NMSE_K | E_supp] <= C1 exp(-beta K) + C2 Psi(L,L_max) + C3 sigma^2,
Psi(L,L_max) = L^2 / (L_max - L + epsilon)^2.
```

The terms have distinct roles. The first term describes the diminishing return from additional refinement depth. The second term grows as the target count approaches the identifiability limit. The third term is the noise floor. This structure makes depth a trade-off variable rather than an unbounded source of improvement.

The operational objective used by the early-stop mechanism is

```text
J(K) = E[NMSE_K] + lambda_FLOPs K.
```

This objective supports plateau-based early stopping: once incremental NMSE improvement is small relative to the computational cost of another layer, stopping can be rational. It does not imply a closed-form globally optimal K for every L or SNR. The SNR sensitivity result in Section 6 confirms the need for this caution, because the current scalar gate does not clear all SNR cells.

## 5.3 CRLB Consistency Check

The CRLB analysis checks whether the analytic 5L Fisher information implementation is internally consistent and whether the estimator follows the expected high-SNR trend in a simple setting. The current evidence gives a maximum analytic-versus-finite-difference FIM relative error of 5.73e-10, a 30 dB mean RMSE/CRLB ratio of 1.0067, and a mean absolute slope error of 0.0067 relative to the expected high-SNR scaling.

This supports a theory-validation bridge: the derivative implementation is numerically sound, and the single-target estimator follows the expected trend at high SNR. It does not prove tightness in the full multi-target CRLB regime, nor does it replace larger Monte Carlo validation under external channel models.

## 5.4 Consequences for the Paper Claims

The theoretical arguments justify three bounded claims:

1. Bounded off-grid refinement is meaningful when coarse sparse support is correct or near-correct.
2. Early stopping is a computation-quality trade-off, not an unrestricted depth-selection theorem.
3. The CRLB machinery is credible as a single-target high-SNR consistency check.

These claims align with the local and CDL evidence. They also explain the remaining limitations: unseen-profile transfer, ray-traced physical validation, broad SNR robustness, hardware-impairment training, and full multi-target CRLB tightness remain outside the supported scope.
