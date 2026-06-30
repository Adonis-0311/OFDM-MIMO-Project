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
class SceneConfig:
    name: str
    n_targets: int
    snr_db: float
    offset_radius: float
    n_oracle_train: int
    n_test: int
    seed_offset: int


@dataclass(frozen=True)
class PreparedSample:
    scene_name: str
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


def generate_samples(
    config: SceneConfig,
    *,
    shape: tuple[int, int, int],
    seed: int,
    count: int,
) -> list[OffgridTensorSample]:
    rng = seed_all(seed + config.seed_offset)
    return [
        generate_offgrid_tensor_sample(
            rng=rng,
            shape=shape,
            n_targets=config.n_targets,
            snr_db=config.snr_db,
            offset_radius=config.offset_radius,
        )
        for _ in range(count)
    ]


def prepare_sample(
    sample: OffgridTensorSample,
    *,
    scene_name: str,
    sample_index: int,
    n_targets: int,
    search_radius: float,
    search_points: int,
) -> PreparedSample:
    coarse = topk_grid_bins(sample.measurement, n_targets)
    refined = refine_bins_local(
        sample.measurement,
        sample.shape,
        coarse,
        search_radius=search_radius,
        search_points=search_points,
    )
    return PreparedSample(
        scene_name=scene_name,
        sample_index=sample_index,
        n_targets=n_targets,
        measurement=sample.measurement,
        clean=sample.clean,
        coarse_bins=coarse,
        refined_bins=refined,
        shape=sample.shape,
    )


def prepare_samples(
    samples: list[OffgridTensorSample],
    *,
    scene_name: str,
    n_targets: int,
    search_radius: float,
    search_points: int,
) -> list[PreparedSample]:
    return [
        prepare_sample(
            sample,
            scene_name=scene_name,
            sample_index=index,
            n_targets=n_targets,
            search_radius=search_radius,
            search_points=search_points,
        )
        for index, sample in enumerate(samples)
    ]


def evaluate_alpha(prepared: PreparedSample, alpha: float) -> float:
    bins = interpolate_bins(prepared.coarse_bins, prepared.refined_bins, alpha)
    estimate = estimate_from_bins_lstsq(prepared.measurement, prepared.shape, bins)
    return measurement_nmse_db(estimate, prepared.clean)


def train_alpha(samples: list[PreparedSample], candidate_alphas: np.ndarray) -> AlphaFit:
    best_alpha = float(candidate_alphas[0])
    best_score = np.inf
    for alpha in candidate_alphas:
        score = finite_mean([evaluate_alpha(sample, float(alpha)) for sample in samples])
        if score < best_score:
            best_score = score
            best_alpha = float(alpha)
    return AlphaFit(alpha=best_alpha, train_nmse_db=best_score)


def scene_verdict(min_gain_vs_grid_db: float, max_gap_vs_oracle_db: float) -> tuple[str, str]:
    if min_gain_vs_grid_db >= 3.0 and max_gap_vs_oracle_db <= 1.0:
        return (
            "local-synthetic-pass",
            "source-trained alpha keeps at least 3 dB gain over grid and stays within 1 dB of target-oracle across synthetic target scenes.",
        )
    if min_gain_vs_grid_db > 0.0:
        return (
            "partial",
            "source-trained alpha remains better than grid but does not meet the stronger local portability heuristic.",
        )
    return (
        "not-supported",
        "source-trained alpha does not reliably improve over the grid baseline under these synthetic shifts.",
    )


