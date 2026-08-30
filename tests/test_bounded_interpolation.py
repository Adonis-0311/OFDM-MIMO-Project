"""Regression tests for the unified bounded-interpolation module (T4.1).

Gate: the unified interface must reproduce the historical scalar path
(tompnet.trainable.interpolate_bins) exactly, and the MLP instance must
reproduce the controller formula alpha = 1.2*sigmoid(W2 tanh(W1 z + b1) + b2)
with feature standardization. Pure numpy; torch not required.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "03_active_modules"))

from tompnet.bounded_interpolation import (  # noqa: E402
    ConstantController, MLPController, interpolate,
)
from tompnet.trainable import interpolate_bins  # noqa: E402


def test_constant_controller_matches_legacy_scalar():
    rng = np.random.default_rng(7)
    for _ in range(20):
        L = int(rng.integers(1, 9))
        coarse = rng.integers(0, 16, size=(L, 3)).astype(float)
        refined = coarse + rng.uniform(-0.45, 0.45, size=(L, 3))
        alpha = float(rng.uniform(0.0, 1.2))
        legacy = np.asarray(
            interpolate_bins(
                [tuple(map(int, c)) for c in coarse],
                [tuple(map(float, r)) for r in refined],
                alpha,
            )
        )
        unified = interpolate(coarse, refined, ConstantController(alpha))
        assert np.allclose(legacy, unified, rtol=0, atol=0), "scalar path drifted"


def test_constant_controller_per_axis():
    coarse = np.array([[2.0, 3.0]])
    refined = np.array([[2.4, 3.4]])
    out = interpolate(coarse, refined, ConstantController((0.5, 0.0)))
    assert np.allclose(out, [[2.2, 3.0]])


def test_mlp_controller_formula():
    rng = np.random.default_rng(11)
    w1 = rng.standard_normal((16, 10)); b1 = rng.standard_normal(16)
    w2 = rng.standard_normal((2, 16)); b2 = rng.standard_normal(2)
    mean = rng.standard_normal(10); std = np.abs(rng.standard_normal(10)) + 0.1
    std[-1] = 0.0  # constant feature -> unit scale
    ctl = MLPController(w1, b1, w2, b2, mean, std)
    z_raw = rng.standard_normal(10)
    safe = np.where(std > 0, std, 1.0)
    z = (z_raw - mean) / safe
    expect = 1.2 / (1.0 + np.exp(-(w2 @ np.tanh(w1 @ z + b1) + b2)))
    got = ctl.alphas(z_raw, 2)
    assert np.allclose(got, expect, rtol=1e-12)
    assert np.all((got > 0) & (got < 1.2))


def test_mlp_loads_from_paper_checkpoint_if_present():
    ckpt = Path(__file__).resolve().parents[1] / "05_results" / \
        "cdl_ac_alias_lock_3seed" / "selected_controller_checkpoint.pt"
    if not ckpt.exists():
        return
    from common.torchless_checkpoint import load_pt
    entry = load_pt(str(ckpt))["models"][0]
    ctl = MLPController.from_checkpoint_entry(entry)
    a = ctl.alphas(np.asarray(entry["feature_mean"], dtype=float), 2)
    assert a.shape == (2,) and np.all((a > 0) & (a < 1.2))
