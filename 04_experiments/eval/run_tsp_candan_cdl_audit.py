"""Evaluate the axis-wise Candan comparator on the frozen CDL test geometry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

import numpy as np
from scipy.stats import t as student_t
from sionna.phy import config as sionna_config


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_active_modules"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from baseline.local_refinement import axiswise_candan_bins  # noqa: E402
from common.manifest import write_run_manifest  # noqa: E402
from common.seed import seed_all  # noqa: E402
from common.tsp_revision_metrics import (  # noqa: E402
    write_csv,
    write_release_metadata,
)
from tompnet.feature_controller import apply_nyquist_alias_lock  # noqa: E402
from run_sionna_cdl_profile_generalization import (  # noqa: E402
    add_awgn,
    generate_profile_channels,
    reconstruct_fft_topk,
)
from run_sionna_cdl_trained_refinement import (  # noqa: E402
    estimate_from_bins_lstsq,
    nmse_db,
    support_to_bins,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profiles", nargs="+", default=["A", "C", "D"])
    parser.add_argument("--snrs", nargs="+", type=float, default=[0.0, 10.0, 20.0, 30.0])
    parser.add_argument("--l-values", nargs="+", type=int, default=[4, 8, 16])
    parser.add_argument(
        "--test-seeds",
        nargs="+",
        type=int,
        default=[20260628, 20260629, 20260630, 20260701, 20260702],
    )
    parser.add_argument("--samples-per-profile-seed", type=int, default=50)
    parser.add_argument("--num-subcarriers", type=int, default=64)
    parser.add_argument("--num-tx-antennas", type=int, default=4)
    parser.add_argument("--spatial-truth-oversampling", type=int, default=4096)
    parser.add_argument("--subcarrier-spacing-hz", type=float, default=120e3)
    parser.add_argument("--carrier-frequency-hz", type=float, default=60e9)
    parser.add_argument("--delay-spread-s", type=float, default=100e-9)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--output-dir-name", default="tsp_candan_cdl_audit_paper")
    return parser.parse_args()


def seed_mean_ci(rows: list[dict[str, object]], key: str) -> tuple[float, float, float]:
    seed_means = np.asarray(
        [
            np.mean([float(row[key]) for row in rows if int(row["seed"]) == seed])
            for seed in sorted({int(row["seed"]) for row in rows})
        ],
        dtype=float,
    )
    center = float(np.mean(seed_means))
    half = float(
        student_t.ppf(0.975, len(seed_means) - 1)
        * np.std(seed_means, ddof=1)
        / np.sqrt(len(seed_means))
    )
    return center, center - half, center + half


def main() -> None:
    args = parse_args()
    started = time.perf_counter()
    rows: list[dict[str, object]] = []
    for profile in args.profiles:
        for seed in args.test_seeds:
            seed_all(seed)
            sionna_config.seed = seed
            rng = np.random.default_rng(seed + 1000 * (ord(profile[0]) - ord("A") + 1))
            clean_batch, _, _, _ = generate_profile_channels(
                profile=profile,
                batch_size=args.samples_per_profile_seed,
                num_subcarriers=args.num_subcarriers,
                subcarrier_spacing_hz=args.subcarrier_spacing_hz,
                carrier_frequency_hz=args.carrier_frequency_hz,
                delay_spread_s=args.delay_spread_s,
                num_tx_antennas=args.num_tx_antennas,
                spatial_truth_oversampling=args.spatial_truth_oversampling,
                device=args.device,
            )
            for snr_db in args.snrs:
                noisy_batch = [add_awgn(clean, snr_db=snr_db, rng=rng)[0] for clean in clean_batch]
                for l_value in args.l_values:
                    for sample_index, (clean, noisy) in enumerate(zip(clean_batch, noisy_batch)):
                        grid_estimate, support, _ = reconstruct_fft_topk(noisy, l_value)
                        coarse_bins = support_to_bins(support, clean.shape)
                        candan_bins = axiswise_candan_bins(noisy, coarse_bins)
                        candan_bins = apply_nyquist_alias_lock(
                            coarse_bins,
                            candan_bins,
                            angle_bin_count=clean.shape[1],
                        )
                        candan_estimate = estimate_from_bins_lstsq(noisy, candan_bins)
                        grid_nmse = nmse_db(grid_estimate, clean)
                        candan_nmse = nmse_db(candan_estimate, clean)
                        rows.append(
                            {
                                "profile": profile,
                                "seed": seed,
                                "snr_db": snr_db,
                                "l_value": l_value,
                                "sample_index": sample_index,
                                "grid_channel_nmse_db": grid_nmse,
                                "candan_channel_nmse_db": candan_nmse,
                                "candan_gain_vs_grid_db": grid_nmse - candan_nmse,
                                "candan_harmful_update": int(candan_nmse > grid_nmse),
                            }
                        )

    summary: list[dict[str, object]] = []
    for profile in args.profiles:
        selected = [row for row in rows if row["profile"] == profile]
        gain, low, high = seed_mean_ci(selected, "candan_gain_vs_grid_db")
        summary.append(
            {
                "profile": profile,
                "scene_count": len(selected),
                "mean_grid_channel_nmse_db": float(
                    np.mean([float(row["grid_channel_nmse_db"]) for row in selected])
                ),
                "mean_candan_channel_nmse_db": float(
                    np.mean([float(row["candan_channel_nmse_db"]) for row in selected])
                ),
                "mean_candan_gain_vs_grid_db": gain,
                "gain_ci95_low_db": low,
                "gain_ci95_high_db": high,
                "harmful_update_rate": float(
                    np.mean([float(row["candan_harmful_update"]) for row in selected])
                ),
            }
        )

    output = ROOT / "05_results" / args.output_dir_name
    output.mkdir(parents=True, exist_ok=True)
    write_csv(output / "per_scene.csv", rows)
    write_csv(output / "profile_summary.csv", summary)
    config = vars(args) | {
        "scene_count": len(rows),
        "elapsed_seconds": time.perf_counter() - started,
    }
    result = {"config": config, "profile_summary": summary}
    (output / "summary.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    command = "python 04_experiments/eval/run_tsp_candan_cdl_audit.py"
    write_release_metadata(
        output,
        config=config,
        seeds=[{"split": "test", "seed": seed} for seed in args.test_seeds],
        command=command,
    )
    write_run_manifest(
        output,
        run_id="tsp_candan_cdl_audit_20260829",
        command=command,
        config=config,
        metrics={"scene_count": len(rows)},
        notes=[
            "Candan and grid use the same FFT top-L support, noisy tensors, periodic coordinates, Nyquist alias lock, and final joint LS convention.",
            "The Candan update uses the published complex three-DFT-sample ratio with the finite-length correction on each axis.",
        ],
        cwd=ROOT,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
