from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from baseline.sparse_recovery import OMPResult, nmse_db, omp
from data.set_a_generator import SetASample, unravel_index


@dataclass(frozen=True)
class TensorOMPMetrics:
    nmse_db: float
    support_recall: float
    angle_rmse_bins: float
    delay_rmse_bins: float
    doppler_rmse_bins: float
    residual_norm: float


def run_tensor_omp(sample: SetASample, max_iters: Optional[int] = None) -> OMPResult:
    n_targets = len(sample.truth.targets)
    return omp(
        sample.dictionary,
        sample.measurement,
        max_iters=max_iters or n_targets,
        tol=np.sqrt(sample.noise_variance * sample.measurement.size) * 0.1,
    )


def evaluate_tensor_omp(sample: SetASample, result: OMPResult) -> TensorOMPMetrics:
    true_support = set(np.flatnonzero(sample.truth.sparse_coefficients))
    est_support = set(result.support[: len(true_support)])
    recall = len(true_support & est_support) / max(len(true_support), 1)
    nmse = nmse_db(result.coefficients, sample.truth.sparse_coefficients)
    true_sorted = sorted(true_support)
    est_sorted = sorted(est_support)
    if not est_sorted:
        return TensorOMPMetrics(nmse, recall, float("inf"), float("inf"), float("inf"), result.residual_norm)
    pairs = list(zip(true_sorted, est_sorted[: len(true_sorted)]))
    errors = np.array(
        [
            np.subtract(
                unravel_index(sample.grid, int(est_idx)),
                unravel_index(sample.grid, int(true_idx)),
            )
            for true_idx, est_idx in pairs
        ],
        dtype=float,
    )
    rmse = np.sqrt(np.mean(errors**2, axis=0))
    return TensorOMPMetrics(
        nmse_db=nmse,
        support_recall=recall,
        angle_rmse_bins=float(rmse[0]),
        delay_rmse_bins=float(rmse[1]),
        doppler_rmse_bins=float(rmse[2]),
        residual_norm=result.residual_norm,
    )
