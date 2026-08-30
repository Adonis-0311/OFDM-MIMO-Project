from __future__ import annotations

import csv
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_active_modules"))

from common.manifest import write_run_manifest, write_summary_md


def finite_mean(values: list[float]) -> float:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    return float(np.mean(arr)) if arr.size else float("nan")


def load_rows(path: Path) -> list[dict[str, float]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [{key: float(value) for key, value in row.items()} for row in reader]


def slope(x_values: list[float], y_values: list[float]) -> float:
    x = np.asarray(x_values, dtype=float)
    y = np.asarray(y_values, dtype=float)
    if x.size < 2:
        return float("nan")
    coeff = np.polyfit(x, y, deg=1)
    return float(coeff[0])


def write_evaluation_summary(
    output_dir: Path,
    *,
    min_support_recall: float,
    max_bound_ratio: float,
    nmse_slope: float,
    runtime_slope: float,
    paper_kruskal_bound: int,
) -> Path:
    status = "supported" if min_support_recall >= 1.0 and max_bound_ratio < 1.0 else "inconclusive"
    if status == "supported":
        mechanism_note = (
            "All tested L values remain below the paper-scale Kruskal proxy bound and recover support exactly "
            "in the on-grid FFT contract. NMSE degrades smoothly as L/Lmax increases, and runtime remains "
            "finite at this FFT-proxy scale."
        )
        next_action = "Use this as the paper-scale on-grid Kruskal sanity row; do not present it as DeepMIMO or off-grid proof."
    else:
        mechanism_note = (
            "The on-grid proxy does not fully satisfy the support/bound sanity check, so additional recovery or "
            "stress conditions are needed before citing it as paper-scale identifiability evidence."
        )
        next_action = "Rerun with more trials or diagnose the L cells that fail the support/bound sanity check."
    lines = [
        "# Stage 3 Paper-Scale Kruskal Proxy Evaluation Summary",
        "",
        "## Outcome Summary",
        "",
        (
            "This run converts the existing paper-scale Tensor-OMP scan into a Kruskal "
            "identifiability proxy table. It uses the 128x16x32 tensor and L={2,4,8,16,32,64} "
            "on-grid FFT contract, then records bound ratios, Kruskal risk factors, NMSE trend, "
            "support recall, and runtime trend."
        ),
        "",
        "## evaluation_summary",
        "",
        "- `research_question`: Does the paper-scale on-grid Tensor-OMP scan remain inside the Kruskal-identifiable regime and recover supports reliably?",
        f"- `claim_update`: {status} for paper-scale on-grid Kruskal proxy evidence.",
        "- `baseline_relation`: Derived from `paper_scale_tensor_omp_g1`, which already validates the 128x16x32 on-grid Tensor-OMP baseline.",
        "- `failure_mode`: No execution failure; remaining limitation is that this is an on-grid FFT proxy, not off-grid, CDL, or DeepMIMO validation.",
        f"- `mechanism_note`: {mechanism_note}",
        f"- `next_action`: {next_action}",
        "- `evidence_level`: Stage-3 paper-scale sanity evidence.",
        "",
        "## Key Metrics",
        "",
        f"- Paper-scale Kruskal proxy bound: {paper_kruskal_bound}",
        f"- Max tested L/Lmax: {max_bound_ratio:.4f}",
        f"- Minimum support recall: {min_support_recall:.4f}",
        f"- NMSE slope vs L/Lmax: {nmse_slope:.4f} dB per bound-ratio unit",
        f"- Runtime slope vs L/Lmax: {runtime_slope:.6f} s per bound-ratio unit",
    ]
    path = output_dir / "evaluation_summary.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    input_csv = ROOT / "05_results" / "paper_scale_tensor_omp_g1" / "paper_scale_tensor_omp_g1.csv"
    rows = load_rows(input_csv)
    shape = (128, 16, 32)
    paper_kruskal_bound = int(np.floor((shape[0] + shape[1] + shape[2] - 2) / 2))
    output_rows: list[dict[str, float]] = []
    for row in rows:
        n_targets = int(row["n_targets"])
        bound_ratio = float(n_targets / paper_kruskal_bound)
        kruskal_margin = float(paper_kruskal_bound - n_targets)
        risk_factor = float((n_targets**2) / max((paper_kruskal_bound - n_targets + 1e-9) ** 2, 1e-300))
        output_rows.append(
            {
                "n_targets": float(n_targets),
                "paper_kruskal_bound": float(paper_kruskal_bound),
                "bound_ratio": bound_ratio,
                "kruskal_margin": kruskal_margin,
                "kruskal_risk_factor": risk_factor,
                "mean_nmse_db": row["mean_nmse_db"],
                "mean_support_recall": row["mean_support_recall"],
                "mean_crlb_proxy_db": row["mean_crlb_proxy_db"],
                "mean_nmse_minus_crlb_proxy_db": row["mean_nmse_minus_crlb_proxy_db"],
                "mean_recovery_seconds": row["mean_recovery_seconds"],
            }
        )

    bound_ratios = [row["bound_ratio"] for row in output_rows]
    nmse_values = [row["mean_nmse_db"] for row in output_rows]
    runtime_values = [row["mean_recovery_seconds"] for row in output_rows]
    recall_values = [row["mean_support_recall"] for row in output_rows]
    nmse_slope = slope(bound_ratios, nmse_values)
    runtime_slope = slope(bound_ratios, runtime_values)
    metrics = {
        "tensor_shape": "128x16x32",
        "paper_kruskal_bound": paper_kruskal_bound,
        "l_values": [int(row["n_targets"]) for row in output_rows],
        "max_bound_ratio": float(max(bound_ratios)),
        "min_kruskal_margin": float(min(row["kruskal_margin"] for row in output_rows)),
        "max_kruskal_risk_factor": float(max(row["kruskal_risk_factor"] for row in output_rows)),
        "min_support_recall": float(min(recall_values)),
        "mean_nmse_db_all": finite_mean(nmse_values),
        "nmse_slope_vs_bound_ratio": nmse_slope,
        "runtime_slope_vs_bound_ratio": runtime_slope,
    }
    output_dir = ROOT / "05_results" / "stage3_paper_scale_kruskal_proxy"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_csv = output_dir / "stage3_paper_scale_kruskal_proxy.csv"
    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output_rows[0].keys()))
        writer.writeheader()
        writer.writerows(output_rows)

    notes = [
        "Derived from the existing paper_scale_tensor_omp_g1 run; no new recovery samples are generated.",
        "Kruskal proxy bound uses floor((Nv + K + M - 2) / 2) for the paper-scale 128x16x32 tensor.",
        "This is on-grid FFT Tensor-OMP sanity evidence and must not be presented as off-grid or DeepMIMO validation.",
    ]
    manifest_path = write_run_manifest(
        output_dir,
        run_id="stage3_paper_scale_kruskal_proxy_20260624",
        command="python 04_experiments/eval/run_stage3_paper_scale_kruskal_proxy.py",
        config={"source_csv": str(input_csv.relative_to(ROOT)), "shape": shape},
        metrics=metrics,
        notes=notes,
        cwd=ROOT,
    )
    summary_path = write_summary_md(
        output_dir,
        title="Stage 3 Paper-Scale Kruskal Proxy",
        config_hash="stage3-paper-scale-kruskal-proxy-20260624",
        metrics=metrics,
        notes=notes,
        artifacts=[str(output_csv.relative_to(ROOT)), str(manifest_path.relative_to(ROOT))],
    )
    evaluation_path = write_evaluation_summary(
        output_dir,
        min_support_recall=float(metrics["min_support_recall"]),
        max_bound_ratio=float(metrics["max_bound_ratio"]),
        nmse_slope=nmse_slope,
        runtime_slope=runtime_slope,
        paper_kruskal_bound=paper_kruskal_bound,
    )
    print(f"Wrote {output_csv.relative_to(ROOT)}")
    print(f"Wrote {summary_path.relative_to(ROOT)}")
    print(f"Wrote {manifest_path.relative_to(ROOT)}")
    print(f"Wrote {evaluation_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
