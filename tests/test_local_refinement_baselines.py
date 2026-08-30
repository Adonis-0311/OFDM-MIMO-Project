from __future__ import annotations

from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "03_active_modules"))

from baseline.local_refinement import (  # noqa: E402
    axiswise_candan_bins,
    axiswise_candan_diagnostics,
    axiswise_quadratic_peak_bins,
    one_step_fixed_support_newton_bins,
    separable_cartesian_local_bins,
)
from data.offgrid_tensor import refine_bins_local, tensor_atom  # noqa: E402


def circular_error(estimate: np.ndarray, truth: np.ndarray, shape: tuple[int, ...]) -> np.ndarray:
    period = np.asarray(shape, dtype=float)
    return np.mod(estimate - truth + period / 2.0, period) - period / 2.0


def test_axiswise_quadratic_peak_moves_toward_single_tone() -> None:
    shape = (32, 12, 16)
    truth = np.asarray([7.22, 4.18, 11.27])
    measurement = tensor_atom(shape, tuple(truth))
    coarse = np.asarray([[7.0, 4.0, 11.0]])
    refined = axiswise_quadratic_peak_bins(measurement, coarse)
    assert np.linalg.norm(circular_error(refined[0], truth, shape)) < np.linalg.norm(
        circular_error(coarse[0], truth, shape)
    )
    assert np.max(np.abs(circular_error(refined[0], coarse[0], shape))) <= 0.5 + 1e-12


def test_axiswise_candan_recovers_single_tone_offset() -> None:
    shape = (32, 12, 16)
    truth = np.asarray([7.22, 4.18, 11.27])
    measurement = tensor_atom(shape, tuple(truth))
    coarse = np.asarray([[7.0, 4.0, 11.0]])
    refined = axiswise_candan_bins(measurement, coarse)
    assert np.linalg.norm(circular_error(refined[0], truth, shape)) < 2e-3
    assert np.max(np.abs(circular_error(refined[0], coarse[0], shape))) <= 0.5 + 1e-12


def test_axiswise_candan_diagnostics_are_observable_and_consistent() -> None:
    shape = (32, 12, 16)
    truth = np.asarray([7.22, 4.18, 11.27])
    measurement = tensor_atom(shape, tuple(truth))
    coarse = np.asarray([[7.0, 4.0, 11.0]])
    result = axiswise_candan_diagnostics(measurement, coarse)
    np.testing.assert_allclose(result.bins, axiswise_candan_bins(measurement, coarse))
    assert result.offsets.shape == coarse.shape
    assert result.unclipped_offsets.shape == coarse.shape
    assert result.denominator_stability.shape == coarse.shape
    assert 0.0 <= result.minimum_denominator_stability <= 1.0
    assert 0.0 <= result.mean_denominator_stability <= 1.0
    assert result.clipping_rate == 0.0


def test_one_step_newton_is_bounded_and_improves_single_tone_score() -> None:
    shape = (32, 12, 16)
    truth = np.asarray([7.22, 4.18, 11.27])
    measurement = tensor_atom(shape, tuple(truth))
    coarse = np.asarray([[7.0, 4.0, 11.0]])
    result = one_step_fixed_support_newton_bins(measurement, coarse)
    coarse_score = abs(np.vdot(tensor_atom(shape, tuple(coarse[0])), measurement)) ** 2
    refined_score = abs(np.vdot(tensor_atom(shape, tuple(result.bins[0])), measurement)) ** 2
    assert refined_score >= coarse_score - 1e-12
    assert np.max(np.abs(circular_error(result.bins[0], coarse[0], shape))) <= 0.45 + 1e-12
    assert result.derivative_evaluations == 1


def test_separable_cartesian_matches_direct_enumeration() -> None:
    shape = (12, 7, 9)
    truth = (3.21, 4.16, 6.29)
    measurement = tensor_atom(shape, truth)
    coarse = np.asarray([[3.0, 4.0, 6.0]])
    direct = np.asarray(
        refine_bins_local(
            measurement,
            shape,
            [(3, 4, 6)],
            search_radius=0.45,
            search_points=5,
        )
    )
    separable = separable_cartesian_local_bins(
        measurement,
        coarse,
        search_radius=0.45,
        search_points=5,
    )
    np.testing.assert_allclose(separable, direct, atol=1e-12, rtol=0.0)
