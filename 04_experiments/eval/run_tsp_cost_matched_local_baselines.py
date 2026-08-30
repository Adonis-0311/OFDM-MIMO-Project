from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
import time

import numpy as np
from scipy.stats import t as student_t


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_active_modules"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from baseline.local_refinement import (  # noqa: E402
    axiswise_candan_bins,
    axiswise_quadratic_peak_bins,
    one_step_fixed_support_newton_bins,
    separable_cartesian_local_bins,
)
from common.manifest import write_run_manifest  # noqa: E402
from common.seed import seed_all  # noqa: E402
from data.offgrid_tensor import (  # noqa: E402
    estimate_from_bins_lstsq,
    generate_offgrid_tensor_sample,
    measurement_nmse_db,
    topk_grid_bins,
)
from run_e12_tensor_nomp_matched_pilot import matched_bin_metrics, truth_bins  # noqa: E402


METHODS = (
    "grid_fft_topL_joint_ls",
    "axiswise_quadratic_peak_joint_ls",
    "axiswise_candan_joint_ls",
    "one_step_fixed_support_newton_joint_ls",
    "cartesian_local_joint_ls",
    "residual_gated_cartesian_local_joint_ls",
)


WORK_CONTRACT = {
    "grid_fft_topL_joint_ls": "one 3-D FFT; 0 local scores; one joint LS",
    "axiswise_quadratic_peak_joint_ls": "one 3-D FFT; 3DL power samples; one joint LS",
    "axiswise_candan_joint_ls": "one 3-D FFT; 3DL complex samples; one joint LS",
    "one_step_fixed_support_newton_joint_ls": "one 3-D FFT; L gradient/Hessian evaluations; <=5L trial scores; one joint LS",
    "cartesian_local_joint_ls": "one 3-D FFT; 125L full-observation scores; one joint LS",
    "residual_gated_cartesian_local_joint_ls": "one 3-D FFT; 125L scores; grid and local joint LS; one residual comparison",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shape", type=int, nargs=3, default=(128, 16, 32))
    parser.add_argument("--l-values", type=int, nargs="+", default=(2, 4, 8))
    parser.add_argument("--snrs", type=float, nargs="+", default=(0.0, 10.0, 20.0, 30.0))
    parser.add_argument(
        "--validation-seeds", type=int, nargs="+", default=(20260808, 20260809)
    )
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
    parser.add_argument("--minimum-validation-positive-recall", type=float, default=0.9)
    parser.add_argument("--output-dir-name", default="tsp_controlled_local_family_paper")
    return parser.parse_args()


def residual_fraction(measurement: np.ndarray, estimate: np.ndarray) -> float:
    return float(
        np.linalg.norm(measurement - estimate) ** 2
        / max(np.linalg.norm(measurement) ** 2, 1e-300)
    )


def calibrate_residual_threshold(
    records: list[dict[str, float | int | str]],
    minimum_positive_recall: float,
) -> dict[str, float]:
    values = np.asarray([float(record["residual_reduction_fraction"]) for record in records])
    candidates = np.unique(np.quantile(values, np.linspace(0.0, 1.0, 201)))
    positive = np.asarray([float(record["local_gain_vs_grid_db"]) > 0.0 for record in records])
    negative = np.asarray([float(record["local_gain_vs_grid_db"]) < 0.0 for record in records])
    gains = np.asarray([float(record["local_gain_vs_grid_db"]) for record in records])
    eligible: list[dict[str, float]] = []
    for threshold in candidates:
        passed = values >= threshold
        recall = float(np.mean(passed[positive])) if np.any(positive) else float("nan")
        if not np.isfinite(recall) or recall + 1e-12 < minimum_positive_recall:
            continue
        rejection = float(np.mean(~passed[negative])) if np.any(negative) else float("nan")
        gated_gain = float(np.mean(np.where(passed, gains, 0.0)))
        eligible.append(
            {
                "threshold": float(threshold),
                "validation_positive_recall": recall,
                "validation_negative_rejection": rejection,
                "validation_gated_gain_db": gated_gain,
                "validation_pass_rate": float(np.mean(passed)),
            }
        )
    if not eligible:
        raise RuntimeError("No residual threshold satisfies the validation recall constraint")
    eligible.sort(
        key=lambda item: (
            item["validation_negative_rejection"],
            item["validation_gated_gain_db"],
            item["validation_positive_recall"],
        ),
        reverse=True,
    )
    return eligible[0]


def method_row(
    *,
    base: dict[str, float | int | str],
    method: str,
    bins: np.ndarray,
    reconstruction: np.ndarray,
    clean: np.ndarray,
    truth: np.ndarray,
    shape: tuple[int, int, int],
    wall_clock_ms: float,
    extras: dict[str, float | int] | None = None,
) -> dict[str, float | int | str]:
    metrics = matched_bin_metrics(bins, truth, shape)
    return {
        **base,
        "method": method,
        "measurement_nmse_db": measurement_nmse_db(reconstruction, clean),
        **metrics,
        "wall_clock_ms": wall_clock_ms,
        **(extras or {}),
    }


def write_csv(path: Path, rows: list[dict[str, float | int | str]]) -> None:
    fields: list[str] = []
    for row in rows:
        for field in row:
            if field not in fields:
                fields.append(field)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def seed_mean_ci(rows: list[dict], key: str) -> tuple[float, float, float]:
    means = np.asarray(
        [
            np.mean([float(row[key]) for row in rows if int(row["seed"]) == seed])
            for seed in sorted({int(row["seed"]) for row in rows})
        ],
        dtype=float,
    )
    center = float(np.mean(means))
    if len(means) < 2:
        return center, center, center
    half = float(student_t.ppf(0.975, len(means) - 1) * np.std(means, ddof=1) / np.sqrt(len(means)))
    return center, center - half, center + half


def summarize(rows: list[dict]) -> list[dict[str, float | int | str]]:
    summary: list[dict[str, float | int | str]] = []
    grid_by_key = {
        (int(row["seed"]), float(row["snr_db"]), int(row["n_targets"]), int(row["sample_index"])): row
        for row in rows
        if row["method"] == "grid_fft_topL_joint_ls"
    }
    for method in METHODS:
        selected = [row for row in rows if row["method"] == method]
        nmse, nmse_low, nmse_high = seed_mean_ci(selected, "measurement_nmse_db")
        hit, hit_low, hit_high = seed_mean_ci(selected, "matched_fraction_within_half_bin")
        harmful = []
        gains = []
        for row in selected:
            key = (int(row["seed"]), float(row["snr_db"]), int(row["n_targets"]), int(row["sample_index"]))
            gain = float(grid_by_key[key]["measurement_nmse_db"]) - float(row["measurement_nmse_db"])
            gains.append(gain)
            harmful.append(gain < 0.0)
        summary.append(
            {
                "method": method,
                "sample_count": len(selected),
                "mean_measurement_nmse_db": nmse,
                "measurement_nmse_ci95_low_db": nmse_low,
                "measurement_nmse_ci95_high_db": nmse_high,
                "mean_gain_vs_grid_db": float(np.mean(gains)),
                "harmful_update_rate": float(np.mean(harmful)),
                "mean_all_axis_half_bin_hit": hit,
                "half_bin_hit_ci95_low": hit_low,
                "half_bin_hit_ci95_high": hit_high,
                "mean_angle_bin_rmse": float(np.mean([float(row["angle_bin_rmse"]) for row in selected])),
                "mean_delay_bin_rmse": float(np.mean([float(row["delay_bin_rmse"]) for row in selected])),
                "mean_doppler_bin_rmse": float(np.mean([float(row["doppler_bin_rmse"]) for row in selected])),
                "median_wall_clock_ms": float(np.median([float(row["wall_clock_ms"]) for row in selected])),
                "work_contract": WORK_CONTRACT[method],
            }
        )
    return summary


def main() -> None:
    args = parse_args()
    shape = tuple(int(value) for value in args.shape)
    period = np.asarray(shape, dtype=float)
    all_rows: list[dict[str, float | int | str]] = []
    gate_records: list[dict[str, float | int | str]] = []
    started_campaign = time.perf_counter()
    for split, seeds in (("validation", args.validation_seeds), ("test", args.test_seeds)):
        for seed in seeds:
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
                        base = {
                            "split": split,
                            "seed": seed,
                            "snr_db": snr_db,
                            "n_targets": n_targets,
                            "sample_index": sample_index,
                        }

                        stage_start = time.perf_counter()
                        coarse = np.asarray(topk_grid_bins(sample.measurement, n_targets), dtype=float)
                        fft_support_ms = (time.perf_counter() - stage_start) * 1000.0

                        stage_start = time.perf_counter()
                        grid_reconstruction = estimate_from_bins_lstsq(
                            sample.measurement, shape, [tuple(item) for item in coarse]
                        )
                        grid_ls_ms = (time.perf_counter() - stage_start) * 1000.0
                        grid_row = method_row(
                            base=base,
                            method="grid_fft_topL_joint_ls",
                            bins=coarse,
                            reconstruction=grid_reconstruction,
                            clean=sample.clean,
                            truth=truth,
                            shape=shape,
                            wall_clock_ms=fft_support_ms + grid_ls_ms,
                            extras={"fft_support_ms": fft_support_ms, "final_ls_ms": grid_ls_ms},
                        )

                        stage_start = time.perf_counter()
                        quadratic_bins = axiswise_quadratic_peak_bins(sample.measurement, coarse)
                        quadratic_update_ms = (time.perf_counter() - stage_start) * 1000.0
                        stage_start = time.perf_counter()
                        quadratic_reconstruction = estimate_from_bins_lstsq(
                            sample.measurement, shape, [tuple(item) for item in quadratic_bins]
                        )
                        quadratic_ls_ms = (time.perf_counter() - stage_start) * 1000.0
                        quadratic_row = method_row(
                            base=base,
                            method="axiswise_quadratic_peak_joint_ls",
                            bins=quadratic_bins,
                            reconstruction=quadratic_reconstruction,
                            clean=sample.clean,
                            truth=truth,
                            shape=shape,
                            wall_clock_ms=fft_support_ms + quadratic_update_ms + quadratic_ls_ms,
                            extras={
                                "fft_support_ms": fft_support_ms,
                                "local_update_ms": quadratic_update_ms,
                                "final_ls_ms": quadratic_ls_ms,
                            },
                        )

                        stage_start = time.perf_counter()
                        candan_bins = axiswise_candan_bins(sample.measurement, coarse)
                        candan_update_ms = (time.perf_counter() - stage_start) * 1000.0
                        stage_start = time.perf_counter()
                        candan_reconstruction = estimate_from_bins_lstsq(
                            sample.measurement, shape, [tuple(item) for item in candan_bins]
                        )
                        candan_ls_ms = (time.perf_counter() - stage_start) * 1000.0
                        candan_row = method_row(
                            base=base,
                            method="axiswise_candan_joint_ls",
                            bins=candan_bins,
                            reconstruction=candan_reconstruction,
                            clean=sample.clean,
                            truth=truth,
                            shape=shape,
                            wall_clock_ms=fft_support_ms + candan_update_ms + candan_ls_ms,
                            extras={
                                "fft_support_ms": fft_support_ms,
                                "local_update_ms": candan_update_ms,
                                "final_ls_ms": candan_ls_ms,
                            },
                        )

                        stage_start = time.perf_counter()
                        newton = one_step_fixed_support_newton_bins(sample.measurement, coarse)
                        newton_update_ms = (time.perf_counter() - stage_start) * 1000.0
                        stage_start = time.perf_counter()
                        newton_reconstruction = estimate_from_bins_lstsq(
                            sample.measurement, shape, [tuple(item) for item in newton.bins]
                        )
                        newton_ls_ms = (time.perf_counter() - stage_start) * 1000.0
                        newton_row = method_row(
                            base=base,
                            method="one_step_fixed_support_newton_joint_ls",
                            bins=newton.bins,
                            reconstruction=newton_reconstruction,
                            clean=sample.clean,
                            truth=truth,
                            shape=shape,
                            wall_clock_ms=fft_support_ms + newton_update_ms + newton_ls_ms,
                            extras={
                                "fft_support_ms": fft_support_ms,
                                "local_update_ms": newton_update_ms,
                                "final_ls_ms": newton_ls_ms,
                                "accepted_newton_updates": newton.accepted_updates,
                                "derivative_evaluations": newton.derivative_evaluations,
                                "trial_score_evaluations": newton.trial_score_evaluations,
                            },
                        )

                        stage_start = time.perf_counter()
                        local_bins = separable_cartesian_local_bins(
                            sample.measurement,
                            coarse,
                            search_radius=args.search_radius,
                            search_points=args.search_points,
                        )
                        local_bins = np.mod(local_bins, period)
                        local_update_ms = (time.perf_counter() - stage_start) * 1000.0
                        stage_start = time.perf_counter()
                        local_reconstruction = estimate_from_bins_lstsq(
                            sample.measurement, shape, [tuple(item) for item in local_bins]
                        )
                        local_ls_ms = (time.perf_counter() - stage_start) * 1000.0
                        local_row = method_row(
                            base=base,
                            method="cartesian_local_joint_ls",
                            bins=local_bins,
                            reconstruction=local_reconstruction,
                            clean=sample.clean,
                            truth=truth,
                            shape=shape,
                            wall_clock_ms=fft_support_ms + local_update_ms + local_ls_ms,
                            extras={
                                "fft_support_ms": fft_support_ms,
                                "local_update_ms": local_update_ms,
                                "final_ls_ms": local_ls_ms,
                            },
                        )

                        decision_start = time.perf_counter()
                        grid_residual = residual_fraction(sample.measurement, grid_reconstruction)
                        local_residual = residual_fraction(sample.measurement, local_reconstruction)
                        decision_ms = (time.perf_counter() - decision_start) * 1000.0
                        gate_records.append(
                            {
                                **base,
                                "residual_reduction_fraction": grid_residual - local_residual,
                                "local_gain_vs_grid_db": float(grid_row["measurement_nmse_db"])
                                - float(local_row["measurement_nmse_db"]),
                                "grid_method_index": len(all_rows),
                                "local_method_index": len(all_rows) + 4,
                                "gate_decision_ms": decision_ms,
                                "gated_wall_clock_ms": fft_support_ms
                                + grid_ls_ms
                                + local_update_ms
                                + local_ls_ms
                                + decision_ms,
                            }
                        )
                        all_rows.extend(
                            [grid_row, quadratic_row, candan_row, newton_row, local_row]
                        )

    validation_records = [record for record in gate_records if record["split"] == "validation"]
    gate = calibrate_residual_threshold(
        validation_records, args.minimum_validation_positive_recall
    )
    threshold = gate["threshold"]
    for record in gate_records:
        if record["split"] != "test":
            continue
        grid_row = all_rows[int(record["grid_method_index"])]
        local_row = all_rows[int(record["local_method_index"])]
        passed = float(record["residual_reduction_fraction"]) >= threshold
        selected = local_row if passed else grid_row
        gated_row = {
            **{key: selected[key] for key in selected if key not in {"method", "wall_clock_ms"}},
            "method": "residual_gated_cartesian_local_joint_ls",
            "wall_clock_ms": float(record["gated_wall_clock_ms"]),
            "gate_pass": int(passed),
            "residual_reduction_fraction": float(record["residual_reduction_fraction"]),
            "fft_support_ms": float(local_row["fft_support_ms"]),
            "local_update_ms": float(local_row["local_update_ms"]),
            "grid_ls_ms": float(grid_row["final_ls_ms"]),
            "final_ls_ms": float(local_row["final_ls_ms"]),
            "gate_decision_ms": float(record["gate_decision_ms"]),
        }
        all_rows.append(gated_row)

    test_rows = [row for row in all_rows if row["split"] == "test"]
    summary_rows = summarize(test_rows)
    output_dir = ROOT / "05_results" / args.output_dir_name
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "local_family_rows.csv", test_rows)
    write_csv(output_dir / "local_family_summary.csv", summary_rows)
    write_csv(output_dir / "gate_calibration_rows.csv", validation_records)
    result = {
        "config": vars(args) | {"shape": list(shape)},
        "gate": gate,
        "validation_scene_count": len(validation_records),
        "test_scene_count": len(args.test_seeds)
        * len(args.snrs)
        * len(args.l_values)
        * args.samples_per_cell_seed,
        "test_row_count": len(test_rows),
        "summary_rows": summary_rows,
        "elapsed_seconds": time.perf_counter() - started_campaign,
        "notes": [
            "All local-family methods share each noisy tensor, known L, FFT top-L support, periodic boundaries, and one final joint-LS convention.",
            "The residual threshold is calibrated only on independent validation seeds and is frozen before the five test seeds are summarized.",
            "Reference CPU times reuse the common FFT-support stage measured once per scene; stage-wise columns expose implementation boundaries.",
            "The Newton comparator uses one gradient/Hessian direction per selected peak with deterministic backtracking and no residual deflation or cyclic update.",
            "The Candan comparator applies the published finite-length correction to complex three-DFT-sample ratios independently on each axis.",
        ],
    }
    (output_dir / "summary.json").write_text(
        json.dumps(result, indent=2, allow_nan=True) + "\n", encoding="utf-8"
    )
    write_run_manifest(
        output_dir,
        run_id="tsp_controlled_local_family_paper_20260829",
        command="python 04_experiments/eval/run_tsp_controlled_local_family_baselines.py",
        config=result["config"],
        metrics={
            "validation_scene_count": result["validation_scene_count"],
            "test_scene_count": result["test_scene_count"],
            "gate_threshold": gate["threshold"],
        },
        notes=result["notes"],
        cwd=ROOT,
    )
    print(json.dumps(result, indent=2, allow_nan=True))


if __name__ == "__main__":
    main()
