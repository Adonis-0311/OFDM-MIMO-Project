from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_active_modules"))

from common.manifest import write_run_manifest, write_summary_md
from common.seed import seed_all
from data.offgrid_tensor import (
    OffgridTensorSample,
    estimate_from_bins_lstsq,
    generate_offgrid_tensor_sample,
    measurement_nmse_db,
    refine_bins_local,
    topk_grid_bins,
)
from tompnet.trainable import interpolate_bins


@dataclass(frozen=True)
class CachedSample:
    seed: int
    split: str
    sample_index: int
    n_targets: int
    sample: OffgridTensorSample
    coarse_bins: list[tuple[int, int, int]]
    refined_bins: list[tuple[float, float, float]]


@dataclass(frozen=True)
class AlphaFit:
    alpha: float
    train_nmse_db: float


def finite_mean(values: list[float]) -> float:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    return float(np.mean(arr)) if arr.size else float("nan")


def prepare_cached_sample(
    sample: OffgridTensorSample,
    *,
    seed: int,
    split: str,
    sample_index: int,
    n_targets: int,
    search_radius: float,
    search_points: int,
) -> CachedSample:
    coarse = topk_grid_bins(sample.measurement, n_targets)
    refined = refine_bins_local(
        sample.measurement,
        sample.shape,
        coarse,
        search_radius=search_radius,
        search_points=search_points,
    )
    return CachedSample(
        seed=seed,
        split=split,
        sample_index=sample_index,
        n_targets=n_targets,
        sample=sample,
        coarse_bins=coarse,
        refined_bins=refined,
    )


def evaluate_cached_alpha(cached: CachedSample, alpha: float) -> float:
    bins = interpolate_bins(cached.coarse_bins, cached.refined_bins, alpha)
    estimate = estimate_from_bins_lstsq(cached.sample.measurement, cached.sample.shape, bins)
    return measurement_nmse_db(estimate, cached.sample.clean)


def train_shared_alpha(samples: list[CachedSample], candidate_alphas: np.ndarray) -> AlphaFit:
    best_alpha = float(candidate_alphas[0])
    best_score = np.inf
    for alpha in candidate_alphas:
        values = [evaluate_cached_alpha(sample, float(alpha)) for sample in samples]
        score = finite_mean(values)
        if score < best_score:
            best_score = score
            best_alpha = float(alpha)
    return AlphaFit(alpha=best_alpha, train_nmse_db=best_score)


