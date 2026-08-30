from __future__ import annotations

import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[2]


def count_files(path: Path, patterns: tuple[str, ...]) -> int:
    if not path.exists():
        return 0
    total = 0
    for pattern in patterns:
        total += sum(1 for item in path.rglob(pattern) if item.is_file())
    return total


def matlab_5g_license() -> dict[str, object]:
    matlab = Path("D:/E/MATLAB/bin/matlab.exe")
    if not matlab.exists():
        return {"matlab_found": False, "fiveg_toolbox_license": False, "raw_output": "MATLAB_NOT_FOUND"}
    command = [
        str(matlab),
        "-batch",
        "disp(['HAS_5G_TOOLBOX=', num2str(license('test','5G_Toolbox'))]); exit",
    ]
    try:
        result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=90)
    except subprocess.TimeoutExpired:
        return {"matlab_found": True, "fiveg_toolbox_license": False, "raw_output": "TIMEOUT"}
    raw = (result.stdout + result.stderr).strip()
    return {
        "matlab_found": True,
        "fiveg_toolbox_license": "HAS_5G_TOOLBOX=1" in raw,
        "raw_output": raw,
    }


def main() -> None:
    reference_root = ROOT / "90_archive" / "2025_thesis_materials" / "参考"
    deepmimo_5gnr = reference_root / "DeepMIMO-5GNR"
    deepmimo_dataset = deepmimo_5gnr / "DeepMIMO_dataset"
    deepmimo_legacy = reference_root / "DeepMIMO-matlab-master"
    cdl_smoke = ROOT / "05_results" / "cdl_profile_generalization_smoke" / "summary.md"
    deepmimo_audit = ROOT / "05_results" / "deepmimo_set_e_access_audit" / "summary.md"
    dataset_files = count_files(deepmimo_dataset, ("*.mat", "*.h5", "*.hdf5", "*.npy", "*.npz"))
    o1_hits = count_files(reference_root, ("*O1*", "*O1_60*"))
    i3_hits = count_files(reference_root, ("*I3*", "*I3_60*"))
    license_info = matlab_5g_license()
    readiness = (
        "ready"
        if dataset_files > 0 and license_info["fiveg_toolbox_license"]
        else "partial_external_dependency"
    )
    payload = {
        "readiness": readiness,
        "matlab": license_info,
        "deepmimo": {
            "reference_root_exists": reference_root.exists(),
            "deepmimo_5gnr_exists": deepmimo_5gnr.exists(),
            "deepmimo_legacy_exists": deepmimo_legacy.exists(),
            "dataset_files": dataset_files,
            "o1_asset_hits": o1_hits,
            "i3_asset_hits": i3_hits,
        },
        "existing_smokes": {
            "cdl_profile_generalization_smoke": cdl_smoke.exists(),
            "deepmimo_set_e_access_audit": deepmimo_audit.exists(),
        },
    }
    output_dir = ROOT / "05_results" / "stage1_dependency_audit"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "stage1_dependency_audit.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    lines = [
        "# Stage 1 Dependency Audit",
        "",
        f"- Readiness: `{readiness}`",
        f"- MATLAB found: `{license_info['matlab_found']}`",
        f"- 5G Toolbox license available: `{license_info['fiveg_toolbox_license']}`",
        f"- DeepMIMO dataset files: `{dataset_files}`",
        f"- O1/O1_60 asset hits: `{o1_hits}`",
        f"- I3/I3_60 asset hits: `{i3_hits}`",
        f"- CDL-like smoke summary present: `{cdl_smoke.exists()}`",
        f"- DeepMIMO access audit present: `{deepmimo_audit.exists()}`",
        "",
        "## Interpretation",
        "",
        "The local code and previous smoke/audit files are present, but standards-aligned CDL/DeepMIMO G1 evidence is not ready on this machine because the 5G Toolbox license check fails and no DeepMIMO scenario dataset files are installed.",
        "",
        "Pack 3 should remain gated unless this dependency gate is explicitly waived or replaced by a documented surrogate protocol.",
        "",
    ]
    (output_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()

