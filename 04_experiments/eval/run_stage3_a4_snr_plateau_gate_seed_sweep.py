from __future__ import annotations

import csv
from pathlib import Path
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_active_modules"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from common.manifest import write_run_manifest, write_summary_md
from common.seed import seed_all
from run_stage3_a4_high_l_plateau_gate import (
    choose_threshold,
    evaluate_threshold,
    plateau_gate_depth,
    run_depth_curve,
)


def finite_mean(values: list[float]) -> float:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    return float(np.mean(arr)) if arr.size else float("nan")


def finite_std(values: list[float]) -> float:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    return float(np.std(arr, ddof=1)) if arr.size > 1 else 0.0


def run_one_cell(
    *,
    seed: int,
    snr_db: float,
    shape: tuple[int, int, int],
    n_targets: int,
    offset_radius: float,
    radii: list[float],
    search_points: int,
    n_train: int,
    n_test: int,
    fixed_depth: int,
    min_depth: int,
    thresholds: list[float],
    tolerance_db: float,
) -> tuple[dict[str, float], list[dict[str, float]]]:
    rng = seed_all(seed + int(round(snr_db * 100.0)))
    train_curves = [
        run_depth_curve(
            rng=rng,
            shape=shape,
            n_targets=n_targets,
            snr_db=snr_db,
            offset_radius=offset_radius,
            radii=radii,
            search_points=search_points,
        )
        for _ in range(n_train)
    ]
    test_curves = [
        run_depth_curve(
            rng=rng,
            shape=shape,
            n_targets=n_targets,
            snr_db=snr_db,
            offset_radius=offset_radius,
            radii=radii,
            search_points=search_points,
        )
        for _ in range(n_test)
    ]

    threshold, train_metrics, _ = choose_threshold(
        train_curves,
        thresholds=thresholds,
        min_depth=min_depth,
        fixed_depth=fixed_depth,
        tolerance_db=tolerance_db,
    )
    test_metrics = evaluate_threshold(
        test_curves,
        threshold_db=threshold,
        min_depth=min_depth,
        fixed_depth=fixed_depth,
    )

    sample_rows: list[dict[str, float]] = []
    for sample_index, curve in enumerate(test_curves):
        depth = plateau_gate_depth(
            curve,
            threshold_db=threshold,
            min_depth=min_depth,
            fixed_depth=fixed_depth,
        )
        sample_rows.append(
            {
                "seed": float(seed),
                "snr_db": float(snr_db),
                "sample_index": float(sample_index),
                "selected_threshold_db": threshold,
                "gate_depth": float(depth),
                "gate_nmse_db": curve[depth],
                "fixed_depth_nmse_db": curve[fixed_depth],
                "gate_gap_vs_fixed_db": curve[depth] - curve[fixed_depth],
                "gate_depth_savings_percent": 100.0 * (fixed_depth - depth) / fixed_depth,
            }
        )

    cell = {
        "seed": float(seed),
        "snr_db": float(snr_db),
        "selected_threshold_db": threshold,
        "train_mean_depth_savings_percent": float(train_metrics["mean_depth_savings_percent"]),
        "train_mean_nmse_gap_db": float(train_metrics["mean_nmse_gap_db"]),
        "test_mean_depth": float(test_metrics["mean_depth"]),
        "test_mean_depth_savings_percent": float(test_metrics["mean_depth_savings_percent"]),
        "test_min_depth_savings_percent": float(test_metrics["min_depth_savings_percent"]),
        "test_mean_nmse_gap_db": float(test_metrics["mean_nmse_gap_db"]),
    }
    return cell, sample_rows


def summarize_by_snr(cell_rows: list[dict[str, float]], snr_values: list[float]) -> list[dict[str, float]]:
    summary_rows: list[dict[str, float]] = []
    for snr_db in snr_values:
        rows = [row for row in cell_rows if abs(float(row["snr_db"]) - snr_db) < 1e-9]
        savings = [float(row["test_mean_depth_savings_percent"]) for row in rows]
        gaps = [float(row["test_mean_nmse_gap_db"]) for row in rows]
        summary_rows.append(
            {
                "snr_db": float(snr_db),
                "mean_depth_savings_percent": finite_mean(savings),
                "std_depth_savings_percent": finite_std(savings),
                "min_depth_savings_percent": float(min(savings)),
                "mean_nmse_gap_db": finite_mean(gaps),
                "max_nmse_gap_db": float(max(gaps)),
                "n_seed_cells": float(len(rows)),
            }
        )
    return summary_rows


