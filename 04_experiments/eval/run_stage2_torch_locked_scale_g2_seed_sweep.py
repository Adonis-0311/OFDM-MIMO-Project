from __future__ import annotations

import csv
from pathlib import Path
import sys
import time

import numpy as np
import torch
from scipy.stats import t

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_active_modules"))

from common.manifest import write_run_manifest, write_summary_md
from common.seed import seed_all
from data.offgrid_tensor import generate_offgrid_tensor_sample
from tompnet.torch_layer import (
    evaluate_torch_refinement_layer_fast,
    prepare_torch_sample,
    train_torch_refinement_layer_fast,
)


def finite_mean(values: list[float]) -> float:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    return float(np.mean(arr)) if arr.size else float("nan")


def finite_std(values: list[float]) -> float:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    return float(np.std(arr, ddof=1)) if arr.size > 1 else 0.0


def mean_ci95(values: list[float]) -> tuple[float, float]:
    arr = np.asarray(values, dtype=float)
    half = float(t.ppf(0.975, arr.size - 1) * np.std(arr, ddof=1) / np.sqrt(arr.size))
    center = float(np.mean(arr))
    return center - half, center + half


def run_one_seed(
    *,
    seed: int,
    shape: tuple[int, int, int],
    snr_db: float,
    l_values: list[int],
    n_train: int,
    n_test: int,
    epochs: int,
    lr: float,
    offset_radius: float,
) -> tuple[list[dict[str, float]], dict[str, float]]:
    rng = seed_all(seed)
    torch.manual_seed(seed)

    train_samples = []
    test_samples_by_l = {n_targets: [] for n_targets in l_values}
    for n_targets in l_values:
        for _ in range(n_train):
            train_samples.append(
                prepare_torch_sample(
                    generate_offgrid_tensor_sample(
                        rng=rng,
                        shape=shape,
                        n_targets=n_targets,
                        snr_db=snr_db,
                        offset_radius=offset_radius,
                    ),
                    n_targets=n_targets,
                )
            )
        for _ in range(n_test):
            test_samples_by_l[n_targets].append(
                prepare_torch_sample(
                    generate_offgrid_tensor_sample(
                        rng=rng,
                        shape=shape,
                        n_targets=n_targets,
                        snr_db=snr_db,
                        offset_radius=offset_radius,
                    ),
                    n_targets=n_targets,
                )
            )

    model, history = train_torch_refinement_layer_fast(
        train_samples,
        shape=shape,
        epochs=epochs,
        lr=lr,
    )

    rows: list[dict[str, float]] = []
    gains: list[float] = []
    for n_targets, samples in test_samples_by_l.items():
        metrics = evaluate_torch_refinement_layer_fast(model, samples, shape=shape)
        gains.append(metrics["gain_vs_grid_db"])
        rows.append(
            {
                "seed": float(seed),
                "n_targets": float(n_targets),
                "alpha": metrics["alpha"],
                "test_grid_nmse_db": metrics["grid_nmse_db"],
                "test_torch_nmse_db": metrics["torch_nmse_db"],
                "test_full_refine_nmse_db": metrics["full_refine_nmse_db"],
                "test_gain_vs_grid_db": metrics["gain_vs_grid_db"],
                "test_gap_vs_full_refine_db": metrics["gap_vs_full_refine_db"],
                "n_test": float(len(samples)),
            }
        )

    train_improvement = float(history[0] - history[-1]) if len(history) >= 2 else 0.0
    seed_summary = {
        "seed": float(seed),
        "alpha": float(model.alpha().detach().cpu().item()),
        "mean_test_gain_vs_grid_db": finite_mean(gains),
        "min_test_gain_vs_grid_db": float(min(gains)),
        "mean_train_improvement_db": train_improvement,
    }
    return rows, seed_summary


