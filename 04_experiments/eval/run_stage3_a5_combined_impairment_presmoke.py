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
from data.impairments import apply_iq_imbalance, apply_mutual_coupling, apply_phase_noise
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
class ImpairmentProfile:
    name: str
    sigma_phi_degrees: float
    iq_gain: float
    iq_phase_degrees: float
    coupling_rho: float
    coupling_phi0_degrees: float


@dataclass(frozen=True)
class PreparedProfileSample:
    profile: ImpairmentProfile
    sample_index: int
    n_targets: int
    measurement: np.ndarray
    clean: np.ndarray
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


def apply_profile(
    measurement: np.ndarray,
    profile: ImpairmentProfile,
    rng: np.random.Generator,
) -> np.ndarray:
    impaired = measurement
    if profile.sigma_phi_degrees > 0:
        impaired = apply_phase_noise(impaired, profile.sigma_phi_degrees, rng)
    if profile.iq_gain != 1.0 or profile.iq_phase_degrees != 0.0:
        impaired = apply_iq_imbalance(impaired, profile.iq_gain, profile.iq_phase_degrees)
    if profile.coupling_rho > 0:
        impaired = apply_mutual_coupling(
            impaired,
            rho=profile.coupling_rho,
            phi0_degrees=profile.coupling_phi0_degrees,
            axis=0,
        )
    return impaired


def prepare_profile_sample(
    sample: OffgridTensorSample,
    *,
    profile: ImpairmentProfile,
    sample_index: int,
    n_targets: int,
    rng: np.random.Generator,
    search_radius: float,
    search_points: int,
) -> PreparedProfileSample:
    measurement = apply_profile(sample.measurement, profile, rng)
    coarse = topk_grid_bins(measurement, n_targets)
    refined = refine_bins_local(
        measurement,
        sample.shape,
        coarse,
        search_radius=search_radius,
        search_points=search_points,
    )
    return PreparedProfileSample(
        profile=profile,
        sample_index=sample_index,
        n_targets=n_targets,
        measurement=measurement,
        clean=sample.clean,
        coarse_bins=coarse,
        refined_bins=refined,
        shape=sample.shape,
    )


def evaluate_alpha(prepared: PreparedProfileSample, alpha: float) -> float:
    bins = interpolate_bins(prepared.coarse_bins, prepared.refined_bins, alpha)
    estimate = estimate_from_bins_lstsq(prepared.measurement, prepared.shape, bins)
    return measurement_nmse_db(estimate, prepared.clean)


