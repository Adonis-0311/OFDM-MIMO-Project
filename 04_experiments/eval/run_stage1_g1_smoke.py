from __future__ import annotations

import csv
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_active_modules"))

from baseline.crlb_5l import coefficient_crlb_proxy
from baseline.tensor_omp import evaluate_tensor_omp, run_tensor_omp
from common.config import ExperimentConfig, GridConfig
from common.manifest import write_run_manifest, write_summary_md
from common.seed import seed_all
from data.set_a_generator import build_dictionary, generate_set_a_sample


def finite_mean(values: list[float]) -> float:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    return float(np.mean(arr)) if arr.size else float("nan")


def main() -> None:
    config = ExperimentConfig(
        seed=20260624,
        snr_db=20.0,
        n_targets=3,
        n_trials=40,
        grid=GridConfig(angle_bins=16, delay_bins=8, doppler_bins=8),
    )
    rng = seed_all(config.seed)
    dictionary = build_dictionary(config.grid)
    rows: list[dict[str, float]] = []
    for snr_db in (10.0, 20.0, 30.0):
        for n_targets in (1, 3, 5):
            nmse_values: list[float] = []
            recall_values: list[float] = []
            delay_rmse_values: list[float] = []
            crlb_values: list[float] = []
            for _ in range(config.n_trials):
                sample = generate_set_a_sample(
                    rng=rng,
                    grid=config.grid,
                    n_targets=n_targets,
                    snr_db=snr_db,
                    dictionary=dictionary,
                )
                result = run_tensor_omp(sample, max_iters=n_targets)
                metrics = evaluate_tensor_omp(sample, result)
                proxy = coefficient_crlb_proxy(sample)
                nmse_values.append(metrics.nmse_db)
                recall_values.append(metrics.support_recall)
                delay_rmse_values.append(metrics.delay_rmse_bins)
                crlb_values.append(proxy.coefficient_nmse_floor_db)
            rows.append(
                {
                    "snr_db": snr_db,
                    "n_targets": n_targets,
                    "mean_nmse_db": finite_mean(nmse_values),
                    "mean_support_recall": finite_mean(recall_values),
                    "mean_delay_rmse_bins": finite_mean(delay_rmse_values),
                    "mean_crlb_proxy_db": finite_mean(crlb_values),
                }
            )

    output_dir = ROOT / "05_results" / "stage1_g1_smoke"
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "stage1_g1_smoke.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    high_snr_rows = [row for row in rows if row["snr_db"] == 30.0]
    metrics = {
        "mean_nmse_db_all": finite_mean([float(row["mean_nmse_db"]) for row in rows]),
        "mean_support_recall_all": finite_mean([float(row["mean_support_recall"]) for row in rows]),
        "mean_nmse_db_snr30": finite_mean([float(row["mean_nmse_db"]) for row in high_snr_rows]),
        "mean_support_recall_snr30": finite_mean(
            [float(row["mean_support_recall"]) for row in high_snr_rows]
        ),
        "mean_nmse_minus_crlb_proxy_db_snr30": finite_mean(
            [
                float(row["mean_nmse_db"]) - float(row["mean_crlb_proxy_db"])
                for row in high_snr_rows
            ]
        ),
        "max_delay_rmse_bins_snr30": float(
            max(float(row["mean_delay_rmse_bins"]) for row in high_snr_rows)
        ),
    }
    notes = [
        "Stage-1 smoke uses an orthonormal tensor DFT dictionary to verify the Set A -> Tensor-OMP -> metric path.",
        "The CRLB value is a coefficient-recovery proxy, not the final 5L joint ISAC CRLB required by the paper.",
        "This run supports G1 wiring and comparability checks; full paper-scale G1 remains pending.",
    ]
    manifest_path = write_run_manifest(
        output_dir,
        run_id="stage1_g1_smoke_20260624",
        command="python 04_experiments/eval/run_stage1_g1_smoke.py",
        config=config,
        metrics=metrics,
        notes=notes,
        cwd=ROOT,
    )
    write_summary_md(
        output_dir,
        title="Stage 1 G1 Smoke",
        config_hash=config.stable_hash(),
        metrics=metrics,
        notes=notes,
        artifacts=[str(csv_path.relative_to(ROOT)), str(manifest_path.relative_to(ROOT))],
    )


if __name__ == "__main__":
    main()