def write_evaluation_summary(
    output_dir: Path,
    *,
    claim_update: str,
    interpretation: str,
    min_gain_vs_grid_db: float,
    max_gap_vs_oracle_db: float,
    source_alpha: float,
    elapsed_seconds: float,
) -> Path:
    lines = [
        "# Stage 3 Synthetic Cross-Scene Generalization Evaluation Summary",
        "",
        "## Outcome Summary",
        "",
        (
            "This run is a local synthetic cross-scene sanity check for the bounded off-grid "
            "alpha path. It trains alpha on one synthetic source scene and evaluates that "
            "same alpha on held-out synthetic target scenes with lower SNR, larger off-grid "
            "offsets, and higher target count."
        ),
        "",
        "It is not DeepMIMO evidence. DeepMIMO Set E remains externally blocked until O1/I3 scenario data and toolbox readiness are available.",
        "",
        "## evaluation_summary",
        "",
        "- `research_question`: Does a source-trained bounded off-grid alpha retain useful NMSE gain under local synthetic scene shifts?",
        f"- `claim_update`: {claim_update} for local synthetic fallback evidence; no DeepMIMO claim.",
        "- `baseline_relation`: Grid Tensor-OMP alpha=0 is the deployment baseline; source-trained alpha is compared against target-oracle alpha retuned on the target scene.",
        "- `failure_mode`: No execution failure; limitation is synthetic distribution shift rather than external ray-traced DeepMIMO validation.",
        f"- `mechanism_note`: {interpretation}",
        "- `next_action`: Keep this as a fallback sanity row only; rerun the true DeepMIMO Set E channel NMSE plus angle/delay RMSE evaluation once external data/toolbox readiness changes.",
        "- `evidence_level`: Stage-3 local synthetic fallback evidence only.",
        "",
        "## Key Metrics",
        "",
        f"- Source-trained alpha: {source_alpha:.4f}",
        f"- Minimum target gain versus grid: {min_gain_vs_grid_db:.4f} dB",
        f"- Maximum target gap versus target-oracle: {max_gap_vs_oracle_db:.4f} dB",
        f"- Wall-clock elapsed time: {elapsed_seconds:.2f} s",
    ]
    path = output_dir / "evaluation_summary.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    shape = (128, 16, 32)
    seed = 20260624
    search_radius = 0.45
    search_points = 5
    candidate_alphas = np.linspace(0.0, 1.2, 7)
    source_train_count = 3
    source = SceneConfig(
        name="source_l8_snr20_offset035",
        n_targets=8,
        snr_db=20.0,
        offset_radius=0.35,
        n_oracle_train=3,
        n_test=3,
        seed_offset=100,
    )
    scenes = [
        source,
        SceneConfig(
            name="target_l8_snr10_offset035",
            n_targets=8,
            snr_db=10.0,
            offset_radius=0.35,
            n_oracle_train=3,
            n_test=3,
            seed_offset=200,
        ),
        SceneConfig(
            name="target_l8_snr20_offset045",
            n_targets=8,
            snr_db=20.0,
            offset_radius=0.45,
            n_oracle_train=3,
            n_test=3,
            seed_offset=300,
        ),
        SceneConfig(
            name="target_l16_snr20_offset035",
            n_targets=16,
            snr_db=20.0,
            offset_radius=0.35,
            n_oracle_train=2,
            n_test=3,
            seed_offset=400,
        ),
    ]
    started = time.perf_counter()

    source_train_raw = generate_samples(
        source,
        shape=shape,
        seed=seed,
        count=source_train_count,
    )
    source_train = prepare_samples(
        source_train_raw,
        scene_name=f"{source.name}_source_train",
        n_targets=source.n_targets,
        search_radius=search_radius,
        search_points=search_points,
    )
    source_fit = train_alpha(source_train, candidate_alphas)

    rows: list[dict[str, float | str]] = []
    sample_rows: list[dict[str, float | str]] = []
    source_scene_source_alpha_nmse = float("nan")

    for scene in scenes:
        oracle_train_raw = generate_samples(
            scene,
            shape=shape,
            seed=seed,
            count=scene.n_oracle_train,
        )
        test_raw = generate_samples(
            scene,
            shape=shape,
            seed=seed + 5000,
            count=scene.n_test,
        )
        oracle_train = prepare_samples(
            oracle_train_raw,
            scene_name=f"{scene.name}_oracle_train",
            n_targets=scene.n_targets,
            search_radius=search_radius,
            search_points=search_points,
        )
        test_samples = prepare_samples(
            test_raw,
            scene_name=scene.name,
            n_targets=scene.n_targets,
            search_radius=search_radius,
            search_points=search_points,
        )
        oracle_fit = train_alpha(oracle_train, candidate_alphas)
        grid_values = [evaluate_alpha(sample, 0.0) for sample in test_samples]
        source_alpha_values = [evaluate_alpha(sample, source_fit.alpha) for sample in test_samples]
        oracle_values = [evaluate_alpha(sample, oracle_fit.alpha) for sample in test_samples]

        grid_nmse = finite_mean(grid_values)
        source_alpha_nmse = finite_mean(source_alpha_values)
        oracle_nmse = finite_mean(oracle_values)
        if scene.name == source.name:
            source_scene_source_alpha_nmse = source_alpha_nmse
        gain_vs_grid = grid_nmse - source_alpha_nmse
        gap_vs_oracle = source_alpha_nmse - oracle_nmse
        rows.append(
            {
                "scene": scene.name,
                "n_targets": float(scene.n_targets),
                "snr_db": scene.snr_db,
                "offset_radius": scene.offset_radius,
                "source_alpha": source_fit.alpha,
                "oracle_alpha": oracle_fit.alpha,
                "source_train_nmse_db": source_fit.train_nmse_db,
                "oracle_train_nmse_db": oracle_fit.train_nmse_db,
                "grid_nmse_db": grid_nmse,
                "source_alpha_nmse_db": source_alpha_nmse,
                "oracle_alpha_nmse_db": oracle_nmse,
                "gain_vs_grid_db": gain_vs_grid,
                "gap_vs_oracle_db": gap_vs_oracle,
                "degradation_vs_source_scene_db": source_alpha_nmse - source_scene_source_alpha_nmse,
                "n_oracle_train": float(scene.n_oracle_train),
                "n_test": float(scene.n_test),
            }
        )
        for sample, grid, source_alpha_value, oracle_value in zip(
            test_samples, grid_values, source_alpha_values, oracle_values
        ):
            sample_rows.append(
                {
                    "scene": scene.name,
                    "sample_index": float(sample.sample_index),
                    "n_targets": float(scene.n_targets),
                    "snr_db": scene.snr_db,
                    "offset_radius": scene.offset_radius,
                    "source_alpha": source_fit.alpha,
                    "oracle_alpha": oracle_fit.alpha,
                    "grid_nmse_db": grid,
                    "source_alpha_nmse_db": source_alpha_value,
                    "oracle_alpha_nmse_db": oracle_value,
                    "gain_vs_grid_db": grid - source_alpha_value,
                    "gap_vs_oracle_db": source_alpha_value - oracle_value,
                }
            )

    elapsed_seconds = time.perf_counter() - started
    target_rows = [row for row in rows if row["scene"] != source.name]
    min_target_gain = min(float(row["gain_vs_grid_db"]) for row in target_rows)
    max_target_gap = max(float(row["gap_vs_oracle_db"]) for row in target_rows)
    claim_update, interpretation = scene_verdict(min_target_gain, max_target_gap)

    output_dir = ROOT / "05_results" / "stage3_synthetic_cross_scene_generalization"
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_csv = output_dir / "stage3_synthetic_cross_scene_generalization.csv"
    with summary_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    samples_csv = output_dir / "stage3_synthetic_cross_scene_generalization_samples.csv"
    with samples_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(sample_rows[0].keys()))
        writer.writeheader()
        writer.writerows(sample_rows)

    metrics = {
        "tensor_shape": "128x16x32",
        "seed": seed,
        "source_scene": source.name,
        "source_train_count": source_train_count,
        "candidate_alphas": candidate_alphas.tolist(),
        "source_alpha": source_fit.alpha,
        "source_train_nmse_db": source_fit.train_nmse_db,
        "min_target_gain_vs_grid_db": min_target_gain,
        "max_target_gap_vs_oracle_db": max_target_gap,
        "claim_update": claim_update,
        "elapsed_seconds": elapsed_seconds,
    }
    notes = [
        "Local synthetic cross-scene fallback only; not DeepMIMO or ray-traced channel evidence.",
        "Source alpha is fitted once on the source scene and reused unchanged on all target scenes.",
        "Target-oracle alpha is retuned on target train samples and reported only as a diagnostic upper bound.",
    ]
    manifest_path = write_run_manifest(
        output_dir,
        run_id="stage3_synthetic_cross_scene_generalization_20260624",
        command="python 04_experiments/eval/run_stage3_synthetic_cross_scene_generalization.py",
        config={
            "shape": shape,
            "seed": seed,
            "search_radius": search_radius,
            "search_points": search_points,
            "candidate_alphas": candidate_alphas.tolist(),
            "source_train_count": source_train_count,
            "scenes": [scene.__dict__ for scene in scenes],
        },
        metrics=metrics,
        notes=notes,
        cwd=ROOT,
    )
    summary_path = write_summary_md(
        output_dir,
        title="Stage 3 Synthetic Cross-Scene Generalization",
        config_hash="stage3-synthetic-cross-scene-generalization-20260624",
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
        claim_update=claim_update,
        interpretation=interpretation,
        min_gain_vs_grid_db=min_target_gain,
        max_gap_vs_oracle_db=max_target_gap,
        source_alpha=source_fit.alpha,
        elapsed_seconds=elapsed_seconds,
    )
    print(f"Wrote {summary_csv.relative_to(ROOT)}")
    print(f"Wrote {samples_csv.relative_to(ROOT)}")
    print(f"Wrote {summary_path.relative_to(ROOT)}")
    print(f"Wrote {manifest_path.relative_to(ROOT)}")
    print(f"Wrote {evaluation_path.relative_to(ROOT)}")
    print(f"claim_update={claim_update}")
    print(f"min_target_gain_vs_grid_db={min_target_gain:.4f}")
    print(f"max_target_gap_vs_oracle_db={max_target_gap:.4f}")


if __name__ == "__main__":
    main()
