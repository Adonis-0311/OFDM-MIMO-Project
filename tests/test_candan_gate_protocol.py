from __future__ import annotations

from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "03_active_modules"))
sys.path.insert(0, str(ROOT / "04_experiments" / "eval"))

from data.offgrid_tensor import generate_offgrid_tensor_sample  # noqa: E402
from run_tsp_candan_gate_protocol_audit import calibrate  # noqa: E402
from run_tsp_crossfit_predictive_gate import balanced_random_folds  # noqa: E402
from run_tsp_projection_gate_runtime import identity_audit  # noqa: E402


def test_projection_energy_matches_explicit_residual() -> None:
    rng = np.random.default_rng(20260829)
    sample = generate_offgrid_tensor_sample(
        rng=rng, shape=(24, 8, 10), n_targets=3, snr_db=10.0,
        offset_radius=0.35,
    )
    result = identity_audit(sample.measurement, 3)
    assert result["explicit_projection_abs_error"] < 1e-12
    assert result["projection_qr_abs_error"] < 1e-12


def test_balanced_random_folds_are_deterministic_and_disjoint() -> None:
    first = balanced_random_folds((64, 4), 12345)
    second = balanced_random_folds((64, 4), 12345)
    np.testing.assert_array_equal(first, second)
    assert np.sum(first == 0) == 128
    assert np.sum(first == 1) == 128


def test_gate_calibration_uses_only_supplied_rows() -> None:
    rows = [
        {"candan_residual_reduction_fraction": -0.2, "candan_gain_vs_grid_db": -1.0},
        {"candan_residual_reduction_fraction": 0.1, "candan_gain_vs_grid_db": 2.0},
        {"candan_residual_reduction_fraction": 0.2, "candan_gain_vs_grid_db": 3.0},
    ]
    rule = calibrate(rows)
    assert rule["threshold"] > -0.2
    assert rule["validation_gated_gain_db"] == 5.0 / 3.0
