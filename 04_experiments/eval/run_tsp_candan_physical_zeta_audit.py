"""Replay the frozen CDL campaign for physical-coordinate and zeta evidence."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.stats import t as student_t
from sionna.phy import config as sionna_config


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_active_modules"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from baseline.local_refinement import axiswise_candan_diagnostics  # noqa: E402
from common.seed import seed_all  # noqa: E402
from common.tsp_revision_metrics import write_release_metadata  # noqa: E402
from tompnet.feature_controller import apply_nyquist_alias_lock  # noqa: E402
from run_sionna_cdl_profile_generalization import (  # noqa: E402
    add_awgn,
    generate_profile_channels,
    reconstruct_fft_topk,
)
from run_sionna_cdl_trained_refinement import (  # noqa: E402
    bins_to_physical,
    estimate_from_bins_lstsq,
    nmse_db,
    support_to_bins,
)
from run_tsp_candan_route_audit import residual_fraction  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profiles", nargs="+", default=("A", "C", "D"))
    parser.add_argument("--snrs", nargs="+", type=float, default=(0.0, 10.0, 20.0, 30.0))
    parser.add_argument("--l-values", nargs="+", type=int, default=(4, 8, 16))
    parser.add_argument("--test-seeds", nargs="+", type=int, default=(20260628, 20260629, 20260630, 20260701, 20260702))
    parser.add_argument("--samples-per-profile-seed", type=int, default=50)
    parser.add_argument("--generator-batch-size", type=int, default=50)
    parser.add_argument("--num-subcarriers", type=int, default=64)
    parser.add_argument("--num-tx-antennas", type=int, default=4)
    parser.add_argument("--spatial-truth-oversampling", type=int, default=4096)
    parser.add_argument("--subcarrier-spacing-hz", type=float, default=120e3)
    parser.add_argument("--carrier-frequency-hz", type=float, default=60e9)
    parser.add_argument("--delay-spread-s", type=float, default=100e-9)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--route-artifact-dir", default="tsp_candan_route_audit_paper")
    parser.add_argument("--zeta-bins", type=int, default=10)
    parser.add_argument("--verification-tolerance-db", type=float, default=1e-9)
    parser.add_argument("--output-dir-name", default="tsp_candan_physical_zeta_audit_paper")
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty CSV: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def circular_distance(left: np.ndarray, right: np.ndarray, period: float) -> np.ndarray:
    delta = np.abs(left - right)
    return np.minimum(delta, period - delta)


def physical_error_arrays(
    estimated_bins: np.ndarray,
    *,
    shape: tuple[int, int],
    truth_delays_s: np.ndarray,
    truth_spatial_frequencies: np.ndarray,
    truth_path_powers: np.ndarray,
    subcarrier_spacing_hz: float,
) -> tuple[np.ndarray, np.ndarray]:
    match_count = min(len(estimated_bins), len(truth_delays_s))
    truth_indices = np.argsort(truth_path_powers)[::-1][:match_count]
    selected_delays = np.asarray(truth_delays_s)[truth_indices]
    selected_spatial = np.asarray(truth_spatial_frequencies)[truth_indices]
    estimated_delays, estimated_spatial = bins_to_physical(
        estimated_bins, shape=shape, subcarrier_spacing_hz=subcarrier_spacing_hz
    )
    delay_period = 1.0 / subcarrier_spacing_hz
    delay_resolution = 1.0 / (shape[0] * subcarrier_spacing_hz)
    spatial_resolution = 1.0 / shape[1]
    delay_cost = circular_distance(selected_delays[:, None], estimated_delays[None, :], delay_period) / delay_resolution
    spatial_cost = circular_distance(selected_spatial[:, None], estimated_spatial[None, :], 1.0) / spatial_resolution
    truth_rows, estimate_columns = linear_sum_assignment(delay_cost**2 + spatial_cost**2)
    delay_error_bins = circular_distance(selected_delays[truth_rows], estimated_delays[estimate_columns], delay_period) / delay_resolution
    spatial_error_bins = circular_distance(selected_spatial[truth_rows], estimated_spatial[estimate_columns], 1.0) / spatial_resolution
    return delay_error_bins, spatial_error_bins


def error_metrics(
    delay_bins: np.ndarray,
    spatial_bins: np.ndarray,
    delay_resolution_ns: float,
    spatial_resolution: float,
) -> dict[str, float]:
    radial = np.sqrt(delay_bins**2 + spatial_bins**2)
    return {
        "delay_rmse_bins": float(np.sqrt(np.mean(delay_bins**2))),
        "delay_rmse_ns": float(np.sqrt(np.mean(delay_bins**2)) * delay_resolution_ns),
        "projected_spatial_rmse_bins": float(np.sqrt(np.mean(spatial_bins**2))),
        "projected_spatial_rmse": float(np.sqrt(np.mean(spatial_bins**2)) * spatial_resolution),
        "joint_quarter_bin_hit": float(np.mean((delay_bins <= 0.25) & (spatial_bins <= 0.25))),
        "joint_tenth_bin_hit": float(np.mean((delay_bins <= 0.1) & (spatial_bins <= 0.1))),
        "delay_quarter_bin_hit": float(np.mean(delay_bins <= 0.25)),
        "spatial_quarter_bin_hit": float(np.mean(spatial_bins <= 0.25)),
        "delay_tenth_bin_hit": float(np.mean(delay_bins <= 0.1)),
        "spatial_tenth_bin_hit": float(np.mean(spatial_bins <= 0.1)),
        "median_delay_error_bins": float(np.median(delay_bins)),
        "median_projected_spatial_error_bins": float(np.median(spatial_bins)),
        "median_coordinate_error_bins": float(np.median(radial)),
    }


def seed_mean_ci(rows: list[dict[str, object]], key: str) -> tuple[float, float, float]:
    seeds = sorted({int(row["seed"]) for row in rows})
    values = np.asarray([np.mean([float(row[key]) for row in rows if int(row["seed"]) == seed]) for seed in seeds])
    center = float(np.mean(values))
    if len(values) < 2:
        return center, center, center
    half = float(student_t.ppf(0.975, len(values) - 1) * np.std(values, ddof=1) / np.sqrt(len(values)))
    return center, center - half, center + half


def component_seed_stat(rows: list[dict[str, object]], method: str) -> dict[str, float]:
    delay = np.asarray([float(r[f"{method}_delay_error_bins"]) for r in rows])
    spatial = np.asarray([float(r[f"{method}_projected_spatial_error_bins"]) for r in rows])
    radial = np.sqrt(delay**2 + spatial**2)
    return {
        "delay_rmse_bins": float(np.sqrt(np.mean(delay**2))),
        "delay_rmse_ns": float(np.sqrt(np.mean(delay**2)) * float(rows[0]["delay_resolution_ns"])),
        "projected_spatial_rmse_bins": float(np.sqrt(np.mean(spatial**2))),
        "projected_spatial_rmse": float(np.sqrt(np.mean(spatial**2)) * float(rows[0]["spatial_resolution"])),
        "joint_quarter_bin_hit": float(np.mean((delay <= 0.25) & (spatial <= 0.25))),
        "joint_tenth_bin_hit": float(np.mean((delay <= 0.1) & (spatial <= 0.1))),
        "delay_quarter_bin_hit": float(np.mean(delay <= 0.25)),
        "spatial_quarter_bin_hit": float(np.mean(spatial <= 0.25)),
        "delay_tenth_bin_hit": float(np.mean(delay <= 0.1)),
        "spatial_tenth_bin_hit": float(np.mean(spatial <= 0.1)),
        "median_delay_error_bins": float(np.median(delay)),
        "median_projected_spatial_error_bins": float(np.median(spatial)),
        "median_coordinate_error_bins": float(np.median(radial)),
    }


def profile_summary(
    scene_rows: list[dict[str, object]], component_rows: list[dict[str, object]]
) -> list[dict[str, object]]:
    output = []
    for profile in [*sorted({str(r["profile"]) for r in scene_rows}), "All"]:
        scenes = scene_rows if profile == "All" else [r for r in scene_rows if r["profile"] == profile]
        components = component_rows if profile == "All" else [r for r in component_rows if r["profile"] == profile]
        seeds = sorted({int(r["seed"]) for r in components})
        item: dict[str, object] = {"profile": profile, "scene_count": len(scenes), "component_count": len(components), "seed_count": len(seeds)}
        for method in ("grid", "candan", "gated_candan"):
            per_seed = [component_seed_stat([r for r in components if int(r["seed"]) == seed], method) for seed in seeds]
            for metric in per_seed[0]:
                values = np.asarray([row[metric] for row in per_seed])
                center = float(np.mean(values))
                half = float(student_t.ppf(0.975, len(values) - 1) * np.std(values, ddof=1) / np.sqrt(len(values)))
                low, high = center - half, center + half
                if metric.endswith("_hit"):
                    low, high = max(0.0, low), min(1.0, high)
                item[f"mean_{method}_{metric}"] = center
                item[f"{method}_{metric}_ci95_low"] = low
                item[f"{method}_{metric}_ci95_high"] = high
        item["gate_pass_rate"] = float(np.mean([float(r["gate_pass"]) for r in scenes]))
        item["clipping_rate"] = float(np.mean([float(r["candan_clipping_rate"]) for r in scenes]))
        item["any_clipping_probability"] = float(np.mean([float(r["candan_clipping_rate"]) > 0.0 for r in scenes]))
        zeta = np.asarray([float(r["candan_minimum_zeta"]) for r in scenes])
        for q in (0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99):
            item[f"minimum_zeta_q{int(100*q):02d}"] = float(np.quantile(zeta, q))
        output.append(item)
    return output


def scene_profile_summary(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    metrics = []
    for method in ("grid", "candan", "gated_candan"):
        metrics.extend([
            f"{method}_delay_rmse_bins", f"{method}_delay_rmse_ns",
            f"{method}_projected_spatial_rmse_bins", f"{method}_projected_spatial_rmse",
            f"{method}_joint_quarter_bin_hit", f"{method}_joint_tenth_bin_hit",
            f"{method}_median_coordinate_error_bins",
        ])
    output = []
    for profile in [*sorted({str(r["profile"]) for r in rows}), "All"]:
        selected = rows if profile == "All" else [r for r in rows if r["profile"] == profile]
        item: dict[str, object] = {"profile": profile, "scene_count": len(selected), "seed_count": len({int(r["seed"]) for r in selected})}
        for key in metrics:
            center, low, high = seed_mean_ci(selected, key)
            if key.endswith("_hit"):
                low, high = max(0.0, low), min(1.0, high)
            item[f"mean_scene_{key}"] = center
            item[f"{key}_seed_ci95_low"] = low
            item[f"{key}_seed_ci95_high"] = high
        output.append(item)
    return output


def zeta_summary(rows: list[dict[str, object]], count: int) -> list[dict[str, object]]:
    values = np.asarray([float(r["candan_minimum_zeta"]) for r in rows])
    edges = np.unique(np.quantile(values, np.linspace(0.0, 1.0, count + 1)))
    if edges.size == 1:
        edges = np.asarray([edges[0], np.nextafter(edges[0], np.inf)])
    output = []
    for index, (low, high) in enumerate(zip(edges[:-1], edges[1:])):
        selected = [r for r in rows if float(r["candan_minimum_zeta"]) >= low and (float(r["candan_minimum_zeta"]) <= high if index == len(edges) - 2 else float(r["candan_minimum_zeta"]) < high)]
        output.append({
            "zeta_bin": index + 1, "zeta_low": float(low), "zeta_high": float(high), "scene_count": len(selected),
            "beneficial_probability": float(np.mean([float(r["candan_gain_vs_grid_db"]) > 0.0 for r in selected])),
            "mean_clean_gain_db": float(np.mean([float(r["candan_gain_vs_grid_db"]) for r in selected])),
            "median_candan_coordinate_error_bins": float(np.median([float(r["candan_median_coordinate_error_bins"]) for r in selected])),
            "mean_clipping_rate": float(np.mean([float(r["candan_clipping_rate"]) for r in selected])),
            "any_clipping_probability": float(np.mean([float(r["candan_clipping_rate"]) > 0.0 for r in selected])),
            "gate_pass_rate": float(np.mean([float(r["gate_pass"]) for r in selected])),
        })
    return output


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    args = parse_args()
    started = time.perf_counter()
    route_dir = ROOT / "05_results" / args.route_artifact_dir
    route_rows = [
        r for r in read_csv(route_dir / "per_scene.csv")
        if r["split"] == "test"
        and r["profile"] in args.profiles
        and int(r["seed"]) in args.test_seeds
        and float(r["snr_db"]) in args.snrs
        and int(r["l_value"]) in args.l_values
        and int(r["sample_index"]) < args.samples_per_profile_seed
    ]
    route_index = {(r["profile"], int(r["seed"]), float(r["snr_db"]), int(r["l_value"]), int(r["sample_index"])): r for r in route_rows}
    gates = {r["method"]: r for r in read_csv(route_dir / "residual_gates.csv")}
    gate_threshold = float(gates["candan"]["threshold"])
    rows: list[dict[str, object]] = []
    component_rows: list[dict[str, object]] = []
    verification_errors: list[float] = []
    for profile in args.profiles:
        for seed in args.test_seeds:
            seed_all(seed)
            sionna_config.seed = seed
            rng = np.random.default_rng(seed + 1000 * (ord(profile[0]) - ord("A") + 1))
            clean_batch, delays_batch, spatial_batch, powers_batch = generate_profile_channels(
                profile=profile, batch_size=args.generator_batch_size,
                num_subcarriers=args.num_subcarriers, subcarrier_spacing_hz=args.subcarrier_spacing_hz,
                carrier_frequency_hz=args.carrier_frequency_hz, delay_spread_s=args.delay_spread_s,
                num_tx_antennas=args.num_tx_antennas, spatial_truth_oversampling=args.spatial_truth_oversampling,
                device=args.device,
            )
            for snr_db in args.snrs:
                noisy_batch = [add_awgn(clean, snr_db=snr_db, rng=rng)[0] for clean in clean_batch]
                for l_value in args.l_values:
                    for sample_index, (clean, noisy) in enumerate(zip(clean_batch, noisy_batch)):
                        if sample_index >= args.samples_per_profile_seed:
                            break
                        grid_estimate, support, _ = reconstruct_fft_topk(noisy, l_value)
                        coarse_bins = support_to_bins(support, clean.shape)
                        candan = axiswise_candan_diagnostics(noisy, coarse_bins)
                        candan_bins = apply_nyquist_alias_lock(coarse_bins, candan.bins, angle_bin_count=clean.shape[1])
                        candan_estimate = estimate_from_bins_lstsq(noisy, candan_bins)
                        grid_nmse = nmse_db(grid_estimate, clean)
                        candan_nmse = nmse_db(candan_estimate, clean)
                        key = (profile, seed, float(snr_db), int(l_value), sample_index)
                        reference = route_index[key]
                        max_error = max(abs(grid_nmse - float(reference["grid_channel_nmse_db"])), abs(candan_nmse - float(reference["candan_channel_nmse_db"])))
                        verification_errors.append(max_error)
                        if max_error > args.verification_tolerance_db:
                            raise RuntimeError(f"route replay mismatch {key}: {max_error:.3e} dB")
                        residual_gain = residual_fraction(noisy, grid_estimate) - residual_fraction(noisy, candan_estimate)
                        passed = residual_gain >= gate_threshold
                        if int(passed) != int(reference["gated_candan_pass"]):
                            raise RuntimeError(f"gate replay mismatch {key}")
                        delay_resolution_ns = 1e9 / (clean.shape[0] * args.subcarrier_spacing_hz)
                        grid_errors = physical_error_arrays(
                            coarse_bins, shape=clean.shape, truth_delays_s=delays_batch[sample_index],
                            truth_spatial_frequencies=spatial_batch[sample_index], truth_path_powers=powers_batch[sample_index],
                            subcarrier_spacing_hz=args.subcarrier_spacing_hz,
                        )
                        candan_errors = physical_error_arrays(
                            candan_bins, shape=clean.shape, truth_delays_s=delays_batch[sample_index],
                            truth_spatial_frequencies=spatial_batch[sample_index], truth_path_powers=powers_batch[sample_index],
                            subcarrier_spacing_hz=args.subcarrier_spacing_hz,
                        )
                        row: dict[str, object] = {
                            "profile": profile, "seed": seed, "snr_db": snr_db, "l_value": l_value, "sample_index": sample_index,
                            "grid_channel_nmse_db": grid_nmse, "candan_channel_nmse_db": candan_nmse,
                            "candan_gain_vs_grid_db": grid_nmse - candan_nmse,
                            "candan_residual_reduction_fraction": residual_gain, "gate_pass": int(passed),
                            "candan_minimum_zeta": candan.minimum_denominator_stability,
                            "candan_mean_zeta": candan.mean_denominator_stability,
                            "candan_clipping_rate": candan.clipping_rate,
                        }
                        spatial_resolution = 1.0 / clean.shape[1]
                        grid_metrics = error_metrics(*grid_errors, delay_resolution_ns, spatial_resolution)
                        candan_metrics = error_metrics(*candan_errors, delay_resolution_ns, spatial_resolution)
                        for name, value in grid_metrics.items():
                            row[f"grid_{name}"] = value
                        for name, value in candan_metrics.items():
                            row[f"candan_{name}"] = value
                            row[f"gated_candan_{name}"] = value if passed else grid_metrics[name]
                        rows.append(row)
                        for component_index in range(len(grid_errors[0])):
                            component: dict[str, object] = {
                                "profile": profile, "seed": seed, "snr_db": snr_db,
                                "l_value": l_value, "sample_index": sample_index,
                                "component_index": component_index,
                                "delay_resolution_ns": delay_resolution_ns,
                                "spatial_resolution": spatial_resolution,
                                "gate_pass": int(passed),
                            }
                            for method, errors in (("grid", grid_errors), ("candan", candan_errors)):
                                delay_error = float(errors[0][component_index])
                                spatial_error = float(errors[1][component_index])
                                component[f"{method}_delay_error_bins"] = delay_error
                                component[f"{method}_projected_spatial_error_bins"] = spatial_error
                            for axis in ("delay_error_bins", "projected_spatial_error_bins"):
                                component[f"gated_candan_{axis}"] = component[f"candan_{axis}"] if passed else component[f"grid_{axis}"]
                            component_rows.append(component)
    if len(rows) != len(route_index):
        raise RuntimeError(f"replayed {len(rows)} rows but route artifact contains {len(route_index)} test rows")
    profiles = profile_summary(rows, component_rows)
    scene_profiles = scene_profile_summary(rows)
    zeta = zeta_summary(rows, args.zeta_bins)
    output = ROOT / "05_results" / args.output_dir_name
    output.mkdir(parents=True, exist_ok=True)
    write_csv(output / "per_scene_physical_zeta.csv", rows)
    write_csv(output / "per_component_physical_errors.csv", component_rows)
    write_csv(output / "profile_physical_metrics.csv", profiles)
    write_csv(output / "profile_scene_physical_metrics.csv", scene_profiles)
    write_csv(output / "zeta_binned_evidence.csv", zeta)
    summary = {
        "scene_count": len(rows), "profile_count": len(args.profiles), "gate_threshold": gate_threshold,
        "route_artifact": str(route_dir.relative_to(ROOT)), "maximum_route_replay_error_db": max(verification_errors),
        "profile_summary": profiles, "elapsed_seconds": time.perf_counter() - started,
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    command = "python 04_experiments/eval/run_tsp_candan_physical_zeta_audit.py"
    write_release_metadata(output, config=vars(args), seeds=[{"split": "test", "seed": s} for s in args.test_seeds], command=command)
    code_path = Path(__file__).resolve()
    manifest = {
        "run_id": "tsp_candan_physical_zeta_audit_20260830", "command": command, "cwd": str(ROOT),
        "config": vars(args), "metrics": {"scene_count": len(rows), "maximum_route_replay_error_db": max(verification_errors)},
        "inputs_sha256": {
            str((route_dir / "per_scene.csv").relative_to(ROOT)): sha256(route_dir / "per_scene.csv"),
            str((route_dir / "residual_gates.csv").relative_to(ROOT)): sha256(route_dir / "residual_gates.csv"),
        },
        "code_sha256": {str(code_path.relative_to(ROOT)): sha256(code_path)},
        "software": {"python": sys.version, "numpy": np.__version__, "platform": platform.platform()},
        "git_commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False).stdout.strip(),
        "notes": [
            "The five frozen test seeds, Sionna CDL generator, AWGN order, top-L supports, alias lock, and residual threshold exactly replay the route audit.",
            "The maximum row-wise NMSE discrepancy against the frozen route artifact is checked before release.",
            "Physical-path assignment uses the strongest min(L, path_count) CIR paths and a joint periodic delay/projected-spatial Hungarian cost.",
        ],
    }
    (output / "audit_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"scene_count": len(rows), "maximum_route_replay_error_db": max(verification_errors), "elapsed_seconds": summary["elapsed_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
