from __future__ import annotations

import csv
from pathlib import Path
import sys

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_active_modules"))

from common.manifest import write_run_manifest, write_summary_md
from common.seed import seed_all
from data.offgrid_tensor import generate_offgrid_tensor_sample
from tompnet.torch_layer import (
    evaluate_torch_refinement_layer,
    prepare_torch_sample,
    train_torch_refinement_layer,
)


def finite_mean(values: list[float]) -> float:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    return float(np.mean(arr)) if arr.size else float("nan")


def main() -> None:
    shape = (32, 4, 8)
    snr_db = 20.0
    seed = 20260624
    n_train = 2
    n_test = 2
    epochs = 8
    lr = 0.10
    offset_radius = 0.35
    rng = seed_all(seed)
    torch.manual_seed(seed)
    rows: list[dict[str, float]] = []
    histories: dict[str, list[float]] = {}
    for n_targets in (2, 4):
        train_samples = [
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
            for _ in range(n_train)
        ]
        test_samples = [
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
            for _ in range(n_test)
        ]
        model, history = train_torch_refinement_layer(
            train_samples,
            shape=shape,
            epochs=epochs,
            lr=lr,
        )
        histories[str(n_targets)] = history
        metrics = evaluate_torch_refinement_layer(model, test_samples, shape=shape)
        rows.append(
            {
                "n_targets": float(n_targets),
                "alpha": metrics["alpha"],
                "train_start_nmse_db": history[0],
                "train_end_nmse_db": history[-1],
                "test_grid_nmse_db": metrics["grid_nmse_db"],
                "test_torch_nmse_db": metrics["torch_nmse_db"],
                "test_full_refine_nmse_db": metrics["full_refine_nmse_db"],
                "test_gain_vs_grid_db": metrics["gain_vs_grid_db"],
                "test_gap_vs_full_refine_db": metrics["gap_vs_full_refine_db"],
            }
        )

    output_dir = ROOT / "05_results" / "stage2_torch_tompnet_smoke"
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "stage2_torch_tompnet_smoke.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    metrics = {
        "tensor_shape": "32x4x8",
        "snr_db": snr_db,
        "torch_version": torch.__version__,
        "epochs": epochs,
        "n_train_per_l": n_train,
        "n_test_per_l": n_test,
        "mean_test_gain_vs_grid_db": finite_mean(
            [float(row["test_gain_vs_grid_db"]) for row in rows]
        ),
        "min_test_gain_vs_grid_db": float(min(float(row["test_gain_vs_grid_db"]) for row in rows)),
        "mean_train_improvement_db": finite_mean(
            [float(row["train_start_nmse_db"]) - float(row["train_end_nmse_db"]) for row in rows]
        ),
    }
    notes = [
        "PyTorch CPU trainable smoke uses nn.Module + Adam to learn bounded off-grid alpha from train samples.",
        "Top-k support initialization is fixed from Tensor-OMP; differentiability covers off-grid atom positions and LS reconstruction.",
        "This is a bounded G2 smoke, not the final full T-OMP-Net training campaign.",
    ]
    manifest_path = write_run_manifest(
        output_dir,
        run_id="stage2_torch_tompnet_smoke_20260624",
        command="python 04_experiments/eval/run_stage2_torch_tompnet_smoke.py",
        config={
            "shape": shape,
            "snr_db": snr_db,
            "seed": seed,
            "n_train": n_train,
            "n_test": n_test,
            "epochs": epochs,
            "lr": lr,
            "offset_radius": offset_radius,
            "l_values": [2, 4],
        },
        metrics=metrics,
        notes=notes,
        cwd=ROOT,
    )
    write_summary_md(
        output_dir,
        title="Stage 2 PyTorch T-OMP-Net Smoke",
        config_hash="stage2-torch-tompnet-20260624",
        metrics=metrics,
        notes=notes,
        artifacts=[str(csv_path.relative_to(ROOT)), str(manifest_path.relative_to(ROOT))],
    )


if __name__ == "__main__":
    main()
