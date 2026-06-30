from __future__ import annotations

import csv
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_active_modules"))

from common.manifest import write_run_manifest, write_summary_md
from common.seed import seed_all
from data.offgrid_tensor import generate_offgrid_tensor_sample
from tompnet.hungarian_loss import permutation_invariant_mse
from tompnet.layer import TOMPNetSmokeConfig, run_minimal_tompnet_smoke


def finite_mean(values: list[float]) -> float:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    return float(np.mean(arr)) if arr.size else float("nan")


def main() -> None:
    shape = (128, 16, 32)
    snr_db = 20.0
    seed = 20260624
    n_trials = 6
    offset_radius = 0.35
    rng = seed_all(seed)
    rows: list[dict[str, float]] = []
    controlled_target = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], dtype=float)
    controlled_loss_delta = abs(
        permutation_invariant_mse(controlled_target, controlled_target)
        - permutation_invariant_mse(controlled_target[::-1], controlled_target)
    )
    for n_targets in (2, 4, 8):
        grid_values: list[float] = []
        tomp_values: list[float] = []
        gain_values: list[float] = []
        loss_values: list[float] = []
        for _ in range(n_trials):
            sample = generate_offgrid_tensor_sample(
                rng=rng,
                shape=shape,
                n_targets=n_targets,
                snr_db=snr_db,
                offset_radius=offset_radius,
            )
            grid = run_minimal_tompnet_smoke(
                sample, TOMPNetSmokeConfig(n_targets=n_targets, enable_offgrid=False)
            )
            tomp = run_minimal_tompnet_smoke(
                sample, TOMPNetSmokeConfig(n_targets=n_targets, enable_offgrid=True)
            )
            truth = np.array(
                [
                    [
                        target.angle_bin + target.angle_offset,
                        target.delay_bin + target.delay_offset,
                        target.doppler_bin + target.doppler_offset,
                    ]
                    for target in sample.targets
                ],
                dtype=float,
            )
            pred = np.array(tomp.bins, dtype=float)
            grid_values.append(grid.measurement_nmse_db)
            tomp_values.append(tomp.measurement_nmse_db)
            gain_values.append(grid.measurement_nmse_db - tomp.measurement_nmse_db)
            loss_values.append(permutation_invariant_mse(pred, truth))
        rows.append(
            {
                "n_targets": float(n_targets),
                "snr_db": snr_db,
                "mean_tensor_omp_nmse_db": finite_mean(grid_values),
                "mean_minimal_tompnet_nmse_db": finite_mean(tomp_values),
                "mean_gain_db": finite_mean(gain_values),
                "mean_permutation_loss": finite_mean(loss_values),
            }
        )

    output_dir = ROOT / "05_results" / "stage2_minimal_tompnet_smoke"
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "stage2_minimal_tompnet_smoke.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    metrics = {
        "tensor_shape": "128x16x32",
        "snr_db": snr_db,
        "n_trials_per_l": n_trials,
        "mean_gain_db": finite_mean([float(row["mean_gain_db"]) for row in rows]),
        "min_gain_db": float(min(float(row["mean_gain_db"]) for row in rows)),
        "mean_permutation_loss": finite_mean([float(row["mean_permutation_loss"]) for row in rows]),
        "controlled_permutation_loss_delta": controlled_loss_delta,
    }
    notes = [
        "This is a minimal deterministic T-OMP-Net smoke/proxy, not a trained neural network.",
        "It validates Pack 3 wiring: unfolded top-k layer shape, bounded off-grid refinement, LS amplitude update, and permutation-invariant loss.",
        "The mean permutation loss is a coordinate-error diagnostic; controlled_permutation_loss_delta verifies order invariance separately.",
        "G2 remains unproven until a trained T-OMP-Net achieves the required comparison under the locked metric contract.",
    ]
    manifest_path = write_run_manifest(
        output_dir,
        run_id="stage2_minimal_tompnet_smoke_20260624",
        command="python 04_experiments/eval/run_stage2_minimal_tompnet_smoke.py",
        config={
            "shape": shape,
            "snr_db": snr_db,
            "seed": seed,
            "n_trials": n_trials,
            "offset_radius": offset_radius,
            "l_values": [2, 4, 8],
        },
        metrics=metrics,
        notes=notes,
        cwd=ROOT,
    )
    write_summary_md(
        output_dir,
        title="Stage 2 Minimal T-OMP-Net Smoke",
        config_hash="stage2-minimal-tompnet-20260624",
        metrics=metrics,
        notes=notes,
        artifacts=[str(csv_path.relative_to(ROOT)), str(manifest_path.relative_to(ROOT))],
    )


if __name__ == "__main__":
    main()
