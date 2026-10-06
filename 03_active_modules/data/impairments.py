from __future__ import annotations

import numpy as np


def apply_phase_noise(
    signal: np.ndarray, sigma_degrees: float, rng: np.random.Generator
) -> np.ndarray:
    sigma = np.deg2rad(sigma_degrees)
    phase = rng.normal(0.0, sigma, size=signal.shape)
    return signal * np.exp(1j * phase)


def apply_iq_imbalance(signal: np.ndarray, gain: float, phase_degrees: float) -> np.ndarray:
    phase = np.deg2rad(phase_degrees)
    i_part = np.real(signal) * gain
    q_part = np.imag(signal) / max(gain, 1e-12)
    return i_part + 1j * q_part * np.exp(1j * phase)


def mutual_coupling_matrix(n_antennas: int, rho: float, phi0_degrees: float) -> np.ndarray:
    rho = float(np.clip(rho, 0.0, 0.3))
    phi0 = np.deg2rad(phi0_degrees)
    idx = np.arange(n_antennas)
    distance = np.abs(idx[:, None] - idx[None, :])
    return (rho**distance) * np.exp(1j * phi0 * distance)


def apply_mutual_coupling(
    array_snapshot: np.ndarray, rho: float, phi0_degrees: float, axis: int = 0
) -> np.ndarray:
    moved = np.moveaxis(array_snapshot, axis, 0)
    coupling = mutual_coupling_matrix(moved.shape[0], rho, phi0_degrees)
    distorted = np.tensordot(coupling, moved, axes=(1, 0))
    return np.moveaxis(distorted, 0, axis)
