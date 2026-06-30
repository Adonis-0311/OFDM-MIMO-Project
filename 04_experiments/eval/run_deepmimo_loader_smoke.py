from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATASET_ROOT = (
    ROOT
    / "90_archive"
    / "2025_thesis_materials"
    / "参考"
    / "DeepMIMO-5GNR"
    / "DeepMIMO_dataset"
)
O1_DIR = DATASET_ROOT / "o1_60"
I3_DIR = DATASET_ROOT / "I3_60_v1"


def has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def choose_existing(candidates: list[Path]) -> Path | None:
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def whosmat(path: Path) -> tuple[str, list[dict[str, Any]]]:
    if has_module("scipy"):
        try:
            from scipy.io import whosmat as scipy_whosmat

            info = scipy_whosmat(path)
            return (
                "scipy",
                [
                    {
                        "name": name,
                        "shape": "x".join(str(dim) for dim in shape),
                        "class": mat_class,
                    }
                    for name, shape, mat_class in info
                ],
            )
        except NotImplementedError:
            pass
        except Exception as exc:
            return ("scipy_error", [{"name": type(exc).__name__, "shape": "", "class": str(exc)}])
    if has_module("h5py"):
        try:
            import h5py

            with h5py.File(path, "r") as handle:
                return (
                    "h5py",
                    [
                        {
                            "name": key,
                            "shape": "x".join(str(dim) for dim in getattr(value, "shape", ())),
                            "class": type(value).__name__,
                        }
                        for key, value in handle.items()
                    ],
                )
        except Exception as exc:
            return ("h5py_error", [{"name": type(exc).__name__, "shape": "", "class": str(exc)}])
    return ("dependency_missing", [])


def inspect_mat(label: str, path: Path | None) -> dict[str, Any]:
    if path is None:
        return {
            "label": label,
            "status": "missing",
            "path": "",
            "reader": "",
            "variables": [],
            "bytes": 0,
        }
    reader, variables = whosmat(path)
    status = "ok" if variables and not reader.endswith("_error") else reader
    return {
        "label": label,
        "status": status,
        "path": str(path),
        "reader": reader,
        "variables": variables[:8],
        "bytes": path.stat().st_size,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true", help="Exit non-zero unless all smoke reads are ok.")
    args = parser.parse_args()

    o1_delay = choose_existing(sorted(O1_DIR.glob("delay_t*_tx*_r000.mat")))
    o1_power = choose_existing(sorted(O1_DIR.glob("power_t*_tx*_r000.mat")))
    o1_phase = choose_existing(sorted(O1_DIR.glob("phase_t*_tx*_r000.mat")))
    i3_cir = choose_existing(sorted(I3_DIR.glob("I3_60.*.CIR.mat")))
    checks = [
        inspect_mat("O1_60 delay ray file", o1_delay),
        inspect_mat("O1_60 power ray file", o1_power),
        inspect_mat("O1_60 phase ray file", o1_phase),
        inspect_mat("I3_60 CIR file", i3_cir),
    ]
    package_status = {
        "DeepMIMOv3": has_module("DeepMIMOv3"),
        "DeepMIMO": has_module("DeepMIMO"),
        "deepmimo": has_module("deepmimo"),
        "scipy": has_module("scipy"),
        "h5py": has_module("h5py"),
    }
    ok_count = sum(1 for check in checks if check["status"] == "ok")
    status = "ok" if ok_count == len(checks) else "dependency_or_data_gap"

    output_dir = ROOT / "05_results" / "deepmimo_loader_smoke"
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "deepmimo_loader_smoke.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["label", "status", "reader", "path", "bytes", "variables"])
        writer.writeheader()
        for check in checks:
            writer.writerow(
                {
                    "label": check["label"],
                    "status": check["status"],
                    "reader": check["reader"],
                    "path": check["path"],
                    "bytes": check["bytes"],
                    "variables": json.dumps(check["variables"], ensure_ascii=False),
                }
            )

    manifest = {
        "status": status,
        "dataset_root": str(DATASET_ROOT),
        "package_status": package_status,
        "checks": checks,
        "notes": [
            "This smoke validates local O1_60 ray files and I3_60 CIR MAT entry points for the E2/E3 loader path.",
            "Install 04_experiments/requirements_sensors.txt before expecting scipy/h5py/DeepMIMO reads to pass.",
        ],
    }
    manifest_path = output_dir / "run_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")

    lines = [
        "# DeepMIMO Loader Smoke",
        "",
        f"- Status: `{status}`",
        f"- Dataset root: `{DATASET_ROOT}`",
        "",
        "## Package Status",
        "",
    ]
    for name, available in package_status.items():
        lines.append(f"- `{name}`: `{available}`")
    lines.extend(["", "## MAT Entry Points", "", "| Entry | Status | Reader | Bytes | Path |", "|---|---|---|---:|---|"])
    for check in checks:
        lines.append(
            f"| {check['label']} | {check['status']} | {check['reader']} | {check['bytes']} | `{check['path']}` |"
        )
    if status == "ok":
        interpretation = (
            "The local O1_60 and I3_60 MAT entry points were read successfully with SciPy. "
            "Later E2/E3 should wrap these ray/CIR entry points into channel tensors aligned with the T-OMP-Net interface."
        )
    else:
        interpretation = (
            "The local O1_60 and I3_60 file entry points are discoverable. A full read requires SciPy or h5py, "
            "and later E2/E3 should wrap these MAT entry points into channel tensors aligned with the T-OMP-Net interface."
        )
    lines.extend(["", "## Interpretation", "", interpretation, ""])
    (output_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {csv_path.relative_to(ROOT)}")
    print(f"wrote {manifest_path.relative_to(ROOT)}")
    print(f"status={status}")

    if args.strict and status != "ok":
        sys.exit(1)


if __name__ == "__main__":
    main()
