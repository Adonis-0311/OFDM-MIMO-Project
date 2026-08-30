from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from baseline.tensor_nomp import correlation_score_gradient_hessian
from data.offgrid_tensor import steering_axis, tensor_atom


def axiswise_quadratic_peak_bins(
    measurement: np.ndarray,
    coarse_bins: np.ndarray,
    *,
    maximum_offset_bins: float = 0.5,
) -> np.ndarray:
    """Three-point parabolic interpolation on each FFT axis.

    The other coordinates remain at the selected coarse bin while one axis is
    interpolated.  Non-concave or numerically flat triplets return zero offset.
    Periodic indexing matches the FFT support convention.
    """

    spectrum_power = np.abs(np.fft.fftn(measurement, norm="ortho")) ** 2
    shape = np.asarray(measurement.shape, dtype=int)
    coarse = np.asarray(coarse_bins, dtype=float)
    refined = coarse.copy()
    for row_index, row in enumerate(coarse):
        center = np.mod(np.rint(row).astype(int), shape)
        center_power = float(spectrum_power[tuple(center)])
        for axis in range(measurement.ndim):
            left = center.copy()
            right = center.copy()
            left[axis] = (left[axis] - 1) % shape[axis]
            right[axis] = (right[axis] + 1) % shape[axis]
            left_power = float(spectrum_power[tuple(left)])
            right_power = float(spectrum_power[tuple(right)])
            curvature = left_power - 2.0 * center_power + right_power
            scale = max(left_power, center_power, right_power, 1.0)
            if curvature >= -1e-14 * scale:
                offset = 0.0
            else:
                offset = 0.5 * (left_power - right_power) / curvature
                offset = float(np.clip(offset, -maximum_offset_bins, maximum_offset_bins))
            refined[row_index, axis] = row[axis] + offset
    return np.mod(refined, shape.astype(float))


@dataclass(frozen=True)
class AxiswiseCandanResult:
    bins: np.ndarray
    offsets: np.ndarray
    unclipped_offsets: np.ndarray
    denominator_stability: np.ndarray
    minimum_denominator_stability: float
    mean_denominator_stability: float
    maximum_absolute_unclipped_offset: float
    clipping_rate: float


def axiswise_candan_diagnostics(
    measurement: np.ndarray,
    coarse_bins: np.ndarray,
    *,
    maximum_offset_bins: float = 0.5,
) -> AxiswiseCandanResult:
    """Apply Candan's estimator and retain observation-only diagnostics.

    The complex FFT coefficient at the selected peak and its two periodic
    neighbors define the update while the other coordinates stay fixed. The
    finite-length correction ``tan(pi/N)/(pi/N)`` is applied separately for
    each axis; the caller performs the common downstream joint LS fit.  The
    normalized denominator magnitude is bounded in ``[0, 1]`` by the triangle
    inequality and exposes locally flat or cancellation-prone triplets without
    using clean-channel or parameter truth.
    """

    spectrum = np.fft.fftn(measurement, norm="ortho")
    shape = np.asarray(measurement.shape, dtype=int)
    coarse = np.asarray(coarse_bins, dtype=float)
    refined = coarse.copy()
    offsets = np.zeros_like(coarse, dtype=float)
    unclipped_offsets = np.zeros_like(coarse, dtype=float)
    denominator_stability = np.zeros_like(coarse, dtype=float)
    for row_index, row in enumerate(coarse):
        center = np.mod(np.rint(row).astype(int), shape)
        center_value = complex(spectrum[tuple(center)])
        for axis in range(measurement.ndim):
            left = center.copy()
            right = center.copy()
            left[axis] = (left[axis] - 1) % shape[axis]
            right[axis] = (right[axis] + 1) % shape[axis]
            left_value = complex(spectrum[tuple(left)])
            right_value = complex(spectrum[tuple(right)])
            denominator = 2.0 * center_value - left_value - right_value
            triplet_scale = (
                abs(left_value) + 2.0 * abs(center_value) + abs(right_value)
            )
            denominator_stability[row_index, axis] = abs(denominator) / max(
                triplet_scale, 1e-300
            )
            numerical_scale = max(
                abs(left_value), abs(center_value), abs(right_value), 1.0
            )
            if abs(denominator) <= 1e-14 * numerical_scale:
                raw_offset = 0.0
            else:
                correction = np.tan(np.pi / shape[axis]) / (np.pi / shape[axis])
                raw_offset = float(
                    correction * np.real((left_value - right_value) / denominator)
                )
            offset = float(
                np.clip(raw_offset, -maximum_offset_bins, maximum_offset_bins)
            )
            offsets[row_index, axis] = offset
            unclipped_offsets[row_index, axis] = raw_offset
            refined[row_index, axis] = row[axis] + offset
    absolute_unclipped = np.abs(unclipped_offsets)
    return AxiswiseCandanResult(
        bins=np.mod(refined, shape.astype(float)),
        offsets=offsets,
        unclipped_offsets=unclipped_offsets,
        denominator_stability=denominator_stability,
        minimum_denominator_stability=float(np.min(denominator_stability)),
        mean_denominator_stability=float(np.mean(denominator_stability)),
        maximum_absolute_unclipped_offset=float(np.max(absolute_unclipped)),
        clipping_rate=float(
            np.mean(absolute_unclipped > maximum_offset_bins + 1e-12)
        ),
    )


