"""Unified steady-state CPU benchmark for the complete local estimator family."""

from __future__ import annotations

import os


for _thread_variable in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_thread_variable] = "1"

import argparse
import json
from pathlib import Path
import sys
import time

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_active_modules"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from baseline.local_refinement import (  # noqa: E402
    axiswise_candan_bins,
    axiswise_quadratic_peak_bins,
    one_step_fixed_support_newton_bins,
    separable_cartesian_local_diagnostics,
)
from common.manifest import write_run_manifest  # noqa: E402
from common.seed import seed_all  # noqa: E402
from common.tsp_revision_metrics import (  # noqa: E402
    matched_component_metrics,
    write_csv,
    write_release_metadata,
)
from data.offgrid_tensor import (  # noqa: E402
    estimate_from_bins_lstsq,
    generate_offgrid_tensor_sample,
    measurement_nmse_db,
    topk_grid_bins,
)
from run_e12_tensor_nomp_matched_pilot import truth_bins  # noqa: E402


METHODS = (
    "grid_fft_topL_joint_ls",
    "axiswise_quadratic_peak_joint_ls",
    "axiswise_candan_joint_ls",
    "residual_gated_candan_joint_ls",
    "one_step_fixed_support_newton_joint_ls",
    "cartesian_local_joint_ls",
    "residual_gated_cartesian_local_joint_ls",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shape", type=int, nargs=3, default=(128, 16, 32))
    parser.add_argument("--l-values", type=int, nargs="+", default=(2, 4, 8))
    parser.add_argument("--snrs", type=float, nargs="+", default=(0.0, 10.0, 20.0, 30.0))
    parser.add_argument(
        "--test-seeds",
        type=int,
        nargs="+",
        default=(20260630, 20260701, 20260702, 20260703, 20260704),
    )
    parser.add_argument("--samples-per-cell-seed", type=int, default=20)
    parser.add_argument("--offset-radius", type=float, default=0.35)
    parser.add_argument("--search-radius", type=float, default=0.45)
    parser.add_argument("--search-points", type=int, default=5)
    parser.add_argument("--warmup-runs", type=int, default=1)
    parser.add_argument("--timed-repeats", type=int, default=3)
    parser.add_argument("--gate-threshold", type=float)
    parser.add_argument("--output-dir-name", default="tsp_unified_runtime_paper")
    return parser.parse_args()


def residual_fraction(measurement: np.ndarray, estimate: np.ndarray) -> float:
    return float(
        np.linalg.norm(measurement - estimate) ** 2
        / max(np.linalg.norm(measurement) ** 2, 1e-300)
    )


def load_gate_threshold(explicit: float | None) -> float:
    if explicit is not None:
        return float(explicit)
    for directory in ("tsp_controlled_local_family_paper", "tsp_cost_matched_local_paper"):
        path = ROOT / "05_results" / directory / "summary.json"
        if path.exists():
            return float(json.loads(path.read_text(encoding="utf-8"))["gate"]["threshold"])
    raise FileNotFoundError("Run the controlled local-family experiment or pass --gate-threshold")


def evaluate_method(
    method: str,
    measurement: np.ndarray,
    clean: np.ndarray,
    truth: np.ndarray,
    n_targets: int,
    shape: tuple[int, int, int],
    search_radius: float,
    search_points: int,
    gate_threshold: float,
) -> dict[str, object]:
    start = time.perf_counter_ns()
    coarse = np.asarray(topk_grid_bins(measurement, n_targets), dtype=float)
    fft_support_ms = (time.perf_counter_ns() - start) / 1e6
    local_update_ms = 0.0
    grid_ls_ms = 0.0
    final_ls_ms = 0.0
    gate_decision_ms = 0.0
    gate_pass = 0
    margin = float("nan")
    saturation = float("nan")

    if method == "grid_fft_topL_joint_ls":
        bins = coarse
        start = time.perf_counter_ns()
        reconstruction = estimate_from_bins_lstsq(
            measurement, shape, [tuple(item) for item in bins]
        )
        final_ls_ms = (time.perf_counter_ns() - start) / 1e6
    elif method == "axiswise_quadratic_peak_joint_ls":
        start = time.perf_counter_ns()
        bins = axiswise_quadratic_peak_bins(measurement, coarse)
        local_update_ms = (time.perf_counter_ns() - start) / 1e6
        start = time.perf_counter_ns()
        reconstruction = estimate_from_bins_lstsq(
            measurement, shape, [tuple(item) for item in bins]
        )
        final_ls_ms = (time.perf_counter_ns() - start) / 1e6
    elif method == "axiswise_candan_joint_ls":
        start = time.perf_counter_ns()
        bins = axiswise_candan_bins(measurement, coarse)
        local_update_ms = (time.perf_counter_ns() - start) / 1e6
        start = time.perf_counter_ns()
        reconstruction = estimate_from_bins_lstsq(
            measurement, shape, [tuple(item) for item in bins]
        )
        final_ls_ms = (time.perf_counter_ns() - start) / 1e6
    elif method == "residual_gated_candan_joint_ls":
        start = time.perf_counter_ns()
        grid_reconstruction = estimate_from_bins_lstsq(
            measurement, shape, [tuple(item) for item in coarse]
        )
        grid_ls_ms = (time.perf_counter_ns() - start) / 1e6
        start = time.perf_counter_ns()
        candan_bins = axiswise_candan_bins(measurement, coarse)
        local_update_ms = (time.perf_counter_ns() - start) / 1e6
        start = time.perf_counter_ns()
        candan_reconstruction = estimate_from_bins_lstsq(
            measurement, shape, [tuple(item) for item in candan_bins]
        )
        final_ls_ms = (time.perf_counter_ns() - start) / 1e6
        start = time.perf_counter_ns()
        residual_reduction = residual_fraction(
            measurement, grid_reconstruction
        ) - residual_fraction(measurement, candan_reconstruction)
        gate_pass = int(residual_reduction >= gate_threshold)
        bins = candan_bins if gate_pass else coarse
        reconstruction = candan_reconstruction if gate_pass else grid_reconstruction
        gate_decision_ms = (time.perf_counter_ns() - start) / 1e6
    elif method == "one_step_fixed_support_newton_joint_ls":
        start = time.perf_counter_ns()
        bins = one_step_fixed_support_newton_bins(measurement, coarse).bins
        local_update_ms = (time.perf_counter_ns() - start) / 1e6
        start = time.perf_counter_ns()
        reconstruction = estimate_from_bins_lstsq(
            measurement, shape, [tuple(item) for item in bins]
        )
        final_ls_ms = (time.perf_counter_ns() - start) / 1e6
    elif method == "cartesian_local_joint_ls":
        start = time.perf_counter_ns()
        result = separable_cartesian_local_diagnostics(
            measurement,
            coarse,
            search_radius=search_radius,
            search_points=search_points,
        )
        local_update_ms = (time.perf_counter_ns() - start) / 1e6
        bins = result.bins
        margin = result.minimum_normalized_margin
        saturation = result.boundary_saturation_rate
        start = time.perf_counter_ns()
        reconstruction = estimate_from_bins_lstsq(
            measurement, shape, [tuple(item) for item in bins]
        )
        final_ls_ms = (time.perf_counter_ns() - start) / 1e6
    elif method == "residual_gated_cartesian_local_joint_ls":
        start = time.perf_counter_ns()
        grid_reconstruction = estimate_from_bins_lstsq(
            measurement, shape, [tuple(item) for item in coarse]
        )
        grid_ls_ms = (time.perf_counter_ns() - start) / 1e6
        start = time.perf_counter_ns()
        result = separable_cartesian_local_diagnostics(
            measurement,
            coarse,
            search_radius=search_radius,
            search_points=search_points,
        )
        local_update_ms = (time.perf_counter_ns() - start) / 1e6
        margin = result.minimum_normalized_margin
        saturation = result.boundary_saturation_rate
        start = time.perf_counter_ns()
        local_reconstruction = estimate_from_bins_lstsq(
            measurement, shape, [tuple(item) for item in result.bins]
        )
        final_ls_ms = (time.perf_counter_ns() - start) / 1e6
        start = time.perf_counter_ns()
        residual_reduction = residual_fraction(measurement, grid_reconstruction) - residual_fraction(
            measurement, local_reconstruction
        )
        gate_pass = int(residual_reduction >= gate_threshold)
        bins = result.bins if gate_pass else coarse
        reconstruction = local_reconstruction if gate_pass else grid_reconstruction
        gate_decision_ms = (time.perf_counter_ns() - start) / 1e6
    else:
        raise ValueError(f"unknown method: {method}")

    total_ms = fft_support_ms + local_update_ms + grid_ls_ms + final_ls_ms + gate_decision_ms
    matched = matched_component_metrics(bins, truth, shape)
    return {
        "measurement_nmse_db": measurement_nmse_db(reconstruction, clean),
        "per_component_half_bin_hit": matched["per_component_hit_rate"],
        "all_components_half_bin_hit": int(matched["all_components_hit"]),
        "gate_pass": gate_pass,
        "minimum_candidate_margin": margin,
        "boundary_saturation_rate": saturation,
        "fft_support_ms": fft_support_ms,
        "local_update_ms": local_update_ms,
        "grid_ls_ms": grid_ls_ms,
        "final_ls_ms": final_ls_ms,
        "gate_decision_ms": gate_decision_ms,
        "wall_clock_ms": total_ms,
    }


def median_timing(records: list[dict[str, object]]) -> dict[str, float]:
    keys = (
        "fft_support_ms",
        "local_update_ms",
        "grid_ls_ms",
        "final_ls_ms",
        "gate_decision_ms",
        "wall_clock_ms",
    )
    return {key: float(np.median([float(record[key]) for record in records])) for key in keys}


def main() -> None:
    args = parse_args()
    if args.timed_repeats < 1 or args.warmup_runs < 0:
        raise ValueError("timed repeats must be positive and warmup runs nonnegative")
    shape = tuple(int(value) for value in args.shape)
    gate_threshold = load_gate_threshold(args.gate_threshold)
    rows: list[dict[str, object]] = []
    scene_number = 0
    campaign_start = time.perf_counter()

    for seed in args.test_seeds:
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
                    method_order = METHODS[scene_number % len(METHODS) :] + METHODS[: scene_number % len(METHODS)]
                    for method in method_order:
                        for _ in range(args.warmup_runs):
                            evaluate_method(
                                method,
                                sample.measurement,
                                sample.clean,
                                truth,
                                n_targets,
                                shape,
                                args.search_radius,
                                args.search_points,
                                gate_threshold,
                            )
                        repetitions = [
                            evaluate_method(
                                method,
                                sample.measurement,
                                sample.clean,
                                truth,
                                n_targets,
                                shape,
                                args.search_radius,
                                args.search_points,
                                gate_threshold,
                            )
                            for _ in range(args.timed_repeats)
                        ]
                        accuracy = repetitions[0]
                        rows.append(
                            {
                                "seed": seed,
                                "snr_db": snr_db,
                                "n_targets": n_targets,
                                "sample_index": sample_index,
                                "method": method,
                                "measurement_nmse_db": accuracy["measurement_nmse_db"],
                                "per_component_half_bin_hit": accuracy["per_component_half_bin_hit"],
                                "all_components_half_bin_hit": accuracy["all_components_half_bin_hit"],
                                "gate_pass": accuracy["gate_pass"],
                                "minimum_candidate_margin": accuracy["minimum_candidate_margin"],
                                "boundary_saturation_rate": accuracy["boundary_saturation_rate"],
                                **median_timing(repetitions),
                            }
                        )
                    scene_number += 1

    per_seed: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []
    for method in METHODS:
        method_rows = [row for row in rows if row["method"] == method]
        for seed in args.test_seeds:
            selected = [row for row in method_rows if int(row["seed"]) == seed]
            per_seed.append(
                {
                    "seed": seed,
                    "method": method,
                    "scene_count": len(selected),
                    "mean_measurement_nmse_db": float(np.mean([float(row["measurement_nmse_db"]) for row in selected])),
                    "mean_per_component_half_bin_hit": float(np.mean([float(row["per_component_half_bin_hit"]) for row in selected])),
                    "median_wall_clock_ms": float(np.median([float(row["wall_clock_ms"]) for row in selected])),
                }
            )
        summary_rows.append(
            {
                "method": method,
                "scene_count": len(method_rows),
                "mean_measurement_nmse_db": float(np.mean([float(row["measurement_nmse_db"]) for row in method_rows])),
                "mean_per_component_half_bin_hit": float(np.mean([float(row["per_component_half_bin_hit"]) for row in method_rows])),
                "median_fft_support_ms": float(np.median([float(row["fft_support_ms"]) for row in method_rows])),
                "median_local_update_ms": float(np.median([float(row["local_update_ms"]) for row in method_rows])),
                "median_grid_ls_ms": float(np.median([float(row["grid_ls_ms"]) for row in method_rows])),
                "median_final_ls_ms": float(np.median([float(row["final_ls_ms"]) for row in method_rows])),
                "median_gate_decision_ms": float(np.median([float(row["gate_decision_ms"]) for row in method_rows])),
                "median_wall_clock_ms": float(np.median([float(row["wall_clock_ms"]) for row in method_rows])),
            }
        )

    output = ROOT / "05_results" / args.output_dir_name
    write_csv(output / "per_scene.csv", rows)
    write_csv(output / "per_seed.csv", per_seed)
    write_csv(output / "summary.csv", summary_rows)
    config = vars(args) | {
        "shape": list(shape),
        "gate_threshold": gate_threshold,
        "dtype": "complex128",
        "thread_count": 1,
        "scene_count": scene_number,
        "elapsed_seconds": time.perf_counter() - campaign_start,
    }
    summary = {"config": config, "methods": summary_rows}
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    command = "python 04_experiments/eval/run_tsp_unified_runtime_benchmark.py"
    write_release_metadata(
        output,
        config=config,
        seeds=[{"split": "test", "seed": seed} for seed in args.test_seeds],
        command=command,
    )
    write_run_manifest(
        output,
        run_id="tsp_unified_runtime_paper_20260829",
        command=command,
        config=config,
        metrics={"scene_count": scene_number, "timed_repeats": args.timed_repeats},
        notes=[
            "Every method starts from the noisy tensor and includes FFT support selection and final joint LS.",
            "Reported stage and total times are per-scene medians over repeated steady-state executions.",
        ],
        cwd=ROOT,
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
