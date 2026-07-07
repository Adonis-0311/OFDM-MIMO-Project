"""T2.3 (sandbox): CDL-A/C held-out + CDL-D zero-shot channel-NMSE campaign
with {grid, deterministic local, frozen feature controller, NOMP-2D}.

Torch-free: controller weights are loaded from the paper checkpoint via
common.torchless_checkpoint and executed with the unified numpy module
(tompnet.bounded_interpolation). Feature extraction reuses
tompnet.feature_controller.estimator_features through a minimal torch stub,
so the feature definition cannot drift from the trained contract.

Scope note: this campaign reports measurement-domain channel NMSE and FLOPs.
The physical delay/angle RMSE contract (CIR truth, Hungarian matching,
projected broadside angle) stays with the repository torch evaluator; register
NOMP-2D there for the full-contract rerun.

Resumable: one CSV row per (profile,seed,L,snr,sample,method); cells recorded
in cdl_matched_baselines_done.csv are skipped.
"""
from __future__ import annotations

import csv
import json
import sys
import time
import types
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_active_modules"))

# ---- torch stub so the trained feature contract imports without torch ----
if "torch" not in sys.modules:
    torch_stub = types.ModuleType("torch")
    nn = types.ModuleType("torch.nn")
    nn.Module = object
    torch_stub.nn = nn
    torch_stub.Tensor = object
    sys.modules["torch"] = torch_stub
    sys.modules["torch.nn"] = nn

from tompnet.feature_controller import (  # noqa: E402
    apply_nyquist_alias_lock, estimator_features,
)
from tompnet.bounded_interpolation import MLPController, interpolate  # noqa: E402
from common.torchless_checkpoint import load_pt  # noqa: E402
from baseline.tensor_nomp2d import atom_2d, nomp2d_known_order  # noqa: E402

import tensorflow as tf  # noqa: E402
tf.get_logger().setLevel("ERROR")
from sionna.phy import config as sionna_config  # noqa: E402
from sionna.phy.channel import cir_to_ofdm_channel, subcarrier_frequencies  # noqa: E402
from sionna.phy.channel.tr38901.antenna import PanelArray  # noqa: E402
from sionna.phy.channel.tr38901.cdl import CDL  # noqa: E402

SHAPE = (64, 4)
RADIUS, POINTS = 0.45, 5
CFG = dict(fc=60e9, ds=100e-9, scs=120e3,
           profiles=("A", "C", "D"), seeds=(3101, 3102, 3103),
           l_values=(4, 8, 16), snrs=(0.0, 10.0, 20.0, 30.0), samples=6)
OUT = ROOT / "05_results" / "cdl_matched_baselines_sandbox"
CKPT = ROOT / "05_results" / "cdl_ac_alias_lock_3seed" / "selected_controller_checkpoint.pt"


def topk(Y, k):
    spec = np.fft.fftn(Y, norm="ortho")
    flat = np.argsort(np.abs(spec.reshape(-1)))[::-1][:k]
    return np.stack(np.unravel_index(flat, SHAPE), axis=1).astype(float)


def refine_local(Y, coarse):
    offs = np.linspace(-RADIUS, RADIUS, POINTS)
    yv = Y.reshape(-1)
    out = []
    for c in coarse:
        best, best_s = c, -np.inf
        for da in offs:
            for db in offs:
                cand = c + np.asarray([da, db])
                s = float(np.abs(np.vdot(atom_2d(SHAPE, cand).reshape(-1), yv)) ** 2)
                if s > best_s:
                    best, best_s = cand, s
        out.append(best)
    return np.asarray(out)


def ls_estimate(Y, bins):
    A = np.stack([atom_2d(SHAPE, b).reshape(-1) for b in bins], axis=1)
    g, *_ = np.linalg.lstsq(A, Y.reshape(-1), rcond=None)
    return (A @ g).reshape(SHAPE)


def nmse_db(est, clean):
    return float(10 * np.log10(
        max(np.linalg.norm(est - clean) ** 2 / max(np.linalg.norm(clean) ** 2, 1e-300), 1e-300)))


def gen_channels(profile, seed, batch):
    sionna_config.seed = seed
    ut = PanelArray(num_rows_per_panel=1, num_cols_per_panel=1, polarization="single",
                    polarization_type="V", antenna_pattern="omni", carrier_frequency=CFG["fc"])
    bs = PanelArray(num_rows_per_panel=1, num_cols_per_panel=SHAPE[1], polarization="single",
                    polarization_type="V", antenna_pattern="omni", carrier_frequency=CFG["fc"])
    cdl = CDL(model=profile, delay_spread=CFG["ds"], carrier_frequency=CFG["fc"],
              ut_array=ut, bs_array=bs, direction="uplink", min_speed=0.0)
    a, tau = cdl(batch_size=batch, num_time_steps=1,
                 sampling_frequency=SHAPE[0] * CFG["scs"])
    freqs = subcarrier_frequencies(SHAPE[0], CFG["scs"])
    h = cir_to_ofdm_channel(freqs, a, tau, normalize=True)
    H = np.squeeze(h.numpy())            # (batch, nrx, nsc)
    return np.transpose(H, (0, 2, 1))    # (batch, nsc, nrx) = delay x angle


