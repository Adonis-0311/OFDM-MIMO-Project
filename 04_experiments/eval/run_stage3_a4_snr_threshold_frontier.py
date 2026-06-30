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
from run_stage3_a4_high_l_plateau_gate import plateau_gate_depth, run_depth_curve


def finite_mean(values: list[float]) -> float:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    return float(np.mean(arr)) if arr.size else float("nan")


def finite_std(values: list[float]) -> float:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    return float(np.std(arr, ddof=1)) if arr.size > 1 else 0.0


def evaluate_threshold(
    curves: list[list[float]],
    *,
    threshold_db: float,
    min_depth: int,
    fixed_depth: int,
) -> dict[str, float]:
    depths: list[float] = []
    gaps: list[float] = []
    savings: list[float] = []
    for curve in curves:
        depth = plateau_gate_depth(
            curve,
            threshold_db=threshold_db,
            min_depth=min_depth,
            fixed_depth=fixed_depth,
        )
        gaps.append(float(curve[depth] - curve[fixed_depth]))
        depths.append(float(depth))
        savings.append(100.0 * (fixed_depth - depth) / max(fixed_depth, 1))
    return {
        "mean_depth": finite_mean(depths),
        "mean_depth_savings_percent": finite_mean(savings),
        "min_depth_savings_percent": float(min(savings)),
        "mean_nmse_gap_db": finite_mean(gaps),
        "max_nmse_gap_db": float(max(gaps)),
    }


def threshold_frontier(
    curves: list[list[float]],
    *,
    thresholds: list[float],
    min_depth: int,
    fixed_depth: int,
) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for threshold in thresholds:
        rows.append(
            {
                "threshold_db": float(threshold),
                **evaluate_threshold(
                    curves,
                    threshold_db=threshold,
                    min_depth=min_depth,
                    fixed_depth=fixed_depth,
                ),
            }
        )
    return rows


def select_max_savings(
    rows: list[dict[str, float]],
    *,
    max_mean_gap_db: float,
    min_mean_savings_percent: float | None = None,
) -> dict[str, float]:
    feasible = [
        row
        for row in rows
        if float(row["mean_nmse_gap_db"]) <= max_mean_gap_db
        and (
            min_mean_savings_percent is None
            or float(row["mean_depth_savings_percent"]) >= min_mean_savings_percent
        )
    ]
    if feasible:
        return max(feasible, key=lambda row: float(row["mean_depth_savings_percent"]))
    return min(rows, key=lambda row: float(row["mean_nmse_gap_db"]))


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
    guarded_tolerance_db: float,
) -> tuple[list[dict[str, float]], list[dict[str, float]]]:
    rng = seed_all(seed + int(round(snr_db * 100.0)) + 11000)
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

    train_rows = threshold_frontier(
        train_curves,
        thresholds=thresholds,
        min_depth=min_depth,
        fixed_depth=fixed_depth,
    )
    test_rows = threshold_frontier(
        test_curves,
        thresholds=thresholds,
        min_depth=min_depth,
        fixed_depth=fixed_depth,
    )

    standard = select_max_savings(train_rows, max_mean_gap_db=tolerance_db)
    guarded = select_max_savings(train_rows, max_mean_gap_db=guarded_tolerance_db)
    oracle = select_max_savings(
        test_rows,
        max_mean_gap_db=tolerance_db,
        min_mean_savings_percent=25.0,
    )
    policies = [
        ("standard_train", standard),
        ("guarded_train", guarded),
        ("test_oracle_frontier", oracle),
    ]

    policy_rows: list[dict[str, float]] = []
    for policy, selected in policies:
        threshold = float(selected["threshold_db"])
        test_metrics = evaluate_threshold(
            test_curves,
            threshold_db=threshold,
            min_depth=min_depth,
            fixed_depth=fixed_depth,
        )
        policy_rows.append(
            {
                "seed": float(seed),
                "snr_db": float(snr_db),
                "policy": policy,
                "selected_threshold_db": threshold,
                "test_mean_depth": float(test_metrics["mean_depth"]),
                "test_mean_depth_savings_percent": float(
                    test_metrics["mean_depth_savings_percent"]
                ),
                "test_min_depth_savings_percent": float(
                    test_metrics["min_depth_savings_percent"]
                ),
                "test_mean_nmse_gap_db": float(test_metrics["mean_nmse_gap_db"]),
                "test_max_nmse_gap_db": float(test_metrics["max_nmse_gap_db"]),
                "passes_mean_gate": float(
                    test_metrics["mean_depth_savings_percent"] >= 25.0
                    and test_metrics["mean_nmse_gap_db"] <= tolerance_db
                ),
            }
        )

    frontier_rows: list[dict[str, float]] = []
    for split, rows in (("train", train_rows), ("test", test_rows)):
        for row in rows:
            frontier_rows.append(
                {
                    "seed": float(seed),
                    "snr_db": float(snr_db),
                    "split": split,
                    **row,
                }
            )
    return policy_rows, frontier_rows


