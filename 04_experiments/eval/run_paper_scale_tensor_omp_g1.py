from __future__ import annotations

import csv
from pathlib import Path
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_active_modules"))

from baseline.tensor_fft_omp import generate_sparse_fft_sample, recover_topk_fft
from common.manifest import write_run_manifest, write_summary_md
from common.seed import seed_all


def finite_mean(values: list[float]) -> float:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    return float(np.mean(arr)) if arr.size else float("nan")


def main() -> None:
    shape = (128, 16, 32)
    snr_db = 20.0
    n_trials = 12
    seed = 20260624
    rng = seed_all(seed)
    rows: list[dict[str, float]] = []
    started = time.perf_counter()
    for n_targets in (2, 4, 8, 16, 32, 64):
        nmse_values: list[float] = []
        recall_values: list[float] = []
        crlb_values: list[float] = []
        elapsed_values: list[float] = []
        for _ in range(n_trials):
            sample = generate_sparse_fft_sample(
                rng=rng,
                shape=shape,
                n_targets=n_targets,
                snr_db=snr_db,
            )
            tick = time.perf_counter()
            result = recover_topk_fft(sample, n_targets)
            elapsed_values.append(time.perf_counter() - tick)
            nmse_values.append(result.nmse_db)
            recall_values.append(result.support_recall)
            crlb_values.append(result.crlb_proxy_db)
        rows.append(
            {
                "n_targets": float(n_targets),
                "snr_db": snr_db,
                "mean_nmse_db": finite_mean(nmse_values),
                "mean_support_recall": finite_mean(recall_values),
                "mean_crlb_proxy_db": finite_mean(crlb_values),
                "mean_nmse_minus_crlb_proxy_db": finite_mean(
                    [nmse - crlb for nmse, crlb in zip(nmse_values, crlb_values)]
                ),
                "mean_recovery_seconds": finite_mean(elapsed_values),
            }
        )

    output_dir = ROOT / "05_results" / "paper_scale_tensor_omp_g1"
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "paper_scale_tensor_omp_g1.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    metrics = {
        "tensor_shape": "128x16x32",
        "snr_db": snr_db,
        "n_trials_per_l": n_trials,
        "mean_nmse_db_all": finite_mean([float(row["mean_nmse_db"]) for row in rows]),
        "min_support_recall": float(min(float(row["mean_support_recall"]) for row in rows)),
        "mean_abs_nmse_crlb_gap_db": finite_mean(
            [abs(float(row["mean_nmse_minus_crlb_proxy_db"])) for row in rows]
        ),
        "wall_seconds": time.perf_counter() - started,
    }
    notes = [
        "Paper-scale scan follows the v2.3R Stage-1 target shape 128x16x32 and L in {2,4,8,16,32,64}.",
        "The unitary FFT tensor contract is equivalent to a normalized on-grid DFT dictionary and avoids materializing a 65536x65536 matrix.",
        "This remains an on-grid baseline scan; off-grid and final 5L CRLB validation are still pending.",
    ]
    manifest_path = write_run_manifest(
        output_dir,
        run_id="paper_scale_tensor_omp_g1_20260624",
        command="python 04_experiments/eval/run_paper_scale_tensor_omp_g1.py",
        config={"shape": shape, "snr_db": snr_db, "n_trials": n_trials, "seed": seed},
        metrics=metrics,
        notes=notes,
        cwd=ROOT,
    )
    write_summary_md(
        output_dir,
        title="Paper-Scale Tensor-OMP G1 Scan",
        config_hash="fft-unitary-20260624",
        metrics=metrics,
        notes=notes,
        artifacts=[str(csv_path.relative_to(ROOT)), str(manifest_path.relative_to(ROOT))],
    )


if __name__ == "__main__":
    main()

