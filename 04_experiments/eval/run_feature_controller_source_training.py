from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_active_modules"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from common.manifest import environment_snapshot
from common.seed import seed_all
from tompnet.feature_controller import (
    FEATURE_NAMES,
    FeatureConditionedRefinementController,
    circular_signed_delta,
    estimator_features,
    match_truth_to_coarse,
)
from run_cdl_geometry_axiswise_source_training import (
    differentiable_nmse,
    make_sample,
)


def finite_mean(values: list[float]) -> float:
    array = np.asarray(values, dtype=float)
    array = array[np.isfinite(array)]
    return float(np.mean(array)) if array.size else float("nan")


def prepare_contract(sample: dict, shape: tuple[int, int], search_radius: float) -> dict:
    coarse = np.asarray(sample["coarse"], dtype=float)
    refined = np.asarray(sample["refined"], dtype=float)
    truth = np.asarray(sample["truth_bins"], dtype=float)
    target = match_truth_to_coarse(coarse, truth, shape=shape)
    local_delta = np.abs(target - coarse)
    local_mask = np.all(local_delta <= 0.75, axis=1)
    return sample | {
        "features": estimator_features(
            np.asarray(sample["measurement"]), coarse, refined,
            search_radius=search_radius,
        ),
        "target_bins": target,
        "local_mask": local_mask,
    }


