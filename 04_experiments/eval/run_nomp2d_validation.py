"""T2.1 validation gate: NOMP-2D on controlled synthetic delay-angle scenes.

Before the 2-D NOMP-inspired path may be used on CDL observations, it must
(a) beat deterministic bounded local refinement decisively on matched
synthetic 64x4 scenes, and (b) recover known single-target offsets to a small
fraction of a bin. Writes 05_results/nomp2d_validation/summary.json.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_active_modules"))

from baseline.tensor_nomp2d import atom_2d, nomp2d_known_order  # noqa: E402

SHAPE = (64, 4)
RADIUS, POINTS = 0.45, 5


def synth_scene(rng, L, snr_db, offset_radius=0.35):
    n = SHAPE[0] * SHAPE[1]
    flat = rng.choice(n, size=L, replace=False)
    bins0 = np.stack(np.unravel_index(flat, SHAPE), axis=1).astype(float)
    offs = rng.uniform(-offset_radius, offset_radius, size=(L, 2))
    gains = (rng.standard_normal(L) + 1j * rng.standard_normal(L)) / np.sqrt(2)
    clean = np.zeros(SHAPE, complex)
    for b, g in zip(bins0 + offs, gains):
        clean += g * atom_2d(SHAPE, b)
    sp = float(np.mean(np.abs(clean) ** 2))
    nv = sp / 10 ** (snr_db / 10)
    noise = np.sqrt(nv / 2) * (rng.standard_normal(SHAPE) + 1j * rng.standard_normal(SHAPE))
    return clean + noise, clean, bins0 + offs


def topk(Y, k):
    spec = np.fft.fftn(Y, norm="ortho")
    flat = np.argsort(np.abs(spec.reshape(-1)))[::-1][:k]
    return np.stack(np.unravel_index(flat, SHAPE), axis=1).astype(float)


def refine_local(Y, coarse):
    offs = np.linspace(-RADIUS, RADIUS, POINTS)
    out = []
    for c in coarse:
        best, best_s = c, -np.inf
        for da in offs:
            for db in offs:
                cand = c + np.asarray([da, db])
                s = float(np.abs(np.vdot(atom_2d(SHAPE, cand).reshape(-1), Y.reshape(-1))) ** 2)
                if s > best_s:
                    best, best_s = cand, s
        out.append(best)
    return np.asarray(out)


def ls_nmse(Y, bins, clean):
    A = np.stack([atom_2d(SHAPE, b).reshape(-1) for b in bins], axis=1)
    g, *_ = np.linalg.lstsq(A, Y.reshape(-1), rcond=None)
    est = (A @ g).reshape(SHAPE)
    return 10 * np.log10(np.linalg.norm(est - clean) ** 2 / np.linalg.norm(clean) ** 2)


def main():
    rng = np.random.default_rng(20260703)
    rows = []
    for L in (1, 2, 4):
        for snr in (10.0, 20.0, 30.0):
            for trial in range(10):
                Y, clean, truth = synth_scene(rng, L, snr)
                coarse = topk(Y, L)
                det = ls_nmse(Y, refine_local(Y, coarse), clean)
                t0 = time.time()
                res = nomp2d_known_order(Y, n_targets=L)
                wall = time.time() - t0
                nomp = 10 * np.log10(
                    np.linalg.norm(res.reconstruction - clean) ** 2
                    / np.linalg.norm(clean) ** 2)
                # single-target offset recovery check
                bin_err = np.nan
                if L == 1:
                    d = np.abs(res.bins[0] - np.mod(truth[0], SHAPE))
                    d = np.minimum(d, SHAPE - d)
                    bin_err = float(np.max(d))
                rows.append(dict(L=L, snr_db=snr, trial=trial,
                                 det_nmse_db=float(det), nomp_nmse_db=float(nomp),
                                 newton_updates=int(res.newton_updates),
                                 single_target_max_bin_err=bin_err,
                                 wall_s=round(wall, 4)))
    out = ROOT / "05_results" / "nomp2d_validation"
    out.mkdir(exist_ok=True)
    arr = rows
    mean = lambda k, f=lambda r: True: float(np.nanmean([r[k] for r in arr if f(r)]))
    summary = {
        "config": dict(shape=SHAPE, radius=RADIUS, points=POINTS,
                       trials_per_cell=10, L=[1, 2, 4], snr_db=[10, 20, 30]),
        "mean_det_nmse_db": mean("det_nmse_db"),
        "mean_nomp_nmse_db": mean("nomp_nmse_db"),
        "mean_nomp_advantage_db": mean("det_nmse_db") - mean("nomp_nmse_db"),
        "single_target_max_bin_err_p95": float(np.nanpercentile(
            [r["single_target_max_bin_err"] for r in arr if r["L"] == 1], 95)),
        "acceptance": None,
        "rows": rows,
    }
    ok = (summary["mean_nomp_advantage_db"] > 15.0 and
          summary["single_target_max_bin_err_p95"] < 0.05)
    summary["acceptance"] = "PASS" if ok else "FAIL"
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps({k: v for k, v in summary.items() if k != "rows"}, indent=2))


if __name__ == "__main__":
    main()
