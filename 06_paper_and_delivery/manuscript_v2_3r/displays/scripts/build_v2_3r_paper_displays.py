from __future__ import annotations

import csv
import json
from pathlib import Path
import statistics
import sys
from typing import Any

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[4]
MANUSCRIPT = ROOT / "06_paper_and_delivery" / "manuscript_v2_3r"
DISPLAY_DIR = MANUSCRIPT / "displays"
FIGURE_DIR = DISPLAY_DIR / "figures"
TABLE_DIR = DISPLAY_DIR / "tables"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def fnum(value: str | float | int) -> float:
    return float(value)


def fmt(value: float, digits: int = 4) -> str:
    return f"{value:.{digits}f}"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def group_by(rows: list[dict[str, str]], key: str) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(row[key], []).append(row)
    return grouped


def mean(values: list[float]) -> float:
    return float(statistics.mean(values))


def stdev(values: list[float]) -> float:
    return float(statistics.stdev(values)) if len(values) > 1 else 0.0


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_g2_summary() -> list[dict[str, float]]:
    rows = read_csv(
        ROOT
        / "05_results"
        / "stage2_torch_locked_scale_g2_seed_sweep_paper_30test"
        / "stage2_torch_locked_scale_g2_seed_sweep_cells.csv"
    )
    output: list[dict[str, float]] = []
    for key, group in sorted(group_by(rows, "n_targets").items(), key=lambda item: fnum(item[0])):
        gains = [fnum(row["test_gain_vs_grid_db"]) for row in group]
        grid = [fnum(row["test_grid_nmse_db"]) for row in group]
        tomp = [fnum(row["test_torch_nmse_db"]) for row in group]
        full_refine_gap = [fnum(row["test_gap_vs_full_refine_db"]) for row in group]
        output.append(
            {
                "n_targets": fnum(key),
                "mean_grid_nmse_db": mean(grid),
                "mean_tompnet_nmse_db": mean(tomp),
                "mean_gain_vs_grid_db": mean(gains),
                "std_gain_vs_grid_db": stdev(gains),
                "min_gain_vs_grid_db": min(gains),
                "mean_gap_vs_full_refine_db": mean(full_refine_gap),
                "n_seed_cells": float(len(group)),
            }
        )
    return output


def build_a4_cross_l_summary() -> list[dict[str, float]]:
    rows = read_csv(
        ROOT
        / "05_results"
        / "stage3_a4_cross_l_plateau_gate_seed_sweep_strengthened"
        / "stage3_a4_cross_l_plateau_gate_seed_sweep_l_summary.csv"
    )
    return [
        {
            "n_targets": fnum(row["n_targets"]),
            "mean_depth_savings_percent": fnum(row["mean_depth_savings_percent"]),
            "min_depth_savings_percent": fnum(row["min_depth_savings_percent"]),
            "mean_nmse_gap_db": fnum(row["mean_nmse_gap_db"]),
            "max_nmse_gap_db": fnum(row["max_nmse_gap_db"]),
            "n_seed_cells": fnum(row["n_seed_cells"]),
        }
        for row in rows
    ]


def build_a4_snr_summary() -> list[dict[str, float]]:
    rows = read_csv(
        ROOT
        / "05_results"
        / "stage3_a4_snr_plateau_gate_seed_sweep"
        / "stage3_a4_snr_plateau_gate_seed_sweep_snr_summary.csv"
    )
    return [
        {
            "snr_db": fnum(row["snr_db"]),
            "mean_depth_savings_percent": fnum(row["mean_depth_savings_percent"]),
            "min_depth_savings_percent": fnum(row["min_depth_savings_percent"]),
            "mean_nmse_gap_db": fnum(row["mean_nmse_gap_db"]),
            "max_nmse_gap_db": fnum(row["max_nmse_gap_db"]),
            "n_seed_cells": fnum(row["n_seed_cells"]),
        }
        for row in rows
    ]


