from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import statistics
import sys
import time

import numpy as np
from scipy.optimize import linear_sum_assignment


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_active_modules"))

from baseline.tensor_nomp import tensor_nomp_known_order
from common.manifest import write_run_manifest
from common.seed import seed_all
from data.offgrid_tensor import (
    estimate_from_bins_lstsq,
    generate_offgrid_tensor_sample,
    measurement_nmse_db,
    refine_bins_local,
    topk_grid_bins,
)


METHODS = (
    "grid_fft_topk_plus_ls",
    "deterministic_cartesian_local_refinement_plus_ls",
    "fixed_source_trained_scalar_interpolation_plus_ls",
    "tensor_nomp3d_known_order_v1",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shape", type=int, nargs=3, default=(128, 16, 32))
    parser.add_argument("--l-values", type=int, nargs="+", default=(2, 4, 8))
    parser.add_argument("--snrs", type=float, nargs="+", default=(0.0, 10.0, 20.0, 30.0))
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=(20260630, 20260701, 20260702, 20260703, 20260704),
    )
    parser.add_argument("--samples-per-cell-seed", type=int, default=20)
    parser.add_argument("--offset-radius", type=float, default=0.35)
    parser.add_argument("--search-radius", type=float, default=0.45)
    parser.add_argument("--search-points", type=int, default=5)
    parser.add_argument("--source-alpha", type=float, default=0.6419195571509573)
    parser.add_argument("--nomp-local-iterations", type=int, default=5)
    parser.add_argument("--nomp-cyclic-passes", type=int, default=2)
    parser.add_argument("--nomp-cyclic-iterations", type=int, default=2)
    parser.add_argument("--nomp-oversampling-points", type=int, default=5)
    parser.add_argument("--output-dir-name", default="tensor_nomp3d_matched_paper_5seed")
    return parser.parse_args()


def truth_bins(sample) -> np.ndarray:
    return np.asarray(
        [
            [
                target.angle_bin + target.angle_offset,
                target.delay_bin + target.delay_offset,
                target.doppler_bin + target.doppler_offset,
            ]
            for target in sample.targets
        ],
        dtype=float,
    )


def matched_bin_metrics(
    estimated: np.ndarray,
    truth: np.ndarray,
    shape: tuple[int, int, int],
) -> dict[str, float]:
    period = np.asarray(shape, dtype=float)
    deltas = np.mod(
        estimated[:, None, :] - truth[None, :, :] + period / 2.0,
        period,
    ) - period / 2.0
    normalized = deltas / period
    cost = np.sum(normalized**2, axis=2)
    estimated_index, truth_index = linear_sum_assignment(cost)
    matched = deltas[estimated_index, truth_index]
    normalized_matched = normalized[estimated_index, truth_index]
    return {
        "angle_bin_rmse": float(np.sqrt(np.mean(matched[:, 0] ** 2))),
        "delay_bin_rmse": float(np.sqrt(np.mean(matched[:, 1] ** 2))),
        "doppler_bin_rmse": float(np.sqrt(np.mean(matched[:, 2] ** 2))),
        "normalized_joint_bin_rmse": float(np.sqrt(np.mean(np.sum(normalized_matched**2, axis=1)))),
        "matched_fraction_within_half_bin": float(np.mean(np.all(np.abs(matched) <= 0.5, axis=1))),
    }


