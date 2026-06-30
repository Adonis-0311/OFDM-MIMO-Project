from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "04_experiments" / "eval"))

from run_sionna_cdl_trained_refinement import (
    bins_to_physical,
    interpolate_bins,
    interpolate_bins_axiswise,
    physical_path_metrics_from_bins,
)


def test_interpolate_bins_applies_fixed_source_layer() -> None:
    coarse = np.asarray([[1.0, 3.0], [7.0, 0.0]])
    refined = np.asarray([[1.5, 2.5], [6.5, -0.5]])
    np.testing.assert_allclose(
        interpolate_bins(coarse, refined, 0.6),
        np.asarray([[1.3, 2.7], [6.7, -0.3]]),
    )


def test_axiswise_interpolation_can_freeze_angle_refinement() -> None:
    coarse = np.asarray([[1.0, 3.0]])
    refined = np.asarray([[1.5, 2.5]])
    np.testing.assert_allclose(
        interpolate_bins_axiswise(
            coarse,
            refined,
            delay_alpha=0.6,
            angle_alpha=0.0,
        ),
        np.asarray([[1.3, 3.0]]),
    )


def test_continuous_bins_convert_to_delay_and_wrapped_spatial_frequency() -> None:
    bins = np.asarray([[-0.5, 3.5], [1.0, -0.5]])
    delays, spatial = bins_to_physical(
        bins,
        shape=(8, 4),
        subcarrier_spacing_hz=100.0,
    )
    np.testing.assert_allclose(delays, np.asarray([0.5 / 800.0, 7.0 / 800.0]))
    np.testing.assert_allclose(spatial, np.asarray([-0.125, -0.125]))


def test_physical_metric_is_zero_for_exact_continuous_bins() -> None:
    shape = (8, 4)
    spacing = 100.0
    bins = np.asarray([[-0.4, 0.8], [-1.2, -0.6]])
    delays, spatial = bins_to_physical(bins, shape=shape, subcarrier_spacing_hz=spacing)
    metrics = physical_path_metrics_from_bins(
        estimated_bins=bins,
        shape=shape,
        truth_delays_s=delays,
        truth_spatial_frequencies=spatial,
        truth_path_powers=np.asarray([2.0, 1.0]),
        subcarrier_spacing_hz=spacing,
    )
    assert metrics["physical_delay_rmse_ns"] < 1e-6
    assert metrics["projected_broadside_angle_rmse_deg"] < 1e-10
