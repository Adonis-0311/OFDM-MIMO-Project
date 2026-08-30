from __future__ import annotations

import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
MODULES = ROOT / "03_active_modules"
if str(MODULES) not in sys.path:
    sys.path.insert(0, str(MODULES))

from baseline.local_refinement import (  # noqa: E402
    separable_cartesian_local_bins,
    separable_cartesian_local_diagnostics,
)
from common.tsp_revision_metrics import (  # noqa: E402
    apply_monotone_calibrator,
    average_precision,
    design_condition_number,
    distinct_pair_metrics,
    fit_monotone_quantile_calibrator,
    fourier_coherence_1d,
    matched_component_metrics,
    roc_auc,
    separable_fourier_coherence,
    support_quality_metrics,
)
from data.offgrid_tensor import tensor_atom  # noqa: E402


def test_fourier_coherence_matches_direct_atom_inner_product() -> None:
    shape = (8, 7, 6)
    delta = (0.31, -0.22, 0.47)
    first = tensor_atom(shape, (1.2, 2.1, 3.4))
    second = tensor_atom(shape, tuple(a + b for a, b in zip((1.2, 2.1, 3.4), delta)))
    direct = abs(np.vdot(first, second))
    predicted = separable_fourier_coherence(shape, delta)
    assert np.isclose(direct, predicted, atol=1e-12)
    assert np.isclose(fourier_coherence_1d(16, 0.0), 1.0)
    assert fourier_coherence_1d(16, 1.0) < 1e-12


def test_component_metrics_preserve_truth_identity() -> None:
    shape = (12, 10, 8)
    truth = np.array([[1.2, 2.2, 3.2], [7.3, 6.3, 5.3]])
    estimates = np.array([[7.4, 6.2, 5.1], [1.1, 2.3, 3.4]])
    metrics = matched_component_metrics(estimates, truth, shape)
    assert metrics["all_components_hit"]
    assert np.all(metrics["hits_by_truth"])
    assert metrics["per_component_hit_rate"] == 1.0


def test_support_quality_detects_duplicate_neighborhood() -> None:
    shape = (12, 10, 8)
    truth = np.array([[1.1, 2.1, 3.1], [7.2, 6.2, 5.2]])
    coarse = np.array([[1.0, 2.0, 3.0], [1.0, 2.0, 3.0]])
    metrics = support_quality_metrics(coarse, truth, shape)
    assert metrics["q_sup"] == 0.5
    assert metrics["duplicate_neighborhood_rate"] == 0.5


def test_distinct_pair_metrics_reward_separation_fidelity() -> None:
    shape = (12, 10, 8)
    truth = np.array([[1.2, 2.0, 3.0], [1.7, 2.0, 3.0], [8.0, 6.0, 5.0]])
    recovered = np.array([[1.18, 2.0, 3.0], [1.72, 2.0, 3.0], [8.0, 6.0, 5.0]])
    collapsed = np.array([[1.42, 2.0, 3.0], [1.48, 2.0, 3.0], [8.0, 6.0, 5.0]])
    good = distinct_pair_metrics(recovered, truth, shape)
    bad = distinct_pair_metrics(collapsed, truth, shape)
    assert good["distinct_pair_recovery"] == 1.0
    assert bad["distinct_pair_recovery"] == 0.0
    assert good["pair_separation_error_bins"] < bad["pair_separation_error_bins"]


def test_separable_diagnostics_wrap_existing_bins() -> None:
    shape = (8, 7, 6)
    truth = (2.35, 3.15, 1.55)
    measurement = tensor_atom(shape, truth)
    coarse = np.array([[2.0, 3.0, 2.0]])
    diagnostic = separable_cartesian_local_diagnostics(measurement, coarse)
    bins = separable_cartesian_local_bins(measurement, coarse)
    assert np.allclose(diagnostic.bins, bins)
    assert diagnostic.selected_offsets.shape == coarse.shape
    assert 0.0 <= diagnostic.minimum_normalized_margin <= 1.0
    assert 0.0 <= diagnostic.boundary_saturation_rate <= 1.0


def test_design_condition_matches_explicit_dictionary() -> None:
    shape = (8, 7, 6)
    bins = np.array([[1.2, 2.1, 3.4], [1.7, 4.2, 0.8]])
    design = np.stack([tensor_atom(shape, tuple(item)).reshape(-1) for item in bins], axis=1)
    assert np.isclose(design_condition_number(shape, bins), np.linalg.cond(design), rtol=1e-10)


def test_gate_discrimination_and_monotone_calibration() -> None:
    scores = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6])
    labels = np.array([0, 0, 0, 1, 1, 1])
    assert roc_auc(scores, labels) == 1.0
    assert average_precision(scores, labels) == 1.0
    calibrator = fit_monotone_quantile_calibrator(scores, labels, n_bins=3)
    probabilities = apply_monotone_calibrator(scores, calibrator)
    assert np.all(np.diff(probabilities) >= 0.0)
