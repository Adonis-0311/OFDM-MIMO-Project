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


def run_one_seed(
    *,
    seed: int,
    shape: tuple[int, int, int],
    n_targets: int,
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
                "sample_index": float(sample_index),
                "selected_threshold_db": threshold,
                "gate_depth": float(depth),
                "gate_nmse_db": curve[depth],
                "fixed_depth_nmse_db": curve[fixed_depth],
                "gate_gap_vs_fixed_db": curve[depth] - curve[fixed_depth],
                "gate_depth_savings_percent": 100.0 * (fixed_depth - depth) / fixed_depth,
            }
        )

    summary = {
        "seed": float(seed),
        "selected_threshold_db": threshold,
        "train_mean_depth_savings_percent": float(train_metrics["mean_depth_savings_percent"]),
        "train_mean_nmse_gap_db": float(train_metrics["mean_nmse_gap_db"]),
        "test_mean_depth": float(test_metrics["mean_depth"]),
        "test_mean_depth_savings_percent": float(test_metrics["mean_depth_savings_percent"]),
        "test_min_depth_savings_percent": float(test_metrics["min_depth_savings_percent"]),
        "test_mean_nmse_gap_db": float(test_metrics["mean_nmse_gap_db"]),
    }
    return summary, sample_rows


def write_evaluation_summary(
    output_dir: Path,
    *,
    metrics: dict[str, float | int | str | list[int]],
    elapsed_seconds: float,
) -> Path:
    status = (
        "supported"
        if float(metrics["mean_seed_depth_savings_percent"]) >= 25.0
        and float(metrics["max_seed_nmse_gap_db"]) <= float(metrics["nmse_tolerance_db"])
        else "inconclusive"
    )
    if status == "supported":
        claim_note = (
            "The high-L plateau gate remains above the 25% depth-saving target across "
            "the seed sweep while staying within the NMSE tolerance."
        )
        next_action = "Promote A4 only as a narrowed high-L/platform-sample early-stop mechanism and avoid global adaptive-depth claims."
    else:
        claim_note = (
            "The high-L plateau gate is not stable enough under the current seed sweep "
            "to carry even the narrowed A4 claim without more work."
        )
        next_action = "Downgrade A4 or replace the scalar plateau rule with a stronger learned gate before making a main-text claim."
    lines = [
        "# Stage 3 A4 High-L Plateau Gate Seed Sweep Evaluation Summary",
        "",
        "## Outcome Summary",
        "",
        (
            "This run repeats the deployable high-L plateau early-stop gate across multiple "
            "seeds for L=32 at tensor shape `128x16x32`. It tests whether the narrowed A4 "
            "claim is stable beyond the first single-seed gate run."
        ),
        "",
        "## evaluation_summary",
        "",
        "- `research_question`: Does the narrowed high-L plateau gate keep >=25% depth/FLOPs savings within the NMSE tolerance across seeds?",
        f"- `claim_update`: {status} for narrowed multi-seed A4 high-L gate evidence.",
        "- `baseline_relation`: Fixed-depth K=8 repeated off-grid refinement is the comparator; each seed trains only a scalar plateau threshold.",
        "- `failure_mode`: No execution failure if complete; remaining limitation is synthetic L=32-only evidence.",
        f"- `mechanism_note`: {claim_note}",
        f"- `next_action`: {next_action}",
        "- `evidence_level`: Multi-seed local high-L A4 strengthening, not a global IA-AUD proof.",
        "",
        "## Key Metrics",
        "",
        f"- Seeds: {metrics['seeds']}",
        f"- Mean seed depth/FLOPs savings: {float(metrics['mean_seed_depth_savings_percent']):.4f}%",
        f"- Std. seed depth/FLOPs savings: {float(metrics['std_seed_depth_savings_percent']):.4f}%",
        f"- Minimum seed depth/FLOPs savings: {float(metrics['min_seed_depth_savings_percent']):.4f}%",
        f"- Mean seed NMSE gap vs fixed depth: {float(metrics['mean_seed_nmse_gap_db']):.4f} dB",
        f"- Maximum seed NMSE gap vs fixed depth: {float(metrics['max_seed_nmse_gap_db']):.4f} dB",
        f"- Wall-clock elapsed time: {elapsed_seconds:.2f} s",
    ]
    path = output_dir / "evaluation_summary.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    shape = (128, 16, 32)
    snr_db = 20.0
    seeds = [20260624, 20260625, 20260626]
    n_targets = 32
    n_train = 4
    n_test = 4
    offset_radius = 0.35
    radii = [0.45, 0.28, 0.18, 0.11, 0.07, 0.045, 0.03, 0.02]
    search_points = 3
    fixed_depth = len(radii)
    min_depth = 3
    tolerance_db = 0.5
    thresholds = [0.05, 0.1, 0.2, 0.35, 0.5, 0.75, 1.0]
    started = time.perf_counter()

    seed_rows: list[dict[str, float]] = []
    sample_rows: list[dict[str, float]] = []
    for seed in seeds:
        seed_summary, seed_samples = run_one_seed(
            seed=seed,
            shape=shape,
            n_targets=n_targets,
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
        seed_rows.append(seed_summary)
        sample_rows.extend(seed_samples)

    elapsed_seconds = time.perf_counter() - started
    savings = [float(row["test_mean_depth_savings_percent"]) for row in seed_rows]
    gaps = [float(row["test_mean_nmse_gap_db"]) for row in seed_rows]

    output_dir = ROOT / "05_results" / "stage3_a4_high_l_plateau_gate_seed_sweep"
    output_dir.mkdir(parents=True, exist_ok=True)
    seed_csv = output_dir / "stage3_a4_high_l_plateau_gate_seed_sweep_seeds.csv"
    with seed_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(seed_rows[0].keys()))
        writer.writeheader()
        writer.writerows(seed_rows)
    sample_csv = output_dir / "stage3_a4_high_l_plateau_gate_seed_sweep_samples.csv"
    with sample_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(sample_rows[0].keys()))
        writer.writeheader()
        writer.writerows(sample_rows)

    metrics = {
        "tensor_shape": "128x16x32",
        "snr_db": snr_db,
        "seeds": seeds,
        "n_targets": n_targets,
        "n_train": n_train,
        "n_test": n_test,
        "fixed_depth": fixed_depth,
        "min_depth": min_depth,
        "nmse_tolerance_db": tolerance_db,
        "threshold_candidates_db": thresholds,
        "mean_seed_depth_savings_percent": finite_mean(savings),
        "std_seed_depth_savings_percent": finite_std(savings),
        "min_seed_depth_savings_percent": float(min(savings)),
        "mean_seed_nmse_gap_db": finite_mean(gaps),
        "max_seed_nmse_gap_db": float(max(gaps)),
        "elapsed_seconds": elapsed_seconds,
    }
    notes = [
        "Multi-seed strengthening for the narrowed high-L A4 plateau gate.",
        "This remains L=32-only synthetic evidence and should not be promoted to a global IA-AUD claim.",
        "Depth is used as the FLOPs proxy because each refinement layer performs the same local-search kernel.",
    ]
    manifest_path = write_run_manifest(
        output_dir,
        run_id="stage3_a4_high_l_plateau_gate_seed_sweep_20260625",
        command="python 04_experiments/eval/run_stage3_a4_high_l_plateau_gate_seed_sweep.py",
        config={
            "shape": shape,
            "snr_db": snr_db,
            "seeds": seeds,
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
        title="Stage 3 A4 High-L Plateau Gate Seed Sweep",
        config_hash="stage3-a4-high-l-plateau-gate-seed-sweep-20260625",
        metrics=metrics,
        notes=notes,
        artifacts=[
            str(seed_csv.relative_to(ROOT)),
            str(sample_csv.relative_to(ROOT)),
            str(manifest_path.relative_to(ROOT)),
        ],
    )
    evaluation_path = write_evaluation_summary(
        output_dir,
        metrics=metrics,
        elapsed_seconds=elapsed_seconds,
    )
    print(f"Wrote {seed_csv.relative_to(ROOT)}")
    print(f"Wrote {sample_csv.relative_to(ROOT)}")
    print(f"Wrote {summary_path.relative_to(ROOT)}")
    print(f"Wrote {manifest_path.relative_to(ROOT)}")
    print(f"Wrote {evaluation_path.relative_to(ROOT)}")
    print(f"mean_seed_depth_savings_percent={metrics['mean_seed_depth_savings_percent']:.4f}")
    print(f"max_seed_nmse_gap_db={metrics['max_seed_nmse_gap_db']:.4f}")


if __name__ == "__main__":
    main()
