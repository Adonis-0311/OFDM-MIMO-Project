from __future__ import annotations

import csv
from pathlib import Path
import sys
import time

import numpy as np
from scipy.stats import t

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


def mean_ci95(values: list[float]) -> tuple[float, float]:
    arr = np.asarray(values, dtype=float)
    center = float(np.mean(arr))
    half = float(t.ppf(0.975, arr.size - 1) * np.std(arr, ddof=1) / np.sqrt(arr.size))
    return center - half, center + half


def run_one_cell(
    *,
    seed: int,
    n_targets: int,
    shape: tuple[int, int, int],
    snr_db: float,
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
    rng = seed_all(seed + n_targets * 1000)
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
                "n_targets": float(n_targets),
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
        "n_targets": float(n_targets),
        "selected_threshold_db": threshold,
        "train_mean_depth_savings_percent": float(train_metrics["mean_depth_savings_percent"]),
        "train_mean_nmse_gap_db": float(train_metrics["mean_nmse_gap_db"]),
        "test_mean_depth": float(test_metrics["mean_depth"]),
        "test_mean_depth_savings_percent": float(test_metrics["mean_depth_savings_percent"]),
        "test_min_depth_savings_percent": float(test_metrics["min_depth_savings_percent"]),
        "test_mean_nmse_gap_db": float(test_metrics["mean_nmse_gap_db"]),
    }
    return cell, sample_rows


def summarize_by_l(cell_rows: list[dict[str, float]], l_values: list[int]) -> list[dict[str, float]]:
    summary_rows: list[dict[str, float]] = []
    for n_targets in l_values:
        rows = [row for row in cell_rows if int(row["n_targets"]) == n_targets]
        savings = [float(row["test_mean_depth_savings_percent"]) for row in rows]
        gaps = [float(row["test_mean_nmse_gap_db"]) for row in rows]
        savings_low, savings_high = mean_ci95(savings)
        gaps_low, gaps_high = mean_ci95(gaps)
        summary_rows.append(
            {
                "n_targets": float(n_targets),
                "mean_depth_savings_percent": finite_mean(savings),
                "std_depth_savings_percent": finite_std(savings),
                "min_depth_savings_percent": float(min(savings)),
                "depth_savings_ci95_low_percent": savings_low,
                "depth_savings_ci95_high_percent": savings_high,
                "mean_nmse_gap_db": finite_mean(gaps),
                "max_nmse_gap_db": float(max(gaps)),
                "nmse_gap_ci95_low_db": gaps_low,
                "nmse_gap_ci95_high_db": gaps_high,
                "n_seed_cells": float(len(rows)),
            }
        )
    return summary_rows


