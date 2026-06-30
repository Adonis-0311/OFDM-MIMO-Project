from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
from itertools import product
from scipy.io import loadmat
from scipy.optimize import linear_sum_assignment

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_active_modules"))

from common.manifest import environment_snapshot
from common.seed import seed_all

DATASET_ROOT = (
    ROOT
    / "90_archive"
    / "2025_thesis_materials"
    / "参考"
    / "DeepMIMO-5GNR"
    / "DeepMIMO_dataset"
    / "o1_60"
)

SOURCE_ALPHA_CSV = (
    ROOT
    / "05_results"
    / "stage2_torch_locked_scale_g2_seed_sweep"
    / "stage2_torch_locked_scale_g2_seed_sweep_seeds.csv"
)


def finite_mean(values: list[float]) -> float:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    return float(np.mean(arr)) if arr.size else float("nan")


def load_source_alpha(path: Path = SOURCE_ALPHA_CSV) -> tuple[float, str]:
    alphas: list[float] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            alphas.append(float(row["alpha"]))
    if not alphas:
        raise ValueError(f"No source alpha values found in {path}.")
    return finite_mean(alphas), str(path.relative_to(ROOT))


def mat_key(kind: str) -> str:
    if kind in {"aoa_az", "aoa_el", "aod_az", "aod_el", "rx_pos", "tx_pos"}:
        return kind
    return kind.split("_")[0]


def load_rows(kind: str, tx_tag: str, rx_tag: str, user_indices: np.ndarray) -> np.ndarray:
    path = DATASET_ROOT / f"{kind}_{tx_tag}_tx000_{rx_tag}.mat"
    data = loadmat(path, squeeze_me=True)[mat_key(kind)]
    if data.ndim == 1:
        return np.asarray(data)[None, :]
    return np.asarray(data[user_indices])


