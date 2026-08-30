from __future__ import annotations

import csv
from pathlib import Path
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_active_modules"))

from common.manifest import write_run_manifest, write_summary_md
from common.seed import seed_all
from data.offgrid_tensor import (
    estimate_from_bins_lstsq,
    generate_offgrid_tensor_sample,
    measurement_nmse_db,
    refine_bins_local,
    topk_grid_bins,
)


def finite_mean(values: list[float]) -> float:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    return float(np.mean(arr)) if arr.size else float("nan")


def run_depth_curve(
    *,
    rng: np.random.Generator,
    shape: tuple[int, int, int],
    n_targets: int,
    snr_db: float,
    offset_radius: float,
    radii: list[float],
    search_points: int,
) -> list[float]:
    sample = generate_offgrid_tensor_sample(
        rng=rng,
        shape=shape,
        n_targets=n_targets,
        snr_db=snr_db,
        offset_radius=offset_radius,
    )
    bins: list[tuple[float, float, float]] = [
        (float(a), float(d), float(v)) for a, d, v in topk_grid_bins(sample.measurement, n_targets)
    ]
    values: list[float] = []
    estimate = estimate_from_bins_lstsq(sample.measurement, shape, bins)
    values.append(measurement_nmse_db(estimate, sample.clean))
    for radius in radii:
        bins = refine_bins_local(
            sample.measurement,
            shape,
            bins,  # type: ignore[arg-type]
            search_radius=radius,
            search_points=search_points,
        )
        estimate = estimate_from_bins_lstsq(sample.measurement, shape, bins)
        values.append(measurement_nmse_db(estimate, sample.clean))
    return values


def plateau_gate_depth(
    curve: list[float],
    *,
    threshold_db: float,
    min_depth: int,
    fixed_depth: int,
) -> int:
    for depth in range(max(1, min_depth), fixed_depth + 1):
        improvement = curve[depth - 1] - curve[depth]
        if improvement < threshold_db:
            return depth
    return fixed_depth


def evaluate_threshold(
    curves: list[list[float]],
    *,
    threshold_db: float,
    min_depth: int,
    fixed_depth: int,
) -> dict[str, float]:
    depths = []
    gaps = []
    savings = []
    for curve in curves:
        depth = plateau_gate_depth(
            curve,
            threshold_db=threshold_db,
            min_depth=min_depth,
            fixed_depth=fixed_depth,
        )
        gap = curve[depth] - curve[fixed_depth]
        saving = 100.0 * (fixed_depth - depth) / max(fixed_depth, 1)
        depths.append(float(depth))
        gaps.append(gap)
        savings.append(saving)
    return {
        "mean_depth": finite_mean(depths),
        "mean_nmse_gap_db": finite_mean(gaps),
        "mean_depth_savings_percent": finite_mean(savings),
        "min_depth_savings_percent": float(min(savings)),
        "max_depth_savings_percent": float(max(savings)),
    }


def choose_threshold(
    curves: list[list[float]],
    *,
    thresholds: list[float],
    min_depth: int,
    fixed_depth: int,
    tolerance_db: float,
) -> tuple[float, dict[str, float], list[dict[str, float]]]:
    rows: list[dict[str, float]] = []
    best_threshold = thresholds[0]
    best_metrics = evaluate_threshold(
        curves,
        threshold_db=best_threshold,
        min_depth=min_depth,
        fixed_depth=fixed_depth,
    )
    feasible_rows = []
    for threshold in thresholds:
        metrics = evaluate_threshold(
            curves,
            threshold_db=threshold,
            min_depth=min_depth,
            fixed_depth=fixed_depth,
        )
        row = {"threshold_db": threshold, **metrics}
        rows.append(row)
        if metrics["mean_nmse_gap_db"] <= tolerance_db:
            feasible_rows.append(row)
    if feasible_rows:
        best = max(feasible_rows, key=lambda row: row["mean_depth_savings_percent"])
        best_threshold = float(best["threshold_db"])
        best_metrics = {key: float(value) for key, value in best.items() if key != "threshold_db"}
    return best_threshold, best_metrics, rows


