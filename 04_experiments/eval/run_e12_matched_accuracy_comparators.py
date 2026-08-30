from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
import time

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_active_modules"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from baseline.subspace_tensor import complex_parafac_als
from common.manifest import write_run_manifest
from common.seed import seed_all
from data.offgrid_tensor import (
    estimate_from_bins_lstsq,
    generate_offgrid_tensor_sample,
    measurement_nmse_db,
)
from run_e12_tensor_nomp_matched_pilot import matched_bin_metrics, truth_bins


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shape", type=int, nargs=3, default=(128, 16, 32))
    parser.add_argument("--l-values", type=int, nargs="+", default=(2, 4, 8))
    parser.add_argument("--snrs", type=float, nargs="+", default=(0.0, 10.0, 20.0, 30.0))
    parser.add_argument(
        "--seeds", type=int, nargs="+",
        default=(20260630, 20260701, 20260702, 20260703, 20260704),
    )
    parser.add_argument("--samples-per-cell-seed", type=int, default=20)
    parser.add_argument("--offset-radius", type=float, default=0.35)
    parser.add_argument("--parafac-iterations", type=int, default=10)
    parser.add_argument("--output-dir-name", default="e12_matched_accuracy_comparators")
    return parser.parse_args()


def factor_frequency_bin(factor: np.ndarray) -> float:
    adjacent = factor[1:] * np.conj(factor[:-1])
    phase = float(np.angle(np.sum(adjacent)))
    return float(np.mod(phase * factor.size / (2.0 * np.pi), factor.size))


def parafac_bins(factors: tuple[np.ndarray, np.ndarray, np.ndarray]) -> np.ndarray:
    rank = factors[0].shape[1]
    return np.asarray(
        [[factor_frequency_bin(factors[axis][:, component]) for axis in range(3)] for component in range(rank)],
        dtype=float,
    )


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    shape = tuple(args.shape)
    output_dir = ROOT / "05_results" / args.output_dir_name
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    for seed in args.seeds:
        rng = seed_all(seed)
        for snr_db in args.snrs:
            for n_targets in args.l_values:
                for sample_index in range(args.samples_per_cell_seed):
                    sample = generate_offgrid_tensor_sample(
                        rng=rng,
                        shape=shape,
                        n_targets=n_targets,
                        snr_db=snr_db,
                        offset_radius=args.offset_radius,
                    )
                    started = time.perf_counter()
                    _, factors = complex_parafac_als(
                        sample.measurement,
                        rank=n_targets,
                        iterations=args.parafac_iterations,
                        seed=seed + sample_index + 1000 * n_targets,
                    )
                    elapsed_ms = (time.perf_counter() - started) * 1000.0
                    bins = parafac_bins(factors)
                    reconstruction = estimate_from_bins_lstsq(
                        sample.measurement, shape, [tuple(item) for item in bins]
                    )
                    metrics = matched_bin_metrics(bins, truth_bins(sample), shape)
                    rows.append({
                        "seed": seed,
                        "snr_db": snr_db,
                        "n_targets": n_targets,
                        "sample_index": sample_index,
                        "method": "complex_parafac_als_10_sweeps",
                        "measurement_nmse_db": measurement_nmse_db(reconstruction, sample.clean),
                        **metrics,
                        "wall_clock_ms": elapsed_ms,
                        "failed": int(not np.all(np.isfinite(bins))),
                    })

    write_csv(output_dir / "matched_accuracy_rows.csv", rows)
    summary_rows = []
    for snr_db in args.snrs:
        for n_targets in args.l_values:
            selected = [r for r in rows if r["snr_db"] == snr_db and r["n_targets"] == n_targets]
            summary_rows.append({
                "method": "complex_parafac_als_10_sweeps",
                "snr_db": snr_db,
                "n_targets": n_targets,
                "sample_count": len(selected),
                "mean_measurement_nmse_db": float(np.mean([r["measurement_nmse_db"] for r in selected])),
                "mean_normalized_joint_bin_rmse": float(np.mean([r["normalized_joint_bin_rmse"] for r in selected])),
                "mean_matched_fraction_within_half_bin": float(np.mean([r["matched_fraction_within_half_bin"] for r in selected])),
                "median_wall_clock_ms": float(np.median([r["wall_clock_ms"] for r in selected])),
                "failure_rate": float(np.mean([r["failed"] for r in selected])),
            })
    write_csv(output_dir / "matched_accuracy_summary.csv", summary_rows)

    limitations = {
        "separable_forward_backward_esprit": (
            "timing-only: the implementation estimates an unordered marginal frequency set on each axis "
            "and has no cross-axis component pairing, so channel NMSE and joint target RMSE would not be matched fairly"
        ),
        "complex_parafac_als_10_sweeps": (
            "matched accuracy reported; factor columns provide cross-axis pairing, and LS reconstruction uses the inferred bins"
        ),
    }
    metrics = {
        "row_count": len(rows),
        "parafac_mean_nmse_db": float(np.mean([r["measurement_nmse_db"] for r in rows])),
        "parafac_mean_joint_bin_rmse": float(np.mean([r["normalized_joint_bin_rmse"] for r in rows])),
        "parafac_failure_rate": float(np.mean([r["failed"] for r in rows])),
        "comparator_limitations": limitations,
    }
    write_run_manifest(
        output_dir,
        run_id="e12_matched_accuracy_comparators_20260630",
        command="python 04_experiments/eval/run_e12_matched_accuracy_comparators.py",
        config=vars(args) | {"shape": list(shape)},
        metrics=metrics,
        notes=[
            "Samples replay the exact E12 seed/SNR/L/generator contract.",
            limitations["separable_forward_backward_esprit"],
            limitations["complex_parafac_als_10_sweeps"],
        ],
        cwd=ROOT,
    )
    (output_dir / "summary.json").write_text(
        json.dumps({"summary_rows": summary_rows, "metrics": metrics}, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "verification.md").write_text(
        "# E12 matched comparator verification\n\n"
        f"- PARAFAC rows: {len(rows)}; failure rate: {metrics['parafac_failure_rate']:.4f}.\n"
        f"- Mean PARAFAC measurement NMSE: {metrics['parafac_mean_nmse_db']:.4f} dB.\n"
        f"- ESPRIT: {limitations['separable_forward_backward_esprit']}.\n"
        "- No comparator row is silently omitted.\n",
        encoding="utf-8",
    )
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
