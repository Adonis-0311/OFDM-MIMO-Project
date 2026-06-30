from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from data.set_a_generator import SetASample
from data.offgrid_tensor import tensor_atom


@dataclass(frozen=True)
class CRLBProxy:
    coefficient_nmse_floor: float
    coefficient_nmse_floor_db: float
    mean_delay_index_std: float


@dataclass(frozen=True)
class FiveParamFIMResult:
    analytic_fim: np.ndarray
    numeric_fim: np.ndarray
    crlb: np.ndarray
    relative_error: float


def coefficient_crlb_proxy(sample: SetASample) -> CRLBProxy:
    """A stage-1 proxy bound for sparse coefficient recovery on a normalized dictionary."""
    support = np.flatnonzero(sample.truth.sparse_coefficients)
    active = sample.dictionary[:, support]
    fim = (active.conj().T @ active).real / max(sample.noise_variance, 1e-300)
    covariance = np.linalg.pinv(fim)
    signal_energy = float(np.linalg.norm(sample.truth.sparse_coefficients) ** 2)
    floor = float(np.trace(covariance).real / max(signal_energy, 1e-300))
    floor_db = 10.0 * np.log10(max(floor, 1e-300))
    gains = np.abs(sample.truth.sparse_coefficients[support])
    delay_std = np.sqrt(sample.noise_variance / np.maximum(gains**2, 1e-300))
    return CRLBProxy(
        coefficient_nmse_floor=floor,
        coefficient_nmse_floor_db=float(floor_db),
        mean_delay_index_std=float(np.mean(delay_std)),
    )


def _atom_derivatives(
    shape: tuple[int, int, int],
    angle_bin: float,
    delay_bin: float,
    doppler_bin: float,
    gain: complex,
) -> list[np.ndarray]:
    atom = tensor_atom(shape, (angle_bin, delay_bin, doppler_bin))
    angle_idx = np.arange(shape[0], dtype=float)[:, None, None]
    delay_idx = np.arange(shape[1], dtype=float)[None, :, None]
    doppler_idx = np.arange(shape[2], dtype=float)[None, None, :]
    return [
        gain * atom * (2j * np.pi * angle_idx / shape[0]),
        gain * atom * (2j * np.pi * delay_idx / shape[1]),
        gain * atom * (2j * np.pi * doppler_idx / shape[2]),
        atom,
        1j * atom,
    ]


def five_param_mean(
    shape: tuple[int, int, int],
    params: np.ndarray,
) -> np.ndarray:
    angle_bin, delay_bin, doppler_bin, gain_re, gain_im = params
    return (gain_re + 1j * gain_im) * tensor_atom(
        shape, (float(angle_bin), float(delay_bin), float(doppler_bin))
    )


def complex_gaussian_fim(derivatives: list[np.ndarray], noise_variance: float) -> np.ndarray:
    n_params = len(derivatives)
    fim = np.zeros((n_params, n_params), dtype=float)
    for i in range(n_params):
        for j in range(n_params):
            fim[i, j] = 2.0 * np.real(np.vdot(derivatives[i], derivatives[j])) / max(
                noise_variance, 1e-300
            )
    return fim


def numeric_derivatives(
    mean_fn: Callable[[np.ndarray], np.ndarray],
    params: np.ndarray,
    *,
    step: float,
) -> list[np.ndarray]:
    derivatives: list[np.ndarray] = []
    for idx in range(params.size):
        plus = params.copy()
        minus = params.copy()
        plus[idx] += step
        minus[idx] -= step
        derivatives.append((mean_fn(plus) - mean_fn(minus)) / (2.0 * step))
    return derivatives


def five_param_fim_crlb(
    *,
    shape: tuple[int, int, int],
    params: np.ndarray,
    noise_variance: float,
    finite_difference_step: float = 1e-5,
) -> FiveParamFIMResult:
    gain = complex(params[3], params[4])
    analytic_derivatives = _atom_derivatives(
        shape,
        angle_bin=float(params[0]),
        delay_bin=float(params[1]),
        doppler_bin=float(params[2]),
        gain=gain,
    )
    analytic = complex_gaussian_fim(analytic_derivatives, noise_variance)
    numeric = complex_gaussian_fim(
        numeric_derivatives(lambda p: five_param_mean(shape, p), params, step=finite_difference_step),
        noise_variance,
    )
    relative_error = float(
        np.linalg.norm(analytic - numeric) / max(np.linalg.norm(analytic), 1e-300)
    )
    crlb = np.linalg.pinv(analytic)
    return FiveParamFIMResult(
        analytic_fim=analytic,
        numeric_fim=numeric,
        crlb=crlb,
        relative_error=relative_error,
    )