def axiswise_candan_bins(
    measurement: np.ndarray,
    coarse_bins: np.ndarray,
    *,
    maximum_offset_bins: float = 0.5,
) -> np.ndarray:
    """Return only the Candan-refined bins for comparator call sites."""

    return axiswise_candan_diagnostics(
        measurement,
        coarse_bins,
        maximum_offset_bins=maximum_offset_bins,
    ).bins


@dataclass(frozen=True)
class SeparableCartesianResult:
    bins: np.ndarray
    selected_offsets: np.ndarray
    minimum_normalized_margin: float
    mean_normalized_margin: float
    boundary_saturation_rate: float


def separable_cartesian_local_diagnostics(
    measurement: np.ndarray,
    coarse_bins: np.ndarray,
    *,
    search_radius: float = 0.45,
    search_points: int = 5,
) -> SeparableCartesianResult:
    """Evaluate the Cartesian local grid by separable tensor contraction.

    This is algebraically equivalent to forming every rank-one tensor atom and
    taking a full inner product, but it scores the complete local cube in one
    optimized contraction per selected neighborhood. C-order ``argmax`` keeps
    the lexicographic tie convention of ``itertools.product``.
    """

    if measurement.ndim != 3:
        raise ValueError("separable Cartesian refinement expects a third-order tensor")
    if search_points < 2:
        raise ValueError("search_points must be at least two")
    offsets = np.linspace(-search_radius, search_radius, search_points)
    shape = tuple(int(value) for value in measurement.shape)
    period = np.asarray(shape, dtype=float)
    refined: list[np.ndarray] = []
    selected_offsets: list[np.ndarray] = []
    margins: list[float] = []
    for coarse in np.asarray(coarse_bins, dtype=float):
        candidates = [
            np.stack([steering_axis(size, float(coarse[axis] + offset)) for offset in offsets])
            for axis, size in enumerate(shape)
        ]
        correlations = np.einsum(
            "ia,jt,kv,atv->ijk",
            candidates[0].conj(),
            candidates[1].conj(),
            candidates[2].conj(),
            measurement,
            optimize=True,
        )
        powers = np.abs(correlations) ** 2
        best = np.unravel_index(int(np.argmax(powers)), correlations.shape)
        best_offsets = offsets[np.asarray(best, dtype=int)]
        refined.append(np.mod(coarse + best_offsets, period))
        selected_offsets.append(best_offsets)
        flat_powers = powers.ravel()
        if flat_powers.size >= 2:
            top_two = np.partition(flat_powers, -2)[-2:]
            margin = float((np.max(top_two) - np.min(top_two)) / max(np.max(top_two), 1e-30))
        else:
            margin = 1.0
        margins.append(margin)
    selected_array = np.asarray(selected_offsets, dtype=float)
    boundary_rate = float(
        np.mean(np.isclose(np.abs(selected_array), search_radius, rtol=0.0, atol=1e-12))
    )
    return SeparableCartesianResult(
        bins=np.asarray(refined, dtype=float),
        selected_offsets=selected_array,
        minimum_normalized_margin=float(np.min(margins)),
        mean_normalized_margin=float(np.mean(margins)),
        boundary_saturation_rate=boundary_rate,
    )


