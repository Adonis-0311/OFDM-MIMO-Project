from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from scipy.stats import t


ROOT = Path(__file__).resolve().parents[2]
METHODS = (
    "grid_fft_topk_plus_ls",
    "deterministic_cartesian_local_refinement_plus_ls",
    "fixed_source_trained_scalar_interpolation_plus_ls",
    "tensor_nomp3d_known_order_v1",
)
NOMP = METHODS[-1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir-name", default="tensor_nomp3d_matched_paper_5seed")
    return parser.parse_args()


def mean_ci95(values: list[float]) -> tuple[float, float, float]:
    array = np.asarray(values, dtype=float)
    center = float(np.mean(array))
    if array.size < 2:
        return center, float("nan"), float("nan")
    half = float(t.ppf(0.975, array.size - 1) * np.std(array, ddof=1) / np.sqrt(array.size))
    return center, center - half, center + half


def main() -> None:
    args = parse_args()
    output_dir = ROOT / "05_results" / args.input_dir_name
    rows = list(csv.DictReader((output_dir / "matched_accuracy_rows.csv").open(encoding="utf-8")))
    numeric = {
        "measurement_nmse_db",
        "gain_vs_grid_db",
        "angle_bin_rmse",
        "delay_bin_rmse",
        "doppler_bin_rmse",
        "normalized_joint_bin_rmse",
        "matched_fraction_within_half_bin",
        "wall_clock_ms",
    }
    for row in rows:
        for key in numeric:
            row[key] = float(row[key])
    key = lambda row: (row["seed"], row["snr_db"], row["n_targets"], row["sample_index"])
    paired: dict[tuple[str, ...], dict[str, dict]] = {}
    for row in rows:
        paired.setdefault(key(row), {})[row["method"]] = row
    if any(set(method_rows) != set(METHODS) for method_rows in paired.values()):
        raise RuntimeError("incomplete paired method rows")

    per_l = []
    for l_value in sorted({int(pair_key[2]) for pair_key in paired}):
        selected = [methods[NOMP] for pair_key, methods in paired.items() if int(pair_key[2]) == l_value]
        per_l.append({
            "n_targets": l_value,
            "sample_count": len(selected),
            "mean_nmse_db": float(np.mean([row["measurement_nmse_db"] for row in selected])),
            "median_nmse_db": float(np.median([row["measurement_nmse_db"] for row in selected])),
            "min_gain_vs_grid_db": float(np.min([row["gain_vs_grid_db"] for row in selected])),
            "max_normalized_joint_bin_rmse": float(np.max([row["normalized_joint_bin_rmse"] for row in selected])),
            "mean_within_half_bin": float(np.mean([row["matched_fraction_within_half_bin"] for row in selected])),
            "median_wall_clock_ms": float(np.median([row["wall_clock_ms"] for row in selected])),
        })

    cell_comparisons = []
    for snr_db in sorted({float(pair_key[1]) for pair_key in paired}):
        for l_value in sorted({int(pair_key[2]) for pair_key in paired}):
            selected_pairs = [
                (pair_key, methods)
                for pair_key, methods in paired.items()
                if float(pair_key[1]) == snr_db and int(pair_key[2]) == l_value
            ]
            nomp_runtime = np.median([methods[NOMP]["wall_clock_ms"] for _, methods in selected_pairs])
            scalar_runtime = np.median([methods[METHODS[2]]["wall_clock_ms"] for _, methods in selected_pairs])
            for comparator in METHODS[:-1]:
                seed_means = []
                for seed in sorted({pair_key[0] for pair_key, _ in selected_pairs}):
                    deltas = [
                        methods[comparator]["measurement_nmse_db"] - methods[NOMP]["measurement_nmse_db"]
                        for pair_key, methods in selected_pairs
                        if pair_key[0] == seed
                    ]
                    seed_means.append(float(np.mean(deltas)))
                center, low, high = mean_ci95(seed_means)
                cell_comparisons.append({
                    "snr_db": snr_db,
                    "n_targets": l_value,
                    "comparator": comparator,
                    "seed_mean_nomp_advantage_db": center,
                    "ci95_low_db": low,
                    "ci95_high_db": high,
                    "nomp_to_scalar_median_runtime_ratio": float(nomp_runtime / scalar_runtime),
                })

    comparisons = {}
    for comparator in METHODS[:-1]:
        deltas = [
            methods[comparator]["measurement_nmse_db"] - methods[NOMP]["measurement_nmse_db"]
            for methods in paired.values()
        ]
        seed_means = []
        for seed in sorted({pair_key[0] for pair_key in paired}):
            seed_deltas = [
                methods[comparator]["measurement_nmse_db"] - methods[NOMP]["measurement_nmse_db"]
                for pair_key, methods in paired.items()
                if pair_key[0] == seed
            ]
            seed_means.append(float(np.mean(seed_deltas)))
        center, low, high = mean_ci95(seed_means)
        comparisons[comparator] = {
            "mean_nomp_advantage_db": float(np.mean(deltas)),
            "median_nomp_advantage_db": float(np.median(deltas)),
            "min_nomp_advantage_db": float(np.min(deltas)),
            "nomp_win_fraction": float(np.mean(np.asarray(deltas) > 0.0)),
            "seed_mean_advantage_db": center,
            "seed_mean_advantage_ci95_low_db": low,
            "seed_mean_advantage_ci95_high_db": high,
            "seed_means_db": seed_means,
        }

    nomp_rows = [methods[NOMP] for methods in paired.values()]
    scalar_rows = [methods[METHODS[2]] for methods in paired.values()]
    runtime_ratio = float(
        np.median([row["wall_clock_ms"] for row in nomp_rows])
        / np.median([row["wall_clock_ms"] for row in scalar_rows])
    )
    analysis = {
        "verification_verdict": "trusted_with_caveats",
        "baseline_acceptance_target": "comparison_ready",
        "paired_sample_count": len(paired),
        "nomp_min_gain_vs_grid_db": float(np.min([row["gain_vs_grid_db"] for row in nomp_rows])),
        "nomp_max_normalized_joint_bin_rmse": float(np.max([row["normalized_joint_bin_rmse"] for row in nomp_rows])),
        "nomp_min_within_half_bin": float(np.min([row["matched_fraction_within_half_bin"] for row in nomp_rows])),
        "nomp_to_scalar_median_runtime_ratio": runtime_ratio,
        "per_l": per_l,
        "per_snr_l_comparisons": cell_comparisons,
        "paired_comparisons": comparisons,
        "claim_update": "oversampled-continuous-comparator-dominates-matched-synthetic-at-runtime-cost",
    }
    (output_dir / "analysis_summary.json").write_text(
        json.dumps(analysis, indent=2) + "\n", encoding="utf-8"
    )
    with (output_dir / "per_snr_l_comparisons.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(cell_comparisons[0]))
        writer.writeheader()
        writer.writerows(cell_comparisons)
    lines = [
        "# E12 matched-accuracy verification",
        "",
        "Verdict: `trusted_with_caveats` for a comparison-ready 3-D cyclic NOMP-inspired baseline.",
        "",
        f"- Paired paper-scale samples: {len(paired)}",
        f"- Minimum NOMP-inspired gain over grid: {analysis['nomp_min_gain_vs_grid_db']:.4f} dB",
        f"- Maximum normalized joint-bin RMSE: {analysis['nomp_max_normalized_joint_bin_rmse']:.6g}",
        f"- Minimum all-axis half-bin hit fraction: {analysis['nomp_min_within_half_bin']:.4f}",
        f"- Median runtime ratio versus fixed scalar path: {runtime_ratio:.3f}x",
        "",
        "## Per-target-count NOMP-inspired result",
        "",
        "| L | n | Mean NMSE (dB) | Median NMSE (dB) | Min gain vs grid (dB) | Max joint-bin RMSE | Half-bin hit | Median ms |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in per_l:
        lines.append(
            f"| {row['n_targets']} | {row['sample_count']} | {row['mean_nmse_db']:.4f} | "
            f"{row['median_nmse_db']:.4f} | {row['min_gain_vs_grid_db']:.4f} | "
            f"{row['max_normalized_joint_bin_rmse']:.6g} | {row['mean_within_half_bin']:.4f} | "
            f"{row['median_wall_clock_ms']:.2f} |"
        )
    lines.extend(["", "## Paired NMSE comparisons", ""])
    for comparator, item in comparisons.items():
        lines.append(
            f"- `{comparator}`: NOMP advantage mean {item['mean_nomp_advantage_db']:.4f} dB; "
            f"median {item['median_nomp_advantage_db']:.4f} dB; minimum {item['min_nomp_advantage_db']:.4f} dB; "
            f"win fraction {item['nomp_win_fraction']:.4f}; seed-mean 95% CI "
            f"[{item['seed_mean_advantage_ci95_low_db']:.4f}, {item['seed_mean_advantage_ci95_high_db']:.4f}] dB."
        )
    lines.extend([
        "",
        "## Scope boundary",
        "",
        "- The comparator uses known target count, dense tensor measurements, and a matched sinusoidal generator.",
        "- It is a 3-D mechanism adaptation, not a reproduction of sparse-resource 2-D NOMP-OFDM-ISAC or its CFAR rule.",
        "- The result refutes any accuracy-superiority claim for the current learned scalar in the matched synthetic regime.",
        "- The remaining defensible question is whether learning can amortize continuous refinement cost or improve shifted/external regimes.",
        "- Per-SNR/per-L seed-mean confidence intervals and runtime ratios are retained in `per_snr_l_comparisons.csv`.",
    ])
    (output_dir / "verification.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    manifest_path = output_dir / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["metrics"].update({
        "claim_update": analysis["claim_update"],
        "nomp_min_gain_vs_grid_db": analysis["nomp_min_gain_vs_grid_db"],
        "nomp_max_normalized_joint_bin_rmse": analysis["nomp_max_normalized_joint_bin_rmse"],
        "nomp_min_within_half_bin": analysis["nomp_min_within_half_bin"],
        "nomp_to_scalar_median_runtime_ratio": runtime_ratio,
        "nomp_min_advantage_vs_scalar_db": comparisons[METHODS[2]]["min_nomp_advantage_db"],
        "nomp_seed_mean_advantage_vs_scalar_ci95_low_db": comparisons[METHODS[2]]["seed_mean_advantage_ci95_low_db"],
        "nomp_seed_mean_advantage_vs_scalar_ci95_high_db": comparisons[METHODS[2]]["seed_mean_advantage_ci95_high_db"],
    })
    manifest["notes"].append(
        "Post-run paired verification accepts the comparator as trusted_with_caveats and refutes learned-scalar accuracy superiority in this matched synthetic regime."
    )
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(analysis, indent=2))


if __name__ == "__main__":
    main()
