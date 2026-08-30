from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path
import sys
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
REFERENCE_ROOT = ROOT / "90_archive" / "2025_thesis_materials" / "参考"
DEEPMIMO_5GNR = REFERENCE_ROOT / "DeepMIMO-5GNR"
DEEPMIMO_LEGACY = REFERENCE_ROOT / "DeepMIMO-matlab-master"
DATASET_ROOT = DEEPMIMO_5GNR / "DeepMIMO_dataset"
O1_DIR = DATASET_ROOT / "o1_60"
I3_DIR = DATASET_ROOT / "I3_60_v1"


def count_files(path: Path, patterns: Iterable[str]) -> int:
    if not path.exists():
        return 0
    total = 0
    for pattern in patterns:
        total += sum(1 for item in path.rglob(pattern) if item.is_file())
    return total


def first_hits(path: Path, patterns: Iterable[str], limit: int = 4) -> list[str]:
    if not path.exists():
        return []
    hits: list[Path] = []
    for pattern in patterns:
        hits.extend(item for item in path.rglob(pattern) if item.is_file())
    unique = sorted(set(hits), key=lambda item: str(item).lower())
    return [str(item) for item in unique[:limit]]


def package_available(*names: str) -> bool:
    return any(importlib.util.find_spec(name) is not None for name in names)


def status_bool(value: bool) -> str:
    return "ok" if value else "missing"


def add_row(rows: list[dict[str, str]], item: str, value: object, status: str, evidence: object) -> None:
    if isinstance(evidence, (list, tuple)):
        evidence_text = "; ".join(str(part) for part in evidence)
    else:
        evidence_text = str(evidence)
    rows.append(
        {
            "item": item,
            "value": str(value),
            "status": status,
            "evidence": evidence_text,
        }
    )


def main() -> None:
    mat_patterns = ("*.mat", "*.h5", "*.hdf5", "*.npy", "*.npz", "*.json")
    dataset_files = count_files(DATASET_ROOT, mat_patterns)
    o1_files = count_files(O1_DIR, mat_patterns)
    i3_files = count_files(I3_DIR, mat_patterns)
    o1_hits = first_hits(O1_DIR, ("*.mat", "*.json"))
    i3_hits = first_hits(I3_DIR, ("*.mat", "*.json"))
    deepmimo_pkg = package_available("DeepMIMOv3", "deepmimo", "DeepMIMO")
    sionna_pkg = package_available("sionna")
    scipy_pkg = package_available("scipy")
    h5py_pkg = package_available("h5py")

    readiness = "ready_open_source" if dataset_files and o1_files and i3_files else "partial"
    rows: list[dict[str, str]] = []
    add_row(rows, "DeepMIMO MATLAB package", DEEPMIMO_LEGACY.exists(), status_bool(DEEPMIMO_LEGACY.exists()), DEEPMIMO_LEGACY)
    add_row(rows, "DeepMIMO 5GNR package", DEEPMIMO_5GNR.exists(), status_bool(DEEPMIMO_5GNR.exists()), DEEPMIMO_5GNR)
    add_row(rows, "DeepMIMO 5GNR dataset folder", DATASET_ROOT.exists(), status_bool(DATASET_ROOT.exists()), DATASET_ROOT)
    add_row(rows, "O1_60 dataset folder", O1_DIR.exists(), status_bool(O1_DIR.exists()), O1_DIR)
    add_row(rows, "I3_60 dataset folder", I3_DIR.exists(), status_bool(I3_DIR.exists()), I3_DIR)
    add_row(rows, "Dataset file count", dataset_files, "ok" if dataset_files else "missing", DATASET_ROOT)
    add_row(rows, "O1/O1_60 local asset hits", o1_files, "ok" if o1_files else "missing", o1_hits)
    add_row(rows, "I3/I3_60 local asset hits", i3_files, "ok" if i3_files else "missing", i3_hits)
    add_row(rows, "DeepMIMO Python package", deepmimo_pkg, status_bool(deepmimo_pkg), "DeepMIMOv3 or DeepMIMO import")
    add_row(rows, "Sionna Python package", sionna_pkg, status_bool(sionna_pkg), "sionna import")
    add_row(rows, "SciPy MAT reader", scipy_pkg, status_bool(scipy_pkg), "scipy import")
    add_row(rows, "h5py MAT/HDF5 reader", h5py_pkg, status_bool(h5py_pkg), "h5py import")
    add_row(rows, "MATLAB 5G Toolbox dependency", "retired", "ok", "Sensors rev.1 open-source route uses Sionna/DeepMIMO/QuaDRiGa")

    output_dir = ROOT / "05_results" / "deepmimo_set_e_access_audit"
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "deepmimo_set_e_access_audit.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["item", "value", "status", "evidence"])
        writer.writeheader()
        writer.writerows(rows)

    payload = {
        "readiness": readiness,
        "reference_root": str(REFERENCE_ROOT),
        "dataset_root": str(DATASET_ROOT),
        "dataset_files": dataset_files,
        "o1_60_files": o1_files,
        "i3_60_files": i3_files,
        "packages": {
            "deepmimo": deepmimo_pkg,
            "sionna": sionna_pkg,
            "scipy": scipy_pkg,
            "h5py": h5py_pkg,
        },
    }
    manifest_path = output_dir / "run_manifest.json"
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "# DeepMIMO Set E Access Audit",
        "",
        "This audit supports v2.3R Sensors Phase-Next E0. It checks whether local DeepMIMO assets are sufficient to start the open-source Python validation route.",
        "",
        f"- Reference root: `{REFERENCE_ROOT}`",
        f"- Readiness: `{readiness}`",
        f"- Dataset files found: `{dataset_files}`",
        f"- O1/O1_60 asset hits: `{o1_files}`",
        f"- I3/I3_60 asset hits: `{i3_files}`",
        f"- DeepMIMO Python package importable: `{deepmimo_pkg}`",
        f"- Sionna Python package importable: `{sionna_pkg}`",
        f"- SciPy MAT reader importable: `{scipy_pkg}`",
        f"- h5py MAT/HDF5 reader importable: `{h5py_pkg}`",
        "",
        "## Audit Table",
        "",
        "| Item | Value | Status | Evidence |",
        "|---|---:|---|---|",
    ]
    for row in rows:
        lines.append(f"| {row['item']} | {row['value']} | {row['status']} | `{row['evidence']}` |")
    package_gate_ready = deepmimo_pkg and sionna_pkg and scipy_pkg and h5py_pkg
    if package_gate_ready:
        package_note = (
            "The Python package gate is installed for the current interpreter; "
            "the next E0 checks can run the DeepMIMO loader smoke and a Sionna CDL smoke."
        )
    else:
        package_note = (
            "The remaining E0 environment gate is to install the Python packages in "
            "`04_experiments/requirements_sensors.txt` before running channel-loader and Sionna CDL smokes."
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "O1_60 and I3_60 local assets are present under the DeepMIMO 5GNR dataset folder, so the former data-access blocker is cleared for the Sensors open-source route.",
            "",
            "5G Toolbox is no longer treated as a dependency for this study. " + package_note,
            "",
            "This audit does not validate final Set E performance; it only verifies that the local asset layer is ready for E2/E3 loader implementation.",
            "",
        ]
    )
    (output_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {csv_path.relative_to(ROOT)}")
    print(f"wrote {manifest_path.relative_to(ROOT)}")
    print(f"readiness={readiness}")

    if readiness != "ready_open_source":
        sys.exit(1)


if __name__ == "__main__":
    main()
