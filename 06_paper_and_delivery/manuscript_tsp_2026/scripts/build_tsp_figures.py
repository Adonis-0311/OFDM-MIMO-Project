"""Rebuild TSP-facing figures from registered CSV artifacts.

The script changes presentation only. It reads the same MATLAB evidence files
used by the manuscript and exports embedded TrueType vector PDFs plus SVG,
PNG, and TIFF companions.
"""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np


ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "05_results" / "matlab_taes_supplement"
PARETO_SUMMARY = (
    ROOT
    / "06_paper_and_delivery"
    / "manuscript_v2_3r"
    / "displays"
    / "tables"
    / "v2_3r_e12_pareto_summary.csv"
)
MATCHED_ROWS = ROOT / "05_results" / "tensor_nomp3d_matched_paper_5seed" / "matched_accuracy_rows.csv"
PARAFAC_ROWS = ROOT / "05_results" / "e12_matched_accuracy_comparators" / "matched_accuracy_rows.csv"
GATE_DIR = ROOT / "05_results" / "tsp_reliability_gate_round2_paper"
COST_DIR = ROOT / "05_results" / "tsp_controlled_local_family_paper"
STRESS_DIR = ROOT / "05_results" / "tsp_separation_nearfar_metrics_v2_paper"
SEPARABLE_DIR = ROOT / "05_results" / "tsp_separable_local_benchmark_paper"
RUNTIME_DIR = ROOT / "05_results" / "tsp_unified_runtime_paper"
FULL_OFFSET_DIR = ROOT / "05_results" / "tsp_full_offset_sweep_paper"
SUPPORT_DIR = ROOT / "05_results" / "tsp_support_quality_stratification_paper"
GATE_ANALYSIS_DIR = ROOT / "05_results" / "tsp_gate_reliability_curve_paper"
TRANSFER_DIR = ROOT / "05_results" / "tsp_cross_geometry_threshold_transfer_paper"
OUT = Path(__file__).resolve().parents[1] / "figures"

BLUE = "#0B5CAD"
TEAL = "#0F766E"
RED = "#B64040"
GOLD = "#B7791F"
GRAY = "#6B7280"
TEXT = "#172033"


def apply_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "font.size": 8,
            "axes.labelsize": 8,
            "axes.titlesize": 8.5,
            "xtick.labelsize": 7.5,
            "ytick.labelsize": 7.5,
            "legend.fontsize": 7.2,
            "axes.linewidth": 0.8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "xtick.direction": "out",
            "ytick.direction": "out",
            "legend.frameon": False,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "text.color": TEXT,
            "axes.labelcolor": TEXT,
            "xtick.color": TEXT,
            "ytick.color": TEXT,
        }
    )