def choose_user_indices(*, n_total: int, n_users: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    if n_users >= n_total:
        return np.arange(n_total)
    # Mix deterministic spatial coverage with a seeded shuffle, avoiding only
    # contiguous sidewalk slices from the O1 receiver grid.
    grid = np.linspace(0, n_total - 1, n_users * 4, dtype=int)
    rng.shuffle(grid)
    return np.sort(np.unique(grid[:n_users]))


def build_channels(
    *,
    tx_tags: list[str],
    rx_tag: str,
    user_indices: np.ndarray,
    num_subcarriers: int,
    subcarrier_spacing_hz: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    frequencies = (
        np.arange(num_subcarriers, dtype=float) - (num_subcarriers - 1) / 2.0
    ) * subcarrier_spacing_hz
    channels = np.zeros((len(user_indices), num_subcarriers, len(tx_tags)), dtype=np.complex128)
    delay_truth = np.full((len(user_indices), len(tx_tags)), np.nan, dtype=float)
    power_truth = np.full((len(user_indices), len(tx_tags)), np.nan, dtype=float)
    for tx_index, tx_tag in enumerate(tx_tags):
        delay = load_rows("delay", tx_tag, rx_tag, user_indices).astype(float)
        power_db = load_rows("power", tx_tag, rx_tag, user_indices).astype(float)
        phase_deg = load_rows("phase", tx_tag, rx_tag, user_indices).astype(float)
        finite = np.isfinite(delay) & np.isfinite(power_db) & np.isfinite(phase_deg)
        amplitude = np.zeros_like(power_db, dtype=float)
        phase = np.zeros_like(phase_deg, dtype=float)
        delay_safe = np.zeros_like(delay, dtype=float)
        amplitude[finite] = 10.0 ** (power_db[finite] / 20.0)
        phase[finite] = np.deg2rad(phase_deg[finite])
        delay_safe[finite] = delay[finite]
        phasor = amplitude * np.exp(1j * phase)
        response = np.sum(
            phasor[:, None, :]
            * np.exp(-2j * np.pi * frequencies[None, :, None] * delay_safe[:, None, :]),
            axis=2,
        )
        channels[:, :, tx_index] = response
        for row_index in range(delay.shape[0]):
            valid = np.flatnonzero(finite[row_index])
            if valid.size:
                best = valid[np.argmax(power_db[row_index, valid])]
                delay_truth[row_index, tx_index] = delay[row_index, best]
                power_truth[row_index, tx_index] = power_db[row_index, best]

    norms = np.sqrt(np.mean(np.abs(channels) ** 2, axis=(1, 2), keepdims=True))
    channels = channels / np.maximum(norms, 1e-300)
    return channels, delay_truth, power_truth


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


def reconstruct_fft_topk(measurement: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
    spectrum = np.fft.fftn(measurement, axes=(0, 1), norm="ortho")
    support = topk_support(spectrum, k)
    estimate_spectrum = np.zeros_like(spectrum.reshape(-1))
    estimate_spectrum[support] = spectrum.reshape(-1)[support]
    estimate_spectrum = estimate_spectrum.reshape(spectrum.shape)
    estimate = np.fft.ifftn(estimate_spectrum, axes=(0, 1), norm="ortho")
    return estimate, support


def steering_axis(n: int, frequency_bin: float) -> np.ndarray:
    idx = np.arange(n, dtype=float)
    return np.exp(2j * np.pi * idx * frequency_bin / n) / np.sqrt(n)


def atom_2d(shape: tuple[int, int], bins: tuple[float, float]) -> np.ndarray:
    delay = steering_axis(shape[0], bins[0])
    tx = steering_axis(shape[1], bins[1])
    return delay[:, None] * tx[None, :]


def support_to_bins(support: np.ndarray, shape: tuple[int, int]) -> list[tuple[int, int]]:
    return [tuple(int(value) for value in np.unravel_index(int(index), shape)) for index in support]


def estimate_from_bins_lstsq(measurement: np.ndarray, bins: list[tuple[float, float]]) -> np.ndarray:
    if not bins:
        return np.zeros_like(measurement)
    atoms = [atom_2d(measurement.shape, bin_pair).reshape(-1) for bin_pair in bins]
    design = np.stack(atoms, axis=1)
    coeffs, *_ = np.linalg.lstsq(design, measurement.reshape(-1), rcond=None)
    return (design @ coeffs).reshape(measurement.shape)


def refine_bins_local(
    measurement: np.ndarray,
    coarse_bins: list[tuple[int, int]],
    *,
    search_radius: float,
    search_points: int,
) -> list[tuple[float, float]]:
    offsets = np.linspace(-search_radius, search_radius, search_points)
    refined: list[tuple[float, float]] = []
    for coarse in coarse_bins:
        best_score = -np.inf
        best_bins = tuple(float(value) for value in coarse)
        for delta in product(offsets, repeat=2):
            candidate = tuple(float(base + step) for base, step in zip(coarse, delta))
            atom = atom_2d(measurement.shape, candidate)
            score = float(np.abs(np.vdot(atom, measurement)) ** 2)
            if score > best_score:
                best_score = score
                best_bins = candidate
        refined.append(best_bins)
    return refined


def bounded_refinement_estimate(
    measurement: np.ndarray,
    support: np.ndarray,
    *,
    search_radius: float,
    search_points: int,
) -> tuple[np.ndarray, list[tuple[int, int]], list[tuple[float, float]]]:
    coarse_bins = support_to_bins(support, measurement.shape)
    refined_bins = refine_bins_local(
        measurement,
        coarse_bins,
        search_radius=search_radius,
        search_points=search_points,
    )
    return estimate_from_bins_lstsq(measurement, refined_bins), coarse_bins, refined_bins


def interpolate_bins(
    coarse_bins: list[tuple[int, int]],
    refined_bins: list[tuple[float, float]],
    alpha: float,
) -> list[tuple[float, float]]:
    return [
        tuple(float(c + alpha * (r - c)) for c, r in zip(coarse, refined))
        for coarse, refined in zip(coarse_bins, refined_bins)
    ]


def alpha_refinement_estimate(
    measurement: np.ndarray,
    support: np.ndarray,
    *,
    alpha: float,
    search_radius: float,
    search_points: int,
) -> tuple[np.ndarray, list[tuple[int, int]], list[tuple[float, float]]]:
    coarse_bins = support_to_bins(support, measurement.shape)
    refined_bins = refine_bins_local(
        measurement,
        coarse_bins,
        search_radius=search_radius,
        search_points=search_points,
    )
    alpha_bins = interpolate_bins(coarse_bins, refined_bins, alpha)
    return estimate_from_bins_lstsq(measurement, alpha_bins), coarse_bins, refined_bins


def estimate_from_prepared_alpha(
    measurement: np.ndarray,
    coarse_bins: list[tuple[int, int]],
    refined_bins: list[tuple[float, float]],
    *,
    alpha: float,
) -> np.ndarray:
    alpha_bins = interpolate_bins(coarse_bins, refined_bins, alpha)
    return estimate_from_bins_lstsq(measurement, alpha_bins)


def oracle_alpha_nmse(
    *,
    measurement: np.ndarray,
    clean: np.ndarray,
    coarse_bins: list[tuple[int, int]],
    refined_bins: list[tuple[float, float]],
    candidate_alphas: list[float],
) -> tuple[float, float]:
    best_alpha = candidate_alphas[0]
    best_nmse = float("inf")
    for alpha in candidate_alphas:
        estimate = estimate_from_prepared_alpha(
            measurement,
            coarse_bins,
            refined_bins,
            alpha=alpha,
        )
        value = nmse_db(estimate, clean)
        if value < best_nmse:
            best_alpha = alpha
            best_nmse = value
    return best_nmse, best_alpha


def nmse_db(estimate: np.ndarray, clean: np.ndarray) -> float:
    denom = float(np.linalg.norm(clean) ** 2)
    nmse = float(np.linalg.norm(estimate - clean) ** 2 / max(denom, 1e-300))
    return 10.0 * np.log10(max(nmse, 1e-300))


def unravel_bins(flat_support: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    return np.asarray([np.unravel_index(int(index), shape) for index in flat_support], dtype=float)


def circular_delta(a: np.ndarray, b: np.ndarray, period: int) -> np.ndarray:
    delta = np.abs(a - b)
    return np.minimum(delta, period - delta)


def bin_rmse(true_support: np.ndarray, est_support: np.ndarray, shape: tuple[int, int]) -> tuple[float, float]:
    true_bins = unravel_bins(true_support, shape)
    est_bins = unravel_bins(est_support, shape)
    cost = (
        circular_delta(true_bins[:, None, 0], est_bins[None, :, 0], shape[0]) ** 2
        + circular_delta(true_bins[:, None, 1], est_bins[None, :, 1], shape[1]) ** 2
    )
    row_ind, col_ind = linear_sum_assignment(cost)
    delay_errors = circular_delta(true_bins[row_ind, 0], est_bins[col_ind, 0], shape[0])
    tx_errors = circular_delta(true_bins[row_ind, 1], est_bins[col_ind, 1], shape[1])
    return float(np.sqrt(np.mean(delay_errors**2))), float(np.sqrt(np.mean(tx_errors**2)))


def support_metrics(clean: np.ndarray, est_support: np.ndarray, k: int) -> dict[str, float]:
    spectrum = np.fft.fftn(clean, axes=(0, 1), norm="ortho")
    true_support = topk_support(spectrum, k)
    true_set = set(int(item) for item in true_support)
    est_set = set(int(item) for item in est_support)
    recall = len(true_set & est_set) / max(len(true_set), 1)
    flat = spectrum.reshape(-1)
    captured = float(np.sum(np.abs(flat[list(est_set)]) ** 2))
    total = float(np.sum(np.abs(flat) ** 2))
    delay_rmse, tx_bin_rmse = bin_rmse(true_support, est_support, clean.shape)
    return {
        "support_recall": float(recall),
        "dominant_energy_recall": captured / max(total, 1e-300),
        "delay_bin_rmse": delay_rmse,
        "tx_bin_rmse": tx_bin_rmse,
    }


def verdict(rows: list[dict[str, float | str]]) -> tuple[str, str, str]:
    nmse_values = [float(row["mean_grid_channel_nmse_db"]) for row in rows]
    source_nmse_values = [float(row["mean_source_alpha_channel_nmse_db"]) for row in rows]
    source_gain_values = [float(row["mean_source_alpha_gain_vs_grid_db"]) for row in rows]
    recall_values = [float(row["mean_support_recall"]) for row in rows]
    if not (
        all(np.isfinite(nmse_values))
        and all(np.isfinite(source_nmse_values))
        and all(np.isfinite(source_gain_values))
        and all(np.isfinite(recall_values))
    ):
        return (
            "failed-metric-gate",
            "fail",
            "At least one DeepMIMO O1_60 evaluation cell produced non-finite metrics.",
        )
    if finite_mean(source_gain_values) > 0.0 and min(recall_values) >= 0.5:
        return (
            "dev-source-alpha-transfer-supported",
            "weak",
            "The source-trained G2 alpha transfer proxy produced finite O1_60 metrics with positive mean gain and acceptable dominant-bin recall in this dev grid.",
        )
    if finite_mean(source_gain_values) > 0.0:
        return (
            "partial-source-alpha-transfer",
            "partial",
            "The source-trained G2 alpha improves mean O1_60 NMSE, but at least one cell has weak dominant-bin recall.",
        )
    return (
        "source-alpha-transfer-fails",
        "fail",
        "The source-trained G2 alpha does not improve mean O1_60 NMSE over grid FFT top-k in this dev grid.",
    )


def write_evaluation_summary(
    output_dir: Path,
    *,
    metrics: dict[str, float | str],
    interpretation: str,
) -> Path:
    lines = [
        "# DeepMIMO O1_60 G2 Evaluation Summary",
        "",
        "## Outcome Summary",
        "",
        "This E2 dev-run reads local DeepMIMO O1_60 raw ray files, synthesizes normalized OFDM frequency responses, adds AWGN, and evaluates grid FFT top-k, Stage-2 source-trained alpha transfer, full bounded refinement, and oracle-alpha diagnostics on the same clean/noisy channel tensors.",
        "",
        "It is not yet the full Sensors E2 result: this run uses a raw MAT loader and delay/TX-bin proxy metrics, and transfers only the scalar Stage-2 alpha path rather than a full trained T-OMP-Net.",
        "",
        "## evaluation_summary",
        "",
        "- `research_question`: Can O1_60 ray-traced data be converted into reproducible OFDM channel tensors and evaluated with the existing Tensor-OMP-style metric contract?",
        f"- `claim_update`: {metrics['claim_update']}",
        f"- `transfer_proxy_classification`: {metrics['transfer_proxy_classification']}",
        f"- `source_alpha`: {metrics['source_alpha']}",
        "- `baseline_relation`: Stage-2 source-trained alpha is compared against grid FFT top-k on the same noisy O1_60 synthesized channel tensor; full bounded refinement and oracle-alpha are diagnostic comparators.",
        "- `failure_mode`: None if executable; limitation is raw-loader proxy metrics and small dev sample size.",
        f"- `mechanism_note`: {interpretation}",
        "- `next_action`: Attach the full trained G2/T-OMP-Net path and scale to 5 seeds x 100 users x SNR {0,10,20,30}.",
        "- `evidence_level`: E2 auxiliary/dev raw-loader and scalar source-alpha transfer validation.",
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
    parser.add_argument("--tx-tags", nargs="+", default=[f"t{i:03d}" for i in range(3, 11)])
    parser.add_argument("--rx-tag", default="r000")
    parser.add_argument("--snrs", nargs="+", type=float, default=[0.0, 10.0, 20.0, 30.0])
    parser.add_argument("--l-values", nargs="+", type=int, default=[4, 8, 16])
    parser.add_argument("--n-users", type=int, default=16)
    parser.add_argument("--seed", type=int, default=20260626)
    parser.add_argument("--num-subcarriers", type=int, default=64)
    parser.add_argument("--subcarrier-spacing-hz", type=float, default=120e3)
    parser.add_argument("--search-radius", type=float, default=0.45)
    parser.add_argument("--search-points", type=int, default=5)
    parser.add_argument("--candidate-alphas", nargs="+", type=float, default=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2])
    parser.add_argument("--output-dir-name", default="deepmimo_o1_60_g2")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    started = time.perf_counter()
    seed_all(args.seed)
    source_alpha, source_alpha_path = load_source_alpha()
    user_indices = choose_user_indices(n_total=497931, n_users=args.n_users, seed=args.seed)
    rx_pos = load_rows("rx_pos", args.tx_tags[0], args.rx_tag, user_indices).astype(float)
    clean_batch, delay_truth, power_truth = build_channels(
        tx_tags=args.tx_tags,
        rx_tag=args.rx_tag,
        user_indices=user_indices,
        num_subcarriers=args.num_subcarriers,
        subcarrier_spacing_hz=args.subcarrier_spacing_hz,
    )
    rows: list[dict[str, float | str]] = []
    sample_rows: list[dict[str, float | str]] = []
    rng = np.random.default_rng(args.seed + 17)
    for snr_db in args.snrs:
        noisy_batch: list[np.ndarray] = []
        noise_vars: list[float] = []
        for clean in clean_batch:
            noisy, noise_variance = add_awgn(clean, snr_db=snr_db, rng=rng)
            noisy_batch.append(noisy)
            noise_vars.append(noise_variance)
        for l_value in args.l_values:
            grid_nmse_values: list[float] = []
            source_nmse_values: list[float] = []
            source_gain_values: list[float] = []
            bounded_nmse_values: list[float] = []
            bounded_gain_values: list[float] = []
            oracle_nmse_values: list[float] = []
            oracle_gain_values: list[float] = []
            oracle_gap_values: list[float] = []
            oracle_alpha_values: list[float] = []
            recall_values: list[float] = []
            energy_values: list[float] = []
            delay_values: list[float] = []
            tx_values: list[float] = []
            for sample_index, (clean, noisy, noise_variance) in enumerate(
                zip(clean_batch, noisy_batch, noise_vars)
            ):
                grid_estimate, est_support = reconstruct_fft_topk(noisy, l_value)
                source_estimate, coarse_bins, refined_bins = alpha_refinement_estimate(
                    noisy,
                    est_support,
                    alpha=source_alpha,
                    search_radius=args.search_radius,
                    search_points=args.search_points,
                )
                bounded_estimate = estimate_from_prepared_alpha(
                    noisy,
                    coarse_bins,
                    refined_bins,
                    alpha=1.0,
                )
                oracle_nmse, oracle_alpha = oracle_alpha_nmse(
                    measurement=noisy,
                    clean=clean,
                    coarse_bins=coarse_bins,
                    refined_bins=refined_bins,
                    candidate_alphas=args.candidate_alphas,
                )
                sample_grid_nmse = nmse_db(grid_estimate, clean)
                sample_source_nmse = nmse_db(source_estimate, clean)
                sample_bounded_nmse = nmse_db(bounded_estimate, clean)
                sample_source_gain = sample_grid_nmse - sample_source_nmse
                sample_gain = sample_grid_nmse - sample_bounded_nmse
                support = support_metrics(clean, est_support, l_value)
                grid_nmse_values.append(sample_grid_nmse)
                source_nmse_values.append(sample_source_nmse)
                source_gain_values.append(sample_source_gain)
                bounded_nmse_values.append(sample_bounded_nmse)
                bounded_gain_values.append(sample_gain)
                oracle_nmse_values.append(oracle_nmse)
                oracle_gain_values.append(sample_grid_nmse - oracle_nmse)
                oracle_gap_values.append(sample_source_nmse - oracle_nmse)
                oracle_alpha_values.append(oracle_alpha)
                recall_values.append(support["support_recall"])
                energy_values.append(support["dominant_energy_recall"])
                delay_values.append(support["delay_bin_rmse"])
                tx_values.append(support["tx_bin_rmse"])
                sample_rows.append(
                    {
                        "user_index": float(user_indices[sample_index]),
                        "sample_index": float(sample_index),
                        "snr_db": float(snr_db),
                        "l_value": float(l_value),
                        "grid_channel_nmse_db": sample_grid_nmse,
                        "source_alpha_channel_nmse_db": sample_source_nmse,
                        "source_alpha_gain_vs_grid_db": sample_source_gain,
                        "bounded_refine_channel_nmse_db": sample_bounded_nmse,
                        "bounded_gain_vs_grid_db": sample_gain,
                        "oracle_alpha_channel_nmse_db": oracle_nmse,
                        "oracle_alpha_gain_vs_grid_db": sample_grid_nmse - oracle_nmse,
                        "source_alpha_gap_vs_oracle_db": sample_source_nmse - oracle_nmse,
                        "oracle_alpha": oracle_alpha,
                        "support_recall": support["support_recall"],
                        "dominant_energy_recall": support["dominant_energy_recall"],
                        "delay_bin_rmse": support["delay_bin_rmse"],
                        "tx_bin_rmse": support["tx_bin_rmse"],
                        "noise_variance": float(noise_variance),
                        "rx_x_m": float(rx_pos[sample_index, 0]),
                        "rx_y_m": float(rx_pos[sample_index, 1]),
                        "rx_z_m": float(rx_pos[sample_index, 2]),
                    }
                )
            rows.append(
                {
                    "snr_db": float(snr_db),
                    "l_value": float(l_value),
                    "n_users": float(args.n_users),
                    "n_tx": float(len(args.tx_tags)),
                    "mean_grid_channel_nmse_db": finite_mean(grid_nmse_values),
                    "mean_source_alpha_channel_nmse_db": finite_mean(source_nmse_values),
                    "mean_source_alpha_gain_vs_grid_db": finite_mean(source_gain_values),
                    "mean_bounded_refine_channel_nmse_db": finite_mean(bounded_nmse_values),
                    "mean_bounded_gain_vs_grid_db": finite_mean(bounded_gain_values),
                    "mean_oracle_alpha_channel_nmse_db": finite_mean(oracle_nmse_values),
                    "mean_oracle_alpha_gain_vs_grid_db": finite_mean(oracle_gain_values),
                    "mean_source_alpha_gap_vs_oracle_db": finite_mean(oracle_gap_values),
                    "mean_oracle_alpha": finite_mean(oracle_alpha_values),
                    "mean_support_recall": finite_mean(recall_values),
                    "mean_dominant_energy_recall": finite_mean(energy_values),
                    "mean_delay_bin_rmse": finite_mean(delay_values),
                    "mean_tx_bin_rmse": finite_mean(tx_values),
                }
            )

    elapsed_seconds = time.perf_counter() - started
    claim_update, transfer_proxy_classification, interpretation = verdict(rows)
    metrics = {
        "claim_update": claim_update,
        "transfer_proxy_classification": transfer_proxy_classification,
        "dataset": "DeepMIMO O1_60 raw ray files",
        "rx_tag": args.rx_tag,
        "tx_tags": ",".join(args.tx_tags),
        "source_alpha": source_alpha,
        "source_alpha_source": source_alpha_path,
        "candidate_alphas": ",".join(str(value) for value in args.candidate_alphas),
        "n_users": float(args.n_users),
        "n_tx": float(len(args.tx_tags)),
        "num_subcarriers": float(args.num_subcarriers),
        "snrs_db": ",".join(str(value) for value in args.snrs),
        "l_values": ",".join(str(value) for value in args.l_values),
        "row_count": float(len(rows)),
        "sample_row_count": float(len(sample_rows)),
        "min_mean_support_recall": min(float(row["mean_support_recall"]) for row in rows),
        "mean_grid_channel_nmse_db_all": finite_mean([float(row["mean_grid_channel_nmse_db"]) for row in rows]),
        "mean_source_alpha_channel_nmse_db_all": finite_mean(
            [float(row["mean_source_alpha_channel_nmse_db"]) for row in rows]
        ),
        "mean_source_alpha_gain_vs_grid_db": finite_mean(
            [float(row["mean_source_alpha_gain_vs_grid_db"]) for row in rows]
        ),
        "min_source_alpha_gain_vs_grid_db": min(float(row["mean_source_alpha_gain_vs_grid_db"]) for row in rows),
        "mean_bounded_refine_channel_nmse_db_all": finite_mean(
            [float(row["mean_bounded_refine_channel_nmse_db"]) for row in rows]
        ),
        "mean_bounded_gain_vs_grid_db": finite_mean([float(row["mean_bounded_gain_vs_grid_db"]) for row in rows]),
        "min_bounded_gain_vs_grid_db": min(float(row["mean_bounded_gain_vs_grid_db"]) for row in rows),
        "mean_oracle_alpha_channel_nmse_db_all": finite_mean(
            [float(row["mean_oracle_alpha_channel_nmse_db"]) for row in rows]
        ),
        "mean_oracle_alpha_gain_vs_grid_db": finite_mean(
            [float(row["mean_oracle_alpha_gain_vs_grid_db"]) for row in rows]
        ),
        "mean_source_alpha_gap_vs_oracle_db": finite_mean(
            [float(row["mean_source_alpha_gap_vs_oracle_db"]) for row in rows]
        ),
        "mean_oracle_alpha": finite_mean([float(row["mean_oracle_alpha"]) for row in rows]),
        "best_mean_grid_channel_nmse_db": min(float(row["mean_grid_channel_nmse_db"]) for row in rows),
        "worst_mean_grid_channel_nmse_db": max(float(row["mean_grid_channel_nmse_db"]) for row in rows),
        "mean_dominant_energy_recall_all": finite_mean(
            [float(row["mean_dominant_energy_recall"]) for row in rows]
        ),
        "rx_x_span_m": float(np.nanmax(rx_pos[:, 0]) - np.nanmin(rx_pos[:, 0])),
        "rx_y_span_m": float(np.nanmax(rx_pos[:, 1]) - np.nanmin(rx_pos[:, 1])),
        "finite_delay_truth_fraction": float(np.isfinite(delay_truth).mean()),
        "finite_power_truth_fraction": float(np.isfinite(power_truth).mean()),
        "elapsed_seconds": elapsed_seconds,
    }

    output_dir = ROOT / "05_results" / args.output_dir_name
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_csv = output_dir / "deepmimo_o1_60_g2.csv"
    with summary_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    samples_csv = output_dir / "deepmimo_o1_60_g2_samples.csv"
    with samples_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(sample_rows[0].keys()))
        writer.writeheader()
        writer.writerows(sample_rows)

    manifest = {
        "run_id": f"deepmimo_o1_60_g2_dev_seed_{args.seed}_n{args.n_users}",
        "command": subprocess.list2cmdline(
            [
                sys.executable,
                str(Path(__file__).resolve().relative_to(ROOT)),
                *sys.argv[1:],
            ]
        ),
        "config": {
            "dataset_root": str(DATASET_ROOT),
            "tx_tags": args.tx_tags,
            "rx_tag": args.rx_tag,
            "snrs": args.snrs,
            "l_values": args.l_values,
            "n_users": args.n_users,
            "seed": args.seed,
            "user_indices": user_indices.tolist(),
            "num_subcarriers": args.num_subcarriers,
            "subcarrier_spacing_hz": args.subcarrier_spacing_hz,
            "source_alpha": source_alpha,
            "source_alpha_source": source_alpha_path,
            "candidate_alphas": args.candidate_alphas,
            "search_radius": args.search_radius,
            "search_points": args.search_points,
        },
        "metrics": metrics,
        "environment": environment_snapshot(ROOT),
        "notes": [
            "Auxiliary/dev E2 run: raw DeepMIMO O1_60 ray MAT files are converted to normalized OFDM frequency-response tensors.",
            "The deployment comparator is the Stage-2 source-trained scalar alpha applied directly to O1_60; full bounded refinement and oracle-alpha are diagnostic comparators.",
            "Delay/TX metrics are dominant-bin proxy RMSE values and must not be presented as final physical angle/delay RMSE.",
            "This is still not a full trained T-OMP-Net/G2 evaluation because only the scalar alpha path transfers from Stage 2.",
        ],
    }
    manifest_path = output_dir / "run_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    evaluation_path = write_evaluation_summary(
        output_dir,
        metrics=metrics,
        interpretation=interpretation,
    )
    lines = [
        "# DeepMIMO O1_60 G2 Dev Run",
        "",
        f"- Claim update: `{claim_update}`",
        f"- Transfer proxy classification: `{transfer_proxy_classification}`",
        f"- TX tags: `{metrics['tx_tags']}`",
        f"- RX tag: `{args.rx_tag}`",
        f"- Source alpha: `{metrics['source_alpha']:.6g}` from `{metrics['source_alpha_source']}`",
        f"- Users: `{args.n_users}`",
        f"- SNRs: `{metrics['snrs_db']}` dB",
        f"- L values: `{metrics['l_values']}`",
        f"- Aggregated rows: `{len(rows)}`",
        f"- Sample rows: `{len(sample_rows)}`",
        f"- Minimum mean support recall: `{metrics['min_mean_support_recall']:.6g}`",
        f"- Mean grid channel NMSE across cells: `{metrics['mean_grid_channel_nmse_db_all']:.6g}` dB",
        f"- Mean source-alpha channel NMSE across cells: `{metrics['mean_source_alpha_channel_nmse_db_all']:.6g}` dB",
        f"- Mean source-alpha gain vs grid: `{metrics['mean_source_alpha_gain_vs_grid_db']:.6g}` dB",
        f"- Mean bounded refinement channel NMSE across cells: `{metrics['mean_bounded_refine_channel_nmse_db_all']:.6g}` dB",
        f"- Mean bounded gain vs grid: `{metrics['mean_bounded_gain_vs_grid_db']:.6g}` dB",
        f"- Mean source-alpha gap vs oracle-alpha: `{metrics['mean_source_alpha_gap_vs_oracle_db']:.6g}` dB",
        f"- Mean dominant energy recall: `{metrics['mean_dominant_energy_recall_all']:.6g}`",
        f"- RX x/y span: `{metrics['rx_x_span_m']:.3f}` m / `{metrics['rx_y_span_m']:.3f}` m",
        f"- Elapsed seconds: `{elapsed_seconds:.2f}`",
        "",
        "## Interpretation",
        "",
        interpretation,
        "",
        "This is a raw-loader and scalar source-alpha transfer validation, not final Sensors E2 evidence. It proves the O1_60 local ray files can be converted into reproducible OFDM channel tensors and scored under a direct Stage-2 alpha transfer proxy.",
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
    print(f"transfer_proxy_classification={transfer_proxy_classification}")
    print(f"min_mean_support_recall={metrics['min_mean_support_recall']:.4f}")
    print(f"mean_grid_channel_nmse_db_all={metrics['mean_grid_channel_nmse_db_all']:.4f}")
    print(f"mean_source_alpha_gain_vs_grid_db={metrics['mean_source_alpha_gain_vs_grid_db']:.4f}")
    print(f"mean_bounded_gain_vs_grid_db={metrics['mean_bounded_gain_vs_grid_db']:.4f}")


if __name__ == "__main__":
    main()
