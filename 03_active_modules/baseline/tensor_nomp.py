from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from itertools import product

import numpy as np

from data.offgrid_tensor import tensor_atom


@dataclass(frozen=True)
class TensorNOMPResult:
    """Result of the matched-budget 3-D cyclic NOMP-inspired baseline.

    This is a tensor extension of the detection/local-Newton/cyclic-feedback
    structure used by NOMP.  It is not a reproduction of the sparse-resource
    2-D OFDM implementation or its CFAR stopping rule.
    """

    bins: np.ndarray
    gains: np.ndarray
    reconstruction: np.ndarray
    residual: np.ndarray
    residual_energy_history: tuple[float, ...]
    newton_updates: int


@lru_cache(maxsize=8)
def _phase_coordinates(shape: tuple[int, int, int]) -> tuple[np.ndarray, ...]:
    coordinates = []
    for axis, axis_size in enumerate(shape):
        base = 2.0 * np.pi * np.arange(axis_size, dtype=float) / axis_size
        reshape = [1, 1, 1]
        reshape[axis] = axis_size
        coordinates.append(np.broadcast_to(base.reshape(reshape), shape).reshape(-1))
    return tuple(coordinates)


def correlation_score_gradient_hessian(
    residual: np.ndarray,
    shape: tuple[int, int, int],
    bins: np.ndarray,
) -> tuple[float, np.ndarray, np.ndarray]:
    """Return |a(b)^H r|^2 and its analytic first/second derivatives."""

    atom = tensor_atom(shape, tuple(float(value) for value in bins)).reshape(-1)
    residual_vec = np.asarray(residual, dtype=np.complex128).reshape(-1)
    coordinates = _phase_coordinates(shape)
    correlation = np.vdot(atom, residual_vec)
    first = np.asarray(
        [np.vdot(1j * coordinate * atom, residual_vec) for coordinate in coordinates],
        dtype=np.complex128,
    )
    second = np.empty((3, 3), dtype=np.complex128)
    for left in range(3):
        for right in range(3):
            second[left, right] = np.vdot(
                -coordinates[left] * coordinates[right] * atom,
                residual_vec,
            )
    score = float(np.abs(correlation) ** 2)
    gradient = 2.0 * np.real(np.conj(correlation) * first)
    hessian = 2.0 * np.real(
        np.conj(first)[:, None] * first[None, :]
        + np.conj(correlation) * second
    )
    return score, gradient.astype(float), hessian.astype(float)


def refine_frequency_newton(
    residual: np.ndarray,
    shape: tuple[int, int, int],
    initial_bins: np.ndarray,
    *,
    iterations: int = 5,
    max_step_bins: float = 0.5,
    line_search_steps: int = 6,
) -> tuple[np.ndarray, int]:
    """Maximize the single-atom residual correlation with safeguarded Newton steps."""

    bins = np.mod(np.asarray(initial_bins, dtype=float), np.asarray(shape, dtype=float))
    updates = 0
    score, _, _ = correlation_score_gradient_hessian(residual, shape, bins)
    for _ in range(iterations):
        _, gradient, hessian = correlation_score_gradient_hessian(residual, shape, bins)
        if not np.all(np.isfinite(gradient)) or not np.all(np.isfinite(hessian)):
            break
        step = -np.linalg.pinv(hessian, rcond=1e-10) @ gradient
        max_abs = float(np.max(np.abs(step)))
        if not np.isfinite(max_abs) or max_abs == 0.0:
            break
        if max_abs > max_step_bins:
            step *= max_step_bins / max_abs
        accepted = False
        for backtrack in range(line_search_steps):
            scale = 0.5**backtrack
            candidate = np.mod(bins + scale * step, np.asarray(shape, dtype=float))
            candidate_score, _, _ = correlation_score_gradient_hessian(
                residual, shape, candidate
            )
            tolerance = 1e-12 * max(score, 1.0)
            if candidate_score > score + tolerance:
                bins = candidate
                score = candidate_score
                updates += 1
                accepted = True
                break
        if not accepted:
            break
    return bins, updates


def _design_matrix(shape: tuple[int, int, int], bins: list[np.ndarray]) -> np.ndarray:
    return np.stack(
        [tensor_atom(shape, tuple(float(value) for value in item)).reshape(-1) for item in bins],
        axis=1,
    )


