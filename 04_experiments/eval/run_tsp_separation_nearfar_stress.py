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
    separable_cartesian_local_diagnostics,
)
from common.manifest import write_run_manifest  # noqa: E402
from common.tsp_revision_metrics import (  # noqa: E402
    assignment_by_normalized_bin_distance,
    candidate_axis_correctness,
    candidate_interference_component_diagnostics,
    candidate_interference_diagnostics,
    distinct_pair_metrics,
    matched_component_metrics,
    support_quality_metrics,
    write_release_metadata,
)
from data.offgrid_tensor import (  # noqa: E402
    estimate_from_bins_lstsq,
    measurement_nmse_db,
    tensor_atom,
    topk_grid_bins,
)
from run_tsp_controlled_local_family_baselines import calibrate_residual_threshold  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shape", type=int, nargs=3, default=(128, 16, 32))
    parser.add_argument("--n-targets", type=int, default=4)
    parser.add_argument("--separations", type=float, nargs="+", default=(0.25, 0.5, 1.0, 2.0))
    parser.add_argument("--dynamic-ranges-db", type=float, nargs="+", default=(0.0, 10.0, 20.0))
    parser.add_argument("--snrs", type=float, nargs="+", default=(0.0, 10.0, 20.0, 30.0))
    parser.add_argument("--validation-seeds", type=int, nargs="+", default=(20260820, 20260821))
    parser.add_argument(
        "--test-seeds", type=int, nargs="+",
        default=(20260822, 20260823, 20260824, 20260825, 20260826),
    )
    parser.add_argument("--samples-per-cell-seed", type=int, default=5)
    parser.add_argument("--search-radius", type=float, default=0.45)
    parser.add_argument("--search-points", type=int, default=5)
    parser.add_argument("--minimum-validation-positive-recall", type=float, default=0.9)
    parser.add_argument("--radius-values", type=float, nargs="+", default=(0.25, 0.35, 0.45, 0.50, 0.55))
    parser.add_argument("--radius-sensitivity-samples-per-seed", type=int, default=10)
    parser.add_argument("--output-dir-name", default="tsp_separation_nearfar_metrics_v2_paper")
    return parser.parse_args()


def circular_delta(left: np.ndarray, right: np.ndarray, period: np.ndarray) -> np.ndarray:
    return np.mod(left - right + period / 2.0, period) - period / 2.0


def controlled_scene(
    rng: np.random.Generator,
    *,
    shape: tuple[int, int, int],
    n_targets: int,
    separation_bins: float,
    dynamic_range_db: float,
    snr_db: float,
    pair_axis: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float]:
    if n_targets < 2:
        raise ValueError("controlled stress test requires at least two targets")
    period = np.asarray(shape, dtype=float)
    truth = np.empty((n_targets, 3), dtype=float)
    truth[0] = rng.uniform(0.0, period)
    truth[1] = truth[0]
    truth[1, pair_axis] = np.mod(truth[1, pair_axis] + separation_bins, period[pair_axis])
    for index in range(2, n_targets):
        for _ in range(10000):
            candidate = rng.uniform(0.0, period)
            distances = [np.linalg.norm(circular_delta(candidate, item, period)) for item in truth[:index]]
            if min(distances) >= 4.0:
                truth[index] = candidate
                break
        else:
            raise RuntimeError("Could not place separated nuisance components")
    weakest = 10.0 ** (-dynamic_range_db / 20.0)
    amplitudes = np.ones(n_targets, dtype=float)
    amplitudes[1] = weakest
    if n_targets > 2:
        amplitudes[2:] = np.geomspace(max(np.sqrt(weakest), weakest), 1.0, n_targets - 2)
    phases = rng.uniform(-np.pi, np.pi, n_targets)
    gains = amplitudes * np.exp(1j * phases)
    clean = np.zeros(shape, dtype=np.complex128)
    for gain, bins in zip(gains, truth):
        clean += gain * tensor_atom(shape, tuple(float(value) for value in bins))
    signal_power = float(np.mean(np.abs(clean) ** 2))
    noise_variance = signal_power / (10.0 ** (snr_db / 10.0))
    noise = np.sqrt(noise_variance / 2.0) * (
        rng.standard_normal(shape) + 1j * rng.standard_normal(shape)
    )
    return clean + noise, clean, truth, gains, noise_variance