def save_bundle(fig: plt.Figure, stem: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for suffix, kwargs in (
        ("pdf", {}),
        ("svg", {}),
        ("png", {"dpi": 300}),
        ("tiff", {"dpi": 600}),
    ):
        fig.savefig(OUT / f"{stem}.{suffix}", bbox_inches="tight", **kwargs)
    plt.close(fig)


def read_rows(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_path(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def learning_marginal() -> None:
    rows = read_rows("learning_marginal_rows.csv")
    grouped: dict[tuple[int, int, str], list[float]] = defaultdict(list)
    for row in rows:
        grouped[(int(row["seed"]), int(row["L"]), row["method"])].append(float(row["nmse_db"]))

    methods = ["grid", "deterministic", "learned", "oracle_alpha"]
    labels = ["Grid", "Deterministic", "Learned\nscalar", "Scalar\noracle"]
    colors = [GRAY, TEAL, BLUE, GOLD]
    markers = ["o", "s", "^", "D"]

    cell_means: dict[str, list[float]] = {method: [] for method in methods}
    for (_, _, method), values in grouped.items():
        cell_means[method].append(float(np.mean(values)))

    fig, ax = plt.subplots(figsize=(3.5, 2.45))
    for idx, method in enumerate(methods):
        values = np.asarray(cell_means[method])
        jitter = np.linspace(-0.09, 0.09, len(values))
        ax.scatter(
            idx + jitter,
            values,
            s=15,
            facecolors="none",
            edgecolors=colors[idx],
            marker=markers[idx],
            linewidths=0.8,
            alpha=0.85,
            zorder=2,
        )
        ax.scatter(
            idx,
            values.mean(),
            s=42,
            color=colors[idx],
            edgecolor="white",
            linewidth=0.6,
            marker="D",
            zorder=3,
        )

    ax.axhline(0, color="#CBD5E1", linewidth=0.7, zorder=0)
    ax.set_xticks(range(len(methods)), labels)
    ax.set_ylabel("Measurement NMSE (dB; lower is better)")
    ax.grid(axis="y", color="#E5E7EB", linewidth=0.6)
    ax.text(
        0.98,
        0.96,
        "learned $-$ deterministic:\n0.07 dB, 95% CI [$-0.12$, 0.25]",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=7.1,
    )
    save_bundle(fig, "v2_3r_learning_marginal")


def method_flow() -> None:
    fig, ax = plt.subplots(figsize=(7.1, 2.25))
    ax.set_xlim(0, 12.2)
    ax.set_ylim(0, 3.2)
    ax.axis("off")

    boxes = [
        (0.15, 1.2, 1.45, 1.05, "Dense\nobservation\n$\\mathbf{y}$", "#E8EEF5"),
        (2.0, 1.2, 1.65, 1.05, "FFT top-$L$\ncoarse\nsupport", "#E8EEF5"),
        (4.05, 1.2, 1.9, 1.05, "$5^D L$ local scores\nfixed candidate set", "#E8EEF5"),
        (6.35, 1.2, 1.55, 1.05, "Joint LS\nlocal estimate", "#E5F1ED"),
        (8.3, 1.2, 1.55, 1.05, "Residual gate\n$\\Delta\\rho\\geq\\tau_\\rho$?", "#FFF4D6"),
    ]
    for x, y, w, h, label, color in boxes:
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                w,
                h,
                boxstyle="round,pad=0.03,rounding_size=0.04",
                facecolor=color,
                edgecolor=TEXT,
                linewidth=1.0,
            )
        )
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=7.4)
    for start, end in [((1.60, 1.72), (2.0, 1.72)), ((3.65, 1.72), (4.05, 1.72)), ((5.95, 1.72), (6.35, 1.72)), ((7.90, 1.72), (8.30, 1.72))]:
        ax.add_patch(
            FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=11, color=TEXT, linewidth=1.0)
        )

    outputs = [
        (10.35, 2.05, 1.55, 0.72, "accept local\ncoordinates + LS", "#DCEFE8"),
        (10.35, 0.45, 1.55, 0.72, "return grid\ncoordinates + fit", "#FBE6E6"),
    ]
    for x, y, w, h, label, color in outputs:
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                w,
                h,
                boxstyle="round,pad=0.03,rounding_size=0.04",
                facecolor=color,
                edgecolor=TEXT,
                linewidth=1.0,
            )
        )
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=7.2)
    ax.add_patch(
        FancyArrowPatch((9.85, 1.85), (10.35, 2.37), arrowstyle="-|>", mutation_scale=11, color=TEAL, linewidth=1.1)
    )
    ax.add_patch(
        FancyArrowPatch((9.85, 1.45), (10.35, 0.81), arrowstyle="-|>", mutation_scale=11, color=RED, linewidth=1.1)
    )
    ax.text(10.0, 2.22, "yes", color=TEAL, fontsize=7.3, ha="center")
    ax.text(10.0, 0.96, "no", color=RED, fontsize=7.3, ha="center")
    ax.text(2.82, 0.76, r"grid residual $\rho_0$", ha="center", fontsize=7.4, color=GRAY)
    ax.text(7.12, 0.76, r"local residual $\rho_1$", ha="center", fontsize=7.4, color=GRAY)
    ax.text(6.05, 2.72, r"$\Delta\rho=\rho_0-\rho_1$ is observable from the same received tensor", ha="center", fontsize=7.7)
    ax.text(6.05, 0.10, "Support identity is retained; the gate changes only which coordinate set is returned.", ha="center", fontsize=7.5, color=GRAY)
    save_bundle(fig, "tsp_method_flow")


def system_model() -> None:
    """TSP-specific schematic with a neutral spatial-axis convention."""
    fig, ax = plt.subplots(figsize=(7.1, 2.25))
    ax.set_xlim(0, 12.4)
    ax.set_ylim(0, 3.2)
    ax.axis("off")

    inputs = [
        (0.15, 2.18, "Spatial ULA samples\n$N_a$", BLUE),
        (0.15, 1.22, "Frequency samples\n$N_\\tau$", TEAL),
        (0.15, 0.26, "Slow-time samples\n$N_\\nu$", GOLD),
    ]
    for x, y, label, color in inputs:
        ax.add_patch(
            FancyBboxPatch(
                (x, y), 1.75, 0.66,
                boxstyle="round,pad=0.03,rounding_size=0.04",
                facecolor=color, alpha=0.13, edgecolor=color, linewidth=1.0,
            )
        )
        ax.text(x + 0.875, y + 0.33, label, ha="center", va="center", fontsize=7.4)
        ax.add_patch(
            FancyArrowPatch((1.90, y + 0.33), (2.65, 1.55), arrowstyle="-|>",
                            mutation_scale=10, color=color, linewidth=1.0)
        )

    stages = [
        (2.68, 1.06, 2.25, 1.00, "Separable tensor\n$\\mathcal{Y}\\in\\mathbb{C}^{N_a\\times N_\\tau\\times N_\\nu}$", "#E8EEF5"),
        (5.38, 1.06, 1.80, 1.00, "Orthonormal FFT\n+ top-$L$ bins", "#E8EEF5"),
        (7.63, 1.06, 2.05, 1.00, "$5^D L$ local scores\n+ joint LS + gate", "#E5F1ED"),
        (10.13, 1.06, 2.05, 1.00, "Coordinates, gains,\nand reconstruction", "#FFF4D6"),
    ]
    for x, y, w, h, label, color in stages:
        ax.add_patch(
            FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03,rounding_size=0.04",
                           facecolor=color, edgecolor=TEXT, linewidth=1.0)
        )
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=7.5)
    for start, end in [((4.93, 1.56), (5.38, 1.56)), ((7.18, 1.56), (7.63, 1.56)),
                       ((9.68, 1.56), (10.13, 1.56))]:
        ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=10,
                                     color=TEXT, linewidth=1.0))
    ax.text(7.4, 2.72,
            r"$\mathcal{Y}=\sum_{\ell=1}^{L}\beta_\ell\,"
            r"\mathbf{a}_{N_a}(b_{a,\ell})\circ\mathbf{a}_{N_\tau}(b_{\tau,\ell})"
            r"\circ\mathbf{a}_{N_\nu}(b_{\nu,\ell})+\mathcal{W}$",
            ha="center", va="center", fontsize=8.3)
    ax.text(7.4, 0.25,
            "The synthetic model uses one generic spatial ULA axis; the CDL study instantiates it as the BS transmit ULA.",
            ha="center", va="center", fontsize=7.2, color=GRAY)
    save_bundle(fig, "tsp_system_model")


