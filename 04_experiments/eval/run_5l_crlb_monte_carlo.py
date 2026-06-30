from __future__ import annotations

import csv
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_active_modules"))

from baseline.crlb_5l import five_param_fim_crlb
from common.manifest import write_run_manifest, write_summary_md
from common.seed import seed_all
from data.offgrid_tensor import (
    OffgridTarget,
    estimate_single_target_multiresolution,
    synthesize_offgrid_clean,
)


def main() -> None:
    shape = (128, 16, 32)
    seed = 20260624
    n_trials = 8
    true_bins = (37.25, 5.4, 11.7)
    true_gain = 0.9 - 0.35j
    target = OffgridTarget(
        angle_bin=int(np.floor(true_bins[0])),
        delay_bin=int(np.floor(true_bins[1])),
        doppler_bin=int(np.floor(true_bins[2])),
        angle_offset=true_bins[0] - np.floor(true_bins[0]),
        delay_offset=true_bins[1] - np.floor(true_bins[1]),
        doppler_offset=true_bins[2] - np.floor(true_bins[2]),
        gain=true_gain,
    )
    clean = synthesize_offgrid_clean(shape, (target,))
    signal_power = float(np.mean(np.abs(clean) ** 2))
    rng = seed_all(seed)
    rows: list[dict[str, float]] = []
    for snr_db in (10.0, 20.0, 30.0):
        noise_variance = signal_power / (10 ** (snr_db / 10))
        errors: list[np.ndarray] = []
        for _ in range(n_trials):
            noise = np.sqrt(noise_variance / 2) * (
                rng.standard_normal(shape) + 1j * rng.standard_normal(shape)
            )
            measurement = clean + noise
            estimate = estimate_single_target_multiresolution(measurement, shape)
            errors.append(
                np.array(
                    [
                        estimate.bins[0] - true_bins[0],
                        estimate.bins[1] - true_bins[1],
                        estimate.bins[2] - true_bins[2],
                        estimate.gain.real - true_gain.real,
                        estimate.gain.imag - true_gain.imag,
                    ],
                    dtype=float,
                )
            )
        error_matrix = np.stack(errors, axis=0)
        rmse = np.sqrt(np.mean(error_matrix**2, axis=0))
        crlb = five_param_fim_crlb(
            shape=shape,
            params=np.array([*true_bins, true_gain.real, true_gain.imag], dtype=float),
            noise_variance=noise_variance,
        )
        crlb_std = np.sqrt(np.maximum(np.diag(crlb.crlb), 0.0))
        ratio = rmse / np.maximum(crlb_std, 1e-300)
        rows.append(
            {
                "snr_db": snr_db,
                "angle_rmse_bin": float(rmse[0]),
                "delay_rmse_bin": float(rmse[1]),
                "doppler_rmse_bin": float(rmse[2]),
                "gain_re_rmse": float(rmse[3]),
                "gain_im_rmse": float(rmse[4]),
                "angle_crlb_std_bin": float(crlb_std[0]),
                "delay_crlb_std_bin": float(crlb_std[1]),
                "doppler_crlb_std_bin": float(crlb_std[2]),
                "gain_re_crlb_std": float(crlb_std[3]),
                "gain_im_crlb_std": float(crlb_std[4]),
                "mean_rmse_crlb_ratio": float(np.mean(ratio)),
                "max_rmse_crlb_ratio": float(np.max(ratio)),
            }
        )

    output_dir = ROOT / "05_results" / "crlb_5l_monte_carlo"
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "crlb_5l_monte_carlo.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    metrics = {
        "tensor_shape": "128x16x32",
        "n_trials_per_snr": n_trials,
        "snr_points": "10,20,30",
        "mean_ratio_at_30db": float(rows[-1]["mean_rmse_crlb_ratio"]),
        "max_ratio_at_30db": float(rows[-1]["max_rmse_crlb_ratio"]),
        "angle_rmse_drop_10db_to_30db": float(
            rows[0]["angle_rmse_bin"] / max(rows[-1]["angle_rmse_bin"], 1e-300)
        ),
    }
    notes = [
        "Monte Carlo uses a single off-grid target and ML-style multiresolution local search initialized by FFT Tensor-OMP.",
        "The run checks estimator RMSE scaling against the analytic 5L CRLB; it is a pilot, not yet a large-sample efficiency proof.",
        "Ratios above 1 are expected because the search grid is finite and n_trials is intentionally small for Stage-1 turnaround.",
    ]
    manifest_path = write_run_manifest(
        output_dir,
        run_id="crlb_5l_monte_carlo_20260624",
        command="python 04_experiments/eval/run_5l_crlb_monte_carlo.py",
        config={
            "shape": shape,
            "seed": seed,
            "n_trials": n_trials,
            "true_bins": true_bins,
            "true_gain": [true_gain.real, true_gain.imag],
        },
        metrics=metrics,
        notes=notes,
        cwd=ROOT,
    )
    write_summary_md(
        output_dir,
        title="5L CRLB Monte Carlo",
        config_hash="5l-mc-20260624",
        metrics=metrics,
        notes=notes,
        artifacts=[str(csv_path.relative_to(ROOT)), str(manifest_path.relative_to(ROOT))],
    )


if __name__ == "__main__":
    main()