def sample_loss(
    model: FeatureConditionedRefinementController,
    sample: dict,
    *,
    shape: tuple[int, int],
    feature_mean: torch.Tensor,
    feature_std: torch.Tensor,
    parameter_weight: float,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    features = (torch.as_tensor(sample["features"], dtype=torch.float64) - feature_mean) / feature_std
    alpha = model(features)
    coarse = torch.as_tensor(sample["coarse"], dtype=torch.float64)
    refined = torch.as_tensor(sample["refined"], dtype=torch.float64)
    nmse = differentiable_nmse(
        coarse,
        refined,
        torch.as_tensor(sample["measurement"], dtype=torch.complex128),
        torch.as_tensor(sample["clean"], dtype=torch.complex128),
        shape,
        alpha,
    )
    predicted = coarse + alpha * (refined - coarse)
    nyquist_mask = torch.isclose(
        torch.remainder(coarse[:, 1], shape[1]),
        torch.tensor(shape[1] / 2.0, dtype=torch.float64),
        atol=1e-12,
    )
    predicted = torch.stack(
        [
            predicted[:, 0],
            torch.where(nyquist_mask, coarse[:, 1], predicted[:, 1]),
        ],
        dim=1,
    )
    dynamic_target = match_truth_to_coarse(
        predicted.detach().cpu().numpy(),
        np.asarray(sample["truth_bins"], dtype=float),
        shape=shape,
    )
    target = torch.as_tensor(dynamic_target, dtype=torch.float64)
    delay_loss = torch.nn.functional.smooth_l1_loss(
        predicted[:, 0], target[:, 0], beta=0.5
    )
    predicted_q = torch.remainder(predicted[:, 1] / shape[1] + 0.5, 1.0) - 0.5
    target_q = torch.remainder(target[:, 1] / shape[1] + 0.5, 1.0) - 0.5
    target_angle = torch.rad2deg(
        torch.asin(torch.clamp(2.0 * target_q, -0.999999, 0.999999))
    )
    estimate_u = 2.0 * predicted_q
    candidate_u = torch.stack(
        [estimate_u - 2.0, estimate_u, estimate_u + 2.0], dim=1
    )
    valid = (candidate_u >= -1.0 - 1e-12) & (candidate_u <= 1.0 + 1e-12)
    candidate_angle = torch.rad2deg(
        torch.asin(torch.clamp(candidate_u, -0.999999, 0.999999))
    )
    candidate_error = torch.abs(candidate_angle - target_angle[:, None])
    alias_aware_angle_error = torch.min(
        torch.where(valid, candidate_error, torch.full_like(candidate_error, 1e6)),
        dim=1,
    ).values
    angle_loss = torch.nn.functional.smooth_l1_loss(
        alias_aware_angle_error / 30.0,
        torch.zeros_like(alias_aware_angle_error),
        beta=0.25,
    )
    parameter_loss = delay_loss + angle_loss
    return nmse + parameter_weight * parameter_loss, nmse, parameter_loss


def sample_metrics(
    model: FeatureConditionedRefinementController,
    sample: dict,
    *,
    shape: tuple[int, int],
    feature_mean: torch.Tensor,
    feature_std: torch.Tensor,
) -> dict[str, float]:
    with torch.no_grad():
        features = (torch.as_tensor(sample["features"], dtype=torch.float64) - feature_mean) / feature_std
        alpha = model(features)
        coarse = torch.as_tensor(sample["coarse"], dtype=torch.float64)
        refined = torch.as_tensor(sample["refined"], dtype=torch.float64)
        model_nmse = differentiable_nmse(
            coarse, refined,
            torch.as_tensor(sample["measurement"], dtype=torch.complex128),
            torch.as_tensor(sample["clean"], dtype=torch.complex128),
            shape, alpha,
        )
        grid_nmse = differentiable_nmse(
            coarse, refined,
            torch.as_tensor(sample["measurement"], dtype=torch.complex128),
            torch.as_tensor(sample["clean"], dtype=torch.complex128),
            shape, torch.zeros(2, dtype=torch.float64),
        )
        predicted = coarse + alpha * (refined - coarse)
        nyquist_mask = torch.isclose(
            torch.remainder(coarse[:, 1], shape[1]),
            torch.tensor(shape[1] / 2.0, dtype=torch.float64),
            atol=1e-12,
        )
        predicted = torch.stack(
            [
                predicted[:, 0],
                torch.where(nyquist_mask, coarse[:, 1], predicted[:, 1]),
            ],
            dim=1,
        )
    period = np.asarray(shape, dtype=float)
    truth = np.asarray(sample["truth_bins"], dtype=float)
    coarse_array = np.asarray(sample["coarse"], dtype=float)
    predicted_array = predicted.numpy()
    grid_target = match_truth_to_coarse(coarse_array, truth, shape=shape)
    model_target = match_truth_to_coarse(predicted_array, truth, shape=shape)
    grid_error = circular_signed_delta(coarse_array, grid_target, period)
    model_error = circular_signed_delta(predicted_array, model_target, period)
    def alias_aware_angle_errors(estimate_bins: np.ndarray, target_bins: np.ndarray) -> np.ndarray:
        estimate_q = np.mod(estimate_bins[:, 1] / shape[1] + 0.5, 1.0) - 0.5
        target_q = np.mod(target_bins[:, 1] / shape[1] + 0.5, 1.0) - 0.5
        target_angle = np.degrees(np.arcsin(np.clip(2.0 * target_q, -1.0, 1.0)))
        errors = []
        for q_value, angle_value in zip(estimate_q, target_angle):
            candidate_u = np.asarray([2.0 * q_value - 2.0, 2.0 * q_value, 2.0 * q_value + 2.0])
            candidate_u = candidate_u[
                (candidate_u >= -1.0 - 1e-12) & (candidate_u <= 1.0 + 1e-12)
            ]
            candidate_angles = np.degrees(np.arcsin(np.clip(candidate_u, -1.0, 1.0)))
            errors.append(float(np.min(np.abs(candidate_angles - angle_value))))
        return np.asarray(errors)
    grid_angle_error_deg = alias_aware_angle_errors(coarse_array, grid_target)
    model_angle_error_deg = alias_aware_angle_errors(predicted_array, model_target)
    local_grid_mask = np.all(np.abs(grid_error) <= 0.75, axis=1)
    local_model_mask = np.all(np.abs(model_error) <= 0.75, axis=1)
    if np.any(local_grid_mask) and np.any(local_model_mask):
        local_grid_delay = float(np.sqrt(np.mean(grid_error[local_grid_mask, 0] ** 2)))
        local_model_delay = float(np.sqrt(np.mean(model_error[local_model_mask, 0] ** 2)))
        local_grid_angle = float(np.sqrt(np.mean(grid_error[local_grid_mask, 1] ** 2)))
        local_model_angle = float(np.sqrt(np.mean(model_error[local_model_mask, 1] ** 2)))
    else:
        local_grid_delay = local_model_delay = float("nan")
        local_grid_angle = local_model_angle = float("nan")
    return {
        "delay_alpha": float(alpha[0]),
        "angle_alpha": float(alpha[1]),
        "grid_nmse_db": float(10 * torch.log10(torch.clamp(grid_nmse, min=1e-30))),
        "model_nmse_db": float(10 * torch.log10(torch.clamp(model_nmse, min=1e-30))),
        "grid_delay_rmse_bins": float(np.sqrt(np.mean(grid_error[:, 0] ** 2))),
        "model_delay_rmse_bins": float(np.sqrt(np.mean(model_error[:, 0] ** 2))),
        "grid_angle_rmse_bins": float(np.sqrt(np.mean(grid_error[:, 1] ** 2))),
        "model_angle_rmse_bins": float(np.sqrt(np.mean(model_error[:, 1] ** 2))),
        "grid_angle_rmse_deg": float(np.sqrt(np.mean(grid_angle_error_deg**2))),
        "model_angle_rmse_deg": float(np.sqrt(np.mean(model_angle_error_deg**2))),
        "local_grid_delay_rmse_bins": local_grid_delay,
        "local_model_delay_rmse_bins": local_model_delay,
        "local_grid_angle_rmse_bins": local_grid_angle,
        "local_model_angle_rmse_bins": local_model_angle,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", nargs="+", type=int, default=[20260624, 20260625, 20260626, 20260627, 20260628])
    parser.add_argument("--snrs", nargs="+", type=float, default=[0.0, 10.0, 20.0, 30.0])
    parser.add_argument("--l-values", nargs="+", type=int, default=[4, 8, 16])
    parser.add_argument("--n-train", type=int, default=4)
    parser.add_argument("--n-test", type=int, default=8)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--lr", type=float, default=0.02)
    parser.add_argument("--hidden-dim", type=int, default=16)
    parser.add_argument("--parameter-weight", type=float, default=0.1)
    parser.add_argument("--offset-radius", type=float, default=0.35)
    parser.add_argument("--search-radius", type=float, default=0.45)
    parser.add_argument("--search-points", type=int, default=5)
    parser.add_argument("--output-dir-name", default="feature_controller_source_training")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    shape = (64, 4)
    started = time.perf_counter()
    cell_rows = []
    seed_rows = []
    checkpoint_models = []
    for seed in args.seeds:
        rng = seed_all(seed)
        torch.manual_seed(seed)
        train_samples = []
        test_cells = {}
        for snr_db in args.snrs:
            for l_value in args.l_values:
                train_samples.extend([
                    prepare_contract(make_sample(
                        rng, shape=shape, l_value=l_value, snr_db=snr_db,
                        offset_radius=args.offset_radius, search_radius=args.search_radius,
                        search_points=args.search_points), shape, args.search_radius)
                    for _ in range(args.n_train)
                ])
                test_cells[(snr_db, l_value)] = [
                    prepare_contract(make_sample(
                        rng, shape=shape, l_value=l_value, snr_db=snr_db,
                        offset_radius=args.offset_radius, search_radius=args.search_radius,
                        search_points=args.search_points), shape, args.search_radius)
                    for _ in range(args.n_test)
                ]
        train_feature_array = np.stack([sample["features"] for sample in train_samples])
        feature_mean = torch.as_tensor(train_feature_array.mean(axis=0), dtype=torch.float64)
        feature_std = torch.as_tensor(np.maximum(train_feature_array.std(axis=0), 1e-6), dtype=torch.float64)
        model = FeatureConditionedRefinementController(hidden_dim=args.hidden_dim)
        optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
        history = []
        for _ in range(args.epochs):
            optimizer.zero_grad()
            components = [
                sample_loss(
                    model, sample, shape=shape, feature_mean=feature_mean,
                    feature_std=feature_std, parameter_weight=args.parameter_weight)
                for sample in train_samples
            ]
            loss = torch.stack([item[0] for item in components]).mean()
            loss.backward()
            optimizer.step()
            history.append(float(loss.detach()))
        seed_samples = []
        for (snr_db, l_value), samples in test_cells.items():
            metrics = [sample_metrics(
                model, sample, shape=shape, feature_mean=feature_mean,
                feature_std=feature_std) for sample in samples]
            seed_samples.extend(metrics)
            cell_rows.append({
                "seed": float(seed), "snr_db": float(snr_db), "l_value": float(l_value),
                **{f"mean_{key}": finite_mean([item[key] for item in metrics]) for key in metrics[0]},
            })
        seed_rows.append({
            "seed": float(seed),
            "mean_delay_alpha": finite_mean([item["delay_alpha"] for item in seed_samples]),
            "std_delay_alpha": float(np.std([item["delay_alpha"] for item in seed_samples])),
            "mean_angle_alpha": finite_mean([item["angle_alpha"] for item in seed_samples]),
            "std_angle_alpha": float(np.std([item["angle_alpha"] for item in seed_samples])),
            "mean_nmse_gain_db": finite_mean([item["grid_nmse_db"]-item["model_nmse_db"] for item in seed_samples]),
            "mean_delay_rmse_reduction_bins": finite_mean([item["grid_delay_rmse_bins"]-item["model_delay_rmse_bins"] for item in seed_samples]),
            "mean_angle_rmse_reduction_bins": finite_mean([item["grid_angle_rmse_bins"]-item["model_angle_rmse_bins"] for item in seed_samples]),
            "mean_angle_rmse_reduction_deg": finite_mean([item["grid_angle_rmse_deg"]-item["model_angle_rmse_deg"] for item in seed_samples]),
            "mean_local_delay_rmse_reduction_bins": finite_mean([item["local_grid_delay_rmse_bins"]-item["local_model_delay_rmse_bins"] for item in seed_samples]),
            "mean_local_angle_rmse_reduction_bins": finite_mean([item["local_grid_angle_rmse_bins"]-item["local_model_angle_rmse_bins"] for item in seed_samples]),
            "train_loss_reduction": history[0] - history[-1],
        })
        checkpoint_models.append({
            "seed": seed,
            "state_dict": model.state_dict(),
            "feature_mean": feature_mean,
            "feature_std": feature_std,
        })
    elapsed = time.perf_counter() - started
    metrics = {
        "claim_update": "source-gate-pending",
        "shape": "64x4", "seed_count": float(len(args.seeds)),
        "mean_delay_alpha": finite_mean([row["mean_delay_alpha"] for row in seed_rows]),
        "mean_std_delay_alpha": finite_mean([row["std_delay_alpha"] for row in seed_rows]),
        "mean_angle_alpha": finite_mean([row["mean_angle_alpha"] for row in seed_rows]),
        "mean_std_angle_alpha": finite_mean([row["std_angle_alpha"] for row in seed_rows]),
        "mean_nmse_gain_db": finite_mean([row["mean_nmse_gain_db"] for row in seed_rows]),
        "mean_delay_rmse_reduction_bins": finite_mean([row["mean_delay_rmse_reduction_bins"] for row in seed_rows]),
        "mean_angle_rmse_reduction_bins": finite_mean([row["mean_angle_rmse_reduction_bins"] for row in seed_rows]),
        "mean_angle_rmse_reduction_deg": finite_mean([row["mean_angle_rmse_reduction_deg"] for row in seed_rows]),
        "mean_local_delay_rmse_reduction_bins": finite_mean([row["mean_local_delay_rmse_reduction_bins"] for row in seed_rows]),
        "mean_local_angle_rmse_reduction_bins": finite_mean([row["mean_local_angle_rmse_reduction_bins"] for row in seed_rows]),
        "elapsed_seconds": elapsed,
    }
    if (
        metrics["mean_nmse_gain_db"] > 0.0
        and metrics["mean_local_delay_rmse_reduction_bins"] > 0.0
        and metrics["mean_angle_rmse_reduction_deg"] > 0.0
        and max(metrics["mean_std_delay_alpha"], metrics["mean_std_angle_alpha"]) >= 0.01
    ):
        metrics["claim_update"] = "feature-controller-source-supported"
    else:
        metrics["claim_update"] = "feature-controller-source-inconclusive"
    output = ROOT / "05_results" / args.output_dir_name
    output.mkdir(parents=True, exist_ok=True)
    for name, records in (("controller_cells.csv", cell_rows), ("controller_seeds.csv", seed_rows)):
        with (output / name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(records[0].keys()))
            writer.writeheader()
            writer.writerows(records)
    torch.save({
        "feature_names": FEATURE_NAMES, "shape": shape, "hidden_dim": args.hidden_dim,
        "search_radius": args.search_radius, "models": checkpoint_models,
        "training_config": vars(args), "metrics": metrics,
    }, output / "controller_checkpoint.pt")
    command = subprocess.list2cmdline([sys.executable, str(Path(__file__).resolve().relative_to(ROOT)), *sys.argv[1:]])
    manifest = {
        "run_id": f"feature_controller_source_{len(args.seeds)}seed", "command": command,
        "config": vars(args) | {"shape": shape}, "metrics": metrics,
        "environment": environment_snapshot(ROOT),
        "notes": [
            "Training and model selection use only geometry-matched synthetic samples.",
            "Features are estimator-internal and available at deployment.",
            "Hungarian matching is fixed per sample before differentiable optimization.",
        ],
    }
    (output / "run_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# Feature-Conditioned Refinement Controller Source Training", "",
        f"- Claim update: {metrics['claim_update']}",
        f"- Mean delay alpha/std: {metrics['mean_delay_alpha']:.6g} / {metrics['mean_std_delay_alpha']:.6g}",
        f"- Mean angle alpha/std: {metrics['mean_angle_alpha']:.6g} / {metrics['mean_std_angle_alpha']:.6g}",
        f"- Mean NMSE gain: {metrics['mean_nmse_gain_db']:.6g} dB",
        f"- Delay/angle bin-RMSE reduction: {metrics['mean_delay_rmse_reduction_bins']:.6g} / {metrics['mean_angle_rmse_reduction_bins']:.6g}",
        f"- Physical broadside-angle RMSE reduction: {metrics['mean_angle_rmse_reduction_deg']:.6g} deg",
        f"- Local-support delay/angle bin-RMSE reduction: {metrics['mean_local_delay_rmse_reduction_bins']:.6g} / {metrics['mean_local_angle_rmse_reduction_bins']:.6g}",
        f"- Elapsed seconds: {elapsed:.2f}", "", "## Evaluation summary", "",
        "- research_question: Can estimator-internal features predict non-collapsed per-sample delay/angle refinement scales?",
        f"- claim_update: {metrics['claim_update']}",
        "- baseline_relation: Grid and controller use identical held-out synthetic samples.",
        "- failure_mode: Non-positive NMSE or either-axis local-support RMSE reduction, or output collapse below 0.01 std.",
        "- next_action: Freeze the source ensemble for one unchanged Sionna CDL run only if supported.",
        "- evidence_level: Source-only development gate.",
    ]
    text = "\n".join(lines) + "\n"
    (output / "summary.md").write_text(text, encoding="utf-8")
    (output / "evaluation_summary.md").write_text(text, encoding="utf-8")
    print(f"Wrote {(output / 'summary.md').relative_to(ROOT)}")
    for key in ("claim_update", "mean_delay_alpha", "mean_std_delay_alpha", "mean_angle_alpha", "mean_std_angle_alpha", "mean_nmse_gain_db", "mean_delay_rmse_reduction_bins", "mean_angle_rmse_reduction_bins", "mean_angle_rmse_reduction_deg", "mean_local_delay_rmse_reduction_bins", "mean_local_angle_rmse_reduction_bins"):
        print(f"{key}={metrics[key]}")


if __name__ == "__main__":
    main()
