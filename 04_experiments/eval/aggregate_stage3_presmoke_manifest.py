from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_manifest(result_dir: str) -> dict:
    path = ROOT / "05_results" / result_dir / "run_manifest.json"
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    a4_depth = load_manifest("stage3_a4_depth_presmoke")
    a4_oracle = load_manifest("stage3_a4_oracle_earlystop")
    a4_high_l_gate = load_manifest("stage3_a4_high_l_plateau_gate")
    a5_hirjl = load_manifest("stage3_a5_hirjl_presmoke")
    a5_combined = load_manifest("stage3_a5_combined_impairment_presmoke")
    rows = [
        {
            "gate_item": "A4 IA-AUD has real adaptive-depth opportunity",
            "status": "pre-smoke-supported / mechanism-direction-revised",
            "evidence": "stage3_a4_depth_presmoke",
            "metric": "saturation depths {2:8, 8:8, 32:5}; depth spread = 3",
        },
        {
            "gate_item": "A4 IA-AUD meets >=25% average FLOPs/depth reduction at similar NMSE",
            "status": "oracle-upper-bound-inconclusive / global-target-not-met",
            "evidence": "stage3_a4_oracle_earlystop",
            "metric": "overall oracle savings = 15.0%; L=32 savings = 27.5%; mean NMSE gap = 0.1820 dB",
        },
        {
            "gate_item": "A4 high-L/platform gate meets >=25% depth reduction at similar NMSE",
            "status": "restricted-high-l-pass / global-claim-not-supported",
            "evidence": "stage3_a4_high_l_plateau_gate",
            "metric": "held-out L=32 gate savings = 33.33%; NMSE gap = 0.3643 dB",
        },
        {
            "gate_item": "A5 phase-noise-only HIR-JL has strong value",
            "status": "pre-smoke-downgrade",
            "evidence": "stage3_a5_hirjl_presmoke",
            "metric": "degradation at 1 deg = 0.0000 dB; degradation at 2 deg = 0.0000 dB",
        },
        {
            "gate_item": "A5 combined-impairment HIR-JL still needs one check",
            "status": "stress-only-supported / main-gate-downgrade",
            "evidence": "stage3_a5_combined_impairment_presmoke",
            "metric": "v2.3R combined degradation = 4.4395 dB; high-stress degradation = 6.6036 dB",
        },
    ]
    output_dir = ROOT / "05_results" / "stage3_presmoke_manifest"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "stage3_presmoke_manifest.json").write_text(
        json.dumps(
            {
                "runs": {
                    "stage3_a4_depth_presmoke": a4_depth,
                    "stage3_a4_oracle_earlystop": a4_oracle,
                    "stage3_a4_high_l_plateau_gate": a4_high_l_gate,
                    "stage3_a5_hirjl_presmoke": a5_hirjl,
                    "stage3_a5_combined_impairment_presmoke": a5_combined,
                },
                "gate_rows": rows,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    lines = [
        "# Stage 3 Pre-Smoke Manifest",
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
            "Stage 3 pre-smoke evidence supports a narrowed A4 narrative: adaptive-depth opportunity exists, the global >=25% average depth/FLOPs target is not proven, but a high-L plateau gate reaches 33.33% held-out depth savings within 0.3643 dB of fixed K=8. A4 should be framed as a high-L/platform-sample early-stop mechanism, not a global IA-AUD claim.",
            "",
            "The combined-impairment check does not meet the 5 dB nominal v2.3R main-gate threshold, but high stress does expose a 6.6036 dB failure mode. Recommendation: remove A5 from the main Stage-3 gate and keep it as an appendix/high-stress robustness analysis.",
            "",
        ]
    )
    (output_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
