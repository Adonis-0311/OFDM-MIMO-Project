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


def saturation_depth(depth_curve: list[float], *, tolerance_db: float) -> int:
    final_best = min(depth_curve)
    for depth, value in enumerate(depth_curve):
        if value <= final_best + tolerance_db:
            return depth
    return len(depth_curve) - 1


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


def write_evaluation_summary(
    output_dir: Path,
    *,
    saturation_by_l: dict[int, int],
    mean_gain_k8_by_l: dict[int, float],
    elapsed_seconds: float,
) -> Path:
    depth_spread = max(saturation_by_l.values()) - min(saturation_by_l.values())
    status = "supported" if depth_spread >= 2 else "inconclusive"
    direction_note = (
        "The observed direction differs from the simple illustrative hypothesis: "
        "L=32 saturates earlier than L=2/L=8, consistent with a possible "
        "support/interference floor rather than unlimited benefit from deeper refinement."
        if saturation_by_l.get(32, 0) < saturation_by_l.get(2, 0)
        else "The observed direction matches the simple deeper-for-harder illustrative hypothesis."
    )
    lines = [
        "# Stage 3 A4 IA-AUD Depth Pre-Smoke Evaluation Summary",
        "",
        "## Outcome Summary",
        "",
        (
            "This pre-smoke tests whether fixed-depth repeated off-grid refinement has "
            "different saturation depths across target counts. It is a problem-existence "
            "check for IA-AUD, not the final gating-network experiment."
        ),
        "",
        "## evaluation_summary",
        "",
        "- `research_question`: Do simple and difficult target-count regimes show different NMSE-vs-depth saturation behavior?",
        f"- `claim_update`: {status} for IA-AUD problem-existence evidence.",
        "- `baseline_relation`: K=0 is grid Tensor-OMP support with LS amplitudes; K=1..8 adds repeated bounded off-grid refinement layers.",
        "- `failure_mode`: No execution failure; remaining limitation is pre-smoke sample count and proxy depth definition.",
        f"- `mechanism_note`: {direction_note}",
        "- `next_action`: If supported, implement A4 gating/FLOPs experiment; if inconclusive, avoid full IA-AUD investment until a stronger depth signal is found.",
        "- `evidence_level`: Stage-3 pre-smoke evidence only.",
        "",
        "## Key Metrics",
        "",
        f"- Saturation depths: {saturation_by_l}",
        f"- K=8 mean gains over K=0: {mean_gain_k8_by_l}",
        f"- Saturation-depth spread: {depth_spread}",
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
    n_trials = 2
    offset_radius = 0.35
    radii = [0.45, 0.28, 0.18, 0.11, 0.07, 0.045, 0.03, 0.02]
    search_points = 3
    tolerance_db = 0.5
    started = time.perf_counter()
    rng = seed_all(seed)

    sample_rows: list[dict[str, float]] = []
    summary_rows: list[dict[str, float]] = []
    saturation_by_l: dict[int, int] = {}
    mean_gain_k8_by_l: dict[int, float] = {}

    for n_targets in l_values:
        curves = [
            run_depth_curve(
                rng=rng,
                shape=shape,
                n_targets=n_targets,
                snr_db=snr_db,
                offset_radius=offset_radius,
                radii=radii,
                search_points=search_points,
            )
            for _ in range(n_trials)
        ]
        mean_curve = [finite_mean([curve[depth] for curve in curves]) for depth in range(len(radii) + 1)]
        sat_depth = saturation_depth(mean_curve, tolerance_db=tolerance_db)
        saturation_by_l[n_targets] = sat_depth
        mean_gain_k8_by_l[n_targets] = mean_curve[0] - mean_curve[-1]
        for trial, curve in enumerate(curves):
            for depth, nmse_db in enumerate(curve):
                sample_rows.append(
                    {
                        "n_targets": float(n_targets),
                        "trial": float(trial),
                        "depth": float(depth),
                        "nmse_db": nmse_db,
                        "gain_vs_k0_db": curve[0] - nmse_db,
                    }
                )
        for depth, nmse_db in enumerate(mean_curve):
            summary_rows.append(
                {
                    "n_targets": float(n_targets),
                    "depth": float(depth),
                    "mean_nmse_db": nmse_db,
                    "mean_gain_vs_k0_db": mean_curve[0] - nmse_db,
                    "saturation_depth": float(sat_depth),
                }
            )

    elapsed_seconds = time.perf_counter() - started
    output_dir = ROOT / "05_results" / "stage3_a4_depth_presmoke"
    output_dir.mkdir(parents=True, exist_ok=True)
    samples_csv = output_dir / "stage3_a4_depth_presmoke_samples.csv"
    with samples_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(sample_rows[0].keys()))
        writer.writeheader()
        writer.writerows(sample_rows)
    summary_csv = output_dir / "stage3_a4_depth_presmoke.csv"
    with summary_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    depth_spread = max(saturation_by_l.values()) - min(saturation_by_l.values())
    metrics = {
        "tensor_shape": "128x16x32",
        "snr_db": snr_db,
        "seed": seed,
        "l_values": l_values,
        "n_trials_per_l": n_trials,
        "depth_values": list(range(len(radii) + 1)),
        "radii": radii,
        "search_points": search_points,
        "saturation_tolerance_db": tolerance_db,
        "saturation_depth_by_l": saturation_by_l,
        "depth_spread": depth_spread,
        "mean_gain_k8_by_l": mean_gain_k8_by_l,
        "elapsed_seconds": elapsed_seconds,
    }
    notes = [
        "A4 pre-smoke uses repeated bounded off-grid refinement as the fixed-depth proxy.",
        "K=0 is grid Tensor-OMP support with LS amplitudes; K=1..8 applies progressively smaller local-search radii.",
        "This checks whether IA-AUD has a real depth-allocation opportunity before implementing a gating network.",
    ]
    manifest_path = write_run_manifest(
        output_dir,
        run_id="stage3_a4_depth_presmoke_20260624",
        command="python 04_experiments/eval/run_stage3_a4_depth_presmoke.py",
        config={
            "shape": shape,
            "snr_db": snr_db,
            "seed": seed,
            "l_values": l_values,
            "n_trials": n_trials,
            "offset_radius": offset_radius,
            "radii": radii,
            "search_points": search_points,
            "saturation_tolerance_db": tolerance_db,
        },
        metrics=metrics,
        notes=notes,
        cwd=ROOT,
    )
    summary_path = write_summary_md(
        output_dir,
        title="Stage 3 A4 IA-AUD Depth Pre-Smoke",
        config_hash="stage3-a4-depth-presmoke-20260624",
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
        saturation_by_l=saturation_by_l,
        mean_gain_k8_by_l=mean_gain_k8_by_l,
        elapsed_seconds=elapsed_seconds,
    )
    print(f"Wrote {summary_csv.relative_to(ROOT)}")
    print(f"Wrote {samples_csv.relative_to(ROOT)}")
    print(f"Wrote {summary_path.relative_to(ROOT)}")
    print(f"Wrote {manifest_path.relative_to(ROOT)}")
    print(f"Wrote {evaluation_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
