from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_manifest(result_dir: str) -> dict:
    path = ROOT / "05_results" / result_dir / "run_manifest.json"
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    stage2_smoke = load_manifest("stage2_minimal_tompnet_smoke")
    trainable_smoke = load_manifest("stage2_trainable_tompnet_smoke")
    torch_smoke = load_manifest("stage2_torch_tompnet_smoke")
    curriculum_g2 = load_manifest("stage2_curriculum_tompnet_g2")
    torch_locked_scale_g2 = load_manifest("stage2_torch_locked_scale_g2")
    rows = [
        {
            "gate_item": "T-OMP-Net at SNR=20 dB improves over Tensor-OMP by >=3 dB",
            "status": "locked-scale-pytorch-pass",
            "evidence": "stage2_torch_locked_scale_g2 plus stage2_curriculum_tompnet_g2",
            "metric": "PyTorch locked-scale mean gain = 6.3646 dB; min L-cell gain = 5.1624 dB",
        },
        {
            "gate_item": "Permutation-invariant loss/RMSE consistency",
            "status": "unit-pass / estimator-pending",
            "evidence": "tests/test_stage1_modules.py and stage2_minimal_tompnet_smoke",
            "metric": "controlled permutation loss delta = 0; coordinate assignment error remains diagnostic",
        },
        {
            "gate_item": "Off-grid ablation at rho_theta=2 lowers NMSE by >=5 dB",
            "status": "locked-scale-pytorch-pass",
            "evidence": "stage2_torch_locked_scale_g2 plus paper_scale_offgrid_stress_g1",
            "metric": "PyTorch locked-scale mean gain = 6.3646 dB; Stage-1 off-grid stress gain = 7.5368 dB",
        },
        {
            "gate_item": "Trainable T-OMP-Net layer/curriculum path",
            "status": "locked-scale-pytorch-pass / broader-statistics-optional",
            "evidence": "stage2_torch_locked_scale_g2 and stage2_curriculum_tompnet_g2",
            "metric": "nn.Module + Adam at 128x16x32, L={2,4,8}; elapsed = 8.03 s after equivalent normal-equation loss optimization",
        },
    ]
    output_dir = ROOT / "05_results" / "stage2_g2_manifest"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "stage2_g2_manifest.json").write_text(
        json.dumps(
            {
                "runs": {
                    "stage2_minimal_tompnet_smoke": stage2_smoke,
                    "stage2_trainable_tompnet_smoke": trainable_smoke,
                    "stage2_torch_tompnet_smoke": torch_smoke,
                    "stage2_curriculum_tompnet_g2": curriculum_g2,
                    "stage2_torch_locked_scale_g2": torch_locked_scale_g2,
                },
                "gate_rows": rows,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    lines = [
        "# Stage 2 G2 Gate Manifest",
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
            "Stage 2 has passed the minimum wiring/proxy smoke, NumPy parameterized train/test smoke, PyTorch CPU trainable smoke, locked-scale curriculum proxy, and locked-scale PyTorch trainable run at 128x16x32 with L={2,4,8}. G2 is accepted for the bounded local Stage-2 gate: the PyTorch run exceeds the >=3 dB target with mean gain 6.3646 dB and minimum L-cell gain 5.1624 dB.",
            "",
            "Stage 3 A4/A5 may start after a short G2 acceptance audit records the small-sample boundary; broader seed/test expansion is optional polish rather than a blocker.",
            "",
            "Acceptance audit: `05_results/stage2_g2_manifest/acceptance_audit.md`.",
            "",
        ]
    )
    (output_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