def residual_fraction(measurement: np.ndarray, estimate: np.ndarray) -> float:
    return float(
        np.linalg.norm(measurement - estimate) ** 2
        / max(np.linalg.norm(measurement) ** 2, 1e-300)
    )


def design_condition(shape: tuple[int, int, int], bins: np.ndarray) -> float:
    design = np.stack(
        [tensor_atom(shape, tuple(float(value) for value in item)).reshape(-1) for item in bins],
        axis=1,
    )
    return float(np.linalg.cond(design))


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def mean(values: list[float]) -> float:
    array = np.asarray(values, dtype=float)
    return float(np.mean(array)) if array.size else float("nan")


def seed_mean_ci(rows: list[dict], key: str) -> tuple[float, float, float]:
    seed_means = np.asarray(
        [
            mean([float(row[key]) for row in rows if int(row["seed"]) == seed])
            for seed in sorted({int(row["seed"]) for row in rows})
        ]
    )
    center = mean(seed_means.tolist())
    if len(seed_means) < 2:
        return center, center, center
    half = float(
        student_t.ppf(0.975, len(seed_means) - 1)
        * np.std(seed_means, ddof=1)
        / np.sqrt(len(seed_means))
    )
    return center, center - half, center + half


def summarize_cells(rows: list[dict]) -> list[dict]:
    output: list[dict] = []
    cells = sorted(
        {
            (float(row["separation_bins"]), float(row["dynamic_range_db"]), float(row["snr_db"]))
            for row in rows
        }
    )
    for separation, dynamic_range, snr_db in cells:
        selected = [
            row for row in rows
            if float(row["separation_bins"]) == separation
            and float(row["dynamic_range_db"]) == dynamic_range
            and float(row["snr_db"]) == snr_db
        ]
        gain, gain_low, gain_high = seed_mean_ci(selected, "gated_gain_vs_grid_db")
        output.append(
            {
                "separation_bins": separation,
                "dynamic_range_db": dynamic_range,
                "snr_db": snr_db,
                "sample_count": len(selected),
                "coarse_per_component_hit_rate": mean([float(row["grid_per_component_half_bin_hit"]) for row in selected]),
                "candan_per_component_hit_rate": mean([float(row["candan_per_component_half_bin_hit"]) for row in selected]),
                "local_per_component_hit_rate": mean([float(row["local_per_component_half_bin_hit"]) for row in selected]),
                "coarse_controlled_pair_joint_hit_rate": mean([float(row["grid_controlled_pair_joint_hit"]) for row in selected]),
                "candan_controlled_pair_joint_hit_rate": mean([float(row["candan_controlled_pair_joint_hit"]) for row in selected]),
                "local_controlled_pair_joint_hit_rate": mean([float(row["local_controlled_pair_joint_hit"]) for row in selected]),
                "coarse_distinct_pair_recovery_rate": mean([float(row["grid_distinct_pair_recovery"]) for row in selected]),
                "candan_distinct_pair_recovery_rate": mean([float(row["candan_distinct_pair_recovery"]) for row in selected]),
                "local_distinct_pair_recovery_rate": mean([float(row["local_distinct_pair_recovery"]) for row in selected]),
                "coarse_pair_separation_error_bins": mean([float(row["grid_pair_separation_error_bins"]) for row in selected]),
                "candan_pair_separation_error_bins": mean([float(row["candan_pair_separation_error_bins"]) for row in selected]),
                "local_pair_separation_error_bins": mean([float(row["local_pair_separation_error_bins"]) for row in selected]),
                "coarse_strong_component_hit_rate": mean([float(row["grid_strong_component_hit"]) for row in selected]),
                "local_strong_component_hit_rate": mean([float(row["local_strong_component_hit"]) for row in selected]),
                "coarse_weak_component_hit_rate": mean([float(row["grid_weak_component_hit"]) for row in selected]),
                "local_weak_component_hit_rate": mean([float(row["local_weak_component_hit"]) for row in selected]),
                "coarse_all_targets_joint_hit_rate": mean([float(row["grid_all_targets_joint_hit"]) for row in selected]),
                "local_all_targets_joint_hit_rate": mean([float(row["local_all_targets_joint_hit"]) for row in selected]),
                "always_local_gain_db": mean([float(row["local_gain_vs_grid_db"]) for row in selected]),
                "candan_gain_db": mean([float(row["candan_gain_vs_grid_db"]) for row in selected]),
                "gated_gain_db": gain,
                "gated_gain_ci95_low_db": gain_low,
                "gated_gain_ci95_high_db": gain_high,
                "harmful_update_rate": mean([float(row["harmful_local_update"]) for row in selected]),
                "gate_pass_rate": mean([float(row["gate_pass"]) for row in selected]),
                "mean_minimum_candidate_margin": mean([float(row["minimum_candidate_margin"]) for row in selected]),
                "mean_candidate_axis_correctness": mean([float(row["candidate_axis_correctness"]) for row in selected]),
                "mean_support_quality": mean([float(row["q_sup"]) for row in selected]),
                "mean_theory_condition_fraction": mean([float(row["theory_condition_fraction"]) for row in selected]),
                "median_coarse_design_condition": float(np.median([float(row["coarse_design_condition"]) for row in selected])),
                "median_refined_design_condition": float(np.median([float(row["refined_design_condition"]) for row in selected])),
            }
        )
    return output