def build_a4_frontier_summary() -> list[dict[str, float | str]]:
    rows = read_csv(
        ROOT
        / "05_results"
        / "stage3_a4_snr_threshold_frontier"
        / "stage3_a4_snr_threshold_frontier_summary.csv"
    )
    return [
        {
            "policy": row["policy"],
            "snr_db": fnum(row["snr_db"]),
            "mean_depth_savings_percent": fnum(row["mean_depth_savings_percent"]),
            "min_depth_savings_percent": fnum(row["min_depth_savings_percent"]),
            "mean_nmse_gap_db": fnum(row["mean_nmse_gap_db"]),
            "max_nmse_gap_db": fnum(row["max_nmse_gap_db"]),
            "pass_rate": fnum(row["pass_rate"]),
            "n_seed_cells": fnum(row["n_seed_cells"]),
        }
        for row in rows
    ]


def build_a4_snr_aware_summary() -> list[dict[str, float | str]]:
    rows = read_csv(
        ROOT
        / "05_results"
        / "stage3_a4_snr_aware_gate_diagnostic"
        / "stage3_a4_snr_aware_gate_summary.csv"
    )
    return [
        {
            "policy": row["policy"],
            "snr_db": fnum(row["snr_db"]),
            "mean_depth_savings_percent": fnum(row["mean_depth_savings_percent"]),
            "min_depth_savings_percent": fnum(row["min_depth_savings_percent"]),
            "mean_nmse_gap_db": fnum(row["mean_nmse_gap_db"]),
            "max_nmse_gap_db": fnum(row["max_nmse_gap_db"]),
            "sample_pass_rate": fnum(row["sample_pass_rate"]),
            "n_samples": fnum(row["n_samples"]),
        }
        for row in rows
    ]


