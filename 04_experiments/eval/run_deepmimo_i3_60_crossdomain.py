from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

import numpy as np
from scipy.io import loadmat

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_active_modules"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from common.manifest import environment_snapshot
from common.seed import seed_all
from run_deepmimo_o1_60_g2 import (
    add_awgn,
    estimate_from_bins_lstsq,
    finite_mean,
    nmse_db,
    refine_bins_local,
    reconstruct_fft_topk,
    support_to_bins,
    support_metrics,
)

DATASET_ROOT = (
    ROOT
    / "90_archive"
    / "2025_thesis_materials"
    / "参考"
    / "DeepMIMO-5GNR"
    / "DeepMIMO_dataset"
    / "I3_60_v1"
)

SOURCE_ALPHA_CSV = (
    ROOT
    / "05_results"
    / "stage2_torch_locked_scale_g2_seed_sweep"
    / "stage2_torch_locked_scale_g2_seed_sweep_seeds.csv"
)


def load_flat_i3_array(bs_index: int) -> np.ndarray:
    path = DATASET_ROOT / f"I3_60.{bs_index}.CIR.mat"
    return np.asarray(loadmat(path, squeeze_me=True)["CIR_array_full"], dtype=float).ravel()


def load_rx_locations() -> np.ndarray:
    path = DATASET_ROOT / "I3_60.RX_Loc.mat"
    return np.asarray(loadmat(path, squeeze_me=True)["RX_Loc_array_full"], dtype=float)


def load_source_alpha(path: Path = SOURCE_ALPHA_CSV) -> tuple[float, str]:
    alphas: list[float] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            alphas.append(float(row["alpha"]))
    if not alphas:
        raise ValueError(f"No source alpha values found in {path}.")
    return finite_mean(alphas), str(path.relative_to(ROOT))


def block_offsets(flat: np.ndarray) -> list[int]:
    n_blocks = int(round(float(flat[0])))
    offsets: list[int] = []
    position = 1
    for _ in range(n_blocks):
        if position + 1 >= flat.size:
            raise ValueError("I3_60 CIR array ended inside a user block header.")
        n_paths = int(round(float(flat[position + 1])))
        next_position = position + 2 + 4 * n_paths
        if n_paths < 0 or next_position > flat.size:
            raise ValueError(f"Invalid I3_60 user block at offset {position}.")
        offsets.append(position)
        position = next_position
    if position != flat.size:
        raise ValueError(f"I3_60 CIR parser ended at {position}, expected {flat.size}.")
    return offsets


def parse_block(flat: np.ndarray, offset: int) -> dict[str, np.ndarray | int]:
    user_id = int(round(float(flat[offset])))
    n_paths = int(round(float(flat[offset + 1])))
    payload = flat[offset + 2 : offset + 2 + 4 * n_paths].reshape(n_paths, 4)
    return {
        "user_id": user_id,
        "path_id": payload[:, 0].astype(int),
        "phase_deg": payload[:, 1],
        "delay_s": payload[:, 2],
        "power_db": payload[:, 3],
    }


