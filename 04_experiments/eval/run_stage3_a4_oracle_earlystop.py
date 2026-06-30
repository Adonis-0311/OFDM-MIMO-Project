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


def oracle_depth_against_fixed(curve: list[float], *, fixed_depth: int, tolerance_db: float) -> int:
    target_nmse = curve[fixed_depth] + tolerance_db
    for depth, nmse_db in enumerate(curve[: fixed_depth + 1]):
        if nmse_db <= target_nmse:
            return depth
    return fixed_depth


def write_evaluation_summary(
    output_dir: Path,
    *,
    mean_depth_savings_percent: float,
    mean_nmse_gap_db: float,
    mean_oracle_depth: float,
    fixed_depth: int,
    tolerance_db: float,
    elapsed_seconds: float,
) -> Path:
    status = (
        "supported"
        if mean_depth_savings_percent >= 25.0 and mean_nmse_gap_db <= tolerance_db
        else "inconclusive"
    )
    if status == "supported":
        mechanism_note = (
            "Oracle early stopping can meet the >=25% depth-reduction target while staying "
            "within the NMSE tolerance, so a learned gate has a plausible upper-bound target."
        )
        next_action = "Train a lightweight gating predictor against oracle depths and test whether it approaches the oracle savings."
    else:
        mechanism_note = (
            "Even oracle early stopping does not yet prove the >=25% depth-reduction target "
            "under the current tolerance/sample contract, so the full IA-AUD gate should not "
            "be claimed without stronger evidence."
        )
        next_action = "Either broaden the oracle sweep/tolerance analysis or downgrade IA-AUD to a cautious trade-off/appendix result."
    lines = [
        "# Stage 3 A4 IA-AUD Oracle Early-Stop Evaluation Summary",
        "",
        "## Outcome Summary",
        "",
        (
            "This run estimates the best-case depth savings available to an adaptive-depth "
            "IA-AUD gate. For each sample, it observes the K=0..8 NMSE curve and chooses "
            f"the earliest depth whose NMSE is within {tolerance_db:.2f} dB of fixed K={fixed_depth}."
        ),
        "",
        "## evaluation_summary",
        "",
        "- `research_question`: Can oracle early stopping reduce average unfolding depth by at least 25% while matching fixed-depth NMSE?",
        f"- `claim_update`: {status} for A4 FLOPs/depth-reduction evidence.",
        "- `baseline_relation`: Fixed-depth K=8 repeated off-grid refinement is the comparator; oracle early-stop uses the same per-sample curve.",
        "- `failure_mode`: No execution failure; remaining limitation is that oracle early-stop is an upper bound, not a trained gate.",
        f"- `mechanism_note`: {mechanism_note}",
        f"- `next_action`: {next_action}",
        "- `evidence_level`: Stage-3 A4 upper-bound evidence, not final gating-network evidence.",
        "",
        "## Key Metrics",
        "",
        f"- Fixed depth: {fixed_depth}",
        f"- NMSE tolerance: {tolerance_db:.2f} dB",
        f"- Mean oracle depth: {mean_oracle_depth:.4f}",
        f"- Mean depth/FLOPs savings: {mean_depth_savings_percent:.4f}%",
        f"- Mean NMSE gap vs fixed depth: {mean_nmse_gap_db:.4f} dB",
        f"- Wall-clock elapsed time: {elapsed_seconds:.2f} s",
    ]
    path = output_dir / "evaluation_summary.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    shape = (128, 16, 32)
    snr_db = 20.0
    seed = 20260624
    l_values = [2, 8, 32]
    n_trials = 5
    offset_radius = 0.35
    radii = [0.45, 0.28, 0.18, 0.11, 0.07, 0.045, 0.03, 0.02]
    search_points = 3
    fixed_depth = len(radii)
    tolerance_db = 0.5
    started = time.perf_counter()
    rng = seed_all(seed)

    sample_rows: list[dict[str, float]] = []
    summary_rows: list[dict[str, float]] = []
    oracle_depths: list[float] = []
    nmse_gaps: list[float] = []
    savings: list[float] = []

    for n_targets in l_values:
        l_oracle_depths: list[float] = []
        l_nmse_gaps: list[float] = []
        l_savings: list[float] = []
        for trial in range(n_trials):
            curve = run_depth_curve(
                rng=rng,
                shape=shape,
                n_targets=n_targets,
                snr_db=snr_db,
                offset_radius=offset_radius,
                radii=radii,
                search_points=search_points,
            )
            oracle_depth = oracle_depth_against_fixed(
                curve,
                fixed_depth=fixed_depth,
                tolerance_db=tolerance_db,
            )
            nmse_gap = curve[oracle_depth] - curve[fixed_depth]
            depth_saving = 100.0 * (fixed_depth - oracle_depth) / max(fixed_depth, 1)
            oracle_depths.append(float(oracle_depth))
            nmse_gaps.append(nmse_gap)
            savings.append(depth_saving)
            l_oracle_depths.append(float(oracle_depth))
            l_nmse_gaps.append(nmse_gap)
            l_savings.append(depth_saving)
            for depth, nmse_db in enumerate(curve):
                sample_rows.append(
                    {
                        "n_targets": float(n_targets),
                        "trial": float(trial),
                        "depth": float(depth),
                        "nmse_db": nmse_db,
                        "fixed_depth_nmse_db": curve[fixed_depth],
                        "oracle_depth": float(oracle_depth),
                        "oracle_nmse_db": curve[oracle_depth],
                        "oracle_gap_vs_fixed_db": nmse_gap,
                        "oracle_depth_savings_percent": depth_saving,
                    }
                )
        summary_rows.append(
            {
                "n_targets": float(n_targets),
                "mean_oracle_depth": finite_mean(l_oracle_depths),
                "mean_nmse_gap_vs_fixed_db": finite_mean(l_nmse_gaps),
                "mean_depth_savings_percent": finite_mean(l_savings),
                "min_depth_savings_percent": float(min(l_savings)),
                "max_depth_savings_percent": float(max(l_savings)),
                "n_trials": float(n_trials),
            }
        )

    elapsed_seconds = time.perf_counter() - started
    output_dir = ROOT / "05_results" / "stage3_a4_oracle_earlystop"
    output_dir.mkdir(parents=True, exist_ok=True)
    samples_csv = output_dir / "stage3_a4_oracle_earlystop_samples.csv"
    with samples_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(sample_rows[0].keys()))
        writer.writeheader()
        writer.writerows(sample_rows)
    summary_csv = output_dir / "stage3_a4_oracle_earlystop.csv"
    with summary_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    metrics = {
        "tensor_shape": "128x16x32",
        "snr_db": snr_db,
        "seed": seed,
        "l_values": l_values,
        "n_trials_per_l": n_trials,
        "fixed_depth": fixed_depth,
        "depth_values": list(range(fixed_depth + 1)),
        "radii": radii,
        "search_points": search_points,
        "nmse_tolerance_db": tolerance_db,
        "mean_oracle_depth": finite_mean(oracle_depths),
        "mean_nmse_gap_vs_fixed_db": finite_mean(nmse_gaps),
        "mean_depth_savings_percent": finite_mean(savings),
        "min_depth_savings_percent": float(min(savings)),
        "max_depth_savings_percent": float(max(savings)),
        "elapsed_seconds": elapsed_seconds,
    }
    notes = [
        "This is an oracle upper-bound run for IA-AUD early stopping, not a trained gating model.",
        "Depth is used as the FLOPs proxy because each refinement layer performs the same local-search kernel.",
        "The oracle stop chooses the earliest K within 0.5 dB of the fixed K=8 NMSE on the same sample.",
    ]
    manifest_path = write_run_manifest(
        output_dir,
        run_id="stage3_a4_oracle_earlystop_20260624",
        command="python 04_experiments/eval/run_stage3_a4_oracle_earlystop.py",
        config={
            "shape": shape,
            "snr_db": snr_db,
            "seed": seed,
            "l_values": l_values,
            "n_trials": n_trials,
            "offset_radius": offset_radius,
            "radii": radii,
            "search_points": search_points,
            "fixed_depth": fixed_depth,
            "nmse_tolerance_db": tolerance_db,
        },
        metrics=metrics,
        notes=notes,
        cwd=ROOT,
    )
    summary_path = write_summary_md(
        output_dir,
        title="Stage 3 A4 IA-AUD Oracle Early-Stop",
        config_hash="stage3-a4-oracle-earlystop-20260624",
        metrics=metrics,
        notes=notes,
        artifacts=[
            str(summary_csv.relative_to(ROOT)),
            str(samples_csv.relative_to(ROOT)),
            str(manifest_path.relative_to(ROOT)),
        ],
    )
    evaluation_path = write_evaluation_summary(
        output_dir,
        mean_depth_savings_percent=float(metrics["mean_depth_savings_percent"]),
        mean_nmse_gap_db=float(metrics["mean_nmse_gap_vs_fixed_db"]),
        mean_oracle_depth=float(metrics["mean_oracle_depth"]),
        fixed_depth=fixed_depth,
        tolerance_db=tolerance_db,
        elapsed_seconds=elapsed_seconds,
    )
    print(f"Wrote {summary_csv.relative_to(ROOT)}")
    print(f"Wrote {samples_csv.relative_to(ROOT)}")
    print(f"Wrote {summary_path.relative_to(ROOT)}")
    print(f"Wrote {manifest_path.relative_to(ROOT)}")
    print(f"Wrote {evaluation_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
