from __future__ import annotations

import argparse
import csv
import json
from itertools import product
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
import torch
from scipy.optimize import linear_sum_assignment
from sionna.phy import config as sionna_config

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_active_modules"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from common.manifest import environment_snapshot
from common.seed import seed_all
from tompnet.feature_controller import (
    FeatureConditionedRefinementController,
    apply_nyquist_alias_lock,
    estimator_features,
)
from run_sionna_cdl_profile_generalization import (
    add_awgn,
    generate_profile_channels,
    reconstruct_fft_topk,
    support_metrics,
)


SOURCE_ALPHA_CSV = (
    ROOT
    / "05_results"
    / "stage2_torch_locked_scale_g2_seed_sweep"
    / "stage2_torch_locked_scale_g2_seed_sweep_seeds.csv"
)


def finite_mean(values: list[float]) -> float:
    array = np.asarray(values, dtype=float)
    array = array[np.isfinite(array)]
    return float(np.mean(array)) if array.size else float("nan")


def load_source_alpha(path: Path = SOURCE_ALPHA_CSV) -> tuple[float, str]:
    alphas: list[float] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            alphas.append(float(row["alpha"]))
    if not alphas:
        raise ValueError(f"No learned alpha values found in {path}.")
    return finite_mean(alphas), str(path.relative_to(ROOT))


def steering_axis(length: int, frequency_bin: float) -> np.ndarray:
    indices = np.arange(length, dtype=float)
    return np.exp(2j * np.pi * indices * frequency_bin / length) / np.sqrt(length)


def atom_2d(shape: tuple[int, int], bins: tuple[float, float]) -> np.ndarray:
    delay = steering_axis(shape[0], bins[0])
    angle = steering_axis(shape[1], bins[1])
    return delay[:, None] * angle[None, :]


