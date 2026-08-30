from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
from scipy.optimize import linear_sum_assignment
import torch
from sionna.phy import config as sionna_config
from sionna.phy.channel import cir_to_ofdm_channel, subcarrier_frequencies
from sionna.phy.channel.tr38901.antenna import PanelArray
from sionna.phy.channel.tr38901.cdl import CDL

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_active_modules"))

from common.manifest import environment_snapshot
from common.seed import seed_all


def finite_mean(values: list[float]) -> float:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    return float(np.mean(arr)) if arr.size else float("nan")


def shape_text(value: object) -> str:
    if hasattr(value, "shape"):
        return "x".join(str(dim) for dim in value.shape)
    return str(value)


def make_arrays(
    *,
    carrier_frequency: float,
    num_tx_antennas: int,
    device: str,
) -> tuple[PanelArray, PanelArray]:
    ut_array = PanelArray(
        num_rows_per_panel=1,
        num_cols_per_panel=1,
        polarization="single",
        polarization_type="V",
        antenna_pattern="omni",
        carrier_frequency=carrier_frequency,
        device=device,
    )
    bs_array = PanelArray(
        num_rows_per_panel=1,
        num_cols_per_panel=num_tx_antennas,
        polarization="single",
        polarization_type="V",
        antenna_pattern="38.901",
        carrier_frequency=carrier_frequency,
        device=device,
    )
    return ut_array, bs_array


