from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Optional

import numpy as np

from common.config import GridConfig


@dataclass(frozen=True)
class TargetTruth:
    angle_index: int
    delay_index: int
    doppler_index: int
    gain: complex


@dataclass(frozen=True)
class ChannelTruth:
    targets: tuple[TargetTruth, ...]
    sparse_coefficients: np.ndarray


@dataclass(frozen=True)
class SetASample:
    measurement: np.ndarray
    dictionary: np.ndarray
    truth: ChannelTruth
    noise_variance: float
    snr_db: float
    grid: GridConfig


def dft_steering(n_observations: int, n_grid: int) -> np.ndarray:
    rows = np.arange(n_observations)[:, None]
    cols = np.arange(n_grid)[None, :]
    return np.exp(2j * np.pi * rows * cols / n_grid) / np.sqrt(n_observations)


def build_dictionary(grid: GridConfig) -> np.ndarray:
    angle = dft_steering(grid.angle_bins, grid.angle_bins)
    delay = dft_steering(grid.delay_bins, grid.delay_bins)
    doppler = dft_steering(grid.doppler_bins, grid.doppler_bins)
    atoms: list[np.ndarray] = []
    for a_idx, d_idx, v_idx in product(
        range(grid.angle_bins), range(grid.delay_bins), range(grid.doppler_bins)
    ):
        atom = np.kron(doppler[:, v_idx], np.kron(delay[:, d_idx], angle[:, a_idx]))
        atoms.append(atom)
    dictionary = np.stack(atoms, axis=1)
    norms = np.linalg.norm(dictionary, axis=0, keepdims=True)
    return dictionary / np.maximum(norms, 1e-12)


def flat_index(grid: GridConfig, angle_index: int, delay_index: int, doppler_index: int) -> int:
    return (
        angle_index * grid.delay_bins * grid.doppler_bins
        + delay_index * grid.doppler_bins
        + doppler_index
    )


def unravel_index(grid: GridConfig, index: int) -> tuple[int, int, int]:
    angle_index = index // (grid.delay_bins * grid.doppler_bins)
    rem = index % (grid.delay_bins * grid.doppler_bins)
    delay_index = rem // grid.doppler_bins
    doppler_index = rem % grid.doppler_bins
    return angle_index, delay_index, doppler_index


def generate_set_a_sample(
    *,
    rng: np.random.Generator,
    grid: GridConfig,
    n_targets: int,
    snr_db: float,
    dictionary: Optional[np.ndarray] = None,
) -> SetASample:
    if n_targets < 1:
        raise ValueError("n_targets must be positive.")
    n_atoms = grid.angle_bins * grid.delay_bins * grid.doppler_bins
    if n_targets > n_atoms:
        raise ValueError("n_targets cannot exceed the grid cardinality.")

    dictionary = build_dictionary(grid) if dictionary is None else dictionary
    support = rng.choice(n_atoms, size=n_targets, replace=False)
    gains = (rng.standard_normal(n_targets) + 1j * rng.standard_normal(n_targets)) / np.sqrt(2)
    sparse = np.zeros(n_atoms, dtype=np.complex128)
    sparse[support] = gains
    clean = dictionary @ sparse
    signal_power = float(np.mean(np.abs(clean) ** 2))
    noise_variance = signal_power / (10 ** (snr_db / 10))
    noise = np.sqrt(noise_variance / 2) * (
        rng.standard_normal(clean.shape) + 1j * rng.standard_normal(clean.shape)
    )
    targets = tuple(
        TargetTruth(*unravel_index(grid, int(idx)), gain=complex(gain))
        for idx, gain in zip(support, gains)
    )
    truth = ChannelTruth(targets=targets, sparse_coefficients=sparse)
    return SetASample(
        measurement=clean + noise,
        dictionary=dictionary,
        truth=truth,
        noise_variance=noise_variance,
        snr_db=snr_db,
        grid=grid,
    )
