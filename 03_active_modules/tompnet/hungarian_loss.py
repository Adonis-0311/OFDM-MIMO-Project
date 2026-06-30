from __future__ import annotations

from itertools import permutations

import numpy as np


def permutation_invariant_mse(
    predicted: np.ndarray,
    target: np.ndarray,
) -> float:
    predicted = np.asarray(predicted, dtype=float)
    target = np.asarray(target, dtype=float)
    if predicted.shape != target.shape:
        raise ValueError("predicted and target must have the same shape.")
    if predicted.ndim != 2:
        raise ValueError("expected arrays with shape (n_targets, n_features).")
    n_targets = predicted.shape[0]
    if n_targets > 8:
        raise ValueError("brute-force permutation loss is intended for smoke tests with <=8 targets.")
    best = np.inf
    for order in permutations(range(n_targets)):
        diff = predicted[list(order)] - target
        loss = float(np.mean(diff**2))
        if loss < best:
            best = loss
    return best

