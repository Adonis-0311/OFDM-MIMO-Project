from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_active_modules"))

from common.manifest import write_run_manifest, write_summary_md
from common.seed import seed_all
from data.impairments import apply_phase_noise
from data.offgrid_tensor import (
    OffgridTensorSample,
    estimate_from_bins_lstsq,
    generate_offgrid_tensor_sample,
    measurement_nmse_db,
    refine_bins_local,
    topk_grid_bins,
)
from tompnet.trainable import interpolate_bins


@dataclass(frozen=True)
class PreparedImpairedSample:
    sample_index: int
    n_targets: int
    sigma_phi_degrees: float
    reference_clean: np.ndarray
    measurement: np.ndarray
    coarse_bins: list[tuple[int, int, int]]
    refined_bins: list[tuple[float, float, float]]
    shape: tuple[int, int, int]


@dataclass(frozen=True)
class AlphaFit:
    alpha: float
    train_nmse_db: float


def finite_mean(values: list[float]) -> float:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    return float(np.mean(arr)) if arr.size else float("nan")


def prepare_impaired_sample(
    sample: OffgridTensorSample,
    *,
    sample_index: int,
    n_targets: int,
    sigma_phi_degrees: float,
    rng: np.random.Generator,
    search_radius: float,
    search_points: int,
) -> PreparedImpairedSample:
    if sigma_phi_degrees > 0:
        measurement = apply_phase_noise(sample.measurement, sigma_phi_degrees, rng)
    else:
        measurement = sample.measurement
    coarse = topk_grid_bins(measurement, n_targets)
    refined = refine_bins_local(
        measurement,
        sample.shape,
        coarse,
        search_radius=search_radius,
        search_points=search_points,
    )
    return PreparedImpairedSample(
        sample_index=sample_index,
        n_targets=n_targets,
        sigma_phi_degrees=sigma_phi_degrees,
        reference_clean=sample.clean,
        measurement=measurement,
        coarse_bins=coarse,
        refined_bins=refined,
        shape=sample.shape,
    )


def evaluate_alpha(prepared: PreparedImpairedSample, alpha: float) -> float:
    bins = interpolate_bins(prepared.coarse_bins, prepared.refined_bins, alpha)
    estimate = estimate_from_bins_lstsq(prepared.measurement, prepared.shape, bins)
    return measurement_nmse_db(estimate, prepared.reference_clean)


def train_alpha(samples: list[PreparedImpairedSample], candidate_alphas: np.ndarray) -> AlphaFit:
    best_alpha = float(candidate_alphas[0])
    best_score = np.inf
    for alpha in candidate_alphas:
        score = finite_mean([evaluate_alpha(sample, float(alpha)) for sample in samples])
        if score < best_score:
            best_score = score
            best_alpha = float(alpha)
    return AlphaFit(alpha=best_alpha, train_nmse_db=best_score)