def run_method(
    method: str,
    sample,
    *,
    n_targets: int,
    search_radius: float,
    search_points: int,
    source_alpha: float,
    nomp_local_iterations: int,
    nomp_cyclic_passes: int,
    nomp_cyclic_iterations: int,
    nomp_oversampling_points: int,
) -> tuple[np.ndarray, np.ndarray, dict[str, float]]:
    started = time.perf_counter()
    extras: dict[str, float] = {}
    if method == "grid_fft_topk_plus_ls":
        bins = np.asarray(topk_grid_bins(sample.measurement, n_targets), dtype=float)
        reconstruction = estimate_from_bins_lstsq(
            sample.measurement, sample.shape, [tuple(item) for item in bins]
        )
    elif method in {
        "deterministic_cartesian_local_refinement_plus_ls",
        "fixed_source_trained_scalar_interpolation_plus_ls",
    }:
        coarse = np.asarray(topk_grid_bins(sample.measurement, n_targets), dtype=float)
        refined = np.asarray(
            refine_bins_local(
                sample.measurement,
                sample.shape,
                [tuple(int(value) for value in item) for item in coarse],
                search_radius=search_radius,
                search_points=search_points,
            ),
            dtype=float,
        )
        bins = refined if method.startswith("deterministic") else coarse + source_alpha * (refined - coarse)
        bins = np.mod(bins, np.asarray(sample.shape, dtype=float))
        reconstruction = estimate_from_bins_lstsq(
            sample.measurement, sample.shape, [tuple(item) for item in bins]
        )
    elif method == "tensor_nomp3d_known_order_v1":
        result = tensor_nomp_known_order(
            sample.measurement,
            n_targets=n_targets,
            local_iterations=nomp_local_iterations,
            cyclic_passes=nomp_cyclic_passes,
            cyclic_iterations=nomp_cyclic_iterations,
            detection_oversampling_points=nomp_oversampling_points,
        )
        bins = result.bins
        reconstruction = result.reconstruction
        extras["newton_updates"] = float(result.newton_updates)
        extras["final_residual_energy"] = float(result.residual_energy_history[-1])
    else:
        raise ValueError(f"unknown method: {method}")
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    extras["wall_clock_ms"] = elapsed_ms
    return bins, reconstruction, extras


def mean(values: list[float]) -> float:
    return float(np.mean(np.asarray(values, dtype=float)))


def median(values: list[float]) -> float:
    return float(statistics.median(values))