def runtime_comparison() -> None:
    rows = read_path(PARETO_SUMMARY)
    label_map = {
        "grid_fft_topk_plus_ls": "Grid",
        "deterministic_cartesian_local_refinement_plus_ls": "Local",
        "fixed_source_trained_scalar_interpolation_plus_ls": "Learned",
        "complex_parafac_als_10_sweeps": "PARAFAC",
        "tensor_nomp3d_known_order_v1": "NOMP-inspired",
    }
    labels = [label_map[row["method"]] for row in rows]
    x = np.asarray([float(row["median_wall_clock_ms"]) for row in rows])
    y = np.asarray([float(row["mean_nmse_db"]) for row in rows])
    y_low = np.asarray([float(row["ci95_low_db"]) for row in rows])
    y_high = np.asarray([float(row["ci95_high_db"]) for row in rows])
    half_bin = np.asarray([float(row["mean_within_half_bin"]) for row in rows])

    raw_rows = [*read_path(MATCHED_ROWS), *read_path(PARAFAC_ROWS)]
    seed_groups: dict[tuple[str, int], list[float]] = defaultdict(list)
    for row in raw_rows:
        seed_groups[(label_map[row["method"]], int(row["seed"]))].append(
            float(row["matched_fraction_within_half_bin"])
        )
    half_ci = []
    for label in labels:
        seed_means = np.asarray(
            [np.mean(values) for (name, _), values in seed_groups.items() if name == label]
        )
        half_ci.append(2.776445 * seed_means.std(ddof=1) / np.sqrt(seed_means.size))
    half_ci = np.asarray(half_ci)
    color_map = {
        "Grid": GRAY,
        "Local": TEAL,
        "Learned": BLUE,
        "PARAFAC": GOLD,
        "NOMP-inspired": RED,
    }
    marker_map = {"Grid": "o", "Local": "s", "Learned": "^", "PARAFAC": "D", "NOMP-inspired": "P"}

    fig, axes = plt.subplots(1, 2, figsize=(7.1, 2.55))
    ax = axes[0]
    for label, xi, yi, lo, hi in zip(labels, x, y, y_low, y_high):
        ax.errorbar(
            xi,
            yi,
            yerr=np.asarray([[yi - lo], [hi - yi]]),
            fmt=marker_map[label],
            markersize=6.2,
            color=color_map[label],
            markeredgecolor="white",
            markeredgewidth=0.5,
            capsize=2.0,
            linewidth=0.8,
            zorder=3,
        )

    offsets = {
        "Grid": (3, 5),
        "Local": (3, -11),
        "Learned": (3, 5),
        "PARAFAC": (3, 5),
        "NOMP-inspired": (-3, 6),
    }
    for label, xi, yi in zip(labels, x, y):
        dx, dy = offsets[label]
        ax.annotate(label, (xi, yi), xytext=(dx, dy), textcoords="offset points", ha="right" if label == "NOMP-inspired" else "left", fontsize=7.0)

    ax.set_xscale("log")
    ax.set_xlabel("Median CPU time per scene (ms)")
    ax.set_ylabel("Measurement NMSE (dB; lower is better)")
    ax.grid(True, which="major", color="#E5E7EB", linewidth=0.6)

    ax = axes[1]
    for label, xi, yi, ci in zip(labels, x, half_bin, half_ci):
        ax.errorbar(
            xi,
            100.0 * yi,
            yerr=100.0 * ci,
            fmt=marker_map[label],
            markersize=6.2,
            color=color_map[label],
            markeredgecolor="white",
            markeredgewidth=0.5,
            capsize=2.0,
            linewidth=0.8,
            zorder=3,
        )
    half_offsets = {
        "Grid": (3, 5),
        "Local": (3, 5),
        "Learned": (3, -11),
        "PARAFAC": (3, -11),
        "NOMP-inspired": (-3, -11),
    }
    for label, xi, yi in zip(labels, x, half_bin):
        dx, dy = half_offsets[label]
        ax.annotate(
            label,
            (xi, 100.0 * yi),
            xytext=(dx, dy),
            textcoords="offset points",
            ha="right" if label == "NOMP-inspired" else "left",
            fontsize=7.0,
        )
    ax.set_xscale("log")
    ax.set_xlabel("Median CPU time per scene (ms)")
    ax.set_ylabel("All-axis half-bin hit rate (%)")
    ax.set_ylim(45, 103)
    ax.grid(True, which="major", color="#E5E7EB", linewidth=0.6)
    axes[0].text(0.02, 0.96, "(a)", transform=axes[0].transAxes, va="top", fontweight="bold")
    axes[1].text(0.02, 0.96, "(b)", transform=axes[1].transAxes, va="top", fontweight="bold")
    save_bundle(fig, "v2_3r_pareto_flops")


