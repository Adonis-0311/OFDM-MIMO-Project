from __future__ import annotations

import csv
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_active_modules"))

from common.manifest import write_run_manifest, write_summary_md
from common.seed import seed_all
from data.offgrid_tensor import generate_offgrid_tensor_sample
from tompnet.trainable import evaluate_calibrated_refinement, train_alpha_grid


def finite_mean(values: list[float]) -> float:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    return float(np.mean(arr)) if arr.size else float("nan")


def main() -> None:
    shape = (128, 16, 32)
    snr_db = 20.0
    seed = 20260624
    n_train = 5
    n_test = 6
    offset_radius = 0.35
    candidate_alphas = np.linspace(0.0, 1.2, 13)
    rng = seed_all(seed)
    rows: list[dict[str, float]] = []
    for n_targets in (2, 4, 8):
        train_samples = [
            generate_offgrid_tensor_sample(
                rng=rng,
                shape=shape,
                n_targets=n_targets,
                snr_db=snr_db,
                offset_radius=offset_radius,
            )
            for _ in range(n_train)
        ]
        test_samples = [
            generate_offgrid_tensor_sample(
                rng=rng,
                shape=shape,
                n_targets=n_targets,
                snr_db=snr_db,
                offset_radius=offset_radius,
            )
            for _ in range(n_test)
        ]
        calibration = train_alpha_grid(
            train_samples,
            n_targets=n_targets,
            candidate_alphas=candidate_alphas,
        )
        grid_values = [
            evaluate_calibrated_refinement(sample, n_targets=n_targets, alpha=0.0)
            for sample in test_samples
        ]
        trained_values = [
            evaluate_calibrated_refinement(sample, n_targets=n_targets, alpha=calibration.alpha)
            for sample in test_samples
        ]
        full_refine_values = [
            evaluate_calibrated_refinement(sample, n_targets=n_targets, alpha=1.0)
            for sample in test_samples
        ]
        rows.append(
            {
                "n_targets": float(n_targets),
                "trained_alpha": calibration.alpha,
                "train_nmse_db": calibration.train_nmse_db,
                "test_grid_nmse_db": finite_mean(grid_values),
                "test_trained_nmse_db": finite_mean(trained_values),
                "test_full_refine_nmse_db": finite_mean(full_refine_values),
                "test_gain_vs_grid_db": finite_mean(grid_values) - finite_mean(trained_values),
                "test_gap_vs_full_refine_db": finite_mean(trained_values) - finite_mean(full_refine_values),
            }
        )

    output_dir = ROOT / "05_results" / "stage2_trainable_tompnet_smoke"
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "stage2_trainable_tompnet_smoke.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    metrics = {
        "tensor_shape": "128x16x32",
        "snr_db": snr_db,
        "n_train_per_l": n_train,
        "n_test_per_l": n_test,
        "mean_test_gain_vs_grid_db": finite_mean(
            [float(row["test_gain_vs_grid_db"]) for row in rows]
        ),
        "min_test_gain_vs_grid_db": float(min(float(row["test_gain_vs_grid_db"]) for row in rows)),
        "mean_abs_gap_vs_full_refine_db": finite_mean(
            [abs(float(row["test_gap_vs_full_refine_db"])) for row in rows]
        ),
    }
    notes = [
        "NumPy trainable smoke learns a bounded off-grid interpolation alpha over curriculum L values.",
        "This is a parameterized/training-path proof of wiring because PyTorch is unavailable in the current environment.",
        "Full G2 still requires the planned trainable T-OMP-Net layer/curriculum implementation once PyTorch is installed.",
    ]
    manifest_path = write_run_manifest(
        output_dir,
        run_id="stage2_trainable_tompnet_smoke_20260624",
        command="python 04_experiments/eval/run_stage2_trainable_tompnet_smoke.py",
        config={
            "shape": shape,
            "snr_db": snr_db,
            "seed": seed,
            "n_train": n_train,
            "n_test": n_test,
            "offset_radius": offset_radius,
            "candidate_alphas": candidate_alphas.tolist(),
        },
        metrics=metrics,
        notes=notes,
        cwd=ROOT,
    )
    write_summary_md(
        output_dir,
        title="Stage 2 Trainable T-OMP-Net Smoke",
        config_hash="stage2-trainable-alpha-20260624",
        metrics=metrics,
        notes=notes,
        artifacts=[str(csv_path.relative_to(ROOT)), str(manifest_path.relative_to(ROOT))],
    )


if __name__ == "__main__":
    main()