def summarize_policy_rows(policy_rows: list[dict[str, float]], snr_values: list[float]) -> list[dict[str, float]]:
    policies = ["standard_train", "guarded_train", "test_oracle_frontier"]
    summary_rows: list[dict[str, float]] = []
    for policy in policies:
        for snr_db in snr_values:
            rows = [
                row
                for row in policy_rows
                if row["policy"] == policy and abs(float(row["snr_db"]) - snr_db) < 1e-9
            ]
            savings = [float(row["test_mean_depth_savings_percent"]) for row in rows]
            gaps = [float(row["test_mean_nmse_gap_db"]) for row in rows]
            pass_flags = [float(row["passes_mean_gate"]) for row in rows]
            summary_rows.append(
                {
                    "policy": policy,
                    "snr_db": float(snr_db),
                    "mean_depth_savings_percent": finite_mean(savings),
                    "min_depth_savings_percent": float(min(savings)),
                    "mean_nmse_gap_db": finite_mean(gaps),
                    "max_nmse_gap_db": float(max(gaps)),
                    "pass_rate": finite_mean(pass_flags),
                    "n_seed_cells": float(len(rows)),
                }
            )
    return summary_rows


def write_evaluation_summary(
    output_dir: Path,
    *,
    metrics: dict[str, float | int | str | list[int] | list[float]],
    summary_rows: list[dict[str, float]],
    elapsed_seconds: float,
) -> Path:
    oracle_rows = [row for row in summary_rows if row["policy"] == "test_oracle_frontier"]
    oracle_min_savings = min(float(row["mean_depth_savings_percent"]) for row in oracle_rows)
    oracle_max_gap = max(float(row["max_nmse_gap_db"]) for row in oracle_rows)
    standard_rows = [row for row in summary_rows if row["policy"] == "standard_train"]
    standard_min_savings = min(float(row["mean_depth_savings_percent"]) for row in standard_rows)
    standard_max_gap = max(float(row["max_nmse_gap_db"]) for row in standard_rows)
    if oracle_min_savings >= 25.0 and oracle_max_gap <= float(metrics["nmse_tolerance_db"]):
        conclusion = (
            "The threshold family has a feasible SNR-aware frontier in this small diagnostic; "
            "the remaining problem is trainable calibration rather than the plateau feature itself."
        )
    else:
        conclusion = (
            "Even the test-frontier diagnostic does not clear the SNR-axis gate, so a scalar "
            "plateau threshold is too weak for a broad SNR claim under this contract."
        )
    lines = [
        "# Stage 3 A4 SNR Threshold Frontier Evaluation Summary",
        "",
        "## Outcome Summary",
        "",
        (
            "This diagnostic compares the existing train-selected scalar plateau gate with a "
            "guarded train selection and a test-oracle threshold frontier for each SNR cell."
        ),
        "",
        "## evaluation_summary",
        "",
        "- `research_question`: Is the A4 SNR failure caused by the scalar plateau feature itself or by threshold calibration?",
        "- `baseline_relation`: Fixed-depth K=8 repeated off-grid refinement remains the quality comparator.",
        "- `evidence_level`: Diagnostic local synthetic frontier; the test-oracle row is an upper bound, not deployable evidence.",
        f"- `mechanism_note`: {conclusion}",
        "- `next_action`: If only the oracle clears the gate, replace the scalar rule with a learned/calibrated SNR-aware gate before widening A4.",
        "",
        "## Key Metrics",
        "",
        f"- Seeds: {metrics['seeds']}",
        f"- SNR values: {metrics['snr_values_db']}",
        f"- Standard-train minimum SNR mean savings: {standard_min_savings:.4f}%",
        f"- Standard-train maximum SNR mean gap: {standard_max_gap:.4f} dB",
        f"- Test-oracle minimum SNR mean savings: {oracle_min_savings:.4f}%",
        f"- Test-oracle maximum SNR mean gap: {oracle_max_gap:.4f} dB",
        f"- Wall-clock elapsed time: {elapsed_seconds:.2f} s",
        "",
        "## Policy/SNR Summary",
        "",
        "| Policy | SNR (dB) | Mean savings (%) | Min savings (%) | Mean gap (dB) | Max gap (dB) | Pass rate |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary_rows:
        lines.append(
            "| "
            f"{row['policy']} | "
            f"{row['snr_db']:.1f} | "
            f"{row['mean_depth_savings_percent']:.4f} | "
            f"{row['min_depth_savings_percent']:.4f} | "
            f"{row['mean_nmse_gap_db']:.4f} | "
            f"{row['max_nmse_gap_db']:.4f} | "
            f"{row['pass_rate']:.4f} |"
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
    guarded_tolerance_db = 0.35
    thresholds = [0.005, 0.01, 0.02, 0.035, 0.05, 0.075, 0.1, 0.15, 0.2, 0.25, 0.35, 0.5, 0.75, 1.0]
    started = time.perf_counter()

    policy_rows: list[dict[str, float]] = []
    frontier_rows: list[dict[str, float]] = []
    for seed in seeds:
        for snr_db in snr_values:
            cell_policies, cell_frontier = run_one_cell(
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
                guarded_tolerance_db=guarded_tolerance_db,
            )
            policy_rows.extend(cell_policies)
            frontier_rows.extend(cell_frontier)

    elapsed_seconds = time.perf_counter() - started
    summary_rows = summarize_policy_rows(policy_rows, snr_values)

    output_dir = ROOT / "05_results" / "stage3_a4_snr_threshold_frontier"
    output_dir.mkdir(parents=True, exist_ok=True)
    policy_csv = output_dir / "stage3_a4_snr_threshold_frontier_policy_cells.csv"
    with policy_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(policy_rows[0].keys()))
        writer.writeheader()
        writer.writerows(policy_rows)
    frontier_csv = output_dir / "stage3_a4_snr_threshold_frontier_thresholds.csv"
    with frontier_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(frontier_rows[0].keys()))
        writer.writeheader()
        writer.writerows(frontier_rows)
    summary_csv = output_dir / "stage3_a4_snr_threshold_frontier_summary.csv"
    with summary_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    standard_rows = [row for row in summary_rows if row["policy"] == "standard_train"]
    guarded_rows = [row for row in summary_rows if row["policy"] == "guarded_train"]
    oracle_rows = [row for row in summary_rows if row["policy"] == "test_oracle_frontier"]
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
        "guarded_train_tolerance_db": guarded_tolerance_db,
        "threshold_candidates_db": thresholds,
        "standard_min_snr_mean_depth_savings_percent": min(
            float(row["mean_depth_savings_percent"]) for row in standard_rows
        ),
        "standard_max_snr_nmse_gap_db": max(float(row["max_nmse_gap_db"]) for row in standard_rows),
        "guarded_min_snr_mean_depth_savings_percent": min(
            float(row["mean_depth_savings_percent"]) for row in guarded_rows
        ),
        "guarded_max_snr_nmse_gap_db": max(float(row["max_nmse_gap_db"]) for row in guarded_rows),
        "oracle_min_snr_mean_depth_savings_percent": min(
            float(row["mean_depth_savings_percent"]) for row in oracle_rows
        ),
        "oracle_max_snr_nmse_gap_db": max(float(row["max_nmse_gap_db"]) for row in oracle_rows),
        "elapsed_seconds": elapsed_seconds,
    }
    notes = [
        "Diagnostic frontier for the A4 SNR boundary; test-oracle rows are not deployable evidence.",
        "Standard-train selection maximizes train savings under the 0.5 dB mean-gap tolerance.",
        "Guarded-train selection uses a stricter 0.35 dB train mean-gap guard.",
    ]
    manifest_path = write_run_manifest(
        output_dir,
        run_id="stage3_a4_snr_threshold_frontier_20260625",
        command="python 04_experiments/eval/run_stage3_a4_snr_threshold_frontier.py",
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
            "guarded_train_tolerance_db": guarded_tolerance_db,
        },
        metrics=metrics,
        notes=notes,
        cwd=ROOT,
    )
    summary_path = write_summary_md(
        output_dir,
        title="Stage 3 A4 SNR Threshold Frontier",
        config_hash="stage3-a4-snr-threshold-frontier-20260625",
        metrics=metrics,
        notes=notes,
        artifacts=[
            str(policy_csv.relative_to(ROOT)),
            str(frontier_csv.relative_to(ROOT)),
            str(summary_csv.relative_to(ROOT)),
            str(manifest_path.relative_to(ROOT)),
        ],
    )
    evaluation_path = write_evaluation_summary(
        output_dir,
        metrics=metrics,
        summary_rows=summary_rows,
        elapsed_seconds=elapsed_seconds,
    )
    print(f"Wrote {policy_csv.relative_to(ROOT)}")
    print(f"Wrote {frontier_csv.relative_to(ROOT)}")
    print(f"Wrote {summary_csv.relative_to(ROOT)}")
    print(f"Wrote {summary_path.relative_to(ROOT)}")
    print(f"Wrote {manifest_path.relative_to(ROOT)}")
    print(f"Wrote {evaluation_path.relative_to(ROOT)}")
    print(
        "standard_min_snr_mean_depth_savings_percent="
        f"{metrics['standard_min_snr_mean_depth_savings_percent']:.4f}"
    )
    print(f"standard_max_snr_nmse_gap_db={metrics['standard_max_snr_nmse_gap_db']:.4f}")
    print(
        "oracle_min_snr_mean_depth_savings_percent="
        f"{metrics['oracle_min_snr_mean_depth_savings_percent']:.4f}"
    )
    print(f"oracle_max_snr_nmse_gap_db={metrics['oracle_max_snr_nmse_gap_db']:.4f}")


if __name__ == "__main__":
    main()