def evaluate_scene(
    *,
    measurement: np.ndarray,
    clean: np.ndarray,
    truth: np.ndarray,
    gains: np.ndarray,
    noise_variance: float,
    shape: tuple[int, int, int],
    n_targets: int,
    search_radius: float,
    search_points: int,
) -> tuple[dict[str, float], list[dict[str, float]]]:
    coarse = np.asarray(topk_grid_bins(measurement, n_targets), dtype=float)
    grid_estimate = estimate_from_bins_lstsq(measurement, shape, [tuple(item) for item in coarse])
    candan = axiswise_candan_bins(measurement, coarse)
    candan_estimate = estimate_from_bins_lstsq(
        measurement, shape, [tuple(item) for item in candan]
    )
    local = separable_cartesian_local_diagnostics(
        measurement,
        coarse,
        search_radius=search_radius,
        search_points=search_points,
    )
    refined = local.bins
    local_estimate = estimate_from_bins_lstsq(measurement, shape, [tuple(item) for item in refined])
    grid_metrics = matched_component_metrics(coarse, truth, shape)
    candan_metrics = matched_component_metrics(candan, truth, shape)
    local_metrics = matched_component_metrics(refined, truth, shape)
    support = support_quality_metrics(coarse, truth, shape)
    theory = candidate_interference_diagnostics(
        coarse,
        truth,
        gains,
        shape,
        search_radius=search_radius,
        search_points=search_points,
        noise_variance=noise_variance,
    )
    theory_components = candidate_interference_component_diagnostics(
        coarse,
        truth,
        gains,
        shape,
        search_radius=search_radius,
        search_points=search_points,
        noise_variance=noise_variance,
    )
    mean_axis_correctness, correctness_by_truth = candidate_axis_correctness(
        coarse,
        refined,
        truth,
        shape,
        search_radius=search_radius,
        search_points=search_points,
    )
    grid_nmse = measurement_nmse_db(grid_estimate, clean)
    candan_nmse = measurement_nmse_db(candan_estimate, clean)
    local_nmse = measurement_nmse_db(local_estimate, clean)
    grid_hits = np.asarray(grid_metrics["hits_by_truth"], dtype=bool)
    candan_hits = np.asarray(candan_metrics["hits_by_truth"], dtype=bool)
    local_hits = np.asarray(local_metrics["hits_by_truth"], dtype=bool)
    grid_pair = distinct_pair_metrics(coarse, truth, shape)
    candan_pair = distinct_pair_metrics(candan, truth, shape)
    local_pair = distinct_pair_metrics(refined, truth, shape)
    component_rows = []
    ratios = np.asarray(theory_components["theory_ratios_by_truth"], dtype=float)
    gaps = np.asarray(theory_components["noiseless_candidate_gaps_by_truth"], dtype=float)
    interference = np.asarray(
        theory_components["interference_envelopes_by_truth"], dtype=float
    )
    for truth_index in range(len(truth)):
        component_rows.append(
            {
                "component_index": truth_index,
                "component_role": (
                    "strong_pair" if truth_index == 0 else
                    "weak_pair" if truth_index == 1 else
                    "nuisance"
                ),
                "theory_ratio": float(ratios[truth_index]),
                "theory_condition_satisfied": float(ratios[truth_index] > 1.0),
                "noiseless_candidate_gap": float(gaps[truth_index]),
                "interference_envelope": float(interference[truth_index]),
                "noise_envelope": float(theory_components["noise_envelope"]),
                "candidate_axis_correctness": float(np.mean(correctness_by_truth[truth_index])),
                "candidate_all_axis_correct": float(np.all(correctness_by_truth[truth_index] > 0.5)),
                "grid_half_bin_hit": float(grid_hits[truth_index]),
                "candan_half_bin_hit": float(candan_hits[truth_index]),
                "local_half_bin_hit": float(local_hits[truth_index]),
            }
        )
    return {
        "grid_nmse_db": grid_nmse,
        "candan_nmse_db": candan_nmse,
        "local_nmse_db": local_nmse,
        "candan_gain_vs_grid_db": grid_nmse - candan_nmse,
        "local_gain_vs_grid_db": grid_nmse - local_nmse,
        "grid_per_component_half_bin_hit": grid_metrics["per_component_hit_rate"],
        "candan_per_component_half_bin_hit": candan_metrics["per_component_hit_rate"],
        "local_per_component_half_bin_hit": local_metrics["per_component_hit_rate"],
        "grid_controlled_pair_joint_hit": float(np.all(grid_hits[:2])),
        "candan_controlled_pair_joint_hit": float(np.all(candan_hits[:2])),
        "local_controlled_pair_joint_hit": float(np.all(local_hits[:2])),
        "grid_distinct_pair_recovery": grid_pair["distinct_pair_recovery"],
        "candan_distinct_pair_recovery": candan_pair["distinct_pair_recovery"],
        "local_distinct_pair_recovery": local_pair["distinct_pair_recovery"],
        "grid_pair_separation_error_bins": grid_pair["pair_separation_error_bins"],
        "candan_pair_separation_error_bins": candan_pair["pair_separation_error_bins"],
        "local_pair_separation_error_bins": local_pair["pair_separation_error_bins"],
        "grid_pair_normalized_separation_error": grid_pair["pair_normalized_separation_error"],
        "local_pair_normalized_separation_error": local_pair["pair_normalized_separation_error"],
        "grid_strong_component_hit": float(grid_hits[0]),
        "candan_strong_component_hit": float(candan_hits[0]),
        "local_strong_component_hit": float(local_hits[0]),
        "grid_weak_component_hit": float(grid_hits[1]),
        "candan_weak_component_hit": float(candan_hits[1]),
        "local_weak_component_hit": float(local_hits[1]),
        "grid_all_targets_joint_hit": float(grid_metrics["all_components_hit"]),
        "local_all_targets_joint_hit": float(local_metrics["all_components_hit"]),
        "minimum_candidate_margin": local.minimum_normalized_margin,
        "mean_candidate_margin": local.mean_normalized_margin,
        "candidate_axis_correctness": mean_axis_correctness,
        "boundary_saturation_rate": local.boundary_saturation_rate,
        "coarse_design_condition": design_condition(shape, coarse),
        "refined_design_condition": design_condition(shape, refined),
        **support,
        **theory,
        "residual_reduction_fraction": residual_fraction(measurement, grid_estimate)
        - residual_fraction(measurement, local_estimate),
        "harmful_local_update": float(local_nmse > grid_nmse),
    }, component_rows


