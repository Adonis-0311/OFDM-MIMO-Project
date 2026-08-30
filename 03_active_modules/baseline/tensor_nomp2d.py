"""2-D (delay-angle) NOMP-inspired refinement for the CDL pipeline (T2.1).

Structure mirrors baseline/tensor_nomp.py (detect -> safeguarded Newton ->
cyclic re-refinement with joint-LS accept/reject) with the atom model and
Jacobian adapted to the 64x4 delay-angle geometry used by the CDL evaluator
(tompnet.feature_controller.atom_2d). Known-order variant; validated on
synthetic controlled offsets before use on CDL observations
(see 04_experiments/eval/run_nomp2d_validation.py).
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product

import numpy as np


@dataclass(frozen=True)
class Nomp2DResult:
    bins: np.ndarray
    gains: np.ndarray
    reconstruction: np.ndarray
    residual_energy: float
    newton_updates: int


def atom_2d(shape: tuple[int, int], bins: np.ndarray) -> np.ndarray:
    d = np.exp(2j * np.pi * np.arange(shape[0]) * bins[0] / shape[0]) / np.sqrt(shape[0])
    a = np.exp(2j * np.pi * np.arange(shape[1]) * bins[1] / shape[1]) / np.sqrt(shape[1])
    return d[:, None] * a[None, :]


def _design(shape, bins_list):
    return np.stack([atom_2d(shape, b).reshape(-1) for b in bins_list], axis=1)


def _score_grad_hess(residual_vec, shape, bins):
    """|a(b)^H r|^2 with analytic first/second derivatives (2x2)."""
    n0, n1 = shape
    w0 = 2.0 * np.pi * np.arange(n0) / n0
    w1 = 2.0 * np.pi * np.arange(n1) / n1
    d = np.exp(2j * np.pi * np.arange(n0) * bins[0] / n0) / np.sqrt(n0)
    a = np.exp(2j * np.pi * np.arange(n1) * bins[1] / n1) / np.sqrt(n1)
    R = residual_vec.reshape(shape)
    # contraction helper: sum conj(x)_i conj(y)_j R_ij
    def c(x, y):
        return np.conj(x) @ R @ np.conj(y)
    c00 = c(d, a)
    first = np.array([-1j * c(w0 * d, a), -1j * c(d, w1 * a)])
    second = np.array([
        [-c(w0 * w0 * d, a), -c(w0 * d, w1 * a)],
        [-c(w0 * d, w1 * a), -c(d, w1 * w1 * a)],
    ])
    score = float(np.abs(c00) ** 2)
    grad = 2.0 * np.real(np.conj(c00) * first)
    hess = 2.0 * np.real(np.conj(first)[:, None] * first[None, :] + np.conj(c00) * second)
    return score, grad, hess


def _newton(residual_vec, shape, bins, iterations, max_step=0.5):
    period = np.asarray(shape, dtype=float)
    bins = np.mod(np.asarray(bins, dtype=float), period)
    updates = 0
    score, _, _ = _score_grad_hess(residual_vec, shape, bins)
    for _ in range(iterations):
        _, grad, hess = _score_grad_hess(residual_vec, shape, bins)
        if not (np.all(np.isfinite(grad)) and np.all(np.isfinite(hess))):
            break
        step = -np.linalg.pinv(hess, rcond=1e-10) @ grad
        mx = float(np.max(np.abs(step)))
        if not np.isfinite(mx) or mx == 0.0:
            break
        if mx > max_step:
            step *= max_step / mx
        accepted = False
        for bt in range(6):
            cand = np.mod(bins + (0.5 ** bt) * step, period)
            cs, _, _ = _score_grad_hess(residual_vec, shape, cand)
            if cs > score + 1e-12 * max(score, 1.0):
                bins, score = cand, cs
                updates += 1
                accepted = True
                break
        if not accepted:
            break
    return bins, updates


def _ls_state(yvec, shape, bins_list):
    if not bins_list:
        r = yvec.copy()
        return np.empty(0, complex), np.zeros_like(yvec), r, float(np.vdot(r, r).real)
    A = _design(shape, bins_list)
    g, *_ = np.linalg.lstsq(A, yvec, rcond=None)
    rec = A @ g
    r = yvec - rec
    return g, rec, r, float(np.vdot(r, r).real)


def nomp2d_known_order(
    measurement: np.ndarray,
    *,
    n_targets: int,
    local_iterations: int = 5,
    cyclic_passes: int = 2,
    cyclic_iterations: int = 2,
    detection_points: int = 5,
    detection_radius: float = 0.5,
) -> Nomp2DResult:
    shape = measurement.shape
    yvec = measurement.reshape(-1).astype(complex)
    period = np.asarray(shape, dtype=float)
    bins_list: list[np.ndarray] = []
    total_updates = 0
    gains, rec, rvec, energy = _ls_state(yvec, shape, bins_list)
    offs = np.linspace(-detection_radius, detection_radius, detection_points)
    for _ in range(n_targets):
        spec = np.fft.fftn(rvec.reshape(shape), norm="ortho")
        coarse = np.asarray(np.unravel_index(int(np.argmax(np.abs(spec))), shape), dtype=float)
        best, best_score = np.mod(coarse, period), -np.inf
        for da, db in product(offs, repeat=2):
            cand = np.mod(coarse + np.asarray([da, db]), period)
            s = float(np.abs(np.vdot(atom_2d(shape, cand).reshape(-1), rvec)) ** 2)
            if s > best_score:
                best, best_score = cand, s
        bins_list.append(best)
        gains, rec, rvec, energy = _ls_state(yvec, shape, bins_list)
        for p in range(cyclic_passes + 1):
            idxs = [len(bins_list) - 1] if p == 0 else list(range(len(bins_list)))
            iters = local_iterations if p == 0 else cyclic_iterations
            for k in idxs:
                A = _design(shape, bins_list)
                partial = rvec + gains[k] * A[:, k]
                prop, upd = _newton(partial, shape, bins_list[k], iters)
                if upd == 0:
                    continue
                prev = bins_list[k].copy()
                bins_list[k] = prop
                trial = _ls_state(yvec, shape, bins_list)
                if trial[3] <= energy + 1e-12 * max(energy, 1.0):
                    gains, rec, rvec, energy = trial
                    total_updates += upd
                else:
                    bins_list[k] = prev
    gains, rec, rvec, energy = _ls_state(yvec, shape, bins_list)
    return Nomp2DResult(
        bins=np.asarray(bins_list),
        gains=gains,
        reconstruction=rec.reshape(shape),
        residual_energy=energy,
        newton_updates=total_updates,
    )
