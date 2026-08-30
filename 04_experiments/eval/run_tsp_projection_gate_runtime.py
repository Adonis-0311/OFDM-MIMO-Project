"""Verify projection-energy gating and benchmark its complete CPU path."""

from __future__ import annotations

import os

for _name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_name] = "1"

import argparse
import json
from pathlib import Path
import sys
import time

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_active_modules"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from baseline.local_refinement import axiswise_candan_diagnostics  # noqa: E402
from common.manifest import write_run_manifest  # noqa: E402
from common.seed import seed_all  # noqa: E402
from common.tsp_revision_metrics import matched_component_metrics, write_csv, write_release_metadata  # noqa: E402
from data.offgrid_tensor import (  # noqa: E402
    estimate_from_bins_lstsq,
    generate_offgrid_tensor_sample,
    measurement_nmse_db,
    tensor_atom,
    topk_grid_bins,
)
from run_e12_tensor_nomp_matched_pilot import truth_bins  # noqa: E402


METHODS = (
    "axiswise_candan_joint_ls",
    "legacy_explicit_residual_gate",
    "projection_energy_gate",
    "stage1_projection_energy_gate",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shape", type=int, nargs=3, default=(128, 16, 32))
    parser.add_argument("--l-values", type=int, nargs="+", default=(2, 4, 8))
    parser.add_argument("--snrs", type=float, nargs="+", default=(0.0, 10.0, 20.0, 30.0))
    parser.add_argument("--test-seeds", type=int, nargs="+", default=(20260630, 20260701, 20260702, 20260703, 20260704))
    parser.add_argument("--samples-per-cell-seed", type=int, default=20)
    parser.add_argument("--offset-radius", type=float, default=0.35)
    parser.add_argument("--warmup-runs", type=int, default=1)
    parser.add_argument("--timed-repeats", type=int, default=3)
    parser.add_argument("--identity-scenes", type=int, default=60)
    parser.add_argument("--protocol-summary", type=Path, default=ROOT / "05_results" / "tsp_candan_gate_protocol_seventh_round" / "summary.json")
    parser.add_argument("--output-dir-name", default="tsp_projection_gate_runtime_seventh_round")
    return parser.parse_args()


def load_rules(path: Path) -> tuple[float, dict[str, float]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    threshold = float(payload["protocols"]["primary_ac_only_zero_shot_d"]["threshold"])
    stage1 = payload["stage1_rule"]
    return threshold, {
        "minimum_zeta": float(stage1["minimum_zeta"]),
        "maximum_clipping_rate": float(stage1["maximum_clipping_rate"]),
    }


def support_from_spectrum(spectrum: np.ndarray, n_targets: int) -> tuple[np.ndarray, np.ndarray]:
    flat = spectrum.reshape(-1)
    support = np.argpartition(np.abs(flat), -n_targets)[-n_targets:]
    support = support[np.argsort(np.abs(flat[support]))[::-1]]
    bins = np.asarray([np.unravel_index(int(index), spectrum.shape) for index in support], dtype=float)
    return bins, support


def grid_reconstruction_from_spectrum(spectrum: np.ndarray, support: np.ndarray) -> np.ndarray:
    selected = np.zeros(spectrum.size, dtype=np.complex128)
    flat = spectrum.reshape(-1)
    selected[support] = flat[support]
    return np.fft.ifftn(selected.reshape(spectrum.shape), norm="ortho")


def residual_fraction(measurement: np.ndarray, estimate: np.ndarray) -> float:
    return float(np.linalg.norm(measurement - estimate) ** 2 / max(np.linalg.norm(measurement) ** 2, 1e-300))


def qr_projection_energy(measurement: np.ndarray, bins: np.ndarray) -> float:
    design = np.stack(
        [tensor_atom(measurement.shape, tuple(float(v) for v in item)).reshape(-1) for item in bins],
        axis=1,
    )
    q_matrix, _ = np.linalg.qr(design, mode="reduced")
    coefficients = q_matrix.conj().T @ measurement.reshape(-1)
    return float(np.vdot(coefficients, coefficients).real)


def evaluate(
    method: str,
    measurement: np.ndarray,
    clean: np.ndarray,
    truth: np.ndarray,
    n_targets: int,
    threshold: float,
    stage1_rule: dict[str, float],
) -> dict[str, object]:
    fft_start = time.perf_counter_ns()
    if method == "legacy_explicit_residual_gate":
        coarse = np.asarray(topk_grid_bins(measurement, n_targets), dtype=float)
        spectrum = None
        support = None
    else:
        spectrum = np.fft.fftn(measurement, norm="ortho")
        coarse, support = support_from_spectrum(spectrum, n_targets)
    fft_support_ms = (time.perf_counter_ns() - fft_start) / 1e6

    local_start = time.perf_counter_ns()
    diagnostics = axiswise_candan_diagnostics(measurement, coarse)
    candan_bins = diagnostics.bins
    local_update_ms = (time.perf_counter_ns() - local_start) / 1e6

    grid_path_ms = 0.0
    candan_ls_ms = 0.0
    gate_decision_ms = 0.0
    gate_pass = 1
    ls_skipped = 0
    projection_delta = float("nan")

    if method == "axiswise_candan_joint_ls":
        start = time.perf_counter_ns()
        reconstruction = estimate_from_bins_lstsq(
            measurement, measurement.shape, [tuple(item) for item in candan_bins]
        )
        candan_ls_ms = (time.perf_counter_ns() - start) / 1e6
    elif method == "legacy_explicit_residual_gate":
        start = time.perf_counter_ns()
        grid = estimate_from_bins_lstsq(
            measurement, measurement.shape, [tuple(item) for item in coarse]
        )
        grid_path_ms = (time.perf_counter_ns() - start) / 1e6
        start = time.perf_counter_ns()
        candan = estimate_from_bins_lstsq(
            measurement, measurement.shape, [tuple(item) for item in candan_bins]
        )
        candan_ls_ms = (time.perf_counter_ns() - start) / 1e6
        start = time.perf_counter_ns()
        explicit_delta = residual_fraction(measurement, grid) - residual_fraction(measurement, candan)
        gate_pass = int(explicit_delta >= threshold)
        reconstruction = candan if gate_pass else grid
        gate_decision_ms = (time.perf_counter_ns() - start) / 1e6
    elif method in {"projection_energy_gate", "stage1_projection_energy_gate"}:
        assert spectrum is not None and support is not None
        stage1_pass = (
            diagnostics.minimum_denominator_stability >= stage1_rule["minimum_zeta"]
            and diagnostics.clipping_rate <= stage1_rule["maximum_clipping_rate"]
        )
        if method == "stage1_projection_energy_gate" and not stage1_pass:
            start = time.perf_counter_ns()
            reconstruction = grid_reconstruction_from_spectrum(spectrum, support)
            grid_path_ms = (time.perf_counter_ns() - start) / 1e6
            gate_pass = 0
            ls_skipped = 1
        else:
            start = time.perf_counter_ns()
            candan = estimate_from_bins_lstsq(
                measurement, measurement.shape, [tuple(item) for item in candan_bins]
            )
            candan_ls_ms = (time.perf_counter_ns() - start) / 1e6
            start = time.perf_counter_ns()
            grid_energy = float(np.sum(np.abs(spectrum.reshape(-1)[support]) ** 2))
            candan_energy = float(np.vdot(candan, candan).real)
            projection_delta = (candan_energy - grid_energy) / max(float(np.vdot(measurement, measurement).real), 1e-300)
            gate_pass = int(projection_delta >= threshold)
            if gate_pass:
                reconstruction = candan
            else:
                reconstruction = grid_reconstruction_from_spectrum(spectrum, support)
            gate_decision_ms = (time.perf_counter_ns() - start) / 1e6
    else:
        raise ValueError(method)

    total_ms = fft_support_ms + local_update_ms + grid_path_ms + candan_ls_ms + gate_decision_ms
    selected_bins = candan_bins if gate_pass else coarse
    matched = matched_component_metrics(selected_bins, truth, measurement.shape)
    return {
        "measurement_nmse_db": measurement_nmse_db(reconstruction, clean),
        "per_component_half_bin_hit": matched["per_component_hit_rate"],
        "gate_pass": gate_pass,
        "ls_skipped": ls_skipped,
        "projection_delta": projection_delta,
        "minimum_zeta": diagnostics.minimum_denominator_stability,
        "clipping_rate": diagnostics.clipping_rate,
        "fft_support_ms": fft_support_ms,
        "local_update_ms": local_update_ms,
        "grid_path_ms": grid_path_ms,
        "candan_ls_ms": candan_ls_ms,
        "gate_decision_ms": gate_decision_ms,
        "wall_clock_ms": total_ms,
    }


def identity_audit(measurement: np.ndarray, n_targets: int) -> dict[str, float]:
    spectrum = np.fft.fftn(measurement, norm="ortho")
    coarse, support = support_from_spectrum(spectrum, n_targets)
    candan_bins = axiswise_candan_diagnostics(measurement, coarse).bins
    grid = grid_reconstruction_from_spectrum(spectrum, support)
    candan = estimate_from_bins_lstsq(
        measurement, measurement.shape, [tuple(item) for item in candan_bins]
    )
    denominator = max(float(np.vdot(measurement, measurement).real), 1e-300)
    explicit = residual_fraction(measurement, grid) - residual_fraction(measurement, candan)
    grid_energy = float(np.sum(np.abs(spectrum.reshape(-1)[support]) ** 2))
    prediction_energy = float(np.vdot(candan, candan).real)
    qr_energy = qr_projection_energy(measurement, candan_bins)
    projection = (prediction_energy - grid_energy) / denominator
    qr_projection = (qr_energy - grid_energy) / denominator
    return {
        "explicit_delta": explicit,
        "projection_delta": projection,
        "qr_projection_delta": qr_projection,
        "explicit_projection_abs_error": abs(explicit - projection),
        "prediction_qr_abs_energy_error": abs(prediction_energy - qr_energy),
        "projection_qr_abs_error": abs(projection - qr_projection),
    }


def median_timing(records: list[dict[str, object]]) -> dict[str, float]:
    keys = ("fft_support_ms", "local_update_ms", "grid_path_ms", "candan_ls_ms", "gate_decision_ms", "wall_clock_ms")
    return {key: float(np.median([float(row[key]) for row in records])) for key in keys}


def main() -> None:
    args = parse_args()
    threshold, stage1_rule = load_rules(args.protocol_summary)
    shape = tuple(args.shape)
    rows: list[dict[str, object]] = []
    identity_rows: list[dict[str, object]] = []
    scene_number = 0
    started = time.perf_counter()
    for seed in args.test_seeds:
        rng = seed_all(seed)
        for snr_db in args.snrs:
            for n_targets in args.l_values:
                for sample_index in range(args.samples_per_cell_seed):
                    sample = generate_offgrid_tensor_sample(
                        rng=rng, shape=shape, n_targets=n_targets,
                        snr_db=snr_db, offset_radius=args.offset_radius,
                    )
                    truth = truth_bins(sample)
                    if scene_number < args.identity_scenes:
                        identity_rows.append({
                            "scene": scene_number, "seed": seed, "snr_db": snr_db,
                            "n_targets": n_targets, **identity_audit(sample.measurement, n_targets),
                        })
                    order = METHODS[scene_number % len(METHODS):] + METHODS[:scene_number % len(METHODS)]
                    for method in order:
                        for _ in range(args.warmup_runs):
                            evaluate(method, sample.measurement, sample.clean, truth, n_targets, threshold, stage1_rule)
                        repetitions = [
                            evaluate(method, sample.measurement, sample.clean, truth, n_targets, threshold, stage1_rule)
                            for _ in range(args.timed_repeats)
                        ]
                        accuracy = repetitions[0]
                        rows.append({
                            "seed": seed, "snr_db": snr_db, "n_targets": n_targets,
                            "sample_index": sample_index, "method": method,
                            "measurement_nmse_db": accuracy["measurement_nmse_db"],
                            "per_component_half_bin_hit": accuracy["per_component_half_bin_hit"],
                            "gate_pass": accuracy["gate_pass"], "ls_skipped": accuracy["ls_skipped"],
                            "projection_delta": accuracy["projection_delta"],
                            "minimum_zeta": accuracy["minimum_zeta"], "clipping_rate": accuracy["clipping_rate"],
                            **median_timing(repetitions),
                        })
                    scene_number += 1

    summary_rows: list[dict[str, object]] = []
    for method in METHODS:
        selected = [row for row in rows if row["method"] == method]
        summary_rows.append({
            "method": method,
            "scene_count": len(selected),
            "mean_measurement_nmse_db": float(np.mean([float(row["measurement_nmse_db"]) for row in selected])),
            "mean_per_component_half_bin_hit": float(np.mean([float(row["per_component_half_bin_hit"]) for row in selected])),
            "gate_pass_rate": float(np.mean([float(row["gate_pass"]) for row in selected])),
            "candan_ls_skip_rate": float(np.mean([float(row["ls_skipped"]) for row in selected])),
            **{f"median_{key}": value for key, value in median_timing(selected).items()},
        })

    identity_summary = {
        "scene_count": len(identity_rows),
        "maximum_explicit_projection_abs_error": float(max(row["explicit_projection_abs_error"] for row in identity_rows)),
        "maximum_prediction_qr_abs_energy_error": float(max(row["prediction_qr_abs_energy_error"] for row in identity_rows)),
        "maximum_projection_qr_abs_error": float(max(row["projection_qr_abs_error"] for row in identity_rows)),
    }
    output = ROOT / "05_results" / args.output_dir_name
    write_csv(output / "per_scene.csv", rows)
    write_csv(output / "summary.csv", summary_rows)
    write_csv(output / "projection_identity.csv", identity_rows)
    config = vars(args) | {
        "shape": list(shape), "protocol_summary": str(args.protocol_summary),
        "gate_threshold": threshold, "stage1_rule": stage1_rule,
        "thread_count": 1, "dtype": "complex128", "scene_count": scene_number,
        "elapsed_seconds": time.perf_counter() - started,
    }
    result = {"config": config, "projection_identity": identity_summary, "methods": summary_rows}
    output.mkdir(parents=True, exist_ok=True)
    (output / "summary.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    command = "python 04_experiments/eval/run_tsp_projection_gate_runtime.py"
    write_release_metadata(output, config=config, seeds=[{"split": "test", "seed": seed} for seed in args.test_seeds], command=command)
    write_run_manifest(
        output,
        run_id="tsp_projection_gate_runtime_seventh_round_20260829",
        command=command,
        config=config,
        metrics={"scene_count": scene_number, **identity_summary},
        notes=[
            "All methods start from the noisy tensor under a one-thread complex128 protocol.",
            "Projection gating uses FFT support energy and the norm of the Candan LS projection; it never forms two residual tensors.",
            "The Stage-1 rule is frozen from CDL-A/C validation before this synthetic runtime campaign.",
        ],
        cwd=ROOT,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
