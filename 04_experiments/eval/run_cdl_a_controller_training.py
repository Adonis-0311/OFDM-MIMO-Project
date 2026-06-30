from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
import torch
from sionna.phy import config as sionna_config

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_active_modules"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from common.manifest import environment_snapshot
from common.seed import seed_all
from tompnet.feature_controller import FEATURE_NAMES, FeatureConditionedRefinementController
from run_feature_controller_source_training import (
    finite_mean,
    prepare_contract,
    sample_loss,
    sample_metrics,
)
from run_sionna_cdl_profile_generalization import (
    add_awgn,
    generate_profile_channels,
    reconstruct_fft_topk,
)
from run_sionna_cdl_trained_refinement import refine_bins_local, support_to_bins


def truth_bins_from_cir(
    delays_s: np.ndarray,
    spatial_frequencies: np.ndarray,
    powers: np.ndarray,
    *,
    shape: tuple[int, int],
    subcarrier_spacing_hz: float,
    l_value: int,
) -> np.ndarray:
    count = min(l_value, len(delays_s))
    indices = np.argsort(powers)[::-1][:count]
    delay_bins = np.mod(-delays_s[indices] * shape[0] * subcarrier_spacing_hz, shape[0])
    angle_bins = np.mod(spatial_frequencies[indices] * shape[1], shape[1])
    return np.stack([delay_bins, angle_bins], axis=1)


