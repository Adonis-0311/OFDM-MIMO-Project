from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shard-prefix", default="tensor_nomp3d_matched_paper_seed_")
    parser.add_argument("--output-dir-name", default="tensor_nomp3d_matched_paper_5seed")
    return parser.parse_args()


def write_csv(path: Path, rows: list[dict]) -> None:
    fieldnames = list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    shards = sorted(path for path in (ROOT / "05_results").glob(f"{args.shard_prefix}*") if path.is_dir())
    if len(shards) != 5:
        raise RuntimeError(f"expected 5 seed shards, found {len(shards)}")
    rows: list[dict] = []
    manifests = []
    for shard in shards:
        with (shard / "matched_accuracy_rows.csv").open(encoding="utf-8", newline="") as handle:
            rows.extend(csv.DictReader(handle))
        manifests.append(json.loads((shard / "run_manifest.json").read_text(encoding="utf-8")))
    output_dir = ROOT / "05_results" / args.output_dir_name
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "matched_accuracy_rows.csv", rows)

    methods = sorted({row["method"] for row in rows})
    summary_rows = []
    for method in methods:
        selected = [row for row in rows if row["method"] == method]
        summary_rows.append({
            "method": method,
            "sample_count": len(selected),
            "mean_measurement_nmse_db": float(np.mean([float(row["measurement_nmse_db"]) for row in selected])),
            "mean_gain_vs_grid_db": float(np.mean([float(row["gain_vs_grid_db"]) for row in selected])),
            "mean_angle_bin_rmse": float(np.mean([float(row["angle_bin_rmse"]) for row in selected])),
            "mean_delay_bin_rmse": float(np.mean([float(row["delay_bin_rmse"]) for row in selected])),
            "mean_doppler_bin_rmse": float(np.mean([float(row["doppler_bin_rmse"]) for row in selected])),
            "mean_normalized_joint_bin_rmse": float(np.mean([float(row["normalized_joint_bin_rmse"]) for row in selected])),
            "mean_matched_fraction_within_half_bin": float(np.mean([float(row["matched_fraction_within_half_bin"]) for row in selected])),
            "median_wall_clock_ms": float(np.median([float(row["wall_clock_ms"]) for row in selected])),
        })
    write_csv(output_dir / "matched_accuracy_summary.csv", summary_rows)

    manifest = manifests[0]
    manifest["run_id"] = "e12_tensor_nomp_matched_paper_5seed_20260630"
    manifest["command"] = "five seed-sharded invocations of run_e12_tensor_nomp_matched_pilot.py; merged by merge_e12_seed_shards.py"
    manifest["config"]["seeds"] = sorted(
        int(seed) for item in manifests for seed in item["config"]["seeds"]
    )
    manifest["metrics"] = {
        "row_count": len(rows),
        "sample_count_per_method": len(rows) // len(methods),
        "claim_update": "paper-scale-matched-comparison-pending-verification",
    }
    manifest["notes"] = list(dict.fromkeys(
        note for item in manifests for note in item.get("notes", [])
    )) + ["Five independent seed shards were merged without changing sample or method rows."]
    (output_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"merged {len(rows)} rows from {len(shards)} shards into {output_dir}")


if __name__ == "__main__":
    main()