def local_family_comparison() -> None:
    rows = read_path(COST_DIR / "local_family_summary.csv")
    runtime_rows = read_path(RUNTIME_DIR / "summary.csv")
    runtime_by_method = {row["method"]: float(row["median_wall_clock_ms"]) for row in runtime_rows}
    label_map = {
        "grid_fft_topL_joint_ls": "Grid",
        "axiswise_quadratic_peak_joint_ls": "3-sample interpolation",
        "one_step_fixed_support_newton_joint_ls": "One-step Newton",
        "cartesian_local_joint_ls": "Cartesian local (separable)",
    }
    rows = [row for row in rows if row["method"] in label_map]
    colors = [GRAY, GOLD, BLUE, TEAL]
    markers = ["o", "D", "^", "s"]
    fig, axes = plt.subplots(1, 2, figsize=(7.1, 2.55))
    for idx, row in enumerate(rows):
        label = label_map[row["method"]]
        runtime = runtime_by_method[row["method"]]
        nmse = float(row["mean_measurement_nmse_db"])
        nmse_low = float(row["measurement_nmse_ci95_low_db"])
        nmse_high = float(row["measurement_nmse_ci95_high_db"])
        hit = 100.0 * float(row["mean_all_axis_half_bin_hit"])
        hit_low = 100.0 * float(row["half_bin_hit_ci95_low"])
        hit_high = 100.0 * float(row["half_bin_hit_ci95_high"])
        axes[0].errorbar(runtime, nmse, yerr=[[nmse - nmse_low], [nmse_high - nmse]],
                         fmt=markers[idx], color=colors[idx], markersize=6.2,
                         markeredgecolor="white", markeredgewidth=0.5, capsize=2.0,
                         linewidth=0.8, label=label)
        axes[1].errorbar(runtime, hit, yerr=[[hit - hit_low], [hit_high - hit]],
                         fmt=markers[idx], color=colors[idx], markersize=6.2,
                         markeredgecolor="white", markeredgewidth=0.5, capsize=2.0,
                         linewidth=0.8, label=label)
    for ax in axes:
        ax.set_xscale("log")
        ax.set_xlabel("Median CPU time per scene (ms)")
        ax.grid(True, which="major", color="#E5E7EB", linewidth=0.6)
    axes[0].set_ylabel("Measurement NMSE (dB; lower is better)")
    axes[1].set_ylabel("All-axis half-bin hit rate (%)")
    axes[1].set_ylim(68, 82)
    axes[0].legend(loc="lower left")
    axes[0].text(0.02, 0.96, "(a)", transform=axes[0].transAxes,
                 va="top", fontweight="bold")
    axes[1].text(0.02, 0.96, "(b)", transform=axes[1].transAxes,
                 va="top", fontweight="bold")
    save_bundle(fig, "tsp_local_family")


