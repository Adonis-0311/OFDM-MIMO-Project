from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Any, Optional, Union

try:
    import yaml
except ModuleNotFoundError:
    yaml = None


@dataclass(frozen=True)
class GridConfig:
    angle_bins: int = 16
    delay_bins: int = 8
    doppler_bins: int = 8


@dataclass(frozen=True)
class ExperimentConfig:
    seed: int = 20260624
    snr_db: float = 20.0
    n_targets: int = 3
    n_trials: int = 32
    max_iters: Optional[int] = None
    grid: GridConfig = field(default_factory=GridConfig)

    @classmethod
    def load(cls, path: Union[str, Path]) -> "ExperimentConfig":
        raw = Path(path).read_text(encoding="utf-8")
        if yaml is not None:
            data = yaml.safe_load(raw)
        else:
            data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("Configuration file must contain a mapping.")
        grid_data = data.pop("grid", {})
        if grid_data is None:
            grid_data = {}
        return cls(grid=GridConfig(**grid_data), **data)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def stable_hash(self) -> str:
        payload = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def config_hash(config: Union[ExperimentConfig, dict[str, Any]]) -> str:
    payload = asdict(config) if hasattr(config, "__dataclass_fields__") else config
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:12]