def oversampled_residual_initialization(
    residual: np.ndarray,
    shape: tuple[int, int, int],
    coarse_bins: np.ndarray,
    *,
    radius_bins: float = 0.5,
    points: int = 5,
) -> np.ndarray:
    """Select a residual-correlation maximum on a local oversampled grid."""

    if points < 1:
        raise ValueError("points must be positive")
    offsets = np.linspace(-radius_bins, radius_bins, points)
    period = np.asarray(shape, dtype=float)
    best = np.mod(np.asarray(coarse_bins, dtype=float), period)
    best_score = -np.inf
    residual_vec = np.asarray(residual, dtype=np.complex128).reshape(-1)
    for delta in product(offsets, repeat=3):
        candidate = np.mod(np.asarray(coarse_bins, dtype=float) + np.asarray(delta), period)
        atom = tensor_atom(shape, tuple(float(value) for value in candidate)).reshape(-1)
        score = float(np.abs(np.vdot(atom, residual_vec)) ** 2)
        if score > best_score:
            best_score = score
            best = candidate
    return best


def _least_squares_state(
    measurement: np.ndarray,
    shape: tuple[int, int, int],
    bins: list[np.ndarray],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    measurement_vec = np.asarray(measurement, dtype=np.complex128).reshape(-1)
    if not bins:
        residual = measurement_vec.copy()
        return np.empty(0, dtype=np.complex128), np.zeros_like(measurement_vec), residual, float(np.vdot(residual, residual).real)
    design = _design_matrix(shape, bins)
    gains, *_ = np.linalg.lstsq(design, measurement_vec, rcond=None)
    reconstruction = design @ gains
    residual = measurement_vec - reconstruction
    energy = float(np.vdot(residual, residual).real)
    return gains, reconstruction, residual, energy


def tensor_nomp_known_order(
    measurement: np.ndarray,
    *,
    n_targets: int,
    local_iterations: int = 5,
    cyclic_passes: int = 2,
    cyclic_iterations: int = 2,
    max_step_bins: float = 0.5,
    detection_oversampling_points: int = 5,
    detection_radius_bins: float = 0.5,
) -> TensorNOMPResult:
    """Run a known-order 3-D cyclic NOMP-inspired estimator.

    Each target is detected from the FFT of the current residual, locally
    Newton-refined, and followed by cyclic refinements of all active atoms.
    Every proposed frequency update is accepted only when joint LS residual
    energy decreases, making the recorded energy history monotone.
    """

    if measurement.ndim != 3:
        raise ValueError("tensor_nomp_known_order expects a third-order tensor")
    if n_targets < 1:
        raise ValueError("n_targets must be positive")
    shape = tuple(int(value) for value in measurement.shape)
    bins: list[np.ndarray] = []
    history: list[float] = []
    total_updates = 0
    gains, reconstruction, residual, energy = _least_squares_state(measurement, shape, bins)
    history.append(energy)

    for _ in range(n_targets):
        spectrum = np.fft.fftn(residual.reshape(shape), norm="ortho")
        coarse_flat = int(np.argmax(np.abs(spectrum)))
        coarse = np.asarray(np.unravel_index(coarse_flat, shape), dtype=float)
        initialized = oversampled_residual_initialization(
            residual,
            shape,
            coarse,
            radius_bins=detection_radius_bins,
            points=detection_oversampling_points,
        )
        bins.append(initialized)
        gains, reconstruction, residual, energy = _least_squares_state(measurement, shape, bins)
        history.append(energy)

        for pass_index in range(cyclic_passes + 1):
            indices = [len(bins) - 1] if pass_index == 0 else list(range(len(bins)))
            iterations = local_iterations if pass_index == 0 else cyclic_iterations
            for index in indices:
                design = _design_matrix(shape, bins)
                partial_residual = residual + gains[index] * design[:, index]
                proposal, updates = refine_frequency_newton(
                    partial_residual,
                    shape,
                    bins[index],
                    iterations=iterations,
                    max_step_bins=max_step_bins,
                )
                if updates == 0:
                    continue
                previous = bins[index].copy()
                bins[index] = proposal
                trial = _least_squares_state(measurement, shape, bins)
                trial_energy = trial[3]
                tolerance = 1e-12 * max(energy, 1.0)
                if trial_energy <= energy + tolerance:
                    gains, reconstruction, residual, energy = trial
                    total_updates += updates
                    history.append(energy)
                else:
                    bins[index] = previous

    gains, reconstruction, residual, energy = _least_squares_state(measurement, shape, bins)
    history.append(energy)
    return TensorNOMPResult(
        bins=np.asarray(bins, dtype=float),
        gains=gains,
        reconstruction=reconstruction.reshape(shape),
        residual=residual.reshape(shape),
        residual_energy_history=tuple(history),
        newton_updates=total_updates,
    )