def write_evaluation_summary(
    output_dir: Path,
    *,
    metrics: dict[str, float | int | str | list[int]],
    elapsed_seconds: float,
) -> Path:
    status = (
        "supported"
        if float(metrics["min_l_cell_gain_vs_grid_db"]) >= 3.0
        and float(metrics["min_seed_mean_gain_vs_grid_db"]) >= 3.0
        else "inconclusive"
    )
    lines = [
        "# Stage 2 PyTorch Locked-Scale G2 Seed Sweep Evaluation Summary",
        "",
        "## Outcome Summary",
        "",
        (
            "This run repeats the locked-scale PyTorch trainable refinement gate across "
            "multiple random seeds at tensor shape `128x16x32` and L={2,4,8}. It is a "
            "paper-strengthening statistical check for the already accepted bounded G2 gate."
        ),
        "",
        "## evaluation_summary",
        "",
        "- `research_question`: Is the locked-scale PyTorch T-OMP-Net gain over grid Tensor-OMP stable across seeds at SNR=20 dB?",
        f"- `claim_update`: {status} for multi-seed locked-scale G2 stability.",
        "- `baseline_relation`: Compared against grid Tensor-OMP on the same held-out samples for every seed and L cell.",
        "- `failure_mode`: No execution failure if the run completes; remaining limitation is still CPU-scale synthetic sample count.",
        "- `next_action`: Use this as paper-strengthening evidence for G2, then prioritize narrowed A4 high-L validation or manuscript claim alignment.",
        "- `evidence_level`: Multi-seed local statistical strengthening, not external-channel validation.",
        "",
        "## Key Metrics",
        "",
        f"- Seeds: {metrics['seeds']}",
        f"- Mean L-cell gain over grid Tensor-OMP: {float(metrics['mean_l_cell_gain_vs_grid_db']):.4f} dB",
        f"- Std. L-cell gain over grid Tensor-OMP: {float(metrics['std_l_cell_gain_vs_grid_db']):.4f} dB",
        f"- Minimum L-cell gain over grid Tensor-OMP: {float(metrics['min_l_cell_gain_vs_grid_db']):.4f} dB",
        f"- Minimum per-seed mean gain: {float(metrics['min_seed_mean_gain_vs_grid_db']):.4f} dB",
        f"- Seed-mean gain 95% CI: [{float(metrics['seed_mean_gain_ci95_low_db']):.4f}, {float(metrics['seed_mean_gain_ci95_high_db']):.4f}] dB",
        f"- Mean train NMSE improvement: {float(metrics['mean_train_improvement_db']):.4f} dB",
        f"- Wall-clock elapsed time: {elapsed_seconds:.2f} s",
    ]
    path = output_dir / "evaluation_summary.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    shape = (128, 16, 32)
    snr_db = 20.0
    seeds = [20260624, 20260625, 20260626, 20260627, 20260628]
    l_values = [2, 4, 8]
    n_train = 2
    n_test = 30
    epochs = 6
    lr = 0.08
    offset_radius = 0.35
    started = time.perf_counter()

    all_rows: list[dict[str, float]] = []
    seed_rows: list[dict[str, float]] = []
    for seed in seeds:
        rows, seed_summary = run_one_seed(
            seed=seed,
            shape=shape,
            snr_db=snr_db,
            l_values=l_values,
            n_train=n_train,
            n_test=n_test,
            epochs=epochs,
            lr=lr,
            offset_radius=offset_radius,
        )
        all_rows.extend(rows)
        seed_rows.append(seed_summary)

    elapsed_seconds = time.perf_counter() - started
    gains = [float(row["test_gain_vs_grid_db"]) for row in all_rows]
    seed_mean_gains = [float(row["mean_test_gain_vs_grid_db"]) for row in seed_rows]
    train_improvements = [float(row["mean_train_improvement_db"]) for row in seed_rows]
    gain_ci95_low, gain_ci95_high = mean_ci95(seed_mean_gains)
    output_dir = ROOT / "05_results" / "stage2_torch_locked_scale_g2_seed_sweep_paper_30test"
    output_dir.mkdir(parents=True, exist_ok=True)

    cell_csv = output_dir / "stage2_torch_locked_scale_g2_seed_sweep_cells.csv"
    with cell_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(all_rows[0].keys()))
        writer.writeheader()
        writer.writerows(all_rows)

    seed_csv = output_dir / "stage2_torch_locked_scale_g2_seed_sweep_seeds.csv"
    with seed_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(seed_rows[0].keys()))
        writer.writeheader()
        writer.writerows(seed_rows)

    metrics = {
        "tensor_shape": "128x16x32",
        "snr_db": snr_db,
        "torch_version": torch.__version__,
        "seeds": seeds,
        "l_values": l_values,
        "n_train_per_l": n_train,
        "n_test_per_l": n_test,
        "epochs": epochs,
        "lr": lr,
        "mean_l_cell_gain_vs_grid_db": finite_mean(gains),
        "std_l_cell_gain_vs_grid_db": finite_std(gains),
        "min_l_cell_gain_vs_grid_db": float(min(gains)),
        "max_l_cell_gain_vs_grid_db": float(max(gains)),
        "min_seed_mean_gain_vs_grid_db": float(min(seed_mean_gains)),
        "seed_mean_gain_ci95_low_db": gain_ci95_low,
        "seed_mean_gain_ci95_high_db": gain_ci95_high,
        "mean_train_improvement_db": finite_mean(train_improvements),
        "elapsed_seconds": elapsed_seconds,
    }
    notes = [
        "Multi-seed strengthening for the bounded local G2 gate; it does not replace external-channel validation.",
        "The baseline remains grid Tensor-OMP on the same held-out samples for every seed and L cell.",
        "The paper-scale strengthening uses 30 held-out scenes per L and seed (450 held-out scenes total).",
    ]
    manifest_path = write_run_manifest(
        output_dir,
        run_id="stage2_torch_locked_scale_g2_seed_sweep_paper_30test_20260630",
        command="python 04_experiments/eval/run_stage2_torch_locked_scale_g2_seed_sweep.py",
        config={
            "shape": shape,
            "snr_db": snr_db,
            "seeds": seeds,
            "l_values": l_values,
            "n_train": n_train,
            "n_test": n_test,
            "epochs": epochs,
            "lr": lr,
            "offset_radius": offset_radius,
        },
        metrics=metrics,
        notes=notes,
        cwd=ROOT,
    )
    summary_path = write_summary_md(
        output_dir,
        title="Stage 2 PyTorch Locked-Scale G2 Seed Sweep",
        config_hash="stage2-torch-locked-scale-g2-seed-sweep-20260625",
        metrics=metrics,
        notes=notes,
        artifacts=[
            str(cell_csv.relative_to(ROOT)),
            str(seed_csv.relative_to(ROOT)),
            str(manifest_path.relative_to(ROOT)),
        ],
    )
    evaluation_path = write_evaluation_summary(
        output_dir,
        metrics=metrics,
        elapsed_seconds=elapsed_seconds,
    )
    print(f"Wrote {cell_csv.relative_to(ROOT)}")
    print(f"Wrote {seed_csv.relative_to(ROOT)}")
    print(f"Wrote {summary_path.relative_to(ROOT)}")
    print(f"Wrote {manifest_path.relative_to(ROOT)}")
    print(f"Wrote {evaluation_path.relative_to(ROOT)}")
    print(f"min_l_cell_gain_vs_grid_db={metrics['min_l_cell_gain_vs_grid_db']:.4f}")
    print(f"mean_l_cell_gain_vs_grid_db={metrics['mean_l_cell_gain_vs_grid_db']:.4f}")


if __name__ == "__main__":
    main()
