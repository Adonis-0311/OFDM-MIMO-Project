from __future__ import annotations

import csv
import json
from pathlib import Path
import statistics
import sys
import time
import tracemalloc
from typing import Callable

import numpy as np
import psutil
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_active_modules"))

from baseline.tensor_fft_omp import TensorFFTSample, generate_sparse_fft_sample, recover_topk_fft
from baseline.subspace_tensor import complex_parafac_als, separable_forward_backward_esprit
from common.manifest import environment_snapshot
from common.seed import seed_all
from data.offgrid_tensor import (
    estimate_from_bins_lstsq,
    generate_offgrid_tensor_sample,
    refine_bins_local,
    topk_grid_bins,
)
from tompnet.torch_layer import TorchOffgridRefinementLayer, prepare_torch_sample


def median(values: list[float]) -> float:
    return float(statistics.median(values)) if values else float("nan")


def finite_mean(values: list[float]) -> float:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    return float(np.mean(arr)) if arr.size else float("nan")


def estimate_fft_ops(shape: tuple[int, ...]) -> float:
    n = float(np.prod(shape))
    stages = float(sum(np.log2(axis) for axis in shape if axis > 1))
    # Complex FFT order proxy; not hardware FLOPs.
    return 5.0 * n * stages


def estimate_local_refine_ops(shape: tuple[int, int, int], n_targets: int, search_points: int) -> float:
    n = float(np.prod(shape))
    candidates = float(n_targets * (search_points**3))
    # Complex atom generation + inner product proxy.
    return 8.0 * n * candidates


def estimate_lstsq_ops(shape: tuple[int, int, int], n_targets: int) -> float:
    n = float(np.prod(shape))
    k = float(n_targets)
    # Dense thin least-squares normal-equation proxy.
    return 8.0 * n * k * k + (2.0 / 3.0) * k**3


