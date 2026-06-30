from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch

from data.offgrid_tensor import (
    OffgridTensorSample,
    estimate_from_bins_lstsq,
    measurement_nmse_db,
    refine_bins_local,
    topk_grid_bins,
)


@dataclass(frozen=True)
class TorchPreparedSample:
    coarse_bins: np.ndarray
    refined_bins: np.ndarray
    measurement: np.ndarray
    clean: np.ndarray
    grid_nmse_db: float
    full_refine_nmse_db: float


class TorchOffgridRefinementLayer(torch.nn.Module):
    def __init__(self, initial_alpha: float = 0.5) -> None:
        super().__init__()
        clipped = min(max(initial_alpha / 1.2, 1e-4), 1.0 - 1e-4)
        raw = np.log(clipped / (1.0 - clipped))
        self.alpha_raw = torch.nn.Parameter(torch.tensor(float(raw), dtype=torch.float64))

    def alpha(self) -> torch.Tensor:
        return 1.2 * torch.sigmoid(self.alpha_raw)

    def forward(
        self,
        coarse_bins: torch.Tensor,
        refined_bins: torch.Tensor,
        measurement: torch.Tensor,
        shape: tuple[int, int, int],
    ) -> torch.Tensor:
        alpha = self.alpha()
        bins = coarse_bins + alpha * (refined_bins - coarse_bins)
        design = torch.stack([torch_atom(shape, bins[idx]) for idx in range(bins.shape[0])], dim=1)
        solution = torch.linalg.lstsq(design, measurement.reshape(-1, 1)).solution.reshape(-1)
        estimate = design @ solution
        return estimate.reshape(shape)


class TorchAxiswiseOffgridRefinementLayer(torch.nn.Module):
    """Bounded learned refinement scales for angle, delay, and Doppler axes."""

    def __init__(self, initial_alpha: tuple[float, float, float] = (0.5, 0.5, 0.5)) -> None:
        super().__init__()
        initial = np.asarray(initial_alpha, dtype=float)
        if initial.shape != (3,):
            raise ValueError("initial_alpha must contain angle, delay, and Doppler values")
        clipped = np.clip(initial / 1.2, 1e-4, 1.0 - 1e-4)
        raw = np.log(clipped / (1.0 - clipped))
        self.alpha_raw = torch.nn.Parameter(torch.as_tensor(raw, dtype=torch.float64))

    def alpha(self) -> torch.Tensor:
        return 1.2 * torch.sigmoid(self.alpha_raw)

    def forward(
        self,
        coarse_bins: torch.Tensor,
        refined_bins: torch.Tensor,
        measurement: torch.Tensor,
        shape: tuple[int, int, int],
    ) -> torch.Tensor:
        bins = coarse_bins + self.alpha() * (refined_bins - coarse_bins)
        design = torch_design_matrix(shape, bins)
        solution = torch.linalg.lstsq(design, measurement.reshape(-1, 1)).solution.reshape(-1)
        return (design @ solution).reshape(shape)


def torch_design_matrix(shape: tuple[int, int, int], bins: torch.Tensor) -> torch.Tensor:
    return torch.stack([torch_atom(shape, bins[idx]) for idx in range(bins.shape[0])], dim=1)


def normal_equation_nmse_loss(
    coarse_bins: torch.Tensor,
    refined_bins: torch.Tensor,
    measurement: torch.Tensor,
    clean: torch.Tensor,
    shape: tuple[int, int, int],
    alpha: torch.Tensor,
    *,
    ridge: float = 1e-10,
) -> torch.Tensor:
    bins = coarse_bins + alpha * (refined_bins - coarse_bins)
    design = torch_design_matrix(shape, bins)
    measurement_vec = measurement.reshape(-1)
    clean_vec = clean.reshape(-1)
    gram = design.conj().T @ design
    eye = torch.eye(gram.shape[0], dtype=gram.dtype, device=gram.device)
    rhs = design.conj().T @ measurement_vec
    coeffs = torch.linalg.solve(gram + ridge * eye, rhs)
    clean_projection = design.conj().T @ clean_vec
    estimate_norm_sq = torch.real(torch.vdot(coeffs, gram @ coeffs))
    cross = torch.real(torch.vdot(coeffs, clean_projection))
    clean_norm_sq = torch.sum(torch.abs(clean_vec) ** 2)
    error_norm_sq = torch.clamp(estimate_norm_sq - 2.0 * cross + clean_norm_sq, min=1e-30)
    return error_norm_sq / torch.clamp(clean_norm_sq, min=1e-30)