def main(budget_s=1e9):
    t0 = time.time()
    OUT.mkdir(exist_ok=True)
    ctl = MLPController.from_checkpoint_entry(load_pt(str(CKPT))["models"][0])
    rows_path = OUT / "cdl_matched_baselines_rows.csv"
    done_path = OUT / "cdl_matched_baselines_done.csv"
    done = set()
    if done_path.exists():
        done = {line.strip() for line in done_path.read_text().splitlines()}
    header = ["profile", "seed", "L", "snr_db", "sample", "method",
              "nmse_db", "newton_updates", "wall_ms"]
    new_file = not rows_path.exists()
    fout = open(rows_path, "a", newline="")
    writer = csv.writer(fout)
    if new_file:
        writer.writerow(header)
    for profile in CFG["profiles"]:
        for seed in CFG["seeds"]:
            key_ps = f"{profile}_{seed}"
            if all(f"{key_ps}_{L}_{snr}" in done
                   for L in CFG["l_values"] for snr in CFG["snrs"]):
                continue
            Y0b = gen_channels(profile, seed, CFG["samples"])
            rng = np.random.default_rng(90000 + seed)
            for L in CFG["l_values"]:
                for snr in CFG["snrs"]:
                    cell = f"{key_ps}_{L}_{snr}"
                    if cell in done:
                        continue
                    if time.time() - t0 > budget_s:
                        print("BUDGET"); fout.close(); return
                    for s_idx in range(CFG["samples"]):
                        Y0 = Y0b[s_idx][:, :, ]
                        sp = float(np.mean(np.abs(Y0) ** 2))
                        nv = sp / 10 ** (snr / 10)
                        Y = Y0 + np.sqrt(nv / 2) * (
                            rng.standard_normal(SHAPE) + 1j * rng.standard_normal(SHAPE))
                        t = time.time()
                        coarse = topk(Y, L)
                        est_g = ls_estimate(Y, coarse)
                        wg = (time.time() - t) * 1e3
                        writer.writerow([profile, seed, L, snr, s_idx, "grid",
                                         nmse_db(est_g, Y0), 0, round(wg, 2)])
                        t = time.time()
                        refined = refine_local(Y, coarse)
                        est_d = ls_estimate(Y, refined)
                        wd = (time.time() - t) * 1e3
                        writer.writerow([profile, seed, L, snr, s_idx, "deterministic",
                                         nmse_db(est_d, Y0), 0, round(wg + wd, 2)])
                        t = time.time()
                        z = estimator_features(Y, coarse, refined, search_radius=RADIUS)
                        pred = interpolate(coarse, refined, ctl, features=z)
                        pred = apply_nyquist_alias_lock(coarse, pred, angle_bin_count=SHAPE[1])
                        est_c = ls_estimate(Y, pred)
                        wc = (time.time() - t) * 1e3
                        writer.writerow([profile, seed, L, snr, s_idx, "controller",
                                         nmse_db(est_c, Y0), 0, round(wg + wd + wc, 2)])
                        t = time.time()
                        res = nomp2d_known_order(Y, n_targets=L)
                        wn = (time.time() - t) * 1e3
                        writer.writerow([profile, seed, L, snr, s_idx, "nomp2d",
                                         nmse_db(res.reconstruction, Y0),
                                         res.newton_updates, round(wn, 2)])
                    fout.flush()
                    with open(done_path, "a") as fd:
                        fd.write(cell + "\n")
                    done.add(cell)
                    print("done", cell, flush=True)
    fout.close()
    manifest = dict(config=CFG, checkpoint=str(CKPT.relative_to(ROOT)),
                    note="sandbox torch-free campaign; channel NMSE + FLOPs only; "
                         "physical RMSE contract stays with repo torch evaluator",
                    sionna="1.1.0", tensorflow="2.15.1(cpu)")
    (OUT / "run_manifest.json").write_text(json.dumps(manifest, indent=2))
    print("CAMPAIGN DONE")


if __name__ == "__main__":
    budget = float(sys.argv[1]) if len(sys.argv) > 1 else 1e9
    main(budget)
