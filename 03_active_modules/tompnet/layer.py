from __future__ import annotations

from dataclasses import dataclass

from data.offgrid_tensor import (
    OffgridTensorSample,
    estimate_from_bins_lstsq,
    measurement_nmse_db,
    refine_bins_local,
    topk_grid_bins,
)


@dataclass(frozen=True)
class TOMPNetSmokeConfig:
    n_targets: int
    enable_offgrid: bool = True
    search_radius: float = 0.45
    search_points: int = 5


@dataclass(frozen=True)
class TOMPNetSmokeResult:
    bins: tuple[tuple[float, float, float], ...]
    measurement_nmse_db: float


def run_minimal_tompnet_smoke(
    sample: OffgridTensorSample,
    config: TOMPNetSmokeConfig,
) -> TOMPNetSmokeResult:
    coarse = topk_grid_bins(sample.measurement, config.n_targets)
    if config.enable_offgrid:
        bins = refine_bins_local(
            sample.measurement,
            sample.shape,
            coarse,
            search_radius=config.search_radius,
            search_points=config.search_points,
        )
    else:
        bins = [(float(a), float(d), float(v)) for a, d, v in coarse]
    estimate = estimate_from_bins_lstsq(sample.measurement, sample.shape, bins)
    return TOMPNetSmokeResult(
        bins=tuple(bins),
        measurement_nmse_db=measurement_nmse_db(estimate, sample.clean),
    )