def write_evaluation_summary(
    output_dir: Path,
    *,
    metrics: dict[str, float | int | str | list[int] | list[float]],
    snr_summary_rows: list[dict[str, float]],
    elapsed_seconds: float,
) -> Path:
    min_savings = min(float(row["mean_depth_savings_percent"]) for row in snr_summary_rows)
    max_gap = max(float(row["max_nmse_gap_db"]) for row in snr_summary_rows)
    status = (
        "supported"
        if min_savings >= 25.0 and max_gap <= float(metrics["nmse_tolerance_db"])
        else "inconclusive"
    )
    if status == "supported":
        claim_note = (
            "The plateau gate keeps the SNR-sweep mean savings above 25% while staying "
            "within the NMSE tolerance for L=32."
        )
        next_action = "Use this as robustness support for the narrowed high-L A4 early-stop claim."
    else:
        claim_note = (
            "The SNR sweep exposes a boundary for the scalar plateau gate under the current "
            "small-sample contract."
        )
        next_action = "Keep A4 narrowed and report the failing SNR cells instead of claiming SNR-robust early stopping."
    lines = [
        "# Stage 3 A4 SNR Plateau Gate Seed Sweep Evaluation Summary",
        "",
        "## Outcome Summary",
        "",
        (
            "This run tests whether the narrowed high-L plateau early-stop gate remains "
            "stable across SNR={10,20,30} dB at L=32 and tensor shape `128x16x32`."
        ),
        "",
        "## evaluation_summary",
        "",
        "- `research_question`: Does the A4 plateau gate keep useful depth/FLOPs savings across SNR={10,20,30} dB for L=32?",
        f"- `claim_update`: {status} for SNR-sweep A4 robustness evidence.",
        "- `baseline_relation`: Fixed-depth K=8 repeated off-grid refinement is the comparator for each seed and SNR cell.",
        "- `failure_mode`: No execution failure if complete; remaining limitation is small local synthetic sample count.",
        f"- `mechanism_note`: {claim_note}",
        f"- `next_action`: {next_action}",
        "- `evidence_level`: SNR-axis local synthetic strengthening, not a global IA-AUD proof.",
        "",
        "## Key Metrics",
        "",
        f"- Seeds: {metrics['seeds']}",
        f"- SNR values: {metrics['snr_values_db']}",
        f"- Minimum mean depth/FLOPs savings over SNR cells: {min_savings:.4f}%",
        f"- Maximum mean NMSE gap over SNR cells: {max_gap:.4f} dB",
        f"- Overall mean cell depth/FLOPs savings: {float(metrics['overall_mean_cell_depth_savings_percent']):.4f}%",
        f"- Overall mean cell NMSE gap: {float(metrics['overall_mean_cell_nmse_gap_db']):.4f} dB",
        f"- Wall-clock elapsed time: {elapsed_seconds:.2f} s",
        "",
        "## SNR Summary",
        "",
        "| SNR (dB) | Mean savings (%) | Min savings (%) | Mean gap (dB) | Max gap (dB) |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in snr_summary_rows:
        lines.append(
            "| "
            f"{row['snr_db']:.1f} | "
            f"{row['mean_depth_savings_percent']:.4f} | "
            f"{row['min_depth_savings_percent']:.4f} | "
            f"{row['mean_nmse_gap_db']:.4f} | "
            f"{row['max_nmse_gap_db']:.4f} |"
        )
    path = output_dir / "evaluation_summary.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    shape = (128, 16, 32)
    n_targets = 32
    snr_values = [10.0, 20.0, 30.0]
    seeds = [20260624, 20260625]
    n_train = 2
    n_test = 2
    offset_radius = 0.35
    radii = [0.45, 0.28, 0.18, 0.11, 0.07, 0.045, 0.03, 0.02]
    search_points = 3
    fixed_depth = len(radii)
    min_depth = 3
    tolerance_db = 0.5
    thresholds = [0.05, 0.1, 0.2, 0.35, 0.5, 0.75, 1.0]
    started = time.perf_counter()

    cell_rows: list[dict[str, float]] = []
    sample_rows: list[dict[str, float]] = []
    for seed in seeds:
        for snr_db in snr_values:
            cell, samples = run_one_cell(
                seed=seed,
                snr_db=snr_db,
                shape=shape,
                n_targets=n_targets,
                offset_radius=offset_radius,
                radii=radii,
                search_points=search_points,
                n_train=n_train,
                n_test=n_test,
                fixed_depth=fixed_depth,
                min_depth=min_depth,
                thresholds=thresholds,
                tolerance_db=tolerance_db,
            )
            cell_rows.append(cell)
            sample_rows.extend(samples)

    elapsed_seconds = time.perf_counter() - started
    snr_summary_rows = summarize_by_snr(cell_rows, snr_values)
    cell_savings = [float(row["test_mean_depth_savings_percent"]) for row in cell_rows]
    cell_gaps = [float(row["test_mean_nmse_gap_db"]) for row in cell_rows]

    output_dir = ROOT / "05_results" / "stage3_a4_snr_plateau_gate_seed_sweep"
    output_dir.mkdir(parents=True, exist_ok=True)
    cells_csv = output_dir / "stage3_a4_snr_plateau_gate_seed_sweep_cells.csv"
    with cells_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(cell_rows[0].keys()))
        writer.writeheader()
        writer.writerows(cell_rows)
    samples_csv = output_dir / "stage3_a4_snr_plateau_gate_seed_sweep_samples.csv"
    with samples_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(sample_rows[0].keys()))
        writer.writeheader()
        writer.writerows(sample_rows)
    snr_summary_csv = output_dir / "stage3_a4_snr_plateau_gate_seed_sweep_snr_summary.csv"
    with snr_summary_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(snr_summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(snr_summary_rows)

    metrics = {
        "tensor_shape": "128x16x32",
        "n_targets": n_targets,
        "snr_values_db": snr_values,
        "seeds": seeds,
        "n_train": n_train,
        "n_test": n_test,
        "fixed_depth": fixed_depth,
        "min_depth": min_depth,
        "nmse_tolerance_db": tolerance_db,
        "threshold_candidates_db": thresholds,
        "overall_mean_cell_depth_savings_percent": finite_mean(cell_savings),
        "overall_std_cell_depth_savings_percent": finite_std(cell_savings),
        "overall_mean_cell_nmse_gap_db": finite_mean(cell_gaps),
        "overall_max_cell_nmse_gap_db": float(max(cell_gaps)),
        "min_snr_mean_depth_savings_percent": min(
            float(row["mean_depth_savings_percent"]) for row in snr_summary_rows
        ),
        "max_snr_nmse_gap_db": max(float(row["max_nmse_gap_db"]) for row in snr_summary_rows),
        "elapsed_seconds": elapsed_seconds,
    }
    notes = [
        "SNR-axis strengthening for the narrowed A4 plateau gate at L=32.",
        "This remains local synthetic evidence and should not be promoted to a global IA-AUD claim.",
        "Depth is used as the FLOPs proxy because each refinement layer performs the same local-search kernel.",
    ]
    manifest_path = write_run_manifest(
        output_dir,
        run_id="stage3_a4_snr_plateau_gate_seed_sweep_20260625",
        command="python 04_experiments/eval/run_stage3_a4_snr_plateau_gate_seed_sweep.py",
        config={
            "shape": shape,
            "n_targets": n_targets,
            "snr_values_db": snr_values,
            "seeds": seeds,
            "n_train": n_train,
            "n_test": n_test,
            "offset_radius": offset_radius,
            "radii": radii,
            "search_points": search_points,
            "fixed_depth": fixed_depth,
            "min_depth": min_depth,
            "threshold_candidates_db": thresholds,
            "nmse_tolerance_db": tolerance_db,
        },
        metrics=metrics,
        notes=notes,
        cwd=ROOT,
    )
    summary_path = write_summary_md(
        output_dir,
        title="Stage 3 A4 SNR Plateau Gate Seed Sweep",
        config_hash="stage3-a4-snr-plateau-gate-seed-sweep-20260625",
        metrics=metrics,
        notes=notes,
        artifacts=[
            str(cells_csv.relative_to(ROOT)),
            str(samples_csv.relative_to(ROOT)),
            str(snr_summary_csv.relative_to(ROOT)),
            str(manifest_path.relative_to(ROOT)),
        ],
    )
    evaluation_path = write_evaluation_summary(
        output_dir,
        metrics=metrics,
        snr_summary_rows=snr_summary_rows,
        elapsed_seconds=elapsed_seconds,
    )
    print(f"Wrote {cells_csv.relative_to(ROOT)}")
    print(f"Wrote {samples_csv.relative_to(ROOT)}")
    print(f"Wrote {snr_summary_csv.relative_to(ROOT)}")
    print(f"Wrote {summary_path.relative_to(ROOT)}")
    print(f"Wrote {manifest_path.relative_to(ROOT)}")
    print(f"Wrote {evaluation_path.relative_to(ROOT)}")
    print(f"min_snr_mean_depth_savings_percent={metrics['min_snr_mean_depth_savings_percent']:.4f}")
    print(f"max_snr_nmse_gap_db={metrics['max_snr_nmse_gap_db']:.4f}")


if __name__ == "__main__":
    main()