def support_to_bins(support: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    return np.asarray(
        [np.unravel_index(int(index), shape) for index in support],
        dtype=float,
    )


def refine_bins_local(
    measurement: np.ndarray,
    coarse_bins: np.ndarray,
    *,
    search_radius: float,
    search_points: int,
) -> np.ndarray:
    offsets = np.linspace(-search_radius, search_radius, search_points)
    refined: list[tuple[float, float]] = []
    for coarse in coarse_bins:
        best_score = -np.inf
        best_bins = (float(coarse[0]), float(coarse[1]))
        for delta in product(offsets, repeat=2):
            candidate = (float(coarse[0] + delta[0]), float(coarse[1] + delta[1]))
            score = float(np.abs(np.vdot(atom_2d(measurement.shape, candidate), measurement)) ** 2)
            if score > best_score:
                best_score = score
                best_bins = candidate
        refined.append(best_bins)
    return np.asarray(refined, dtype=float)


def interpolate_bins(coarse_bins: np.ndarray, refined_bins: np.ndarray, alpha: float) -> np.ndarray:
    if coarse_bins.shape != refined_bins.shape:
        raise ValueError("coarse_bins and refined_bins must have the same shape")
    return coarse_bins + float(alpha) * (refined_bins - coarse_bins)


def interpolate_bins_axiswise(
    coarse_bins: np.ndarray,
    refined_bins: np.ndarray,
    *,
    delay_alpha: float,
    angle_alpha: float,
) -> np.ndarray:
    if coarse_bins.shape != refined_bins.shape:
        raise ValueError("coarse_bins and refined_bins must have the same shape")
    alpha = np.asarray([delay_alpha, angle_alpha], dtype=float)
    return coarse_bins + alpha * (refined_bins - coarse_bins)


def estimate_from_bins_lstsq(measurement: np.ndarray, bins: np.ndarray) -> np.ndarray:
    if len(bins) == 0:
        return np.zeros_like(measurement)
    design = np.stack(
        [atom_2d(measurement.shape, (float(pair[0]), float(pair[1]))).reshape(-1) for pair in bins],
        axis=1,
    )
    coefficients, *_ = np.linalg.lstsq(design, measurement.reshape(-1), rcond=None)
    return (design @ coefficients).reshape(measurement.shape)


def nmse_db(estimate: np.ndarray, clean: np.ndarray) -> float:
    denominator = float(np.linalg.norm(clean) ** 2)
    ratio = float(np.linalg.norm(estimate - clean) ** 2 / max(denominator, 1e-300))
    return 10.0 * np.log10(max(ratio, 1e-300))


def circular_distance(values_a: np.ndarray, values_b: np.ndarray, period: float) -> np.ndarray:
    delta = np.abs(values_a - values_b)
    return np.minimum(delta, period - delta)


def bins_to_physical(
    bins: np.ndarray,
    *,
    shape: tuple[int, int],
    subcarrier_spacing_hz: float,
) -> tuple[np.ndarray, np.ndarray]:
    delay_bins, angle_bins = shape
    delays_s = np.mod(-bins[:, 0], delay_bins) / (delay_bins * subcarrier_spacing_hz)
    spatial_frequencies = np.mod(bins[:, 1] / angle_bins + 0.5, 1.0) - 0.5
    return delays_s, spatial_frequencies


def broadside_angle_error_deg(truth_q: float, estimate_q: float) -> float:
    truth_angle = float(np.degrees(np.arcsin(np.clip(2.0 * truth_q, -1.0, 1.0))))
    estimate_u = 2.0 * estimate_q
    candidates = np.asarray([estimate_u - 2.0, estimate_u, estimate_u + 2.0])
    candidates = candidates[(candidates >= -1.0 - 1e-12) & (candidates <= 1.0 + 1e-12)]
    candidate_angles = np.degrees(np.arcsin(np.clip(candidates, -1.0, 1.0)))
    return float(np.min(np.abs(candidate_angles - truth_angle)))


def physical_path_metrics_from_bins(
    *,
    estimated_bins: np.ndarray,
    shape: tuple[int, int],
    truth_delays_s: np.ndarray,
    truth_spatial_frequencies: np.ndarray,
    truth_path_powers: np.ndarray,
    subcarrier_spacing_hz: float,
) -> dict[str, float]:
    number_of_matches = min(len(estimated_bins), len(truth_delays_s))
    truth_indices = np.argsort(truth_path_powers)[::-1][:number_of_matches]
    selected_delays = truth_delays_s[truth_indices]
    selected_spatial = truth_spatial_frequencies[truth_indices]
    estimated_delays, estimated_spatial = bins_to_physical(
        estimated_bins,
        shape=shape,
        subcarrier_spacing_hz=subcarrier_spacing_hz,
    )

    delay_period_s = 1.0 / subcarrier_spacing_hz
    delay_resolution_s = 1.0 / (shape[0] * subcarrier_spacing_hz)
    spatial_resolution = 1.0 / shape[1]
    delay_cost = circular_distance(
        selected_delays[:, None], estimated_delays[None, :], delay_period_s
    ) / delay_resolution_s
    spatial_cost = circular_distance(
        selected_spatial[:, None], estimated_spatial[None, :], 1.0
    ) / spatial_resolution
    row_indices, column_indices = linear_sum_assignment(delay_cost**2 + spatial_cost**2)

    delay_errors_s = circular_distance(
        selected_delays[row_indices], estimated_delays[column_indices], delay_period_s
    )
    spatial_errors = circular_distance(
        selected_spatial[row_indices], estimated_spatial[column_indices], 1.0
    )
    angle_errors_deg = np.asarray(
        [
            broadside_angle_error_deg(
                float(selected_spatial[truth_index]),
                float(estimated_spatial[estimate_index]),
            )
            for truth_index, estimate_index in zip(row_indices, column_indices)
        ],
        dtype=float,
    )
    return {
        "matched_physical_paths": float(len(row_indices)),
        "physical_delay_rmse_ns": float(np.sqrt(np.mean(delay_errors_s**2)) * 1e9),
        "physical_delay_rmse_bins": float(
            np.sqrt(np.mean((delay_errors_s / delay_resolution_s) ** 2))
        ),
        "projected_spatial_frequency_rmse": float(
            np.sqrt(np.mean(spatial_errors**2))
        ),
        "projected_spatial_frequency_rmse_bins": float(
            np.sqrt(np.mean((spatial_errors / spatial_resolution) ** 2))
        ),
        "projected_broadside_angle_rmse_deg": float(np.sqrt(np.mean(angle_errors_deg**2))),
    }


def transfer_verdict(metrics: dict[str, float | str]) -> tuple[str, str]:
    nmse_gain = float(metrics["mean_trained_refinement_gain_vs_grid_db"])
    delay_gain = float(metrics["mean_physical_delay_rmse_reduction_vs_grid_ns"])
    angle_gain = float(metrics["mean_projected_angle_rmse_reduction_vs_grid_deg"])
    if nmse_gain > 0.0 and delay_gain > 0.0 and angle_gain > 0.0:
        evidence_suffix = (
            "scaled"
            if float(metrics.get("seed_count", 0.0)) >= 5.0
            and float(metrics.get("samples_per_profile_seed", 0.0)) >= 50.0
            else "dev"
        )
        return (
            f"trained-refinement-physical-transfer-supported-{evidence_suffix}",
            "The frozen trained bounded-refinement estimator improves channel NMSE and both CIR-grounded physical RMSE metrics on the tested CDL cells.",
        )
    if nmse_gain > 0.0 and (delay_gain > 0.0 or angle_gain > 0.0):
        return (
            "trained-refinement-physical-transfer-mixed",
            "The frozen trained bounded-refinement estimator improves channel NMSE and one physical metric, but the other physical metric does not improve; retain this as mixed evidence.",
        )
    if nmse_gain <= 0.0 and delay_gain <= 0.0 and angle_gain <= 0.0:
        return (
            "trained-refinement-physical-transfer-refuted",
            "The frozen trained bounded-refinement estimator fails to improve channel NMSE or either physical metric on the tested CDL cells.",
        )
    return (
        "trained-refinement-physical-transfer-inconclusive",
        "The channel and physical metrics move in conflicting directions, so the transfer claim remains inconclusive.",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profiles", nargs="+", default=["A", "C", "D"])
    parser.add_argument("--snrs", nargs="+", type=float, default=[0.0, 10.0, 20.0, 30.0])
    parser.add_argument("--l-values", nargs="+", type=int, default=[4, 8, 16])
    parser.add_argument("--seeds", nargs="+", type=int, default=[20260626, 20260627])
    parser.add_argument("--samples-per-profile-seed", type=int, default=4)
    parser.add_argument("--num-subcarriers", type=int, default=64)
    parser.add_argument("--num-tx-antennas", type=int, default=4)
    parser.add_argument("--spatial-truth-oversampling", type=int, default=4096)
    parser.add_argument("--subcarrier-spacing-hz", type=float, default=120e3)
    parser.add_argument("--carrier-frequency-hz", type=float, default=60e9)
    parser.add_argument("--delay-spread-s", type=float, default=100e-9)
    parser.add_argument("--search-radius", type=float, default=0.45)
    parser.add_argument("--search-points", type=int, default=5)
    parser.add_argument("--delay-alpha-override", type=float)
    parser.add_argument("--angle-alpha-override", type=float)
    parser.add_argument("--controller-checkpoint")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--output-dir-name", default="sionna_cdl_trained_refinement")
    return parser.parse_args()


def write_evaluation_summary(
    output_dir: Path,
    *,
    metrics: dict[str, float | str],
    interpretation: str,
) -> Path:
    is_source_model = metrics["estimator_mode"] in {
        "source-trained-shared-alpha",
        "source-trained-feature-controller",
    }
    estimator_statement = (
        "This run transfers a frozen source-trained bounded-refinement estimator."
        if is_source_model
        else "This run is an axis-coupling diagnostic with explicitly overridden delay/angle alpha values."
    )
    lines = [
        "# Sionna CDL Trained-Refinement Physical Evaluation",
        "",
        "## Outcome Summary",
        "",
        interpretation,
        "",
        estimator_statement + " It evaluates continuous delay/angle bins with CIR-grounded Hungarian matching; it does not claim a deeper multi-parameter T-OMP-Net architecture.",
        "",
        "## evaluation_summary",
        "",
        "- `research_question`: Does the Stage-2 source-trained bounded-refinement layer improve CDL channel NMSE and CIR-grounded delay/projected-angle RMSE over grid FFT top-k?",
        f"- `claim_update`: {metrics['claim_update']}",
        "- `baseline_relation`: Grid and trained refinement use identical noisy CDL samples, support budgets, truth paths, and Hungarian physical-metric contract.",
        "- `failure_mode`: A mixed or negative physical result means the frozen estimator is insufficient for that profile/setting; no test-truth tuning is permitted.",
        f"- `mechanism_note`: {interpretation}",
        "- `next_action`: If supported, scale the unchanged contract; if mixed/refuted, preserve the negative result and implement a genuinely richer trained refinement model before another external run.",
        "- `evidence_level`: E1 auxiliary/dev trained-refinement physical transfer evidence.",
        "",
        "## Key Metrics",
        "",
    ]
    for key, value in metrics.items():
        if isinstance(value, float):
            lines.append(f"- `{key}`: {value:.6g}")
        else:
            lines.append(f"- `{key}`: `{value}`")
    path = output_dir / "evaluation_summary.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    args = parse_args()
    started = time.perf_counter()
    source_alpha, source_alpha_path = load_source_alpha()
    if args.controller_checkpoint and (
        args.delay_alpha_override is not None or args.angle_alpha_override is not None
    ):
        raise ValueError("controller checkpoint cannot be combined with alpha overrides")
    controller_models = []
    controller_checkpoint_path = ""
    if args.controller_checkpoint:
        checkpoint_path = Path(args.controller_checkpoint)
        if not checkpoint_path.is_absolute():
            checkpoint_path = ROOT / checkpoint_path
        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        for item in checkpoint["models"]:
            model = FeatureConditionedRefinementController(
                hidden_dim=int(checkpoint["hidden_dim"])
            )
            model.load_state_dict(item["state_dict"])
            model.eval()
            controller_models.append(
                (model, item["feature_mean"], item["feature_std"])
            )
        controller_checkpoint_path = str(checkpoint_path.relative_to(ROOT))
    delay_alpha = source_alpha if args.delay_alpha_override is None else args.delay_alpha_override
    angle_alpha = source_alpha if args.angle_alpha_override is None else args.angle_alpha_override
    estimator_mode = (
        "source-trained-feature-controller"
        if controller_models
        else "source-trained-shared-alpha"
        if args.delay_alpha_override is None and args.angle_alpha_override is None
        else "axis-ablation-not-paper-estimator"
    )
    rows: list[dict[str, float | str]] = []
    sample_rows: list[dict[str, float | str]] = []

    for profile in args.profiles:
        for seed in args.seeds:
            seed_all(seed)
            torch.manual_seed(seed)
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
                    cell_samples: list[dict[str, float | str]] = []
                    for sample_index, (clean, noisy) in enumerate(zip(clean_batch, noisy_batch)):
                        grid_estimate, support, _ = reconstruct_fft_topk(noisy, l_value)
                        coarse_bins = support_to_bins(support, clean.shape)
                        locally_refined_bins = refine_bins_local(
                            noisy,
                            coarse_bins,
                            search_radius=args.search_radius,
                            search_points=args.search_points,
                        )
                        sample_delay_alpha = delay_alpha
                        sample_angle_alpha = angle_alpha
                        if controller_models:
                            feature_vector = estimator_features(
                                noisy,
                                coarse_bins,
                                locally_refined_bins,
                                search_radius=args.search_radius,
                            )
                            predictions = []
                            with torch.no_grad():
                                for controller, feature_mean, feature_std in controller_models:
                                    normalized = (
                                        torch.as_tensor(feature_vector, dtype=torch.float64)
                                        - feature_mean
                                    ) / feature_std
                                    predictions.append(controller(normalized).numpy())
                            ensemble_alpha = np.mean(np.stack(predictions), axis=0)
                            sample_delay_alpha = float(ensemble_alpha[0])
                            sample_angle_alpha = float(ensemble_alpha[1])
                        trained_bins = interpolate_bins_axiswise(
                            coarse_bins,
                            locally_refined_bins,
                            delay_alpha=sample_delay_alpha,
                            angle_alpha=sample_angle_alpha,
                        )
                        if controller_models:
                            trained_bins = apply_nyquist_alias_lock(
                                coarse_bins,
                                trained_bins,
                                angle_bin_count=clean.shape[1],
                            )
                        trained_estimate = estimate_from_bins_lstsq(noisy, trained_bins)
                        grid_nmse = nmse_db(grid_estimate, clean)
                        trained_nmse = nmse_db(trained_estimate, clean)
                        grid_physical = physical_path_metrics_from_bins(
                            estimated_bins=coarse_bins,
                            shape=clean.shape,
                            truth_delays_s=delays_batch[sample_index],
                            truth_spatial_frequencies=spatial_batch[sample_index],
                            truth_path_powers=powers_batch[sample_index],
                            subcarrier_spacing_hz=args.subcarrier_spacing_hz,
                        )
                        trained_physical = physical_path_metrics_from_bins(
                            estimated_bins=trained_bins,
                            shape=clean.shape,
                            truth_delays_s=delays_batch[sample_index],
                            truth_spatial_frequencies=spatial_batch[sample_index],
                            truth_path_powers=powers_batch[sample_index],
                            subcarrier_spacing_hz=args.subcarrier_spacing_hz,
                        )
                        support_result = support_metrics(clean, support, l_value)
                        sample_row: dict[str, float | str] = {
                            "profile": profile,
                            "seed": float(seed),
                            "sample_index": float(sample_index),
                            "snr_db": float(snr_db),
                            "l_value": float(l_value),
                            "source_alpha": source_alpha,
                            "delay_alpha": sample_delay_alpha,
                            "angle_alpha": sample_angle_alpha,
                            "estimator_mode": estimator_mode,
                            "grid_channel_nmse_db": grid_nmse,
                            "trained_refinement_channel_nmse_db": trained_nmse,
                            "trained_refinement_gain_vs_grid_db": grid_nmse - trained_nmse,
                            "grid_physical_delay_rmse_ns": grid_physical["physical_delay_rmse_ns"],
                            "trained_refinement_physical_delay_rmse_ns": trained_physical["physical_delay_rmse_ns"],
                            "physical_delay_rmse_reduction_vs_grid_ns": grid_physical["physical_delay_rmse_ns"] - trained_physical["physical_delay_rmse_ns"],
                            "grid_projected_broadside_angle_rmse_deg": grid_physical["projected_broadside_angle_rmse_deg"],
                            "trained_refinement_projected_broadside_angle_rmse_deg": trained_physical["projected_broadside_angle_rmse_deg"],
                            "projected_angle_rmse_reduction_vs_grid_deg": grid_physical["projected_broadside_angle_rmse_deg"] - trained_physical["projected_broadside_angle_rmse_deg"],
                            "matched_physical_paths": trained_physical["matched_physical_paths"],
                            "support_recall": support_result["support_recall"],
                            "topk_energy_efficiency": support_result["topk_energy_efficiency"],
                        }
                        sample_rows.append(sample_row)
                        cell_samples.append(sample_row)
                    rows.append(
                        {
                            "profile": profile,
                            "seed": float(seed),
                            "snr_db": float(snr_db),
                            "l_value": float(l_value),
                            "n_samples": float(len(cell_samples)),
                            "source_alpha": source_alpha,
                            "delay_alpha": finite_mean(
                                [float(item["delay_alpha"]) for item in cell_samples]
                            ),
                            "angle_alpha": finite_mean(
                                [float(item["angle_alpha"]) for item in cell_samples]
                            ),
                            "estimator_mode": estimator_mode,
                            **{
                                f"mean_{key}": finite_mean([float(item[key]) for item in cell_samples])
                                for key in (
                                    "grid_channel_nmse_db",
                                    "trained_refinement_channel_nmse_db",
                                    "trained_refinement_gain_vs_grid_db",
                                    "grid_physical_delay_rmse_ns",
                                    "trained_refinement_physical_delay_rmse_ns",
                                    "physical_delay_rmse_reduction_vs_grid_ns",
                                    "grid_projected_broadside_angle_rmse_deg",
                                    "trained_refinement_projected_broadside_angle_rmse_deg",
                                    "projected_angle_rmse_reduction_vs_grid_deg",
                                    "support_recall",
                                    "topk_energy_efficiency",
                                )
                            },
                        }
                    )

    elapsed_seconds = time.perf_counter() - started
    metrics: dict[str, float | str] = {
        "profiles": ",".join(args.profiles),
        "snrs_db": ",".join(str(value) for value in args.snrs),
        "l_values": ",".join(str(value) for value in args.l_values),
        "seed_count": float(len(args.seeds)),
        "samples_per_profile_seed": float(args.samples_per_profile_seed),
        "row_count": float(len(rows)),
        "sample_row_count": float(len(sample_rows)),
        "source_alpha": source_alpha,
        "source_alpha_source": source_alpha_path,
        "delay_alpha": finite_mean([float(row["delay_alpha"]) for row in rows]),
        "angle_alpha": finite_mean([float(row["angle_alpha"]) for row in rows]),
        "estimator_mode": estimator_mode,
        "controller_checkpoint": controller_checkpoint_path,
        "controller_ensemble_size": float(len(controller_models)),
        "mean_grid_channel_nmse_db": finite_mean([float(row["mean_grid_channel_nmse_db"]) for row in rows]),
        "mean_trained_refinement_channel_nmse_db": finite_mean([float(row["mean_trained_refinement_channel_nmse_db"]) for row in rows]),
        "mean_trained_refinement_gain_vs_grid_db": finite_mean([float(row["mean_trained_refinement_gain_vs_grid_db"]) for row in rows]),
        "min_cell_trained_refinement_gain_vs_grid_db": min(float(row["mean_trained_refinement_gain_vs_grid_db"]) for row in rows),
        "mean_grid_physical_delay_rmse_ns": finite_mean([float(row["mean_grid_physical_delay_rmse_ns"]) for row in rows]),
        "mean_trained_refinement_physical_delay_rmse_ns": finite_mean([float(row["mean_trained_refinement_physical_delay_rmse_ns"]) for row in rows]),
        "mean_physical_delay_rmse_reduction_vs_grid_ns": finite_mean([float(row["mean_physical_delay_rmse_reduction_vs_grid_ns"]) for row in rows]),
        "mean_grid_projected_broadside_angle_rmse_deg": finite_mean([float(row["mean_grid_projected_broadside_angle_rmse_deg"]) for row in rows]),
        "mean_trained_refinement_projected_broadside_angle_rmse_deg": finite_mean([float(row["mean_trained_refinement_projected_broadside_angle_rmse_deg"]) for row in rows]),
        "mean_projected_angle_rmse_reduction_vs_grid_deg": finite_mean([float(row["mean_projected_angle_rmse_reduction_vs_grid_deg"]) for row in rows]),
        "min_cell_physical_delay_rmse_reduction_vs_grid_ns": min(float(row["mean_physical_delay_rmse_reduction_vs_grid_ns"]) for row in rows),
        "min_cell_projected_angle_rmse_reduction_vs_grid_deg": min(float(row["mean_projected_angle_rmse_reduction_vs_grid_deg"]) for row in rows),
        "delay_resolution_ns": 1e9 / (args.num_subcarriers * args.subcarrier_spacing_hz),
        "elapsed_seconds": elapsed_seconds,
    }
    claim_update, interpretation = transfer_verdict(metrics)
    if estimator_mode == "axis-ablation-not-paper-estimator":
        claim_update = f"diagnostic-{claim_update}"
        interpretation = (
            "Axis-coupling diagnostic only: "
            + interpretation
            + " The override is not a trained paper estimator and is used only to route the next model design."
        )
    metrics["claim_update"] = claim_update

    output_dir = ROOT / "05_results" / args.output_dir_name
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_csv = output_dir / "sionna_cdl_trained_refinement.csv"
    sample_csv = output_dir / "sionna_cdl_trained_refinement_samples.csv"
    for path, records in ((summary_csv, rows), (sample_csv, sample_rows)):
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(records[0].keys()))
            writer.writeheader()
            writer.writerows(records)

    manifest = {
        "run_id": f"sionna_cdl_trained_refinement_{len(args.seeds)}x{args.samples_per_profile_seed}",
        "command": subprocess.list2cmdline([sys.executable, str(Path(__file__).resolve().relative_to(ROOT)), *sys.argv[1:]]),
        "config": {
            "profiles": args.profiles,
            "snrs": args.snrs,
            "l_values": args.l_values,
            "seeds": args.seeds,
            "samples_per_profile_seed": args.samples_per_profile_seed,
            "num_subcarriers": args.num_subcarriers,
            "num_tx_antennas": args.num_tx_antennas,
            "spatial_truth_oversampling": args.spatial_truth_oversampling,
            "subcarrier_spacing_hz": args.subcarrier_spacing_hz,
            "carrier_frequency_hz": args.carrier_frequency_hz,
            "delay_spread_s": args.delay_spread_s,
            "search_radius": args.search_radius,
            "search_points": args.search_points,
            "source_alpha": source_alpha,
            "source_alpha_source": source_alpha_path,
            "delay_alpha": delay_alpha,
            "angle_alpha": angle_alpha,
            "estimator_mode": estimator_mode,
            "controller_checkpoint": controller_checkpoint_path,
            "controller_ensemble_size": len(controller_models),
            "device": args.device,
        },
        "metrics": metrics,
        "environment": environment_snapshot(ROOT),
        "notes": [
            "Grid and trained refinement are paired on identical Sionna CDL samples.",
            "The transferred estimator is frozen before this run; no external test-truth tuning is performed.",
            "Delay truth comes from Sionna tau; angle is the identifiable projected ULA broadside quantity.",
            "This dev result must not be described as a deeper full T-OMP-Net evaluation.",
            "Any axis override is a diagnostic ablation only and must not be promoted as a trained estimator.",
        ],
    }
    manifest_path = output_dir / "run_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    evaluation_path = write_evaluation_summary(output_dir, metrics=metrics, interpretation=interpretation)
    summary_lines = [
        "# Sionna CDL Trained-Refinement Physical Evaluation",
        "",
        f"- Claim update: `{claim_update}`",
        f"- Source alpha: `{source_alpha:.6g}` from `{source_alpha_path}`",
        f"- Mean applied delay/angle alpha: `{metrics['delay_alpha']:.6g}` / `{metrics['angle_alpha']:.6g}` (`{estimator_mode}`)",
        f"- Mean channel NMSE gain vs grid: `{metrics['mean_trained_refinement_gain_vs_grid_db']:.6g}` dB",
        f"- Mean physical delay RMSE: grid `{metrics['mean_grid_physical_delay_rmse_ns']:.6g}` ns -> trained `{metrics['mean_trained_refinement_physical_delay_rmse_ns']:.6g}` ns",
        f"- Mean projected-angle RMSE: grid `{metrics['mean_grid_projected_broadside_angle_rmse_deg']:.6g}` deg -> trained `{metrics['mean_trained_refinement_projected_broadside_angle_rmse_deg']:.6g}` deg",
        f"- Elapsed seconds: `{elapsed_seconds:.2f}`",
        "",
        "## Interpretation",
        "",
        interpretation,
        "",
        "## Evidence boundary",
        "",
        (
            "This records the physical-metric result for the frozen trained bounded-refinement estimator. "
            if estimator_mode in {"source-trained-shared-alpha", "source-trained-feature-controller"}
            else "This is a diagnostic axis-coupling ablation and is not a trained paper estimator. "
        )
        + "It is not evidence for a deeper multi-parameter T-OMP-Net unless that architecture is implemented and evaluated separately.",
        "",
        "## Artifacts",
        "",
        f"- `{summary_csv.relative_to(ROOT)}`",
        f"- `{sample_csv.relative_to(ROOT)}`",
        f"- `{manifest_path.relative_to(ROOT)}`",
        f"- `{evaluation_path.relative_to(ROOT)}`",
    ]
    summary_path = output_dir / "summary.md"
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    print(f"Wrote {summary_path.relative_to(ROOT)}")
    print(f"claim_update={claim_update}")
    print(f"mean_trained_refinement_gain_vs_grid_db={metrics['mean_trained_refinement_gain_vs_grid_db']:.6f}")
    print(f"mean_physical_delay_rmse_reduction_vs_grid_ns={metrics['mean_physical_delay_rmse_reduction_vs_grid_ns']:.6f}")
    print(f"mean_projected_angle_rmse_reduction_vs_grid_deg={metrics['mean_projected_angle_rmse_reduction_vs_grid_deg']:.6f}")


if __name__ == "__main__":
    main()
