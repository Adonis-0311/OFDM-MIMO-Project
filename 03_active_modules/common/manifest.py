from __future__ import annotations

from dataclasses import asdict, is_dataclass
import json
import platform
import subprocess
from pathlib import Path
from typing import Any, Optional, Union

import numpy as np


def _json_ready(value: Any) -> Any:
    if is_dataclass(value):
        return _json_ready(asdict(value))
    if isinstance(value, dict):
        return {str(k): _json_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(v) for v in value]
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    return value


def git_commit(cwd: Union[Path, str] = ".") -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(cwd),
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def environment_snapshot(cwd: Union[Path, str] = ".") -> dict[str, str]:
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "git_commit": git_commit(cwd),
    }


def write_run_manifest(
    output_dir: Union[str, Path],
    *,
    run_id: str,
    command: str,
    config: Any,
    metrics: dict[str, Any],
    notes: Optional[list[str]] = None,
    cwd: Union[str, Path] = ".",
) -> Path:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    manifest = {
        "run_id": run_id,
        "command": command,
        "config": _json_ready(config),
        "metrics": _json_ready(metrics),
        "environment": environment_snapshot(cwd),
        "notes": notes or [],
    }
    path = output / "run_manifest.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return path


def write_summary_md(
    output_dir: Union[str, Path],
    *,
    title: str,
    config_hash: str,
    metrics: dict[str, Any],
    notes: list[str],
    artifacts: list[str],
) -> Path:
    output = Path(output_dir)
    lines = [
        f"# {title}",
        "",
        f"- Config hash: `{config_hash}`",
        "",
        "## Metrics",
        "",
    ]
    for key, value in metrics.items():
        if isinstance(value, float):
            lines.append(f"- `{key}`: {value:.6g}")
        else:
            lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Notes", ""])
    lines.extend(f"- {note}" for note in notes)
    lines.extend(["", "## Artifacts", ""])
    lines.extend(f"- `{artifact}`" for artifact in artifacts)
    path = output / "summary.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
