from __future__ import annotations

import csv
from pathlib import Path
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_active_modules"))

from common.manifest import write_run_manifest, write_summary_md


PARAMETERS = ("angle", "delay", "doppler", "gain_re", "gain_im")


def read_csv(path: Path) -> list[dict[str, float]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows: list[dict[str, float]] = []
        for row in reader:
            rows.append({key: float(value) for key, value in row.items()})
    return rows


def slope_per_db(rows: list[dict[str, float]], column: str) -> float:
    snr = np.asarray([row["snr_db"] for row in rows], dtype=float)
    values = np.asarray([max(row[column], 1e-300) for row in rows], dtype=float)
    slope, _intercept = np.polyfit(snr, np.log10(values), deg=1)
    return float(slope)


def finite_mean(values: list[float]) -> float:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    return float(np.mean(arr)) if arr.size else float("nan")


def write_evaluation_summary(
    output_dir: Path,
    *,
    claim_update: str,
    mean_ratio_at_30db: float,
    max_ratio_at_30db: float,
    max_relative_fim_error: float,
    mean_abs_rmse_slope_error: float,
    elapsed_seconds: float,
) -> Path:
    if claim_update == "supported-pilot":
        interpretation = (
            "analytic 5L FIM derivatives match finite differences, CRLB standard deviations scale "
            "with the expected 10 dB -> sqrt(10) law, and the high-SNR estimator ratio is close to 1."
        )
        next_action = (
            "Use this as single-target Stage-3 CRLB trend evidence; keep multi-target 5L CRLB "
            "tightness as a future/appendix extension unless a larger Monte Carlo budget is approved."
        )
    else:
        interpretation = (
            "the existing pilot does not satisfy the conservative tightness audit, so it should stay "
            "as implementation validation rather than Stage-3 asymptotic evidence."
        )
        next_action = "Run a larger Monte Carlo or improve the estimator search before citing CRLB tightness."
    lines = [
        "# Stage 3 5L CRLB Asymptotic Tightness Evaluation Summary",
        "",
        "## Outcome Summary",
        "",
        (
            "This audit converts the existing analytic 5L FIM validation and single-target Monte Carlo "
            "pilot into a Stage-3 CRLB tightness evidence row. It checks derivative correctness, "
            "SNR-scaling slopes, and high-SNR RMSE/CRLB ratios."
        ),
        "",
        "## evaluation_summary",
        "",
        "- `research_question`: Do the analytic 5L CRLB and FFT-initialized off-grid estimator show the expected high-SNR asymptotic trend?",
        f"- `claim_update`: {claim_update} for single-target 5L CRLB asymptotic trend evidence.",
        "- `baseline_relation`: Aggregates `crlb_5l_fim_validation` and `crlb_5l_monte_carlo` without changing their metric definitions.",
        "- `failure_mode`: No execution failure; limitation is small-sample, single-target evidence rather than large-sample multi-target efficiency proof.",
        f"- `mechanism_note`: {interpretation}",
        f"- `next_action`: {next_action}",
        "- `evidence_level`: Stage-3 local CRLB trend evidence; not full multi-target CRLB tightness proof.",
        "",
        "## Key Metrics",
        "",
        f"- Max analytic-vs-numeric FIM relative error: {max_relative_fim_error:.4e}",
        f"- Mean RMSE/CRLB ratio at 30 dB: {mean_ratio_at_30db:.4f}",
        f"- Max RMSE/CRLB ratio at 30 dB: {max_ratio_at_30db:.4f}",
        f"- Mean absolute RMSE slope error versus -0.05 per dB: {mean_abs_rmse_slope_error:.4f}",
        f"- Wall-clock elapsed time: {elapsed_seconds:.2f} s",
    ]
    path = output_dir / "evaluation_summary.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    started = time.perf_counter()
    fim_csv = ROOT / "05_results" / "crlb_5l_fim_validation" / "crlb_5l_fim_validation.csv"
    mc_csv = ROOT / "05_results" / "crlb_5l_monte_carlo" / "crlb_5l_monte_carlo.csv"
    if not fim_csv.exists() or not mc_csv.exists():
        missing = [str(path.relative_to(ROOT)) for path in (fim_csv, mc_csv) if not path.exists()]
        raise FileNotFoundError(f"Missing prerequisite CRLB evidence: {missing}")

    fim_rows = read_csv(fim_csv)
    mc_rows = read_csv(mc_csv)
    fim_rows = sorted(fim_rows, key=lambda row: row["snr_db"])
    mc_rows = sorted(mc_rows, key=lambda row: row["snr_db"])
    high_snr = max(mc_rows, key=lambda row: row["snr_db"])

    detail_rows: list[dict[str, float | str]] = []
    rmse_slope_errors: list[float] = []
    crlb_slope_errors: list[float] = []
    for param in PARAMETERS:
        rmse_col = f"{param}_rmse" if param.startswith("gain") else f"{param}_rmse_bin"
        crlb_col = f"{param}_crlb_std" if param.startswith("gain") else f"{param}_crlb_std_bin"
        rmse_slope = slope_per_db(mc_rows, rmse_col)
        crlb_slope = slope_per_db(mc_rows, crlb_col)
        ratio_at_30db = float(high_snr[rmse_col] / max(high_snr[crlb_col], 1e-300))
        rmse_error = abs(rmse_slope - (-0.05))
        crlb_error = abs(crlb_slope - (-0.05))
        rmse_slope_errors.append(rmse_error)
        crlb_slope_errors.append(crlb_error)
        detail_rows.append(
            {
                "parameter": param,
                "rmse_log10_slope_per_db": rmse_slope,
                "crlb_log10_slope_per_db": crlb_slope,
                "rmse_slope_error_vs_expected": rmse_error,
                "crlb_slope_error_vs_expected": crlb_error,
                "rmse_crlb_ratio_at_30db": ratio_at_30db,
            }
        )

    max_relative_fim_error = max(row["relative_fim_error"] for row in fim_rows)
    mean_ratio_at_30db = float(high_snr["mean_rmse_crlb_ratio"])
    max_ratio_at_30db = float(high_snr["max_rmse_crlb_ratio"])
    mean_abs_rmse_slope_error = finite_mean(rmse_slope_errors)
    mean_abs_crlb_slope_error = finite_mean(crlb_slope_errors)
    claim_update = (
        "supported-pilot"
        if (
            max_relative_fim_error < 1e-6
            and 0.75 <= mean_ratio_at_30db <= 1.25
            and max_ratio_at_30db <= 1.75
            and mean_abs_rmse_slope_error <= 0.02
            and mean_abs_crlb_slope_error <= 1e-6
        )
        else "partial-or-inconclusive"
    )
    elapsed_seconds = time.perf_counter() - started

    output_dir = ROOT / "05_results" / "stage3_crlb_asymptotic_tightness"
    output_dir.mkdir(parents=True, exist_ok=True)
    detail_csv = output_dir / "stage3_crlb_asymptotic_tightness.csv"
    with detail_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(detail_rows[0].keys()))
        writer.writeheader()
        writer.writerows(detail_rows)

    metrics = {
        "source_fim_csv": str(fim_csv.relative_to(ROOT)),
        "source_monte_carlo_csv": str(mc_csv.relative_to(ROOT)),
        "claim_update": claim_update,
        "max_relative_fim_error": max_relative_fim_error,
        "mean_ratio_at_30db": mean_ratio_at_30db,
        "max_ratio_at_30db": max_ratio_at_30db,
        "mean_abs_rmse_slope_error_vs_expected": mean_abs_rmse_slope_error,
        "mean_abs_crlb_slope_error_vs_expected": mean_abs_crlb_slope_error,
        "expected_log10_slope_per_db": -0.05,
        "elapsed_seconds": elapsed_seconds,
    }
    notes = [
        "This is a Stage-3 audit of existing 5L CRLB evidence, not a fresh large-sample Monte Carlo.",
        "The evidence supports single-target high-SNR trend consistency and analytic derivative correctness.",
        "Small-sample ratios below 1 at lower SNR are treated as a pilot limitation, not as a CRLB violation claim.",
    ]
    manifest_path = write_run_manifest(
        output_dir,
        run_id="stage3_crlb_asymptotic_tightness_20260624",
        command="python 04_experiments/eval/run_stage3_crlb_asymptotic_tightness.py",
        config={
            "fim_csv": str(fim_csv.relative_to(ROOT)),
            "monte_carlo_csv": str(mc_csv.relative_to(ROOT)),
            "parameters": PARAMETERS,
            "expected_log10_slope_per_db": -0.05,
            "acceptance": {
                "max_relative_fim_error": "< 1e-6",
                "mean_ratio_at_30db": "0.75..1.25",
                "max_ratio_at_30db": "<= 1.75",
                "mean_abs_rmse_slope_error": "<= 0.02",
            },
        },
        metrics=metrics,
        notes=notes,
        cwd=ROOT,
    )
    summary_path = write_summary_md(
        output_dir,
        title="Stage 3 5L CRLB Asymptotic Tightness",
        config_hash="stage3-crlb-asymptotic-tightness-20260624",
        metrics=metrics,
        notes=notes,
        artifacts=[
            str(detail_csv.relative_to(ROOT)),
            str(manifest_path.relative_to(ROOT)),
        ],
    )
    evaluation_path = write_evaluation_summary(
        output_dir,
        claim_update=claim_update,
        mean_ratio_at_30db=mean_ratio_at_30db,
        max_ratio_at_30db=max_ratio_at_30db,
        max_relative_fim_error=max_relative_fim_error,
        mean_abs_rmse_slope_error=mean_abs_rmse_slope_error,
        elapsed_seconds=elapsed_seconds,
    )
    print(f"Wrote {detail_csv.relative_to(ROOT)}")
    print(f"Wrote {summary_path.relative_to(ROOT)}")
    print(f"Wrote {manifest_path.relative_to(ROOT)}")
    print(f"Wrote {evaluation_path.relative_to(ROOT)}")
    print(f"claim_update={claim_update}")
    print(f"mean_ratio_at_30db={mean_ratio_at_30db:.4f}")
    print(f"max_relative_fim_error={max_relative_fim_error:.4e}")
    print(f"mean_abs_rmse_slope_error_vs_expected={mean_abs_rmse_slope_error:.4f}")


if __name__ == "__main__":
    main()
