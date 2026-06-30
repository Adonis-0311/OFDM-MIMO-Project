from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_active_modules"))

from common.manifest import write_run_manifest


DATASETS = {
    "o1_60": {
        "label": "DeepMIMO O1_60",
        "directory_pattern": "deepmimo_o1_60_source_alpha_n{n_users}_seed_{seed}",
        "paper_role": "E2 ray-traced scalar source-alpha transfer robustness",
    },
    "i3_60": {
        "label": "DeepMIMO I3_60",
        "directory_pattern": "deepmimo_i3_60_source_alpha_n{n_users}_seed_{seed}",
        "paper_role": "E3 indoor cross-scenario scalar source-alpha transfer robustness",
    },
}

METRIC_KEYS = (
    "mean_grid_channel_nmse_db_all",
    "mean_source_alpha_channel_nmse_db_all",
    "mean_source_alpha_gain_vs_grid_db",
    "min_source_alpha_gain_vs_grid_db",
    "mean_source_alpha_gap_vs_oracle_db",
    "min_mean_support_recall",
    "mean_dominant_energy_recall_all",
    "elapsed_seconds",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--seeds",
        nargs="+",
        type=int,
        default=[20260626, 20260627, 20260628, 20260629, 20260630],
    )
    parser.add_argument("--n-users", type=int, default=100)
    parser.add_argument(
        "--output-dir-name",
        default="deepmimo_source_alpha_seed_campaign",
    )
    return parser.parse_args()