def summarize_theory_components(rows: list[dict]) -> list[dict]:
    output = []
    for condition in (0, 1):
        selected = [
            row for row in rows
            if int(float(row["theory_condition_satisfied"])) == condition
        ]
        output.append(
            {
                "score_gap_condition": "satisfied" if condition else "not_satisfied",
                "component_count": len(selected),
                "seed_count": len({int(row["seed"]) for row in selected}),
                "mean_candidate_axis_correctness": mean([float(row["candidate_axis_correctness"]) for row in selected]),
                "candidate_all_axis_correct_rate": mean([float(row["candidate_all_axis_correct"]) for row in selected]),
                "grid_half_bin_hit_rate": mean([float(row["grid_half_bin_hit"]) for row in selected]),
                "local_half_bin_hit_rate": mean([float(row["local_half_bin_hit"]) for row in selected]),
                "mean_theory_ratio": mean([float(row["theory_ratio"]) for row in selected]),
            }
        )
    return output


def summarize_theory_scenes(rows: list[dict]) -> list[dict]:
    output = []
    for condition in (0, 1):
        selected = [
            row for row in rows
            if int(float(row["theory_all_components_condition"])) == condition
        ]
        output.append(
            {
                "all_component_score_gap_condition": "satisfied" if condition else "not_satisfied",
                "scene_count": len(selected),
                "seed_count": len({int(row["seed"]) for row in selected}),
                "mean_candidate_axis_correctness": mean([float(row["candidate_axis_correctness"]) for row in selected]),
                "local_per_component_half_bin_hit_rate": mean([float(row["local_per_component_half_bin_hit"]) for row in selected]),
                "local_all_targets_joint_hit_rate": mean([float(row["local_all_targets_joint_hit"]) for row in selected]),
                "mean_local_gain_db": mean([float(row["local_gain_vs_grid_db"]) for row in selected]),
            }
        )
    return output