def write_csv(path: Path, rows: list[dict[str, float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_e12_pareto_summary() -> list[dict[str, float | str]]:
    rows = read_csv(
        ROOT / "05_results" / "tensor_nomp3d_matched_paper_5seed" / "matched_accuracy_rows.csv"
    )
    rows.extend(
        read_csv(
            ROOT / "05_results" / "e12_matched_accuracy_comparators" / "matched_accuracy_rows.csv"
        )
    )
    output: list[dict[str, float | str]] = []
    labels = {
        "grid_fft_topk_plus_ls": "Grid FFT top-k + LS",
        "deterministic_cartesian_local_refinement_plus_ls": "Deterministic local refinement",
        "fixed_source_trained_scalar_interpolation_plus_ls": "Learned scalar refinement",
        "tensor_nomp3d_known_order_v1": "NOMP-inspired refinement",
        "complex_parafac_als_10_sweeps": "Complex PARAFAC-ALS",
    }
    for method, group in group_by(rows, "method").items():
        seed_means = []
        for _, seed_rows in group_by(group, "seed").items():
            seed_means.append(mean([fnum(row["measurement_nmse_db"]) for row in seed_rows]))
        center = mean(seed_means)
        ci_half = 2.776 * stdev(seed_means) / np.sqrt(len(seed_means))
        output.append({
            "method": method,
            "label": labels[method],
            "mean_nmse_db": center,
            "ci95_low_db": center - ci_half,
            "ci95_high_db": center + ci_half,
            "median_wall_clock_ms": float(np.median([fnum(row["wall_clock_ms"]) for row in group])),
            "mean_within_half_bin": mean([fnum(row["matched_fraction_within_half_bin"]) for row in group]),
            "sample_count": float(len(group)),
        })
    return output


def plot_e12_pareto(summary: list[dict[str, float | str]]) -> dict[str, str]:
    apply_style()
    style = {
        "grid_fft_topk_plus_ls": ("#7A7A7A", "o", "Grid"),
        "deterministic_cartesian_local_refinement_plus_ls": ("#4E79A7", "s", "Local"),
        "fixed_source_trained_scalar_interpolation_plus_ls": ("#E69F00", "*", "Learned"),
        "tensor_nomp3d_known_order_v1": ("#7A5195", "D", "NOMP-inspired"),
        "complex_parafac_als_10_sweeps": ("#2A9D8F", "P", "PARAFAC"),
    }
    by_method = {str(row["method"]): row for row in summary}
    left_frontier = [
        "grid_fft_topk_plus_ls",
        "complex_parafac_als_10_sweeps",
        "tensor_nomp3d_known_order_v1",
    ]
    right_frontier = [
        "grid_fft_topk_plus_ls",
        "fixed_source_trained_scalar_interpolation_plus_ls",
        "deterministic_cartesian_local_refinement_plus_ls",
        "tensor_nomp3d_known_order_v1",
    ]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.85), constrained_layout=True)

    for panel, (ax, metric, ylabel, frontier) in enumerate([
        (axes[0], "mean_nmse_db", "Measurement NMSE (dB)", left_frontier),
        (axes[1], "mean_within_half_bin", "All-axis half-bin hit rate (%)", right_frontier),
    ]):
        frontier_xy = [
            (float(by_method[key]["median_wall_clock_ms"]),
             100.0 * float(by_method[key][metric]) if panel else float(by_method[key][metric]))
            for key in frontier
        ]
        ax.plot(
            [item[0] for item in frontier_xy], [item[1] for item in frontier_xy],
            color="#555555", lw=1.1, ls="--", alpha=0.75, zorder=1,
            label="Non-dominated frontier",
        )
        for method, row in by_method.items():
            color, marker, short = style[method]
            x = float(row["median_wall_clock_ms"])
            y = 100.0 * float(row[metric]) if panel else float(row[metric])
            kwargs = {}
            if panel == 0:
                kwargs["yerr"] = np.asarray([[
                    y - float(row["ci95_low_db"])
                ], [
                    float(row["ci95_high_db"]) - y
                ]])
            ax.errorbar(
                x, y, fmt=marker, color=color, markeredgecolor="white",
                markeredgewidth=0.7, capsize=2.2, markersize=7.2,
                zorder=3, **kwargs,
            )
            offsets = ({
                "Grid": (5, 5), "PARAFAC": (5, -13), "Local": (6, -13),
                "Learned": (6, 7), "NOMP-inspired": (-78, 7),
            } if panel == 0 else {
                "Grid": (5, 5), "PARAFAC": (5, 8), "Local": (6, -15),
                "Learned": (6, 7), "NOMP-inspired": (-78, 8),
            })
            ax.annotate(
                short, (x, y), xytext=offsets[short], textcoords="offset points",
                fontsize=7.2, color="#273142",
            )
        ax.set_xscale("log")
        ax.set_xlabel("Median CPU wall-clock (ms, log scale)")
        ax.set_ylabel(ylabel)
        ax.grid(alpha=0.24, which="both")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.text(-0.075, 1.02, "a" if panel == 0 else "b", transform=ax.transAxes,
                va="top", fontweight="bold", clip_on=False)
    axes[0].annotate(
        "better", xy=(0.04, 0.06), xytext=(0.22, 0.22),
        xycoords="axes fraction", textcoords="axes fraction",
        arrowprops={"arrowstyle": "->", "color": "#555555", "lw": 0.9},
        fontsize=7.2, color="#555555",
    )
    axes[1].annotate(
        "better", xy=(0.04, 0.94), xytext=(0.22, 0.78),
        xycoords="axes fraction", textcoords="axes fraction",
        arrowprops={"arrowstyle": "->", "color": "#555555", "lw": 0.9},
        fontsize=7.2, color="#555555",
    )
    axes[0].legend(frameon=False, loc="lower center", fontsize=7.0)
    axes[1].text(
        0.98, 0.04, "Known order; dense matched tensor", transform=axes[1].transAxes,
        ha="right", va="bottom", fontsize=6.8, color="#666666",
    )
    png = FIGURE_DIR / "v2_3r_pareto_compute_accuracy.png"
    pdf = FIGURE_DIR / "v2_3r_pareto_compute_accuracy.pdf"
    fig.savefig(png, dpi=300)
    fig.savefig(pdf)
    plt.close(fig)
    return {"png": rel(png), "pdf": rel(pdf)}


def write_e12_table(summary: list[dict[str, float | str]]) -> None:
    lines = [
        "# E12 Matched Accuracy and Runtime",
        "",
        "| Method | NMSE (dB; seed-mean 95% CI) | Median ms | Within half bin | Availability |",
        "|---|---:|---:|---:|---|",
    ]
    for row in summary:
        lines.append(
            f"| {row['label']} | {float(row['mean_nmse_db']):.3f} "
            f"[{float(row['ci95_low_db']):.3f}, {float(row['ci95_high_db']):.3f}] | "
            f"{float(row['median_wall_clock_ms']):.2f} | "
            f"{float(row['mean_within_half_bin']):.3f} | matched accuracy |"
        )
    lines.append(
        "| Separable FB-ESPRIT | -- | see E4 timing table | -- | timing-only: no cross-axis pairing |"
    )
    write_text(TABLE_DIR / "v2_3r_e12_matched_accuracy_table.md", "\n".join(lines) + "\n")


def build_markdown_tables(
    g2: list[dict[str, float]],
    a4_l: list[dict[str, float]],
    a4_snr: list[dict[str, float]],
    a4_frontier: list[dict[str, float | str]],
    a4_snr_aware: list[dict[str, float | str]],
) -> None:
    main_lines = [
        "# v2.3R Main Result Table",
        "",
        "| Result | Axis | Primary metric | Boundary |",
        "|---|---|---:|---|",
    ]
    for row in g2:
        main_lines.append(
            "| G2 one-parameter bounded interpolation | "
            f"L={int(row['n_targets'])} | "
            f"{fmt(row['mean_gain_vs_grid_db'])} dB mean gain; {fmt(row['min_gain_vs_grid_db'])} dB min seed-cell gain | "
            "local synthetic/off-grid |"
        )
    for row in a4_l:
        verdict = "positive high-L support" if row["n_targets"] >= 32 else "boundary"
        main_lines.append(
            "| A4 plateau early stop | "
            f"L={int(row['n_targets'])} | "
            f"{fmt(row['mean_depth_savings_percent'])}% savings; {fmt(row['max_nmse_gap_db'])} dB max gap | "
            f"{verdict} |"
        )
    write_text(TABLE_DIR / "v2_3r_main_result_table.md", "\n".join(main_lines) + "\n")

    sensitivity_lines = [
        "# v2.3R A4 SNR Sensitivity Table",
        "",
        "| SNR (dB) | Mean savings (%) | Min savings (%) | Mean gap (dB) | Max gap (dB) | Paper use |",
        "|---:|---:|---:|---:|---:|---|",
    ]
    for row in a4_snr:
        if row["mean_depth_savings_percent"] < 25.0:
            use = "boundary: savings below target"
        elif row["max_nmse_gap_db"] > 0.5:
            use = "boundary: gap exceeds tolerance"
        else:
            use = "passes this small cell only"
        sensitivity_lines.append(
            "| "
            f"{row['snr_db']:.1f} | "
            f"{fmt(row['mean_depth_savings_percent'])} | "
            f"{fmt(row['min_depth_savings_percent'])} | "
            f"{fmt(row['mean_nmse_gap_db'])} | "
            f"{fmt(row['max_nmse_gap_db'])} | "
            f"{use} |"
        )
    write_text(TABLE_DIR / "v2_3r_a4_snr_sensitivity_table.md", "\n".join(sensitivity_lines) + "\n")

    frontier_lines = [
        "# v2.3R A4 SNR Threshold Frontier Table",
        "",
        "| Policy | SNR (dB) | Mean savings (%) | Min savings (%) | Mean gap (dB) | Max gap (dB) | Pass rate | Paper use |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in a4_frontier:
        policy = str(row["policy"])
        if policy == "test_oracle_frontier":
            use = "diagnostic upper bound, not deployable"
        elif policy == "guarded_train":
            use = "conservative scalar threshold diagnostic"
        else:
            use = "train-selected scalar threshold diagnostic"
        frontier_lines.append(
            "| "
            f"{policy} | "
            f"{float(row['snr_db']):.1f} | "
            f"{fmt(float(row['mean_depth_savings_percent']))} | "
            f"{fmt(float(row['min_depth_savings_percent']))} | "
            f"{fmt(float(row['mean_nmse_gap_db']))} | "
            f"{fmt(float(row['max_nmse_gap_db']))} | "
            f"{fmt(float(row['pass_rate']))} | "
            f"{use} |"
        )
    write_text(TABLE_DIR / "v2_3r_a4_snr_threshold_frontier_table.md", "\n".join(frontier_lines) + "\n")

    snr_aware_lines = [
        "# v2.3R A4 SNR-Aware Gate Diagnostic Table",
        "",
        "| Policy | SNR (dB) | Mean savings (%) | Min savings (%) | Mean gap (dB) | Max gap (dB) | Sample pass rate | Paper use |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in a4_snr_aware:
        policy = str(row["policy"])
        if policy == "per_curve_quality_oracle":
            use = "diagnostic upper bound, not deployable"
        elif policy == "curve_feature_knn_train":
            use = "lightweight learned gate diagnostic"
        else:
            use = "SNR-indexed scalar threshold comparator"
        snr_aware_lines.append(
            "| "
            f"{policy} | "
            f"{float(row['snr_db']):.1f} | "
            f"{fmt(float(row['mean_depth_savings_percent']))} | "
            f"{fmt(float(row['min_depth_savings_percent']))} | "
            f"{fmt(float(row['mean_nmse_gap_db']))} | "
            f"{fmt(float(row['max_nmse_gap_db']))} | "
            f"{fmt(float(row['sample_pass_rate']))} | "
            f"{use} |"
        )
    write_text(TABLE_DIR / "v2_3r_a4_snr_aware_gate_table.md", "\n".join(snr_aware_lines) + "\n")


def apply_style() -> None:
    plt.style.use("default")
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "#4B5563",
            "axes.labelcolor": "#111827",
            "axes.linewidth": 0.8,
            "axes.titlesize": 9.5,
            "axes.labelsize": 8.5,
            "font.size": 8,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 7.5,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.bbox": "tight",
        }
    )


def plot_display(g2: list[dict[str, float]], a4_l: list[dict[str, float]], a4_snr: list[dict[str, float]]) -> dict[str, str]:
    apply_style()
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.45), constrained_layout=True)

    colors = {
        "main": "#4E79A7",
        "support": "#59A14F",
        "boundary": "#E15759",
        "neutral": "#8C8C8C",
        "light": "#D9E2EC",
    }

    # Panel A: individual seed means plus the L-wise mean.
    ax = axes[0]
    raw_g2 = read_csv(
        ROOT
        / "05_results"
        / "stage2_torch_locked_scale_g2_seed_sweep_paper_30test"
        / "stage2_torch_locked_scale_g2_seed_sweep_cells.csv"
    )
    l_values = [int(row["n_targets"]) for row in g2]
    x = np.arange(len(l_values), dtype=float)
    rng = np.random.default_rng(20260629)
    for index, l_value in enumerate(l_values):
        seed_gains = np.asarray(
            [
                fnum(row["test_gain_vs_grid_db"])
                for row in raw_g2
                if int(fnum(row["n_targets"])) == l_value
            ]
        )
        ax.scatter(
            np.full(len(seed_gains), index) + rng.uniform(-0.07, 0.07, len(seed_gains)),
            seed_gains,
            s=18,
            facecolor="white",
            edgecolor=colors["main"],
            linewidth=0.9,
            zorder=3,
        )
        ax.scatter(
            [index],
            [np.mean(seed_gains)],
            marker="D",
            s=34,
            color=colors["main"],
            edgecolor="white",
            linewidth=0.6,
            zorder=4,
        )
    ax.axhline(3.0, color=colors["neutral"], lw=0.9, ls="--")
    ax.set_xticks(x, [str(value) for value in l_values])
    ax.set_xlabel("Targets L")
    ax.set_ylabel("NMSE gain vs grid (dB)")
    ax.set_title("G2: five seed means")
    ax.text(0.02, 0.92, "a", transform=ax.transAxes, fontweight="bold", fontsize=8.5)
    ax.text(0.98, 0.08, "3 dB gate", transform=ax.transAxes, ha="right", va="bottom", fontsize=6.5, color=colors["neutral"])
    ax.set_ylim(2.5, 8.2)

    # Panel B: cross-L trade-off in one coordinate system.
    ax = axes[1]
    xlim = (18.0, 36.0)
    ylim = (0.25, 0.72)
    ax.fill_between([25.0, xlim[1]], ylim[0], 0.5, color="#E4F0E7", alpha=0.9)
    ax.axvline(25.0, color=colors["neutral"], lw=0.9, ls="--")
    ax.axhline(0.5, color=colors["neutral"], lw=0.9, ls="--")
    for row in a4_l:
        passed = row["mean_depth_savings_percent"] >= 25.0 and row["max_nmse_gap_db"] <= 0.5
        color = colors["support"] if passed else colors["boundary"]
        ax.scatter(
            row["mean_depth_savings_percent"],
            row["max_nmse_gap_db"],
            s=34,
            color=color,
            edgecolor="white",
            linewidth=0.6,
            zorder=3,
        )
        ax.annotate(
            f"L={int(row['n_targets'])}",
            (row["mean_depth_savings_percent"], row["max_nmse_gap_db"]),
            xytext=(4, 4),
            textcoords="offset points",
            fontsize=6.5,
            color="#2F4858",
        )
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_xlabel("Mean depth saving (%)")
    ax.set_ylabel("Maximum NMSE gap (dB)")
    ax.set_title("A4: cross-L trade-off at 20 dB")
    ax.text(0.02, 0.92, "b", transform=ax.transAxes, fontweight="bold", fontsize=8.5)
    ax.text(0.97, 0.08, "admissible", transform=ax.transAxes, ha="right", fontsize=6.3, color=colors["support"])

    # Panel C: SNR sensitivity in the same coordinate system.
    ax = axes[2]
    ax.fill_between([25.0, xlim[1]], ylim[0], 0.5, color="#E4F0E7", alpha=0.9)
    ax.axvline(25.0, color=colors["neutral"], lw=0.9, ls="--")
    ax.axhline(0.5, color=colors["neutral"], lw=0.9, ls="--")
    for row in a4_snr:
        passed = row["mean_depth_savings_percent"] >= 25.0 and row["max_nmse_gap_db"] <= 0.5
        color = colors["support"] if passed else colors["boundary"]
        ax.scatter(
            row["mean_depth_savings_percent"],
            row["max_nmse_gap_db"],
            s=34,
            color=color,
            edgecolor="white",
            linewidth=0.6,
            zorder=3,
        )
        label_left = row["mean_depth_savings_percent"] > 33.0
        ax.annotate(
            f"{int(row['snr_db'])} dB",
            (row["mean_depth_savings_percent"], row["max_nmse_gap_db"]),
            xytext=(-4 if label_left else 4, 4),
            textcoords="offset points",
            ha="right" if label_left else "left",
            fontsize=6.5,
            color="#2F4858",
        )
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_xlabel("Mean depth saving (%)")
    ax.set_ylabel("Maximum NMSE gap (dB)")
    ax.set_title("A4: SNR sensitivity at L=32")
    ax.text(0.02, 0.92, "c", transform=ax.transAxes, fontweight="bold", fontsize=8.5)
    ax.text(0.97, 0.08, "no cell passes", transform=ax.transAxes, ha="right", fontsize=6.3, color=colors["boundary"])

    for item in axes:
        item.grid(alpha=0.22)
        item.spines["top"].set_visible(False)

    png = FIGURE_DIR / "v2_3r_evidence_summary.png"
    pdf = FIGURE_DIR / "v2_3r_evidence_summary.pdf"
    fig.savefig(png, dpi=300)
    fig.savefig(pdf)
    plt.close(fig)
    return {"png": rel(png), "pdf": rel(pdf)}