def write_evaluation_summary(
    output_dir: Path,
    *,
    metrics: dict[str, float | int | str | list[int]],
    l_summary_rows: list[dict[str, float]],
    elapsed_seconds: float,
) -> Path:
    high_l_rows = [row for row in l_summary_rows if int(row["n_targets"]) >= 32]
    high_l_min_savings = min(float(row["mean_depth_savings_percent"]) for row in high_l_rows)
    high_l_max_gap = max(float(row["max_nmse_gap_db"]) for row in high_l_rows)
    status = (
        "supported"
        if high_l_min_savings >= 25.0 and high_l_max_gap <= float(metrics["nmse_tolerance_db"])
        else "inconclusive"
    )
    if status == "supported":
        claim_note = (
            "The plateau gate keeps the high-L mean savings above 25% for L>=32 while "
            "remaining within the NMSE tolerance. L=16 should be treated as boundary evidence."
        )
        next_action = "Use A4 as a high-L/platform early-stop result and aggregate it into the paper evidence table."
    else:
        claim_note = (
            "The cross-L sweep does not support a stable high-L claim under the current "
            "sample contract. A4 should be demoted or retested with a learned gate."
        )
        next_action = "Do not promote A4 beyond appendix until a stronger cross-L gate result exists."
    lines = [
        "# Stage 3 A4 Cross-L Plateau Gate Seed Sweep Evaluation Summary",
        "",
        "## Outcome Summary",
        "",
        (
            "This run extends the narrowed A4 plateau early-stop evidence from L=32 to "
            "L={16,32,64}. It tests whether the deployable scalar plateau gate behaves "
            "like a high-L/platform mechanism rather than a single-L artifact."
        ),
        "",
        "## evaluation_summary",
        "",
        "- `research_question`: Does the narrowed A4 plateau gate remain useful across L={16,32,64}, especially for L>=32?",
        f"- `claim_update`: {status} for cross-L high-L A4 evidence.",
        "- `baseline_relation`: Fixed-depth K=8 repeated off-grid refinement is the comparator for each seed and L cell.",
        "- `failure_mode`: No execution failure if complete; remaining limitation is a deliberately small CPU-feasible seed/sample count.",
        f"- `mechanism_note`: {claim_note}",
        f"- `next_action`: {next_action}",
        "- `evidence_level`: Cross-L local synthetic strengthening, not a global IA-AUD proof.",
        "",
        "## Key Metrics",
        "",
        f"- Seeds: {metrics['seeds']}",
        f"- L values: {metrics['l_values']}",
        f"- High-L minimum mean depth/FLOPs savings: {high_l_min_savings:.4f}%",
        f"- High-L maximum mean NMSE gap: {high_l_max_gap:.4f} dB",
        f"- Overall mean cell depth/FLOPs savings: {float(metrics['overall_mean_cell_depth_savings_percent']):.4f}%",
        f"- Overall mean cell NMSE gap: {float(metrics['overall_mean_cell_nmse_gap_db']):.4f} dB",
        f"- Wall-clock elapsed time: {elapsed_seconds:.2f} s",
        "",
        "## L Summary",
        "",
        "| L | Mean savings (%) | Min savings (%) | Mean gap (dB) | Max gap (dB) |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in l_summary_rows:
        lines.append(
            "| "
            f"{int(row['n_targets'])} | "
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
    snr_db = 20.0
    seeds = [20260624, 20260625, 20260626, 20260627, 20260628]
    l_values = [16, 32, 64]
    n_train = 2
    n_test = 5
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
        for n_targets in l_values:
            cell, samples = run_one_cell(
                seed=seed,
                n_targets=n_targets,
                shape=shape,
                snr_db=snr_db,
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
    l_summary_rows = summarize_by_l(cell_rows, l_values)
    cell_savings = [float(row["test_mean_depth_savings_percent"]) for row in cell_rows]
    cell_gaps = [float(row["test_mean_nmse_gap_db"]) for row in cell_rows]
    high_l_rows = [row for row in l_summary_rows if int(row["n_targets"]) >= 32]

    output_dir = ROOT / "05_results" / "stage3_a4_cross_l_plateau_gate_seed_sweep_strengthened"
    output_dir.mkdir(parents=True, exist_ok=True)
    cells_csv = output_dir / "stage3_a4_cross_l_plateau_gate_seed_sweep_cells.csv"
    with cells_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(cell_rows[0].keys()))
        writer.writeheader()
        writer.writerows(cell_rows)
    samples_csv = output_dir / "stage3_a4_cross_l_plateau_gate_seed_sweep_samples.csv"
    with samples_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(sample_rows[0].keys()))
        writer.writeheader()
        writer.writerows(sample_rows)
    l_summary_csv = output_dir / "stage3_a4_cross_l_plateau_gate_seed_sweep_l_summary.csv"
    with l_summary_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(l_summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(l_summary_rows)

    metrics = {
        "tensor_shape": "128x16x32",
        "snr_db": snr_db,
        "seeds": seeds,
        "l_values": l_values,
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
        "high_l_min_mean_depth_savings_percent": min(
            float(row["mean_depth_savings_percent"]) for row in high_l_rows
        ),
        "high_l_max_nmse_gap_db": max(float(row["max_nmse_gap_db"]) for row in high_l_rows),
        "elapsed_seconds": elapsed_seconds,
    }
    notes = [
        "Cross-L strengthening for the narrowed A4 plateau gate over L={16,32,64}.",
        "L=16 is boundary evidence; the paper-facing high-L claim should rely on L>=32.",
        "This remains local synthetic evidence and should not be promoted to a global IA-AUD claim.",
    ]
    manifest_path = write_run_manifest(
        output_dir,
        run_id="stage3_a4_cross_l_plateau_gate_seed_sweep_strengthened_20260630",
        command="python 04_experiments/eval/run_stage3_a4_cross_l_plateau_gate_seed_sweep.py",
        config={
            "shape": shape,
            "snr_db": snr_db,
            "seeds": seeds,
            "l_values": l_values,
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
        title="Stage 3 A4 Cross-L Plateau Gate Seed Sweep",
        config_hash="stage3-a4-cross-l-plateau-gate-seed-sweep-20260625",
        metrics=metrics,
        notes=notes,
        artifacts=[
            str(cells_csv.relative_to(ROOT)),
            str(samples_csv.relative_to(ROOT)),
            str(l_summary_csv.relative_to(ROOT)),
            str(manifest_path.relative_to(ROOT)),
        ],
    )
    evaluation_path = write_evaluation_summary(
        output_dir,
        metrics=metrics,
        l_summary_rows=l_summary_rows,
        elapsed_seconds=elapsed_seconds,
    )
    print(f"Wrote {cells_csv.relative_to(ROOT)}")
    print(f"Wrote {samples_csv.relative_to(ROOT)}")
    print(f"Wrote {l_summary_csv.relative_to(ROOT)}")
    print(f"Wrote {summary_path.relative_to(ROOT)}")
    print(f"Wrote {manifest_path.relative_to(ROOT)}")
    print(f"Wrote {evaluation_path.relative_to(ROOT)}")
    print(f"high_l_min_mean_depth_savings_percent={metrics['high_l_min_mean_depth_savings_percent']:.4f}")
    print(f"high_l_max_nmse_gap_db={metrics['high_l_max_nmse_gap_db']:.4f}")


if __name__ == "__main__":
    main()
