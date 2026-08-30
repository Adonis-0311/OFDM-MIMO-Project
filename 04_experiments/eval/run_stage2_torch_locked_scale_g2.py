from __future__ import annotations

import csv
from pathlib import Path
import sys
import time

import numpy as np
import torch

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


def write_evaluation_summary(
    output_dir: Path,
    *,
    mean_gain: float,
    min_gain: float,
    train_improvement: float,
    elapsed_seconds: float,
) -> Path:
    status = "supported" if mean_gain >= 3.0 and min_gain >= 3.0 else "inconclusive"
    lines = [
        "# Stage 2 PyTorch Locked-Scale G2 Evaluation Summary",
        "",
        "## Outcome Summary",
        "",
        (
            "The locked-scale PyTorch G2 run trains a real `nn.Module` bounded off-grid "
            "refinement layer with Adam at tensor shape `128x16x32` across the curriculum "
            "`L={2,4,8}`. The optimized loss keeps the same LS-estimator objective but "
            "uses normal equations so CPU execution is feasible."
        ),
        "",
        "## evaluation_summary",
        "",
        "- `research_question`: Can the PyTorch trainable T-OMP-Net refinement path run at the locked Stage-2 scale and beat grid Tensor-OMP on held-out SNR=20 dB samples?",
        f"- `claim_update`: {status} for locked-scale PyTorch G2 evidence.",
        "- `baseline_relation`: Compared against grid Tensor-OMP on the same held-out samples for each L cell.",
        "- `failure_mode`: No execution failure in the optimized normal-equation PyTorch path; remaining limitation is small CPU sample count.",
        "- `next_action`: Run a G2 acceptance audit or expand seeds/test counts if stronger statistical evidence is required before Stage 3.",
        "- `evidence_level`: Locked-scale PyTorch trainable evidence achieved; broader statistical campaign remains optional polish.",
        "",
        "## Key Metrics",
        "",
        "- Tensor shape: 128x16x32",
        "- L curriculum: {2,4,8}",
        f"- Mean held-out gain over grid Tensor-OMP: {mean_gain:.4f} dB",
        f"- Minimum held-out L-cell gain: {min_gain:.4f} dB",
        f"- Mean train NMSE improvement: {train_improvement:.4f} dB",
        f"- Wall-clock elapsed time: {elapsed_seconds:.2f} s",
    ]
    path = output_dir / "evaluation_summary.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    shape = (128, 16, 32)
    snr_db = 20.0
    seed = 20260624
    l_values = [2, 4, 8]
    n_train = 2
    n_test = 2
    epochs = 6
    lr = 0.08
    offset_radius = 0.35
    rng = seed_all(seed)
    torch.manual_seed(seed)
    started = time.perf_counter()

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

    elapsed_seconds = time.perf_counter() - started
    output_dir = ROOT / "05_results" / "stage2_torch_locked_scale_g2"
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "stage2_torch_locked_scale_g2.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    history_path = output_dir / "train_history.csv"
    with history_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["epoch", "train_nmse_db"])
        writer.writeheader()
        for epoch, train_nmse_db in enumerate(history, start=1):
            writer.writerow({"epoch": epoch, "train_nmse_db": train_nmse_db})

    train_improvement = float(history[0] - history[-1]) if len(history) >= 2 else 0.0
    metrics = {
        "tensor_shape": "128x16x32",
        "snr_db": snr_db,
        "torch_version": torch.__version__,
        "seed": seed,
        "l_values": l_values,
        "n_train_per_l": n_train,
        "n_test_per_l": n_test,
        "epochs": epochs,
        "lr": lr,
        "alpha": float(model.alpha().detach().cpu().item()),
        "mean_test_gain_vs_grid_db": finite_mean(gains),
        "min_test_gain_vs_grid_db": float(min(gains)),
        "mean_train_improvement_db": train_improvement,
        "elapsed_seconds": elapsed_seconds,
    }
    notes = [
        "Locked-scale PyTorch run uses nn.Module + Adam at 128x16x32 across L={2,4,8}.",
        "The fast loss is algebraically equivalent to the LS reconstruction loss but solves LxL normal equations instead of a tall 65536xL least-squares problem.",
        "This run addresses the previous PyTorch locked-scale CPU blocker; sample count remains deliberately small for a bounded local G2 gate run.",
    ]
    manifest_path = write_run_manifest(
        output_dir,
        run_id="stage2_torch_locked_scale_g2_20260624",
        command="python 04_experiments/eval/run_stage2_torch_locked_scale_g2.py",
        config={
            "shape": shape,
            "snr_db": snr_db,
            "seed": seed,
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
        title="Stage 2 PyTorch Locked-Scale G2 Run",
        config_hash="stage2-torch-locked-scale-g2-20260624",
        metrics=metrics,
        notes=notes,
        artifacts=[
            str(csv_path.relative_to(ROOT)),
            str(history_path.relative_to(ROOT)),
            str(manifest_path.relative_to(ROOT)),
        ],
    )
    evaluation_path = write_evaluation_summary(
        output_dir,
        mean_gain=float(metrics["mean_test_gain_vs_grid_db"]),
        min_gain=float(metrics["min_test_gain_vs_grid_db"]),
        train_improvement=train_improvement,
        elapsed_seconds=elapsed_seconds,
    )
    print(f"Wrote {csv_path.relative_to(ROOT)}")
    print(f"Wrote {history_path.relative_to(ROOT)}")
    print(f"Wrote {summary_path.relative_to(ROOT)}")
    print(f"Wrote {manifest_path.relative_to(ROOT)}")
    print(f"Wrote {evaluation_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