def torch_atom(shape: tuple[int, int, int], bins: torch.Tensor) -> torch.Tensor:
    device = bins.device
    dtype = torch.float64
    axes = [
        torch.arange(axis_size, dtype=dtype, device=device)
        for axis_size in shape
    ]
    angle = torch.exp(2j * torch.pi * axes[0] * bins[0] / shape[0]) / np.sqrt(shape[0])
    delay = torch.exp(2j * torch.pi * axes[1] * bins[1] / shape[1]) / np.sqrt(shape[1])
    doppler = torch.exp(2j * torch.pi * axes[2] * bins[2] / shape[2]) / np.sqrt(shape[2])
    return (
        angle[:, None, None]
        * delay[None, :, None]
        * doppler[None, None, :]
    ).reshape(-1)


def prepare_torch_sample(
    sample: OffgridTensorSample,
    *,
    n_targets: int,
    search_radius: float = 0.45,
    search_points: int = 5,
) -> TorchPreparedSample:
    coarse = topk_grid_bins(sample.measurement, n_targets)
    refined = refine_bins_local(
        sample.measurement,
        sample.shape,
        coarse,
        search_radius=search_radius,
        search_points=search_points,
    )
    grid_estimate = estimate_from_bins_lstsq(
        sample.measurement,
        sample.shape,
        [(float(a), float(d), float(v)) for a, d, v in coarse],
    )
    refined_estimate = estimate_from_bins_lstsq(sample.measurement, sample.shape, refined)
    return TorchPreparedSample(
        coarse_bins=np.asarray(coarse, dtype=np.float64),
        refined_bins=np.asarray(refined, dtype=np.float64),
        measurement=sample.measurement.astype(np.complex128),
        clean=sample.clean.astype(np.complex128),
        grid_nmse_db=measurement_nmse_db(grid_estimate, sample.clean),
        full_refine_nmse_db=measurement_nmse_db(refined_estimate, sample.clean),
    )


def nmse_loss(estimate: torch.Tensor, clean: torch.Tensor) -> torch.Tensor:
    return torch.sum(torch.abs(estimate - clean) ** 2) / torch.clamp(
        torch.sum(torch.abs(clean) ** 2), min=1e-30
    )


def train_torch_refinement_layer(
    train_samples: list[TorchPreparedSample],
    *,
    shape: tuple[int, int, int],
    epochs: int,
    lr: float,
) -> tuple[TorchOffgridRefinementLayer, list[float]]:
    model = TorchOffgridRefinementLayer(initial_alpha=0.5)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    history: list[float] = []
    for _ in range(epochs):
        optimizer.zero_grad()
        losses = []
        for sample in train_samples:
            estimate = model(
                torch.as_tensor(sample.coarse_bins, dtype=torch.float64),
                torch.as_tensor(sample.refined_bins, dtype=torch.float64),
                torch.as_tensor(sample.measurement, dtype=torch.complex128),
                shape,
            )
            clean = torch.as_tensor(sample.clean, dtype=torch.complex128)
            losses.append(nmse_loss(estimate, clean))
        loss = torch.stack(losses).mean()
        loss.backward()
        optimizer.step()
        history.append(float(10.0 * torch.log10(torch.clamp(loss.detach(), min=1e-30))))
    return model, history


def train_torch_refinement_layer_fast(
    train_samples: list[TorchPreparedSample],
    *,
    shape: tuple[int, int, int],
    epochs: int,
    lr: float,
) -> tuple[TorchOffgridRefinementLayer, list[float]]:
    model = TorchOffgridRefinementLayer(initial_alpha=0.5)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    prepared = [
        (
            torch.as_tensor(sample.coarse_bins, dtype=torch.float64),
            torch.as_tensor(sample.refined_bins, dtype=torch.float64),
            torch.as_tensor(sample.measurement, dtype=torch.complex128),
            torch.as_tensor(sample.clean, dtype=torch.complex128),
        )
        for sample in train_samples
    ]
    history: list[float] = []
    for _ in range(epochs):
        optimizer.zero_grad()
        losses = [
            normal_equation_nmse_loss(
                coarse_bins,
                refined_bins,
                measurement,
                clean,
                shape,
                model.alpha(),
            )
            for coarse_bins, refined_bins, measurement, clean in prepared
        ]
        loss = torch.stack(losses).mean()
        loss.backward()
        optimizer.step()
        history.append(float(10.0 * torch.log10(torch.clamp(loss.detach(), min=1e-30))))
    return model, history


def train_torch_axiswise_refinement_layer_fast(
    train_samples: list[TorchPreparedSample],
    *,
    shape: tuple[int, int, int],
    epochs: int,
    lr: float,
) -> tuple[TorchAxiswiseOffgridRefinementLayer, list[float]]:
    model = TorchAxiswiseOffgridRefinementLayer()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    prepared = [
        (
            torch.as_tensor(sample.coarse_bins, dtype=torch.float64),
            torch.as_tensor(sample.refined_bins, dtype=torch.float64),
            torch.as_tensor(sample.measurement, dtype=torch.complex128),
            torch.as_tensor(sample.clean, dtype=torch.complex128),
        )
        for sample in train_samples
    ]
    history: list[float] = []
    for _ in range(epochs):
        optimizer.zero_grad()
        losses = [
            normal_equation_nmse_loss(
                coarse_bins,
                refined_bins,
                measurement,
                clean,
                shape,
                model.alpha(),
            )
            for coarse_bins, refined_bins, measurement, clean in prepared
        ]
        loss = torch.stack(losses).mean()
        loss.backward()
        optimizer.step()
        history.append(float(10.0 * torch.log10(torch.clamp(loss.detach(), min=1e-30))))
    return model, history


