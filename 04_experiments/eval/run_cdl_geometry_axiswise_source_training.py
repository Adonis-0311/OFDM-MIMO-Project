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
sys.path.insert(0, str(Path(__file__).resolve().parent))

from common.manifest import environment_snapshot
from common.seed import seed_all
from run_sionna_cdl_trained_refinement import (
    atom_2d,
    estimate_from_bins_lstsq,
    finite_mean,
    refine_bins_local,
    support_to_bins,
)
from run_sionna_cdl_profile_generalization import reconstruct_fft_topk


class Axiswise2DLayer(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        initial = np.asarray([0.5, 0.5]) / 1.2
        self.alpha_raw = torch.nn.Parameter(torch.as_tensor(
            np.log(initial / (1.0 - initial)), dtype=torch.float64))

    def alpha(self) -> torch.Tensor:
        return 1.2 * torch.sigmoid(self.alpha_raw)


def torch_atom_2d(shape: tuple[int, int], bins: torch.Tensor) -> torch.Tensor:
    delay_index = torch.arange(shape[0], dtype=torch.float64)
    angle_index = torch.arange(shape[1], dtype=torch.float64)
    delay = torch.exp(2j * torch.pi * delay_index * bins[0] / shape[0]) / np.sqrt(shape[0])
    angle = torch.exp(2j * torch.pi * angle_index * bins[1] / shape[1]) / np.sqrt(shape[1])
    return (delay[:, None] * angle[None, :]).reshape(-1)


def differentiable_nmse(
    coarse: torch.Tensor,
    refined: torch.Tensor,
    measurement: torch.Tensor,
    clean: torch.Tensor,
    shape: tuple[int, int],
    alpha: torch.Tensor,
) -> torch.Tensor:
    bins = coarse + alpha * (refined - coarse)
    design = torch.stack([torch_atom_2d(shape, bins[index]) for index in range(len(bins))], dim=1)
    gram = design.conj().T @ design
    rhs = design.conj().T @ measurement.reshape(-1)
    eye = torch.eye(len(bins), dtype=gram.dtype)
    coefficients = torch.linalg.solve(gram + 1e-8 * eye, rhs)
    estimate = design @ coefficients
    clean_vector = clean.reshape(-1)
    return torch.sum(torch.abs(estimate - clean_vector) ** 2) / torch.sum(torch.abs(clean_vector) ** 2)


def make_sample(
    rng: np.random.Generator,
    *,
    shape: tuple[int, int],
    l_value: int,
    snr_db: float,
    offset_radius: float,
    search_radius: float,
    search_points: int,
) -> dict[str, np.ndarray | float]:
    flat_support = rng.choice(np.prod(shape), size=l_value, replace=False)
    base_bins = np.asarray([np.unravel_index(int(index), shape) for index in flat_support], dtype=float)
    true_bins = base_bins + rng.uniform(-offset_radius, offset_radius, size=(l_value, 2))
    gains = (rng.standard_normal(l_value) + 1j * rng.standard_normal(l_value)) / np.sqrt(2)
    clean = sum(gain * atom_2d(shape, tuple(bins)) for gain, bins in zip(gains, true_bins))
    signal_power = float(np.mean(np.abs(clean) ** 2))
    noise_variance = signal_power / (10.0 ** (snr_db / 10.0))
    noise = np.sqrt(noise_variance / 2.0) * (
        rng.standard_normal(shape) + 1j * rng.standard_normal(shape))
    measurement = clean + noise
    _, support, _ = reconstruct_fft_topk(measurement, l_value)
    coarse = support_to_bins(support, shape)
    refined = refine_bins_local(
        measurement, coarse, search_radius=search_radius, search_points=search_points)
    return {
        "coarse": coarse,
        "refined": refined,
        "measurement": measurement,
        "clean": clean,
        "truth_bins": true_bins,
    }


def loss_for_sample(sample: dict, shape: tuple[int, int], alpha: torch.Tensor) -> torch.Tensor:
    return differentiable_nmse(
        torch.as_tensor(sample["coarse"], dtype=torch.float64),
        torch.as_tensor(sample["refined"], dtype=torch.float64),
        torch.as_tensor(sample["measurement"], dtype=torch.complex128),
        torch.as_tensor(sample["clean"], dtype=torch.complex128),
        shape,
        alpha,
    )


def evaluate(samples: list[dict], shape: tuple[int, int], alpha: np.ndarray) -> tuple[float, float]:
    grid_values = []
    model_values = []
    for sample in samples:
        coarse = np.asarray(sample["coarse"])
        refined = np.asarray(sample["refined"])
        model_bins = coarse + alpha * (refined - coarse)
        grid = estimate_from_bins_lstsq(np.asarray(sample["measurement"]), coarse)
        model = estimate_from_bins_lstsq(np.asarray(sample["measurement"]), model_bins)
        clean = np.asarray(sample["clean"])
        denominator = max(float(np.linalg.norm(clean) ** 2), 1e-300)
        grid_values.append(10 * np.log10(max(float(np.linalg.norm(grid-clean) ** 2) / denominator, 1e-300)))
        model_values.append(10 * np.log10(max(float(np.linalg.norm(model-clean) ** 2) / denominator, 1e-300)))
    return finite_mean(grid_values), finite_mean(model_values)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", nargs="+", type=int, default=[20260624, 20260625, 20260626, 20260627, 20260628])
    parser.add_argument("--snrs", nargs="+", type=float, default=[0.0, 10.0, 20.0, 30.0])
    parser.add_argument("--l-values", nargs="+", type=int, default=[4, 8, 16])
    parser.add_argument("--n-train", type=int, default=3)
    parser.add_argument("--n-test", type=int, default=6)
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--lr", type=float, default=0.06)
    parser.add_argument("--offset-radius", type=float, default=0.35)
    parser.add_argument("--search-radius", type=float, default=0.45)
    parser.add_argument("--search-points", type=int, default=5)
    parser.add_argument("--output-dir-name", default="cdl_geometry_axiswise_source_training")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    shape = (64, 4)
    started = time.perf_counter()
    cell_rows = []
    seed_rows = []
    for seed in args.seeds:
        rng = seed_all(seed)
        torch.manual_seed(seed)
        train_samples = []
        test_cells = {}
        for snr_db in args.snrs:
            for l_value in args.l_values:
                train_samples.extend([make_sample(
                    rng, shape=shape, l_value=l_value, snr_db=snr_db,
                    offset_radius=args.offset_radius, search_radius=args.search_radius,
                    search_points=args.search_points) for _ in range(args.n_train)])
                test_cells[(snr_db, l_value)] = [make_sample(
                    rng, shape=shape, l_value=l_value, snr_db=snr_db,
                    offset_radius=args.offset_radius, search_radius=args.search_radius,
                    search_points=args.search_points) for _ in range(args.n_test)]
        model = Axiswise2DLayer()
        optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
        history = []
        for _ in range(args.epochs):
            optimizer.zero_grad()
            loss = torch.stack([loss_for_sample(sample, shape, model.alpha()) for sample in train_samples]).mean()
            loss.backward()
            optimizer.step()
            history.append(float(10 * torch.log10(torch.clamp(loss.detach(), min=1e-30))))
        alpha = model.alpha().detach().cpu().numpy()
        seed_gains = []
        for (snr_db, l_value), samples in test_cells.items():
            grid_nmse, model_nmse = evaluate(samples, shape, alpha)
            gain = grid_nmse - model_nmse
            seed_gains.append(gain)
            cell_rows.append({
                "seed": float(seed), "snr_db": float(snr_db), "l_value": float(l_value),
                "delay_alpha": float(alpha[0]), "angle_alpha": float(alpha[1]),
                "grid_nmse_db": grid_nmse, "axiswise_nmse_db": model_nmse,
                "gain_vs_grid_db": gain,
            })
        seed_rows.append({
            "seed": float(seed), "delay_alpha": float(alpha[0]), "angle_alpha": float(alpha[1]),
            "mean_gain_vs_grid_db": finite_mean(seed_gains),
            "min_gain_vs_grid_db": float(min(seed_gains)),
            "train_improvement_db": history[0] - history[-1],
        })
    elapsed = time.perf_counter() - started
    gains = [row["gain_vs_grid_db"] for row in cell_rows]
    metrics = {
        "claim_update": "supported-source" if finite_mean(gains) > 0 and min(gains) > -0.5 else "mixed-source",
        "shape": "64x4", "seed_count": float(len(args.seeds)),
        "mean_delay_alpha": finite_mean([row["delay_alpha"] for row in seed_rows]),
        "mean_angle_alpha": finite_mean([row["angle_alpha"] for row in seed_rows]),
        "mean_axis_separation": finite_mean([row["delay_alpha"]-row["angle_alpha"] for row in seed_rows]),
        "mean_gain_vs_grid_db": finite_mean(gains), "min_cell_gain_vs_grid_db": float(min(gains)),
        "elapsed_seconds": elapsed,
    }
    output = ROOT / "05_results" / args.output_dir_name
    output.mkdir(parents=True, exist_ok=True)
    for name, records in (("source_cells.csv", cell_rows), ("source_seeds.csv", seed_rows)):
        with (output / name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(records[0].keys()))
            writer.writeheader()
            writer.writerows(records)
    command = subprocess.list2cmdline([sys.executable, str(Path(__file__).resolve().relative_to(ROOT)), *sys.argv[1:]])
    manifest = {
        "run_id": f"cdl_geometry_axiswise_source_{len(args.seeds)}seed", "command": command,
        "config": vars(args) | {"shape": shape}, "metrics": metrics,
        "environment": environment_snapshot(ROOT),
        "notes": [
            "Training data are synthetic and independent of Sionna CDL.",
            "Only observation geometry, SNR grid, and support budgets match the frozen external contract.",
            "Axis order is delay then projected angle.",
        ],
    }
    (output / "run_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# CDL-Geometry Axiswise Synthetic Source Training", "",
        f"- Claim update: {metrics['claim_update']}",
        f"- Mean delay/angle alpha: {metrics['mean_delay_alpha']:.6g} / {metrics['mean_angle_alpha']:.6g}",
        f"- Mean axis separation: {metrics['mean_axis_separation']:.6g}",
        f"- Mean/min cell gain vs grid: {metrics['mean_gain_vs_grid_db']:.6g} / {metrics['min_cell_gain_vs_grid_db']:.6g} dB",
        f"- Elapsed seconds: {elapsed:.2f}", "", "## Evaluation summary", "",
        "- research_question: Does source-only training at the external observation geometry learn a defensible frozen delay/angle refinement layer?",
        f"- claim_update: {metrics['claim_update']}",
        "- baseline_relation: Grid baseline and axiswise layer use identical held-out synthetic samples.",
        "- failure_mode: Weak axis separation or negative cells indicate geometry matching alone is insufficient.",
        "- next_action: Freeze mean alphas and evaluate once on Sionna CDL only if the source gate is credible.",
        "- evidence_level: Synthetic geometry-matched source training; no external performance claim.",
    ]
    text = "\n".join(lines) + "\n"
    (output / "summary.md").write_text(text, encoding="utf-8")
    (output / "evaluation_summary.md").write_text(text, encoding="utf-8")
    print(f"Wrote {(output / 'summary.md').relative_to(ROOT)}")
    for key in ("claim_update", "mean_delay_alpha", "mean_angle_alpha", "mean_axis_separation", "mean_gain_vs_grid_db", "min_cell_gain_vs_grid_db"):
        print(f"{key}={metrics[key]}")


if __name__ == "__main__":
    main()