def load_seed_rows(*, seeds: list[int], n_users: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    reference_contract: dict[str, Any] | None = None
    for dataset_key, spec in DATASETS.items():
        for seed in seeds:
            directory = spec["directory_pattern"].format(n_users=n_users, seed=seed)
            manifest_path = ROOT / "05_results" / directory / "run_manifest.json"
            if not manifest_path.exists():
                raise FileNotFoundError(f"Missing campaign manifest: {manifest_path}")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            config = manifest["config"]
            metrics = manifest["metrics"]
            if int(config["seed"]) != seed or int(config["n_users"]) != n_users:
                raise ValueError(f"Seed/user contract mismatch in {manifest_path}")
            contract = {
                "snrs": config["snrs"],
                "l_values": config["l_values"],
                "num_subcarriers": config["num_subcarriers"],
                "subcarrier_spacing_hz": config["subcarrier_spacing_hz"],
                "source_alpha": config["source_alpha"],
                "candidate_alphas": config["candidate_alphas"],
                "search_radius": config["search_radius"],
                "search_points": config["search_points"],
            }
            if reference_contract is None:
                reference_contract = contract
            elif contract != reference_contract:
                raise ValueError(f"Evaluation contract mismatch in {manifest_path}")
            values = {key: float(metrics[key]) for key in METRIC_KEYS}
            if not np.all(np.isfinite(list(values.values()))):
                raise ValueError(f"Non-finite campaign metric in {manifest_path}")
            rows.append(
                {
                    "dataset_key": dataset_key,
                    "dataset": spec["label"],
                    "paper_role": spec["paper_role"],
                    "seed": seed,
                    "n_users": n_users,
                    "run_id": manifest["run_id"],
                    "transfer_proxy_classification": metrics[
                        "transfer_proxy_classification"
                    ],
                    "source_alpha": float(metrics["source_alpha"]),
                    **values,
                    "manifest_path": str(manifest_path.relative_to(ROOT)),
                }
            )
    return rows


def mean_ci(values: list[float]) -> tuple[float, float, float, float]:
    array = np.asarray(values, dtype=float)
    mean = float(np.mean(array))
    if array.size < 2:
        return mean, 0.0, mean, mean
    std = float(np.std(array, ddof=1))
    margin = float(stats.t.ppf(0.975, df=array.size - 1) * std / np.sqrt(array.size))
    return mean, std, mean - margin, mean + margin


def campaign_classification(classifications: list[str]) -> str:
    normalized = {value.lower() for value in classifications}
    if "fail" in normalized:
        return "fail"
    if "partial" in normalized:
        return "partial"
    if normalized == {"weak"}:
        return "weak"
    raise ValueError(f"Unexpected transfer classifications: {sorted(normalized)}")


def aggregate_rows(seed_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    aggregate: list[dict[str, Any]] = []
    for dataset_key, spec in DATASETS.items():
        rows = [row for row in seed_rows if row["dataset_key"] == dataset_key]
        gain_mean, gain_std, gain_ci_low, gain_ci_high = mean_ci(
            [row["mean_source_alpha_gain_vs_grid_db"] for row in rows]
        )
        grid_mean, grid_std, grid_ci_low, grid_ci_high = mean_ci(
            [row["mean_grid_channel_nmse_db_all"] for row in rows]
        )
        source_mean, source_std, source_ci_low, source_ci_high = mean_ci(
            [row["mean_source_alpha_channel_nmse_db_all"] for row in rows]
        )
        gap_mean, gap_std, gap_ci_low, gap_ci_high = mean_ci(
            [row["mean_source_alpha_gap_vs_oracle_db"] for row in rows]
        )
        classification = campaign_classification(
            [row["transfer_proxy_classification"] for row in rows]
        )
        claim_update = {
            "weak": "scaled-source-alpha-transfer-weak-support",
            "partial": "scaled-source-alpha-transfer-partial-support",
            "fail": "scaled-source-alpha-transfer-failed",
        }[classification]
        aggregate.append(
            {
                "dataset_key": dataset_key,
                "dataset": spec["label"],
                "paper_role": spec["paper_role"],
                "claim_update": claim_update,
                "campaign_classification": classification,
                "n_seeds": len(rows),
                "n_users_per_seed": int(rows[0]["n_users"]),
                "source_alpha": float(rows[0]["source_alpha"]),
                "mean_grid_channel_nmse_db": grid_mean,
                "std_grid_channel_nmse_db": grid_std,
                "ci95_grid_channel_nmse_db_low": grid_ci_low,
                "ci95_grid_channel_nmse_db_high": grid_ci_high,
                "mean_source_alpha_channel_nmse_db": source_mean,
                "std_source_alpha_channel_nmse_db": source_std,
                "ci95_source_alpha_channel_nmse_db_low": source_ci_low,
                "ci95_source_alpha_channel_nmse_db_high": source_ci_high,
                "mean_source_alpha_gain_vs_grid_db": gain_mean,
                "std_source_alpha_gain_vs_grid_db": gain_std,
                "ci95_source_alpha_gain_vs_grid_db_low": gain_ci_low,
                "ci95_source_alpha_gain_vs_grid_db_high": gain_ci_high,
                "min_seed_mean_source_alpha_gain_vs_grid_db": min(
                    row["mean_source_alpha_gain_vs_grid_db"] for row in rows
                ),
                "min_cell_source_alpha_gain_vs_grid_db": min(
                    row["min_source_alpha_gain_vs_grid_db"] for row in rows
                ),
                "mean_source_alpha_gap_vs_oracle_db": gap_mean,
                "std_source_alpha_gap_vs_oracle_db": gap_std,
                "ci95_source_alpha_gap_vs_oracle_db_low": gap_ci_low,
                "ci95_source_alpha_gap_vs_oracle_db_high": gap_ci_high,
                "min_mean_support_recall": min(
                    row["min_mean_support_recall"] for row in rows
                ),
                "mean_dominant_energy_recall": float(
                    np.mean([row["mean_dominant_energy_recall_all"] for row in rows])
                ),
                "total_elapsed_seconds": float(
                    np.sum([row["elapsed_seconds"] for row in rows])
                ),
            }
        )
    return aggregate


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_evaluation_summary(
    output_dir: Path,
    *,
    aggregate: list[dict[str, Any]],
) -> Path:
    o1 = next(row for row in aggregate if row["dataset_key"] == "o1_60")
    i3 = next(row for row in aggregate if row["dataset_key"] == "i3_60")
    lines = [
        "# DeepMIMO Source-Alpha Seed Campaign Evaluation Summary",
        "",
        (
            "- `outcome_summary`: Five-seed, 100-user robustness evaluation completed "
            f"with O1_60 classified `{o1['campaign_classification']}` and I3_60 "
            f"classified `{i3['campaign_classification']}`."
        ),
        (
            "- `claim_update`: O1_60 and I3_60 scalar source-alpha transfer claims "
            "are updated from single-seed development evidence to scaled multi-seed "
            "proxy evidence at their measured classifications."
        ),
        (
            "- `baseline_relation`: Every seed uses the same grid FFT top-k baseline, "
            "Stage-2 source alpha, SNR/L grid, and channel construction as the parent dev runs."
        ),
        (
            "- `failure_mode`: This remains a scalar-alpha transfer proxy with dominant-bin "
            "delay/TX metrics; it is not a full trained G2/T-OMP-Net cross-domain result."
        ),
        (
            "- `next_action`: Attach the full trained estimator path and physical angle/delay "
            "metrics before promoting E2/E3 to final Sensors external-validation evidence."
        ),
        "- `evidence_level`: E2/E3 supporting multi-seed robustness evidence.",
    ]
    path = output_dir / "evaluation_summary.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_summary(output_dir: Path, aggregate: list[dict[str, Any]]) -> Path:
    lines = [
        "# DeepMIMO Source-Alpha Multi-Seed Campaign",
        "",
        "The campaign varies only user sampling and AWGN seed. Dataset construction, SNR/L cells, grid baseline, Stage-2 source alpha, refinement search, and metric definitions remain fixed.",
        "",
        "| Dataset | Class | Seeds x users | Grid NMSE (dB) | Source-alpha NMSE (dB) | Gain vs grid, mean [95% CI] (dB) | Min cell gain (dB) | Min support recall | Oracle gap (dB) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in aggregate:
        lines.append(
            f"| {row['dataset']} | {row['campaign_classification']} | "
            f"{row['n_seeds']} x {row['n_users_per_seed']} | "
            f"{row['mean_grid_channel_nmse_db']:.4f} | "
            f"{row['mean_source_alpha_channel_nmse_db']:.4f} | "
            f"{row['mean_source_alpha_gain_vs_grid_db']:.4f} "
            f"[{row['ci95_source_alpha_gain_vs_grid_db_low']:.4f}, "
            f"{row['ci95_source_alpha_gain_vs_grid_db_high']:.4f}] | "
            f"{row['min_cell_source_alpha_gain_vs_grid_db']:.4f} | "
            f"{row['min_mean_support_recall']:.4f} | "
            f"{row['mean_source_alpha_gap_vs_oracle_db']:.4f} |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "These results strengthen the reproducibility and sampling-robustness of the scalar source-alpha transfer proxy. They do not establish full trained G2/T-OMP-Net performance or physical angle/delay RMSE on DeepMIMO.",
        ]
    )
    path = output_dir / "summary.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    args = parse_args()
    seed_rows = load_seed_rows(seeds=args.seeds, n_users=args.n_users)
    aggregate = aggregate_rows(seed_rows)
    output_dir = ROOT / "05_results" / args.output_dir_name
    output_dir.mkdir(parents=True, exist_ok=True)
    seed_csv = output_dir / "seed_metrics.csv"
    aggregate_csv = output_dir / "dataset_aggregate.csv"
    write_csv(seed_csv, seed_rows)
    write_csv(aggregate_csv, aggregate)
    evaluation_path = write_evaluation_summary(output_dir, aggregate=aggregate)
    summary_path = write_summary(output_dir, aggregate)

    metrics = {
        "claim_update": "scaled-deepmimo-source-alpha-campaign-recorded",
        "n_datasets": len(aggregate),
        "n_seeds": len(args.seeds),
        "n_users_per_seed": args.n_users,
        "n_seed_runs": len(seed_rows),
    }
    for row in aggregate:
        prefix = row["dataset_key"]
        for key in (
            "campaign_classification",
            "mean_grid_channel_nmse_db",
            "mean_source_alpha_channel_nmse_db",
            "mean_source_alpha_gain_vs_grid_db",
            "ci95_source_alpha_gain_vs_grid_db_low",
            "ci95_source_alpha_gain_vs_grid_db_high",
            "min_seed_mean_source_alpha_gain_vs_grid_db",
            "min_cell_source_alpha_gain_vs_grid_db",
            "min_mean_support_recall",
            "mean_source_alpha_gap_vs_oracle_db",
        ):
            metrics[f"{prefix}_{key}"] = row[key]

    command = subprocess.list2cmdline(
        [
            sys.executable,
            str(Path(__file__).resolve().relative_to(ROOT)),
            *sys.argv[1:],
        ]
    )
    source_manifests = [row["manifest_path"] for row in seed_rows]
    manifest_path = write_run_manifest(
        output_dir,
        run_id=f"deepmimo_source_alpha_seed_campaign_{len(args.seeds)}x{args.n_users}",
        command=command,
        config={
            "seeds": args.seeds,
            "n_users_per_seed": args.n_users,
            "source_manifests": source_manifests,
            "confidence_interval": "two-sided Student-t 95% CI over seed means",
            "fixed_contract": (
                "SNR/L cells, channel construction, grid baseline, Stage-2 source alpha, "
                "refinement search, and metrics"
            ),
        },
        metrics=metrics,
        notes=[
            "Writing-facing E2/E3 robustness campaign for claim C4.",
            "Only the random user sample and AWGN realization vary across seeds.",
            "Negative and partial classifications are retained in seed_metrics.csv.",
            "Scalar source-alpha proxy only; not final trained G2/T-OMP-Net evidence.",
        ],
        cwd=ROOT,
    )
    print(f"Wrote {seed_csv.relative_to(ROOT)}")
    print(f"Wrote {aggregate_csv.relative_to(ROOT)}")
    print(f"Wrote {summary_path.relative_to(ROOT)}")
    print(f"Wrote {evaluation_path.relative_to(ROOT)}")
    print(f"Wrote {manifest_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
