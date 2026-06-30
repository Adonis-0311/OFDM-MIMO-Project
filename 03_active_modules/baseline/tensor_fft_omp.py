from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class TensorFFTSample:
    measurement: np.ndarray
    coefficients: np.ndarray
    noise_variance: float
    snr_db: float


@dataclass(frozen=True)
class TensorFFTResult:
    coefficients: np.ndarray
    support_recall: float
    nmse_db: float
    crlb_proxy_db: float


def generate_sparse_fft_sample(
    *,
    rng: np.random.Generator,
    shape: tuple[int, int, int],
    n_targets: int,
    snr_db: float,
) -> TensorFFTSample:
    n_atoms = int(np.prod(shape))
    if n_targets > n_atoms:
        raise ValueError("n_targets cannot exceed tensor cardinality.")
    coefficients = np.zeros(shape, dtype=np.complex128)
    support = rng.choice(n_atoms, size=n_targets, replace=False)
    gains = (rng.standard_normal(n_targets) + 1j * rng.standard_normal(n_targets)) / np.sqrt(2)
    coefficients.reshape(-1)[support] = gains
    clean = np.fft.ifftn(coefficients, norm="ortho")
    signal_power = float(np.mean(np.abs(clean) ** 2))
    noise_variance = signal_power / (10 ** (snr_db / 10))
    noise = np.sqrt(noise_variance / 2) * (
        rng.standard_normal(shape) + 1j * rng.standard_normal(shape)
    )
    return TensorFFTSample(
        measurement=clean + noise,
        coefficients=coefficients,
        noise_variance=noise_variance,
        snr_db=snr_db,
    )


def recover_topk_fft(sample: TensorFFTSample, n_targets: int) -> TensorFFTResult:
    matched = np.fft.fftn(sample.measurement, norm="ortho")
    flat = matched.reshape(-1)
    if n_targets >= flat.size:
        support = np.arange(flat.size)
    else:
        support = np.argpartition(np.abs(flat), -n_targets)[-n_targets:]
    estimate = np.zeros_like(flat)
    estimate[support] = flat[support]
    estimate = estimate.reshape(sample.coefficients.shape)
    true_support = set(np.flatnonzero(sample.coefficients.reshape(-1)))
    est_support = set(int(idx) for idx in support)
    recall = len(true_support & est_support) / max(len(true_support), 1)
    denom = float(np.linalg.norm(sample.coefficients) ** 2)
    nmse = float(np.linalg.norm(estimate - sample.coefficients) ** 2 / max(denom, 1e-300))
    floor = float(n_targets * sample.noise_variance / max(denom, 1e-300))
    return TensorFFTResult(
        coefficients=estimate,
        support_recall=recall,
        nmse_db=10.0 * np.log10(max(nmse, 1e-300)),
        crlb_proxy_db=10.0 * np.log10(max(floor, 1e-300)),
    )

