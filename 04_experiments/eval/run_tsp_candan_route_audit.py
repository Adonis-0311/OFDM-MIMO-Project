"""Audit residual-gated Candan and a one-feature Candan--Cartesian route.

All thresholds are selected on validation seeds and frozen before the test
profiles are summarized.  Route features are computed from the noisy tensor,
coarse support, and Candan update only; clean channels and path truth are used
solely for validation selection and test evaluation.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
import time

import numpy as np
from scipy.stats import t as student_t
from sklearn.metrics import average_precision_score, roc_auc_score
from sionna.phy import config as sionna_config


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_active_modules"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from baseline.local_refinement import (  # noqa: E402
    axiswise_candan_diagnostics,
)
from common.manifest import write_run_manifest  # noqa: E402
from common.seed import seed_all  # noqa: E402
from common.tsp_revision_metrics import write_release_metadata  # noqa: E402
from tompnet.feature_controller import (  # noqa: E402
    FEATURE_NAMES,
    apply_nyquist_alias_lock,
    estimator_features,
)
from run_sionna_cdl_profile_generalization import (  # noqa: E402
    add_awgn,
    generate_profile_channels,
    reconstruct_fft_topk,
)
from run_sionna_cdl_trained_refinement import (  # noqa: E402
    estimate_from_bins_lstsq,
    nmse_db,
    physical_path_metrics_from_bins,
    support_to_bins,
)
from run_tsp_reliability_gate import (  # noqa: E402
    design_condition,
    refined_bins_and_margins,
    residual_fraction,
)


ROUTE_DIRECTIONS = {
    "candan_minimum_denominator_stability": "low",
    "candan_mean_denominator_stability": "low",
    "candan_maximum_absolute_unclipped_offset": "high",
    "candan_clipping_rate": "high",
    "candan_residual_reduction_fraction": "low",
    "log10_candan_condition": "high",
    "grid_residual_fraction": "high",
    "topk_energy_fraction": "low",
    "log10_design_condition": "high",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profiles", nargs="+", default=["A", "C", "D"])
    parser.add_argument("--snrs", nargs="+", type=float, default=[0.0, 10.0, 20.0, 30.0])
    parser.add_argument("--l-values", nargs="+", type=int, default=[4, 8, 16])
    parser.add_argument(
        "--validation-seeds", nargs="+", type=int,
        default=[20260625, 20260626, 20260627],
    )
    parser.add_argument(
        "--test-seeds", nargs="+", type=int,
        default=[20260628, 20260629, 20260630, 20260701, 20260702],
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
    parser.add_argument("--route-win-epsilon-db", type=float, default=0.1)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--output-dir-name", default="tsp_candan_route_audit_paper")
    return parser.parse_args()


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def thresholds(values: np.ndarray) -> np.ndarray:
    return np.unique(np.quantile(values, np.linspace(0.0, 1.0, 101)))


def passes(value: float, direction: str, threshold: float) -> bool:
    return value <= threshold if direction == "low" else value >= threshold


def calibrate_route(rows: list[dict[str, object]]) -> dict[str, object]:
    candidates: list[dict[str, object]] = []
    candan_mean = float(np.mean([float(row["candan_gain_vs_grid_db"]) for row in rows]))
    for feature, direction in ROUTE_DIRECTIONS.items():
        values = np.asarray([float(row[feature]) for row in rows], dtype=float)
        for threshold in thresholds(values):
            fallback = [passes(float(row[feature]), direction, float(threshold)) for row in rows]
            gains = [
                float(row["cartesian_gain_vs_grid_db"] if use_cart else row["candan_gain_vs_grid_db"])
                for row, use_cart in zip(rows, fallback)
            ]
            candidates.append(
                {
                    "feature": feature,
                    "direction": direction,
                    "threshold": float(threshold),
                    "validation_hybrid_gain_db": float(np.mean(gains)),
                    "validation_gain_over_candan_db": float(np.mean(gains) - candan_mean),
                    "validation_fallback_rate": float(np.mean(fallback)),
                }
            )
    return max(
        candidates,
        key=lambda item: (
            float(item["validation_hybrid_gain_db"]),
            -float(item["validation_fallback_rate"]),
        ),
    )


def calibrate_residual_gate(
    rows: list[dict[str, object]], *, gain_key: str, residual_key: str
) -> dict[str, object]:
    values = np.asarray([float(row[residual_key]) for row in rows], dtype=float)
    candidates: list[dict[str, object]] = []
    for threshold in thresholds(values):
        accepted = values >= threshold
        gains = np.asarray([float(row[gain_key]) for row in rows], dtype=float)
        candidates.append(
            {
                "feature": residual_key,
                "direction": "high",
                "threshold": float(threshold),
                "validation_gated_gain_db": float(np.mean(np.where(accepted, gains, 0.0))),
                "validation_pass_rate": float(np.mean(accepted)),
            }
        )
    return max(
        candidates,
        key=lambda item: (
            float(item["validation_gated_gain_db"]),
            -float(item["validation_pass_rate"]),
        ),
    )


def seed_mean_ci(rows: list[dict[str, object]], key: str) -> tuple[float, float, float]:
    seeds = sorted({int(row["seed"]) for row in rows})
    seed_means = np.asarray(
        [np.mean([float(row[key]) for row in rows if int(row["seed"]) == seed]) for seed in seeds],
        dtype=float,
    )
    center = float(np.mean(seed_means))
    if seed_means.size < 2:
        return center, center, center
    half = float(
        student_t.ppf(0.975, seed_means.size - 1)
        * np.std(seed_means, ddof=1)
        / np.sqrt(seed_means.size)
    )
    return center, center - half, center + half


def classification_metrics(
    rows: list[dict[str, object]], *, feature: str, direction: str, threshold: float,
    epsilon_db: float,
) -> dict[str, object]:
    labels = np.asarray(
        [float(row["cartesian_advantage_over_candan_db"]) > epsilon_db for row in rows],
        dtype=bool,
    )
    raw = np.asarray([float(row[feature]) for row in rows], dtype=float)
    scores = -raw if direction == "low" else raw
    decisions = scores >= (-threshold if direction == "low" else threshold)
    positive = int(np.sum(labels))
    negative = int(labels.size - positive)
    return {
        "row_count": int(labels.size),
        "positive_count": positive,
        "fallback_rate": float(np.mean(decisions)),
        "positive_recall": float(np.mean(decisions[labels])) if positive else float("nan"),
        "negative_rejection": float(np.mean(~decisions[~labels])) if negative else float("nan"),
        "auroc": float(roc_auc_score(labels, scores)) if positive and negative else float("nan"),
        "average_precision": float(average_precision_score(labels, scores)) if positive else float("nan"),
    }


def gate_classification_metrics(
    rows: list[dict[str, object]], *, method: str
) -> dict[str, object]:
    positive = [row for row in rows if float(row[f"{method}_gain_vs_grid_db"]) > 0.0]
    negative = [row for row in rows if float(row[f"{method}_gain_vs_grid_db"]) < 0.0]
    return {
        "row_count": len(rows),
        "positive_count": len(positive),
        "negative_count": len(negative),
        "pass_rate": float(np.mean([float(row[f"gated_{method}_pass"]) for row in rows])),
        "positive_recall": float(np.mean([float(row[f"gated_{method}_pass"]) for row in positive])) if positive else float("nan"),
        "negative_rejection": float(np.mean([1.0-float(row[f"gated_{method}_pass"]) for row in negative])) if negative else float("nan"),
    }


def summarize(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    groups = [
        *[(profile, [row for row in rows if row["profile"] == profile])
          for profile in sorted({str(row["profile"]) for row in rows})],
        ("All", rows),
    ]
    for profile, selected in groups:
        item: dict[str, object] = {"profile": profile, "scene_count": len(selected)}
        for key in [
            "candan_gain_vs_grid_db",
            "gated_candan_gain_vs_grid_db",
            "cartesian_gain_vs_grid_db",
            "hybrid_gain_vs_grid_db",
            "gated_hybrid_gain_vs_grid_db",
            "oracle_gain_vs_grid_db",
        ]:
            center, low, high = seed_mean_ci(selected, key)
            prefix = key.removesuffix("_gain_vs_grid_db")
            item[f"{prefix}_gain_db"] = center
            item[f"{prefix}_gain_ci95_low_db"] = low
            item[f"{prefix}_gain_ci95_high_db"] = high
        item["hybrid_fallback_rate"] = float(np.mean([float(row["hybrid_fallback"]) for row in selected]))
        item["gated_candan_pass_rate"] = float(np.mean([float(row["gated_candan_pass"]) for row in selected]))
        item["gated_hybrid_pass_rate"] = float(np.mean([float(row["gated_hybrid_pass"]) for row in selected]))
        item["candan_delay_rmse_ns"] = float(np.mean([float(row["candan_delay_rmse_ns"]) for row in selected]))
        item["gated_candan_delay_rmse_ns"] = float(np.mean([float(row["gated_candan_delay_rmse_ns"]) for row in selected]))
        item["candan_angle_rmse_deg"] = float(np.mean([float(row["candan_angle_rmse_deg"]) for row in selected]))
        item["gated_candan_angle_rmse_deg"] = float(np.mean([float(row["gated_candan_angle_rmse_deg"]) for row in selected]))
        output.append(item)
    return output


def main() -> None:
    args = parse_args()
    started = time.perf_counter()
    all_seeds = list(dict.fromkeys([*args.validation_seeds, *args.test_seeds]))
    rows: list[dict[str, object]] = []

    for profile in args.profiles:
        for seed in all_seeds:
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
                        candan = axiswise_candan_diagnostics(noisy, coarse_bins)
                        candan_bins = apply_nyquist_alias_lock(
                            coarse_bins, candan.bins, angle_bin_count=clean.shape[1]
                        )
                        cartesian_bins, margins = refined_bins_and_margins(
                            noisy, coarse_bins,
                            search_radius=args.search_radius,
                            search_points=args.search_points,
                        )
                        cartesian_bins = apply_nyquist_alias_lock(
                            coarse_bins, cartesian_bins, angle_bin_count=clean.shape[1]
                        )
                        candan_estimate = estimate_from_bins_lstsq(noisy, candan_bins)
                        cartesian_estimate = estimate_from_bins_lstsq(noisy, cartesian_bins)
                        grid_nmse = nmse_db(grid_estimate, clean)
                        candan_nmse = nmse_db(candan_estimate, clean)
                        cartesian_nmse = nmse_db(cartesian_estimate, clean)
                        grid_residual = residual_fraction(noisy, grid_estimate)
                        candan_residual = residual_fraction(noisy, candan_estimate)
                        cartesian_residual = residual_fraction(noisy, cartesian_estimate)
                        feature_vector = estimator_features(
                            noisy, coarse_bins, candan_bins, search_radius=0.5
                        )
                        physical = {}
                        for method, bins in [
                            ("grid", coarse_bins), ("candan", candan_bins),
                            ("cartesian", cartesian_bins),
                        ]:
                            physical[method] = physical_path_metrics_from_bins(
                                estimated_bins=bins,
                                shape=clean.shape,
                                truth_delays_s=delays_batch[sample_index],
                                truth_spatial_frequencies=spatial_batch[sample_index],
                                truth_path_powers=powers_batch[sample_index],
                                subcarrier_spacing_hz=args.subcarrier_spacing_hz,
                            )
                        row: dict[str, object] = {
                            "profile": profile,
                            "split": "validation" if seed in args.validation_seeds else "test",
                            "seed": seed,
                            "sample_index": sample_index,
                            "snr_db": snr_db,
                            "l_value": l_value,
                            "grid_channel_nmse_db": grid_nmse,
                            "candan_channel_nmse_db": candan_nmse,
                            "cartesian_channel_nmse_db": cartesian_nmse,
                            "candan_gain_vs_grid_db": grid_nmse - candan_nmse,
                            "cartesian_gain_vs_grid_db": grid_nmse - cartesian_nmse,
                            "cartesian_advantage_over_candan_db": candan_nmse - cartesian_nmse,
                            "grid_residual_fraction": grid_residual,
                            "candan_residual_fraction": candan_residual,
                            "cartesian_residual_fraction": cartesian_residual,
                            "candan_residual_reduction_fraction": grid_residual - candan_residual,
                            "cartesian_residual_reduction_fraction": grid_residual - cartesian_residual,
                            "candan_minimum_denominator_stability": candan.minimum_denominator_stability,
                            "candan_mean_denominator_stability": candan.mean_denominator_stability,
                            "candan_maximum_absolute_unclipped_offset": candan.maximum_absolute_unclipped_offset,
                            "candan_clipping_rate": candan.clipping_rate,
                            "minimum_cartesian_candidate_margin": float(np.min(margins)),
                            "log10_candan_condition": float(np.log10(max(design_condition(clean.shape, candan_bins), 1.0))),
                            "log10_cartesian_condition": float(np.log10(max(design_condition(clean.shape, cartesian_bins), 1.0))),
                        }
                        for method in ["grid", "candan", "cartesian"]:
                            row[f"{method}_delay_rmse_ns"] = physical[method]["physical_delay_rmse_ns"]
                            row[f"{method}_angle_rmse_deg"] = physical[method]["projected_broadside_angle_rmse_deg"]
                        row.update({name: float(value) for name, value in zip(FEATURE_NAMES, feature_vector)})
                        rows.append(row)

    validation = [row for row in rows if row["split"] == "validation"]
    test = [row for row in rows if row["split"] == "test"]
    route = calibrate_route(validation)
    feature = str(route["feature"])
    direction = str(route["direction"])
    route_threshold = float(route["threshold"])
    for row in rows:
        fallback = passes(float(row[feature]), direction, route_threshold)
        row["hybrid_fallback"] = int(fallback)
        selected_method = "cartesian" if fallback else "candan"
        row["hybrid_channel_nmse_db"] = row[f"{selected_method}_channel_nmse_db"]
        row["hybrid_gain_vs_grid_db"] = row[f"{selected_method}_gain_vs_grid_db"]
        row["hybrid_residual_reduction_fraction"] = row[f"{selected_method}_residual_reduction_fraction"]
        row["hybrid_delay_rmse_ns"] = row[f"{selected_method}_delay_rmse_ns"]
        row["hybrid_angle_rmse_deg"] = row[f"{selected_method}_angle_rmse_deg"]
        row["oracle_gain_vs_grid_db"] = max(
            0.0, float(row["candan_gain_vs_grid_db"]), float(row["cartesian_gain_vs_grid_db"])
        )

    candan_gate = calibrate_residual_gate(
        validation,
        gain_key="candan_gain_vs_grid_db",
        residual_key="candan_residual_reduction_fraction",
    )
    hybrid_gate = calibrate_residual_gate(
        validation,
        gain_key="hybrid_gain_vs_grid_db",
        residual_key="hybrid_residual_reduction_fraction",
    )
    for row in rows:
        for method, gate in [("candan", candan_gate), ("hybrid", hybrid_gate)]:
            accepted = float(row[f"{method}_residual_reduction_fraction"]) >= float(gate["threshold"])
            row[f"gated_{method}_pass"] = int(accepted)
            row[f"gated_{method}_gain_vs_grid_db"] = float(row[f"{method}_gain_vs_grid_db"]) if accepted else 0.0
            row[f"gated_{method}_channel_nmse_db"] = float(row[f"{method}_channel_nmse_db"]) if accepted else float(row["grid_channel_nmse_db"])
            row[f"gated_{method}_delay_rmse_ns"] = float(row[f"{method}_delay_rmse_ns"]) if accepted else float(row["grid_delay_rmse_ns"])
            row[f"gated_{method}_angle_rmse_deg"] = float(row[f"{method}_angle_rmse_deg"]) if accepted else float(row["grid_angle_rmse_deg"])

    route_metrics = {
        "validation": classification_metrics(
            validation, feature=feature, direction=direction,
            threshold=route_threshold, epsilon_db=args.route_win_epsilon_db,
        ),
        "test": classification_metrics(
            test, feature=feature, direction=direction,
            threshold=route_threshold, epsilon_db=args.route_win_epsilon_db,
        ),
    }
    gate_metrics = {
        "candan_test": gate_classification_metrics(test, method="candan"),
        "hybrid_test": gate_classification_metrics(test, method="hybrid"),
    }
    summary_rows = summarize(test)
    output = ROOT / "05_results" / args.output_dir_name
    output.mkdir(parents=True, exist_ok=True)
    write_csv(output / "per_scene.csv", rows)
    write_csv(output / "test_profile_summary.csv", summary_rows)
    write_csv(output / "route_rule.csv", [route])
    write_csv(output / "residual_gates.csv", [
        {"method": "candan", **candan_gate},
        {"method": "hybrid", **hybrid_gate},
    ])
    result = {
        "config": vars(args),
        "route": route,
        "candan_gate": candan_gate,
        "hybrid_gate": hybrid_gate,
        "route_classification": route_metrics,
        "gate_classification": gate_metrics,
        "test_profile_summary": summary_rows,
        "elapsed_seconds": time.perf_counter() - started,
    }
    (output / "summary.json").write_text(
        json.dumps(result, indent=2, allow_nan=True) + "\n", encoding="utf-8"
    )
    command = "python 04_experiments/eval/run_tsp_candan_route_audit.py"
    write_release_metadata(
        output,
        config=vars(args),
        seeds=[
            *[{"split": "validation", "seed": seed} for seed in args.validation_seeds],
            *[{"split": "test", "seed": seed} for seed in args.test_seeds],
        ],
        command=command,
    )
    write_run_manifest(
        output,
        run_id="tsp_candan_route_audit_20260829",
        command=command,
        config=vars(args),
        metrics={"validation_scene_count": len(validation), "test_scene_count": len(test)},
        notes=[
            "Route and residual thresholds are selected on validation seeds only.",
            "Route features use only the noisy tensor, coarse support, and Candan update.",
            "The oracle is reported only as a specialization ceiling and is not an executable method.",
        ],
        cwd=ROOT,
    )
    print(json.dumps(result, indent=2, allow_nan=True))


if __name__ == "__main__":
    main()