def estimate_separable_esprit_ops(shape: tuple[int, int, int], rank: int) -> float:
    total = 0.0
    for axis_size in shape:
        snapshots = float(np.prod(shape) // axis_size)
        size = float(axis_size)
        effective_rank = float(min(rank, axis_size - 1, int(snapshots)))
        # Covariance formation plus Hermitian eigendecomposition proxy.
        total += (
            8.0 * size * size * snapshots
            + (20.0 / 3.0) * size**3
            + 8.0 * (size - 1.0) * effective_rank**2
            + (20.0 / 3.0) * effective_rank**3
        )
    return total


def estimate_parafac_als_ops(
    shape: tuple[int, int, int],
    rank: int,
    iterations: int,
) -> float:
    n = float(np.prod(shape))
    r = float(rank)
    # Three MTTKRP updates and small least-squares solves per ALS sweep.
    return float(iterations) * (24.0 * n * r + 8.0 * sum(shape) * r * r + 2.0 * r**3)


def measure_callable(fn: Callable[[], object], *, repeats: int, warmups: int = 1) -> dict[str, float]:
    process = psutil.Process()
    for _ in range(warmups):
        fn()
    times_ms: list[float] = []
    peaks_mb: list[float] = []
    rss_deltas_mb: list[float] = []
    for _ in range(repeats):
        before_rss = process.memory_info().rss
        tracemalloc.start()
        started = time.perf_counter()
        fn()
        elapsed = time.perf_counter() - started
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        after_rss = process.memory_info().rss
        times_ms.append(elapsed * 1000.0)
        peaks_mb.append(peak / (1024.0 * 1024.0))
        rss_deltas_mb.append(max(after_rss - before_rss, 0) / (1024.0 * 1024.0))
    return {
        "median_wall_clock_ms": median(times_ms),
        "mean_wall_clock_ms": finite_mean(times_ms),
        "python_peak_alloc_mb": median(peaks_mb),
        "rss_delta_mb": median(rss_deltas_mb),
    }


def benchmark_grid_fft(sample: TensorFFTSample, *, n_targets: int, repeats: int) -> dict[str, float]:
    metrics = measure_callable(lambda: recover_topk_fft(sample, n_targets), repeats=repeats)
    metrics["operation_proxy"] = estimate_fft_ops(sample.measurement.shape)
    metrics["parameter_count"] = 0.0
    return metrics


def benchmark_local_refinement(
    *,
    shape: tuple[int, int, int],
    n_targets: int,
    snr_db: float,
    offset_radius: float,
    search_radius: float,
    search_points: int,
    seed: int,
    repeats: int,
) -> dict[str, float]:
    rng = seed_all(seed)
    sample = generate_offgrid_tensor_sample(
        rng=rng,
        shape=shape,
        n_targets=n_targets,
        snr_db=snr_db,
        offset_radius=offset_radius,
    )
    coarse = topk_grid_bins(sample.measurement, n_targets)

    def run() -> object:
        refined = refine_bins_local(
            sample.measurement,
            shape,
            coarse,
            search_radius=search_radius,
            search_points=search_points,
        )
        return estimate_from_bins_lstsq(sample.measurement, shape, refined)

    metrics = measure_callable(run, repeats=repeats)
    metrics["operation_proxy"] = (
        estimate_fft_ops(shape)
        + estimate_local_refine_ops(shape, n_targets, search_points)
        + estimate_lstsq_ops(shape, n_targets)
    )
    metrics["parameter_count"] = 0.0
    return metrics


def benchmark_torch_alpha_layer(
    *,
    shape: tuple[int, int, int],
    n_targets: int,
    snr_db: float,
    offset_radius: float,
    search_radius: float,
    search_points: int,
    seed: int,
    repeats: int,
) -> dict[str, float]:
    rng = seed_all(seed)
    torch.manual_seed(seed)
    sample = prepare_torch_sample(
        generate_offgrid_tensor_sample(
            rng=rng,
            shape=shape,
            n_targets=n_targets,
            snr_db=snr_db,
            offset_radius=offset_radius,
        ),
        n_targets=n_targets,
        search_radius=search_radius,
        search_points=search_points,
    )
    model = TorchOffgridRefinementLayer(initial_alpha=0.5)
    coarse = torch.as_tensor(sample.coarse_bins, dtype=torch.float64)
    refined = torch.as_tensor(sample.refined_bins, dtype=torch.float64)
    measurement = torch.as_tensor(sample.measurement, dtype=torch.complex128)

    def run() -> object:
        with torch.no_grad():
            return model(coarse, refined, measurement, shape)

    metrics = measure_callable(run, repeats=repeats)
    metrics["operation_proxy"] = estimate_lstsq_ops(shape, n_targets) + estimate_local_refine_ops(
        shape,
        n_targets,
        1,
    )
    metrics["parameter_count"] = float(sum(param.numel() for param in model.parameters()))
    return metrics


def benchmark_separable_esprit(
    measurement: np.ndarray,
    *,
    rank: int,
    repeats: int,
) -> dict[str, float]:
    metrics = measure_callable(
        lambda: separable_forward_backward_esprit(measurement, rank=rank),
        repeats=repeats,
    )
    metrics["operation_proxy"] = estimate_separable_esprit_ops(measurement.shape, rank)
    metrics["parameter_count"] = 0.0
    return metrics


def benchmark_parafac_als(
    measurement: np.ndarray,
    *,
    rank: int,
    iterations: int,
    repeats: int,
    seed: int,
) -> dict[str, float]:
    metrics = measure_callable(
        lambda: complex_parafac_als(
            measurement,
            rank=rank,
            iterations=iterations,
            seed=seed,
        ),
        repeats=repeats,
    )
    metrics["operation_proxy"] = estimate_parafac_als_ops(
        measurement.shape,
        rank,
        iterations,
    )
    metrics["parameter_count"] = 0.0
    return metrics


def implemented_row(
    *,
    method: str,
    category: str,
    status: str,
    l_value: int,
    shape: tuple[int, int, int],
    metrics: dict[str, float],
    notes: str,
) -> dict[str, float | str]:
    return {
        "method": method,
        "category": category,
        "status": status,
        "tensor_shape": "x".join(str(value) for value in shape),
        "l_value": float(l_value),
        "parameter_count": float(metrics.get("parameter_count", float("nan"))),
        "operation_proxy": float(metrics.get("operation_proxy", float("nan"))),
        "median_wall_clock_ms": float(metrics.get("median_wall_clock_ms", float("nan"))),
        "mean_wall_clock_ms": float(metrics.get("mean_wall_clock_ms", float("nan"))),
        "python_peak_alloc_mb": float(metrics.get("python_peak_alloc_mb", float("nan"))),
        "rss_delta_mb": float(metrics.get("rss_delta_mb", float("nan"))),
        "notes": notes,
    }


def write_evaluation_summary(
    output_dir: Path,
    *,
    metrics: dict[str, float | str],
    rows: list[dict[str, float | str]],
) -> Path:
    implemented = [row for row in rows if row["status"] == "implemented"]
    fastest = min(implemented, key=lambda row: float(row["median_wall_clock_ms"]))
    slowest = max(implemented, key=lambda row: float(row["median_wall_clock_ms"]))
    lines = [
        "# Complexity Benchmark Evaluation Summary",
        "",
        "## Outcome Summary",
        "",
        "This E4 dev-run establishes a reproducible complexity and wall-clock table for all selected estimator families.",
        "",
        "The separable forward-backward ESPRIT row is a complexity comparator without cross-axis pairing; it is not labeled as full Unitary ESPRIT. PARAFAC uses a fixed-iteration complex ALS implementation.",
        "",
        "## evaluation_summary",
        "",
        "- `research_question`: What are the parameter count, operation-proxy, CPU wall-clock, and memory footprints of the implemented Tensor-OMP/T-OMP-Net paths?",
        f"- `claim_update`: {metrics['claim_update']}",
        "- `baseline_relation`: Grid FFT top-k is the reference baseline; bounded refinement and Torch alpha layer are measured on matching synthetic tensor scale.",
        "- `failure_mode`: Operation counts are analytical proxies rather than profiler FLOPs, and timing depends on this CPU/software environment.",
        "- `mechanism_note`: ESPRIT forms three axis-wise forward-backward covariance eigensystems; PARAFAC performs fixed-sweep complex ALS updates.",
        "- `next_action`: Keep estimation-accuracy claims separate until matched comparator accuracy experiments are reviewed.",
        "- `evidence_level`: E4 auxiliary/dev complexity evidence.",
        "",
        "## Key Metrics",
        "",
        f"- Implemented method rows: {metrics['implemented_rows']}",
        f"- Not-implemented comparator rows: {metrics['not_implemented_rows']}",
        f"- Fastest implemented method: {fastest['method']} at {float(fastest['median_wall_clock_ms']):.4f} ms",
        f"- Slowest implemented method: {slowest['method']} at {float(slowest['median_wall_clock_ms']):.4f} ms",
        f"- Max parameter count: {float(metrics['max_parameter_count']):.0f}",
    ]
    path = output_dir / "evaluation_summary.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    shape = (128, 16, 32)
    snr_db = 20.0
    offset_radius = 0.35
    search_radius = 0.45
    search_points = 5
    repeats = 5
    parafac_iterations = 5
    seed = 20260626
    l_values = [4, 8, 16]
    rng = seed_all(seed)
    rows: list[dict[str, float | str]] = []

    for l_value in l_values:
        fft_sample = generate_sparse_fft_sample(
            rng=rng,
            shape=shape,
            n_targets=l_value,
            snr_db=snr_db,
        )
        rows.append(
            implemented_row(
                method="grid_fft_topk_tensor_omp",
                category="baseline",
                status="implemented",
                l_value=l_value,
                shape=shape,
                metrics=benchmark_grid_fft(fft_sample, n_targets=l_value, repeats=repeats),
                notes="FFT matched filter plus top-k support selection on an on-grid sparse tensor sample.",
            )
        )
        rows.append(
            implemented_row(
                method="bounded_local_refinement_lstsq",
                category="offgrid_refinement",
                status="implemented",
                l_value=l_value,
                shape=shape,
                metrics=benchmark_local_refinement(
                    shape=shape,
                    n_targets=l_value,
                    snr_db=snr_db,
                    offset_radius=offset_radius,
                    search_radius=search_radius,
                    search_points=search_points,
                    seed=seed + l_value,
                    repeats=repeats,
                ),
                notes="Current deterministic bounded local search plus LS reconstruction proxy used by Stage-2/3 experiments.",
            )
        )
        rows.append(
            implemented_row(
                method="torch_alpha_refinement_layer_forward",
                category="tompnet_proxy",
                status="implemented",
                l_value=l_value,
                shape=shape,
                metrics=benchmark_torch_alpha_layer(
                    shape=shape,
                    n_targets=l_value,
                    snr_db=snr_db,
                    offset_radius=offset_radius,
                    search_radius=search_radius,
                    search_points=search_points,
                    seed=seed + 100 + l_value,
                    repeats=repeats,
                ),
                notes="One-parameter PyTorch alpha layer forward pass using prepared coarse/refined bins and torch.linalg.lstsq.",
            )
        )
        rows.append(
            implemented_row(
                method="separable_forward_backward_esprit",
                category="classical_subspace_comparator",
                status="implemented",
                l_value=l_value,
                shape=shape,
                metrics=benchmark_separable_esprit(
                    fft_sample.measurement,
                    rank=l_value,
                    repeats=repeats,
                ),
                notes="Axis-wise forward-backward ESPRIT complexity comparator; no cross-axis component pairing and not full Unitary ESPRIT.",
            )
        )
        rows.append(
            implemented_row(
                method="complex_parafac_als_5_sweeps",
                category="tensor_decomposition_comparator",
                status="implemented",
                l_value=l_value,
                shape=shape,
                metrics=benchmark_parafac_als(
                    fft_sample.measurement,
                    rank=l_value,
                    iterations=parafac_iterations,
                    repeats=repeats,
                    seed=seed + 200 + l_value,
                ),
                notes="Complex CP/PARAFAC-ALS complexity comparator with five fixed sweeps and deterministic initialization.",
            )
        )

    implemented = [row for row in rows if row["status"] == "implemented"]
    metrics = {
        "claim_update": "complexity-comparator-table-ready",
        "tensor_shape": "128x16x32",
        "snr_db": snr_db,
        "l_values": ",".join(str(value) for value in l_values),
        "repeats": float(repeats),
        "implemented_rows": float(len(implemented)),
        "not_implemented_rows": float(sum(row["status"] == "not_implemented" for row in rows)),
        "min_median_wall_clock_ms": min(float(row["median_wall_clock_ms"]) for row in implemented),
        "max_median_wall_clock_ms": max(float(row["median_wall_clock_ms"]) for row in implemented),
        "max_parameter_count": max(float(row["parameter_count"]) for row in implemented),
        "max_python_peak_alloc_mb": max(float(row["python_peak_alloc_mb"]) for row in implemented),
    }

    output_dir = ROOT / "05_results" / "complexity_benchmark"
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "complexity_benchmark.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    manifest = {
        "run_id": "complexity_benchmark_dev_20260627",
        "command": "python 04_experiments/eval/run_complexity_benchmark.py",
        "config": {
            "shape": shape,
            "snr_db": snr_db,
            "offset_radius": offset_radius,
            "search_radius": search_radius,
            "search_points": search_points,
            "repeats": repeats,
            "parafac_iterations": parafac_iterations,
            "seed": seed,
            "l_values": l_values,
        },
        "metrics": metrics,
        "environment": environment_snapshot(ROOT),
        "notes": [
            "Operation proxy is an order-of-growth arithmetic proxy, not hardware FLOPs from a profiler.",
            "Wall-clock timings are CPU local timings on the current workstation.",
            "The ESPRIT row is separable forward-backward ESPRIT, not full Unitary ESPRIT, and does not perform cross-axis pairing.",
            "The PARAFAC row uses five fixed ALS sweeps; neither comparator receives an accuracy claim from this timing run.",
        ],
    }
    manifest_path = output_dir / "run_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    evaluation_path = write_evaluation_summary(output_dir, metrics=metrics, rows=rows)
    lines = [
        "# Complexity Benchmark",
        "",
        f"- Claim update: `{metrics['claim_update']}`",
        f"- Tensor shape: `{metrics['tensor_shape']}`",
        f"- L values: `{metrics['l_values']}`",
        f"- Implemented method rows: `{int(metrics['implemented_rows'])}`",
        f"- Not-implemented comparator rows: `{int(metrics['not_implemented_rows'])}`",
        f"- Min median wall-clock: `{metrics['min_median_wall_clock_ms']:.6g}` ms",
        f"- Max median wall-clock: `{metrics['max_median_wall_clock_ms']:.6g}` ms",
        f"- Max parameter count: `{metrics['max_parameter_count']:.0f}`",
        "",
        "## Interpretation",
        "",
        "The repository now has executable complexity rows for the Tensor-OMP/T-OMP-Net proxy paths, separable forward-backward ESPRIT, and complex PARAFAC-ALS. Operation proxies are not profiler FLOPs, and comparator accuracy remains outside this timing-only evidence block.",
        "",
        "## Artifacts",
        "",
        f"- `{csv_path.relative_to(ROOT)}`",
        f"- `{manifest_path.relative_to(ROOT)}`",
        f"- `{evaluation_path.relative_to(ROOT)}`",
    ]
    summary_path = output_dir / "summary.md"
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {csv_path.relative_to(ROOT)}")
    print(f"Wrote {summary_path.relative_to(ROOT)}")
    print(f"Wrote {manifest_path.relative_to(ROOT)}")
    print(f"Wrote {evaluation_path.relative_to(ROOT)}")
    print(f"claim_update={metrics['claim_update']}")
    print(f"implemented_rows={int(metrics['implemented_rows'])}")
    print(f"max_median_wall_clock_ms={metrics['max_median_wall_clock_ms']:.4f}")


if __name__ == "__main__":
    main()
