from __future__ import annotations

import argparse
import csv
import json
from itertools import product
from pathlib import Path
import sys
import time

import numpy as np
from scipy.stats import t as student_t
from sionna.phy import config as sionna_config


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_active_modules"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from common.seed import seed_all
from tompnet.feature_controller import (
    FEATURE_NAMES,
    apply_nyquist_alias_lock,
    estimator_features,
)
from run_sionna_cdl_profile_generalization import (
    add_awgn,
    generate_profile_channels,
    reconstruct_fft_topk,
)
from run_sionna_cdl_trained_refinement import (
    atom_2d,
    estimate_from_bins_lstsq,
    nmse_db,
    physical_path_metrics_from_bins,
    support_to_bins,
)


GATE_DIRECTIONS = {
    "grid_residual_fraction": "high",
    "residual_reduction_fraction": "high",
    "minimum_candidate_margin": "high",
    "log10_refined_condition": "low",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profiles", nargs="+", default=["A", "C", "D"])
    parser.add_argument("--snrs", nargs="+", type=float, default=[0.0, 10.0, 20.0, 30.0])
    parser.add_argument("--l-values", nargs="+", type=int, default=[4, 8, 16])
    parser.add_argument(
        "--validation-seeds", nargs="+", type=int, default=[20260625, 20260626, 20260627]
    )
    parser.add_argument(
        "--test-seeds", nargs="+", type=int,
        default=[20260628, 20260629, 20260630, 20260701, 20260702]
    )
    parser.add_argument("--samples-per-profile-seed", type=int, default=50)
    parser.add_argument("--num-subcarriers", type=int, default=64)
    parser.add_argument("--num-tx-antennas", type=int, default=4)
    parser.add_argument("--spatial-truth-oversampling", type=int, default=4096)
    parser.add_argument("--subcarrier-spacing-hz", type=float, default=120e3)
    parser.add_argument("--carrier-frequency-hz", type=float, default=60e9)
    parser.add_argument("--delay-spread-s", type=float, default=100e-9)
    parser.add_argument("--search-radius", type=float, default=0.45)
    parser.add_argument("--search-points", type=int, default=5)
    parser.add_argument("--minimum-validation-positive-recall", type=float, default=0.9)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--output-dir-name", default="tsp_reliability_gate")
    return parser.parse_args()


def refined_bins_and_margins(
    measurement: np.ndarray,
    coarse_bins: np.ndarray,
    *,
    search_radius: float,
    search_points: int,
) -> tuple[np.ndarray, np.ndarray]:
    offsets = np.linspace(-search_radius, search_radius, search_points)
    refined: list[tuple[float, float]] = []
    margins: list[float] = []
    for coarse in coarse_bins:
        scored: list[tuple[float, tuple[float, float]]] = []
        for delta in product(offsets, repeat=2):
            candidate = (float(coarse[0] + delta[0]), float(coarse[1] + delta[1]))
            score = float(
                np.abs(np.vdot(atom_2d(measurement.shape, candidate), measurement))
                ** 2
            )
            scored.append((score, candidate))
        scored.sort(key=lambda item: item[0], reverse=True)
        best_score, best_bins = scored[0]
        second_score = scored[1][0]
        refined.append(best_bins)
        margins.append((best_score - second_score) / max(best_score, 1e-300))
    return np.asarray(refined, dtype=float), np.asarray(margins, dtype=float)


def residual_fraction(measurement: np.ndarray, estimate: np.ndarray) -> float:
    return float(
        np.linalg.norm(measurement - estimate) ** 2
        / max(np.linalg.norm(measurement) ** 2, 1e-300)
    )


def design_condition(shape: tuple[int, int], bins: np.ndarray) -> float:
    design = np.stack(
        [atom_2d(shape, (float(item[0]), float(item[1]))).reshape(-1) for item in bins],
        axis=1,
    )
    return float(np.linalg.cond(design))


def write_csv(path: Path, rows: list[dict[str, float | str]]) -> None:
    fieldnames = list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def quantile_thresholds(values: np.ndarray) -> np.ndarray:
    quantiles = np.linspace(0.0, 1.0, 101)
    return np.unique(np.quantile(values, quantiles))


def passes_rule(row: dict[str, float | str], feature: str, direction: str, threshold: float) -> bool:
    value = float(row[feature])
    return value >= threshold if direction == "high" else value <= threshold


def calibrate_single_threshold(
    validation_rows: list[dict[str, float | str]],
    *,
    minimum_positive_recall: float,
) -> dict[str, float | str]:
    candidates: list[dict[str, float | str]] = []
    for feature, direction in GATE_DIRECTIONS.items():
        values = np.asarray([float(row[feature]) for row in validation_rows], dtype=float)
        for threshold in quantile_thresholds(values):
            passed = [passes_rule(row, feature, direction, float(threshold)) for row in validation_rows]
            pass_rate = float(np.mean(passed))
            positive_mask = [
                float(row["local_gain_vs_grid_db"]) > 0.0 for row in validation_rows
            ]
            negative_mask = [
                float(row["local_gain_vs_grid_db"]) < 0.0 for row in validation_rows
            ]
            positive_recall = float(
                np.mean(
                    [accept for accept, positive in zip(passed, positive_mask) if positive]
                )
            )
            if positive_recall + 1e-12 < minimum_positive_recall:
                continue
            gated_gain = float(
                np.mean(
                    [
                        float(row["local_gain_vs_grid_db"]) if accept else 0.0
                        for row, accept in zip(validation_rows, passed)
                    ]
                )
            )
            negative_rejection = float(
                np.mean(
                    [
                        not accept
                        for accept, negative in zip(passed, negative_mask)
                        if negative
                    ]
                )
            )
            candidates.append(
                {
                    "feature": feature,
                    "direction": direction,
                    "threshold": float(threshold),
                    "validation_gated_gain_db": gated_gain,
                    "validation_pass_rate": pass_rate,
                    "validation_positive_gain_recall": positive_recall,
                    "validation_negative_gain_rejection": negative_rejection,
                }
            )
    if not candidates:
        raise RuntimeError("No gate candidate satisfies the validation pass-rate constraint.")
    candidates.sort(
        key=lambda item: (
            float(item["validation_negative_gain_rejection"]),
            float(item["validation_gated_gain_db"]),
            float(item["validation_positive_gain_recall"]),
        ),
        reverse=True,
    )
    return candidates[0]


def mean(values: list[float]) -> float:
    array = np.asarray(values, dtype=float)
    return float(np.mean(array)) if array.size else float("nan")


def wilson_interval(successes: int, trials: int) -> tuple[float, float]:
    if trials == 0:
        return float("nan"), float("nan")
    z = 1.959963984540054
    proportion = successes / trials
    denominator = 1.0 + z**2 / trials
    center = (proportion + z**2 / (2.0 * trials)) / denominator
    half = z * np.sqrt(
        proportion * (1.0 - proportion) / trials + z**2 / (4.0 * trials**2)
    ) / denominator
    return float(center - half), float(center + half)


def seed_mean_ci(
    rows: list[dict[str, float | str]],
    value_key: str,
) -> tuple[float, float, float]:
    seed_means = [
        mean([float(row[value_key]) for row in rows if row["seed"] == seed])
        for seed in sorted({int(row["seed"]) for row in rows})
    ]
    center = mean(seed_means)
    if len(seed_means) < 2:
        return center, center, center
    half_width = float(
        student_t.ppf(0.975, len(seed_means) - 1)
        * np.std(np.asarray(seed_means), ddof=1)
        / np.sqrt(len(seed_means))
    )
    return center, center - half_width, center + half_width


def summarize_test_rows(
    rows: list[dict[str, float | str]],
) -> list[dict[str, float | str]]:
    summary: list[dict[str, float | str]] = []
    for profile in sorted({str(row["profile"]) for row in rows}):
        selected = [row for row in rows if row["profile"] == profile]
        positive = [row for row in selected if float(row["local_gain_vs_grid_db"]) > 0.0]
        negative = [row for row in selected if float(row["local_gain_vs_grid_db"]) < 0.0]
        true_positive = sum(int(row["gate_pass"]) for row in positive)
        false_negative = len(positive) - true_positive
        true_negative = sum(1 - int(row["gate_pass"]) for row in negative)
        false_positive = len(negative) - true_negative
        recall_low, recall_high = wilson_interval(true_positive, len(positive))
        rejection_low, rejection_high = wilson_interval(true_negative, len(negative))
        always_mean, always_low, always_high = seed_mean_ci(
            selected, "local_gain_vs_grid_db"
        )
        gated_mean, gated_low, gated_high = seed_mean_ci(
            selected, "gated_gain_vs_grid_db"
        )
        summary.append(
            {
                "profile": profile,
                "sample_count": len(selected),
                "always_refine_gain_db": always_mean,
                "always_refine_gain_ci95_low_db": always_low,
                "always_refine_gain_ci95_high_db": always_high,
                "gated_refine_gain_db": gated_mean,
                "gated_refine_gain_ci95_low_db": gated_low,
                "gated_refine_gain_ci95_high_db": gated_high,
                "gate_pass_rate": mean([float(row["gate_pass"]) for row in selected]),
                "positive_gain_count": len(positive),
                "negative_gain_count": len(negative),
                "true_positive_count": true_positive,
                "false_negative_count": false_negative,
                "true_negative_count": true_negative,
                "false_positive_count": false_positive,
                "positive_gain_recall": mean(
                    [float(row["gate_pass"]) for row in positive]
                )
                if positive
                else float("nan"),
                "positive_gain_recall_wilson95_low": recall_low,
                "positive_gain_recall_wilson95_high": recall_high,
                "negative_gain_rejection": mean(
                    [1.0 - float(row["gate_pass"]) for row in negative]
                )
                if negative
                else float("nan"),
                "negative_gain_rejection_wilson95_low": rejection_low,
                "negative_gain_rejection_wilson95_high": rejection_high,
                "grid_delay_rmse_ns": mean(
                    [float(row["grid_delay_rmse_ns"]) for row in selected]
                ),
                "always_refine_delay_rmse_ns": mean(
                    [float(row["local_delay_rmse_ns"]) for row in selected]
                ),
                "gated_refine_delay_rmse_ns": mean(
                    [float(row["gated_delay_rmse_ns"]) for row in selected]
                ),
                "grid_delay_rmse_bins": mean(
                    [float(row["grid_delay_rmse_bins"]) for row in selected]
                ),
                "always_refine_delay_rmse_bins": mean(
                    [float(row["local_delay_rmse_bins"]) for row in selected]
                ),
                "gated_refine_delay_rmse_bins": mean(
                    [float(row["gated_delay_rmse_bins"]) for row in selected]
                ),
                "grid_spatial_frequency_rmse_bins": mean(
                    [float(row["grid_spatial_frequency_rmse_bins"]) for row in selected]
                ),
                "always_refine_spatial_frequency_rmse_bins": mean(
                    [float(row["local_spatial_frequency_rmse_bins"]) for row in selected]
                ),
                "gated_refine_spatial_frequency_rmse_bins": mean(
                    [float(row["gated_spatial_frequency_rmse_bins"]) for row in selected]
                ),
                "grid_angle_rmse_deg": mean(
                    [float(row["grid_angle_rmse_deg"]) for row in selected]
                ),
                "always_refine_angle_rmse_deg": mean(
                    [float(row["local_angle_rmse_deg"]) for row in selected]
                ),
                "gated_refine_angle_rmse_deg": mean(
                    [float(row["gated_angle_rmse_deg"]) for row in selected]
                ),
            }
        )
    return summary


def summarize_test_cells(
    rows: list[dict[str, float | str]],
) -> list[dict[str, float | str]]:
    summary: list[dict[str, float | str]] = []
    cells = sorted(
        {
            (str(row["profile"]), float(row["snr_db"]), int(row["l_value"]))
            for row in rows
        }
    )
    for profile, snr_db, l_value in cells:
        selected = [
            row
            for row in rows
            if row["profile"] == profile
            and float(row["snr_db"]) == snr_db
            and int(row["l_value"]) == l_value
        ]
        positive = [row for row in selected if float(row["local_gain_vs_grid_db"]) > 0.0]
        negative = [row for row in selected if float(row["local_gain_vs_grid_db"]) < 0.0]
        tp = sum(int(row["gate_pass"]) for row in positive)
        tn = sum(1 - int(row["gate_pass"]) for row in negative)
        recall_low, recall_high = wilson_interval(tp, len(positive))
        rejection_low, rejection_high = wilson_interval(tn, len(negative))
        gated_mean, gated_low, gated_high = seed_mean_ci(selected, "gated_gain_vs_grid_db")
        summary.append(
            {
                "profile": profile,
                "snr_db": snr_db,
                "l_value": l_value,
                "sample_count": len(selected),
                "gated_gain_db": gated_mean,
                "gated_gain_ci95_low_db": gated_low,
                "gated_gain_ci95_high_db": gated_high,
                "gate_pass_rate": mean([float(row["gate_pass"]) for row in selected]),
                "positive_gain_count": len(positive),
                "negative_gain_count": len(negative),
                "true_positive_count": tp,
                "false_negative_count": len(positive) - tp,
                "true_negative_count": tn,
                "false_positive_count": len(negative) - tn,
                "positive_gain_recall": tp / len(positive) if positive else float("nan"),
                "positive_gain_recall_wilson95_low": recall_low,
                "positive_gain_recall_wilson95_high": recall_high,
                "negative_gain_rejection": tn / len(negative) if negative else float("nan"),
                "negative_gain_rejection_wilson95_low": rejection_low,
                "negative_gain_rejection_wilson95_high": rejection_high,
                "grid_delay_rmse_bins": mean(
                    [float(row["grid_delay_rmse_bins"]) for row in selected]
                ),
                "gated_delay_rmse_bins": mean(
                    [float(row["gated_delay_rmse_bins"]) for row in selected]
                ),
                "grid_spatial_frequency_rmse_bins": mean(
                    [float(row["grid_spatial_frequency_rmse_bins"]) for row in selected]
                ),
                "gated_spatial_frequency_rmse_bins": mean(
                    [float(row["gated_spatial_frequency_rmse_bins"]) for row in selected]
                ),
            }
        )
    return summary


def main() -> None:
    args = parse_args()
    started = time.perf_counter()
    all_seeds = list(dict.fromkeys([*args.validation_seeds, *args.test_seeds]))
    rows: list[dict[str, float | str]] = []

    for profile in args.profiles:
        profile_seeds = all_seeds if profile in {"A", "C"} else list(args.test_seeds)
        for seed in profile_seeds:
            seed_all(seed)
            sionna_config.seed = seed
            rng = np.random.default_rng(seed + 1000 * (ord(profile[0]) - ord("A") + 1))
            clean_batch, delays_batch, spatial_batch, powers_batch = generate_profile_channels(
                profile=profile,
                batch_size=args.samples_per_profile_seed,
                num_subcarriers=args.num_subcarriers,
                subcarrier_spacing_hz=args.subcarrier_spacing_hz,
                carrier_frequency_hz=args.carrier_frequency_hz,
                delay_spread_s=args.delay_spread_s,
                num_tx_antennas=args.num_tx_antennas,
                spatial_truth_oversampling=args.spatial_truth_oversampling,
                device=args.device,
            )
            for snr_db in args.snrs:
                noisy_batch = [add_awgn(clean, snr_db=snr_db, rng=rng)[0] for clean in clean_batch]
                for l_value in args.l_values:
                    for sample_index, (clean, noisy) in enumerate(zip(clean_batch, noisy_batch)):
                        grid_estimate, support, _ = reconstruct_fft_topk(noisy, l_value)
                        coarse_bins = support_to_bins(support, clean.shape)
                        refined_bins, margins = refined_bins_and_margins(
                            noisy,
                            coarse_bins,
                            search_radius=args.search_radius,
                            search_points=args.search_points,
                        )
                        refined_bins = apply_nyquist_alias_lock(
                            coarse_bins,
                            refined_bins,
                            angle_bin_count=clean.shape[1],
                        )
                        local_estimate = estimate_from_bins_lstsq(noisy, refined_bins)
                        feature_vector = estimator_features(
                            noisy,
                            coarse_bins,
                            refined_bins,
                            search_radius=args.search_radius,
                        )
                        grid_residual = residual_fraction(noisy, grid_estimate)
                        local_residual = residual_fraction(noisy, local_estimate)
                        grid_physical = physical_path_metrics_from_bins(
                            estimated_bins=coarse_bins,
                            shape=clean.shape,
                            truth_delays_s=delays_batch[sample_index],
                            truth_spatial_frequencies=spatial_batch[sample_index],
                            truth_path_powers=powers_batch[sample_index],
                            subcarrier_spacing_hz=args.subcarrier_spacing_hz,
                        )
                        local_physical = physical_path_metrics_from_bins(
                            estimated_bins=refined_bins,
                            shape=clean.shape,
                            truth_delays_s=delays_batch[sample_index],
                            truth_spatial_frequencies=spatial_batch[sample_index],
                            truth_path_powers=powers_batch[sample_index],
                            subcarrier_spacing_hz=args.subcarrier_spacing_hz,
                        )
                        grid_nmse = nmse_db(grid_estimate, clean)
                        local_nmse = nmse_db(local_estimate, clean)
                        row: dict[str, float | str] = {
                            "profile": profile,
                            "split": "validation" if seed in args.validation_seeds else "test",
                            "seed": seed,
                            "sample_index": sample_index,
                            "snr_db": snr_db,
                            "l_value": l_value,
                            "grid_channel_nmse_db": grid_nmse,
                            "local_channel_nmse_db": local_nmse,
                            "local_gain_vs_grid_db": grid_nmse - local_nmse,
                            "grid_delay_rmse_ns": grid_physical["physical_delay_rmse_ns"],
                            "local_delay_rmse_ns": local_physical["physical_delay_rmse_ns"],
                            "grid_delay_rmse_bins": grid_physical[
                                "physical_delay_rmse_bins"
                            ],
                            "local_delay_rmse_bins": local_physical[
                                "physical_delay_rmse_bins"
                            ],
                            "grid_spatial_frequency_rmse_bins": grid_physical[
                                "projected_spatial_frequency_rmse_bins"
                            ],
                            "local_spatial_frequency_rmse_bins": local_physical[
                                "projected_spatial_frequency_rmse_bins"
                            ],
                            "grid_angle_rmse_deg": grid_physical[
                                "projected_broadside_angle_rmse_deg"
                            ],
                            "local_angle_rmse_deg": local_physical[
                                "projected_broadside_angle_rmse_deg"
                            ],
                            "minimum_candidate_margin": float(np.min(margins)),
                            "mean_candidate_margin": float(np.mean(margins)),
                            "residual_reduction_fraction": grid_residual - local_residual,
                            "log10_refined_condition": float(
                                np.log10(max(design_condition(clean.shape, refined_bins), 1.0))
                            ),
                        }
                        row.update(
                            {
                                name: float(value)
                                for name, value in zip(FEATURE_NAMES, feature_vector)
                            }
                        )
                        rows.append(row)

    validation_rows = [
        row
        for row in rows
        if row["split"] == "validation" and row["profile"] in {"A", "C"}
    ]
    gate = calibrate_single_threshold(
        validation_rows,
        minimum_positive_recall=args.minimum_validation_positive_recall,
    )
    feature = str(gate["feature"])
    direction = str(gate["direction"])
    threshold = float(gate["threshold"])

    for row in rows:
        accept = passes_rule(row, feature, direction, threshold)
        row["gate_pass"] = int(accept)
        row["gated_channel_nmse_db"] = (
            float(row["local_channel_nmse_db"])
            if accept
            else float(row["grid_channel_nmse_db"])
        )
        row["gated_gain_vs_grid_db"] = (
            float(row["local_gain_vs_grid_db"]) if accept else 0.0
        )
        row["gated_delay_rmse_ns"] = (
            float(row["local_delay_rmse_ns"])
            if accept
            else float(row["grid_delay_rmse_ns"])
        )
        row["gated_delay_rmse_bins"] = (
            float(row["local_delay_rmse_bins"])
            if accept
            else float(row["grid_delay_rmse_bins"])
        )
        row["gated_spatial_frequency_rmse_bins"] = (
            float(row["local_spatial_frequency_rmse_bins"])
            if accept
            else float(row["grid_spatial_frequency_rmse_bins"])
        )
        row["gated_angle_rmse_deg"] = (
            float(row["local_angle_rmse_deg"])
            if accept
            else float(row["grid_angle_rmse_deg"])
        )

    test_rows = [row for row in rows if row["split"] == "test"]
    summary_rows = summarize_test_rows(test_rows)
    cell_summary_rows = summarize_test_cells(test_rows)

    validation_loso_rows: list[dict[str, float | str]] = []
    for held_out_seed in args.validation_seeds:
        calibration_subset = [
            row for row in validation_rows if int(row["seed"]) != held_out_seed
        ]
        evaluation_subset = [
            row for row in validation_rows if int(row["seed"]) == held_out_seed
        ]
        loso_gate = calibrate_single_threshold(
            calibration_subset,
            minimum_positive_recall=args.minimum_validation_positive_recall,
        )
        loso_pass = [
            passes_rule(
                row,
                str(loso_gate["feature"]),
                str(loso_gate["direction"]),
                float(loso_gate["threshold"]),
            )
            for row in evaluation_subset
        ]
        positive = [float(row["local_gain_vs_grid_db"]) > 0.0 for row in evaluation_subset]
        negative = [float(row["local_gain_vs_grid_db"]) < 0.0 for row in evaluation_subset]
        validation_loso_rows.append(
            {
                "held_out_seed": held_out_seed,
                "feature": str(loso_gate["feature"]),
                "direction": str(loso_gate["direction"]),
                "threshold": float(loso_gate["threshold"]),
                "calibration_row_count": len(calibration_subset),
                "held_out_row_count": len(evaluation_subset),
                "held_out_pass_rate": mean([float(value) for value in loso_pass]),
                "held_out_positive_recall": mean(
                    [float(value) for value, label in zip(loso_pass, positive) if label]
                ),
                "held_out_negative_rejection": mean(
                    [float(not value) for value, label in zip(loso_pass, negative) if label]
                ),
                "held_out_gated_gain_db": mean(
                    [
                        float(row["local_gain_vs_grid_db"]) if accept else 0.0
                        for row, accept in zip(evaluation_subset, loso_pass)
                    ]
                ),
            }
        )

    sensitivity_rows: list[dict[str, float | str]] = []
    selected_feature = str(gate["feature"])
    selected_direction = str(gate["direction"])
    feature_values = np.asarray(
        [float(row[selected_feature]) for row in validation_rows], dtype=float
    )
    for sensitivity_threshold in quantile_thresholds(feature_values):
        for group_name, selected_rows in [
            ("validation_A_C", validation_rows),
            *[
                (
                    f"test_{profile}",
                    [row for row in test_rows if row["profile"] == profile],
                )
                for profile in sorted({str(row["profile"]) for row in test_rows})
            ],
        ]:
            decisions = [
                passes_rule(
                    row, selected_feature, selected_direction, float(sensitivity_threshold)
                )
                for row in selected_rows
            ]
            sensitivity_rows.append(
                {
                    "group": group_name,
                    "feature": selected_feature,
                    "threshold": float(sensitivity_threshold),
                    "row_count": len(selected_rows),
                    "pass_rate": mean([float(value) for value in decisions]),
                    "gated_gain_db": mean(
                        [
                            float(row["local_gain_vs_grid_db"]) if accept else 0.0
                            for row, accept in zip(selected_rows, decisions)
                        ]
                    ),
                }
            )
    output_dir = ROOT / "05_results" / args.output_dir_name
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "reliability_gate_rows.csv", rows)
    write_csv(output_dir / "reliability_gate_test_summary.csv", summary_rows)
    write_csv(output_dir / "reliability_gate_cell_summary.csv", cell_summary_rows)
    write_csv(output_dir / "reliability_gate_validation_loso.csv", validation_loso_rows)
    write_csv(output_dir / "reliability_gate_threshold_sensitivity.csv", sensitivity_rows)

    result = {
        "gate": gate,
        "config": vars(args),
        "row_count": len(rows),
        "validation_row_count": len(validation_rows),
        "test_row_count": len(test_rows),
        "test_summary": summary_rows,
        "cell_summary": cell_summary_rows,
        "validation_loso": validation_loso_rows,
        "worst_test_cell_gated_gain_db": min(
            float(row["gated_gain_db"]) for row in cell_summary_rows
        ),
        "elapsed_seconds": time.perf_counter() - started,
        "notes": [
            "The gate uses one estimator-observable feature and a threshold selected only on CDL-A/C validation seeds.",
            "CDL-D is not used for feature selection or threshold calibration.",
            "Clean channels and physical truth are used only to select the validation rule and to evaluate frozen test outcomes.",
            "The rule is risk-aware rather than a non-degradation guarantee because its feature is computed from the same noisy observation.",
            "CDL-D validation rows are not generated; row_count equals the A/C validation rows plus all A/C/D test rows.",
            "Classification summaries report TP, FP, TN, FN counts and Wilson 95% intervals; cells with an empty class use NaN/N/A rather than zero.",
        ],
    }
    (output_dir / "summary.json").write_text(
        json.dumps(result, indent=2, allow_nan=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, allow_nan=True))


if __name__ == "__main__":
    main()