def write_csv(path: Path, rows: list[dict]) -> None:
    fieldnames = list(rows[0])
    for row in rows[1:]:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    shape = tuple(args.shape)
    output_dir = ROOT / "05_results" / args.output_dir_name
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    for seed in args.seeds:
        rng = seed_all(seed)
        for snr_db in args.snrs:
            for n_targets in args.l_values:
                for sample_index in range(args.samples_per_cell_seed):
                    sample = generate_offgrid_tensor_sample(
                        rng=rng,
                        shape=shape,
                        n_targets=n_targets,
                        snr_db=snr_db,
                        offset_radius=args.offset_radius,
                    )
                    truth = truth_bins(sample)
                    sample_rows: dict[str, dict] = {}
                    for method in METHODS:
                        bins, reconstruction, extras = run_method(
                            method,
                            sample,
                            n_targets=n_targets,
                            search_radius=args.search_radius,
                            search_points=args.search_points,
                            source_alpha=args.source_alpha,
                            nomp_local_iterations=args.nomp_local_iterations,
                            nomp_cyclic_passes=args.nomp_cyclic_passes,
                            nomp_cyclic_iterations=args.nomp_cyclic_iterations,
                            nomp_oversampling_points=args.nomp_oversampling_points,
                        )
                        metrics = matched_bin_metrics(bins, truth, shape)
                        row = {
                            "seed": seed,
                            "snr_db": snr_db,
                            "n_targets": n_targets,
                            "sample_index": sample_index,
                            "method": method,
                            "measurement_nmse_db": measurement_nmse_db(reconstruction, sample.clean),
                            **metrics,
                            **extras,
                        }
                        sample_rows[method] = row
                    grid_nmse = sample_rows["grid_fft_topk_plus_ls"]["measurement_nmse_db"]
                    for method in METHODS:
                        sample_rows[method]["gain_vs_grid_db"] = grid_nmse - sample_rows[method]["measurement_nmse_db"]
                        rows.append(sample_rows[method])

    cells_path = output_dir / "matched_accuracy_rows.csv"
    write_csv(cells_path, rows)
    summary_rows: list[dict] = []
    for method in METHODS:
        method_rows = [row for row in rows if row["method"] == method]
        summary_rows.append({
            "method": method,
            "sample_count": len(method_rows),
            "mean_measurement_nmse_db": mean([row["measurement_nmse_db"] for row in method_rows]),
            "mean_gain_vs_grid_db": mean([row["gain_vs_grid_db"] for row in method_rows]),
            "mean_angle_bin_rmse": mean([row["angle_bin_rmse"] for row in method_rows]),
            "mean_delay_bin_rmse": mean([row["delay_bin_rmse"] for row in method_rows]),
            "mean_doppler_bin_rmse": mean([row["doppler_bin_rmse"] for row in method_rows]),
            "mean_normalized_joint_bin_rmse": mean([row["normalized_joint_bin_rmse"] for row in method_rows]),
            "mean_matched_fraction_within_half_bin": mean([row["matched_fraction_within_half_bin"] for row in method_rows]),
            "median_wall_clock_ms": median([row["wall_clock_ms"] for row in method_rows]),
        })
    summary_path = output_dir / "matched_accuracy_summary.csv"
    write_csv(summary_path, summary_rows)
    summary = {row["method"]: row for row in summary_rows}
    nomp = summary["tensor_nomp3d_known_order_v1"]
    scalar = summary["fixed_source_trained_scalar_interpolation_plus_ls"]
    metrics = {
        "row_count": len(rows),
        "sample_count_per_method": nomp["sample_count"],
        "nomp_mean_gain_vs_grid_db": nomp["mean_gain_vs_grid_db"],
        "nomp_mean_measurement_nmse_db": nomp["mean_measurement_nmse_db"],
        "nomp_mean_normalized_joint_bin_rmse": nomp["mean_normalized_joint_bin_rmse"],
        "nomp_mean_matched_fraction_within_half_bin": nomp["mean_matched_fraction_within_half_bin"],
        "nomp_median_wall_clock_ms": nomp["median_wall_clock_ms"],
        "scalar_mean_gain_vs_grid_db": scalar["mean_gain_vs_grid_db"],
        "scalar_mean_measurement_nmse_db": scalar["mean_measurement_nmse_db"],
        "scalar_mean_normalized_joint_bin_rmse": scalar["mean_normalized_joint_bin_rmse"],
        "scalar_median_wall_clock_ms": scalar["median_wall_clock_ms"],
        "nomp_nmse_delta_vs_scalar_db": scalar["mean_measurement_nmse_db"] - nomp["mean_measurement_nmse_db"],
        "claim_update": "paper-scale-matched-comparison-pending-verification",
    }
    notes = [
        "All methods receive the same samples, known target count, and least-squares reconstruction contract.",
        "The fixed scalar is the mean source-trained G2 alpha and is not tuned on pilot truth.",
        "The 3-D cyclic NOMP-inspired comparator adapts detection/local-Newton/cyclic-feedback to a dense tensor; it is not an exact reproduction of the sparse-resource 2-D OFDM algorithm or CFAR stopping rule.",
        "This is the prespecified paper-scale matched-accuracy campaign; matched-regime caveats remain binding.",
    ]
    config = vars(args) | {"shape": list(shape)}
    write_run_manifest(
        output_dir,
        run_id="e12_tensor_nomp_matched_paper_5seed_20260630",
        command="python 04_experiments/eval/run_e12_tensor_nomp_matched_pilot.py",
        config=config,
        metrics=metrics,
        notes=notes,
        cwd=ROOT,
    )
    (output_dir / "summary.json").write_text(
        json.dumps({"summary_rows": summary_rows, "metrics": metrics}, indent=2) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# E12 3-D cyclic NOMP-inspired paper-scale matched campaign",
        "",
        "This campaign evaluates a fair paired metric contract at the prespecified paper scale.",
        "",
        "| Method | NMSE (dB) | Gain vs grid (dB) | Joint bin RMSE | Within 0.5 bin | Median ms |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in summary_rows:
        lines.append(
            f"| {row['method']} | {row['mean_measurement_nmse_db']:.4f} | "
            f"{row['mean_gain_vs_grid_db']:.4f} | {row['mean_normalized_joint_bin_rmse']:.6f} | "
            f"{row['mean_matched_fraction_within_half_bin']:.4f} | {row['median_wall_clock_ms']:.2f} |"
        )
    lines.extend(["", *[f"- {note}" for note in notes]])
    (output_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