def reliability_gate() -> None:
    rows = [row for row in read_path(GATE_DIR / "reliability_gate_rows.csv") if row["split"] == "test"]
    summary = read_path(GATE_DIR / "reliability_gate_test_summary.csv")
    with (GATE_DIR / "summary.json").open(encoding="utf-8") as handle:
        threshold = float(json.load(handle)["gate"]["threshold"])
    profiles = ["A", "C", "D"]

    fig, axes = plt.subplots(1, 2, figsize=(7.1, 2.55))
    residuals = [
        [float(row["residual_reduction_fraction"]) for row in rows if row["profile"] == profile]
        for profile in profiles
    ]
    box = axes[0].boxplot(
        residuals,
        tick_labels=[f"CDL-{profile}" for profile in profiles],
        patch_artist=True,
        showfliers=False,
        whis=(5, 95),
        widths=0.58,
    )
    for patch, color in zip(box["boxes"], [BLUE, TEAL, GOLD]):
        patch.set_facecolor(color)
        patch.set_alpha(0.30)
        patch.set_edgecolor(color)
    for median in box["medians"]:
        median.set_color(TEXT)
        median.set_linewidth(1.2)
    axes[0].axhline(threshold, color=RED, linestyle="--", linewidth=1.0)
    axes[0].text(
        0.98,
        0.95,
        rf"frozen $\tau_\rho={threshold:.3f}$",
        transform=axes[0].transAxes,
        ha="right",
        va="top",
        fontsize=7.1,
        color=RED,
    )
    axes[0].set_ylabel(r"Observed residual reduction $\Delta\rho$")
    axes[0].grid(axis="y", color="#E5E7EB", linewidth=0.6)

    xloc = np.arange(len(profiles), dtype=float)
    width = 0.34
    by_profile = {row["profile"]: row for row in summary}
    always = np.asarray([float(by_profile[p]["always_refine_gain_db"]) for p in profiles])
    gated = np.asarray([float(by_profile[p]["gated_refine_gain_db"]) for p in profiles])
    always_ci = np.asarray(
        [
            float(by_profile[p]["always_refine_gain_ci95_high_db"])
            - float(by_profile[p]["always_refine_gain_db"])
            for p in profiles
        ]
    )
    gated_ci = np.asarray(
        [
            float(by_profile[p]["gated_refine_gain_ci95_high_db"])
            - float(by_profile[p]["gated_refine_gain_db"])
            for p in profiles
        ]
    )
    axes[1].bar(
        xloc - width / 2,
        always,
        width,
        yerr=always_ci,
        color=TEAL,
        alpha=0.80,
        capsize=2,
        label="Always refine",
    )
    axes[1].bar(
        xloc + width / 2,
        gated,
        width,
        yerr=gated_ci,
        color=BLUE,
        alpha=0.85,
        capsize=2,
        label="Residual-gated",
    )
    for idx, profile in enumerate(profiles):
        pass_rate = 100.0 * float(by_profile[profile]["gate_pass_rate"])
        axes[1].text(
            xloc[idx] + width / 2,
            gated[idx] + gated_ci[idx] + 0.25,
            f"pass {pass_rate:.1f}%",
            ha="center",
            va="bottom",
            fontsize=6.8,
        )
    axes[1].axhline(0.0, color="#475569", linewidth=0.8)
    axes[1].set_xticks(xloc, [f"CDL-{profile}" for profile in profiles])
    axes[1].set_ylabel("Channel-NMSE gain over grid (dB)")
    axes[1].grid(axis="y", color="#E5E7EB", linewidth=0.6)
    axes[1].legend(loc="upper right")
    axes[0].text(0.02, 0.96, "(a)", transform=axes[0].transAxes, va="top", fontweight="bold")
    axes[1].text(0.02, 0.96, "(b)", transform=axes[1].transAxes, va="top", fontweight="bold")
    save_bundle(fig, "tsp_reliability_gate")


def reliability_cells() -> None:
    rows = read_path(GATE_DIR / "reliability_gate_cell_summary.csv")
    profiles = ["A", "C", "D"]
    snrs = sorted({float(row["snr_db"]) for row in rows})
    l_values = sorted({int(row["l_value"]) for row in rows})
    values = {(row["profile"], float(row["snr_db"]), int(row["l_value"])):
              float(row["gated_gain_db"]) for row in rows}
    arrays = [np.asarray([[values[(p, snr, l)] for l in l_values] for snr in snrs])
              for p in profiles]
    vmax = max(float(np.nanmax(array)) for array in arrays)
    vmin = min(float(np.nanmin(array)) for array in arrays)
    norm = mpl.colors.TwoSlopeNorm(vmin=min(vmin, -0.12), vcenter=0.0, vmax=vmax)

    fig, axes = plt.subplots(1, 3, figsize=(7.1, 2.35), sharey=True)
    image_handle = None
    for ax, profile, array in zip(axes, profiles, arrays):
        image_handle = ax.imshow(array, cmap="coolwarm", norm=norm, aspect="auto")
        ax.set_title(f"CDL-{profile}")
        ax.set_xticks(range(len(l_values)), [str(l) for l in l_values])
        ax.set_xlabel("Returned order $L$")
        for i in range(len(snrs)):
            for j in range(len(l_values)):
                value = array[i, j]
                color = "white" if abs(norm(value) - 0.5) > 0.30 else TEXT
                ax.text(j, i, f"{value:.2f}", ha="center", va="center",
                        fontsize=6.8, color=color)
    axes[0].set_yticks(range(len(snrs)), [f"{snr:g}" for snr in snrs])
    axes[0].set_ylabel("SNR (dB)")
    colorbar = fig.colorbar(image_handle, ax=axes, fraction=0.025, pad=0.025)
    colorbar.set_label("Gated channel-NMSE gain (dB)")
    save_bundle(fig, "tsp_gate_cells")


