from __future__ import annotations

import csv
from pathlib import Path
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_active_modules"))

from common.manifest import write_run_manifest, write_summary_md
from common.seed import seed_all
from data.offgrid_tensor import (
    estimate_from_bins_lstsq,
    generate_offgrid_tensor_sample,
    measurement_nmse_db,
    refine_bins_local,
    topk_grid_bins,
)


def finite_mean(values: list[float]) -> float:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    return float(np.mean(arr)) if arr.size else float("nan")


def main() -> None:
    shape = (128, 16, 32)
    snr_db = 20.0
    seed = 20260624
    n_trials = 4
    offset_radius = 0.35
    search_radius = 0.45
    search_points = 5
    rng = seed_all(seed)
    started = time.perf_counter()
    rows: list[dict[str, float]] = []
    for n_targets in (2, 4, 8, 16):
        coarse_values: list[float] = []
        refined_values: list[float] = []
        improvement_values: list[float] = []
        elapsed_values: list[float] = []
        for _ in range(n_trials):
            sample = generate_offgrid_tensor_sample(
                rng=rng,
                shape=shape,
                n_targets=n_targets,
                snr_db=snr_db,
                offset_radius=offset_radius,
            )
            tick = time.perf_counter()
            coarse_bins = topk_grid_bins(sample.measurement, n_targets)
            coarse_estimate = estimate_from_bins_lstsq(
                sample.measurement,
                shape,
                [(float(a), float(d), float(v)) for a, d, v in coarse_bins],
            )
            refined_bins = refine_bins_local(
                sample.measurement,
                shape,
                coarse_bins,
                search_radius=search_radius,
                search_points=search_points,
            )
            refined_estimate = estimate_from_bins_lstsq(sample.measurement, shape, refined_bins)
            elapsed_values.append(time.perf_counter() - tick)
            coarse_nmse = measurement_nmse_db(coarse_estimate, sample.clean)
            refined_nmse = measurement_nmse_db(refined_estimate, sample.clean)
            coarse_values.append(coarse_nmse)
            refined_values.append(refined_nmse)
            improvement_values.append(coarse_nmse - refined_nmse)
        rows.append(
            {
                "n_targets": float(n_targets),
                "snr_db": snr_db,
                "offset_radius_bins": offset_radius,
                "mean_grid_nmse_db": finite_mean(coarse_values),
                "mean_refined_nmse_db": finite_mean(refined_values),
                "mean_refinement_gain_db": finite_mean(improvement_values),
                "mean_recovery_seconds": finite_mean(elapsed_values),
            }
        )

    output_dir = ROOT / "05_results" / "paper_scale_offgrid_stress_g1"
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "paper_scale_offgrid_stress_g1.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    metrics = {
        "tensor_shape": "128x16x32",
        "snr_db": snr_db,
        "offset_radius_bins": offset_radius,
        "n_trials_per_l": n_trials,
        "mean_grid_nmse_db": finite_mean([float(row["mean_grid_nmse_db"]) for row in rows]),
        "mean_refined_nmse_db": finite_mean(
            [float(row["mean_refined_nmse_db"]) for row in rows]
        ),
        "mean_refinement_gain_db": finite_mean(
            [float(row["mean_refinement_gain_db"]) for row in rows]
        ),
        "min_refinement_gain_db": float(min(float(row["mean_refinement_gain_db"]) for row in rows)),
        "wall_seconds": time.perf_counter() - started,
    }
    notes = [
        "Paper-scale off-grid stress uses continuous angle-delay-Doppler bins on shape 128x16x32.",
        "Metric is measurement-domain NMSE against the noiseless off-grid tensor, so it is not a sparse-grid coefficient NMSE.",
        "Bounded local refinement is a deterministic oracle-free search around Tensor-OMP grid picks and supports the v2.3R off-grid mechanism gate.",
    ]
    manifest_path = write_run_manifest(
        output_dir,
        run_id="paper_scale_offgrid_stress_g1_20260624",
        command="python 04_experiments/eval/run_paper_scale_offgrid_stress_g1.py",
        config={
            "shape": shape,
            "snr_db": snr_db,
            "seed": seed,
            "n_trials": n_trials,
            "offset_radius": offset_radius,
            "search_radius": search_radius,
            "search_points": search_points,
        },
        metrics=metrics,
        notes=notes,
        cwd=ROOT,
    )
    write_summary_md(
        output_dir,
        title="Paper-Scale Off-Grid Stress G1",
        config_hash="offgrid-local-20260624",
        metrics=metrics,
        notes=notes,
        artifacts=[str(csv_path.relative_to(ROOT)), str(manifest_path.relative_to(ROOT))],
    )


if __name__ == "__main__":
    main()