def write_catalog(paths: dict[str, str], pareto_paths: dict[str, str], tables: dict[str, str]) -> None:
    catalog_path = DISPLAY_DIR / "figure_catalog.json"
    existing: dict[str, Any] = {}
    if catalog_path.exists():
        existing = json.loads(catalog_path.read_text(encoding="utf-8"))
    evidence_entry = {
        "id": "fig_v2_3r_evidence_summary",
        "surface_class": "paper_main_candidate",
        "claim": "G2 is locally supported; A4 is positive only for high-L at the core SNR, while SNR sensitivity is boundary evidence.",
        "source_data": [
            "05_results/stage2_torch_locked_scale_g2_seed_sweep/stage2_torch_locked_scale_g2_seed_sweep_cells.csv",
            "05_results/stage3_a4_cross_l_plateau_gate_seed_sweep/stage3_a4_cross_l_plateau_gate_seed_sweep_l_summary.csv",
            "05_results/stage3_a4_snr_plateau_gate_seed_sweep/stage3_a4_snr_plateau_gate_seed_sweep_snr_summary.csv",
        ],
        "script": "06_paper_and_delivery/manuscript_v2_3r/displays/scripts/build_v2_3r_paper_displays.py",
        "exports": paths,
        "self_review_note": "Rendered figure was inspected and revised into a gate-centered trade-off plane with individual G2 seeds and no dual axes.",
    }
    pareto_entry = {
        "id": "fig_v2_3r_pareto_compute_accuracy",
        "surface_class": "paper_main_candidate",
        "claim": "The learned scalar is a low-compute amortized point; NOMP-inspired refinement dominates matched-synthetic accuracy at higher runtime.",
        "source_data": [
            "05_results/tensor_nomp3d_matched_paper_5seed/matched_accuracy_rows.csv",
            "05_results/e12_matched_accuracy_comparators/matched_accuracy_rows.csv",
        ],
        "script": "06_paper_and_delivery/manuscript_v2_3r/displays/scripts/build_v2_3r_paper_displays.py",
        "exports": pareto_paths,
        "self_review_note": "Single log-runtime axis, seed-mean 95% NMSE intervals, colorblind-safe colors, and no accuracy-win framing for the learned point.",
    }
    retained = [
        item for item in existing.get("figures", [])
        if item.get("id") not in {evidence_entry["id"], pareto_entry["id"]}
    ]
    catalog: dict[str, Any] = {
        "version": 1,
        "generated_at": "2026-06-29",
        "figures": retained + [evidence_entry, pareto_entry],
        "tables": {**existing.get("tables", {}), **tables},
    }
    write_text(catalog_path, json.dumps(catalog, indent=2) + "\n")