def stress_mechanism() -> None:
    rows = read_path(STRESS_DIR / "stress_test_cell_summary.csv")
    separations = sorted({float(row["separation_bins"]) for row in rows})
    dynamic_ranges = sorted({float(row["dynamic_range_db"]) for row in rows})
    grouped: dict[tuple[float, float], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(float(row["separation_bins"]), float(row["dynamic_range_db"]))].append(row)

    specs = [
        ("coarse_per_component_hit_rate", "Coarse per-component half-bin hit (%)", "Blues", 100.0),
        ("local_per_component_hit_rate", "Local per-component half-bin hit (%)", "Blues", 100.0),
        ("half_bin_improvement", "Local improvement (percentage points)", "YlGn", 100.0),
        ("gated_gain_db", "Gated channel-NMSE gain (dB)", "YlGn", 1.0),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(7.1, 4.35), sharex=True, sharey=True)
    for panel, (ax, (key, title, cmap, scale)) in enumerate(zip(axes.flat, specs)):
        if key == "half_bin_improvement":
            array = np.asarray(
                [
                    [
                        np.mean([float(row["local_per_component_hit_rate"])
                                 - float(row["coarse_per_component_hit_rate"])
                                 for row in grouped[(sep, dr)]]) * scale
                        for dr in dynamic_ranges
                    ]
                    for sep in separations
                ]
            )
        else:
            array = np.asarray(
                [
                    [np.mean([float(row[key]) for row in grouped[(sep, dr)]]) * scale
                     for dr in dynamic_ranges]
                    for sep in separations
                ]
            )
        image_handle = ax.imshow(array, cmap=cmap, aspect="auto")
        for i in range(len(separations)):
            for j in range(len(dynamic_ranges)):
                value = array[i, j]
                normalized = image_handle.norm(value)
                color = "white" if normalized > 0.62 else TEXT
                if "hit" in key or "improvement" in key:
                    label = f"{value:.0f}"
                else:
                    label = f"{value:.2f}"
                ax.text(j, i, label, ha="center", va="center", fontsize=7.0, color=color)
        ax.set_title(title)
        ax.set_xticks(range(len(dynamic_ranges)), [f"{value:g}" for value in dynamic_ranges])
        ax.set_yticks(range(len(separations)), [f"{value:g}" for value in separations])
        ax.text(0.02, 0.96, f"({chr(97 + panel)})", transform=ax.transAxes,
                va="top", fontweight="bold", color=TEXT)
    for ax in axes[1]:
        ax.set_xlabel("Pair dynamic range (dB)")
    for ax in axes[:, 0]:
        ax.set_ylabel("Pair separation (bins)")
    save_bundle(fig, "tsp_stress_mechanism")


