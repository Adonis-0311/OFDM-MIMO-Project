from __future__ import annotations

from dataclasses import dataclass
from itertools import product

import numpy as np


@dataclass(frozen=True)
class OffgridTarget:
    angle_bin: int
    delay_bin: int
    doppler_bin: int
    angle_offset: float
    delay_offset: float
    doppler_offset: float
    gain: complex


@dataclass(frozen=True)
class OffgridTensorSample:
    measurement: np.ndarray
    clean: np.ndarray
    targets: tuple[OffgridTarget, ...]
    noise_variance: float
    snr_db: float
    shape: tuple[int, int, int]


@dataclass(frozen=True)
class SingleTargetEstimate:
    bins: tuple[float, float, float]
    gain: complex
    score: float


def steering_axis(n: int, frequency_bin: float) -> np.ndarray:
    idx = np.arange(n, dtype=float)
    return np.exp(2j * np.pi * idx * frequency_bin / n) / np.sqrt(n)


def tensor_atom(shape: tuple[int, int, int], bins: tuple[float, float, float]) -> np.ndarray:
    angle = steering_axis(shape[0], bins[0])
    delay = steering_axis(shape[1], bins[1])
    doppler = steering_axis(shape[2], bins[2])
    return angle[:, None, None] * delay[None, :, None] * doppler[None, None, :]


def synthesize_offgrid_clean(shape: tuple[int, int, int], targets: tuple[OffgridTarget, ...]) -> np.ndarray:
    clean = np.zeros(shape, dtype=np.complex128)
    for target in targets:
        bins = (
            target.angle_bin + target.angle_offset,
            target.delay_bin + target.delay_offset,
            target.doppler_bin + target.doppler_offset,
        )
        clean += target.gain * tensor_atom(shape, bins)
    return clean


def generate_offgrid_tensor_sample(
    *,
    rng: np.random.Generator,
    shape: tuple[int, int, int],
    n_targets: int,
    snr_db: float,
    offset_radius: float,
) -> OffgridTensorSample:
    n_atoms = int(np.prod(shape))
    support = rng.choice(n_atoms, size=n_targets, replace=False)
    gains = (rng.standard_normal(n_targets) + 1j * rng.standard_normal(n_targets)) / np.sqrt(2)
    offsets = rng.uniform(-offset_radius, offset_radius, size=(n_targets, 3))
    targets: list[OffgridTarget] = []
    for flat_index, gain, offset in zip(support, gains, offsets):
        angle_bin, rem = divmod(int(flat_index), shape[1] * shape[2])
        delay_bin, doppler_bin = divmod(rem, shape[2])
        targets.append(
            OffgridTarget(
                angle_bin=angle_bin,
                delay_bin=delay_bin,
                doppler_bin=doppler_bin,
                angle_offset=float(offset[0]),
                delay_offset=float(offset[1]),
                doppler_offset=float(offset[2]),
                gain=complex(gain),
            )
        )
    clean = synthesize_offgrid_clean(shape, tuple(targets))
    signal_power = float(np.mean(np.abs(clean) ** 2))
    noise_variance = signal_power / (10 ** (snr_db / 10))
    noise = np.sqrt(noise_variance / 2) * (
        rng.standard_normal(shape) + 1j * rng.standard_normal(shape)
    )
    return OffgridTensorSample(
        measurement=clean + noise,
        clean=clean,
        targets=tuple(targets),
        noise_variance=noise_variance,
        snr_db=snr_db,
        shape=shape,
    )


def topk_grid_bins(measurement: np.ndarray, n_targets: int) -> list[tuple[int, int, int]]:
    matched = np.fft.fftn(measurement, norm="ortho")
    flat = matched.reshape(-1)
    support = np.argpartition(np.abs(flat), -n_targets)[-n_targets:]
    ordered = support[np.argsort(np.abs(flat[support]))[::-1]]
    bins: list[tuple[int, int, int]] = []
    for flat_index in ordered:
        angle_bin, rem = divmod(int(flat_index), measurement.shape[1] * measurement.shape[2])
        delay_bin, doppler_bin = divmod(rem, measurement.shape[2])
        bins.append((angle_bin, delay_bin, doppler_bin))
    return bins


def estimate_from_bins(
    measurement: np.ndarray,
    shape: tuple[int, int, int],
    bins: list[tuple[float, float, float]],
) -> np.ndarray:
    estimate = np.zeros(shape, dtype=np.complex128)
    for bin_triplet in bins:
        atom = tensor_atom(shape, bin_triplet)
        gain = np.vdot(atom, measurement)
        estimate += gain * atom
    return estimate


def estimate_from_bins_lstsq(
    measurement: np.ndarray,
    shape: tuple[int, int, int],
    bins: list[tuple[float, float, float]],
) -> np.ndarray:
    if not bins:
        return np.zeros(shape, dtype=np.complex128)
    atoms = [tensor_atom(shape, bin_triplet).reshape(-1) for bin_triplet in bins]
    design = np.stack(atoms, axis=1)
    gains, *_ = np.linalg.lstsq(design, measurement.reshape(-1), rcond=None)
    return (design @ gains).reshape(shape)


def refine_bins_local(
    measurement: np.ndarray,
    shape: tuple[int, int, int],
    coarse_bins: list[tuple[int, int, int]],
    *,
    search_radius: float,
    search_points: int,
) -> list[tuple[float, float, float]]:
    offsets = np.linspace(-search_radius, search_radius, search_points)
    refined: list[tuple[float, float, float]] = []
    for coarse in coarse_bins:
        best_score = -np.inf
        best_bins = tuple(float(value) for value in coarse)
        for delta in product(offsets, repeat=3):
            candidate = tuple(float(base + step) for base, step in zip(coarse, delta))
            atom = tensor_atom(shape, candidate)
            score = float(np.abs(np.vdot(atom, measurement)) ** 2)
            if score > best_score:
                best_score = score
                best_bins = candidate
        refined.append(best_bins)
    return refined


def estimate_single_target_multiresolution(
    measurement: np.ndarray,
    shape: tuple[int, int, int],
    *,
    search_points: int = 7,
    radii: tuple[float, ...] = (0.5, 0.12, 0.03, 0.006, 0.0012, 0.00024),
) -> SingleTargetEstimate:
    coarse = topk_grid_bins(measurement, 1)[0]
    center = tuple(float(value) for value in coarse)
    best_score = -np.inf
    best_bins = center
    for radius in radii:
        offsets = np.linspace(-radius, radius, search_points)
        for delta in product(offsets, repeat=3):
            candidate = tuple(base + step for base, step in zip(center, delta))
            atom = tensor_atom(shape, candidate)
            score = float(np.abs(np.vdot(atom, measurement)) ** 2)
            if score > best_score:
                best_score = score
                best_bins = candidate
        center = best_bins
    atom = tensor_atom(shape, best_bins)
    gain = complex(np.vdot(atom, measurement))
    return SingleTargetEstimate(bins=best_bins, gain=gain, score=best_score)


def measurement_nmse_db(estimate: np.ndarray, clean: np.ndarray) -> float:
    denom = float(np.linalg.norm(clean) ** 2)
    nmse = float(np.linalg.norm(estimate - clean) ** 2 / max(denom, 1e-300))
    return 10.0 * np.log10(max(nmse, 1e-300))