def evaluate_torch_refinement_layer(
    model: TorchOffgridRefinementLayer,
    samples: list[TorchPreparedSample],
    *,
    shape: tuple[int, int, int],
) -> dict[str, float]:
    values = []
    grid_values = []
    full_values = []
    with torch.no_grad():
        for sample in samples:
            estimate = model(
                torch.as_tensor(sample.coarse_bins, dtype=torch.float64),
                torch.as_tensor(sample.refined_bins, dtype=torch.float64),
                torch.as_tensor(sample.measurement, dtype=torch.complex128),
                shape,
            )
            clean = torch.as_tensor(sample.clean, dtype=torch.complex128)
            loss = nmse_loss(estimate, clean)
            values.append(float(10.0 * torch.log10(torch.clamp(loss, min=1e-30))))
            grid_values.append(sample.grid_nmse_db)
            full_values.append(sample.full_refine_nmse_db)
    return {
        "grid_nmse_db": float(np.mean(grid_values)),
        "torch_nmse_db": float(np.mean(values)),
        "full_refine_nmse_db": float(np.mean(full_values)),
        "gain_vs_grid_db": float(np.mean(grid_values) - np.mean(values)),
        "gap_vs_full_refine_db": float(np.mean(values) - np.mean(full_values)),
        "alpha": float(model.alpha().detach().cpu().item()),
    }


def evaluate_torch_refinement_layer_fast(
    model: TorchOffgridRefinementLayer,
    samples: list[TorchPreparedSample],
    *,
    shape: tuple[int, int, int],
) -> dict[str, float]:
    values = []
    grid_values = []
    full_values = []
    with torch.no_grad():
        alpha = model.alpha()
        for sample in samples:
            loss = normal_equation_nmse_loss(
                torch.as_tensor(sample.coarse_bins, dtype=torch.float64),
                torch.as_tensor(sample.refined_bins, dtype=torch.float64),
                torch.as_tensor(sample.measurement, dtype=torch.complex128),
                torch.as_tensor(sample.clean, dtype=torch.complex128),
                shape,
                alpha,
            )
            values.append(float(10.0 * torch.log10(torch.clamp(loss, min=1e-30))))
            grid_values.append(sample.grid_nmse_db)
            full_values.append(sample.full_refine_nmse_db)
    return {
        "grid_nmse_db": float(np.mean(grid_values)),
        "torch_nmse_db": float(np.mean(values)),
        "full_refine_nmse_db": float(np.mean(full_values)),
        "gain_vs_grid_db": float(np.mean(grid_values) - np.mean(values)),
        "gap_vs_full_refine_db": float(np.mean(values) - np.mean(full_values)),
        "alpha": float(alpha.detach().cpu().item()),
    }


def evaluate_torch_axiswise_refinement_layer_fast(
    model: TorchAxiswiseOffgridRefinementLayer,
    samples: list[TorchPreparedSample],
    *,
    shape: tuple[int, int, int],
) -> dict[str, float]:
    values: list[float] = []
    grid_values: list[float] = []
    full_values: list[float] = []
    with torch.no_grad():
        alpha = model.alpha()
        for sample in samples:
            loss = normal_equation_nmse_loss(
                torch.as_tensor(sample.coarse_bins, dtype=torch.float64),
                torch.as_tensor(sample.refined_bins, dtype=torch.float64),
                torch.as_tensor(sample.measurement, dtype=torch.complex128),
                torch.as_tensor(sample.clean, dtype=torch.complex128),
                shape,
                alpha,
            )
            values.append(float(10.0 * torch.log10(torch.clamp(loss, min=1e-30))))
            grid_values.append(sample.grid_nmse_db)
            full_values.append(sample.full_refine_nmse_db)
    alpha_values = alpha.detach().cpu().numpy()
    return {
        "grid_nmse_db": float(np.mean(grid_values)),
        "axiswise_nmse_db": float(np.mean(values)),
        "full_refine_nmse_db": float(np.mean(full_values)),
        "gain_vs_grid_db": float(np.mean(grid_values) - np.mean(values)),
        "gap_vs_full_refine_db": float(np.mean(values) - np.mean(full_values)),
        "angle_alpha": float(alpha_values[0]),
        "delay_alpha": float(alpha_values[1]),
        "doppler_alpha": float(alpha_values[2]),
    }
