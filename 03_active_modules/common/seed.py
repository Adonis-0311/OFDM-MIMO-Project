from __future__ import annotations

import os
import random

import numpy as np


def seed_all(seed: int) -> np.random.Generator:
    """Seed Python, NumPy, and Torch when Torch is available."""
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except Exception:
        pass
    return np.random.default_rng(seed)