def generate_samples(
    *,
    profile: str,
    seed: int,
    batch_size: int,
    snrs: list[float],
    l_values: list[int],
    search_radius: float,
    search_points: int,
    subcarrier_spacing_hz: float,
) -> list[dict]:
    seed_all(seed)
    torch.manual_seed(seed)
    sionna_config.seed = seed
    rng = np.random.default_rng(seed + 1000 * (ord(profile[0]) - ord("A") + 1))
    clean_batch, delays_batch, spatial_batch, powers_batch = generate_profile_channels(
        profile=profile,
        batch_size=batch_size,
        num_subcarriers=64,
        subcarrier_spacing_hz=subcarrier_spacing_hz,
        carrier_frequency_hz=60e9,
        delay_spread_s=100e-9,
        num_tx_antennas=4,
        spatial_truth_oversampling=4096,
        device="cpu",
    )
    samples = []
    for snr_db in snrs:
        noisy_batch = [add_awgn(clean, snr_db=snr_db, rng=rng)[0] for clean in clean_batch]
        for l_value in l_values:
            for index, (clean, noisy) in enumerate(zip(clean_batch, noisy_batch)):
                _, support, _ = reconstruct_fft_topk(noisy, l_value)
                coarse = support_to_bins(support, clean.shape)
                refined = refine_bins_local(
                    noisy, coarse, search_radius=search_radius,
                    search_points=search_points)
                truth_bins = truth_bins_from_cir(
                    delays_batch[index], spatial_batch[index], powers_batch[index],
                    shape=clean.shape, subcarrier_spacing_hz=subcarrier_spacing_hz,
                    l_value=l_value)
                samples.append(prepare_contract({
                    "coarse": coarse, "refined": refined, "measurement": noisy,
                    "clean": clean, "truth_bins": truth_bins,
                    "snr_db": snr_db, "l_value": l_value,
                }, clean.shape, search_radius))
    return samples


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-profiles", nargs="+", default=["A"])
    parser.add_argument("--validation-profiles", nargs="+", default=["A"])
    parser.add_argument("--train-seeds", nargs="+", type=int, default=[20260620, 20260621, 20260622])
    parser.add_argument("--validation-seeds", nargs="+", type=int, default=[20260623])
    parser.add_argument("--train-samples-per-seed", type=int, default=12)
    parser.add_argument("--validation-samples-per-seed", type=int, default=8)
    parser.add_argument("--snrs", nargs="+", type=float, default=[0.0, 10.0, 20.0, 30.0])
    parser.add_argument("--l-values", nargs="+", type=int, default=[4, 8, 16])
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--lr", type=float, default=0.02)
    parser.add_argument("--hidden-dim", type=int, default=16)
    parser.add_argument("--parameter-weight", type=float, default=1.0)
    parser.add_argument("--search-radius", type=float, default=0.45)
    parser.add_argument("--search-points", type=int, default=5)
    parser.add_argument("--subcarrier-spacing-hz", type=float, default=120e3)
    parser.add_argument("--output-dir-name", default="cdl_a_feature_controller_training")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    shape = (64, 4)
    started = time.perf_counter()
    validation_samples = []
    for profile in args.validation_profiles:
        for seed in args.validation_seeds:
            validation_samples.extend(generate_samples(
                profile=profile, seed=seed,
                batch_size=args.validation_samples_per_seed,
                snrs=args.snrs, l_values=args.l_values,
                search_radius=args.search_radius, search_points=args.search_points,
                subcarrier_spacing_hz=args.subcarrier_spacing_hz))
    models = []
    seed_rows = []
    for seed in args.train_seeds:
        train_samples = []
        for profile in args.train_profiles:
            train_samples.extend(generate_samples(
                profile=profile, seed=seed,
                batch_size=args.train_samples_per_seed,
                snrs=args.snrs, l_values=args.l_values,
                search_radius=args.search_radius, search_points=args.search_points,
                subcarrier_spacing_hz=args.subcarrier_spacing_hz))
        features = np.stack([sample["features"] for sample in train_samples])
        feature_mean = torch.as_tensor(features.mean(axis=0), dtype=torch.float64)
        feature_std = torch.as_tensor(np.maximum(features.std(axis=0), 1e-6), dtype=torch.float64)
        torch.manual_seed(seed)
        model = FeatureConditionedRefinementController(hidden_dim=args.hidden_dim)
        optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
        history = []
        for _ in range(args.epochs):
            optimizer.zero_grad()
            losses = [sample_loss(
                model, sample, shape=shape, feature_mean=feature_mean,
                feature_std=feature_std, parameter_weight=args.parameter_weight)
                for sample in train_samples]
            loss = torch.stack([item[0] for item in losses]).mean()
            loss.backward()
            optimizer.step()
            history.append(float(loss.detach()))
        metrics = [sample_metrics(
            model, sample, shape=shape, feature_mean=feature_mean,
            feature_std=feature_std) for sample in validation_samples]
        seed_rows.append({
            "seed": float(seed),
            "mean_delay_alpha": finite_mean([item["delay_alpha"] for item in metrics]),
            "std_delay_alpha": float(np.std([item["delay_alpha"] for item in metrics])),
            "mean_angle_alpha": finite_mean([item["angle_alpha"] for item in metrics]),
            "std_angle_alpha": float(np.std([item["angle_alpha"] for item in metrics])),
            "mean_nmse_gain_db": finite_mean([item["grid_nmse_db"]-item["model_nmse_db"] for item in metrics]),
            "mean_delay_rmse_reduction_bins": finite_mean([item["grid_delay_rmse_bins"]-item["model_delay_rmse_bins"] for item in metrics]),
            "mean_angle_rmse_reduction_bins": finite_mean([item["grid_angle_rmse_bins"]-item["model_angle_rmse_bins"] for item in metrics]),
            "mean_angle_rmse_reduction_deg": finite_mean([item["grid_angle_rmse_deg"]-item["model_angle_rmse_deg"] for item in metrics]),
            "mean_local_delay_rmse_reduction_bins": finite_mean([item["local_grid_delay_rmse_bins"]-item["local_model_delay_rmse_bins"] for item in metrics]),
            "mean_local_angle_rmse_reduction_bins": finite_mean([item["local_grid_angle_rmse_bins"]-item["local_model_angle_rmse_bins"] for item in metrics]),
            "train_loss_reduction": history[0] - history[-1],
        })
        models.append({
            "seed": seed, "state_dict": model.state_dict(),
            "feature_mean": feature_mean, "feature_std": feature_std})
    elapsed = time.perf_counter() - started
    metrics = {
        "claim_update": "cdl-a-training-inconclusive",
        "training_profiles": ",".join(args.train_profiles),
        "validation_profiles": ",".join(args.validation_profiles),
        "train_seed_count": float(len(args.train_seeds)),
        "validation_seed_count": float(len(args.validation_seeds)),
        **{key: finite_mean([row[key] for row in seed_rows]) for key in (
            "mean_delay_alpha", "std_delay_alpha", "mean_angle_alpha", "std_angle_alpha",
            "mean_nmse_gain_db", "mean_delay_rmse_reduction_bins",
            "mean_angle_rmse_reduction_bins", "mean_angle_rmse_reduction_deg",
            "mean_local_delay_rmse_reduction_bins",
            "mean_local_angle_rmse_reduction_bins")},
        "elapsed_seconds": elapsed,
    }
    if (
        metrics["mean_nmse_gain_db"] > 0
        and metrics["mean_delay_rmse_reduction_bins"] > 0
        and metrics["mean_angle_rmse_reduction_deg"] >= 0.0
    ):
        metrics["claim_update"] = "cdl-profile-heldout-physical-supported"
    output = ROOT / "05_results" / args.output_dir_name
    output.mkdir(parents=True, exist_ok=True)
    with (output / "training_seeds.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(seed_rows[0].keys()))
        writer.writeheader()
        writer.writerows(seed_rows)
    torch.save({
        "feature_names": FEATURE_NAMES, "shape": shape,
        "hidden_dim": args.hidden_dim, "search_radius": args.search_radius,
        "models": models, "training_profiles": args.train_profiles,
        "training_config": vars(args), "metrics": metrics,
    }, output / "controller_checkpoint.pt")
    command = subprocess.list2cmdline([sys.executable, str(Path(__file__).resolve().relative_to(ROOT)), *sys.argv[1:]])
    manifest = {
        "run_id": f"cdl_a_controller_{len(args.train_seeds)}train_seed",
        "command": command, "config": vars(args) | {"shape": shape},
        "metrics": metrics, "environment": environment_snapshot(ROOT),
        "notes": [
            f"Training profiles: {args.train_profiles}; validation profiles: {args.validation_profiles}.",
            "Validation seeds are disjoint from training seeds.",
            "Any profile omitted from both training and validation remains an untouched zero-shot test profile.",
        ],
    }
    (output / "run_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# CDL Profile Feature Controller Training", "",
        f"- Claim update: {metrics['claim_update']}",
        f"- Held-out validation NMSE gain: {metrics['mean_nmse_gain_db']:.6g} dB",
        f"- Held-out validation delay/angle RMSE reduction: {metrics['mean_delay_rmse_reduction_bins']:.6g} / {metrics['mean_angle_rmse_reduction_bins']:.6g} bins",
        f"- Held-out physical broadside-angle RMSE reduction: {metrics['mean_angle_rmse_reduction_deg']:.6g} deg",
        f"- Mean delay/angle alpha: {metrics['mean_delay_alpha']:.6g} / {metrics['mean_angle_alpha']:.6g}",
        f"- Elapsed seconds: {elapsed:.2f}", "", "## Evaluation summary", "",
        "- research_question: Can a profile-trained controller improve held-out physical parameters before zero-shot profile testing?",
        f"- claim_update: {metrics['claim_update']}",
        "- baseline_relation: Held-out validation uses disjoint seeds and the unchanged grid comparator.",
        "- failure_mode: Non-positive held-out NMSE, delay-bin reduction, or physical broadside-angle reduction.",
        "- next_action: Freeze and test only on profiles omitted from training and validation.",
        "- evidence_level: Profile training with disjoint-seed validation; omitted profiles remain untouched.",
    ]
    text = "\n".join(lines) + "\n"
    (output / "summary.md").write_text(text, encoding="utf-8")
    (output / "evaluation_summary.md").write_text(text, encoding="utf-8")
    print(f"Wrote {(output / 'summary.md').relative_to(ROOT)}")
    for key in ("claim_update", "mean_nmse_gain_db", "mean_delay_rmse_reduction_bins", "mean_angle_rmse_reduction_bins", "mean_angle_rmse_reduction_deg", "mean_delay_alpha", "mean_angle_alpha"):
        print(f"{key}={metrics[key]}")


if __name__ == "__main__":
    main()
