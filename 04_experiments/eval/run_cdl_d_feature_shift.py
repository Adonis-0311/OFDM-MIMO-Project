"""T5.1: quantify the CDL-A/C -> CDL-D distribution shift on the 10 controller
features (+ per-sample delay-spread and angular-concentration proxies).

Outputs 05_results/cdl_d_feature_shift/cdl_d_shift.csv with, per feature:
standardized mean difference (SMD, pooled A/C sigma) and the two-sample
Kolmogorov-Smirnov statistic. fig_feature_shift built separately from the CSV.
"""
from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_active_modules"))

if "torch" not in sys.modules:
    torch_stub = types.ModuleType("torch"); nn = types.ModuleType("torch.nn")
    nn.Module = object; torch_stub.nn = nn; torch_stub.Tensor = object
    sys.modules["torch"] = torch_stub; sys.modules["torch.nn"] = nn

from tompnet.feature_controller import FEATURE_NAMES, estimator_features  # noqa: E402
from baseline.tensor_nomp2d import atom_2d  # noqa: E402
from scipy.stats import ks_2samp  # noqa: E402

import tensorflow as tf  # noqa: E402
tf.get_logger().setLevel("ERROR")
from sionna.phy import config as sionna_config  # noqa: E402
from sionna.phy.channel import cir_to_ofdm_channel, subcarrier_frequencies  # noqa: E402
from sionna.phy.channel.tr38901.antenna import PanelArray  # noqa: E402
from sionna.phy.channel.tr38901.cdl import CDL  # noqa: E402

SHAPE = (64, 4); RADIUS, POINTS = 0.45, 5
FC, DS, SCS = 60e9, 100e-9, 120e3
SEEDS = (4101, 4102, 4103); SAMPLES = 20; L = 8; SNR = 20.0
EXTRA = ("rms_delay_spread_bins", "angle_spectrum_concentration")


def gen(profile, seed, batch):
    sionna_config.seed = seed
    ut = PanelArray(num_rows_per_panel=1, num_cols_per_panel=1, polarization="single",
                    polarization_type="V", antenna_pattern="omni", carrier_frequency=FC)
    bs = PanelArray(num_rows_per_panel=1, num_cols_per_panel=SHAPE[1], polarization="single",
                    polarization_type="V", antenna_pattern="omni", carrier_frequency=FC)
    cdl = CDL(model=profile, delay_spread=DS, carrier_frequency=FC,
              ut_array=ut, bs_array=bs, direction="uplink", min_speed=0.0)
    a, tau = cdl(batch_size=batch, num_time_steps=1, sampling_frequency=SHAPE[0] * SCS)
    freqs = subcarrier_frequencies(SHAPE[0], SCS)
    h = cir_to_ofdm_channel(freqs, a, tau, normalize=True)
    return np.transpose(np.squeeze(h.numpy()), (0, 2, 1))


def topk(Y, k):
    spec = np.fft.fftn(Y, norm="ortho")
    flat = np.argsort(np.abs(spec.reshape(-1)))[::-1][:k]
    return np.stack(np.unravel_index(flat, SHAPE), axis=1).astype(float)


def refine_local(Y, coarse):
    offs = np.linspace(-RADIUS, RADIUS, POINTS)
    yv = Y.reshape(-1); out = []
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


def extras(Y):
    # RMS delay spread in delay bins from the delay-domain power profile
    p = np.mean(np.abs(np.fft.ifft(Y, axis=0)) ** 2, axis=1)
    k = np.arange(SHAPE[0])
    mean_k = float(np.sum(k * p) / np.sum(p))
    rms = float(np.sqrt(np.sum(((k - mean_k) ** 2) * p) / np.sum(p)))
    # angular concentration: max/total energy over the 4-bin angle spectrum
    pa = np.mean(np.abs(np.fft.fft(Y, axis=1)) ** 2, axis=0)
    conc = float(np.max(pa) / max(np.sum(pa), 1e-300))
    return rms, conc


def main():
    feats = {p: [] for p in ("A", "C", "D")}
    for profile in feats:
        for seed in SEEDS:
            Y0b = gen(profile, seed, SAMPLES)
            rng = np.random.default_rng(70000 + seed)
            for i in range(SAMPLES):
                Y0 = Y0b[i]
                sp = float(np.mean(np.abs(Y0) ** 2)); nv = sp / 10 ** (SNR / 10)
                Y = Y0 + np.sqrt(nv / 2) * (rng.standard_normal(SHAPE)
                                            + 1j * rng.standard_normal(SHAPE))
                coarse = topk(Y, L)
                refined = refine_local(Y, coarse)
                z = estimator_features(Y, coarse, refined, search_radius=RADIUS)
                rms, conc = extras(Y)
                feats[profile].append(np.concatenate([z, [rms, conc]]))
    names = list(FEATURE_NAMES) + list(EXTRA)
    ac = np.asarray(feats["A"] + feats["C"]); dd = np.asarray(feats["D"])
    out = ROOT / "05_results" / "cdl_d_feature_shift"; out.mkdir(exist_ok=True)
    rows = []
    for j, name in enumerate(names):
        a, b = ac[:, j], dd[:, j]
        pooled = np.sqrt(0.5 * (np.var(a, ddof=1) + np.var(b, ddof=1)))
        smd = float((np.mean(b) - np.mean(a)) / pooled) if pooled > 0 else 0.0
        ks = float(ks_2samp(a, b).statistic) if pooled > 0 else 0.0
        rows.append(dict(feature=name, mean_ac=float(np.mean(a)), mean_d=float(np.mean(b)),
                         smd=smd, ks=ks))
    with open(out / "cdl_d_shift.csv", "w") as f:
        f.write("feature,mean_ac,mean_d,smd,ks\n")
        for r in rows:
            f.write(f"{r['feature']},{r['mean_ac']:.6g},{r['mean_d']:.6g},{r['smd']:.4f},{r['ks']:.4f}\n")
    (out / "run_manifest.json").write_text(json.dumps(dict(
        seeds=SEEDS, samples=SAMPLES, L=L, snr_db=SNR, shape=SHAPE,
        n_ac=len(ac), n_d=len(dd)), indent=2))
    for r in sorted(rows, key=lambda r: -abs(r["smd"])):
        print(f"{r['feature']:32s} SMD {r['smd']:+.2f}  KS {r['ks']:.2f}")


if __name__ == "__main__":
    main()