def generate_profile_channels(
    *,
    profile: str,
    batch_size: int,
    num_subcarriers: int,
    subcarrier_spacing_hz: float,
    carrier_frequency_hz: float,
    delay_spread_s: float,
    num_tx_antennas: int,
    spatial_truth_oversampling: int,
    device: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    ut_array, bs_array = make_arrays(
        carrier_frequency=carrier_frequency_hz,
        num_tx_antennas=num_tx_antennas,
        device=device,
    )
    model = CDL(
        model=profile,
        delay_spread=delay_spread_s,
        carrier_frequency=carrier_frequency_hz,
        ut_array=ut_array,
        bs_array=bs_array,
        direction="downlink",
        min_speed=0.0,
        max_speed=0.0,
        device=device,
    )
    h_cir, tau = model(
        batch_size=batch_size,
        num_time_steps=1,
        sampling_frequency=num_subcarriers * subcarrier_spacing_hz,
    )
    frequencies = subcarrier_frequencies(
        num_subcarriers,
        subcarrier_spacing_hz,
        device=device,
    )
    h_ofdm = cir_to_ofdm_channel(frequencies, h_cir, tau, normalize=True)
    # [batch, rx, rx_ant, tx, tx_ant, time, subcarrier] -> [batch, subcarrier, tx_ant]
    tensor = h_ofdm[:, 0, 0, 0, :, 0, :].permute(0, 2, 1)
    channels = tensor.detach().cpu().numpy().astype(np.complex128)

    # Each CIR path is a cluster-level antenna vector. Its delay is returned
    # directly by Sionna. A 1-D ULA identifies only projected spatial
    # frequency, so the clean per-cluster antenna vector is oversampled to
    # define an effective broadside direction without pretending to recover
    # separate azimuth and zenith angles.
    path_vectors = h_cir[:, 0, 0, 0, :, :, 0].detach().cpu().numpy()
    path_powers = np.sum(np.abs(path_vectors) ** 2, axis=1)
    spatial_spectra = np.fft.fft(
        path_vectors,
        n=spatial_truth_oversampling,
        axis=1,
    )
    spatial_peak_bins = np.argmax(np.abs(spatial_spectra), axis=1)
    spatial_frequency_grid = np.fft.fftfreq(spatial_truth_oversampling)
    projected_spatial_frequencies = spatial_frequency_grid[spatial_peak_bins]
    physical_delays_s = tau[:, 0, 0, :].detach().cpu().numpy().astype(float)
    return (
        channels,
        physical_delays_s,
        projected_spatial_frequencies.astype(float),
        path_powers.astype(float),
    )


def add_awgn(clean: np.ndarray, *, snr_db: float, rng: np.random.Generator) -> tuple[np.ndarray, float]:
    signal_power = float(np.mean(np.abs(clean) ** 2))
    noise_variance = signal_power / (10.0 ** (snr_db / 10.0))
    noise = np.sqrt(noise_variance / 2.0) * (
        rng.standard_normal(clean.shape) + 1j * rng.standard_normal(clean.shape)
    )
    return clean + noise, noise_variance


def topk_support(spectrum: np.ndarray, k: int) -> np.ndarray:
    flat = spectrum.reshape(-1)
    if k >= flat.size:
        return np.arange(flat.size)
    support = np.argpartition(np.abs(flat), -k)[-k:]
    return support[np.argsort(np.abs(flat[support]))[::-1]]


def reconstruct_fft_topk(measurement: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    spectrum = np.fft.fftn(measurement, norm="ortho")
    support = topk_support(spectrum, k)
    estimate_spectrum = np.zeros_like(spectrum.reshape(-1))
    estimate_spectrum[support] = spectrum.reshape(-1)[support]
    estimate_spectrum = estimate_spectrum.reshape(spectrum.shape)
    estimate = np.fft.ifftn(estimate_spectrum, norm="ortho")
    return estimate, support, spectrum


def nmse_db(estimate: np.ndarray, clean: np.ndarray) -> float:
    denom = float(np.linalg.norm(clean) ** 2)
    nmse = float(np.linalg.norm(estimate - clean) ** 2 / max(denom, 1e-300))
    return 10.0 * np.log10(max(nmse, 1e-300))


def support_metrics(clean: np.ndarray, est_support: np.ndarray, k: int) -> dict[str, float]:
    clean_spectrum = np.fft.fftn(clean, norm="ortho")
    true_support = topk_support(clean_spectrum, k)
    true_set = set(int(item) for item in true_support)
    est_set = set(int(item) for item in est_support)
    recall = len(true_set & est_set) / max(len(true_set), 1)
    clean_flat = clean_spectrum.reshape(-1)
    captured_energy = float(np.sum(np.abs(clean_flat[list(est_set)]) ** 2))
    total_energy = float(np.sum(np.abs(clean_flat) ** 2))
    energy_recall = captured_energy / max(total_energy, 1e-300)
    optimal_topk_energy = float(np.sum(np.abs(clean_flat[true_support]) ** 2))
    topk_energy_efficiency = captured_energy / max(optimal_topk_energy, 1e-300)
    sorted_energy = np.sort(np.abs(clean_flat) ** 2)[::-1]
    cumulative_energy = np.cumsum(sorted_energy) / max(total_energy, 1e-300)
    effective_support_95 = float(np.searchsorted(cumulative_energy, 0.95) + 1)
    effective_support_99 = float(np.searchsorted(cumulative_energy, 0.99) + 1)
    clean_topk_energy_fraction = optimal_topk_energy / max(total_energy, 1e-300)
    delay_support_recall = axis_support_recall(
        true_support,
        est_support,
        clean.shape,
        axis=0,
    )
    angle_support_recall = axis_support_recall(
        true_support,
        est_support,
        clean.shape,
        axis=1,
    )
    delay_rmse, angle_rmse = bin_rmse(true_support, est_support, clean.shape)
    return {
        "support_recall": float(recall),
        "dominant_energy_recall": float(energy_recall),
        "topk_energy_efficiency": float(topk_energy_efficiency),
        "clean_topk_energy_fraction": float(clean_topk_energy_fraction),
        "effective_support_95": effective_support_95,
        "effective_support_99": effective_support_99,
        "delay_support_recall": delay_support_recall,
        "angle_support_recall": angle_support_recall,
        "delay_bin_rmse": delay_rmse,
        "angle_bin_rmse": angle_rmse,
    }


def unravel_bins(flat_support: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    return np.asarray([np.unravel_index(int(index), shape) for index in flat_support], dtype=float)


def circular_delta(a: np.ndarray, b: np.ndarray, period: int) -> np.ndarray:
    delta = np.abs(a - b)
    return np.minimum(delta, period - delta)


def axis_support_recall(
    true_support: np.ndarray,
    est_support: np.ndarray,
    shape: tuple[int, int],
    *,
    axis: int,
) -> float:
    true_bins = unravel_bins(true_support, shape)
    est_bins = unravel_bins(est_support, shape)
    delta = circular_delta(
        true_bins[:, None, axis],
        est_bins[None, :, axis],
        shape[axis],
    )
    # A binary assignment maximizes the number of exact axis matches. Using
    # squared distance can sacrifice zero-distance pairs when several global
    # assignments have similar total displacement.
    cost = (delta != 0).astype(float)
    row_ind, col_ind = linear_sum_assignment(cost)
    errors = circular_delta(
        true_bins[row_ind, axis],
        est_bins[col_ind, axis],
        shape[axis],
    )
    return float(np.mean(errors == 0))


def bin_rmse(true_support: np.ndarray, est_support: np.ndarray, shape: tuple[int, int]) -> tuple[float, float]:
    true_bins = unravel_bins(true_support, shape)
    est_bins = unravel_bins(est_support, shape)
    cost = (
        circular_delta(true_bins[:, None, 0], est_bins[None, :, 0], shape[0]) ** 2
        + circular_delta(true_bins[:, None, 1], est_bins[None, :, 1], shape[1]) ** 2
    )
    row_ind, col_ind = linear_sum_assignment(cost)
    delay_errors = circular_delta(true_bins[row_ind, 0], est_bins[col_ind, 0], shape[0])
    angle_errors = circular_delta(true_bins[row_ind, 1], est_bins[col_ind, 1], shape[1])
    return (
        float(np.sqrt(np.mean(delay_errors**2))),
        float(np.sqrt(np.mean(angle_errors**2))),
    )


def circular_distance(values_a: np.ndarray, values_b: np.ndarray, period: float) -> np.ndarray:
    delta = np.abs(values_a - values_b)
    return np.minimum(delta, period - delta)


def broadside_angle_error_deg(truth_q: float, estimate_q: float) -> float:
    truth_angle = float(np.degrees(np.arcsin(np.clip(2.0 * truth_q, -1.0, 1.0))))
    estimate_u = 2.0 * estimate_q
    candidates = np.asarray([estimate_u - 2.0, estimate_u, estimate_u + 2.0])
    candidates = candidates[(candidates >= -1.0 - 1e-12) & (candidates <= 1.0 + 1e-12)]
    candidate_angles = np.degrees(np.arcsin(np.clip(candidates, -1.0, 1.0)))
    return float(np.min(np.abs(candidate_angles - truth_angle)))


def physical_path_metrics(
    *,
    est_support: np.ndarray,
    shape: tuple[int, int],
    truth_delays_s: np.ndarray,
    truth_spatial_frequencies: np.ndarray,
    truth_path_powers: np.ndarray,
    subcarrier_spacing_hz: float,
) -> dict[str, float]:
    num_delay_bins, num_angle_bins = shape
    num_matches = min(len(est_support), len(truth_delays_s))
    truth_indices = np.argsort(truth_path_powers)[::-1][:num_matches]
    selected_truth_delays = truth_delays_s[truth_indices]
    selected_truth_q = truth_spatial_frequencies[truth_indices]

    est_bins = unravel_bins(est_support, shape).astype(int)
    est_delays = (
        (-est_bins[:, 0]) % num_delay_bins
    ) / (num_delay_bins * subcarrier_spacing_hz)
    spatial_frequency_grid = np.fft.fftfreq(num_angle_bins)
    est_q = spatial_frequency_grid[est_bins[:, 1]]

    delay_period_s = 1.0 / subcarrier_spacing_hz
    delay_resolution_s = 1.0 / (num_delay_bins * subcarrier_spacing_hz)
    spatial_resolution = 1.0 / num_angle_bins
    delay_cost = circular_distance(
        selected_truth_delays[:, None],
        est_delays[None, :],
        delay_period_s,
    ) / delay_resolution_s
    spatial_cost = circular_distance(
        selected_truth_q[:, None],
        est_q[None, :],
        1.0,
    ) / spatial_resolution
    row_ind, col_ind = linear_sum_assignment(delay_cost**2 + spatial_cost**2)

    delay_errors_s = circular_distance(
        selected_truth_delays[row_ind],
        est_delays[col_ind],
        delay_period_s,
    )
    angle_errors_deg = np.asarray(
        [
            broadside_angle_error_deg(
                float(selected_truth_q[truth_index]),
                float(est_q[estimate_index]),
            )
            for truth_index, estimate_index in zip(row_ind, col_ind)
        ],
        dtype=float,
    )
    return {
        "matched_physical_paths": float(len(row_ind)),
        "physical_delay_rmse_ns": float(np.sqrt(np.mean(delay_errors_s**2)) * 1e9),
        "projected_broadside_angle_rmse_deg": float(
            np.sqrt(np.mean(angle_errors_deg**2))
        ),
    }


def verdict(rows: list[dict[str, float | str]]) -> tuple[str, str]:
    nmse_values = [float(row["mean_channel_nmse_db"]) for row in rows]
    recall_values = [float(row["mean_support_recall"]) for row in rows]
    efficiency_values = [float(row["mean_topk_energy_efficiency"]) for row in rows]
    if (
        all(np.isfinite(nmse_values))
        and all(np.isfinite(recall_values))
        and all(np.isfinite(efficiency_values))
    ):
        if min(recall_values) >= 0.5:
            return (
                "dev-chain-supported",
                "All CDL-A/C/D profile cells ran with finite channel NMSE and at least half of dominant delay-angle FFT bins recovered in every aggregated cell.",
            )
        if min(efficiency_values) >= 0.9:
            return (
                "energy-supported-exact-bin-weak",
                "All cells recover at least 90% of the clean oracle top-k energy, but exact bin overlap remains weak where the requested support budget exceeds the resolvable CDL sparsity; retain exact recall as a limitation rather than promoting E1 to final physical-path evidence.",
            )
        return (
            "executable-but-weak-support",
            "All CDL-A/C/D profile cells ran with finite metrics, but the dominant-bin recall is weak in at least one cell; E1 needs stronger estimator tuning before paper use.",
        )
    return (
        "failed-metric-gate",
        "At least one CDL profile cell produced non-finite metrics; inspect sample rows before scaling E1.",
    )


def write_evaluation_summary(
    output_dir: Path,
    *,
    claim_update: str,
    interpretation: str,
    metrics: dict[str, float | str],
) -> Path:
    lines = [
        "# Sionna CDL Profile Generalization Evaluation Summary",
        "",
        "## Outcome Summary",
        "",
        (
            "This E1 run validates the open-source Sionna CDL-A/C/D channel path and a "
            f"delay-angle FFT sparse-recovery schema with {int(metrics['seed_count'])} seeds "
            f"and {int(metrics['samples_per_profile_seed'])} samples per profile and seed."
        ),
        "",
        "The run records CIR-grounded delay RMSE in nanoseconds and effective projected ULA broadside-angle RMSE in degrees. It remains a grid FFT top-k baseline, not the full trained estimator result.",
        "",
        "## evaluation_summary",
        "",
        "- `research_question`: Can the Sionna CDL-A/C/D channel generator feed a reproducible Tensor-OMP-style delay-angle sparse recovery evaluation across SNR and sparsity budgets?",
        f"- `claim_update`: {claim_update}",
        "- `baseline_relation`: The comparator is a grid FFT top-k Tensor-OMP proxy applied to the same noisy CDL frequency-response tensor as the clean-channel target.",
        (
            "- `failure_mode`: Exact-bin support is weak in over-budgeted low-SNR CDL-D "
            "cells even when oracle top-k energy efficiency remains high; the physical "
            "metrics are cluster-effective ULA quantities rather than separate AoD/ZoD."
        ),
        f"- `mechanism_note`: {interpretation}",
        "- `next_action`: Attach the full trained estimator and compare its CIR-grounded delay/projected-angle RMSE against this grid baseline before promoting E1.",
        "- `paper_role`: E1 supporting external-channel robustness and limitation evidence.",
        "- `section_id`: 06_experiments; 07_limitations.",
        "- `item_id`: E8.",
        "- `claim_links`: C4.",
        "- `main_or_appendix`: Appendix/supporting until the trained estimator is evaluated with the same physical metrics.",
        (
            "- `evidence_level`: E1 scaled supporting evidence."
            if float(metrics["seed_count"]) >= 5
            and float(metrics["samples_per_profile_seed"]) >= 50
            else "- `evidence_level`: E1 auxiliary/dev chain validation."
        ),
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
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--output-dir-name", default="sionna_cdl_profile_generalization")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    started = time.perf_counter()
    rows: list[dict[str, float | str]] = []
    sample_rows: list[dict[str, float | str]] = []

    for profile in args.profiles:
        for seed in args.seeds:
            seed_all(seed)
            torch.manual_seed(seed)
            sionna_config.seed = seed
            rng = np.random.default_rng(seed + 1000 * (ord(profile[0]) - ord("A") + 1))
            (
                clean_batch,
                physical_delays_batch,
                projected_spatial_frequency_batch,
                physical_path_power_batch,
            ) = generate_profile_channels(
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
                noisy_batch = []
                noise_vars = []
                for clean in clean_batch:
                    noisy, noise_variance = add_awgn(clean, snr_db=snr_db, rng=rng)
                    noisy_batch.append(noisy)
                    noise_vars.append(noise_variance)
                for l_value in args.l_values:
                    nmse_values: list[float] = []
                    recall_values: list[float] = []
                    energy_values: list[float] = []
                    topk_efficiency_values: list[float] = []
                    clean_topk_fraction_values: list[float] = []
                    effective_95_values: list[float] = []
                    effective_99_values: list[float] = []
                    delay_recall_values: list[float] = []
                    angle_recall_values: list[float] = []
                    delay_values: list[float] = []
                    angle_values: list[float] = []
                    physical_delay_values: list[float] = []
                    projected_angle_values: list[float] = []
                    matched_path_values: list[float] = []
                    clean_grid_delay_values: list[float] = []
                    clean_grid_angle_values: list[float] = []
                    for sample_index, (clean, noisy, noise_variance) in enumerate(
                        zip(clean_batch, noisy_batch, noise_vars)
                    ):
                        estimate, est_support, _ = reconstruct_fft_topk(noisy, l_value)
                        sample_nmse = nmse_db(estimate, clean)
                        support = support_metrics(clean, est_support, l_value)
                        physical = physical_path_metrics(
                            est_support=est_support,
                            shape=clean.shape,
                            truth_delays_s=physical_delays_batch[sample_index],
                            truth_spatial_frequencies=(
                                projected_spatial_frequency_batch[sample_index]
                            ),
                            truth_path_powers=physical_path_power_batch[sample_index],
                            subcarrier_spacing_hz=args.subcarrier_spacing_hz,
                        )
                        clean_spectrum = np.fft.fftn(clean, norm="ortho")
                        clean_support = topk_support(clean_spectrum, l_value)
                        clean_grid_physical = physical_path_metrics(
                            est_support=clean_support,
                            shape=clean.shape,
                            truth_delays_s=physical_delays_batch[sample_index],
                            truth_spatial_frequencies=(
                                projected_spatial_frequency_batch[sample_index]
                            ),
                            truth_path_powers=physical_path_power_batch[sample_index],
                            subcarrier_spacing_hz=args.subcarrier_spacing_hz,
                        )
                        nmse_values.append(sample_nmse)
                        recall_values.append(support["support_recall"])
                        energy_values.append(support["dominant_energy_recall"])
                        topk_efficiency_values.append(support["topk_energy_efficiency"])
                        clean_topk_fraction_values.append(support["clean_topk_energy_fraction"])
                        effective_95_values.append(support["effective_support_95"])
                        effective_99_values.append(support["effective_support_99"])
                        delay_recall_values.append(support["delay_support_recall"])
                        angle_recall_values.append(support["angle_support_recall"])
                        delay_values.append(support["delay_bin_rmse"])
                        angle_values.append(support["angle_bin_rmse"])
                        physical_delay_values.append(physical["physical_delay_rmse_ns"])
                        projected_angle_values.append(
                            physical["projected_broadside_angle_rmse_deg"]
                        )
                        matched_path_values.append(physical["matched_physical_paths"])
                        clean_grid_delay_values.append(
                            clean_grid_physical["physical_delay_rmse_ns"]
                        )
                        clean_grid_angle_values.append(
                            clean_grid_physical[
                                "projected_broadside_angle_rmse_deg"
                            ]
                        )
                        sample_rows.append(
                            {
                                "profile": profile,
                                "seed": float(seed),
                                "sample_index": float(sample_index),
                                "snr_db": float(snr_db),
                                "l_value": float(l_value),
                                "channel_nmse_db": sample_nmse,
                                "support_recall": support["support_recall"],
                                "dominant_energy_recall": support["dominant_energy_recall"],
                                "topk_energy_efficiency": support["topk_energy_efficiency"],
                                "clean_topk_energy_fraction": support["clean_topk_energy_fraction"],
                                "effective_support_95": support["effective_support_95"],
                                "effective_support_99": support["effective_support_99"],
                                "delay_support_recall": support["delay_support_recall"],
                                "angle_support_recall": support["angle_support_recall"],
                                "delay_bin_rmse": support["delay_bin_rmse"],
                                "angle_bin_rmse": support["angle_bin_rmse"],
                                "physical_delay_rmse_ns": physical[
                                    "physical_delay_rmse_ns"
                                ],
                                "projected_broadside_angle_rmse_deg": physical[
                                    "projected_broadside_angle_rmse_deg"
                                ],
                                "matched_physical_paths": physical[
                                    "matched_physical_paths"
                                ],
                                "clean_grid_physical_delay_rmse_ns": (
                                    clean_grid_physical["physical_delay_rmse_ns"]
                                ),
                                "clean_grid_projected_broadside_angle_rmse_deg": (
                                    clean_grid_physical[
                                        "projected_broadside_angle_rmse_deg"
                                    ]
                                ),
                                "physical_delay_rmse_gap_vs_clean_grid_ns": (
                                    physical["physical_delay_rmse_ns"]
                                    - clean_grid_physical["physical_delay_rmse_ns"]
                                ),
                                "projected_angle_rmse_gap_vs_clean_grid_deg": (
                                    physical["projected_broadside_angle_rmse_deg"]
                                    - clean_grid_physical[
                                        "projected_broadside_angle_rmse_deg"
                                    ]
                                ),
                                "physical_truth_path_count": float(
                                    len(physical_delays_batch[sample_index])
                                ),
                                "noise_variance": float(noise_variance),
                            }
                        )
                    rows.append(
                        {
                            "profile": profile,
                            "seed": float(seed),
                            "snr_db": float(snr_db),
                            "l_value": float(l_value),
                            "n_samples": float(args.samples_per_profile_seed),
                            "mean_channel_nmse_db": finite_mean(nmse_values),
                            "mean_support_recall": finite_mean(recall_values),
                            "mean_dominant_energy_recall": finite_mean(energy_values),
                            "mean_topk_energy_efficiency": finite_mean(topk_efficiency_values),
                            "mean_clean_topk_energy_fraction": finite_mean(clean_topk_fraction_values),
                            "mean_effective_support_95": finite_mean(effective_95_values),
                            "mean_effective_support_99": finite_mean(effective_99_values),
                            "mean_delay_support_recall": finite_mean(delay_recall_values),
                            "mean_angle_support_recall": finite_mean(angle_recall_values),
                            "mean_delay_bin_rmse": finite_mean(delay_values),
                            "mean_angle_bin_rmse": finite_mean(angle_values),
                            "mean_physical_delay_rmse_ns": finite_mean(
                                physical_delay_values
                            ),
                            "mean_projected_broadside_angle_rmse_deg": finite_mean(
                                projected_angle_values
                            ),
                            "mean_matched_physical_paths": finite_mean(
                                matched_path_values
                            ),
                            "mean_clean_grid_physical_delay_rmse_ns": finite_mean(
                                clean_grid_delay_values
                            ),
                            "mean_clean_grid_projected_broadside_angle_rmse_deg": finite_mean(
                                clean_grid_angle_values
                            ),
                            "mean_physical_delay_rmse_gap_vs_clean_grid_ns": finite_mean(
                                [
                                    estimate - clean
                                    for estimate, clean in zip(
                                        physical_delay_values,
                                        clean_grid_delay_values,
                                    )
                                ]
                            ),
                            "mean_projected_angle_rmse_gap_vs_clean_grid_deg": finite_mean(
                                [
                                    estimate - clean
                                    for estimate, clean in zip(
                                        projected_angle_values,
                                        clean_grid_angle_values,
                                    )
                                ]
                            ),
                        }
                    )

    elapsed_seconds = time.perf_counter() - started
    claim_update, interpretation = verdict(rows)
    high_snr_rows = [row for row in rows if float(row["snr_db"]) >= 20.0]
    metrics = {
        "claim_update": claim_update,
        "physical_metric_status": "cir-grounded-grid-baseline-and-clean-floor-recorded",
        "profiles": ",".join(args.profiles),
        "snrs_db": ",".join(str(value) for value in args.snrs),
        "l_values": ",".join(str(value) for value in args.l_values),
        "seed_count": float(len(args.seeds)),
        "samples_per_profile_seed": float(args.samples_per_profile_seed),
        "row_count": float(len(rows)),
        "sample_row_count": float(len(sample_rows)),
        "min_mean_support_recall": min(float(row["mean_support_recall"]) for row in rows),
        "mean_channel_nmse_db_all": finite_mean([float(row["mean_channel_nmse_db"]) for row in rows]),
        "best_mean_channel_nmse_db": min(float(row["mean_channel_nmse_db"]) for row in rows),
        "worst_mean_channel_nmse_db": max(float(row["mean_channel_nmse_db"]) for row in rows),
        "mean_dominant_energy_recall_all": finite_mean(
            [float(row["mean_dominant_energy_recall"]) for row in rows]
        ),
        "min_mean_topk_energy_efficiency": min(
            float(row["mean_topk_energy_efficiency"]) for row in rows
        ),
        "mean_topk_energy_efficiency_all": finite_mean(
            [float(row["mean_topk_energy_efficiency"]) for row in rows]
        ),
        "min_mean_delay_support_recall": min(
            float(row["mean_delay_support_recall"]) for row in rows
        ),
        "min_mean_angle_support_recall": min(
            float(row["mean_angle_support_recall"]) for row in rows
        ),
        "mean_effective_support_95_all": finite_mean(
            [float(row["mean_effective_support_95"]) for row in rows]
        ),
        "mean_effective_support_99_all": finite_mean(
            [float(row["mean_effective_support_99"]) for row in rows]
        ),
        "mean_physical_delay_rmse_ns_all": finite_mean(
            [float(row["mean_physical_delay_rmse_ns"]) for row in rows]
        ),
        "mean_projected_broadside_angle_rmse_deg_all": finite_mean(
            [
                float(row["mean_projected_broadside_angle_rmse_deg"])
                for row in rows
            ]
        ),
        "mean_physical_delay_rmse_ns_snr_ge_20": finite_mean(
            [float(row["mean_physical_delay_rmse_ns"]) for row in high_snr_rows]
        ),
        "mean_projected_broadside_angle_rmse_deg_snr_ge_20": finite_mean(
            [
                float(row["mean_projected_broadside_angle_rmse_deg"])
                for row in high_snr_rows
            ]
        ),
        "mean_clean_grid_physical_delay_rmse_ns_all": finite_mean(
            [float(row["mean_clean_grid_physical_delay_rmse_ns"]) for row in rows]
        ),
        "mean_clean_grid_projected_broadside_angle_rmse_deg_all": finite_mean(
            [
                float(row["mean_clean_grid_projected_broadside_angle_rmse_deg"])
                for row in rows
            ]
        ),
        "mean_physical_delay_rmse_gap_vs_clean_grid_ns_all": finite_mean(
            [
                float(row["mean_physical_delay_rmse_gap_vs_clean_grid_ns"])
                for row in rows
            ]
        ),
        "mean_projected_angle_rmse_gap_vs_clean_grid_deg_all": finite_mean(
            [
                float(row["mean_projected_angle_rmse_gap_vs_clean_grid_deg"])
                for row in rows
            ]
        ),
        "max_mean_physical_delay_rmse_ns": max(
            float(row["mean_physical_delay_rmse_ns"]) for row in rows
        ),
        "max_mean_projected_broadside_angle_rmse_deg": max(
            float(row["mean_projected_broadside_angle_rmse_deg"])
            for row in rows
        ),
        "delay_resolution_ns": 1e9
        / (args.num_subcarriers * args.subcarrier_spacing_hz),
        "projected_angle_definition": (
            "effective ULA broadside angle from oversampled clean per-cluster CIR; "
            "endfire alias handled in spatial-frequency matching"
        ),
        "elapsed_seconds": elapsed_seconds,
    }

    output_dir = ROOT / "05_results" / args.output_dir_name
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_csv = output_dir / "sionna_cdl_profile_generalization.csv"
    with summary_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    samples_csv = output_dir / "sionna_cdl_profile_generalization_samples.csv"
    with samples_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(sample_rows[0].keys()))
        writer.writeheader()
        writer.writerows(sample_rows)

    manifest = {
        "run_id": (
            f"sionna_cdl_profile_generalization_dev_"
            f"{len(args.seeds)}x{args.samples_per_profile_seed}_"
            f"n{args.num_subcarriers}_m{args.num_tx_antennas}_physical"
        ),
        "command": subprocess.list2cmdline(
            [
                sys.executable,
                str(Path(__file__).resolve().relative_to(ROOT)),
                *sys.argv[1:],
            ]
        ),
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
            "device": args.device,
        },
        "metrics": metrics,
        "environment": environment_snapshot(ROOT),
        "notes": [
            "Auxiliary/dev E1 run: validates Sionna CDL-A/C/D -> noisy frequency response -> FFT top-k Tensor-OMP proxy metrics.",
            "Physical delay truth comes directly from Sionna CIR tau; effective projected broadside angle truth comes from an oversampled clean per-cluster CIR antenna response.",
            "The projected broadside metric is the identifiable 1-D ULA angle, not separate azimuth/zenith AoD.",
            "Exact support recall is retained; top-k energy efficiency and axis-specific recall diagnose over-budgeted or unresolved support cells without replacing the canonical metric.",
            "The manifest records whether the selected seed/sample configuration reaches the planned five-seed x 50-sample E1 scale.",
        ],
    }
    manifest_path = output_dir / "run_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    evaluation_path = write_evaluation_summary(
        output_dir,
        claim_update=claim_update,
        interpretation=interpretation,
        metrics=metrics,
    )
    lines = [
        "# Sionna CDL Profile Generalization",
        "",
        f"- Claim update: `{claim_update}`",
        f"- Profiles: `{metrics['profiles']}`",
        f"- SNRs: `{metrics['snrs_db']}` dB",
        f"- L values: `{metrics['l_values']}`",
        f"- Aggregated rows: `{len(rows)}`",
        f"- Sample rows: `{len(sample_rows)}`",
        f"- Minimum mean support recall: `{metrics['min_mean_support_recall']:.6g}`",
        f"- Mean channel NMSE across cells: `{metrics['mean_channel_nmse_db_all']:.6g}` dB",
        f"- Mean dominant energy recall: `{metrics['mean_dominant_energy_recall_all']:.6g}`",
        f"- Minimum mean top-k energy efficiency: `{metrics['min_mean_topk_energy_efficiency']:.6g}`",
        f"- Minimum mean delay support recall: `{metrics['min_mean_delay_support_recall']:.6g}`",
        f"- Minimum mean angle support recall: `{metrics['min_mean_angle_support_recall']:.6g}`",
        f"- Mean effective 95% / 99% support size: `{metrics['mean_effective_support_95_all']:.6g}` / `{metrics['mean_effective_support_99_all']:.6g}`",
        f"- Mean physical delay RMSE: `{metrics['mean_physical_delay_rmse_ns_all']:.6g}` ns",
        f"- Mean projected broadside-angle RMSE: `{metrics['mean_projected_broadside_angle_rmse_deg_all']:.6g}` deg",
        f"- SNR>=20 dB physical delay / projected-angle RMSE: `{metrics['mean_physical_delay_rmse_ns_snr_ge_20']:.6g}` ns / `{metrics['mean_projected_broadside_angle_rmse_deg_snr_ge_20']:.6g}` deg",
        f"- Clean-grid physical delay / projected-angle RMSE floor: `{metrics['mean_clean_grid_physical_delay_rmse_ns_all']:.6g}` ns / `{metrics['mean_clean_grid_projected_broadside_angle_rmse_deg_all']:.6g}` deg",
        f"- Noisy physical RMSE gap vs clean-grid floor: `{metrics['mean_physical_delay_rmse_gap_vs_clean_grid_ns_all']:.6g}` ns / `{metrics['mean_projected_angle_rmse_gap_vs_clean_grid_deg_all']:.6g}` deg",
        f"- Elapsed seconds: `{elapsed_seconds:.2f}`",
        "",
        "## Interpretation",
        "",
        interpretation,
        "",
        "This is a CIR-grounded physical-metric grid baseline, not final paper-facing trained-estimator E1 evidence. Delay is measured against Sionna tau; angle is the effective projected broadside quantity identifiable by the 1-D half-wavelength ULA.",
        "",
        "## Artifacts",
        "",
        f"- `{summary_csv.relative_to(ROOT)}`",
        f"- `{samples_csv.relative_to(ROOT)}`",
        f"- `{manifest_path.relative_to(ROOT)}`",
        f"- `{evaluation_path.relative_to(ROOT)}`",
    ]
    summary_path = output_dir / "summary.md"
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {summary_csv.relative_to(ROOT)}")
    print(f"Wrote {samples_csv.relative_to(ROOT)}")
    print(f"Wrote {summary_path.relative_to(ROOT)}")
    print(f"Wrote {manifest_path.relative_to(ROOT)}")
    print(f"Wrote {evaluation_path.relative_to(ROOT)}")
    print(f"claim_update={claim_update}")
    print(f"min_mean_support_recall={metrics['min_mean_support_recall']:.4f}")
    print(f"mean_channel_nmse_db_all={metrics['mean_channel_nmse_db_all']:.4f}")


if __name__ == "__main__":
    main()