def train_alpha(samples: list[PreparedProfileSample], candidate_alphas: np.ndarray) -> AlphaFit:
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
    v23r_degradation: float,
    high_degradation: float,
    v23r_oracle_recovery: float,
    elapsed_seconds: float,
) -> Path:
    if v23r_degradation >= 5.0:
        status = "supported"
        interpretation = "combined v2.3R stress creates a large enough failure mode to justify HIR-JL robust training."
        next_action = "Keep A5 as a Stage-3 robust-training line and implement HIR-JL against combined impairments."
    elif high_degradation >= 5.0:
        status = "stress-only-supported"
        interpretation = "nominal v2.3R combined stress is weak, but high stress exposes a failure mode; A5 should be appendix or stress-analysis rather than a main gate."
        next_action = "Downgrade A5 from the main gate, but keep a high-stress appendix robustness check."
    else:
        status = "downgrade"
        interpretation = "even combined impairment does not produce a strong degradation signal in this pre-smoke."
        next_action = "Remove A5 from the main Stage-3 line and prioritize A4 plus paper-scale Kruskal/DeepMIMO evidence."
    lines = [
        "# Stage 3 A5 Combined-Impairment Pre-Smoke Evaluation Summary",
        "",
        "## Outcome Summary",
        "",
        (
            "This pre-smoke tests whether phase noise, IQ imbalance, and physical mutual "
            "coupling together create a large enough failure mode to justify HIR-JL robust "
            "training after phase-noise-only stress showed negligible degradation."
        ),
        "",
        "## evaluation_summary",
        "",
        "- `research_question`: Do combined hardware impairments create enough NMSE degradation to keep A5/HIR-JL in the main Stage-3 line?",
        f"- `claim_update`: {status} for A5/HIR-JL combined-impairment evidence.",
        "- `baseline_relation`: Clean-trained bounded refinement is compared against clean performance, impaired grid Tensor-OMP, and oracle-retuned alpha per profile.",
        "- `failure_mode`: No execution failure; remaining limitation is synthetic impairment profile realism and small pre-smoke sample count.",
        f"- `mechanism_note`: {interpretation}",
        f"- `next_action`: {next_action}",
        "- `evidence_level`: Stage-3 pre-smoke evidence only.",
        "",
        "## Key Metrics",
        "",
        f"- v2.3R combined degradation: {v23r_degradation:.4f} dB",
        f"- high-stress combined degradation: {high_degradation:.4f} dB",
        f"- v2.3R oracle-retune recovery: {v23r_oracle_recovery:.4f} dB",
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
    candidate_alphas = np.linspace(0.0, 1.2, 7)
    profiles = [
        ImpairmentProfile("clean", 0.0, 1.0, 0.0, 0.0, 0.0),
        ImpairmentProfile("phase_only_2deg", 2.0, 1.0, 0.0, 0.0, 0.0),
        ImpairmentProfile("iq_coupling_medium", 0.0, 1.05, 3.0, 0.2, 5.0),
        ImpairmentProfile("combined_v23r", 2.0, 1.05, 3.0, 0.2, 5.0),
        ImpairmentProfile("combined_high", 3.0, 1.10, 5.0, 0.3, 10.0),
    ]
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
    clean_profile = profiles[0]
    clean_train = [
        prepare_profile_sample(
            sample,
            profile=clean_profile,
            sample_index=index,
            n_targets=n_targets,
            rng=rng,
            search_radius=search_radius,
            search_points=search_points,
        )
        for index, sample in enumerate(base_train)
    ]
    clean_fit = train_alpha(clean_train, candidate_alphas)

    rows: list[dict[str, float | str]] = []
    sample_rows: list[dict[str, float | str]] = []
    clean_nmse = float("nan")
    degradation_by_profile: dict[str, float] = {}
    oracle_recovery_by_profile: dict[str, float] = {}
    oracle_alpha_by_profile: dict[str, float] = {}

    for profile_index, profile in enumerate(profiles):
        profile_rng = seed_all(seed + 100 * profile_index + 31)
        prepared_samples = [
            prepare_profile_sample(
                sample,
                profile=profile,
                sample_index=index,
                n_targets=n_targets,
                rng=profile_rng,
                search_radius=search_radius,
                search_points=search_points,
            )
            for index, sample in enumerate(base_test)
        ]
        oracle_fit = train_alpha(prepared_samples, candidate_alphas)
        oracle_alpha_by_profile[profile.name] = oracle_fit.alpha
        grid_values = [evaluate_alpha(sample, 0.0) for sample in prepared_samples]
        clean_alpha_values = [evaluate_alpha(sample, clean_fit.alpha) for sample in prepared_samples]
        oracle_values = [evaluate_alpha(sample, oracle_fit.alpha) for sample in prepared_samples]
        if profile.name == "clean":
            clean_nmse = finite_mean(clean_alpha_values)
        degradation = finite_mean(clean_alpha_values) - clean_nmse
        oracle_recovery = finite_mean(clean_alpha_values) - finite_mean(oracle_values)
        degradation_by_profile[profile.name] = degradation
        oracle_recovery_by_profile[profile.name] = oracle_recovery
        rows.append(
            {
                "profile": profile.name,
                "sigma_phi_degrees": profile.sigma_phi_degrees,
                "iq_gain": profile.iq_gain,
                "iq_phase_degrees": profile.iq_phase_degrees,
                "coupling_rho": profile.coupling_rho,
                "coupling_phi0_degrees": profile.coupling_phi0_degrees,
                "clean_trained_alpha": clean_fit.alpha,
                "oracle_alpha": oracle_fit.alpha,
                "grid_nmse_db": finite_mean(grid_values),
                "clean_alpha_nmse_db": finite_mean(clean_alpha_values),
                "oracle_alpha_nmse_db": finite_mean(oracle_values),
                "degradation_vs_clean_db": degradation,
                "oracle_recovery_db": oracle_recovery,
                "grid_gap_vs_clean_alpha_db": finite_mean(grid_values) - finite_mean(clean_alpha_values),
                "n_test": float(len(prepared_samples)),
            }
        )
        for sample, grid, clean_alpha_value, oracle_value in zip(
            prepared_samples, grid_values, clean_alpha_values, oracle_values
        ):
            sample_rows.append(
                {
                    "profile": profile.name,
                    "sample_index": float(sample.sample_index),
                    "n_targets": float(n_targets),
                    "clean_trained_alpha": clean_fit.alpha,
                    "oracle_alpha": oracle_fit.alpha,
                    "grid_nmse_db": grid,
                    "clean_alpha_nmse_db": clean_alpha_value,
                    "oracle_alpha_nmse_db": oracle_value,
                    "degradation_vs_clean_db": clean_alpha_value - clean_nmse,
                    "oracle_recovery_db": clean_alpha_value - oracle_value,
                }
            )

    elapsed_seconds = time.perf_counter() - started
    output_dir = ROOT / "05_results" / "stage3_a5_combined_impairment_presmoke"
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_csv = output_dir / "stage3_a5_combined_impairment_presmoke.csv"
    with summary_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    samples_csv = output_dir / "stage3_a5_combined_impairment_presmoke_samples.csv"
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
        "profiles": [profile.__dict__ for profile in profiles],
        "candidate_alphas": candidate_alphas.tolist(),
        "clean_trained_alpha": clean_fit.alpha,
        "clean_train_nmse_db": clean_fit.train_nmse_db,
        "degradation_by_profile_db": degradation_by_profile,
        "oracle_recovery_by_profile_db": oracle_recovery_by_profile,
        "oracle_alpha_by_profile": oracle_alpha_by_profile,
        "elapsed_seconds": elapsed_seconds,
    }
    notes = [
        "Combined-impairment pre-smoke checks whether A5 remains valuable after phase-noise-only stress was weak.",
        "Profiles apply phase noise, IQ imbalance, and physical mutual coupling directly to the measured tensor.",
        "Oracle-retuned alpha per profile is diagnostic only; it is not a robust-training result.",
    ]
    manifest_path = write_run_manifest(
        output_dir,
        run_id="stage3_a5_combined_impairment_presmoke_20260624",
        command="python 04_experiments/eval/run_stage3_a5_combined_impairment_presmoke.py",
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
            "profiles": [profile.__dict__ for profile in profiles],
            "candidate_alphas": candidate_alphas.tolist(),
        },
        metrics=metrics,
        notes=notes,
        cwd=ROOT,
    )
    summary_path = write_summary_md(
        output_dir,
        title="Stage 3 A5 Combined-Impairment Pre-Smoke",
        config_hash="stage3-a5-combined-impairment-presmoke-20260624",
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
        v23r_degradation=degradation_by_profile["combined_v23r"],
        high_degradation=degradation_by_profile["combined_high"],
        v23r_oracle_recovery=oracle_recovery_by_profile["combined_v23r"],
        elapsed_seconds=elapsed_seconds,
    )
    print(f"Wrote {summary_csv.relative_to(ROOT)}")
    print(f"Wrote {samples_csv.relative_to(ROOT)}")
    print(f"Wrote {summary_path.relative_to(ROOT)}")
    print(f"Wrote {manifest_path.relative_to(ROOT)}")
    print(f"Wrote {evaluation_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