def choose_user_indices(*, n_total: int, n_users: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    if n_users >= n_total:
        return np.arange(n_total)
    grid = np.linspace(0, n_total - 1, n_users * 4, dtype=int)
    rng.shuffle(grid)
    return np.sort(np.unique(grid[:n_users]))


def build_channels(
    *,
    bs_indices: list[int],
    user_indices: np.ndarray,
    num_subcarriers: int,
    subcarrier_spacing_hz: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    frequencies = (
        np.arange(num_subcarriers, dtype=float) - (num_subcarriers - 1) / 2.0
    ) * subcarrier_spacing_hz
    flats = {bs_index: load_flat_i3_array(bs_index) for bs_index in bs_indices}
    offsets = {bs_index: block_offsets(flat) for bs_index, flat in flats.items()}
    n_blocks = min(len(value) for value in offsets.values())
    if np.max(user_indices) >= n_blocks:
        raise ValueError(f"Requested user index beyond I3_60 block count {n_blocks}.")

    channels = np.zeros((len(user_indices), num_subcarriers, len(bs_indices)), dtype=np.complex128)
    path_counts = np.zeros((len(user_indices), len(bs_indices)), dtype=float)
    delay_truth = np.full((len(user_indices), len(bs_indices)), np.nan, dtype=float)
    power_truth = np.full((len(user_indices), len(bs_indices)), np.nan, dtype=float)
    for bs_axis, bs_index in enumerate(bs_indices):
        flat = flats[bs_index]
        bs_offsets = offsets[bs_index]
        for row_index, user_index in enumerate(user_indices):
            block = parse_block(flat, bs_offsets[int(user_index)])
            phase = np.deg2rad(np.asarray(block["phase_deg"], dtype=float))
            delay = np.asarray(block["delay_s"], dtype=float)
            power_db = np.asarray(block["power_db"], dtype=float)
            finite = np.isfinite(phase) & np.isfinite(delay) & np.isfinite(power_db)
            path_counts[row_index, bs_axis] = float(np.sum(finite))
            if np.any(finite):
                amplitude = 10.0 ** (power_db[finite] / 20.0)
                phasor = amplitude * np.exp(1j * phase[finite])
                channels[row_index, :, bs_axis] = np.sum(
                    phasor[None, :] * np.exp(-2j * np.pi * frequencies[:, None] * delay[finite][None, :]),
                    axis=1,
                )
                strongest = np.flatnonzero(finite)[np.argmax(power_db[finite])]
                delay_truth[row_index, bs_axis] = delay[strongest]
                power_truth[row_index, bs_axis] = power_db[strongest]

    norms = np.sqrt(np.mean(np.abs(channels) ** 2, axis=(1, 2), keepdims=True))
    channels = channels / np.maximum(norms, 1e-300)
    return channels, path_counts, delay_truth, power_truth


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


def verdict(rows: list[dict[str, float | str]]) -> tuple[str, str, str]:
    grid_nmse = [float(row["mean_grid_channel_nmse_db"]) for row in rows]
    source_nmse = [float(row["mean_source_alpha_channel_nmse_db"]) for row in rows]
    recall = [float(row["mean_support_recall"]) for row in rows]
    source_gain = [float(row["mean_source_alpha_gain_vs_grid_db"]) for row in rows]
    if not all(np.isfinite(grid_nmse + source_nmse + recall + source_gain)):
        return (
            "failed-metric-gate",
            "fail",
            "At least one I3_60 evaluation cell produced non-finite metrics.",
        )
    if finite_mean(source_gain) > 0.0 and min(recall) >= 0.5:
        return (
            "weak-source-alpha-transfer",
            "weak",
            "The source-trained G2 alpha transfer proxy produced finite I3_60 metrics with positive mean gain and acceptable dominant-bin recall.",
        )
    if finite_mean(source_gain) > 0.0:
        return (
            "partial-source-alpha-transfer",
            "partial",
            "The source-trained G2 alpha improves mean I3_60 NMSE, but at least one cell has weak dominant-bin recall.",
        )
    return (
        "source-alpha-transfer-fails",
        "fail",
        "The source-trained G2 alpha does not improve mean I3_60 NMSE over grid FFT top-k in this dev grid.",
    )


def write_evaluation_summary(
    output_dir: Path,
    *,
    metrics: dict[str, float | str],
    interpretation: str,
) -> Path:
    lines = [
        "# DeepMIMO I3_60 Cross-Domain Dev Summary",
        "",
        "## Outcome Summary",
        "",
        "This E3 dev-run reads local DeepMIMO I3_60 CIR MAT files, synthesizes normalized OFDM frequency responses, adds AWGN, and evaluates grid FFT top-k, Stage-2 source-trained alpha transfer, full bounded refinement, and oracle-alpha diagnostics.",
        "",
        "It is not yet the full cross-domain G2/T-OMP-Net result: the transferred object is the scalar Stage-2 alpha path rather than a full network, and delay/TX metrics remain dominant-bin proxy metrics.",
        "",
        "## evaluation_summary",
        "",
        "- `research_question`: Can I3_60 indoor ray-traced CIR data be converted into reproducible OFDM channel tensors and assigned a weak/partial/fail proxy classification under the current Tensor-OMP-style metric contract?",
        f"- `claim_update`: {metrics['claim_update']}",
        f"- `transfer_proxy_classification`: {metrics['transfer_proxy_classification']}",
        f"- `source_alpha`: {metrics['source_alpha']}",
        "- `baseline_relation`: Stage-2 source-trained alpha is compared against grid FFT top-k on the same noisy I3_60 synthesized channel tensor; full bounded refinement and oracle-alpha are diagnostic comparators.",
        "- `failure_mode`: None if executable; limitation is raw-loader proxy metrics, two-BS channel width, and scalar-alpha rather than full trained cross-domain model transfer.",
        f"- `mechanism_note`: {interpretation}",
        "- `next_action`: Attach the trained locked-scale G2/T-OMP-Net path or train an I3-compatible adapter, then rerun I3_60 with physical angle/delay metrics.",
        "- `evidence_level`: E3 auxiliary/dev raw-loader and proxy cross-scenario classification.",
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
    parser.add_argument("--bs-indices", nargs="+", type=int, default=[1, 2])
    parser.add_argument("--snrs", nargs="+", type=float, default=[0.0, 10.0, 20.0, 30.0])
    parser.add_argument("--l-values", nargs="+", type=int, default=[4, 8, 16])
    parser.add_argument("--n-users", type=int, default=16)
    parser.add_argument("--seed", type=int, default=20260626)
    parser.add_argument("--num-subcarriers", type=int, default=64)
    parser.add_argument("--subcarrier-spacing-hz", type=float, default=120e3)
    parser.add_argument("--search-radius", type=float, default=0.45)
    parser.add_argument("--search-points", type=int, default=5)
    parser.add_argument("--candidate-alphas", nargs="+", type=float, default=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2])
    parser.add_argument("--output-dir-name", default="deepmimo_i3_60_crossdomain")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    started = time.perf_counter()
    seed_all(args.seed)
    source_alpha, source_alpha_path = load_source_alpha()
    first_flat = load_flat_i3_array(args.bs_indices[0])
    n_blocks = len(block_offsets(first_flat))
    user_indices = choose_user_indices(n_total=n_blocks, n_users=args.n_users, seed=args.seed)
    rx_pos = load_rx_locations()[user_indices]
    clean_batch, path_counts, delay_truth, power_truth = build_channels(
        bs_indices=args.bs_indices,
        user_indices=user_indices,
        num_subcarriers=args.num_subcarriers,
        subcarrier_spacing_hz=args.subcarrier_spacing_hz,
    )

    rows: list[dict[str, float | str]] = []
    sample_rows: list[dict[str, float | str]] = []
    rng = np.random.default_rng(args.seed + 31)
    for snr_db in args.snrs:
        noisy_batch = []
        noise_vars = []
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
                        "rx_x_m": float(rx_pos[sample_index, 1]),
                        "rx_y_m": float(rx_pos[sample_index, 2]),
                        "rx_z_m": float(rx_pos[sample_index, 3]),
                    }
                )
            rows.append(
                {
                    "snr_db": float(snr_db),
                    "l_value": float(l_value),
                    "n_users": float(args.n_users),
                    "n_bs": float(len(args.bs_indices)),
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
    metrics: dict[str, float | str] = {
        "claim_update": claim_update,
        "transfer_proxy_classification": transfer_proxy_classification,
        "dataset": "DeepMIMO I3_60_v1 CIR files",
        "bs_indices": ",".join(str(value) for value in args.bs_indices),
        "source_alpha": source_alpha,
        "source_alpha_source": source_alpha_path,
        "candidate_alphas": ",".join(str(value) for value in args.candidate_alphas),
        "n_users": float(args.n_users),
        "n_bs": float(len(args.bs_indices)),
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
        "mean_dominant_energy_recall_all": finite_mean(
            [float(row["mean_dominant_energy_recall"]) for row in rows]
        ),
        "mean_path_count": float(np.mean(path_counts)),
        "min_path_count": float(np.min(path_counts)),
        "max_path_count": float(np.max(path_counts)),
        "rx_x_span_m": float(np.nanmax(rx_pos[:, 1]) - np.nanmin(rx_pos[:, 1])),
        "rx_y_span_m": float(np.nanmax(rx_pos[:, 2]) - np.nanmin(rx_pos[:, 2])),
        "finite_delay_truth_fraction": float(np.isfinite(delay_truth).mean()),
        "finite_power_truth_fraction": float(np.isfinite(power_truth).mean()),
        "elapsed_seconds": elapsed_seconds,
    }

    output_dir = ROOT / "05_results" / args.output_dir_name
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_csv = output_dir / "deepmimo_i3_60_crossdomain.csv"
    with summary_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    samples_csv = output_dir / "deepmimo_i3_60_crossdomain_samples.csv"
    with samples_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(sample_rows[0].keys()))
        writer.writeheader()
        writer.writerows(sample_rows)

    manifest = {
        "run_id": f"deepmimo_i3_60_crossdomain_dev_seed_{args.seed}_n{args.n_users}",
        "command": subprocess.list2cmdline(
            [
                sys.executable,
                str(Path(__file__).resolve().relative_to(ROOT)),
                *sys.argv[1:],
            ]
        ),
        "config": {
            "dataset_root": str(DATASET_ROOT),
            "bs_indices": args.bs_indices,
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
            "Auxiliary/dev E3 run: raw DeepMIMO I3_60 CIR MAT files are converted to normalized OFDM frequency-response tensors.",
            "The deployment comparator is the Stage-2 source-trained scalar alpha applied directly to I3_60; full bounded refinement and oracle-alpha are diagnostic comparators.",
            "I3_60 CIR parser treats each path payload as path_id, phase_deg, delay_s, power_db based on block-boundary validation and DeepMIMO CIR value ranges.",
            "Delay/TX metrics are dominant-bin proxy RMSE values and must not be presented as final physical angle/delay RMSE.",
            "This is still not a full trained cross-domain G2/T-OMP-Net evaluation because only the scalar alpha path transfers across domains.",
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
        "# DeepMIMO I3_60 Cross-Domain Dev Run",
        "",
        f"- Claim update: `{claim_update}`",
        f"- Transfer proxy classification: `{transfer_proxy_classification}`",
        f"- BS indices: `{metrics['bs_indices']}`",
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
        f"- Mean path count: `{metrics['mean_path_count']:.3f}`",
        f"- RX x/y span: `{metrics['rx_x_span_m']:.3f}` m / `{metrics['rx_y_span_m']:.3f}` m",
        f"- Elapsed seconds: `{elapsed_seconds:.2f}`",
        "",
        "## Interpretation",
        "",
        interpretation,
        "",
        "This is a raw-loader and scalar source-alpha transfer validation, not final Sensors E3 evidence. It proves the I3_60 local CIR files can be converted into reproducible OFDM channel tensors and scored under a direct Stage-2 alpha transfer proxy.",
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
