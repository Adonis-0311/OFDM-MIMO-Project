from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_manifest(result_dir: str) -> dict:
    path = ROOT / "05_results" / result_dir / "run_manifest.json"
    if not path.exists():
        return {"run_id": result_dir, "status": "manifest_missing"}
    return json.loads(path.read_text(encoding="utf-8"))


def fmt_db(value: object) -> str:
    if isinstance(value, (int, float)):
        if value != 0 and abs(value) < 1e-3:
            return f"{value:.4e}"
        return f"{value:.4f}"
    return str(value)


def main() -> None:
    a4_high_l = load_manifest("stage3_a4_high_l_plateau_gate")
    a5_combined = load_manifest("stage3_a5_combined_impairment_presmoke")
    kruskal_proxy = load_manifest("stage3_paper_scale_kruskal_proxy")
    synthetic_cross_scene = load_manifest("stage3_synthetic_cross_scene_generalization")
    crlb_tightness = load_manifest("stage3_crlb_asymptotic_tightness")
    deepmimo_audit = load_manifest("deepmimo_set_e_access_audit")
    deepmimo_campaign = load_manifest("deepmimo_source_alpha_seed_campaign")
    deepmimo_readiness = deepmimo_audit.get("readiness", "unknown")
    deepmimo_dataset_files = deepmimo_audit.get("dataset_files", "n/a")
    deepmimo_metrics = deepmimo_campaign.get("metrics", {})
    synthetic_metrics = synthetic_cross_scene.get("metrics", {})
    synthetic_gain = synthetic_metrics.get("min_target_gain_vs_grid_db", "n/a")
    synthetic_gap = synthetic_metrics.get("max_target_gap_vs_oracle_db", "n/a")
    synthetic_status = synthetic_metrics.get("claim_update", "unknown")
    crlb_metrics = crlb_tightness.get("metrics", {})
    crlb_status = crlb_metrics.get("claim_update", "unknown")
    crlb_fim_error = crlb_metrics.get("max_relative_fim_error", "n/a")
    crlb_ratio = crlb_metrics.get("mean_ratio_at_30db", "n/a")
    crlb_slope_error = crlb_metrics.get("mean_abs_rmse_slope_error_vs_expected", "n/a")
    rows = [
        {
            "gate_item": "A4 IA-AUD FLOPs/depth reduction",
            "status": "restricted-high-l-pass / global-claim-not-supported",
            "evidence": "stage3_a4_high_l_plateau_gate",
            "metric": "held-out L=32 gate savings = 33.33%; NMSE gap = 0.3643 dB",
        },
        {
            "gate_item": "A5 HIR-JL robustness value",
            "status": "main-gate-downgrade / appendix-high-stress-only",
            "evidence": "stage3_a5_combined_impairment_presmoke",
            "metric": "nominal combined degradation = 4.4395 dB; high-stress degradation = 6.6036 dB",
        },
        {
            "gate_item": "Paper-scale Kruskal identifiability sanity",
            "status": "on-grid-proxy-pass",
            "evidence": "stage3_paper_scale_kruskal_proxy",
            "metric": "Kruskal proxy bound = 87; max L/Lmax = 0.7356; min support recall = 1.0",
        },
        {
            "gate_item": "Synthetic cross-scene generalization fallback",
            "status": f"{synthetic_status} / not-deepmimo",
            "evidence": "stage3_synthetic_cross_scene_generalization",
            "metric": f"min target gain vs grid = {fmt_db(synthetic_gain)} dB; max gap vs target oracle = {fmt_db(synthetic_gap)} dB",
        },
        {
            "gate_item": "5L CRLB asymptotic tightness",
            "status": f"{crlb_status} / single-target-pilot",
            "evidence": "stage3_crlb_asymptotic_tightness",
            "metric": f"max FIM relative error = {fmt_db(crlb_fim_error)}; 30 dB mean RMSE/CRLB ratio = {fmt_db(crlb_ratio)}; mean slope error = {fmt_db(crlb_slope_error)}",
        },
        {
            "gate_item": "DeepMIMO Set E external validation",
            "status": "access-ready / o1-weak / i3-partial",
            "evidence": "deepmimo_source_alpha_seed_campaign",
            "metric": (
                f"readiness = {deepmimo_readiness}; dataset files = {deepmimo_dataset_files}; "
                f"O1 five-seed gain = {fmt_db(deepmimo_metrics.get('o1_60_mean_source_alpha_gain_vs_grid_db', 'n/a'))} dB; "
                f"I3 five-seed gain = {fmt_db(deepmimo_metrics.get('i3_60_mean_source_alpha_gain_vs_grid_db', 'n/a'))} dB; "
                f"I3 min cell = {fmt_db(deepmimo_metrics.get('i3_60_min_cell_source_alpha_gain_vs_grid_db', 'n/a'))} dB"
            ),
        },
    ]
    output_dir = ROOT / "05_results" / "stage3_g3_manifest"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "stage3_g3_manifest.json").write_text(
        json.dumps(
            {
                "runs": {
                    "stage3_a4_high_l_plateau_gate": a4_high_l,
                    "stage3_a5_combined_impairment_presmoke": a5_combined,
                    "stage3_paper_scale_kruskal_proxy": kruskal_proxy,
                    "stage3_synthetic_cross_scene_generalization": synthetic_cross_scene,
                    "stage3_crlb_asymptotic_tightness": crlb_tightness,
                    "deepmimo_set_e_access_audit": deepmimo_audit,
                    "deepmimo_source_alpha_seed_campaign": deepmimo_campaign,
                },
                "gate_rows": rows,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    lines = [
        "# Stage 3 / G3 Manifest",
        "",
        "## Gate Status",
        "",
        "| Gate item | Status | Evidence | Metric |",
        "|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['gate_item']} | {row['status']} | `{row['evidence']}` | {row['metric']} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "Stage 3 has enough local evidence to support a restricted A4 high-L early-stop mechanism and an on-grid paper-scale Kruskal sanity row. A5 should be downgraded from the main gate and retained only as high-stress robustness appendix evidence.",
            "",
            "The synthetic cross-scene fallback supports local portability of the source-trained bounded off-grid alpha under controlled synthetic shifts, but it is not ray-traced, not standards-aligned CDL, and not DeepMIMO Set E evidence.",
            "",
            "The 5L CRLB asymptotic tightness audit supports analytic derivative correctness and single-target high-SNR trend consistency. It remains pilot evidence, not a full multi-target efficiency proof.",
            "",
            "DeepMIMO access is ready and the five-seed x 100-user scalar source-alpha proxy campaign records weak O1_60 support and partial I3_60 support. This removes the data-access blocker but does not establish final Set E performance; the full trained estimator and physical angle/delay metrics remain required.",
            "",
            "Acceptance audit: `05_results/stage3_g3_manifest/acceptance_audit.md`.",
            "",
        ]
    )
    (output_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
