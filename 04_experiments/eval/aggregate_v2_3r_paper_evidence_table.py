from __future__ import annotations

import csv
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_active_modules"))

from common.manifest import write_run_manifest, write_summary_md


def load_manifest(relative_path: str) -> dict[str, Any]:
    path = ROOT / relative_path
    return json.loads(path.read_text(encoding="utf-8"))


def fmt(value: Any, digits: int = 4) -> str:
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def row(
    *,
    component: str,
    paper_role: str,
    status: str,
    claim: str,
    primary_metric: str,
    evidence_dir: str,
    run_id: str,
    paper_use: str,
    boundary: str,
) -> dict[str, str]:
    return {
        "component": component,
        "paper_role": paper_role,
        "status": status,
        "claim": claim,
        "primary_metric": primary_metric,
        "evidence_dir": evidence_dir,
        "run_id": run_id,
        "paper_use": paper_use,
        "boundary": boundary,
    }


def write_table_markdown(output_dir: Path, rows: list[dict[str, str]]) -> Path:
    lines = [
        "# v2.3R Paper Evidence Table",
        "",
        "This table is generated from current manifests and audit files. It is intended as a manuscript-facing evidence map, not as a substitute for the underlying run artifacts.",
        "",
        "| Component | Role | Status | Primary metric | Evidence | Paper use | Boundary |",
        "|---|---|---|---|---|---|---|",
    ]
    for item in rows:
        lines.append(
            "| "
            f"{item['component']} | "
            f"{item['paper_role']} | "
            f"{item['status']} | "
            f"{item['primary_metric']} | "
            f"`{item['evidence_dir']}` | "
            f"{item['paper_use']} | "
            f"{item['boundary']} |"
        )
    lines.extend(
        [
            "",
            "## Claim Discipline",
            "",
            "- Treat G2 and A4 as local synthetic/off-grid evidence; the larger samples strengthen precision but do not create an external-channel claim.",
            "- Treat A4 as high-L/platform early stopping for L>=32 at SNR=20 dB, not as a global IA-AUD optimal-depth proof or broad SNR-robust gate.",
            "- Treat A5 as appendix/high-stress failure-mode evidence, not as a main contribution.",
            "- Treat the scaled Sionna CDL output as energy-supported but exact-bin-weak evidence: it reaches 5 seeds x 50 samples and now includes CIR-grounded grid-baseline delay/projected-angle RMSE plus a clean-grid floor, but full Sensors E1 still needs the trained estimator path.",
            "- Treat DeepMIMO O1_60 as scaled 5-seed x 100-user weak scalar source-alpha transfer proxy evidence only; full Sensors E2 still needs full trained G2/T-OMP-Net evaluation and physical angle/delay metric validation.",
            "- Treat DeepMIMO I3_60 as scaled 5-seed x 100-user partial scalar source-alpha transfer proxy evidence only; its mean NMSE gain is positive but at least one cell is negative, and full Sensors E3 still needs trained cross-domain G2/T-OMP-Net evaluation and physical angle/delay metric validation.",
            "- The matched NOMP-inspired result dominates learned-scalar accuracy only in the known-order dense sinusoidal regime; frame the learned path as a lower-compute amortized point plus a separately validated CDL controller.",
            "- Separable forward-backward ESPRIT remains timing-only because the current implementation has no cross-axis pairing; PARAFAC-ALS carries matched accuracy and failure-rate rows.",
            "- DeepMIMO O1_60/I3_60 data access and scaled scalar-alpha proxy runs are ready, but do not claim final DeepMIMO Set E performance until full trained channel NMSE plus physical angle/delay RMSE runs are recorded.",
            "- Treat CRLB evidence as single-target high-SNR trend consistency plus analytic derivative validation, not as full multi-target asymptotic efficiency.",
        ]
    )
    path = output_dir / "paper_evidence_table.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    g2 = load_manifest("05_results/stage2_torch_locked_scale_g2_seed_sweep_paper_30test/run_manifest.json")
    a4_cross_l = load_manifest("05_results/stage3_a4_cross_l_plateau_gate_seed_sweep_strengthened/run_manifest.json")
    e12 = load_manifest("05_results/tensor_nomp3d_matched_paper_5seed/run_manifest.json")
    e12_comparators = load_manifest("05_results/e12_matched_accuracy_comparators/run_manifest.json")
    a4_snr = load_manifest("05_results/stage3_a4_snr_plateau_gate_seed_sweep/run_manifest.json")
    a4_frontier = load_manifest("05_results/stage3_a4_snr_threshold_frontier/run_manifest.json")
    a4_snr_aware = load_manifest("05_results/stage3_a4_snr_aware_gate_diagnostic/run_manifest.json")
    kruskal = load_manifest("05_results/stage3_paper_scale_kruskal_proxy/run_manifest.json")
    synthetic = load_manifest("05_results/stage3_synthetic_cross_scene_generalization/run_manifest.json")
    sionna_cdl = load_manifest("05_results/sionna_cdl_profile_generalization/run_manifest.json")
    sionna_cdl_scaled = load_manifest(
        "05_results/sionna_cdl_profile_generalization_scaled/run_manifest.json"
    )
    sionna_cdl_physical = load_manifest(
        "05_results/sionna_cdl_physical_metrics_grid_baseline/run_manifest.json"
    )
    deepmimo_audit = load_manifest("05_results/deepmimo_set_e_access_audit/run_manifest.json")
    deepmimo_o1 = load_manifest("05_results/deepmimo_o1_60_g2/run_manifest.json")
    deepmimo_i3 = load_manifest("05_results/deepmimo_i3_60_crossdomain/run_manifest.json")
    deepmimo_campaign = load_manifest(
        "05_results/deepmimo_source_alpha_seed_campaign/run_manifest.json"
    )
    complexity = load_manifest("05_results/complexity_benchmark/run_manifest.json")
    crlb = load_manifest("05_results/stage3_crlb_asymptotic_tightness/run_manifest.json")
    a5 = load_manifest("05_results/stage3_a5_combined_impairment_presmoke/run_manifest.json")

    g2m = g2["metrics"]
    a4m = a4_cross_l["metrics"]
    e12m = e12["metrics"]
    e12cm = e12_comparators["metrics"]
    a4sm = a4_snr["metrics"]
    a4fm = a4_frontier["metrics"]
    a4am = a4_snr_aware["metrics"]
    km = kruskal["metrics"]
    sm = synthetic["metrics"]
    cdlm = sionna_cdl["metrics"]
    cdlsm = sionna_cdl_scaled["metrics"]
    cdlpm = sionna_cdl_physical["metrics"]
    o1m = deepmimo_o1["metrics"]
    i3m = deepmimo_i3["metrics"]
    dcm = deepmimo_campaign["metrics"]
    exm = complexity["metrics"]
    cm = crlb["metrics"]
    a5m = a5["metrics"]
    a5_degradation = a5m["degradation_by_profile_db"]

    rows = [
        row(
            component="G2 T-OMP-Net bounded off-grid refinement",
            paper_role="main result candidate",
            status="supported-local",
            claim=(
                "Trainable bounded off-grid refinement improves measurement NMSE over grid Tensor-OMP "
                "at locked tensor scale."
            ),
            primary_metric=(
                f"mean gain {fmt(g2m['mean_l_cell_gain_vs_grid_db'])} dB; "
                f"min L-cell gain {fmt(g2m['min_l_cell_gain_vs_grid_db'])} dB"
            ),
            evidence_dir="05_results/stage2_torch_locked_scale_g2_seed_sweep_paper_30test",
            run_id=g2["run_id"],
            paper_use="main text method/evaluation table",
            boundary="local synthetic/off-grid; 30 held-out scenes per L/seed; not external-channel validation",
        ),
        row(
            component="E12 matched NOMP-inspired compute--accuracy comparison",
            paper_role="main trade-off evidence",
            status="trusted-with-caveats",
            claim="NOMP-inspired continuous refinement dominates accuracy while the learned scalar occupies a lower-compute point.",
            primary_metric=(
                f"NOMP min gain vs grid {fmt(e12m['nomp_min_gain_vs_grid_db'])} dB; "
                f"NOMP/scalar median runtime ratio {fmt(e12m['nomp_to_scalar_median_runtime_ratio'])}x"
            ),
            evidence_dir="05_results/tensor_nomp3d_matched_paper_5seed",
            run_id=e12["run_id"],
            paper_use="main matched-comparison subsection and Pareto figure",
            boundary="known target count, dense tensor, matched sinusoidal generator; not a reproduction of CFAR NOMP-OFDM-ISAC",
        ),
        row(
            component="E12 ESPRIT/PARAFAC matched comparator availability",
            paper_role="comparator boundary",
            status="parafac-matched-esprit-timing-only",
            claim="PARAFAC-ALS has matched accuracy rows; separable FB-ESPRIT is explicitly timing-only because joint pairing is unavailable.",
            primary_metric=(
                f"PARAFAC mean NMSE {fmt(e12cm['parafac_mean_nmse_db'])} dB; "
                f"failure rate {fmt(e12cm['parafac_failure_rate'])}"
            ),
            evidence_dir="05_results/e12_matched_accuracy_comparators",
            run_id=e12_comparators["run_id"],
            paper_use="matched table plus explicit timing-only row",
            boundary="fixed ten-sweep ALS; ESPRIT lacks cross-axis component pairing",
        ),
        row(
            component="A4 high-L plateau early stopping",
            paper_role="narrowed Stage-3 contribution",
            status="supported-for-L>=32",
            claim="A deployable plateau gate reduces depth/FLOPs for high-L samples while staying near fixed K=8 NMSE.",
            primary_metric=(
                f"L>=32 min mean savings {fmt(a4m['high_l_min_mean_depth_savings_percent'])}%; "
                f"max gap {fmt(a4m['high_l_max_nmse_gap_db'])} dB"
            ),
            evidence_dir="05_results/stage3_a4_cross_l_plateau_gate_seed_sweep_strengthened",
            run_id=a4_cross_l["run_id"],
            paper_use="main or secondary result with high-L wording",
            boundary="not global IA-AUD; L=16 is boundary-only because max gap exceeds 0.5 dB",
        ),
        row(
            component="A4 SNR-axis plateau gate sensitivity",
            paper_role="boundary/diagnostic result",
            status="snr-robustness-inconclusive",
            claim="The current scalar plateau gate does not support a broad SNR-robust early-stop claim.",
            primary_metric=(
                f"min SNR-cell mean savings {fmt(a4sm['min_snr_mean_depth_savings_percent'])}%; "
                f"max gap {fmt(a4sm['max_snr_nmse_gap_db'])} dB"
            ),
            evidence_dir="05_results/stage3_a4_snr_plateau_gate_seed_sweep",
            run_id=a4_snr["run_id"],
            paper_use="boundary row or appendix sensitivity",
            boundary="SNR={10,20,30}, L=32; 10/20 dB exceed 0.5 dB max-gap in small sample, 30 dB falls below 25% mean savings",
        ),
        row(
            component="A4 SNR threshold frontier diagnostic",
            paper_role="boundary/diagnostic result",
            status="scalar-frontier-fails-snr-axis",
            claim="A finer scalar threshold frontier still does not support widening A4 across the tested SNR axis.",
            primary_metric=(
                f"standard min SNR savings {fmt(a4fm['standard_min_snr_mean_depth_savings_percent'])}%; "
                f"oracle min SNR savings {fmt(a4fm['oracle_min_snr_mean_depth_savings_percent'])}%; "
                f"oracle max gap {fmt(a4fm['oracle_max_snr_nmse_gap_db'])} dB"
            ),
            evidence_dir="05_results/stage3_a4_snr_threshold_frontier",
            run_id=a4_frontier["run_id"],
            paper_use="appendix diagnostic or future-work steering",
            boundary="test-oracle frontier is diagnostic only; result argues against broadening A4 with a scalar threshold gate",
        ),
        row(
            component="A4 SNR-aware gate diagnostic",
            paper_role="boundary/diagnostic result",
            status="snr-aware-gate-refuted-current-curves",
            claim=(
                "A lightweight SNR/curve-feature-aware sequential gate still does not support widening "
                "A4 across the tested SNR axis under the current refinement curves."
            ),
            primary_metric=(
                f"kNN min SNR savings {fmt(a4am['knn_min_snr_mean_depth_savings_percent'])}%; "
                f"kNN max gap {fmt(a4am['knn_max_snr_nmse_gap_db'])} dB; "
                f"oracle min SNR savings {fmt(a4am['oracle_min_snr_mean_depth_savings_percent'])}%"
            ),
            evidence_dir="05_results/stage3_a4_snr_aware_gate_diagnostic",
            run_id=a4_snr_aware["run_id"],
            paper_use="appendix diagnostic or future-work steering",
            boundary=(
                "per-curve quality oracle is diagnostic only; result suggests the current curve family "
                "lacks enough cross-SNR early-stop room without refinement-schedule redesign"
            ),
        ),
        row(
            component="Paper-scale Kruskal/on-grid sanity",
            paper_role="supporting sanity row",
            status="supported-on-grid-proxy",
            claim="Paper-scale on-grid Tensor-OMP stays below the Kruskal proxy bound with perfect support recall in this local scan.",
            primary_metric=(
                f"bound {km['paper_kruskal_bound']}; "
                f"max L/Lmax {fmt(km['max_bound_ratio'])}; "
                f"min recall {fmt(km['min_support_recall'])}"
            ),
            evidence_dir="05_results/stage3_paper_scale_kruskal_proxy",
            run_id=kruskal["run_id"],
            paper_use="sanity/check table or appendix",
            boundary="on-grid proxy only; not off-grid, CDL, or DeepMIMO evidence",
        ),
        row(
            component="Synthetic cross-scene portability",
            paper_role="fallback portability evidence",
            status=str(sm["claim_update"]),
            claim="A source-trained bounded off-grid alpha keeps useful gain under controlled synthetic scene shifts.",
            primary_metric=(
                f"min target gain {fmt(sm['min_target_gain_vs_grid_db'])} dB; "
                f"max gap vs target oracle {fmt(sm['max_target_gap_vs_oracle_db'])} dB"
            ),
            evidence_dir="05_results/stage3_synthetic_cross_scene_generalization",
            run_id=synthetic["run_id"],
            paper_use="fallback/generalization sanity row",
            boundary="not ray-traced, not CDL, and not DeepMIMO Set E validation",
        ),
        row(
            component="Sionna CDL profile generalization",
            paper_role="E1 external-channel dev-chain",
            status=str(cdlm["claim_update"]),
            claim="The open-source Sionna CDL-A/C/D channel path can feed a reproducible delay-angle sparse-recovery evaluation schema.",
            primary_metric=(
                f"profiles {cdlm['profiles']}; "
                f"mean channel NMSE {fmt(cdlm['mean_channel_nmse_db_all'])} dB; "
                f"min mean support recall {fmt(cdlm['min_mean_support_recall'])}"
            ),
            evidence_dir="05_results/sionna_cdl_profile_generalization",
            run_id=sionna_cdl["run_id"],
            paper_use="development evidence only until full E1 rerun",
            boundary=(
                "bin-proxy delay/angle metrics and small dev sample count; "
                "current support recall is weak, so do not use as Sensors main CDL result yet"
            ),
        ),
        row(
            component="Sionna CDL-A/C/D scaled support diagnostic",
            paper_role="E1 scaled external-channel support",
            status=str(cdlsm["claim_update"]),
            claim=(
                "At the planned five-seed x 50-sample scale and a 128 x 16 FFT grid, "
                "CDL-A/C/D recovery retains high oracle top-k energy efficiency while exact "
                "bin overlap remains weak only in over-budgeted low-SNR CDL-D cells."
            ),
            primary_metric=(
                f"samples {fmt(cdlsm['sample_row_count'])}; "
                f"mean channel NMSE {fmt(cdlsm['mean_channel_nmse_db_all'])} dB; "
                f"min exact recall {fmt(cdlsm['min_mean_support_recall'])}; "
                f"min top-k energy efficiency {fmt(cdlsm['min_mean_topk_energy_efficiency'])}; "
                f"min delay/angle recall {fmt(cdlsm['min_mean_delay_support_recall'])}/"
                f"{fmt(cdlsm['min_mean_angle_support_recall'])}"
            ),
            evidence_dir="05_results/sionna_cdl_profile_generalization_scaled",
            run_id=sionna_cdl_scaled["run_id"],
            paper_use="supporting/appendix E1 evidence and limitation analysis",
            boundary=(
                "five seeds x 50 samples with canonical exact recall retained; CDL-D at 0 dB "
                "and L=16 remains exact-bin weak because its resolvable support is much smaller "
                "than the requested budget; trained estimator comparison remains open"
            ),
        ),
        row(
            component="Sionna CDL CIR-grounded physical grid baseline",
            paper_role="E1 physical-metric baseline",
            status=str(cdlpm["physical_metric_status"]),
            claim=(
                "Sionna tau and clean per-cluster CIR responses now provide reproducible "
                "nanosecond delay and projected broadside-angle metrics for the grid baseline."
            ),
            primary_metric=(
                f"mean delay RMSE {fmt(cdlpm['mean_physical_delay_rmse_ns_all'])} ns; "
                f"SNR>=20 delay RMSE {fmt(cdlpm['mean_physical_delay_rmse_ns_snr_ge_20'])} ns; "
                f"clean-grid delay floor {fmt(cdlpm['mean_clean_grid_physical_delay_rmse_ns_all'])} ns; "
                f"mean projected-angle RMSE {fmt(cdlpm['mean_projected_broadside_angle_rmse_deg_all'])} deg; "
                f"clean-grid angle floor {fmt(cdlpm['mean_clean_grid_projected_broadside_angle_rmse_deg_all'])} deg"
            ),
            evidence_dir="05_results/sionna_cdl_physical_metrics_grid_baseline",
            run_id=sionna_cdl_physical["run_id"],
            paper_use="E1 grid comparator and representation-floor evidence",
            boundary=(
                "projected broadside angle is the identifiable 1-D ULA quantity, not separate "
                "azimuth/zenith AoD; high-SNR results lie near the clean-grid floor, so this is "
                "not trained-estimator performance"
            ),
        ),
        row(
            component="DeepMIMO O1_60 raw-loader G2 dev",
            paper_role="E2 ray-traced dev-chain",
            status=str(o1m["claim_update"]),
            claim="A Stage-2 source-trained scalar G2 alpha can be applied directly to O1_60 channel tensors and assigned a weak/partial/fail transfer-proxy classification.",
            primary_metric=(
                f"class {o1m['transfer_proxy_classification']}; "
                f"alpha {fmt(o1m['source_alpha'])}; "
                f"users {fmt(o1m['n_users'])}; tx {fmt(o1m['n_tx'])}; "
                f"grid NMSE {fmt(o1m['mean_grid_channel_nmse_db_all'])} dB; "
                f"source-alpha NMSE {fmt(o1m['mean_source_alpha_channel_nmse_db_all'])} dB; "
                f"source-alpha gain {fmt(o1m['mean_source_alpha_gain_vs_grid_db'])} dB; "
                f"bounded NMSE {fmt(o1m['mean_bounded_refine_channel_nmse_db_all'])} dB; "
                f"oracle gap {fmt(o1m['mean_source_alpha_gap_vs_oracle_db'])} dB; "
                f"min mean support recall {fmt(o1m['min_mean_support_recall'])}"
            ),
            evidence_dir="05_results/deepmimo_o1_60_g2",
            run_id=deepmimo_o1["run_id"],
            paper_use="development evidence only until full E2 G2/T-OMP-Net run",
            boundary=(
                "raw MAT loader plus grid FFT top-k and Stage-2 source-trained scalar alpha transfer proxy; small 16-user dev sample; "
                "full bounded refinement and oracle-alpha are diagnostic comparators, not the deployed claim; "
                "delay/TX-bin metrics are not final physical angle/delay RMSE"
            ),
        ),
        row(
            component="DeepMIMO I3_60 cross-domain raw-loader dev",
            paper_role="E3 indoor cross-scenario dev-chain",
            status=str(i3m["claim_update"]),
            claim="A Stage-2 source-trained scalar G2 alpha can be applied directly to I3_60 channel tensors and assigned a weak/partial/fail transfer-proxy classification.",
            primary_metric=(
                f"class {i3m['transfer_proxy_classification']}; "
                f"alpha {fmt(i3m['source_alpha'])}; "
                f"users {fmt(i3m['n_users'])}; bs {fmt(i3m['n_bs'])}; "
                f"grid NMSE {fmt(i3m['mean_grid_channel_nmse_db_all'])} dB; "
                f"source-alpha NMSE {fmt(i3m['mean_source_alpha_channel_nmse_db_all'])} dB; "
                f"source-alpha gain {fmt(i3m['mean_source_alpha_gain_vs_grid_db'])} dB; "
                f"bounded NMSE {fmt(i3m['mean_bounded_refine_channel_nmse_db_all'])} dB; "
                f"oracle gap {fmt(i3m['mean_source_alpha_gap_vs_oracle_db'])} dB; "
                f"min mean support recall {fmt(i3m['min_mean_support_recall'])}"
            ),
            evidence_dir="05_results/deepmimo_i3_60_crossdomain",
            run_id=deepmimo_i3["run_id"],
            paper_use="development evidence only until full E3 trained cross-domain run",
            boundary=(
                "raw CIR loader plus grid FFT top-k and Stage-2 source-trained scalar alpha transfer proxy; "
                "partial classification because at least one cell has weak support recall; "
                "full bounded refinement and oracle-alpha are diagnostic comparators, not the deployed claim; "
                "not a full trained synthetic-to-I3 G2/T-OMP-Net transfer result"
            ),
        ),
        row(
            component="DeepMIMO source-alpha multi-seed robustness",
            paper_role="E2/E3 scaled external-channel proxy",
            status=(
                f"o1-{dcm['o1_60_campaign_classification']}; "
                f"i3-{dcm['i3_60_campaign_classification']}"
            ),
            claim=(
                "Across five independent 100-user samples, the fixed Stage-2 source alpha "
                "retains weak O1_60 transfer support and partial I3_60 transfer support."
            ),
            primary_metric=(
                f"O1 gain {fmt(dcm['o1_60_mean_source_alpha_gain_vs_grid_db'])} dB "
                f"[95% CI {fmt(dcm['o1_60_ci95_source_alpha_gain_vs_grid_db_low'])}, "
                f"{fmt(dcm['o1_60_ci95_source_alpha_gain_vs_grid_db_high'])}], "
                f"min cell {fmt(dcm['o1_60_min_cell_source_alpha_gain_vs_grid_db'])} dB; "
                f"I3 gain {fmt(dcm['i3_60_mean_source_alpha_gain_vs_grid_db'])} dB "
                f"[95% CI {fmt(dcm['i3_60_ci95_source_alpha_gain_vs_grid_db_low'])}, "
                f"{fmt(dcm['i3_60_ci95_source_alpha_gain_vs_grid_db_high'])}], "
                f"min cell {fmt(dcm['i3_60_min_cell_source_alpha_gain_vs_grid_db'])} dB"
            ),
            evidence_dir="05_results/deepmimo_source_alpha_seed_campaign",
            run_id=deepmimo_campaign["run_id"],
            paper_use="supporting multi-seed robustness evidence for C4 and E2/E3 boundary",
            boundary=(
                "five seeds x 100 users but scalar source-alpha transfer only; I3 remains partial "
                "because a cell has negative gain and support recall remains weak; not a full "
                "trained G2/T-OMP-Net or physical angle/delay evaluation"
            ),
        ),
        row(
            component="Complexity and runtime benchmark",
            paper_role="E4 engineering dev table",
            status=str(exm["claim_update"]),
            claim="The implemented Tensor-OMP/T-OMP-Net proxy paths now have a reproducible CPU wall-clock, parameter-count, memory, and operation-proxy table.",
            primary_metric=(
                f"implemented rows {fmt(exm['implemented_rows'])}; "
                f"not implemented rows {fmt(exm['not_implemented_rows'])}; "
                f"max median wall-clock {fmt(exm['max_median_wall_clock_ms'])} ms; "
                f"max params {fmt(exm['max_parameter_count'])}"
            ),
            evidence_dir="05_results/complexity_benchmark",
            run_id=complexity["run_id"],
            paper_use="development evidence only until ESPRIT/PARAFAC comparators are added",
            boundary=(
                "operation proxy is not profiler FLOPs; Torch alpha row is prepared-bin forward timing; "
                "ESPRIT/Unitary-ESPRIT and PARAFAC-ALS are explicit implementation gaps"
            ),
        ),
        row(
            component="5L CRLB trend consistency",
            paper_role="theory/evaluation support",
            status=str(cm["claim_update"]),
            claim="Analytic 5L FIM derivatives match finite differences and the single-target estimator follows the high-SNR CRLB trend.",
            primary_metric=(
                f"max FIM rel. error {cm['max_relative_fim_error']:.2e}; "
                f"30 dB mean RMSE/CRLB {fmt(cm['mean_ratio_at_30db'])}; "
                f"slope error {fmt(cm['mean_abs_rmse_slope_error_vs_expected'])}"
            ),
            evidence_dir="05_results/stage3_crlb_asymptotic_tightness",
            run_id=crlb["run_id"],
            paper_use="theory validation row",
            boundary="single-target high-SNR pilot; not full multi-target asymptotic efficiency",
        ),
        row(
            component="A5 combined impairment stress",
            paper_role="appendix/high-stress analysis",
            status="main-gate-downgrade",
            claim="Nominal combined impairment does not clear the main 5 dB robustness gate; high stress exposes a useful failure mode.",
            primary_metric=(
                f"nominal degradation {fmt(a5_degradation['combined_v23r'])} dB; "
                f"high-stress degradation {fmt(a5_degradation['combined_high'])} dB"
            ),
            evidence_dir="05_results/stage3_a5_combined_impairment_presmoke",
            run_id=a5["run_id"],
            paper_use="appendix or negative/robustness boundary",
            boundary="do not present HIR-JL as a main contribution without a new robust-training result",
        ),
        row(
            component="DeepMIMO Set E external validation",
            paper_role="ready external-data gate",
            status=str(deepmimo_audit["readiness"]),
            claim="DeepMIMO O1_60/I3_60 local assets and Python loader dependencies are ready; O1_60 has a raw-loader dev run but no full Set E G2/T-OMP-Net performance claim is recorded yet.",
            primary_metric=(
                f"dataset files {deepmimo_audit['dataset_files']}; "
                f"O1_60 files {deepmimo_audit['o1_60_files']}; "
                f"I3_60 files {deepmimo_audit['i3_60_files']}; "
                f"packages {deepmimo_audit['packages']}"
            ),
            evidence_dir="05_results/deepmimo_set_e_access_audit",
            run_id="deepmimo_set_e_access_audit",
            paper_use="methods/reproducibility readiness note only",
            boundary="must not report final DeepMIMO channel NMSE/angle/delay RMSE until scaled E2/E3 G2/T-OMP-Net performance runs are recorded",
        ),
    ]

    output_dir = ROOT / "05_results" / "v2_3r_paper_evidence_table"
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "paper_evidence_table.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    markdown_path = write_table_markdown(output_dir, rows)

    metrics = {
        "n_rows": len(rows),
        "supported_local_rows": sum("supported" in item["status"] for item in rows),
        "blocked_rows": sum("blocked" in item["status"] for item in rows),
        "downgraded_rows": sum("downgrade" in item["status"] for item in rows),
        "g2_mean_gain_db": g2m["mean_l_cell_gain_vs_grid_db"],
        "a4_high_l_min_savings_percent": a4m["high_l_min_mean_depth_savings_percent"],
        "a4_snr_min_savings_percent": a4sm["min_snr_mean_depth_savings_percent"],
        "a4_snr_max_gap_db": a4sm["max_snr_nmse_gap_db"],
        "a4_frontier_standard_min_savings_percent": a4fm[
            "standard_min_snr_mean_depth_savings_percent"
        ],
        "a4_frontier_oracle_min_savings_percent": a4fm[
            "oracle_min_snr_mean_depth_savings_percent"
        ],
        "a4_frontier_oracle_max_gap_db": a4fm["oracle_max_snr_nmse_gap_db"],
        "a4_snr_aware_knn_min_savings_percent": a4am[
            "knn_min_snr_mean_depth_savings_percent"
        ],
        "a4_snr_aware_knn_max_gap_db": a4am["knn_max_snr_nmse_gap_db"],
        "a4_snr_aware_oracle_min_savings_percent": a4am[
            "oracle_min_snr_mean_depth_savings_percent"
        ],
        "a4_snr_aware_oracle_max_gap_db": a4am["oracle_max_snr_nmse_gap_db"],
        "sionna_cdl_claim_update": cdlm["claim_update"],
        "sionna_cdl_min_mean_support_recall": cdlm["min_mean_support_recall"],
        "sionna_cdl_mean_channel_nmse_db": cdlm["mean_channel_nmse_db_all"],
        "sionna_cdl_scaled_claim_update": cdlsm["claim_update"],
        "sionna_cdl_scaled_seed_count": cdlsm["seed_count"],
        "sionna_cdl_scaled_samples_per_profile_seed": cdlsm[
            "samples_per_profile_seed"
        ],
        "sionna_cdl_scaled_mean_channel_nmse_db": cdlsm[
            "mean_channel_nmse_db_all"
        ],
        "sionna_cdl_scaled_min_mean_support_recall": cdlsm[
            "min_mean_support_recall"
        ],
        "sionna_cdl_scaled_min_topk_energy_efficiency": cdlsm[
            "min_mean_topk_energy_efficiency"
        ],
        "sionna_cdl_scaled_min_delay_support_recall": cdlsm[
            "min_mean_delay_support_recall"
        ],
        "sionna_cdl_scaled_min_angle_support_recall": cdlsm[
            "min_mean_angle_support_recall"
        ],
        "sionna_cdl_physical_metric_status": cdlpm["physical_metric_status"],
        "sionna_cdl_physical_mean_delay_rmse_ns": cdlpm[
            "mean_physical_delay_rmse_ns_all"
        ],
        "sionna_cdl_physical_mean_delay_rmse_ns_snr_ge_20": cdlpm[
            "mean_physical_delay_rmse_ns_snr_ge_20"
        ],
        "sionna_cdl_physical_clean_grid_delay_floor_ns": cdlpm[
            "mean_clean_grid_physical_delay_rmse_ns_all"
        ],
        "sionna_cdl_physical_mean_projected_angle_rmse_deg": cdlpm[
            "mean_projected_broadside_angle_rmse_deg_all"
        ],
        "sionna_cdl_physical_clean_grid_projected_angle_floor_deg": cdlpm[
            "mean_clean_grid_projected_broadside_angle_rmse_deg_all"
        ],
        "deepmimo_o1_claim_update": o1m["claim_update"],
        "deepmimo_o1_transfer_proxy_classification": o1m["transfer_proxy_classification"],
        "deepmimo_o1_source_alpha": o1m["source_alpha"],
        "deepmimo_o1_min_mean_support_recall": o1m["min_mean_support_recall"],
        "deepmimo_o1_mean_grid_channel_nmse_db": o1m["mean_grid_channel_nmse_db_all"],
        "deepmimo_o1_mean_source_alpha_channel_nmse_db": o1m[
            "mean_source_alpha_channel_nmse_db_all"
        ],
        "deepmimo_o1_mean_source_alpha_gain_vs_grid_db": o1m[
            "mean_source_alpha_gain_vs_grid_db"
        ],
        "deepmimo_o1_min_source_alpha_gain_vs_grid_db": o1m[
            "min_source_alpha_gain_vs_grid_db"
        ],
        "deepmimo_o1_mean_bounded_refine_channel_nmse_db": o1m[
            "mean_bounded_refine_channel_nmse_db_all"
        ],
        "deepmimo_o1_mean_bounded_gain_vs_grid_db": o1m["mean_bounded_gain_vs_grid_db"],
        "deepmimo_o1_min_bounded_gain_vs_grid_db": o1m["min_bounded_gain_vs_grid_db"],
        "deepmimo_o1_mean_source_alpha_gap_vs_oracle_db": o1m[
            "mean_source_alpha_gap_vs_oracle_db"
        ],
        "deepmimo_i3_claim_update": i3m["claim_update"],
        "deepmimo_i3_transfer_proxy_classification": i3m["transfer_proxy_classification"],
        "deepmimo_i3_source_alpha": i3m["source_alpha"],
        "deepmimo_i3_min_mean_support_recall": i3m["min_mean_support_recall"],
        "deepmimo_i3_mean_grid_channel_nmse_db": i3m["mean_grid_channel_nmse_db_all"],
        "deepmimo_i3_mean_source_alpha_channel_nmse_db": i3m[
            "mean_source_alpha_channel_nmse_db_all"
        ],
        "deepmimo_i3_mean_source_alpha_gain_vs_grid_db": i3m[
            "mean_source_alpha_gain_vs_grid_db"
        ],
        "deepmimo_i3_min_source_alpha_gain_vs_grid_db": i3m[
            "min_source_alpha_gain_vs_grid_db"
        ],
        "deepmimo_i3_mean_bounded_refine_channel_nmse_db": i3m[
            "mean_bounded_refine_channel_nmse_db_all"
        ],
        "deepmimo_i3_mean_bounded_gain_vs_grid_db": i3m["mean_bounded_gain_vs_grid_db"],
        "deepmimo_i3_min_bounded_gain_vs_grid_db": i3m["min_bounded_gain_vs_grid_db"],
        "deepmimo_i3_mean_source_alpha_gap_vs_oracle_db": i3m[
            "mean_source_alpha_gap_vs_oracle_db"
        ],
        "deepmimo_campaign_n_seeds": dcm["n_seeds"],
        "deepmimo_campaign_n_users_per_seed": dcm["n_users_per_seed"],
        "deepmimo_campaign_o1_classification": dcm[
            "o1_60_campaign_classification"
        ],
        "deepmimo_campaign_o1_mean_gain_db": dcm[
            "o1_60_mean_source_alpha_gain_vs_grid_db"
        ],
        "deepmimo_campaign_o1_gain_ci95_low_db": dcm[
            "o1_60_ci95_source_alpha_gain_vs_grid_db_low"
        ],
        "deepmimo_campaign_o1_gain_ci95_high_db": dcm[
            "o1_60_ci95_source_alpha_gain_vs_grid_db_high"
        ],
        "deepmimo_campaign_o1_min_cell_gain_db": dcm[
            "o1_60_min_cell_source_alpha_gain_vs_grid_db"
        ],
        "deepmimo_campaign_i3_classification": dcm[
            "i3_60_campaign_classification"
        ],
        "deepmimo_campaign_i3_mean_gain_db": dcm[
            "i3_60_mean_source_alpha_gain_vs_grid_db"
        ],
        "deepmimo_campaign_i3_gain_ci95_low_db": dcm[
            "i3_60_ci95_source_alpha_gain_vs_grid_db_low"
        ],
        "deepmimo_campaign_i3_gain_ci95_high_db": dcm[
            "i3_60_ci95_source_alpha_gain_vs_grid_db_high"
        ],
        "deepmimo_campaign_i3_min_cell_gain_db": dcm[
            "i3_60_min_cell_source_alpha_gain_vs_grid_db"
        ],
        "complexity_claim_update": exm["claim_update"],
        "complexity_implemented_rows": exm["implemented_rows"],
        "complexity_not_implemented_rows": exm["not_implemented_rows"],
        "complexity_max_median_wall_clock_ms": exm["max_median_wall_clock_ms"],
        "deepmimo_status": deepmimo_audit["readiness"],
        "deepmimo_dataset_files": deepmimo_audit["dataset_files"],
    }
    notes = [
        "Generated manuscript-facing evidence map from current run manifests.",
        "The table preserves claim boundaries so local evidence is not promoted to external validation.",
        "Regenerate this table after rerunning G2, A4, DeepMIMO, A5, Kruskal, synthetic, or CRLB evidence.",
    ]
    manifest_path = write_run_manifest(
        output_dir,
        run_id="v2_3r_paper_evidence_table_20260627",
        command="python 04_experiments/eval/aggregate_v2_3r_paper_evidence_table.py",
        config={
            "sources": [
                "05_results/stage2_torch_locked_scale_g2_seed_sweep/run_manifest.json",
                "05_results/stage3_a4_cross_l_plateau_gate_seed_sweep/run_manifest.json",
                "05_results/stage3_a4_snr_plateau_gate_seed_sweep/run_manifest.json",
                "05_results/stage3_a4_snr_threshold_frontier/run_manifest.json",
                "05_results/stage3_a4_snr_aware_gate_diagnostic/run_manifest.json",
                "05_results/stage3_paper_scale_kruskal_proxy/run_manifest.json",
                "05_results/stage3_synthetic_cross_scene_generalization/run_manifest.json",
                "05_results/sionna_cdl_profile_generalization/run_manifest.json",
                "05_results/sionna_cdl_profile_generalization_scaled/run_manifest.json",
                "05_results/sionna_cdl_physical_metrics_grid_baseline/run_manifest.json",
                "05_results/deepmimo_o1_60_g2/run_manifest.json",
                "05_results/deepmimo_i3_60_crossdomain/run_manifest.json",
                "05_results/deepmimo_source_alpha_seed_campaign/run_manifest.json",
                "05_results/complexity_benchmark/run_manifest.json",
                "05_results/stage3_crlb_asymptotic_tightness/run_manifest.json",
                "05_results/stage3_a5_combined_impairment_presmoke/run_manifest.json",
                "05_results/deepmimo_set_e_access_audit/run_manifest.json",
            ]
        },
        metrics=metrics,
        notes=notes,
        cwd=ROOT,
    )
    summary_path = write_summary_md(
        output_dir,
        title="v2.3R Paper Evidence Table",
        config_hash="v2-3r-paper-evidence-table-20260627",
        metrics=metrics,
        notes=notes,
        artifacts=[
            str(csv_path.relative_to(ROOT)),
            str(markdown_path.relative_to(ROOT)),
            str(manifest_path.relative_to(ROOT)),
        ],
    )
    print(f"Wrote {csv_path.relative_to(ROOT)}")
    print(f"Wrote {markdown_path.relative_to(ROOT)}")
    print(f"Wrote {summary_path.relative_to(ROOT)}")
    print(f"Wrote {manifest_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