def main() -> None:
    g2 = build_g2_summary()
    a4_l = build_a4_cross_l_summary()
    a4_snr = build_a4_snr_summary()
    a4_frontier = build_a4_frontier_summary()
    a4_snr_aware = build_a4_snr_aware_summary()
    e12_pareto = build_e12_pareto_summary()

    write_csv(TABLE_DIR / "v2_3r_g2_l_summary.csv", g2)
    write_csv(TABLE_DIR / "v2_3r_a4_cross_l_summary.csv", a4_l)
    write_csv(TABLE_DIR / "v2_3r_a4_snr_summary.csv", a4_snr)
    write_csv(TABLE_DIR / "v2_3r_a4_snr_threshold_frontier_summary.csv", a4_frontier)  # type: ignore[arg-type]
    write_csv(TABLE_DIR / "v2_3r_a4_snr_aware_gate_summary.csv", a4_snr_aware)  # type: ignore[arg-type]
    build_markdown_tables(g2, a4_l, a4_snr, a4_frontier, a4_snr_aware)
    write_csv(TABLE_DIR / "v2_3r_e12_pareto_summary.csv", e12_pareto)  # type: ignore[arg-type]
    write_e12_table(e12_pareto)
    figure_paths = plot_display(g2, a4_l, a4_snr)
    pareto_paths = plot_e12_pareto(e12_pareto)
    write_catalog(
        figure_paths,
        pareto_paths,
        {
            "main_result_table": "06_paper_and_delivery/manuscript_v2_3r/displays/tables/v2_3r_main_result_table.md",
            "a4_snr_sensitivity_table": "06_paper_and_delivery/manuscript_v2_3r/displays/tables/v2_3r_a4_snr_sensitivity_table.md",
            "a4_snr_threshold_frontier_table": "06_paper_and_delivery/manuscript_v2_3r/displays/tables/v2_3r_a4_snr_threshold_frontier_table.md",
            "a4_snr_aware_gate_table": "06_paper_and_delivery/manuscript_v2_3r/displays/tables/v2_3r_a4_snr_aware_gate_table.md",
            "e12_matched_accuracy_table": "06_paper_and_delivery/manuscript_v2_3r/displays/tables/v2_3r_e12_matched_accuracy_table.md",
        },
    )
    print(f"Wrote {pareto_paths['png']}")
    print(f"Wrote {pareto_paths['pdf']}")
    print(f"Wrote {figure_paths['png']}")
    print(f"Wrote {figure_paths['pdf']}")
    print("Wrote 06_paper_and_delivery/manuscript_v2_3r/displays/figure_catalog.json")


if __name__ == "__main__":
    sys.exit(main())