def main() -> None:
    args = parse_args()
    shape = tuple(int(value) for value in args.shape)
    rows: list[dict] = []
    component_rows: list[dict] = []
    started = time.perf_counter()
    for split, seeds in (("validation", args.validation_seeds), ("test", args.test_seeds)):
        for seed in seeds:
            rng = np.random.default_rng(seed)
            for separation in args.separations:
                for dynamic_range_db in args.dynamic_ranges_db:
                    for snr_db in args.snrs:
                        for sample_index in range(args.samples_per_cell_seed):
                            pair_axis = sample_index % 3
                            measurement, clean, truth, gains, noise_variance = controlled_scene(
                                rng,
                                shape=shape,
                                n_targets=args.n_targets,
                                separation_bins=separation,
                                dynamic_range_db=dynamic_range_db,
                                snr_db=snr_db,
                                pair_axis=pair_axis,
                            )
                            metrics, scene_components = evaluate_scene(
                                measurement=measurement,
                                clean=clean,
                                truth=truth,
                                gains=gains,
                                noise_variance=noise_variance,
                                shape=shape,
                                n_targets=args.n_targets,
                                search_radius=args.search_radius,
                                search_points=args.search_points,
                            )
                            rows.append(
                                {
                                    "split": split,
                                    "seed": seed,
                                    "separation_bins": separation,
                                    "dynamic_range_db": dynamic_range_db,
                                    "snr_db": snr_db,
                                    "sample_index": sample_index,
                                    "pair_axis": pair_axis,
                                    **metrics,
                                }
                            )
                            component_rows.extend(
                                {
                                    "split": split,
                                    "seed": seed,
                                    "separation_bins": separation,
                                    "dynamic_range_db": dynamic_range_db,
                                    "snr_db": snr_db,
                                    "sample_index": sample_index,
                                    "pair_axis": pair_axis,
                                    **component,
                                }
                                for component in scene_components
                            )

    validation_rows = [row for row in rows if row["split"] == "validation"]
    gate = calibrate_residual_threshold(
        validation_rows, args.minimum_validation_positive_recall
    )
    threshold = float(gate["threshold"])
    for row in rows:
        gate_pass = float(row["residual_reduction_fraction"]) >= threshold
        row["gate_pass"] = int(gate_pass)
        row["gated_gain_vs_grid_db"] = (
            float(row["local_gain_vs_grid_db"]) if gate_pass else 0.0
        )
        row["gated_per_component_half_bin_hit"] = (
            float(row["local_per_component_half_bin_hit"])
            if gate_pass
            else float(row["grid_per_component_half_bin_hit"])
        )

    test_rows = [row for row in rows if row["split"] == "test"]
    test_component_rows = [row for row in component_rows if row["split"] == "test"]
    cell_rows = summarize_cells(test_rows)
    theory_component_summary = summarize_theory_components(test_component_rows)
    theory_scene_summary = summarize_theory_scenes(test_rows)

    radius_rows: list[dict] = []
    for seed in args.test_seeds:
        rng = np.random.default_rng(seed + 500000)
        for sample_index in range(args.radius_sensitivity_samples_per_seed):
            measurement, clean, truth, gains, noise_variance = controlled_scene(
                rng,
                shape=shape,
                n_targets=args.n_targets,
                separation_bins=1.0,
                dynamic_range_db=10.0,
                snr_db=20.0,
                pair_axis=sample_index % 3,
            )
            for radius in args.radius_values:
                metrics, _ = evaluate_scene(
                    measurement=measurement,
                    clean=clean,
                    truth=truth,
                    gains=gains,
                    noise_variance=noise_variance,
                    shape=shape,
                    n_targets=args.n_targets,
                    search_radius=radius,
                    search_points=args.search_points,
                )
                radius_rows.append(
                    {
                        "seed": seed,
                        "sample_index": sample_index,
                        "search_radius": radius,
                        "local_gain_vs_grid_db": metrics["local_gain_vs_grid_db"],
                        "local_per_component_half_bin_hit": metrics["local_per_component_half_bin_hit"],
                        "harmful_local_update": metrics["harmful_local_update"],
                        "boundary_saturation_rate": metrics["boundary_saturation_rate"],
                    }
                )
    radius_summary: list[dict] = []
    for radius in args.radius_values:
        selected = [row for row in radius_rows if float(row["search_radius"]) == radius]
        radius_summary.append(
            {
                "search_radius": radius,
                "sample_count": len(selected),
                "mean_local_gain_vs_grid_db": mean([float(row["local_gain_vs_grid_db"]) for row in selected]),
                "mean_local_per_component_half_bin_hit": mean([float(row["local_per_component_half_bin_hit"]) for row in selected]),
                "harmful_update_rate": mean([float(row["harmful_local_update"]) for row in selected]),
                "mean_boundary_saturation_rate": mean([float(row["boundary_saturation_rate"]) for row in selected]),
            }
        )

    output_dir = ROOT / "05_results" / args.output_dir_name
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "stress_rows.csv", rows)
    write_csv(output_dir / "stress_component_rows.csv", component_rows)
    write_csv(output_dir / "stress_test_cell_summary.csv", cell_rows)
    write_csv(output_dir / "theory_component_summary.csv", theory_component_summary)
    write_csv(output_dir / "theory_scene_summary.csv", theory_scene_summary)
    write_csv(output_dir / "radius_sensitivity_rows.csv", radius_rows)
    write_csv(output_dir / "radius_sensitivity_summary.csv", radius_summary)
    result = {
        "config": vars(args) | {"shape": list(shape)},
        "gate": gate,
        "validation_scene_count": len(validation_rows),
        "test_scene_count": len(test_rows),
        "cell_summary": cell_rows,
        "theory_component_summary": theory_component_summary,
        "theory_scene_summary": theory_scene_summary,
        "radius_summary": radius_summary,
        "worst_cell_gated_gain_db": min(float(row["gated_gain_db"]) for row in cell_rows),
        "elapsed_seconds": time.perf_counter() - started,
        "notes": [
            "Each scene contains one controlled close pair; the pair axis cycles across angle, delay, and Doppler.",
            "The second member of the pair sets the requested amplitude dynamic range; nuisance components are placed at least four Euclidean circular bins away.",
            "The residual threshold is calibrated only on two validation seeds and frozen on five independent test seeds.",
            "All generated scenes contribute to the support, component-hit, conditioning, and reconstruction summaries.",
            "The score-gap envelope uses eta=0.05 and 125 candidates per neighborhood; component and all-component scene counts are stored explicitly.",
            "Distinct-pair recovery jointly requires truth-assigned coordinate accuracy and separation fidelity; separation error is also reported continuously.",
        ],
    }
    (output_dir / "summary.json").write_text(
        json.dumps(result, indent=2, allow_nan=True) + "\n", encoding="utf-8"
    )
    command = "python 04_experiments/eval/run_tsp_separation_nearfar_stress.py"
    write_release_metadata(
        output_dir,
        config=result["config"],
        seeds=[
            *({"split": "validation", "seed": seed} for seed in args.validation_seeds),
            *({"split": "test", "seed": seed} for seed in args.test_seeds),
        ],
        command=command,
    )
    write_run_manifest(
        output_dir,
        run_id="tsp_separation_nearfar_metrics_v2_paper_20260829",
        command=command,
        config=result["config"],
        metrics={
            "validation_scene_count": len(validation_rows),
            "test_scene_count": len(test_rows),
            "gate_threshold": gate["threshold"],
            "worst_cell_gated_gain_db": result["worst_cell_gated_gain_db"],
        },
        notes=result["notes"],
        cwd=ROOT,
    )
    print(json.dumps(result, indent=2, allow_nan=True))


if __name__ == "__main__":
    main()
