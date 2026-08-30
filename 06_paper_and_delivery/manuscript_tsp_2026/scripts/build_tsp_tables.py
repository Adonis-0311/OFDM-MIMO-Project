"""Generate compact LaTeX evidence tables from registered TSP CSV artifacts."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[3]
MANUSCRIPT = Path(__file__).resolve().parents[1]
OUT = MANUSCRIPT / "tables"
GATE_DIR = ROOT / "05_results" / "tsp_reliability_gate_round2_paper"
COST_DIR = ROOT / "05_results" / "tsp_controlled_local_family_paper"
STRESS_DIR = ROOT / "05_results" / "tsp_candan_stress_zeta_audit_paper"
STRESS_LEGACY_DIR = ROOT / "05_results" / "tsp_separation_nearfar_metrics_v2_paper"
SEPARABLE_DIR = ROOT / "05_results" / "tsp_separable_local_benchmark_paper"
RUNTIME_DIR = ROOT / "05_results" / "tsp_unified_runtime_paper"
FULL_OFFSET_DIR = ROOT / "05_results" / "tsp_full_offset_sweep_paper"
TRANSFER_DIR = ROOT / "05_results" / "tsp_cross_geometry_threshold_transfer_paper"
BOOTSTRAP_DIR = ROOT / "05_results" / "tsp_seed_cluster_bootstrap_paper"
GATE_ANALYSIS_DIR = ROOT / "05_results" / "tsp_gate_reliability_curve_paper"
SUPPORT_DIR = ROOT / "05_results" / "tsp_support_quality_stratification_paper"
CANDAN_CDL_DIR = ROOT / "05_results" / "tsp_candan_cdl_audit_paper"
ROUTE_DIR = ROOT / "05_results" / "tsp_candan_route_audit_paper"
BOUNDARY_DIR = ROOT / "05_results" / "tsp_fifth_round_boundary_audit_paper"
PROTOCOL_DIR = ROOT / "05_results" / "tsp_candan_gate_protocol_seventh_round"
PROJECTION_RUNTIME_DIR = ROOT / "05_results" / "tsp_projection_gate_runtime_seventh_round"
PHYSICAL_DIR = ROOT / "05_results" / "tsp_candan_physical_zeta_audit_paper"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def pct(value: str, digits: int = 1) -> str:
    bounded = min(max(float(value), 0.0), 1.0)
    return f"{100.0 * bounded:.{digits}f}"


def write(name: str, lines: list[str]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text("\n".join(lines) + "\n", encoding="utf-8")


def local_family() -> None:
    rows = read_rows(COST_DIR / "local_family_summary.csv")
    labels = {
        "grid_fft_topL_joint_ls": "Grid FFT top-$L$",
        "axiswise_quadratic_peak_joint_ls": "Quadratic power three-sample",
        "axiswise_candan_joint_ls": "Candan complex three-sample",
        "one_step_fixed_support_newton_joint_ls": "One-step fixed-support Newton",
        "cartesian_local_joint_ls": "Cartesian local",
    }
    lines = [
        r"\begin{table*}[!ht]",
        r"\centering",
        r"\caption{Controlled local-family results on 1200 common test scenes. Intervals are Student-$t$ 95\% intervals over five seed means. Improved denotes the fraction of scenes whose clean-channel NMSE is lower than that of the grid estimate.}",
        r"\label{tab:supp_local_family}",
        r"\scriptsize",
        r"\setlength{\tabcolsep}{3.0pt}",
        r"\begin{tabular}{lcccc}",
        r"\toprule",
        r"Method & NMSE [95\%] (dB) & Gain (dB) & Half-bin [95\%] & Improved \\",
        r"\midrule",
    ]
    for row in rows:
        if row["method"] not in labels:
            continue
        lines.append(
            f"{labels[row['method']]} & "
            f"${float(row['mean_measurement_nmse_db']):.2f}\\,"
            f"[{float(row['measurement_nmse_ci95_low_db']):.2f},{float(row['measurement_nmse_ci95_high_db']):.2f}]$ & "
            f"{float(row['mean_gain_vs_grid_db']):.2f} & "
            f"${pct(row['mean_all_axis_half_bin_hit'])}\\,"
            f"[{pct(row['half_bin_hit_ci95_low'])},{pct(row['half_bin_hit_ci95_high'])}]\\%$ & "
            f"{'--' if row['method'] == 'grid_fft_topL_joint_ls' else pct(1.0 - float(row['harmful_update_rate'])) + r'\%'} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table*}"])
    write("tsp_local_family_table.tex", lines)


def gate_cells() -> None:
    rows = read_rows(GATE_DIR / "reliability_gate_cell_summary.csv")
    lines = []
    for profile in ("A", "C", "D"):
        profile_rows = [row for row in rows if row["profile"] == profile]
        lines.extend(
            [
                r"\begin{table}[!ht]",
                r"\centering",
                r"\scriptsize",
                r"\setlength{\tabcolsep}{2.5pt}",
                (
                    rf"\caption{{Frozen-gate results for CDL-{profile} across all SNR--$L$ cells. "
                    r"Gain intervals use five seed means; counts are TP/FN/TN/FP.}"
                ),
                r"\label{tab:supp_gate_cells}" if profile == "A" else "",
                r"\begin{tabular}{cclclcc}",
                r"\toprule",
                r"SNR & $L$ & Gain [95\%] (dB) & Pass & TP/FN/TN/FP & Delay G/R & Spatial G/R \\",
                r"\midrule",
            ]
        )
        for row in profile_rows:
            gain = (
                f"${float(row['gated_gain_db']):.2f}\\,"
                f"[{float(row['gated_gain_ci95_low_db']):.2f},{float(row['gated_gain_ci95_high_db']):.2f}]$"
            )
            counts = "/".join(
                row[key]
                for key in ("true_positive_count", "false_negative_count", "true_negative_count", "false_positive_count")
            )
            lines.append(
                f"{float(row['snr_db']):.0f} & {row['l_value']} & {gain} & "
                f"{pct(row['gate_pass_rate'])}\\% & {counts} & "
                f"{float(row['grid_delay_rmse_bins']):.2f}/{float(row['gated_delay_rmse_bins']):.2f} & "
                f"{float(row['grid_spatial_frequency_rmse_bins']):.2f}/{float(row['gated_spatial_frequency_rmse_bins']):.2f} \\\\"
            )
        lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}", ""])
    write("tsp_gate_cells_table.tex", lines)


def gate_loso() -> None:
    rows = read_rows(GATE_DIR / "reliability_gate_validation_loso.csv")
    lines = [
        r"\begin{table}[!ht]",
        r"\centering",
        r"\caption{Leave-one-validation-seed-out gate stability.}",
        r"\label{tab:supp_gate_loso}",
        r"\footnotesize",
        r"\begin{tabular}{ccccc}",
        r"\toprule",
        r"Held-out seed & Threshold & Pass & Recall & Rejection \\",
        r"\midrule",
    ]
    for row in rows:
        lines.append(
            f"{row['held_out_seed']} & {float(row['threshold']):.4f} & "
            f"{pct(row['held_out_pass_rate'])}\\% & {pct(row['held_out_positive_recall'])}\\% & "
            f"{pct(row['held_out_negative_rejection'])}\\% \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    write("tsp_gate_loso_table.tex", lines)


def stress_cells() -> None:
    path = STRESS_DIR / "candan_48cell_summary.csv"
    if not path.exists():
        return
    rows = read_rows(path)
    lines = []
    for separation in (0.25, 0.50, 1.00, 2.00):
        separation_rows = [row for row in rows if float(row["separation_bins"]) == separation]
        lines.extend(
            [
                r"\begin{table}[!ht]",
                r"\centering",
                r"\scriptsize",
                r"\setlength{\tabcolsep}{2.5pt}",
                (
                    rf"\caption{{Controlled near--far stress results at {separation:.2f}-bin separation. "
                    r"Intervals use five seed means.}"
                ),
                r"\label{tab:supp_stress_cells}" if separation == 0.25 else "",
                r"\begin{tabular}{cccrrrrr}",
                r"\toprule",
                r"DR & SNR & Gain [95\%] & Per-comp. & Pair & Strict & Strong & Weak \\",
                r"(dB) & (dB) & (dB) & (dB) & (\%) & (\%) & (\%) & (\%) \\",
                r"\midrule",
            ]
        )
        for row in separation_rows:
            gated = (
                f"${float(row['mean_candan_gain_vs_grid_db']):.2f}\\,"
                f"[{float(row['candan_gain_vs_grid_db_ci95_low']):.2f},{float(row['candan_gain_vs_grid_db_ci95_high']):.2f}]$"
            )
            lines.append(
                f"{float(row['dynamic_range_db']):.0f} & {float(row['snr_db']):.0f} & "
                f"{gated} & {pct(row['mean_candan_per_component_hit'])} & "
                f"{pct(row['mean_candan_designated_pair_assignment'])} & "
                f"{pct(row['mean_candan_strict_recovery'])} & "
                f"{pct(row['mean_candan_strong_hit'])} & "
                f"{pct(row['mean_candan_weak_hit'])} \\\\"
            )
        lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}", ""])
    write("tsp_stress_cells_table.tex", lines)


def stress_cells_long() -> None:
    rows = read_rows(STRESS_DIR / "candan_48cell_summary.csv")
    heading = [r"\toprule",
               r"Sep. & DR & SNR & Gain [95\%] & Per-comp. & Pair & Strict & Strong/weak \\",
               r"(bin) & (dB) & (dB) & (dB) & (\%) & (\%) & (\%) & (\%/\%) \\",
               r"\midrule"]
    body = []
    for row in rows:
        gain = (f"${float(row['mean_candan_gain_vs_grid_db']):.2f}\\,"
                f"[{float(row['candan_gain_vs_grid_db_ci95_low']):.2f},"
                f"{float(row['candan_gain_vs_grid_db_ci95_high']):.2f}]$")
        body.append(
            f"{float(row['separation_bins']):.2f} & {float(row['dynamic_range_db']):.0f} & "
            f"{float(row['snr_db']):.0f} & {gain} & {pct(row['mean_candan_per_component_hit'])} & "
            f"{pct(row['mean_candan_designated_pair_assignment'])} & {pct(row['mean_candan_strict_recovery'])} & "
            f"{pct(row['mean_candan_strong_hit'])}/{pct(row['mean_candan_weak_hit'])} \\\\"
        )
    lines = [r"\begingroup", r"\scriptsize", r"\setlength{\tabcolsep}{3.0pt}",
             r"\refstepcounter{table}\label{tab:supp_stress_cells}",
             r"\begin{center}",
             r"\textsc{Table \thetable}: Complete pure-Candan controlled near--far ledger.\\",
             r"Intervals use five seed means.\par\smallskip",
             r"\begin{tabular}{cccrrrrr}"] + heading + body[:28] + [
             r"\bottomrule", r"\end{tabular}", r"\end{center}", r"\newpage",
             r"\begin{center}", r"\textsc{Table \thetable\ (continued)}\par\smallskip",
             r"\begin{tabular}{cccrrrrr}"] + heading + body[28:] + [
             r"\bottomrule", r"\end{tabular}", r"\end{center}", r"\endgroup"]
    write("tsp_stress_cells_table.tex", lines)


def seventh_round_audits() -> None:
    metrics = [row for row in read_rows(PROTOCOL_DIR / "test_incremental_metrics.csv")
               if row["protocol"] == "theory_fixed_tau_zero_no_calibration"]
    lines = [r"\begin{table}[!ht]", r"\centering", r"\footnotesize",
             r"\caption{Calibration-free projection selection. Increments and intervals are paired over five seed means.}",
             r"\label{tab:supp_projection_protocol}",
             r"\begin{tabular}{lrrrrr}", r"\toprule",
             r"Profile & Candan & Selected & Increment [95\%] & Return & Harmful rejection \\",
             r"\midrule"]
    for row in metrics:
        rejection = "--" if row["harmful_rejection"].lower() == "nan" else pct(row["harmful_rejection"])
        lines.append(
            f"{row['profile']} & {float(row['ungated_gain_db']):.3f} & {float(row['gated_gain_db']):.3f} & "
            f"${float(row['paired_increment_db']):.3f}\\,[{float(row['paired_increment_ci95_low_db']):.3f},{float(row['paired_increment_ci95_high_db']):.3f}]$ & "
            f"{pct(row['pass_rate'])} & {rejection} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    write("tsp_projection_protocol_table.tex", lines)

    runtime = read_rows(PROJECTION_RUNTIME_DIR / "summary.csv")
    labels = {"axiswise_candan_joint_ls": "Candan",
              "legacy_explicit_residual_gate": "Explicit two-residual implementation",
              "projection_energy_gate": "Projection-selected Candan"}
    lines = [r"\begin{table}[!ht]", r"\centering", r"\footnotesize",
             r"\caption{Unified 1200-scene runtime audit (one thread, complex128, median of three repetitions).}",
             r"\label{tab:supp_projection_runtime}", r"\begin{tabular}{lrrr}", r"\toprule",
             r"Method & Update (ms) & Decision (ms) & End to end (ms) \\", r"\midrule"]
    for row in runtime:
        if row["method"] not in labels:
            continue
        lines.append(f"{labels[row['method']]} & {float(row['median_local_update_ms']):.2f} & "
                     f"{float(row['median_gate_decision_ms']):.2f} & {float(row['median_wall_clock_ms']):.2f} \\\\ ")
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    write("tsp_projection_runtime_table.tex", lines)

    physical = read_rows(PHYSICAL_DIR / "profile_scene_physical_metrics.csv")
    lines = [r"\begin{table}[!ht]", r"\centering", r"\scriptsize",
             r"\caption{CDL physical-parameter results on the same 9000 scenes.}",
             r"\label{tab:supp_physical}", r"\begin{tabular}{lrrrrrr}", r"\toprule",
             r"Profile & \multicolumn{3}{c}{Delay RMSE (ns)} & \multicolumn{3}{c}{Joint quarter-bin hit (\%)} \\",
             r" & Grid & Candan & Selected & Grid & Candan & Selected \\", r"\midrule"]
    for row in physical:
        lines.append(f"{row['profile']} & {float(row['mean_scene_grid_delay_rmse_ns']):.2f} & "
                     f"{float(row['mean_scene_candan_delay_rmse_ns']):.2f} & {float(row['mean_scene_gated_candan_delay_rmse_ns']):.2f} & "
                     f"{pct(row['mean_scene_grid_joint_quarter_bin_hit'])} & {pct(row['mean_scene_candan_joint_quarter_bin_hit'])} & "
                     f"{pct(row['mean_scene_gated_candan_joint_quarter_bin_hit'])} \\\\ ")
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    write("tsp_physical_table.tex", lines)


def stress_pair_summary() -> None:
    rows = read_rows(BOUNDARY_DIR / "strict_pair_by_separation.csv")
    lines = [
        r"\begin{table}[!ht]",
        r"\centering",
        r"\caption{Controlled-pair metrics with five-seed Student-$t$ intervals for strict recovery. Pair assignment requires both designated components within half a bin; strict recovery also requires distinct coordinates and separation fidelity. Separation error averages all scenes, including failed assignments.}",
        r"\label{tab:supp_pair_metrics}",
        r"\scriptsize",
        r"\setlength{\tabcolsep}{3pt}",
        r"\begin{tabular}{clrrlr}",
        r"\toprule",
        r"Separation & Method & Scenes & Assignment & Strict recovery [95\%] & Sep. error \\",
        r"(bin) & & & (\%) & (\%) & (bin) \\",
        r"\midrule",
    ]
    for separation in (0.25, 0.50, 1.00, 2.00):
        selected_new = [row for row in rows if float(row["separation_bins"]) == separation]
        for index, row in enumerate(selected_new):
            sep = f"{separation:.2f}" if index == 0 else ""
            lines.append(
                f"{sep} & {row['method']} & {row['scene_count']} & "
                f"{pct(row['pair_assignment_rate'])} & "
                f"${pct(row['strict_recovery_rate'])}\\,[{pct(row['strict_ci95_low'])},{pct(row['strict_ci95_high'])}]$ & "
                f"{float(row['mean_separation_error_bins']):.2f} \\\\"
            )
        if separation != 2.00:
            lines.append(r"\addlinespace[1pt]")
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    write("tsp_stress_pair_table.tex", lines)
    return

    for separation in (0.25, 0.50, 1.00, 2.00):
        selected = [row for row in rows if float(row["separation_bins"]) == separation]
        lines.append(
            f"{separation:.2f} & "
            f"{100 * mean(float(row['grid_controlled_pair_joint_hit']) for row in selected):.1f} & "
            f"{100 * mean(float(row['local_controlled_pair_joint_hit']) for row in selected):.1f} & "
            f"{100 * mean(float(row['grid_distinct_pair_recovery']) for row in selected):.1f} & "
            f"{100 * mean(float(row['local_distinct_pair_recovery']) for row in selected):.1f} & "
            f"{mean(float(row['grid_pair_separation_error_bins']) for row in selected):.2f} & "
            f"{mean(float(row['local_pair_separation_error_bins']) for row in selected):.2f} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    write("tsp_stress_pair_table.tex", lines)


def support_quality() -> None:
    rows = [
        row for row in read_rows(SUPPORT_DIR / "support_quality_strata.csv")
        if row["stratum_type"] == "coarse_support_quality"
    ]
    lines = [
        r"\begin{table}[!ht]",
        r"\centering",
        r"\caption{Support-quality strata on all 1200 full-offset test scenes. Intervals use the seed as the statistical unit.}",
        r"\label{tab:supp_support_quality}",
        r"\scriptsize",
        r"\setlength{\tabcolsep}{3pt}",
        r"\begin{tabular}{crrrr}",
        r"\toprule",
        r"$q_{\rm sup}$ & Scenes/seeds & Gain [95\%] (dB) & Candidate correctness [95\%] & Mean $\kappa(A_1)$ \\",
        r"\midrule",
    ]
    for row in rows:
        quality = row["stratum"].split("=")[1]
        lines.append(
            f"{quality} & {row['scene_count']}/{row['seed_count']} & "
            f"${float(row['mean_local_gain_vs_grid_db']):.2f}\\,[{float(row['local_gain_ci95_low_db']):.2f},{float(row['local_gain_ci95_high_db']):.2f}]$ & "
            f"${pct(row['mean_candidate_axis_correctness'])}\\,[{pct(row['candidate_axis_correctness_ci95_low'])},{pct(row['candidate_axis_correctness_ci95_high'])}]\\%$ & "
            f"{float(row['mean_refined_design_condition']):.2f} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    write("tsp_support_quality_table.tex", lines)


def theory_condition() -> None:
    components = read_rows(STRESS_LEGACY_DIR / "theory_component_summary.csv")
    scenes = read_rows(STRESS_LEGACY_DIR / "theory_scene_summary.csv")
    lines = [
        r"\begin{table}[!ht]",
        r"\centering",
        r"\caption{Score-gap sufficient-condition grouping with $\eta=0.05$ and 125 candidates per neighborhood.}",
        r"\label{tab:supp_theory_condition}",
        r"\footnotesize",
        r"\begin{tabular}{lrrrr}",
        r"\toprule",
        r"Grouping & Count & Candidate axes & All candidate axes & Local half-bin \\",
        r"\midrule",
    ]
    for row in reversed(components):
        label = "Component condition holds" if row["score_gap_condition"] == "satisfied" else "Other components"
        lines.append(
            f"{label} & {row['component_count']} & "
            f"{pct(row['mean_candidate_axis_correctness'])}\\% & "
            f"{pct(row['candidate_all_axis_correct_rate'])}\\% & "
            f"{pct(row['local_half_bin_hit_rate'])}\\% \\\\"
        )
    all_scene = next(
        row
        for row in scenes
        if row["all_component_score_gap_condition"] == "satisfied"
    )
    lines.append(r"\midrule")
    lines.append(
        f"All-$L$ scene condition holds & {all_scene['scene_count']} & -- & -- & -- \\\\"
    )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    write("tsp_theory_condition_table.tex", lines)


def full_offset() -> None:
    rows = read_rows(FULL_OFFSET_DIR / "method_summary.csv")
    labels = {
        "grid_fft_topL_joint_ls": "Grid FFT top-$L$",
        "axiswise_quadratic_peak_joint_ls": "Quadratic power three-sample",
        "axiswise_candan_joint_ls": "Candan complex three-sample",
        "one_step_fixed_support_newton_joint_ls": "One-step fixed-support Newton",
        "cartesian_local_joint_ls": "Cartesian local",
    }
    lines = [
        r"\begin{table}[!ht]",
        r"\centering",
        r"\caption{Full-offset test on 1200 scenes with fractional coordinates in $[-0.49,0.49]$.}",
        r"\label{tab:supp_full_offset}",
        r"\footnotesize",
        r"\begin{tabular}{lrrr}",
        r"\toprule",
        r"Method & NMSE (dB) & Gain (dB) & Per-component hit (\%) \\",
        r"\midrule",
    ]
    for row in rows:
        if row["method"] not in labels:
            continue
        lines.append(
            f"{labels[row['method']]} & {float(row['mean_measurement_nmse_db']):.2f} & "
            f"{float(row['mean_gain_vs_grid_db']):.2f} & "
            f"{pct(row['mean_per_component_half_bin_hit'])} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    write("tsp_full_offset_table.tex", lines)


def gate_transfer() -> None:
    rows = read_rows(TRANSFER_DIR / "transfer_summary.csv")
    short = {"CDL": "CDL", "Synthetic full-offset": "Full offset"}
    lines = [
        r"\begin{table}[!ht]",
        r"\centering",
        r"\caption{Frozen-threshold transfer between full-offset synthetic and CDL geometries.}",
        r"\label{tab:supp_gate_transfer}",
        r"\footnotesize",
        r"\begin{tabular}{llrrrr}",
        r"\toprule",
        r"Calibrate & Test & Pass & Recall & Rejection & Gated gain \\",
        r" & & (\%) & (\%) & (\%) & (dB) \\",
        r"\midrule",
    ]
    for row in rows:
        rejection = (
            "--"
            if row["negative_gain_rejection"].lower() == "nan"
            else pct(row["negative_gain_rejection"])
        )
        lines.append(
            f"{short[row['calibration_geometry']]} & {short[row['test_geometry']]} & "
            f"{pct(row['pass_rate'])} & {pct(row['positive_gain_recall'])} & "
            f"{rejection} & {float(row['gated_gain_db']):.2f} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    write("tsp_gate_transfer_table.tex", lines)


def cluster_bootstrap() -> None:
    rows = read_rows(BOOTSTRAP_DIR / "cluster_bootstrap_summary.csv")
    selected = [
        row
        for row in rows
        if row["metric"] in {
            "gated_gain_db", "positive_gain_recall", "negative_gain_rejection",
            "auroc", "average_precision", "brier_score",
            "expected_calibration_error_10bin",
        }
        and row["cluster_bootstrap_ci95_low"].lower() != "nan"
    ]
    short = {"CDL": "CDL", "Synthetic full-offset": "Full offset"}
    metric = {
        "gated_gain_db": "Gated gain (dB)",
        "positive_gain_recall": "Positive-gain recall",
        "negative_gain_rejection": "Negative-gain rejection",
        "auroc": "AUROC",
        "average_precision": "Average precision",
        "brier_score": "Brier score",
        "expected_calibration_error_10bin": "ECE (10 bins)",
    }
    lines = [
        r"\begin{table}[!ht]",
        r"\centering",
        r"\caption{Seed-cluster bootstrap intervals (10,000 resamples of five complete seed blocks).}",
        r"\label{tab:supp_cluster_bootstrap}",
        r"\footnotesize",
        r"\begin{tabular}{llrrr}",
        r"\toprule",
        r"Geometry & Metric & Estimate & 2.5\% & 97.5\% \\",
        r"\midrule",
    ]
    for row in selected:
        scale = 100.0 if row["metric"] in {"positive_gain_recall", "negative_gain_rejection"} else 1.0
        digits = 3 if row["metric"] in {
            "auroc", "average_precision", "brier_score",
            "expected_calibration_error_10bin",
        } else 2
        lines.append(
            f"{short[row['geometry']]} & {metric[row['metric']]} & "
            f"{scale * float(row['point_estimate']):.{digits}f} & "
            f"{scale * float(row['cluster_bootstrap_ci95_low']):.{digits}f} & "
            f"{scale * float(row['cluster_bootstrap_ci95_high']):.{digits}f} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    write("tsp_cluster_bootstrap_table.tex", lines)


def candan_cdl() -> None:
    rows = read_rows(CANDAN_CDL_DIR / "profile_summary.csv")
    lines = [
        r"\begin{table}[!ht]", r"\centering",
        r"\caption{Candan complex three-sample comparator on the frozen 9000-scene CDL test geometry. Intervals use five seed means.}",
        r"\label{tab:supp_candan_cdl}", r"\footnotesize",
        r"\begin{tabular}{crrrr}", r"\toprule",
        r"Profile & Scenes & Grid NMSE & Candan NMSE & Gain [95\%] \\",
        r" & & (dB) & (dB) & (dB) \\", r"\midrule",
    ]
    for row in rows:
        lines.append(
            f"CDL-{row['profile']} & {row['scene_count']} & "
            f"{float(row['mean_grid_channel_nmse_db']):.2f} & "
            f"{float(row['mean_candan_channel_nmse_db']):.2f} & "
            f"${float(row['mean_candan_gain_vs_grid_db']):.2f}\\,[{float(row['gain_ci95_low_db']):.2f},{float(row['gain_ci95_high_db']):.2f}]$ \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    write("tsp_candan_cdl_table.tex", lines)


def candan_gate_profiles() -> None:
    rows = read_rows(ROUTE_DIR / "test_profile_summary.csv")
    lines = [
        r"\begin{table}[!t]", r"\centering",
        r"\caption{Residual-gated Candan on frozen CDL tests. Intervals use five seed means.}",
        r"\label{tab:candan_gate_profiles}", r"\footnotesize",
        r"\setlength{\tabcolsep}{3.1pt}",
        r"\begin{tabular}{lccc}", r"\toprule",
        r"Profile & Candan gain & Gated gain & Pass \\",
        r" & (dB) & (dB) & (\%) \\", r"\midrule",
    ]
    for row in rows:
        label = "All" if row["profile"] == "All" else f"CDL-{row['profile']}"
        lines.append(
            f"{label} & {float(row['candan_gain_db']):.2f} & "
            f"${float(row['gated_candan_gain_db']):.2f}\\,[{float(row['gated_candan_gain_ci95_low_db']):.2f},{float(row['gated_candan_gain_ci95_high_db']):.2f}]$ & "
            f"{pct(row['gated_candan_pass_rate'])} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    write("tsp_candan_gate_profiles_table.tex", lines)


def boundary_audits() -> None:
    duplicates = read_rows(BOUNDARY_DIR / "duplicate_association.csv")
    false_accepts = read_rows(BOUNDARY_DIR / "gate_false_accept_summary.csv")
    lines = [
        r"\begin{table}[!ht]", r"\centering",
        r"\caption{Duplicate-neighborhood association on 1200 controlled-pair scenes.}",
        r"\label{tab:supp_duplicate}", r"\footnotesize",
        r"\begin{tabular}{lrrrr}", r"\toprule",
        r"Group & Scenes & Candan strict & Cartesian strict & Cartesian gain \\",
        r" & & (\%) & (\%) & (dB) \\", r"\midrule",
    ]
    for row in duplicates:
        lines.append(
            f"{row['group']} & {row['scene_count']} & {pct(row['candan_strict_recovery_rate'])} & "
            f"{pct(row['cartesian_strict_recovery_rate'])} & {float(row['cartesian_gain_vs_grid_db']):.2f} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}", ""])
    duplicate_lines = list(lines)
    false_start = len(lines)
    lines.extend([
        r"\begin{table}[!ht]", r"\centering",
        r"\caption{False accepts of the frozen CDL residual gate. Loss is measured against the clean channel.}",
        r"\label{tab:supp_false_accept}", r"\footnotesize",
        r"\begin{tabular}{lrrrr}", r"\toprule",
        r"Profile & Negative scenes & False accepts & Mean loss & Maximum loss \\",
        r" & & (\%) & (dB) & (dB) \\", r"\midrule",
    ])
    for row in false_accepts:
        lines.append(
            f"{row['profile']} & {row['negative_scene_count']} & {pct(row['false_accept_rate'], 2)} & "
            f"{float(row['mean_clean_loss_db']):.2f} & {float(row['maximum_clean_loss_db']):.2f} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    write("tsp_boundary_audit_tables.tex", lines)
    write("tsp_duplicate_table.tex", duplicate_lines)
    write("tsp_false_accept_table.tex", lines[false_start:])


def main() -> None:
    local_family()
    gate_cells()
    gate_loso()
    stress_cells_long()
    stress_pair_summary()
    support_quality()
    theory_condition()
    full_offset()
    gate_transfer()
    cluster_bootstrap()
    candan_cdl()
    boundary_audits()
    seventh_round_audits()


if __name__ == "__main__":
    main()
