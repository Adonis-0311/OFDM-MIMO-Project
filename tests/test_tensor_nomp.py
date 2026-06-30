from __future__ import annotations

import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "03_active_modules"))

from baseline.tensor_nomp import (
    correlation_score_gradient_hessian,
    oversampled_residual_initialization,
    tensor_nomp_known_order,
)
from common.seed import seed_all
from data.offgrid_tensor import (
    estimate_from_bins_lstsq,
    generate_offgrid_tensor_sample,
    measurement_nmse_db,
    topk_grid_bins,
)


def _circular_delta(left: np.ndarray, right: np.ndarray, shape: tuple[int, ...]) -> np.ndarray:
    period = np.asarray(shape, dtype=float)
    return np.mod(left - right + period / 2.0, period) - period / 2.0


def test_correlation_derivatives_match_finite_differences() -> None:
    rng = seed_all(551)
    shape = (8, 5, 6)
    residual = rng.standard_normal(shape) + 1j * rng.standard_normal(shape)
    bins = np.array([2.3, 1.4, 4.2])
    _, gradient, hessian = correlation_score_gradient_hessian(residual, shape, bins)
    step = 1e-5
    numerical_gradient = np.empty(3)
    numerical_hessian = np.empty((3, 3))
    for axis in range(3):
        offset = np.zeros(3)
        offset[axis] = step
        plus = correlation_score_gradient_hessian(residual, shape, bins + offset)[0]
        minus = correlation_score_gradient_hessian(residual, shape, bins - offset)[0]
        numerical_gradient[axis] = (plus - minus) / (2.0 * step)
        plus_gradient = correlation_score_gradient_hessian(residual, shape, bins + offset)[1]
        minus_gradient = correlation_score_gradient_hessian(residual, shape, bins - offset)[1]
        numerical_hessian[:, axis] = (plus_gradient - minus_gradient) / (2.0 * step)
    np.testing.assert_allclose(gradient, numerical_gradient, rtol=2e-5, atol=2e-5)
    np.testing.assert_allclose(hessian, numerical_hessian, rtol=2e-5, atol=2e-5)


def test_single_target_nomp_improves_grid_and_tracks_offgrid_bins() -> None:
    sample = generate_offgrid_tensor_sample(
        rng=seed_all(552),
        shape=(16, 8, 10),
        n_targets=1,
        snr_db=60.0,
        offset_radius=0.35,
    )
    grid_bins = topk_grid_bins(sample.measurement, 1)
    grid = estimate_from_bins_lstsq(
        sample.measurement,
        sample.shape,
        [tuple(float(value) for value in grid_bins[0])],
    )
    result = tensor_nomp_known_order(sample.measurement, n_targets=1)
    truth = np.array([
        sample.targets[0].angle_bin + sample.targets[0].angle_offset,
        sample.targets[0].delay_bin + sample.targets[0].delay_offset,
        sample.targets[0].doppler_bin + sample.targets[0].doppler_offset,
    ])
    assert np.linalg.norm(_circular_delta(result.bins[0], truth, sample.shape)) < 0.02
    assert measurement_nmse_db(result.reconstruction, sample.clean) < measurement_nmse_db(grid, sample.clean) - 10.0


def test_oversampled_initialization_does_not_reduce_residual_correlation() -> None:
    sample = generate_offgrid_tensor_sample(
        rng=seed_all(554), shape=(12, 6, 8), n_targets=1, snr_db=50.0, offset_radius=0.35
    )
    coarse = np.asarray(topk_grid_bins(sample.measurement, 1)[0], dtype=float)
    initialized = oversampled_residual_initialization(
        sample.measurement, sample.shape, coarse, radius_bins=0.5, points=5
    )
    coarse_score = correlation_score_gradient_hessian(sample.measurement, sample.shape, coarse)[0]
    initialized_score = correlation_score_gradient_hessian(sample.measurement, sample.shape, initialized)[0]
    assert initialized_score >= coarse_score


def test_multi_target_nomp_has_monotone_accepted_residual_history() -> None:
    sample = generate_offgrid_tensor_sample(
        rng=seed_all(553),
        shape=(16, 8, 10),
        n_targets=3,
        snr_db=35.0,
        offset_radius=0.3,
    )
    result = tensor_nomp_known_order(sample.measurement, n_targets=3)
    history = np.asarray(result.residual_energy_history)
    assert result.bins.shape == (3, 3)
    assert result.reconstruction.shape == sample.shape
    assert np.all(np.diff(history) <= 1e-10 * np.maximum(history[:-1], 1.0))
    assert history[-1] < history[0]
