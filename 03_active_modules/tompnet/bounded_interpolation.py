"""Unified feature-conditioned bounded interpolation (T4.1).

One interface, two instances:
  * ConstantController  -- the local 3-D scalar model (axis-shared constant);
  * MLPController       -- the 10->16->2 CDL feature controller.

The scalar path is the degenerate controller whose output ignores features.
Numerical outputs are regression-tested against the historical implementations
(tests/test_bounded_interpolation.py); this module changes packaging, not
results. Torch is optional: MLPController accepts plain numpy weights, e.g.
loaded via common.torchless_checkpoint.load_pt.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol

import numpy as np

ALPHA_BOUND = 1.2


class Controller(Protocol):
    def alphas(self, features: Optional[np.ndarray], n_axes: int) -> np.ndarray:
        """Return per-axis interpolation scales in (0, ALPHA_BOUND)."""


@dataclass(frozen=True)
class ConstantController:
    """Degenerate instance: constant, axis-shared (or per-axis) scale."""
    alpha: float | tuple[float, ...]

    def alphas(self, features: Optional[np.ndarray], n_axes: int) -> np.ndarray:
        value = np.asarray(self.alpha, dtype=float)
        if value.ndim == 0:
            return np.full(n_axes, float(value))
        if value.size != n_axes:
            raise ValueError("per-axis alpha size mismatch")
        return value.astype(float)


@dataclass(frozen=True)
class MLPController:
    """Feature-conditioned instance (10 -> hidden -> n_axes tanh MLP).

    Mirrors FeatureConditionedRefinementController.forward:
        alpha = ALPHA_BOUND * sigmoid(W2 tanh(W1 z + b1) + b2)
    with z standardized by (feature_mean, feature_std); zero stds are treated
    as unit scale, matching torch training where the constant feature
    contributes no gradient.
    """
    w1: np.ndarray
    b1: np.ndarray
    w2: np.ndarray
    b2: np.ndarray
    feature_mean: np.ndarray
    feature_std: np.ndarray

    @classmethod
    def from_checkpoint_entry(cls, entry: dict) -> "MLPController":
        sd = entry["state_dict"]
        return cls(
            w1=np.asarray(sd["network.0.weight"], dtype=float),
            b1=np.asarray(sd["network.0.bias"], dtype=float),
            w2=np.asarray(sd["network.2.weight"], dtype=float),
            b2=np.asarray(sd["network.2.bias"], dtype=float),
            feature_mean=np.asarray(entry["feature_mean"], dtype=float),
            feature_std=np.asarray(entry["feature_std"], dtype=float),
        )

    def alphas(self, features: Optional[np.ndarray], n_axes: int) -> np.ndarray:
        if features is None:
            raise ValueError("MLPController requires estimator features")
        std = np.where(self.feature_std > 0, self.feature_std, 1.0)
        z = (np.asarray(features, dtype=float) - self.feature_mean) / std
        h = np.tanh(self.w1 @ z + self.b1)
        logits = self.w2 @ h + self.b2
        out = ALPHA_BOUND / (1.0 + np.exp(-logits))
        if out.size != n_axes:
            raise ValueError("controller output does not match axis count")
        return out


def interpolate(
    coarse_bins: np.ndarray,
    refined_bins: np.ndarray,
    controller: Controller,
    *,
    features: Optional[np.ndarray] = None,
) -> np.ndarray:
    """b_hat = b0 + alpha (.) (b_star - b0), one call for both instances."""
    coarse = np.asarray(coarse_bins, dtype=float)
    refined = np.asarray(refined_bins, dtype=float)
    if coarse.shape != refined.shape:
        raise ValueError("coarse/refined shape mismatch")
    alphas = controller.alphas(features, coarse.shape[1])
    return coarse + alphas[None, :] * (refined - coarse)
