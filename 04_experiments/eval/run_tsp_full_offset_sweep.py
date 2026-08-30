"""Full-bin-offset robustness, radius sensitivity, and support-quality audit."""

from __future__ import annotations

import argparse
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
    separable_cartesian_local_diagnostics,
)
from common.manifest import write_run_manifest  # noqa: E402
from common.seed import seed_all  # noqa: E402
from common.tsp_revision_metrics import (  # noqa: E402
    candidate_axis_correctness,
    candidate_interference_diagnostics,
    design_condition_number,
    matched_component_metrics,
    minimum_circular_separation,
    refined_collision_rate,
    support_quality_metrics,
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
from run_tsp_controlled_local_family_baselines import calibrate_residual_threshold  # noqa: E402


PRIMARY_METHODS = (
    "grid_fft_topL_joint_ls",
    "axiswise_quadratic_peak_joint_ls",
    "axiswise_candan_joint_ls",
    "one_step_fixed_support_newton_joint_ls",
    "cartesian_local_joint_ls",
    "residual_gated_cartesian_local_joint_ls",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shape", type=int, nargs=3, default=(128, 16, 32))
    parser.add_argument("--l-values", type=int, nargs="+", default=(2, 4, 8))
    parser.add_argument("--snrs", type=float, nargs="+", default=(0.0, 10.0, 20.0, 30.0))
    parser.add_argument("--validation-seeds", type=int, nargs="+", default=(20260808, 20260809))
    parser.add_argument(
        "--test-seeds",
        type=int,
        nargs="+",
        default=(20260630, 20260701, 20260702, 20260703, 20260704),
    )
    parser.add_argument("--samples-per-cell-seed", type=int, default=20)
    parser.add_argument("--offset-radius", type=float, default=0.49)
    parser.add_argument("--search-radii", type=float, nargs="+", default=(0.25, 0.35, 0.45, 0.50, 0.55))
    parser.add_argument("--primary-search-radius", type=float, default=0.45)
    parser.add_argument("--search-points", type=int, default=5)
    parser.add_argument("--minimum-validation-positive-recall", type=float, default=0.9)
    parser.add_argument("--output-dir-name", default="tsp_full_offset_sweep_paper")
    return parser.parse_args()


def residual_fraction(measurement: np.ndarray, estimate: np.ndarray) -> float:
    return float(
        np.linalg.norm(measurement - estimate) ** 2
        / max(np.linalg.norm(measurement) ** 2, 1e-300)
    )


def offset_bucket(offset: float) -> str:
    value = abs(float(offset))
    if value < 0.1:
        return "[0.00,0.10)"
    if value < 0.2:
        return "[0.10,0.20)"
    if value < 0.3:
        return "[0.20,0.30)"
    if value < 0.4:
        return "[0.30,0.40)"
    return "[0.40,0.49]"


def seed_mean_ci(rows: list[dict[str, object]], key: str) -> tuple[float, float, float]:
    seeds = sorted({int(row["seed"]) for row in rows})
    seed_means = np.asarray(
        [np.mean([float(row[key]) for row in rows if int(row["seed"]) == seed]) for seed in seeds],
        dtype=float,
    )
    center = float(np.mean(seed_means))
    if len(seed_means) < 2:
        return center, center, center
    half = float(
        student_t.ppf(0.975, len(seed_means) - 1)
        * np.std(seed_means, ddof=1)
        / np.sqrt(len(seed_means))
    )
    return center, center - half, center + half


def evaluate_bins(
    bins: np.ndarray,
    measurement: np.ndarray,
    clean: np.ndarray,
    truth: np.ndarray,
    shape: tuple[int, int, int],
) -> tuple[np.ndarray, dict[str, object]]:
    reconstruction = estimate_from_bins_lstsq(
        measurement, shape, [tuple(item) for item in bins]
    )
    matched = matched_component_metrics(bins, truth, shape)
    return reconstruction, {
        "bins": bins,
        "measurement_nmse_db": measurement_nmse_db(reconstruction, clean),
        "per_component_half_bin_hit": matched["per_component_hit_rate"],
        "all_components_half_bin_hit": float(matched["all_components_hit"]),
        "errors_by_truth": matched["errors_by_truth"],
        "design_condition": design_condition_number(shape, bins),
        "collision_rate": refined_collision_rate(bins, shape),
    }


def summarize_methods(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for method in PRIMARY_METHODS:
        nmse_key = f"{method}_nmse_db"
        hit_key = f"{method}_per_component_half_bin_hit"
        selected = [row for row in rows if row["split"] == "test"]
        nmse, nmse_low, nmse_high = seed_mean_ci(selected, nmse_key)
        hit, hit_low, hit_high = seed_mean_ci(selected, hit_key)
        output.append(
            {
                "method": method,
                "scene_count": len(selected),
                "mean_measurement_nmse_db": nmse,
                "measurement_nmse_ci95_low_db": nmse_low,
                "measurement_nmse_ci95_high_db": nmse_high,
                "mean_per_component_half_bin_hit": hit,
                "hit_ci95_low": hit_low,
                "hit_ci95_high": hit_high,
                "mean_gain_vs_grid_db": float(
                    np.mean(
                        [
                            float(row["grid_fft_topL_joint_ls_nmse_db"]) - float(row[nmse_key])
                            for row in selected
                        ]
                    )
                ),
            }
        )
    return output


def summarize_edges(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    test = [row for row in rows if row["split"] == "test"]
    for method in PRIMARY_METHODS:
        for axis in ("angle", "delay", "doppler"):
            for bucket in ("[0.00,0.10)", "[0.10,0.20)", "[0.20,0.30)", "[0.30,0.40)", "[0.40,0.49]"):
                selected = [
                    row
                    for row in test
                    if row["method"] == method and row["axis"] == axis and row["offset_bucket"] == bucket
                ]
                if not selected:
                    continue
                output.append(
                    {
                        "method": method,
                        "axis": axis,
                        "offset_bucket": bucket,
                        "component_axis_count": len(selected),
                        "mean_absolute_bin_error": float(np.mean([float(row["absolute_bin_error"]) for row in selected])),
                        "half_bin_axis_hit_rate": float(np.mean([float(row["half_bin_axis_hit"]) for row in selected])),
                        "candidate_axis_correctness": float(
                            np.mean(
                                [float(row["candidate_axis_correct"]) for row in selected]
                            )
                        )
                        if method == "cartesian_local_joint_ls"
                        else float("nan"),
                    }
                )
    return output


def support_strata(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    test = [row for row in rows if row["split"] == "test"]
    condition_values = np.asarray([float(row["coarse_design_condition"]) for row in test])
    condition_edges = np.quantile(condition_values, [0.25, 0.5, 0.75])
    labeled: list[tuple[str, str, list[dict[str, object]]]] = []
    for quality in sorted({float(row["q_sup"]) for row in test}):
        labeled.append(("coarse_support_quality", f"q_sup={quality:.3f}", [row for row in test if float(row["q_sup"]) == quality]))
    labeled.extend(
        [
            ("duplicate_neighborhood", "none", [row for row in test if float(row["duplicate_neighborhood_rate"]) == 0.0]),
            ("duplicate_neighborhood", "present", [row for row in test if float(row["duplicate_neighborhood_rate"]) > 0.0]),
        ]
    )
    lower = -float("inf")
    for index, upper in enumerate([*condition_edges, float("inf")], start=1):
        labeled.append(
            (
                "coarse_condition_quartile",
                f"Q{index}",
                [
                    row
                    for row in test
                    if lower < float(row["coarse_design_condition"]) <= upper
                ],
            )
        )
        lower = float(upper)

    output: list[dict[str, object]] = []
    for stratum_type, stratum, selected in labeled:
        if not selected:
            continue
        output.append(
            {
                "stratum_type": stratum_type,
                "stratum": stratum,
                "scene_count": len(selected),
                "mean_q_sup": float(np.mean([float(row["q_sup"]) for row in selected])),
                "mean_local_gain_vs_grid_db": float(np.mean([float(row["local_gain_vs_grid_db"]) for row in selected])),
                "local_harmful_update_rate": float(np.mean([float(row["harmful_local_update"]) for row in selected])),
                "mean_gated_gain_vs_grid_db": float(np.mean([float(row["gated_gain_vs_grid_db"]) for row in selected])),
                "gate_pass_rate": float(np.mean([float(row["gate_pass"]) for row in selected])),
                "mean_local_per_component_hit": float(
                    np.mean([float(row["cartesian_local_joint_ls_per_component_half_bin_hit"]) for row in selected])
                ),
            }
        )
    return output


def main() -> None:
    args = parse_args()
    if not any(np.isclose(radius, args.primary_search_radius) for radius in args.search_radii):
        raise ValueError("primary search radius must be included in --search-radii")
    shape = tuple(int(value) for value in args.shape)
    scene_rows: list[dict[str, object]] = []
    axis_rows: list[dict[str, object]] = []
    radius_rows: list[dict[str, object]] = []
    started = time.perf_counter()

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
                        gains = np.asarray([target.gain for target in sample.targets])
                        amplitudes = np.maximum(np.abs(gains), 1e-15)
                        dynamic_range_db = 20.0 * np.log10(np.max(amplitudes) / np.min(amplitudes))
                        coarse = np.asarray(topk_grid_bins(sample.measurement, n_targets), dtype=float)
                        support = support_quality_metrics(coarse, truth, shape)
                        grid_reconstruction, grid = evaluate_bins(
                            coarse, sample.measurement, sample.clean, truth, shape
                        )

                        quadratic_bins = axiswise_quadratic_peak_bins(sample.measurement, coarse)
                        _, quadratic = evaluate_bins(
                            quadratic_bins, sample.measurement, sample.clean, truth, shape
                        )
                        candan_bins = axiswise_candan_bins(sample.measurement, coarse)
                        _, candan = evaluate_bins(
                            candan_bins, sample.measurement, sample.clean, truth, shape
                        )
                        newton_bins = one_step_fixed_support_newton_bins(
                            sample.measurement, coarse
                        ).bins
                        _, newton = evaluate_bins(
                            newton_bins, sample.measurement, sample.clean, truth, shape
                        )

                        primary_local = None
                        primary_local_reconstruction = None
                        primary_local_result = None
                        for radius in args.search_radii:
                            local_result = separable_cartesian_local_diagnostics(
                                sample.measurement,
                                coarse,
                                search_radius=radius,
                                search_points=args.search_points,
                            )
                            local_reconstruction, local_metrics = evaluate_bins(
                                local_result.bins,
                                sample.measurement,
                                sample.clean,
                                truth,
                                shape,
                            )
                            correctness, _ = candidate_axis_correctness(
                                coarse,
                                local_result.bins,
                                truth,
                                shape,
                                search_radius=radius,
                                search_points=args.search_points,
                            )
                            radius_rows.append(
                                {
                                    "split": split,
                                    "seed": seed,
                                    "snr_db": snr_db,
                                    "n_targets": n_targets,
                                    "sample_index": sample_index,
                                    "search_radius": radius,
                                    "measurement_nmse_db": local_metrics["measurement_nmse_db"],
                                    "gain_vs_grid_db": float(grid["measurement_nmse_db"])
                                    - float(local_metrics["measurement_nmse_db"]),
                                    "per_component_half_bin_hit": local_metrics["per_component_half_bin_hit"],
                                    "harmful_update": float(
                                        float(local_metrics["measurement_nmse_db"])
                                        > float(grid["measurement_nmse_db"])
                                    ),
                                    "candidate_axis_correctness": correctness,
                                    "boundary_saturation_rate": local_result.boundary_saturation_rate,
                                    "minimum_candidate_margin": local_result.minimum_normalized_margin,
                                }
                            )
                            if np.isclose(radius, args.primary_search_radius):
                                primary_local = local_metrics
                                primary_local_reconstruction = local_reconstruction
                                primary_local_result = local_result

                        assert primary_local is not None
                        assert primary_local_reconstruction is not None
                        assert primary_local_result is not None
                        theory = candidate_interference_diagnostics(
                            coarse,
                            truth,
                            gains,
                            shape,
                            search_radius=args.primary_search_radius,
                            search_points=args.search_points,
                            noise_variance=sample.noise_variance,
                        )
                        candidate_correctness, candidate_matrix = candidate_axis_correctness(
                            coarse,
                            primary_local_result.bins,
                            truth,
                            shape,
                            search_radius=args.primary_search_radius,
                            search_points=args.search_points,
                        )
                        grid_residual = residual_fraction(sample.measurement, grid_reconstruction)
                        local_residual = residual_fraction(
                            sample.measurement, primary_local_reconstruction
                        )
                        method_results = {
                            "grid_fft_topL_joint_ls": grid,
                            "axiswise_quadratic_peak_joint_ls": quadratic,
                            "axiswise_candan_joint_ls": candan,
                            "one_step_fixed_support_newton_joint_ls": newton,
                            "cartesian_local_joint_ls": primary_local,
                        }
                        row: dict[str, object] = {
                            "split": split,
                            "seed": seed,
                            "snr_db": snr_db,
                            "n_targets": n_targets,
                            "sample_index": sample_index,
                            "dynamic_range_db": dynamic_range_db,
                            "minimum_true_separation_bins": minimum_circular_separation(truth, shape),
                            "coarse_design_condition": grid["design_condition"],
                            "refined_design_condition": primary_local["design_condition"],
                            "refined_collision_rate": primary_local["collision_rate"],
                            "candidate_axis_correctness": candidate_correctness,
                            "minimum_candidate_margin": primary_local_result.minimum_normalized_margin,
                            "mean_candidate_margin": primary_local_result.mean_normalized_margin,
                            "boundary_saturation_rate": primary_local_result.boundary_saturation_rate,
                            "residual_reduction_fraction": grid_residual - local_residual,
                            "local_gain_vs_grid_db": float(grid["measurement_nmse_db"])
                            - float(primary_local["measurement_nmse_db"]),
                            "harmful_local_update": float(
                                float(primary_local["measurement_nmse_db"])
                                > float(grid["measurement_nmse_db"])
                            ),
                            **support,
                            **theory,
                        }
                        for method, metrics in method_results.items():
                            row[f"{method}_nmse_db"] = metrics["measurement_nmse_db"]
                            row[f"{method}_per_component_half_bin_hit"] = metrics[
                                "per_component_half_bin_hit"
                            ]
                            row[f"{method}_all_components_half_bin_hit"] = metrics[
                                "all_components_half_bin_hit"
                            ]
                        scene_rows.append(row)

                        offsets = np.asarray(
                            [
                                [target.angle_offset, target.delay_offset, target.doppler_offset]
                                for target in sample.targets
                            ]
                        )
                        for method, metrics in method_results.items():
                            errors = np.asarray(metrics["errors_by_truth"], dtype=float)
                            for truth_index in range(n_targets):
                                for axis_index, axis_name in enumerate(("angle", "delay", "doppler")):
                                    axis_rows.append(
                                        {
                                            "split": split,
                                            "seed": seed,
                                            "snr_db": snr_db,
                                            "n_targets": n_targets,
                                            "sample_index": sample_index,
                                            "truth_index": truth_index,
                                            "axis": axis_name,
                                            "method": method,
                                            "absolute_true_offset": abs(offsets[truth_index, axis_index]),
                                            "offset_bucket": offset_bucket(offsets[truth_index, axis_index]),
                                            "absolute_bin_error": abs(errors[truth_index, axis_index]),
                                            "half_bin_axis_hit": float(
                                                abs(errors[truth_index, axis_index]) <= 0.5
                                            ),
                                            "candidate_axis_correct": float(
                                                candidate_matrix[truth_index, axis_index]
                                            )
                                            if method == "cartesian_local_joint_ls"
                                            else float("nan"),
                                        }
                                    )

    validation_rows = [row for row in scene_rows if row["split"] == "validation"]
    gate = calibrate_residual_threshold(
        validation_rows, args.minimum_validation_positive_recall
    )
    threshold = float(gate["threshold"])
    for row in scene_rows:
        passed = float(row["residual_reduction_fraction"]) >= threshold
        row["gate_pass"] = int(passed)
        row["gated_gain_vs_grid_db"] = float(row["local_gain_vs_grid_db"]) if passed else 0.0
        for metric in ("nmse_db", "per_component_half_bin_hit", "all_components_half_bin_hit"):
            local_key = f"cartesian_local_joint_ls_{metric}"
            grid_key = f"grid_fft_topL_joint_ls_{metric}"
            row[f"residual_gated_cartesian_local_joint_ls_{metric}"] = (
                row[local_key] if passed else row[grid_key]
            )

    axis_index = {
        (
            row["split"],
            int(row["seed"]),
            float(row["snr_db"]),
            int(row["n_targets"]),
            int(row["sample_index"]),
            int(row["truth_index"]),
            row["axis"],
            row["method"],
        ): row
        for row in axis_rows
    }
    gated_axis_rows: list[dict[str, object]] = []
    for scene in scene_rows:
        selected_method = (
            "cartesian_local_joint_ls" if int(scene["gate_pass"]) else "grid_fft_topL_joint_ls"
        )
        for truth_index in range(int(scene["n_targets"])):
            for axis_name in ("angle", "delay", "doppler"):
                key = (
                    scene["split"],
                    int(scene["seed"]),
                    float(scene["snr_db"]),
                    int(scene["n_targets"]),
                    int(scene["sample_index"]),
                    truth_index,
                    axis_name,
                    selected_method,
                )
                source = axis_index[key]
                gated_axis_rows.append(
                    {
                        **source,
                        "method": "residual_gated_cartesian_local_joint_ls",
                    }
                )
    axis_rows.extend(gated_axis_rows)

    test_radius = [row for row in radius_rows if row["split"] == "test"]
    radius_summary: list[dict[str, object]] = []
    for radius in args.search_radii:
        selected = [row for row in test_radius if np.isclose(float(row["search_radius"]), radius)]
        radius_summary.append(
            {
                "search_radius": radius,
                "scene_count": len(selected),
                "mean_gain_vs_grid_db": float(np.mean([float(row["gain_vs_grid_db"]) for row in selected])),
                "mean_per_component_half_bin_hit": float(np.mean([float(row["per_component_half_bin_hit"]) for row in selected])),
                "harmful_update_rate": float(np.mean([float(row["harmful_update"]) for row in selected])),
                "mean_candidate_axis_correctness": float(np.mean([float(row["candidate_axis_correctness"]) for row in selected])),
                "mean_boundary_saturation_rate": float(np.mean([float(row["boundary_saturation_rate"]) for row in selected])),
            }
        )

    output = ROOT / "05_results" / args.output_dir_name
    write_csv(output / "per_scene.csv", scene_rows)
    write_csv(output / "per_axis.csv", axis_rows)
    write_csv(output / "radius_per_scene.csv", radius_rows)
    method_summary = summarize_methods(scene_rows)
    edge_summary = summarize_edges(axis_rows)
    strata_summary = support_strata(scene_rows)
    write_csv(output / "method_summary.csv", method_summary)
    write_csv(output / "edge_offset_summary.csv", edge_summary)
    write_csv(output / "radius_summary.csv", radius_summary)
    write_csv(output / "support_quality_summary.csv", strata_summary)
    config = vars(args) | {
        "shape": list(shape),
        "gate_threshold": threshold,
        "validation_scene_count": len(validation_rows),
        "test_scene_count": len([row for row in scene_rows if row["split"] == "test"]),
        "elapsed_seconds": time.perf_counter() - started,
    }
    result = {
        "config": config,
        "gate": gate,
        "method_summary": method_summary,
        "radius_summary": radius_summary,
        "support_quality_summary": strata_summary,
    }
    (output / "summary.json").write_text(json.dumps(result, indent=2, allow_nan=True) + "\n", encoding="utf-8")
    command = "python 04_experiments/eval/run_tsp_full_offset_sweep.py"
    write_release_metadata(
        output,
        config=config,
        seeds=[
            *({"split": "validation", "seed": seed} for seed in args.validation_seeds),
            *({"split": "test", "seed": seed} for seed in args.test_seeds),
        ],
        command=command,
    )
    write_run_manifest(
        output,
        run_id="tsp_full_offset_sweep_paper_20260829",
        command=command,
        config=config,
        metrics={
            "gate_threshold": threshold,
            "test_scene_count": config["test_scene_count"],
            "offset_radius": args.offset_radius,
        },
        notes=[
            "The test spans the complete fractional-bin interval and reports edge-offset performance by axis.",
            "The same scenes support method, radius, support-quality, and conditioning comparisons.",
        ],
        cwd=ROOT,
    )
    print(json.dumps(result, indent=2, allow_nan=True))


if __name__ == "__main__":
    main()
