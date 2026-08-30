from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_manifest(result_dir: str) -> dict:
    path = ROOT / "05_results" / result_dir / "run_manifest.json"
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    runs = {
        "stage1_g1_smoke": load_manifest("stage1_g1_smoke"),
        "paper_scale_tensor_omp_g1": load_manifest("paper_scale_tensor_omp_g1"),
        "paper_scale_offgrid_stress_g1": load_manifest("paper_scale_offgrid_stress_g1"),
        "crlb_5l_fim_validation": load_manifest("crlb_5l_fim_validation"),
        "crlb_5l_monte_carlo": load_manifest("crlb_5l_monte_carlo"),
    }
    gate_rows = [
        {
            "gate_item": "Set A -> Tensor-OMP -> metrics -> manifest wiring",
            "status": "pass",
            "evidence": "stage1_g1_smoke",
            "metric": "support recall at 30 dB = 1.0; mean NMSE at 30 dB = -56.8796 dB",
        },
        {
            "gate_item": "Paper-scale on-grid Tensor-OMP scan",
            "status": "pass",
            "evidence": "paper_scale_tensor_omp_g1",
            "metric": "shape 128x16x32; L={2,4,8,16,32,64}; min support recall = 1.0",
        },
        {
            "gate_item": "Paper-scale off-grid bounded refinement stress",
            "status": "pass",
            "evidence": "paper_scale_offgrid_stress_g1",
            "metric": "mean refinement gain = 7.5368 dB; minimum L-cell gain = 6.9946 dB",
        },
        {
            "gate_item": "5L analytic FIM/CRLB implementation validation",
            "status": "pass",
            "evidence": "crlb_5l_fim_validation",
            "metric": "max analytic-vs-finite-difference FIM relative error = 5.7304e-10",
        },
        {
            "gate_item": "Standards-aligned CDL/DeepMIMO wrapper validation",
            "status": "tracked-for-g3",
            "evidence": "stage1_dependency_audit",
            "metric": "not a V2.3R G1 blocker; 5G Toolbox license = false; DeepMIMO dataset files = 0",
        },
        {
            "gate_item": "Final estimator-efficiency Monte Carlo against 5L CRLB",
            "status": "pilot-pass",
            "evidence": "crlb_5l_monte_carlo",
            "metric": "30 dB mean RMSE/CRLB ratio = 1.0067; angle RMSE drops 9.928x from 10 to 30 dB",
        },
    ]
    output_dir = ROOT / "05_results" / "stage1_g1_manifest"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "stage1_g1_manifest.json"
    json_path.write_text(
        json.dumps({"runs": runs, "gate_rows": gate_rows}, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    lines = [
        "# Stage 1 G1 Gate Manifest",
        "",
        "## Gate Status",
        "",
        "| Gate item | Status | Evidence | Metric |",
        "|---|---|---|---|",
    ]
    for row in gate_rows:
        lines.append(
            f"| {row['gate_item']} | {row['status']} | `{row['evidence']}` | {row['metric']} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "G1 is accepted under the V2.3R gate definition. Standards-aligned CDL/DeepMIMO remains tracked for G3 and external-dependency planning.",
            "",
            "Stage 2 / Pack 3 may begin with bounded minimal T-OMP-Net smoke runs.",
            "",
        ]
    )
    (output_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
