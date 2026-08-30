from __future__ import annotations

import numpy as np
import torch
from scipy.optimize import linear_sum_assignment


FEATURE_NAMES = (
    "support_fraction",
    "topk_energy_fraction",
    "grid_residual_fraction",
    "mean_abs_delay_step",
    "mean_abs_angle_step",
    "std_abs_delay_step",
    "std_abs_angle_step",
    "unique_delay_fraction",
    "unique_angle_fraction",
    "log10_design_condition",
)


def atom_2d(shape: tuple[int, int], bins: np.ndarray) -> np.ndarray:
    delay_index = np.arange(shape[0], dtype=float)
    angle_index = np.arange(shape[1], dtype=float)
    delay = np.exp(2j * np.pi * delay_index * bins[0] / shape[0]) / np.sqrt(shape[0])
    angle = np.exp(2j * np.pi * angle_index * bins[1] / shape[1]) / np.sqrt(shape[1])
    return delay[:, None] * angle[None, :]


def design_matrix(shape: tuple[int, int], bins: np.ndarray) -> np.ndarray:
    return np.stack([atom_2d(shape, pair).reshape(-1) for pair in bins], axis=1)


def estimator_features(
    measurement: np.ndarray,
    coarse_bins: np.ndarray,
    refined_bins: np.ndarray,
    *,
    search_radius: float,
) -> np.ndarray:
    shape = measurement.shape
    support_count = max(len(coarse_bins), 1)
    spectrum = np.fft.fftn(measurement, norm="ortho")
    support_indices = tuple(coarse_bins.astype(int).T)
    selected_energy = float(np.sum(np.abs(spectrum[support_indices]) ** 2))
    total_energy = max(float(np.sum(np.abs(spectrum) ** 2)), 1e-300)
    design = design_matrix(shape, coarse_bins)
    coefficients, *_ = np.linalg.lstsq(design, measurement.reshape(-1), rcond=None)
    grid_estimate = (design @ coefficients).reshape(shape)
    residual_fraction = float(
        np.linalg.norm(measurement - grid_estimate) ** 2
        / max(np.linalg.norm(measurement) ** 2, 1e-300)
    )
    steps = np.abs(refined_bins - coarse_bins) / max(search_radius, 1e-12)
    condition = float(np.linalg.cond(design))
    features = np.asarray(
        [
            support_count / np.prod(shape),
            selected_energy / total_energy,
            residual_fraction,
            float(np.mean(steps[:, 0])),
            float(np.mean(steps[:, 1])),
            float(np.std(steps[:, 0])),
            float(np.std(steps[:, 1])),
            len(np.unique(coarse_bins[:, 0].astype(int))) / support_count,
            len(np.unique(coarse_bins[:, 1].astype(int))) / support_count,
            np.log10(max(condition, 1.0)),
        ],
        dtype=np.float64,
    )
    if not np.all(np.isfinite(features)):
        raise ValueError("non-finite estimator feature")
    return features


def circular_signed_delta(values: np.ndarray, reference: np.ndarray, period: np.ndarray) -> np.ndarray:
    return np.mod(values - reference + period / 2.0, period) - period / 2.0


def match_truth_to_coarse(
    coarse_bins: np.ndarray,
    truth_bins: np.ndarray,
    *,
    shape: tuple[int, int],
) -> np.ndarray:
    period = np.asarray(shape, dtype=float)
    deltas = circular_signed_delta(
        truth_bins[:, None, :],
        coarse_bins[None, :, :],
        period,
    )
    cost = np.sum(deltas**2, axis=2)
    truth_indices, coarse_indices = linear_sum_assignment(cost)
    matched = np.empty_like(coarse_bins, dtype=float)
    for truth_index, coarse_index in zip(truth_indices, coarse_indices):
        delta = circular_signed_delta(
            truth_bins[truth_index],
            coarse_bins[coarse_index],
            period,
        )
        matched[coarse_index] = coarse_bins[coarse_index] + delta
    return matched


class FeatureConditionedRefinementController(torch.nn.Module):
    def __init__(self, hidden_dim: int = 16) -> None:
        super().__init__()
        self.network = torch.nn.Sequential(
            torch.nn.Linear(len(FEATURE_NAMES), hidden_dim, dtype=torch.float64),
            torch.nn.Tanh(),
            torch.nn.Linear(hidden_dim, 2, dtype=torch.float64),
        )
        torch.nn.init.zeros_(self.network[-1].weight)
        initial = 0.5 / 1.2
        torch.nn.init.constant_(self.network[-1].bias, float(np.log(initial / (1.0 - initial))))

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return 1.2 * torch.sigmoid(self.network(features))


def apply_nyquist_alias_lock(
    coarse_bins: np.ndarray,
    predicted_bins: np.ndarray,
    *,
    angle_bin_count: int,
) -> np.ndarray:
    locked = np.asarray(predicted_bins, dtype=float).copy()
    wrapped_coarse = np.mod(np.asarray(coarse_bins)[:, 1], angle_bin_count)
    mask = np.isclose(wrapped_coarse, angle_bin_count / 2.0, atol=1e-12)
    locked[mask, 1] = np.asarray(coarse_bins)[mask, 1]
    return locked