def full_offset_support() -> None:
    radius_rows = read_path(FULL_OFFSET_DIR / "radius_summary.csv")
    edge_rows = [
        row
        for row in read_path(FULL_OFFSET_DIR / "edge_offset_summary.csv")
        if row["method"] == "cartesian_local_joint_ls"
    ]
    support_rows = [
        row
        for row in read_path(SUPPORT_DIR / "support_quality_strata.csv")
        if row["stratum_type"] == "coarse_support_quality"
    ]
    stress_rows = [
        row for row in read_path(STRESS_DIR / "stress_rows.csv") if row["split"] == "test"
    ]

    fig, axes = plt.subplots(2, 2, figsize=(7.1, 4.45))
    ax = axes[0, 0]
    radii = np.asarray([float(row["search_radius"]) for row in radius_rows])
    gains = np.asarray([float(row["mean_gain_vs_grid_db"]) for row in radius_rows])
    saturation = 100.0 * np.asarray(
        [float(row["mean_boundary_saturation_rate"]) for row in radius_rows]
    )
    ax.plot(radii, gains, color=TEAL, marker="o", linewidth=1.2, label="NMSE gain")
    ax.set_xlabel("Search radius (bins)")
    ax.set_ylabel("Gain over grid (dB)", color=TEAL)
    ax.tick_params(axis="y", colors=TEAL)
    second = ax.twinx()
    second.plot(radii, saturation, color=GOLD, marker="s", linestyle="--", linewidth=1.1)
    second.set_ylabel("Boundary selections (%)", color=GOLD)
    second.tick_params(axis="y", colors=GOLD)
    ax.grid(axis="x", color="#E5E7EB", linewidth=0.6)
    ax.set_title("Full-offset radius sweep")

    ax = axes[0, 1]
    buckets = ["[0.00,0.10)", "[0.10,0.20)", "[0.20,0.30)", "[0.30,0.40)", "[0.40,0.49]"]
    axis_styles = (("angle", BLUE, "o"), ("delay", TEAL, "s"), ("doppler", GOLD, "^"))
    for axis_name, color, marker in axis_styles:
        by_bucket = {(row["axis"], row["offset_bucket"]): row for row in edge_rows}
        values = [100.0 * float(by_bucket[(axis_name, bucket)]["half_bin_axis_hit_rate"]) for bucket in buckets]
        ax.plot(range(len(buckets)), values, color=color, marker=marker, linewidth=1.1, label=axis_name.capitalize())
    ax.set_xticks(range(len(buckets)), ["0-.1", ".1-.2", ".2-.3", ".3-.4", ".4-.49"])
    ax.set_xlabel("Absolute fractional-bin offset")
    ax.set_ylabel("Axis half-bin hit rate (%)")
    ax.set_ylim(45, 103)
    ax.grid(axis="y", color="#E5E7EB", linewidth=0.6)
    ax.legend(loc="lower left", ncols=3)
    ax.set_title("Edge-offset behavior")

    ax = axes[1, 0]
    quality = np.asarray([float(row["stratum"].split("=")[1]) for row in support_rows])
    support_gain = np.asarray([float(row["mean_local_gain_vs_grid_db"]) for row in support_rows])
    correctness = 100.0 * np.asarray([float(row["mean_candidate_axis_correctness"]) for row in support_rows])
    ax.plot(quality, support_gain, color=TEAL, marker="o", linewidth=1.2)
    ax.set_xlabel(r"Coarse support quality $q_{\rm sup}$")
    ax.set_ylabel("Gain over grid (dB)", color=TEAL)
    ax.tick_params(axis="y", colors=TEAL)
    second = ax.twinx()
    second.plot(quality, correctness, color=BLUE, marker="s", linestyle="--", linewidth=1.1)
    second.set_ylabel("Candidate-axis correctness (%)", color=BLUE)
    second.tick_params(axis="y", colors=BLUE)
    ax.grid(axis="x", color="#E5E7EB", linewidth=0.6)
    ax.set_title("Support-quality stratification")

    ax = axes[1, 1]
    theory_groups = (
        ("Not certified", [row for row in stress_rows if float(row["theory_condition_fraction"]) == 0.0]),
        ("Certified", [row for row in stress_rows if float(row["theory_condition_fraction"]) > 0.0]),
    )
    group_gain = [
        np.mean([float(row["local_gain_vs_grid_db"]) for row in rows])
        for _, rows in theory_groups
    ]
    group_correctness = [
        100.0 * np.mean([float(row["candidate_axis_correctness"]) for row in rows])
        for _, rows in theory_groups
    ]
    positions = np.arange(2)
    bars = ax.bar(positions, group_gain, color=[GRAY, TEAL], alpha=0.82, width=0.58)
    ax.set_xticks(positions, [label for label, _ in theory_groups])
    ax.set_ylabel("Gain over grid (dB)", color=TEAL)
    ax.tick_params(axis="y", colors=TEAL)
    ax.set_ylim(0, 8.2)
    second = ax.twinx()
    second.plot(positions, group_correctness, color=BLUE, marker="s", linewidth=1.2)
    second.set_ylabel("Candidate-axis correctness (%)", color=BLUE)
    second.tick_params(axis="y", colors=BLUE)
    second.set_ylim(66, 74)
    for bar, value in zip(bars, group_gain):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 0.15, f"{value:.2f}",
                ha="center", va="bottom", fontsize=7.0)
    ax.grid(axis="y", color="#E5E7EB", linewidth=0.6)
    ax.set_title("Fourier-coherence phase evidence")
    for index, ax in enumerate(axes.flat):
        ax.text(0.02, 0.96, f"({chr(97 + index)})", transform=ax.transAxes,
                va="top", fontweight="bold")
    fig.tight_layout()
    save_bundle(fig, "tsp_full_offset_support")


