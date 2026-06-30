from __future__ import annotations

import csv
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_active_modules"))

from baseline.crlb_5l import five_param_fim_crlb
from common.manifest import write_run_manifest, write_summary_md


def finite_mean(values: list[float]) -> float:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    return float(np.mean(arr)) if arr.size else float("nan")


def main() -> None:
    shape = (128, 16, 32)
    params = np.array([37.25, 5.4, 11.7, 0.9, -0.35], dtype=float)
    signal_energy = params[3] ** 2 + params[4] ** 2
    rows: list[dict[str, float]] = []
    for snr_db in (0.0, 10.0, 20.0, 30.0):
        noise_variance = signal_energy / (10 ** (snr_db / 10))
        result = five_param_fim_crlb(
            shape=shape,
            params=params,
            noise_variance=noise_variance,
            finite_difference_step=1e-5,
        )
        crlb_diag = np.diag(result.crlb)
        rows.append(
            {
                "snr_db": snr_db,
                "relative_fim_error": result.relative_error,
                "angle_std_bin": float(np.sqrt(max(crlb_diag[0], 0.0))),
                "delay_std_bin": float(np.sqrt(max(crlb_diag[1], 0.0))),
                "doppler_std_bin": float(np.sqrt(max(crlb_diag[2], 0.0))),
                "gain_re_std": float(np.sqrt(max(crlb_diag[3], 0.0))),
                "gain_im_std": float(np.sqrt(max(crlb_diag[4], 0.0))),
            }
        )

    output_dir = ROOT / "05_results" / "crlb_5l_fim_validation"
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "crlb_5l_fim_validation.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    angle_drop = float(rows[0]["angle_std_bin"] / rows[-1]["angle_std_bin"])
    metrics = {
        "tensor_shape": "128x16x32",
        "max_relative_fim_error": float(max(row["relative_fim_error"] for row in rows)),
        "angle_std_drop_0db_to_30db": angle_drop,
        "mean_relative_fim_error": finite_mean([float(row["relative_fim_error"]) for row in rows]),
        "snr_points": "0,10,20,30",
    }
    notes = [
        "5L parameter vector is [angle_bin, delay_bin, doppler_bin, gain_real, gain_imag].",
        "Complex Gaussian FIM uses 2/sigma^2 Re{dmu_i^H dmu_j}.",
        "This validates analytic derivatives against central finite differences; it is the Stage-1 FIM/CRLB implementation gate, not a Monte Carlo estimator-efficiency claim.",
    ]
    manifest_path = write_run_manifest(
        output_dir,
        run_id="crlb_5l_fim_validation_20260624",
        command="python 04_experiments/eval/run_5l_crlb_fim_validation.py",
        config={"shape": shape, "params": params.tolist(), "snr_db": [0, 10, 20, 30]},
        metrics=metrics,
        notes=notes,
        cwd=ROOT,
    )
    write_summary_md(
        output_dir,
        title="5L CRLB FIM Validation",
        config_hash="5l-fim-20260624",
        metrics=metrics,
        notes=notes,
        artifacts=[str(csv_path.relative_to(ROOT)), str(manifest_path.relative_to(ROOT))],
    )


if __name__ == "__main__":
    main()

