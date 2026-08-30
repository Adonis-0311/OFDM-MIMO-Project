from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SeparableESPRITResult:
    frequency_bins: tuple[np.ndarray, ...]
    effective_ranks: tuple[int, ...]


def _axis_esprit(matrix: np.ndarray, rank: int) -> tuple[np.ndarray, int]:
    axis_size, snapshots = matrix.shape
    effective_rank = min(rank, axis_size - 1, snapshots)
    covariance = matrix @ matrix.conj().T / max(snapshots, 1)
    exchange = np.fliplr(np.eye(axis_size))
    covariance = 0.5 * (
        covariance + exchange @ covariance.conj() @ exchange
    )
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    subspace = eigenvectors[:, np.argsort(eigenvalues)[-effective_rank:]]
    shift = np.linalg.pinv(subspace[:-1, :]) @ subspace[1:, :]
    modes = np.linalg.eigvals(shift)
    bins = np.mod(np.angle(modes) * axis_size / (2.0 * np.pi), axis_size)
    return np.sort(bins.astype(float)), effective_rank


def separable_forward_backward_esprit(
    tensor: np.ndarray,
    *,
    rank: int,
) -> SeparableESPRITResult:
    estimates = []
    ranks = []
    for axis in range(tensor.ndim):
        matrix = np.moveaxis(tensor, axis, 0).reshape(tensor.shape[axis], -1)
        bins, effective_rank = _axis_esprit(matrix, rank)
        estimates.append(bins)
        ranks.append(effective_rank)
    return SeparableESPRITResult(
        frequency_bins=tuple(estimates),
        effective_ranks=tuple(ranks),
    )


def khatri_rao(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    if left.shape[1] != right.shape[1]:
        raise ValueError("factor matrices must have the same column count")
    return np.einsum("ir,jr->ijr", left, right).reshape(
        left.shape[0] * right.shape[0],
        left.shape[1],
    )


def cp_reconstruct(weights: np.ndarray, factors: tuple[np.ndarray, np.ndarray, np.ndarray]) -> np.ndarray:
    return np.einsum(
        "r,ir,jr,kr->ijk",
        weights,
        factors[0],
        factors[1],
        factors[2],
    )


def complex_parafac_als(
    tensor: np.ndarray,
    *,
    rank: int,
    iterations: int = 10,
    seed: int = 0,
) -> tuple[np.ndarray, tuple[np.ndarray, np.ndarray, np.ndarray]]:
    if tensor.ndim != 3:
        raise ValueError("PARAFAC-ALS expects a third-order tensor")
    rng = np.random.default_rng(seed)
    factors = [
        (
            rng.standard_normal((axis_size, rank))
            + 1j * rng.standard_normal((axis_size, rank))
        ) / np.sqrt(2.0 * axis_size)
        for axis_size in tensor.shape
    ]
    for _ in range(iterations):
        for mode in range(3):
            others = [index for index in range(3) if index != mode]
            kr = khatri_rao(factors[others[0]], factors[others[1]])
            unfolding = np.moveaxis(tensor, mode, 0).reshape(tensor.shape[mode], -1)
            factors[mode] = unfolding @ np.linalg.pinv(kr.T)
    weights = np.ones(rank, dtype=float)
    for component in range(rank):
        for mode in range(3):
            norm = float(np.linalg.norm(factors[mode][:, component]))
            if norm > 0.0:
                factors[mode][:, component] /= norm
                weights[component] *= norm
    return weights, (factors[0], factors[1], factors[2])
