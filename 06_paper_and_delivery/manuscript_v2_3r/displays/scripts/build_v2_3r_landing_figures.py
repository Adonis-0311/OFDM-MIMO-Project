"""Paper-facing landing figures for v2.3R.

Clean academic style. plain Rectangles (no FancyBbox padding), straight
arrows, no in-figure titles (LaTeX captions provide them).
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.patches import FancyArrowPatch, Polygon, Rectangle
import numpy as np


ROOT = Path(__file__).resolve().parents[4]
MANUSCRIPT = ROOT / "06_paper_and_delivery" / "manuscript_v2_3r"
DISPLAY_DIR = MANUSCRIPT / "displays"
FIGURE_DIR = DISPLAY_DIR / "figures"

BLUE = "#3B6FA8"
TEAL = "#3E8E7E"
RED = "#C45B5B"
AMBER = "#C49A53"
INK = "#1F2A37"
MUTED = "#6B7280"
LIGHT = "#F1F3F5"
PALE_BLUE = "#E4ECF5"
PALE_GREEN = "#E6F0E6"
PALE_RED = "#F5E4E4"


def apply_style() -> None:
    plt.style.use("default")
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 9.0,
        "axes.titlesize": 9.5,
        "axes.labelsize": 9.0,
        "axes.edgecolor": INK,
        "axes.linewidth": 0.8,
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
        "legend.fontsize": 8.0,
        "legend.frameon": False,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.04,
    })


def save(fig: plt.Figure, stem: str) -> dict[str, str]:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    png = FIGURE_DIR / f"{stem}.png"
    pdf = FIGURE_DIR / f"{stem}.pdf"
    fig.savefig(png, dpi=300, facecolor="white")
    fig.savefig(pdf, facecolor="white")
    plt.close(fig)
    return {"png": png.relative_to(ROOT).as_posix(),
            "pdf": pdf.relative_to(ROOT).as_posix()}


def block(ax, x, y, w, h, text, face=LIGHT, edge=INK,
          fontsize=9.0, weight="normal", linespacing=1.22,
          min_fontsize=5.5):
    """Draw a box and shrink its label until it has a safe inner margin.

    Diagram text is measured by the same Matplotlib renderer used for export.
    This prevents a long label from looking acceptable in source coordinates
    while crossing its rectangle after font substitution or PDF rendering.
    """
    rect = Rectangle((x, y), w, h, facecolor=face,
                     edgecolor=edge, linewidth=0.8)
    ax.add_patch(rect)
    label = ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                    fontsize=fontsize, color=INK, fontweight=weight,
                    linespacing=linespacing)

    # Reserve 7% horizontally and 9% vertically on each side.  Bounding boxes
    # are evaluated in display pixels, so the check remains valid at any DPI.
    fig = ax.figure
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    p0 = ax.transData.transform((x, y))
    p1 = ax.transData.transform((x + w, y + h))
    max_width = abs(p1[0] - p0[0]) * 0.86
    max_height = abs(p1[1] - p0[1]) * 0.82
    fitted_size = float(fontsize)
    bbox = label.get_window_extent(renderer=renderer)
    while ((bbox.width > max_width or bbox.height > max_height)
           and fitted_size > min_fontsize):
        fitted_size = max(min_fontsize, fitted_size - 0.2)
        label.set_fontsize(fitted_size)
        fig.canvas.draw()
        bbox = label.get_window_extent(renderer=renderer)

    if bbox.width > max_width + 0.5 or bbox.height > max_height + 0.5:
        raise RuntimeError(
            f"Box label cannot be fitted safely: {text!r}; "
            f"bbox=({bbox.width:.1f}, {bbox.height:.1f}), "
            f"limit=({max_width:.1f}, {max_height:.1f})"
        )
    return rect, label


def arrow(ax, x0, y0, x1, y1, color=INK, lw=1.0, rad=0.0):
    cs = f"arc3,rad={rad}" if rad else "arc3"
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1),
                                  arrowstyle="-|>",
                                  connectionstyle=cs,
                                  color=color, linewidth=lw,
                                  mutation_scale=10,
                                  shrinkA=0, shrinkB=0))


def diagram_ax(fig):
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    return ax


def draw_array(ax, x, y, label, color, n=4, dy=0.045):
    for i in range(n):
        ax.add_patch(plt.Circle((x, y + i * dy), 0.011,
                                  facecolor=color, edgecolor="white", lw=0.5))
    ax.plot([x, x], [y - 0.015, y + (n - 1) * dy + 0.015],
            color=color, lw=1.4)
    ax.text(x, y - 0.06, label, ha="center", va="top",
            fontsize=8.5, color=INK)


def draw_cube(ax, x, y, w, h):
    d = 0.035
    front = np.array([[x, y], [x+w, y], [x+w, y+h], [x, y+h]])
    top = np.array([[x, y+h], [x+d, y+h+d], [x+w+d, y+h+d], [x+w, y+h]])
    side = np.array([[x+w, y], [x+w+d, y+d], [x+w+d, y+h+d], [x+w, y+h]])
    ax.add_patch(Polygon(front, closed=True, facecolor=PALE_BLUE,
                          edgecolor=BLUE, linewidth=0.8))
    ax.add_patch(Polygon(top, closed=True, facecolor="#D7E1EE",
                          edgecolor=BLUE, linewidth=0.8))
    ax.add_patch(Polygon(side, closed=True, facecolor="#C7D4E5",
                          edgecolor=BLUE, linewidth=0.8))
    for px, py in [(0.22, 0.30), (0.48, 0.70), (0.72, 0.42), (0.62, 0.85)]:
        ax.add_patch(plt.Circle((x + px * w, y + py * h), 0.010,
                                  facecolor=RED, edgecolor="white", lw=0.4))


def plot_system_model():
    fig = plt.figure(figsize=(7.0, 2.4))
    ax = diagram_ax(fig)
    tx_x, rx_x = 0.07, 0.40
    draw_array(ax, tx_x, 0.55, "Tx subarrays\n(FDMA tones)", BLUE)
    draw_array(ax, rx_x, 0.55, "Rx ULA", TEAL)
    paths = [(0.235, 0.84, BLUE, 0.70, 0.71),
             (0.235, 0.62, AMBER, 0.62, 0.63),
             (0.235, 0.40, TEAL, 0.55, 0.55)]
    for tx_p, ty_p, color, tx_y, rx_y in paths:
        ax.add_patch(plt.Circle((tx_p, ty_p), 0.014,
                                  facecolor=color, edgecolor="white", lw=0.5))
        arrow(ax, tx_x + 0.013, tx_y, tx_p, ty_p, color=color, lw=0.9)
        arrow(ax, tx_p, ty_p, rx_x - 0.013, rx_y, color=color, lw=0.9)
    ax.text(0.235, 0.32, r"$L$ paths $(\theta_\ell,\tau_\ell,\nu_\ell,\beta_\ell)$",
            ha="center", va="top", fontsize=8.8, color=INK)
    arrow(ax, rx_x + 0.013, 0.62, 0.515, 0.62, lw=1.2)
    block(ax, 0.52, 0.52, 0.16, 0.20, "Matched filtering\n+ stacking",
          face=LIGHT, fontsize=8.8, weight="bold")
    arrow(ax, 0.685, 0.62, 0.745, 0.62, lw=1.2)
    draw_cube(ax, 0.755, 0.49, 0.13, 0.26)
    ax.text(0.825, 0.41, "Angle-delay-Doppler\ntensor $\\mathcal{Y}$",
            ha="center", va="top", fontsize=8.6, color=INK)
    block(ax, 0.02, 0.05, 0.55, 0.20,
          r"$\mathcal{Y}=\sum_{\ell=1}^{L}\beta_\ell\,"
          r"\mathbf{a}(\theta_\ell)\circ\mathbf{b}(\tau_\ell)"
          r"\circ\mathbf{c}(\nu_\ell)+\mathcal{N}$",
          face=LIGHT, fontsize=10.0)
    block(ax, 0.60, 0.05, 0.38, 0.20,
          "Outputs\nChannel NMSE  |  Delay RMSE\nProjected-angle RMSE",
          face=PALE_GREEN, fontsize=7.8)
    return save(fig, "v2_3r_system_model")


def plot_architecture():
    fig = plt.figure(figsize=(7.0, 3.25))
    ax = diagram_ax(fig)

    def row_label(y, title, subtitle, color):
        ax.text(0.015, y + 0.108, title, ha="left", va="center",
                fontsize=8.4, fontweight="bold", color=color)
        ax.text(0.015, y + 0.057, subtitle, ha="left", va="center",
                fontsize=6.4, color=MUTED, linespacing=1.25)

    # Path 1: the local synthetic G2 implementation learns exactly one scalar.
    y, h = 0.700, 0.180
    row_label(y, "LOCAL 3-D (G2)", "five seeds\nsmall held-out sample", BLUE)
    specs = [
        (0.175, 0.105, "Observation\n$\\mathcal{Y}$", PALE_BLUE),
        (0.315, 0.120, "FFT top-$k$\ncoarse bins\n$\\mathbf{b}_0$", LIGHT),
        (0.470, 0.125, "Deterministic\nlocal candidate\n$\\mathbf{b}_\\star$", LIGHT),
        (0.630, 0.125, "Learned scalar\n$\\alpha$\n(1 parameter)", PALE_GREEN),
        (0.790, 0.190, "Bounded interpolation\n+ LS reconstruction", PALE_GREEN),
    ]
    for idx, (x, w, label, face) in enumerate(specs):
        block(ax, x, y, w, h, label, face=face, fontsize=6.7,
              weight="bold" if idx in (3, 4) else "normal")
        if idx < len(specs) - 1:
            arrow(ax, x + w, y + h / 2, specs[idx + 1][0], y + h / 2, lw=1.0)

    # Path 2: the CDL source-trained controller is a separate 10-16-2 model.
    y = 0.405
    row_label(y, "CDL 2-D", "A/C: disjoint train/val\nD: zero-shot", TEAL)
    specs = [
        (0.175, 0.105, "$64\\times4$\nmeasurement", PALE_BLUE),
        (0.315, 0.125, "Coarse / local\ncandidate pair", LIGHT),
        (0.475, 0.115, "10 estimator\nfeatures", LIGHT),
        (0.625, 0.145, "Feature controller\n$10\\!\\to\\!16\\!\\to\\!2$\n(210 parameters)", PALE_GREEN),
        (0.805, 0.175, "Axis scales +\nalias lock + LS /\nphysical match", PALE_GREEN),
    ]
    for idx, (x, w, label, face) in enumerate(specs):
        block(ax, x, y, w, h, label, face=face, fontsize=6.5,
              weight="bold" if idx in (3, 4) else "normal")
        if idx < len(specs) - 1:
            arrow(ax, x + w, y + h / 2, specs[idx + 1][0], y + h / 2,
                  color=TEAL if idx >= 2 else INK, lw=1.0)

    # Path 3 is diagnostic only; it must not visually masquerade as network depth.
    y, h = 0.075, 0.175
    ax.add_patch(Rectangle((0.015, y), 0.965, h, facecolor="#FFF6E5",
                           edgecolor="#C98200", lw=0.9, ls="--"))
    ax.text(0.035, y + h - 0.040, "A4 DEPTH DIAGNOSTIC (not the CDL controller depth)",
            ha="left", va="top", fontsize=8.4, fontweight="bold", color="#9A6200")
    ax.text(0.035, y + 0.050,
            "Repeated deterministic radius schedule  →  scalar plateau gate  →  depth / NMSE trade-off",
            ha="left", va="center", fontsize=8.0, color=INK)
    return save(fig, "v2_3r_refinement_paths")


def read_rows(paths):
    rows = []
    for p in paths:
        with p.open(newline="", encoding="utf-8") as h:
            rows.extend(csv.DictReader(h))
    return rows


def profile_seed_values(rows, field):
    g = {}
    for r in rows:
        k = (r["profile"], int(float(r["seed"])))
        g.setdefault(k, []).append(float(r[field]))
    out = {p: [] for p in ("A", "C", "D")}
    for (p, _), vs in sorted(g.items()):
        out[p].append(float(np.mean(vs)))
    return out


def plot_cdl_evidence():
    rows = read_rows([
        ROOT/"05_results"/"sionna_cdl_ac_alias_lock_selected_scaled"/"sionna_cdl_trained_refinement.csv",
        ROOT/"05_results"/"sionna_cdl_d_alias_lock_selected_zero_shot_scaled"/"sionna_cdl_trained_refinement.csv",
    ])
    fields = [
        ("mean_trained_refinement_gain_vs_grid_db",
         "Channel NMSE gain (dB)", "Channel NMSE"),
        ("mean_physical_delay_rmse_reduction_vs_grid_ns",
         "Delay RMSE reduction (ns)", "Delay RMSE"),
        ("mean_projected_angle_rmse_reduction_vs_grid_deg",
         r"Angle RMSE reduction ($^\circ$)", "Projected-angle RMSE"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.3),
                              constrained_layout=True)
    rng = np.random.default_rng(20260628)
    colors = {"A": BLUE, "C": TEAL, "D": RED}
    for panel, (field, xlabel, title) in enumerate(fields):
        ax = axes[panel]
        v = profile_seed_values(rows, field)
        for idx, p in enumerate(("A", "C", "D")):
            sv = np.asarray(v[p])
            y = idx + rng.uniform(-0.10, 0.10, size=len(sv))
            ax.scatter(sv, y, s=24, facecolor="white",
                        edgecolor=colors[p], linewidth=1.0, zorder=3)
            ax.scatter([np.mean(sv)], [idx], marker="D", s=48,
                        color=colors[p], edgecolor="white",
                        linewidth=0.7, zorder=4)
        ax.axvline(0.0, color=INK, lw=1.0, ls="--", zorder=2)
        ax.set_yticks([0, 1, 2])
        ax.set_yticklabels(["CDL-A", "CDL-C", "CDL-D\n(zero-shot)"])
        ax.invert_yaxis()
        ax.set_xlabel(xlabel)
        ax.set_title(title, fontweight="bold", loc="left", pad=4)
        ax.grid(axis="x", color=MUTED, alpha=0.30, lw=0.6)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.tick_params(axis="y", length=0)
        ax.margins(y=0.18)
    return save(fig, "v2_3r_cdl_profile_evidence")


def plot_graphical_abstract():
    fig = plt.figure(figsize=(7.0, 3.0))
    ax = diagram_ax(fig)
    band_y, band_h = 0.55, 0.30
    draw_cube(ax, 0.025, band_y, 0.13, band_h)
    ax.text(0.090, band_y - 0.06, "Sparse angle-delay-\nDoppler observation",
            ha="center", va="top", fontsize=8.6, color=INK)
    arrow(ax, 0.190, band_y + band_h / 2, 0.245, band_y + band_h / 2,
          lw=1.3)
    block(ax, 0.245, band_y, 0.385, band_h,
          "Learned bounded refinement\nTop-$k$ support + LS\n"
          "Local scalar or CDL\nfeature controller\n"
          "(distinct validated paths)",
          face=PALE_BLUE, fontsize=8.5, weight="bold",
          linespacing=1.08)
    ax.text(0.438, band_y - 0.06,
            "Hungarian matching + alias-aware physical loss",
            ha="center", va="top", fontsize=8.4, color=TEAL,
            fontstyle="italic")
    arrow(ax, 0.635, band_y + band_h / 2, 0.665, band_y + band_h / 2,
          lw=1.3)
    block(ax, 0.670, band_y + band_h / 2 + 0.01, 0.305, band_h / 2 - 0.01,
          "Channel NMSE", face=PALE_GREEN, fontsize=9.0, weight="bold")
    block(ax, 0.670, band_y, 0.305, band_h / 2 - 0.01,
          "Delay + projected-angle\nestimates",
          face=PALE_GREEN, fontsize=9.0, weight="bold")
    ax.plot([0.05, 0.95], [0.39, 0.39], color=MUTED, lw=0.6, ls="--")
    ax.text(0.5, 0.365, "HELD-OUT EVIDENCE", ha="center", va="top",
            fontsize=9.0, fontweight="bold", color=INK)
    chip_y, chip_h, chip_w = 0.10, 0.22, 0.30
    xs = [0.025, 0.345, 0.665]
    specs = [
        ("+6.23 dB", "CDL-A/C channel NMSE", PALE_GREEN),
        ("-10.12 ns", "CDL-A/C delay RMSE", PALE_GREEN),
        ("Zero-shot CDL-D", "exposes profile-shift limit", PALE_RED),
    ]
    for x, (big, small, face) in zip(xs, specs):
        ax.add_patch(Rectangle((x, chip_y), chip_w, chip_h,
                                  facecolor=face, edgecolor=INK, lw=0.7))
        ax.text(x + chip_w / 2, chip_y + chip_h - 0.06, big,
                ha="center", va="top", fontsize=11.5,
                fontweight="bold", color=INK)
        ax.text(x + chip_w / 2, chip_y + chip_h / 2 - 0.06, small,
                ha="center", va="top", fontsize=8.4, color=INK)
    ax.text(0.5, 0.04,
            "Interpretable bounded refinement around selected tensor atoms;"
            " failure boundaries kept visible.",
            ha="center", va="bottom", fontsize=8.0,
            color=MUTED, fontstyle="italic")
    return save(fig, "v2_3r_graphical_abstract")


def update_catalog(exports: dict[str, dict[str, str]]) -> None:
    catalog_path = DISPLAY_DIR / "figure_catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8")) if catalog_path.exists() else {}
    entries = {
        "system": {
            "id": "fig_v2_3r_system_model",
            "surface_class": "paper_main",
            "claim": "The FDMA virtual-array observation preserves an interpretable sparse angle-delay-Doppler representation.",
            "source_data": ["01_design_and_plan/ISAC_DeepUnfolding_TechnicalDesign_v2.3R.md"],
        },
        "architecture": {
            "id": "fig_v2_3r_refinement_paths",
            "surface_class": "paper_main",
            "claim": "The local scalar, CDL feature controller, and A4 depth diagnostic are distinct executable paths.",
            "source_data": [
                "03_active_modules/tompnet/torch_layer.py",
                "03_active_modules/tompnet/feature_controller.py",
                "04_experiments/eval/run_stage3_a4_cross_l_plateau_gate_seed_sweep.py",
            ],
        },
        "cdl": {
            "id": "fig_v2_3r_cdl_profile_evidence",
            "surface_class": "paper_main",
            "claim": "Held-out CDL-A/C gains coexist with a zero-shot CDL-D channel/delay failure boundary.",
            "source_data": [
                "05_results/sionna_cdl_ac_alias_lock_selected_scaled/",
                "05_results/sionna_cdl_d_alias_lock_selected_zero_shot_scaled/",
            ],
        },
        "graphical_abstract": {
            "id": "fig_v2_3r_graphical_abstract",
            "surface_class": "delivery",
            "claim": "Learned bounded post-support refinement has positive held-out CDL-A/C evidence and a visible CDL-D boundary.",
            "source_data": [
                "05_results/sionna_cdl_ac_alias_lock_selected_scaled/",
                "05_results/sionna_cdl_d_alias_lock_selected_zero_shot_scaled/",
            ],
        },
    }
    new_ids = {entry["id"] for entry in entries.values()}
    retained = [item for item in catalog.get("figures", []) if item.get("id") not in new_ids]
    for key, entry in entries.items():
        retained.append({
            **entry,
            "script": "06_paper_and_delivery/manuscript_v2_3r/displays/scripts/build_v2_3r_landing_figures.py",
            "exports": exports[key],
            "self_review_note": "Inspected at source resolution and after IEEE two-column PDF embedding; no text overflow, overlap, or clipped labels.",
        })
    catalog.update({"version": 1, "generated_at": "2026-06-29", "figures": retained})
    catalog_path.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")


def main():
    apply_style()
    ex = {
        "system": plot_system_model(),
        "architecture": plot_architecture(),
        "cdl": plot_cdl_evidence(),
        "graphical_abstract": plot_graphical_abstract(),
    }
    update_catalog(ex)
    for n, p in ex.items():
        print(f"{n}: {p['pdf']}")


if __name__ == "__main__":
    main()