def separable_cartesian_local_bins(
    measurement: np.ndarray,
    coarse_bins: np.ndarray,
    *,
    search_radius: float = 0.45,
    search_points: int = 5,
) -> np.ndarray:
    """Return bins from the optimized Cartesian local score cube."""

    return separable_cartesian_local_diagnostics(
        measurement,
        coarse_bins,
        search_radius=search_radius,
        search_points=search_points,
    ).bins


@dataclass(frozen=True)
class OneStepNewtonResult:
    bins: np.ndarray
    accepted_updates: int
    derivative_evaluations: int
    trial_score_evaluations: int


def _correlation_score(
    measurement: np.ndarray,
    shape: tuple[int, int, int],
    bins: np.ndarray,
) -> float:
    atom = tensor_atom(shape, tuple(float(value) for value in bins))
    return float(np.abs(np.vdot(atom, measurement)) ** 2)


def one_step_fixed_support_newton_bins(
    measurement: np.ndarray,
    coarse_bins: np.ndarray,
    *,
    maximum_step_bins: float = 0.45,
    line_search_steps: int = 5,
) -> OneStepNewtonResult:
    """Apply one safeguarded Newton direction to each fixed coarse peak.

    Each component uses the full observation, as does the Cartesian local
    comparator.  One gradient/Hessian evaluation defines the direction; a
    deterministic backtracking search accepts the first score-improving step.
    No residual deflation, support replacement, or repeated Newton iteration is
    performed.
    """

    if measurement.ndim != 3:
        raise ValueError("one-step fixed-support Newton expects a third-order tensor")
    if line_search_steps < 1:
        raise ValueError("line_search_steps must be positive")
    shape = tuple(int(value) for value in measurement.shape)
    period = np.asarray(shape, dtype=float)
    refined: list[np.ndarray] = []
    accepted_updates = 0
    trial_evaluations = 0
    for coarse in np.asarray(coarse_bins, dtype=float):
        initial = np.mod(coarse, period)
        score, gradient, hessian = correlation_score_gradient_hessian(
            measurement, shape, initial
        )
        if not np.all(np.isfinite(gradient)) or not np.all(np.isfinite(hessian)):
            refined.append(initial)
            continue
        step = -np.linalg.pinv(hessian, rcond=1e-10) @ gradient
        maximum = float(np.max(np.abs(step)))
        if not np.isfinite(maximum) or maximum == 0.0:
            refined.append(initial)
            continue
        if maximum > maximum_step_bins:
            step *= maximum_step_bins / maximum
        selected = initial
        tolerance = 1e-12 * max(score, 1.0)
        for backtrack in range(line_search_steps):
            candidate = np.mod(initial + (0.5**backtrack) * step, period)
            candidate_score = _correlation_score(measurement, shape, candidate)
            trial_evaluations += 1
            if candidate_score > score + tolerance:
                selected = candidate
                accepted_updates += 1
                break
        refined.append(selected)
    return OneStepNewtonResult(
        bins=np.asarray(refined, dtype=float),
        accepted_updates=accepted_updates,
        derivative_evaluations=len(refined),
        trial_score_evaluations=trial_evaluations,
    )
