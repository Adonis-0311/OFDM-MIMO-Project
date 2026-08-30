"""Create balanced support-quality strata from the full-offset experiment."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

import numpy as np
from scipy.stats import t as student_t


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_active_modules"))

from common.manifest import write_run_manifest  # noqa: E402
from common.tsp_revision_metrics import write_csv, write_release_metadata  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir-name", default="tsp_full_offset_sweep_paper")
    parser.add_argument("--output-dir-name", default="tsp_support_quality_stratification_paper")
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def summarize(
    stratum_type: str, stratum: str, rows: list[dict[str, str]]
) -> dict[str, object]:
    def seed_mean_ci(key: str) -> tuple[float, float, float]:
        seed_means = np.asarray(
            [
                np.mean([float(row[key]) for row in rows if int(row["seed"]) == seed])
                for seed in sorted({int(row["seed"]) for row in rows})
            ],
            dtype=float,
        )
        center = float(np.mean(seed_means))
        if len(seed_means) < 2:
            return center, center, center
        half_width = float(
            student_t.ppf(0.975, len(seed_means) - 1)
            * np.std(seed_means, ddof=1)
            / np.sqrt(len(seed_means))
        )
        return center, center - half_width, center + half_width

    gain, gain_low, gain_high = seed_mean_ci("local_gain_vs_grid_db")
    correctness, correctness_low, correctness_high = seed_mean_ci(
        "candidate_axis_correctness"
    )
    return {
        "stratum_type": stratum_type,
        "stratum": stratum,
        "scene_count": len(rows),
        "seed_count": len({int(row["seed"]) for row in rows}),
        "mean_q_sup": float(np.mean([float(row["q_sup"]) for row in rows])),
        "mean_duplicate_neighborhood_rate": float(
            np.mean([float(row["duplicate_neighborhood_rate"]) for row in rows])
        ),
        "mean_coarse_design_condition": float(
            np.mean([float(row["coarse_design_condition"]) for row in rows])
        ),
        "mean_refined_design_condition": float(
            np.mean([float(row["refined_design_condition"]) for row in rows])
        ),
        "mean_local_gain_vs_grid_db": gain,
        "local_gain_ci95_low_db": gain_low,
        "local_gain_ci95_high_db": gain_high,
        "mean_gated_gain_vs_grid_db": float(
            np.mean([float(row["gated_gain_vs_grid_db"]) for row in rows])
        ),
        "mean_local_per_component_hit": float(
            np.mean(
                [
                    float(row["cartesian_local_joint_ls_per_component_half_bin_hit"])
                    for row in rows
                ]
            )
        ),
        "mean_candidate_axis_correctness": correctness,
        "candidate_axis_correctness_ci95_low": correctness_low,
        "candidate_axis_correctness_ci95_high": correctness_high,
        "local_harmful_update_rate": float(
            np.mean([float(row["harmful_local_update"]) for row in rows])
        ),
    }


def main() -> None:
    args = parse_args()
    source = ROOT / "05_results" / args.source_dir_name
    rows = [row for row in read_csv(source / "per_scene.csv") if row["split"] == "test"]
    output_rows: list[dict[str, object]] = []

    for quality in sorted({float(row["q_sup"]) for row in rows}):
        selected = [row for row in rows if float(row["q_sup"]) == quality]
        output_rows.append(summarize("coarse_support_quality", f"q_sup={quality:.3f}", selected))

    output_rows.append(
        summarize(
            "duplicate_neighborhood",
            "none",
            [row for row in rows if float(row["duplicate_neighborhood_rate"]) == 0.0],
        )
    )
    output_rows.append(
        summarize(
            "duplicate_neighborhood",
            "present",
            [row for row in rows if float(row["duplicate_neighborhood_rate"]) > 0.0],
        )
    )

    sorted_by_condition = sorted(
        rows,
        key=lambda row: (
            float(row["coarse_design_condition"]),
            int(row["seed"]),
            float(row["snr_db"]),
            int(row["n_targets"]),
            int(row["sample_index"]),
        ),
    )
    for quartile_index, indices in enumerate(
        np.array_split(np.arange(len(sorted_by_condition)), 4), start=1
    ):
        selected = [sorted_by_condition[int(index)] for index in indices]
        output_rows.append(
            summarize("coarse_condition_rank_quartile", f"Q{quartile_index}", selected)
        )

    separation_groups = (
        ("<1 bin", lambda value: value < 1.0),
        ("1--2 bins", lambda value: 1.0 <= value < 2.0),
        (">=2 bins", lambda value: value >= 2.0),
    )
    for label, predicate in separation_groups:
        selected = [
            row for row in rows if predicate(float(row["minimum_true_separation_bins"]))
        ]
        if selected:
            output_rows.append(summarize("minimum_true_separation", label, selected))

    output = ROOT / "05_results" / args.output_dir_name
    write_csv(output / "support_quality_strata.csv", output_rows)
    config = vars(args) | {"test_scene_count": len(rows)}
    result = {"config": config, "strata": output_rows}
    (output / "summary.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    command = "python 04_experiments/eval/run_tsp_support_quality_stratification.py"
    write_release_metadata(
        output,
        config=config,
        seeds=[{"split": "test", "seed": seed} for seed in sorted({int(row["seed"]) for row in rows})],
        command=command,
    )
    write_run_manifest(
        output,
        run_id="tsp_support_quality_stratification_paper_20260829",
        command=command,
        config=config,
        metrics={"test_scene_count": len(rows), "stratum_count": len(output_rows)},
        notes=[
            "Balanced rank quartiles preserve all tied conditioning values while keeping equal scene counts.",
            "Support coverage, duplicate neighborhoods, conditioning, and minimum separation are reported on the same full-offset scenes.",
        ],
        cwd=ROOT,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
