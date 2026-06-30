from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class OMPResult:
    coefficients: np.ndarray
    support: tuple[int, ...]
    residual_norm: float
    n_iters: int


def omp(
    dictionary: np.ndarray,
    measurement: np.ndarray,
    *,
    max_iters: int,
    tol: float = 1e-10,
) -> OMPResult:
    if max_iters < 1:
        raise ValueError("max_iters must be positive.")
    residual = measurement.copy()
    support: list[int] = []
    coefficients = np.zeros(dictionary.shape[1], dtype=np.complex128)
    for _ in range(max_iters):
        correlations = np.abs(dictionary.conj().T @ residual)
        if support:
            correlations[np.array(support)] = -np.inf
        next_idx = int(np.argmax(correlations))
        support.append(next_idx)
        active = dictionary[:, support]
        active_coef, *_ = np.linalg.lstsq(active, measurement, rcond=None)
        residual = measurement - active @ active_coef
        if np.linalg.norm(residual) <= tol:
            break
    coefficients[np.array(support)] = active_coef
    return OMPResult(
        coefficients=coefficients,
        support=tuple(support),
        residual_norm=float(np.linalg.norm(residual)),
        n_iters=len(support),
    )


def nmse_db(estimate: np.ndarray, reference: np.ndarray) -> float:
    denom = float(np.linalg.norm(reference) ** 2)
    if denom <= 0:
        return float("nan")
    nmse = float(np.linalg.norm(estimate - reference) ** 2 / denom)
    return 10.0 * np.log10(max(nmse, 1e-300))