def write_evaluation_summary(
    output_dir: Path,
    *,
    degradation_at_1: float,
    degradation_at_2: float,
    oracle_recovery_at_2: float,
    elapsed_seconds: float,
) -> Path:
    if degradation_at_1 > 8.0:
        status = "strongly-supported"
        interpretation = "sigma_phi=1 degree already causes severe degradation, so HIR-JL has high expected value."
        next_action = "Implement HIR-JL robust training with phase noise plus physical mutual coupling."
    elif degradation_at_2 <= 1.0:
        status = "downgrade"
        interpretation = "sigma_phi up to 2 degrees barely degrades the clean-trained path, so HIR-JL should be downgraded."
        next_action = "Do not invest in phase-noise-only HIR-JL; run one mutual-coupling/IQ stress check before deciding whether any A5 robust-training line remains."
    else:
        status = "supported"
        interpretation = "phase noise causes measurable degradation, but the value case is moderate rather than overwhelming."
        next_action = "Run a stronger combined-impairment pre-smoke before committing to full HIR-JL robust training."
    lines = [
        "# Stage 3 A5 HIR-JL Phase-Noise Pre-Smoke Evaluation Summary",
        "",
        "## Outcome Summary",
        "",
        (
            "This pre-smoke trains the bounded off-grid refinement alpha on clean samples, "
            "then evaluates the same path under phase-noise stress. It also reports an "
            "oracle-retuned alpha per sigma to separate clean-model fragility from simple "
            "one-parameter recalibration."
        ),
        "",
        "## evaluation_summary",
        "",
        "- `research_question`: Does phase noise create enough NMSE degradation to justify HIR-JL robust training?",
        f"- `claim_update`: {status} for A5/HIR-JL problem-existence evidence.",
        "- `baseline_relation`: Clean-trained bounded refinement is compared against its clean sigma=0 performance, grid Tensor-OMP under the same impairment, and oracle-retuned alpha per sigma.",
        "- `failure_mode`: No execution failure; remaining limitation is phase-noise-only impairment and small pre-smoke sample count.",
        f"- `mechanism_note`: {interpretation}",
        f"- `next_action`: {next_action}",
        "- `evidence_level`: Stage-3 pre-smoke evidence only.",
        "",
        "## Key Metrics",
        "",
        f"- Clean-trained degradation at sigma_phi=1 degree: {degradation_at_1:.4f} dB",
        f"- Clean-trained degradation at sigma_phi=2 degrees: {degradation_at_2:.4f} dB",
        f"- Oracle retuning recovery at sigma_phi=2 degrees: {oracle_recovery_at_2:.4f} dB",
        f"- Wall-clock elapsed time: {elapsed_seconds:.2f} s",
    ]
    path = output_dir / "evaluation_summary.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    shape = (128, 16, 32)
    snr_db = 20.0
    seed = 20260624
    n_targets = 8
    n_train = 4
    n_test = 5
    offset_radius = 0.35
    search_radius = 0.45
    search_points = 5
    sigma_values = [0.0, 0.5, 1.0, 2.0, 3.0]
    candidate_alphas = np.linspace(0.0, 1.2, 7)
    started = time.perf_counter()
    rng = seed_all(seed)

    base_train = [
        generate_offgrid_tensor_sample(
            rng=rng,
            shape=shape,
            n_targets=n_targets,
            snr_db=snr_db,
            offset_radius=offset_radius,
        )
        for _ in range(n_train)
    ]
    base_test = [
        generate_offgrid_tensor_sample(
            rng=rng,
            shape=shape,
            n_targets=n_targets,
            snr_db=snr_db,
            offset_radius=offset_radius,
        )
        for _ in range(n_test)
    ]

    clean_train = [
        prepare_impaired_sample(
            sample,
            sample_index=index,
            n_targets=n_targets,
            sigma_phi_degrees=0.0,
            rng=rng,
            search_radius=search_radius,
            search_points=search_points,
        )
        for index, sample in enumerate(base_train)
    ]
    clean_fit = train_alpha(clean_train, candidate_alphas)

    rows: list[dict[str, float]] = []
    sample_rows: list[dict[str, float]] = []
    clean_tompnet_nmse = float("nan")
    degradation_by_sigma: dict[float, float] = {}
    oracle_recovery_by_sigma: dict[float, float] = {}
    oracle_alpha_by_sigma: dict[float, float] = {}

    for sigma_phi in sigma_values:
        sigma_rng = seed_all(seed + int(sigma_phi * 1000) + 17)
        test_samples = [
            prepare_impaired_sample(
                sample,
                sample_index=index,
                n_targets=n_targets,
                sigma_phi_degrees=sigma_phi,
                rng=sigma_rng,
                search_radius=search_radius,
                search_points=search_points,
            )
            for index, sample in enumerate(base_test)
        ]
        oracle_fit = train_alpha(test_samples, candidate_alphas)
        oracle_alpha_by_sigma[sigma_phi] = oracle_fit.alpha
        grid_values = [evaluate_alpha(sample, 0.0) for sample in test_samples]
        clean_alpha_values = [evaluate_alpha(sample, clean_fit.alpha) for sample in test_samples]
        oracle_values = [evaluate_alpha(sample, oracle_fit.alpha) for sample in test_samples]
        if sigma_phi == 0.0:
            clean_tompnet_nmse = finite_mean(clean_alpha_values)
        degradation = finite_mean(clean_alpha_values) - clean_tompnet_nmse
        oracle_recovery = finite_mean(clean_alpha_values) - finite_mean(oracle_values)
        degradation_by_sigma[sigma_phi] = degradation
        oracle_recovery_by_sigma[sigma_phi] = oracle_recovery
        rows.append(
            {
                "sigma_phi_degrees": sigma_phi,
                "clean_trained_alpha": clean_fit.alpha,
                "oracle_alpha": oracle_fit.alpha,
                "grid_nmse_db": finite_mean(grid_values),
                "clean_alpha_nmse_db": finite_mean(clean_alpha_values),
                "oracle_alpha_nmse_db": finite_mean(oracle_values),
                "degradation_vs_clean_db": degradation,
                "oracle_recovery_db": oracle_recovery,
                "grid_gap_vs_clean_alpha_db": finite_mean(grid_values) - finite_mean(clean_alpha_values),
                "n_test": float(len(test_samples)),
            }
        )
        for sample, grid, clean_alpha_value, oracle_value in zip(
            test_samples, grid_values, clean_alpha_values, oracle_values
        ):
            sample_rows.append(
                {
                    "sample_index": float(sample.sample_index),
                    "n_targets": float(n_targets),
                    "sigma_phi_degrees": sigma_phi,
                    "clean_trained_alpha": clean_fit.alpha,
                    "oracle_alpha": oracle_fit.alpha,
                    "grid_nmse_db": grid,
                    "clean_alpha_nmse_db": clean_alpha_value,
                    "oracle_alpha_nmse_db": oracle_value,
                    "degradation_vs_clean_db": clean_alpha_value - clean_tompnet_nmse,
                    "oracle_recovery_db": clean_alpha_value - oracle_value,
                }
            )

    elapsed_seconds = time.perf_counter() - started
    output_dir = ROOT / "05_results" / "stage3_a5_hirjl_presmoke"
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_csv = output_dir / "stage3_a5_hirjl_presmoke.csv"
    with summary_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    samples_csv = output_dir / "stage3_a5_hirjl_presmoke_samples.csv"
    with samples_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(sample_rows[0].keys()))
        writer.writeheader()
        writer.writerows(sample_rows)

    metrics = {
        "tensor_shape": "128x16x32",
        "snr_db": snr_db,
        "seed": seed,
        "n_targets": n_targets,
        "n_train": n_train,
        "n_test": n_test,
        "sigma_phi_degrees": sigma_values,
        "candidate_alphas": candidate_alphas.tolist(),
        "clean_trained_alpha": clean_fit.alpha,
        "clean_train_nmse_db": clean_fit.train_nmse_db,
        "degradation_by_sigma_db": degradation_by_sigma,
        "oracle_recovery_by_sigma_db": oracle_recovery_by_sigma,
        "oracle_alpha_by_sigma": oracle_alpha_by_sigma,
        "elapsed_seconds": elapsed_seconds,
    }
    notes = [
        "A5 pre-smoke isolates phase-noise stress before full HIR-JL robust training.",
        "Clean-trained alpha is fitted only at sigma_phi=0 and reused under all phase-noise levels.",
        "Oracle-retuned alpha per sigma is reported as a diagnostic; it is not a deployable robust-training result.",
    ]
    manifest_path = write_run_manifest(
        output_dir,
        run_id="stage3_a5_hirjl_presmoke_20260624",
        command="python 04_experiments/eval/run_stage3_a5_hirjl_presmoke.py",
        config={
            "shape": shape,
            "snr_db": snr_db,
            "seed": seed,
            "n_targets": n_targets,
            "n_train": n_train,
            "n_test": n_test,
            "offset_radius": offset_radius,
            "search_radius": search_radius,
            "search_points": search_points,
            "sigma_phi_degrees": sigma_values,
            "candidate_alphas": candidate_alphas.tolist(),
        },
        metrics=metrics,
        notes=notes,
        cwd=ROOT,
    )
    summary_path = write_summary_md(
        output_dir,
        title="Stage 3 A5 HIR-JL Phase-Noise Pre-Smoke",
        config_hash="stage3-a5-hirjl-presmoke-20260624",
        metrics=metrics,
        notes=notes,
        artifacts=[
            str(summary_csv.relative_to(ROOT)),
            str(samples_csv.relative_to(ROOT)),
            str(manifest_path.relative_to(ROOT)),
        ],
    )
    evaluation_path = write_evaluation_summary(
        output_dir,
        degradation_at_1=degradation_by_sigma[1.0],
        degradation_at_2=degradation_by_sigma[2.0],
        oracle_recovery_at_2=oracle_recovery_by_sigma[2.0],
        elapsed_seconds=elapsed_seconds,
    )
    print(f"Wrote {summary_csv.relative_to(ROOT)}")
    print(f"Wrote {samples_csv.relative_to(ROOT)}")
    print(f"Wrote {summary_path.relative_to(ROOT)}")
    print(f"Wrote {manifest_path.relative_to(ROOT)}")
    print(f"Wrote {evaluation_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