def write_evaluation_summary(
    output_dir: Path,
    *,
    threshold: float,
    test_metrics: dict[str, float],
    tolerance_db: float,
    fixed_depth: int,
    elapsed_seconds: float,
) -> Path:
    status = (
        "supported"
        if test_metrics["mean_depth_savings_percent"] >= 25.0
        and test_metrics["mean_nmse_gap_db"] <= tolerance_db
        else "inconclusive"
    )
    if status == "supported":
        mechanism_note = (
            "A simple trained threshold gate reaches the high-L >=25% depth-reduction target "
            "within the NMSE tolerance, so A4 remains viable as a narrowed high-L/platform gate."
        )
        next_action = "Implement the high-L gate as the A4 appendix or restricted mainline and avoid global IA-AUD claims."
    else:
        mechanism_note = (
            "The lightweight high-L plateau gate does not meet the >=25% savings target on held-out samples, "
            "so A4 should be downgraded unless a stronger learned gate is added."
        )
        next_action = "Downgrade A4 to a cautious trade-off/appendix result or replace the gate with a genuinely trained predictor."
    lines = [
        "# Stage 3 A4 High-L Plateau Gate Evaluation Summary",
        "",
        "## Outcome Summary",
        "",
        (
            "This run tests a deployable high-L early-stop gate. A scalar threshold is selected "
            "on training curves, then evaluated on held-out L=32 curves against fixed K=8."
        ),
        "",
        "## evaluation_summary",
        "",
        "- `research_question`: Can a lightweight plateau gate reach >=25% depth/FLOPs savings on high-L samples while staying near fixed-depth NMSE?",
        f"- `claim_update`: {status} for narrowed high-L A4 gate evidence.",
        "- `baseline_relation`: Fixed-depth K=8 is the comparator; the gate uses only sequential per-layer improvement and a trained scalar threshold.",
        "- `failure_mode`: No execution failure; remaining limitation is L=32-only scope and small train/test sample count.",
        f"- `mechanism_note`: {mechanism_note}",
        f"- `next_action`: {next_action}",
        "- `evidence_level`: Stage-3 restricted A4 gate evidence.",
        "",
        "## Key Metrics",
        "",
        f"- Selected threshold: {threshold:.4f} dB",
        f"- Fixed depth: {fixed_depth}",
        f"- NMSE tolerance: {tolerance_db:.2f} dB",
        f"- Test mean depth: {test_metrics['mean_depth']:.4f}",
        f"- Test mean depth/FLOPs savings: {test_metrics['mean_depth_savings_percent']:.4f}%",
        f"- Test mean NMSE gap vs fixed depth: {test_metrics['mean_nmse_gap_db']:.4f} dB",
        f"- Wall-clock elapsed time: {elapsed_seconds:.2f} s",
    ]
    path = output_dir / "evaluation_summary.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    shape = (128, 16, 32)
    snr_db = 20.0
    seed = 20260624
    n_targets = 32
    n_train = 6
    n_test = 6
    offset_radius = 0.35
    radii = [0.45, 0.28, 0.18, 0.11, 0.07, 0.045, 0.03, 0.02]
    search_points = 3
    fixed_depth = len(radii)
    min_depth = 3
    tolerance_db = 0.5
    thresholds = [0.05, 0.1, 0.2, 0.35, 0.5, 0.75, 1.0]
    started = time.perf_counter()
    rng = seed_all(seed)

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
    threshold, train_metrics, threshold_rows = choose_threshold(
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

    sample_rows: list[dict[str, float | str]] = []
    for split, curves in (("train", train_curves), ("test", test_curves)):
        for sample_index, curve in enumerate(curves):
            depth = plateau_gate_depth(
                curve,
                threshold_db=threshold,
                min_depth=min_depth,
                fixed_depth=fixed_depth,
            )
            for curve_depth, nmse_db in enumerate(curve):
                sample_rows.append(
                    {
                        "split": split,
                        "sample_index": float(sample_index),
                        "depth": float(curve_depth),
                        "nmse_db": nmse_db,
                        "gate_depth": float(depth),
                        "gate_nmse_db": curve[depth],
                        "fixed_depth_nmse_db": curve[fixed_depth],
                        "gate_gap_vs_fixed_db": curve[depth] - curve[fixed_depth],
                        "gate_depth_savings_percent": 100.0 * (fixed_depth - depth) / fixed_depth,
                    }
                )

    elapsed_seconds = time.perf_counter() - started
    output_dir = ROOT / "05_results" / "stage3_a4_high_l_plateau_gate"
    output_dir.mkdir(parents=True, exist_ok=True)
    threshold_csv = output_dir / "stage3_a4_high_l_plateau_gate_thresholds.csv"
    with threshold_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(threshold_rows[0].keys()))
        writer.writeheader()
        writer.writerows(threshold_rows)
    samples_csv = output_dir / "stage3_a4_high_l_plateau_gate_samples.csv"
    with samples_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(sample_rows[0].keys()))
        writer.writeheader()
        writer.writerows(sample_rows)

    metrics = {
        "tensor_shape": "128x16x32",
        "snr_db": snr_db,
        "seed": seed,
        "n_targets": n_targets,
        "n_train": n_train,
        "n_test": n_test,
        "fixed_depth": fixed_depth,
        "min_depth": min_depth,
        "radii": radii,
        "search_points": search_points,
        "threshold_candidates_db": thresholds,
        "selected_threshold_db": threshold,
        "nmse_tolerance_db": tolerance_db,
        "train_metrics": train_metrics,
        "test_metrics": test_metrics,
        "elapsed_seconds": elapsed_seconds,
    }
    notes = [
        "This is a narrowed high-L A4 gate test, not a global IA-AUD claim.",
        "The gate stops when the incremental NMSE improvement falls below a trained scalar threshold after a minimum depth.",
        "Depth is used as the FLOPs proxy because each refinement layer performs the same local-search kernel.",
    ]
    manifest_path = write_run_manifest(
        output_dir,
        run_id="stage3_a4_high_l_plateau_gate_20260624",
        command="python 04_experiments/eval/run_stage3_a4_high_l_plateau_gate.py",
        config={
            "shape": shape,
            "snr_db": snr_db,
            "seed": seed,
            "n_targets": n_targets,
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
        title="Stage 3 A4 High-L Plateau Gate",
        config_hash="stage3-a4-high-l-plateau-gate-20260624",
        metrics=metrics,
        notes=notes,
        artifacts=[
            str(threshold_csv.relative_to(ROOT)),
            str(samples_csv.relative_to(ROOT)),
            str(manifest_path.relative_to(ROOT)),
        ],
    )
    evaluation_path = write_evaluation_summary(
        output_dir,
        threshold=threshold,
        test_metrics=test_metrics,
        tolerance_db=tolerance_db,
        fixed_depth=fixed_depth,
        elapsed_seconds=elapsed_seconds,
    )
    print(f"Wrote {threshold_csv.relative_to(ROOT)}")
    print(f"Wrote {samples_csv.relative_to(ROOT)}")
    print(f"Wrote {summary_path.relative_to(ROOT)}")
    print(f"Wrote {manifest_path.relative_to(ROOT)}")
    print(f"Wrote {evaluation_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
