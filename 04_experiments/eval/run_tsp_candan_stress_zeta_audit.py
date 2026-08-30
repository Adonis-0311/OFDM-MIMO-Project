"""Controlled 48-cell Candan, residual-gate, and zeta evidence audit."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

import numpy as np
from scipy.stats import t as student_t


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_active_modules"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from baseline.local_refinement import axiswise_candan_diagnostics  # noqa: E402
from common.tsp_revision_metrics import (  # noqa: E402
    distinct_pair_metrics,
    matched_component_metrics,
    write_release_metadata,
)
from data.offgrid_tensor import (  # noqa: E402
    estimate_from_bins_lstsq,
    measurement_nmse_db,
    topk_grid_bins,
)
from run_tsp_separation_nearfar_stress import (  # noqa: E402
    controlled_scene,
    residual_fraction,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shape", type=int, nargs=3, default=(128, 16, 32))
    parser.add_argument("--n-targets", type=int, default=4)
    parser.add_argument("--separations", type=float, nargs="+", default=(0.25, 0.5, 1.0, 2.0))
    parser.add_argument("--dynamic-ranges-db", type=float, nargs="+", default=(0.0, 10.0, 20.0))
    parser.add_argument("--snrs", type=float, nargs="+", default=(0.0, 10.0, 20.0, 30.0))
    parser.add_argument("--validation-seeds", type=int, nargs="+", default=(20260820, 20260821))
    parser.add_argument(
        "--test-seeds", type=int, nargs="+",
        default=(20260822, 20260823, 20260824, 20260825, 20260826),
    )
    parser.add_argument("--samples-per-cell-seed", type=int, default=5)
    parser.add_argument("--zeta-bins", type=int, default=10)
    parser.add_argument("--output-dir-name", default="tsp_candan_stress_zeta_audit_paper")
    return parser.parse_args()


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty CSV: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def seed_mean_ci(rows: list[dict[str, object]], key: str) -> tuple[float, float, float]:
    seeds = sorted({int(row["seed"]) for row in rows})
    values = np.asarray([
        np.mean([float(row[key]) for row in rows if int(row["seed"]) == seed])
        for seed in seeds
    ])
    center = float(np.mean(values))
    if len(values) < 2:
        return center, center, center
    half = float(student_t.ppf(0.975, len(values) - 1) * np.std(values, ddof=1) / np.sqrt(len(values)))
    return center, center - half, center + half


def candidate_thresholds(values: np.ndarray) -> np.ndarray:
    unique = np.unique(values)
    if unique.size == 1:
        return unique
    return np.concatenate(([unique[0]], (unique[:-1] + unique[1:]) / 2.0, [np.nextafter(unique[-1], np.inf)]))


def calibrate_gate(rows: list[dict[str, object]]) -> dict[str, float]:
    residual = np.asarray([float(row["candan_residual_reduction_fraction"]) for row in rows])
    gains = np.asarray([float(row["candan_gain_vs_grid_db"]) for row in rows])
    candidates = []
    for threshold in candidate_thresholds(residual):
        accepted = residual >= threshold
        candidates.append((float(np.mean(np.where(accepted, gains, 0.0))), -float(np.mean(accepted)), float(threshold)))
    gain, negative_pass, threshold = max(candidates)
    return {"threshold": threshold, "validation_gated_gain_db": gain, "validation_pass_rate": -negative_pass}


def evaluate_scene(
    measurement: np.ndarray,
    clean: np.ndarray,
    truth: np.ndarray,
    shape: tuple[int, int, int],
    n_targets: int,
) -> dict[str, object]:
    coarse = np.asarray(topk_grid_bins(measurement, n_targets), dtype=float)
    grid_estimate = estimate_from_bins_lstsq(measurement, shape, [tuple(row) for row in coarse])
    candan = axiswise_candan_diagnostics(measurement, coarse)
    candan_estimate = estimate_from_bins_lstsq(measurement, shape, [tuple(row) for row in candan.bins])
    grid_nmse = measurement_nmse_db(grid_estimate, clean)
    candan_nmse = measurement_nmse_db(candan_estimate, clean)
    grid_metrics = matched_component_metrics(coarse, truth, shape)
    candan_metrics = matched_component_metrics(candan.bins, truth, shape)
    grid_pair = distinct_pair_metrics(coarse, truth, shape)
    candan_pair = distinct_pair_metrics(candan.bins, truth, shape)
    grid_hits = np.asarray(grid_metrics["hits_by_truth"], dtype=bool)
    candan_hits = np.asarray(candan_metrics["hits_by_truth"], dtype=bool)
    return {
        "grid_nmse_db": grid_nmse,
        "candan_nmse_db": candan_nmse,
        "candan_gain_vs_grid_db": grid_nmse - candan_nmse,
        "grid_per_component_hit": grid_metrics["per_component_hit_rate"],
        "candan_per_component_hit": candan_metrics["per_component_hit_rate"],
        "grid_designated_pair_assignment": float(np.all(grid_hits[:2])),
        "candan_designated_pair_assignment": float(np.all(candan_hits[:2])),
        "grid_strict_recovery": grid_pair["distinct_pair_recovery"],
        "candan_strict_recovery": candan_pair["distinct_pair_recovery"],
        "grid_strong_hit": float(grid_hits[0]),
        "candan_strong_hit": float(candan_hits[0]),
        "grid_weak_hit": float(grid_hits[1]),
        "candan_weak_hit": float(candan_hits[1]),
        "grid_all_target_hit": float(grid_metrics["all_components_hit"]),
        "candan_all_target_hit": float(candan_metrics["all_components_hit"]),
        "grid_mean_coordinate_error_bins": grid_metrics["mean_absolute_bin_error"],
        "candan_mean_coordinate_error_bins": candan_metrics["mean_absolute_bin_error"],
        "candan_residual_reduction_fraction": residual_fraction(measurement, grid_estimate)
        - residual_fraction(measurement, candan_estimate),
        "candan_minimum_zeta": candan.minimum_denominator_stability,
        "candan_mean_zeta": candan.mean_denominator_stability,
        "candan_clipping_rate": candan.clipping_rate,
        "candan_any_clipping": float(candan.clipping_rate > 0.0),
    }


def summarize_cells(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    output = []
    cells = sorted({(float(r["separation_bins"]), float(r["dynamic_range_db"]), float(r["snr_db"])) for r in rows})
    metrics = [
        "candan_gain_vs_grid_db", "gated_candan_gain_vs_grid_db", "grid_per_component_hit",
        "candan_per_component_hit", "gated_candan_per_component_hit",
        "grid_designated_pair_assignment", "candan_designated_pair_assignment",
        "gated_candan_designated_pair_assignment", "grid_strict_recovery",
        "candan_strict_recovery", "gated_candan_strict_recovery", "grid_strong_hit",
        "candan_strong_hit", "gated_candan_strong_hit", "grid_weak_hit",
        "candan_weak_hit", "gated_candan_weak_hit", "candan_clipping_rate",
        "candan_any_clipping", "candan_minimum_zeta", "gate_pass",
    ]
    for separation, dynamic_range, snr_db in cells:
        selected = [r for r in rows if float(r["separation_bins"]) == separation and float(r["dynamic_range_db"]) == dynamic_range and float(r["snr_db"]) == snr_db]
        item: dict[str, object] = {
            "separation_bins": separation,
            "dynamic_range_db": dynamic_range,
            "snr_db": snr_db,
            "scene_count": len(selected),
            "seed_count": len({int(r["seed"]) for r in selected}),
        }
        for key in metrics:
            center, low, high = seed_mean_ci(selected, key)
            if key not in {"candan_gain_vs_grid_db", "gated_candan_gain_vs_grid_db", "candan_minimum_zeta"}:
                low, high = max(0.0, low), min(1.0, high)
            item[f"mean_{key}"] = center
            item[f"{key}_ci95_low"] = low
            item[f"{key}_ci95_high"] = high
        output.append(item)
    return output


def zeta_bins(rows: list[dict[str, object]], count: int) -> list[dict[str, object]]:
    zeta = np.asarray([float(r["candan_minimum_zeta"]) for r in rows])
    edges = np.unique(np.quantile(zeta, np.linspace(0.0, 1.0, count + 1)))
    if edges.size == 1:
        edges = np.asarray([edges[0], np.nextafter(edges[0], np.inf)])
    output = []
    for index, (low, high) in enumerate(zip(edges[:-1], edges[1:])):
        selected = [r for r in rows if float(r["candan_minimum_zeta"]) >= low and (float(r["candan_minimum_zeta"]) <= high if index == len(edges) - 2 else float(r["candan_minimum_zeta"]) < high)]
        output.append({
            "zeta_bin": index + 1, "zeta_low": float(low), "zeta_high": float(high),
            "scene_count": len(selected),
            "beneficial_probability": float(np.mean([float(r["candan_gain_vs_grid_db"]) > 0.0 for r in selected])),
            "mean_clean_gain_db": float(np.mean([float(r["candan_gain_vs_grid_db"]) for r in selected])),
            "median_coordinate_error_bins": float(np.median([float(r["candan_mean_coordinate_error_bins"]) for r in selected])),
            "mean_clipping_rate": float(np.mean([float(r["candan_clipping_rate"]) for r in selected])),
            "any_clipping_probability": float(np.mean([float(r["candan_any_clipping"]) for r in selected])),
            "gate_pass_rate": float(np.mean([float(r["gate_pass"]) for r in selected])),
        })
    return output


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    args = parse_args()
    shape = tuple(int(v) for v in args.shape)
    started = time.perf_counter()
    rows: list[dict[str, object]] = []
    for split, seeds in (("validation", args.validation_seeds), ("test", args.test_seeds)):
        for seed in seeds:
            rng = np.random.default_rng(seed)
            for separation in args.separations:
                for dynamic_range_db in args.dynamic_ranges_db:
                    for snr_db in args.snrs:
                        for sample_index in range(args.samples_per_cell_seed):
                            pair_axis = sample_index % 3
                            measurement, clean, truth, _, _ = controlled_scene(
                                rng, shape=shape, n_targets=args.n_targets,
                                separation_bins=separation, dynamic_range_db=dynamic_range_db,
                                snr_db=snr_db, pair_axis=pair_axis,
                            )
                            row = {
                                "split": split, "seed": seed, "separation_bins": separation,
                                "dynamic_range_db": dynamic_range_db, "snr_db": snr_db,
                                "sample_index": sample_index, "pair_axis": pair_axis,
                            }
                            row.update(evaluate_scene(measurement, clean, truth, shape, args.n_targets))
                            rows.append(row)
    validation = [r for r in rows if r["split"] == "validation"]
    test = [r for r in rows if r["split"] == "test"]
    gate = calibrate_gate(validation)
    threshold = float(gate["threshold"])
    for row in rows:
        passed = float(row["candan_residual_reduction_fraction"]) >= threshold
        row["gate_pass"] = int(passed)
        row["gated_candan_gain_vs_grid_db"] = float(row["candan_gain_vs_grid_db"]) if passed else 0.0
        for suffix in ["per_component_hit", "designated_pair_assignment", "strict_recovery", "strong_hit", "weak_hit", "all_target_hit", "mean_coordinate_error_bins"]:
            row[f"gated_candan_{suffix}"] = row[f"candan_{suffix}"] if passed else row[f"grid_{suffix}"]
    cells = summarize_cells(test)
    zeta = zeta_bins(test, args.zeta_bins)
    overall = {
        "validation_scene_count": len(validation), "test_scene_count": len(test),
        "cell_count": len(cells), "gate": gate,
        "mean_candan_gain_db": float(np.mean([float(r["candan_gain_vs_grid_db"]) for r in test])),
        "mean_gated_candan_gain_db": float(np.mean([float(r["gated_candan_gain_vs_grid_db"]) for r in test])),
        "minimum_cell_candan_gain_db": min(float(r["mean_candan_gain_vs_grid_db"]) for r in cells),
        "minimum_cell_gated_candan_gain_db": min(float(r["mean_gated_candan_gain_vs_grid_db"]) for r in cells),
        "gate_pass_rate": float(np.mean([float(r["gate_pass"]) for r in test])),
        "minimum_zeta_quantiles": {str(q): float(np.quantile([float(r["candan_minimum_zeta"]) for r in test], q)) for q in (0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99)},
        "clipping_rate": float(np.mean([float(r["candan_clipping_rate"]) for r in test])),
        "elapsed_seconds": time.perf_counter() - started,
    }
    output = ROOT / "05_results" / args.output_dir_name
    output.mkdir(parents=True, exist_ok=True)
    write_csv(output / "per_scene.csv", rows)
    write_csv(output / "candan_48cell_summary.csv", cells)
    write_csv(output / "zeta_binned_evidence.csv", zeta)
    (output / "summary.json").write_text(json.dumps(overall, indent=2) + "\n", encoding="utf-8")
    command = "python 04_experiments/eval/run_tsp_candan_stress_zeta_audit.py"
    write_release_metadata(
        output, config=vars(args),
        seeds=[*[{"split": "validation", "seed": s} for s in args.validation_seeds], *[{"split": "test", "seed": s} for s in args.test_seeds]],
        command=command,
    )
    code_path = Path(__file__).resolve()
    manifest = {
        "run_id": "tsp_candan_stress_zeta_audit_20260830",
        "command": command, "cwd": str(ROOT), "config": vars(args), "metrics": overall,
        "software": {"python": sys.version, "numpy": np.__version__, "platform": platform.platform()},
        "code_sha256": {str(code_path.relative_to(ROOT)): sha256(code_path)},
        "git_commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False).stdout.strip(),
        "notes": [
            "The scalar residual threshold is selected only on the two controlled-stress validation seeds.",
            "Every reported interval is a Student-t interval over the five test-seed means.",
            "All coordinate metrics use Hungarian truth assignment with periodic bin distances.",
        ],
    }
    (output / "audit_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(overall, indent=2))


if __name__ == "__main__":
    main()