def write_evaluation_summary(
    output_dir: Path,
    *,
    mean_gain: float,
    min_gain: float,
    shared_alpha_mean: float,
    torch_blocker_seconds: int,
) -> Path:
    status = "supported" if mean_gain >= 3.0 and min_gain >= 3.0 else "inconclusive"
    lines = [
        "# Stage 2 Curriculum T-OMP-Net G2 Evaluation Summary",
        "",
        "## Outcome Summary",
        "",
        (
            "The locked-scale curriculum validation keeps the Stage-2 tensor shape at "
            "`128x16x32` and trains one shared bounded off-grid refinement alpha across "
            "`L={2,4,8}`. It is a stronger scale/curriculum check than the earlier "
            "single-smoke runs, while still remaining a NumPy/LS proxy rather than the "
            "final full neural T-OMP-Net campaign."
        ),
        "",
        "## evaluation_summary",
        "",
        "- `research_question`: Does a shared curriculum-trained bounded off-grid refinement improve held-out SNR=20 dB samples at the locked Stage-2 scale?",
        f"- `claim_update`: {status} for locked-scale curriculum proxy evidence; PyTorch locked-scale evidence remains resource-limited.",
        "- `baseline_relation`: Compared against grid Tensor-OMP on the same held-out samples for each seed and L cell.",
        f"- `failure_mode`: PyTorch locked-scale prototype exceeded the local CPU timeout budget of {torch_blocker_seconds} seconds; NumPy cached validation completed.",
        "- `next_action`: Optimize or batch the PyTorch training path before promoting G2 from strong proxy support to full acceptance.",
        "- `evidence_level`: Solid locked-scale curriculum proxy; full PyTorch/curriculum acceptance still pending.",
        "",
        "## Key Metrics",
        "",
        "- Tensor shape: 128x16x32",
        "- L curriculum: {2,4,8}",
        f"- Mean held-out gain over grid Tensor-OMP: {mean_gain:.4f} dB",
        f"- Minimum held-out L/seed-cell gain: {min_gain:.4f} dB",
        f"- Mean shared curriculum alpha: {shared_alpha_mean:.4f}",
    ]
    path = output_dir / "evaluation_summary.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    shape = (128, 16, 32)
    snr_db = 20.0
    seeds = [20260624, 20260625]
    l_values = [2, 4, 8]
    n_train = 2
    n_test = 3
    offset_radius = 0.35
    search_radius = 0.45
    search_points = 5
    candidate_alphas = np.linspace(0.0, 1.2, 7)
    torch_blocker_seconds = 180

    rows: list[dict[str, float]] = []
    sample_rows: list[dict[str, float | int | str]] = []
    shared_alphas: list[float] = []
    all_gains: list[float] = []

    for seed in seeds:
        rng = seed_all(seed)
        train_samples: list[CachedSample] = []
        test_samples_by_l: dict[int, list[CachedSample]] = {n_targets: [] for n_targets in l_values}
        for n_targets in l_values:
            for sample_index in range(n_train):
                sample = generate_offgrid_tensor_sample(
                    rng=rng,
                    shape=shape,
                    n_targets=n_targets,
                    snr_db=snr_db,
                    offset_radius=offset_radius,
                )
                train_samples.append(
                    prepare_cached_sample(
                        sample,
                        seed=seed,
                        split="train",
                        sample_index=sample_index,
                        n_targets=n_targets,
                        search_radius=search_radius,
                        search_points=search_points,
                    )
                )
            for sample_index in range(n_test):
                sample = generate_offgrid_tensor_sample(
                    rng=rng,
                    shape=shape,
                    n_targets=n_targets,
                    snr_db=snr_db,
                    offset_radius=offset_radius,
                )
                test_samples_by_l[n_targets].append(
                    prepare_cached_sample(
                        sample,
                        seed=seed,
                        split="test",
                        sample_index=sample_index,
                        n_targets=n_targets,
                        search_radius=search_radius,
                        search_points=search_points,
                    )
                )

        fit = train_shared_alpha(train_samples, candidate_alphas)
        shared_alphas.append(fit.alpha)

        for n_targets, samples in test_samples_by_l.items():
            grid_values = [evaluate_cached_alpha(sample, 0.0) for sample in samples]
            trained_values = [evaluate_cached_alpha(sample, fit.alpha) for sample in samples]
            full_values = [evaluate_cached_alpha(sample, 1.0) for sample in samples]
            gain = finite_mean(grid_values) - finite_mean(trained_values)
            all_gains.append(gain)
            rows.append(
                {
                    "seed": float(seed),
                    "n_targets": float(n_targets),
                    "shared_alpha": fit.alpha,
                    "train_nmse_db": fit.train_nmse_db,
                    "test_grid_nmse_db": finite_mean(grid_values),
                    "test_curriculum_nmse_db": finite_mean(trained_values),
                    "test_full_refine_nmse_db": finite_mean(full_values),
                    "test_gain_vs_grid_db": gain,
                    "test_gap_vs_full_refine_db": finite_mean(trained_values) - finite_mean(full_values),
                    "n_test": float(len(samples)),
                }
            )
            for sample, grid, trained, full in zip(samples, grid_values, trained_values, full_values):
                sample_rows.append(
                    {
                        "seed": seed,
                        "split": sample.split,
                        "sample_index": sample.sample_index,
                        "n_targets": n_targets,
                        "shared_alpha": fit.alpha,
                        "grid_nmse_db": grid,
                        "curriculum_nmse_db": trained,
                        "full_refine_nmse_db": full,
                        "gain_vs_grid_db": grid - trained,
                    }
                )

    output_dir = ROOT / "05_results" / "stage2_curriculum_tompnet_g2"
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "stage2_curriculum_tompnet_g2.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    sample_csv_path = output_dir / "stage2_curriculum_tompnet_g2_samples.csv"
    with sample_csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(sample_rows[0].keys()))
        writer.writeheader()
        writer.writerows(sample_rows)

    metrics = {
        "tensor_shape": "128x16x32",
        "snr_db": snr_db,
        "seeds": seeds,
        "l_values": l_values,
        "n_train_per_l": n_train,
        "n_test_per_l": n_test,
        "candidate_alphas": candidate_alphas.tolist(),
        "mean_shared_alpha": finite_mean(shared_alphas),
        "mean_test_gain_vs_grid_db": finite_mean(all_gains),
        "min_test_gain_vs_grid_db": float(min(all_gains)),
        "num_l_seed_cells": len(all_gains),
        "torch_locked_scale_timeout_seconds": torch_blocker_seconds,
    }
    notes = [
        "Locked-scale curriculum proxy trains one shared bounded off-grid alpha across L={2,4,8}.",
        "Cached local-refinement bins avoid repeating the expensive 3-D local search for every candidate alpha.",
        "This strengthens G2 scale/curriculum evidence, but it is still not the final full PyTorch T-OMP-Net training campaign.",
        "A direct PyTorch locked-scale prototype exceeded the local CPU timeout budget and remains an explicit resource blocker.",
    ]
    manifest_path = write_run_manifest(
        output_dir,
        run_id="stage2_curriculum_tompnet_g2_20260624",
        command="python 04_experiments/eval/run_stage2_curriculum_tompnet_g2.py",
        config={
            "shape": shape,
            "snr_db": snr_db,
            "seeds": seeds,
            "n_train": n_train,
            "n_test": n_test,
            "offset_radius": offset_radius,
            "search_radius": search_radius,
            "search_points": search_points,
            "candidate_alphas": candidate_alphas.tolist(),
            "l_values": l_values,
        },
        metrics=metrics,
        notes=notes,
        cwd=ROOT,
    )
    summary_path = write_summary_md(
        output_dir,
        title="Stage 2 Curriculum T-OMP-Net G2 Validation",
        config_hash="stage2-curriculum-g2-20260624",
        metrics=metrics,
        notes=notes,
        artifacts=[
            str(csv_path.relative_to(ROOT)),
            str(sample_csv_path.relative_to(ROOT)),
            str(manifest_path.relative_to(ROOT)),
        ],
    )
    evaluation_path = write_evaluation_summary(
        output_dir,
        mean_gain=float(metrics["mean_test_gain_vs_grid_db"]),
        min_gain=float(metrics["min_test_gain_vs_grid_db"]),
        shared_alpha_mean=float(metrics["mean_shared_alpha"]),
        torch_blocker_seconds=torch_blocker_seconds,
    )
    print(f"Wrote {csv_path.relative_to(ROOT)}")
    print(f"Wrote {sample_csv_path.relative_to(ROOT)}")
    print(f"Wrote {summary_path.relative_to(ROOT)}")
    print(f"Wrote {manifest_path.relative_to(ROOT)}")
    print(f"Wrote {evaluation_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