def gate_reliability_transfer() -> None:
    observations = [
        row
        for row in read_path(GATE_ANALYSIS_DIR / "gate_observations.csv")
        if row["geometry"] == "CDL"
    ]
    reliability = [
        row
        for row in read_path(GATE_ANALYSIS_DIR / "reliability_curve.csv")
        if row["geometry"] == "CDL" and row["group"] == "all"
    ]
    transfer = read_path(TRANSFER_DIR / "transfer_summary.csv")
    with (GATE_DIR / "summary.json").open(encoding="utf-8") as handle:
        threshold = float(json.load(handle)["gate"]["threshold"])

    fig, axes = plt.subplots(1, 3, figsize=(7.1, 2.45))
    ax = axes[0]
    profile_style = (("A", BLUE), ("C", TEAL), ("D", GOLD))
    for profile, color in profile_style:
        selected = [row for row in observations if row["group"] == profile][::8]
        ax.scatter(
            [float(row["residual_reduction_fraction"]) for row in selected],
            [float(row["local_gain_vs_grid_db"]) for row in selected],
            s=5,
            color=color,
            alpha=0.28,
            linewidths=0,
            label=f"CDL-{profile}",
        )
    ax.axvline(threshold, color=RED, linestyle="--", linewidth=0.9)
    ax.axhline(0.0, color=GRAY, linewidth=0.7)
    ax.set_xlabel(r"Residual reduction $\Delta\rho$")
    ax.set_ylabel("Clean NMSE gain (dB)")
    ax.set_xlim(-0.03, 0.13)
    ax.set_ylim(-12, 27)
    ax.legend(loc="upper left", markerscale=2.0)
    ax.grid(color="#E5E7EB", linewidth=0.5)

    ax = axes[1]
    predicted = [float(row["mean_predicted_probability"]) for row in reliability]
    observed = [float(row["observed_positive_rate"]) for row in reliability]
    ax.plot([0, 1], [0, 1], color=GRAY, linestyle=":", linewidth=1.0)
    ax.plot(predicted, observed, color=BLUE, marker="o", linewidth=1.2)
    ax.set_xlabel("Predicted positive-gain probability")
    ax.set_ylabel("Observed positive-gain rate")
    ax.set_xlim(-0.03, 1.03)
    ax.set_ylim(-0.03, 1.03)
    ax.grid(color="#E5E7EB", linewidth=0.5)

    ax = axes[2]
    calibration_names = sorted({row["calibration_geometry"] for row in transfer})
    test_names = sorted({row["test_geometry"] for row in transfer})
    values = np.asarray(
        [
            [
                float(next(row for row in transfer if row["calibration_geometry"] == calibration and row["test_geometry"] == test)["gated_gain_db"])
                for test in test_names
            ]
            for calibration in calibration_names
        ]
    )
    image_handle = ax.imshow(values, cmap="YlGn", aspect="auto", vmin=0.0)
    for row_index in range(len(calibration_names)):
        for column_index in range(len(test_names)):
            ax.text(column_index, row_index, f"{values[row_index, column_index]:.2f}",
                    ha="center", va="center", fontsize=7.2)
    short = {"CDL": "CDL", "Synthetic full-offset": "Full offset"}
    ax.set_xticks(range(len(test_names)), [short[name] for name in test_names])
    ax.set_yticks(range(len(calibration_names)), [short[name] for name in calibration_names])
    ax.set_xlabel("Test geometry")
    ax.set_ylabel("Threshold calibration")
    colorbar = fig.colorbar(image_handle, ax=ax, fraction=0.046, pad=0.03)
    colorbar.set_label("Gated NMSE gain (dB)")
    for index, ax in enumerate(axes):
        ax.text(0.02, 0.96, f"({chr(97 + index)})", transform=ax.transAxes,
                va="top", fontweight="bold")
    fig.tight_layout()
    save_bundle(fig, "tsp_gate_reliability_transfer")


def mean_ci(values: np.ndarray) -> tuple[float, float]:
    mean = float(values.mean())
    if len(values) < 2:
        return mean, 0.0
    return mean, 1.96 * float(values.std(ddof=1)) / math.sqrt(len(values))


def wordlength() -> None:
    rows = read_rows("fixedpoint_sweep.csv")
    grouped: dict[tuple[str, int], list[float]] = defaultdict(list)
    for row in rows:
        grouped[(row["domain"], int(row["W"]))].append(float(row["delta_vs_float_db"]))

    domains = [
        ("local3d", "Local 3-D ($128\\times16\\times32$)", BLUE, "o", "-"),
        ("cdl2d", "CDL geometry ($64\\times4$)", RED, "s", "--"),
    ]
    fig, ax = plt.subplots(figsize=(3.5, 2.55))
    for key, label, color, marker, linestyle in domains:
        ws = sorted(w for domain, w in grouped if domain == key)
        means, cis = [], []
        for w in ws:
            mean, ci = mean_ci(np.asarray(grouped[(key, w)]))
            means.append(max(mean, 0.01))
            cis.append(ci)
        lower = np.maximum(np.asarray(means) - np.asarray(cis), 0.01)
        upper = np.asarray(means) + np.asarray(cis)
        ax.plot(ws, means, color=color, marker=marker, linestyle=linestyle, linewidth=1.2, markersize=4, label=label)
        ax.fill_between(ws, lower, upper, color=color, alpha=0.13, linewidth=0)

    ax.axhline(0.5, color="#475569", linestyle=":", linewidth=1.0)
    ax.text(17.9, 0.55, "0.5 dB tolerance", ha="right", va="bottom", fontsize=7.0)
    ax.set_yscale("log")
    ax.set_xticks([6, 8, 10, 12, 14, 16, 18])
    ax.set_xlabel("Datapath word length $W$ (bits, $F=W-2$)")
    ax.set_ylabel("NMSE loss vs. floating-point kernel (dB)")
    ax.set_ylim(0.008, 30)
    ax.grid(axis="y", which="major", color="#E5E7EB", linewidth=0.6)
    ax.legend(loc="upper right")
    save_bundle(fig, "v2_3r_nmse_vs_wordlength")


def main() -> None:
    apply_style()
    system_model()
    method_flow()
    learning_marginal()
    local_family_comparison()
    runtime_comparison()
    reliability_gate()
    reliability_cells()
    stress_mechanism()
    full_offset_support()
    gate_reliability_transfer()
    wordlength()


if __name__ == "__main__":
    main()
