"""Summarize zeta-to-gain/error/clipping associations from frozen audit ledgers."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

import numpy as np
from scipy.stats import spearmanr


ROOT = Path(__file__).resolve().parents[2]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def correlation_rows(
    rows: list[dict[str, str]], *, domain: str, profile: str,
    error_key: str,
) -> list[dict[str, object]]:
    zeta = np.asarray([float(r["candan_minimum_zeta"]) for r in rows])
    targets = {
        "clean_gain_db": np.asarray([float(r["candan_gain_vs_grid_db"]) for r in rows]),
        "coordinate_error_bins": np.asarray([float(r[error_key]) for r in rows]),
        "clipping_rate": np.asarray([float(r["candan_clipping_rate"]) for r in rows]),
    }
    output = []
    for outcome, values in targets.items():
        result = spearmanr(zeta, values)
        output.append({
            "domain": domain, "profile": profile, "outcome": outcome,
            "scene_count": len(rows), "spearman_rho": float(result.statistic),
            "two_sided_p_value": float(result.pvalue),
        })
    return output


def quantile_rows(rows: list[dict[str, str]], *, domain: str, profile: str) -> dict[str, object]:
    zeta = np.asarray([float(r["candan_minimum_zeta"]) for r in rows])
    return {
        "domain": domain, "profile": profile, "scene_count": len(rows),
        **{f"minimum_zeta_q{int(100*q):02d}": float(np.quantile(zeta, q)) for q in (0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99)},
    }


def binned_rows(
    rows: list[dict[str, str]], *, domain: str, profile: str,
    error_key: str, bin_count: int = 10,
) -> list[dict[str, object]]:
    zeta = np.asarray([float(r["candan_minimum_zeta"]) for r in rows])
    edges = np.unique(np.quantile(zeta, np.linspace(0.0, 1.0, bin_count + 1)))
    output = []
    for index, (low, high) in enumerate(zip(edges[:-1], edges[1:])):
        selected = [
            r for r in rows
            if float(r["candan_minimum_zeta"]) >= low
            and (float(r["candan_minimum_zeta"]) <= high if index == len(edges) - 2 else float(r["candan_minimum_zeta"]) < high)
        ]
        output.append({
            "domain": domain, "profile": profile, "zeta_bin": index + 1,
            "zeta_low": float(low), "zeta_high": float(high), "scene_count": len(selected),
            "beneficial_probability": float(np.mean([float(r["candan_gain_vs_grid_db"]) > 0.0 for r in selected])),
            "mean_clean_gain_db": float(np.mean([float(r["candan_gain_vs_grid_db"]) for r in selected])),
            "median_coordinate_error_bins": float(np.median([float(r[error_key]) for r in selected])),
            "mean_clipping_rate": float(np.mean([float(r["candan_clipping_rate"]) for r in selected])),
        })
    return output


def main() -> None:
    stress_path = ROOT / "05_results/tsp_candan_stress_zeta_audit_paper/per_scene.csv"
    physical_path = ROOT / "05_results/tsp_candan_physical_zeta_audit_paper/per_scene_physical_zeta.csv"
    stress = [r for r in read_csv(stress_path) if r["split"] == "test"]
    physical = read_csv(physical_path)
    associations = correlation_rows(
        stress, domain="controlled_stress", profile="All",
        error_key="candan_mean_coordinate_error_bins",
    )
    distributions = [quantile_rows(stress, domain="controlled_stress", profile="All")]
    bins = binned_rows(
        stress, domain="controlled_stress", profile="All",
        error_key="candan_mean_coordinate_error_bins",
    )
    for profile in ("A", "C", "D", "All"):
        selected = physical if profile == "All" else [r for r in physical if r["profile"] == profile]
        associations.extend(correlation_rows(
            selected, domain="CDL", profile=profile,
            error_key="candan_median_coordinate_error_bins",
        ))
        distributions.append(quantile_rows(selected, domain="CDL", profile=profile))
        bins.extend(binned_rows(
            selected, domain="CDL", profile=profile,
            error_key="candan_median_coordinate_error_bins",
        ))
    output = ROOT / "05_results/tsp_candan_zeta_closed_loop_paper"
    output.mkdir(parents=True, exist_ok=True)
    write_csv(output / "zeta_associations.csv", associations)
    write_csv(output / "zeta_profile_distributions.csv", distributions)
    write_csv(output / "zeta_beneficial_clipping_bins.csv", bins)
    summary = {
        "stress_test_scenes": len(stress), "cdl_test_scenes": len(physical),
        "association_rows": len(associations), "binned_rows": len(bins),
        "input_sha256": {
            str(stress_path.relative_to(ROOT)): sha256(stress_path),
            str(physical_path.relative_to(ROOT)): sha256(physical_path),
        },
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    code_path = Path(__file__).resolve()
    manifest = {
        "run_id": "tsp_candan_zeta_closed_loop_20260830",
        "command": "python 04_experiments/eval/summarize_tsp_candan_zeta_closed_loop.py",
        "cwd": str(ROOT), "metrics": summary,
        "code_sha256": {str(code_path.relative_to(ROOT)): sha256(code_path)},
        "software": {"python": sys.version, "numpy": np.__version__, "platform": platform.platform()},
        "git_commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False).stdout.strip(),
        "notes": [
            "All associations are descriptive two-sided Spearman statistics over frozen test scenes.",
            "Quantile bins are formed independently within each reported domain/profile and use no clean truth for estimator decisions.",
        ],
    }
    (output / "audit_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (output / "command.txt").write_text(manifest["command"] + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
