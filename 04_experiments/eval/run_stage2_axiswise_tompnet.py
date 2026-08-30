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

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_active_modules"))

from common.manifest import environment_snapshot
from common.seed import seed_all
from data.offgrid_tensor import generate_offgrid_tensor_sample
from tompnet.torch_layer import (
    evaluate_torch_axiswise_refinement_layer_fast,
    normal_equation_nmse_loss,
    prepare_torch_sample,
    train_torch_axiswise_refinement_layer_fast,
)

SHARED_ALPHA_CSV = ROOT / "05_results" / "stage2_torch_locked_scale_g2_seed_sweep" / "stage2_torch_locked_scale_g2_seed_sweep_seeds.csv"


def finite_mean(values: list[float]) -> float:
    array = np.asarray(values, dtype=float)
    return float(np.mean(array[np.isfinite(array)]))


def load_shared_alpha() -> float:
    with SHARED_ALPHA_CSV.open(newline="", encoding="utf-8") as handle:
        values = [float(row["alpha"]) for row in csv.DictReader(handle)]
    return finite_mean(values)


def evaluate_fixed_alpha(samples: list, *, shape: tuple[int, int, int], alpha: float) -> float:
    values = []
    with torch.no_grad():
        fixed = torch.tensor(alpha, dtype=torch.float64)
        for sample in samples:
            loss = normal_equation_nmse_loss(
                torch.as_tensor(sample.coarse_bins, dtype=torch.float64),
                torch.as_tensor(sample.refined_bins, dtype=torch.float64),
                torch.as_tensor(sample.measurement, dtype=torch.complex128),
                torch.as_tensor(sample.clean, dtype=torch.complex128),
                shape,
                fixed,
            )
            values.append(float(10.0 * torch.log10(torch.clamp(loss, min=1e-30))))
    return finite_mean(values)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", nargs="+", type=int, default=[20260624, 20260625, 20260626, 20260627, 20260628])
    parser.add_argument("--l-values", nargs="+", type=int, default=[2, 4, 8])
    parser.add_argument("--n-train", type=int, default=4)
    parser.add_argument("--n-test", type=int, default=6)
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--lr", type=float, default=0.08)
    parser.add_argument("--snr-db", type=float, default=20.0)
    parser.add_argument("--offset-radius", type=float, default=0.35)
    parser.add_argument("--output-dir-name", default="stage2_axiswise_tompnet")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    shape = (128, 16, 32)
    shared_alpha = load_shared_alpha()
    started = time.perf_counter()
    rows: list[dict[str, float]] = []
    seed_rows: list[dict[str, float]] = []

    for seed in args.seeds:
        rng = seed_all(seed)
        torch.manual_seed(seed)
        train_samples = []
        test_by_l = {value: [] for value in args.l_values}
        for l_value in args.l_values:
            for _ in range(args.n_train):
                train_samples.append(prepare_torch_sample(generate_offgrid_tensor_sample(
                    rng=rng, shape=shape, n_targets=l_value, snr_db=args.snr_db,
                    offset_radius=args.offset_radius), n_targets=l_value))
            for _ in range(args.n_test):
                test_by_l[l_value].append(prepare_torch_sample(generate_offgrid_tensor_sample(
                    rng=rng, shape=shape, n_targets=l_value, snr_db=args.snr_db,
                    offset_radius=args.offset_radius), n_targets=l_value))

        model, history = train_torch_axiswise_refinement_layer_fast(
            train_samples, shape=shape, epochs=args.epochs, lr=args.lr)
        alphas = model.alpha().detach().cpu().numpy()
        seed_gains = []
        seed_deltas = []
        for l_value, samples in test_by_l.items():
            result = evaluate_torch_axiswise_refinement_layer_fast(model, samples, shape=shape)
            shared_nmse = evaluate_fixed_alpha(samples, shape=shape, alpha=shared_alpha)
            delta_vs_shared = shared_nmse - result["axiswise_nmse_db"]
            seed_gains.append(result["gain_vs_grid_db"])
            seed_deltas.append(delta_vs_shared)
            rows.append({
                "seed": float(seed), "l_value": float(l_value),
                "angle_alpha": result["angle_alpha"], "delay_alpha": result["delay_alpha"],
                "doppler_alpha": result["doppler_alpha"], "grid_nmse_db": result["grid_nmse_db"],
                "shared_alpha_nmse_db": shared_nmse, "axiswise_nmse_db": result["axiswise_nmse_db"],
                "axiswise_gain_vs_grid_db": result["gain_vs_grid_db"],
                "axiswise_gain_vs_shared_db": delta_vs_shared,
                "axiswise_gap_vs_full_refine_db": result["gap_vs_full_refine_db"],
            })
        seed_rows.append({
            "seed": float(seed), "angle_alpha": float(alphas[0]), "delay_alpha": float(alphas[1]),
            "doppler_alpha": float(alphas[2]), "mean_gain_vs_grid_db": finite_mean(seed_gains),
            "mean_gain_vs_shared_db": finite_mean(seed_deltas),
            "train_improvement_db": float(history[0] - history[-1]),
        })

    elapsed = time.perf_counter() - started
    gains_grid = [row["axiswise_gain_vs_grid_db"] for row in rows]
    gains_shared = [row["axiswise_gain_vs_shared_db"] for row in rows]
    metrics = {
        "claim_update": "supported-local" if min(gains_grid) >= 3.0 else "inconclusive-local",
        "tensor_shape": "128x16x32", "snr_db": args.snr_db,
        "seed_count": float(len(args.seeds)), "n_train_per_l": float(args.n_train),
        "n_test_per_l": float(args.n_test), "epochs": float(args.epochs),
        "shared_alpha": shared_alpha,
        "mean_angle_alpha": finite_mean([row["angle_alpha"] for row in seed_rows]),
        "mean_delay_alpha": finite_mean([row["delay_alpha"] for row in seed_rows]),
        "mean_doppler_alpha": finite_mean([row["doppler_alpha"] for row in seed_rows]),
        "mean_axiswise_gain_vs_grid_db": finite_mean(gains_grid),
        "min_axiswise_gain_vs_grid_db": float(min(gains_grid)),
        "mean_axiswise_gain_vs_shared_db": finite_mean(gains_shared),
        "min_axiswise_gain_vs_shared_db": float(min(gains_shared)),
        "elapsed_seconds": elapsed,
    }
    output = ROOT / "05_results" / args.output_dir_name
    output.mkdir(parents=True, exist_ok=True)
    for name, records in (("stage2_axiswise_cells.csv", rows), ("stage2_axiswise_seeds.csv", seed_rows)):
        with (output / name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(records[0].keys()))
            writer.writeheader()
            writer.writerows(records)
    command = subprocess.list2cmdline([sys.executable, str(Path(__file__).resolve().relative_to(ROOT)), *sys.argv[1:]])
    manifest = {
        "run_id": f"stage2_axiswise_tompnet_{len(args.seeds)}seed", "command": command,
        "config": vars(args) | {"shape": shape}, "metrics": metrics,
        "environment": environment_snapshot(ROOT),
        "notes": [
            "Axis order is angle, delay, Doppler; each alpha is bounded to (0, 1.2).",
            "Training uses source synthetic NMSE only; no Sionna CDL data or truth is used.",
            "The shared-alpha comparator is evaluated on identical held-out samples.",
        ],
    }
    (output / "run_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    summary = [
        "# Stage 2 Axiswise T-OMP-Net Source Training", "",
        f"- Claim update: {metrics['claim_update']}",
        f"- Mean learned angle/delay/Doppler alpha: {metrics['mean_angle_alpha']:.6g} / {metrics['mean_delay_alpha']:.6g} / {metrics['mean_doppler_alpha']:.6g}",
        f"- Mean/min gain vs grid: {metrics['mean_axiswise_gain_vs_grid_db']:.6g} / {metrics['min_axiswise_gain_vs_grid_db']:.6g} dB",
        f"- Mean/min gain vs shared alpha: {metrics['mean_axiswise_gain_vs_shared_db']:.6g} / {metrics['min_axiswise_gain_vs_shared_db']:.6g} dB",
        f"- Elapsed seconds: {elapsed:.2f}", "", "## Evaluation summary", "",
        "- research_question: Can source-only axiswise bounded refinement preserve local G2 gain while decoupling angle and delay for frozen external transfer?",
        f"- claim_update: {metrics['claim_update']}",
        "- baseline_relation: Grid and shared-alpha baselines use identical held-out synthetic samples.",
        "- failure_mode: If axis alphas collapse together or local gain falls below 3 dB, the richer parameterization is not justified.",
        "- next_action: Freeze mean source-trained angle/delay alphas and evaluate once on unchanged Sionna CDL.",
        "- evidence_level: Source-domain multi-seed development evidence; external validity is not implied.",
    ]
    text = "\n".join(summary) + "\n"
    (output / "summary.md").write_text(text, encoding="utf-8")
    (output / "evaluation_summary.md").write_text(text, encoding="utf-8")
    print(f"Wrote {(output / 'summary.md').relative_to(ROOT)}")
    for key in ("claim_update", "mean_angle_alpha", "mean_delay_alpha", "mean_doppler_alpha", "mean_axiswise_gain_vs_grid_db", "mean_axiswise_gain_vs_shared_db"):
        print(f"{key}={metrics[key]}")


if __name__ == "__main__":
    main()
