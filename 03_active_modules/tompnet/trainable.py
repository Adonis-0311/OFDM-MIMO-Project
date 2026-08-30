from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from data.offgrid_tensor import (
    OffgridTensorSample,
    estimate_from_bins_lstsq,
    measurement_nmse_db,
    refine_bins_local,
    topk_grid_bins,
)


@dataclass(frozen=True)
class CalibrationResult:
    alpha: float
    train_nmse_db: float


def interpolate_bins(
    coarse_bins: list[tuple[int, int, int]],
    refined_bins: list[tuple[float, float, float]],
    alpha: float,
) -> list[tuple[float, float, float]]:
    calibrated: list[tuple[float, float, float]] = []
    for coarse, refined in zip(coarse_bins, refined_bins):
        calibrated.append(
            tuple(float(c + alpha * (r - c)) for c, r in zip(coarse, refined))
        )
    return calibrated


def evaluate_calibrated_refinement(
    sample: OffgridTensorSample,
    *,
    n_targets: int,
    alpha: float,
    search_radius: float = 0.45,
    search_points: int = 5,
) -> float:
    coarse = topk_grid_bins(sample.measurement, n_targets)
    refined = refine_bins_local(
        sample.measurement,
        sample.shape,
        coarse,
        search_radius=search_radius,
        search_points=search_points,
    )
    bins = interpolate_bins(coarse, refined, alpha)
    estimate = estimate_from_bins_lstsq(sample.measurement, sample.shape, bins)
    return measurement_nmse_db(estimate, sample.clean)


def train_alpha_grid(
    samples: list[OffgridTensorSample],
    *,
    n_targets: int,
    candidate_alphas: np.ndarray,
    search_radius: float = 0.45,
    search_points: int = 5,
) -> CalibrationResult:
    best_alpha = float(candidate_alphas[0])
    best_score = np.inf
    for alpha in candidate_alphas:
        values = [
            evaluate_calibrated_refinement(
                sample,
                n_targets=n_targets,
                alpha=float(alpha),
                search_radius=search_radius,
                search_points=search_points,
            )
            for sample in samples
        ]
        score = float(np.mean(values))
        if score < best_score:
            best_score = score
            best_alpha = float(alpha)
    return CalibrationResult(alpha=best_alpha, train_nmse_db=best_score)

