from __future__ import annotations

import csv
from pathlib import Path
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_active_modules"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from common.manifest import write_run_manifest, write_summary_md
from common.seed import seed_all
from run_stage3_a4_high_l_plateau_gate import (
    choose_threshold,
    plateau_gate_depth,
    run_depth_curve,
)


def finite_mean(values: list[float]) -> float:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    return float(np.mean(arr)) if arr.size else float("nan")


def finite_std(values: list[float]) -> float:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    return float(np.std(arr, ddof=1)) if arr.size > 1 else 0.0


def oracle_depth(
    curve: list[float],
    *,
    min_depth: int,
    fixed_depth: int,
    tolerance_db: float,
) -> int:
    for depth in range(min_depth, fixed_depth + 1):
        if curve[depth] - curve[fixed_depth] <= tolerance_db:
            return depth
    return fixed_depth


def curve_feature(
    curve: list[float],
    *,
    snr_db: float,
    depth: int,
    fixed_depth: int,
) -> np.ndarray:
    improvements = np.asarray(
        [float(curve[i - 1] - curve[i]) for i in range(1, depth + 1)],
        dtype=float,
    )
    recent = improvements[-2:] if improvements.size >= 2 else improvements
    return np.asarray(
        [
            snr_db / 30.0,
            depth / max(float(fixed_depth), 1.0),
            float(improvements[-1]) if improvements.size else 0.0,
            float(np.mean(recent)) if recent.size else 0.0,
            float(curve[0] - curve[depth]),
        ],
        dtype=float,
    )


def build_knn_training(
    curves: list[dict[str, float | int | list[float] | str]],
    *,
    min_depth: int,
    fixed_depth: int,
    tolerance_db: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    features: list[np.ndarray] = []
    stop_labels: list[float] = []
    target_depths: list[float] = []
    target_savings: list[float] = []
    for row in curves:
        curve = row["curve"]
        assert isinstance(curve, list)
        snr_db = float(row["snr_db"])
        target_depth = oracle_depth(
            curve,
            min_depth=min_depth,
            fixed_depth=fixed_depth,
            tolerance_db=tolerance_db,
        )
        for depth in range(min_depth, fixed_depth + 1):
            features.append(
                curve_feature(curve, snr_db=snr_db, depth=depth, fixed_depth=fixed_depth)
            )
            stop_labels.append(float(depth >= target_depth))
            target_depths.append(float(target_depth))
            target_savings.append(100.0 * (fixed_depth - target_depth) / max(fixed_depth, 1))
    feature_matrix = np.vstack(features)
    scale = np.std(feature_matrix, axis=0)
    scale[scale < 1e-9] = 1.0
    return (
        feature_matrix / scale,
        np.asarray(stop_labels, dtype=float),
        np.asarray(target_depths, dtype=float),
        np.asarray(target_savings, dtype=float),
    )


def knn_gate_depth(
    curve: list[float],
    *,
    snr_db: float,
    min_depth: int,
    fixed_depth: int,
    train_features: np.ndarray,
    train_labels: np.ndarray,
    feature_scale: np.ndarray,
    k: int,
    vote_threshold: float,
) -> int:
    for depth in range(min_depth, fixed_depth + 1):
        raw_feature = curve_feature(curve, snr_db=snr_db, depth=depth, fixed_depth=fixed_depth)
        feature = raw_feature / feature_scale
        distances = np.linalg.norm(train_features - feature[None, :], axis=1)
        k_eff = min(k, distances.size)
        nearest = np.argpartition(distances, k_eff - 1)[:k_eff]
        stop_vote = float(np.mean(train_labels[nearest]))
        if stop_vote >= vote_threshold:
            return depth
    return fixed_depth


def evaluate_depth_policy(
    curves: list[dict[str, float | int | list[float] | str]],
    *,
    policy: str,
    fixed_depth: int,
    min_depth: int,
    tolerance_db: float,
    scalar_thresholds_by_snr: dict[float, float] | None = None,
    knn_state: dict[str, object] | None = None,
) -> tuple[list[dict[str, float | str]], list[dict[str, float | str]]]:
    cell_rows: list[dict[str, float | str]] = []
    sample_rows: list[dict[str, float | str]] = []
    for row in curves:
        curve = row["curve"]
        assert isinstance(curve, list)
        snr_db = float(row["snr_db"])
        if policy == "per_curve_quality_oracle":
            depth = oracle_depth(
                curve,
                min_depth=min_depth,
                fixed_depth=fixed_depth,
                tolerance_db=tolerance_db,
            )
        elif policy == "snr_scalar_train":
            assert scalar_thresholds_by_snr is not None
            depth = plateau_gate_depth(
                curve,
                threshold_db=scalar_thresholds_by_snr[snr_db],
                min_depth=min_depth,
                fixed_depth=fixed_depth,
            )
        elif policy == "curve_feature_knn_train":
            assert knn_state is not None
            depth = knn_gate_depth(
                curve,
                snr_db=snr_db,
                min_depth=min_depth,
                fixed_depth=fixed_depth,
                train_features=knn_state["features"],  # type: ignore[arg-type]
                train_labels=knn_state["labels"],  # type: ignore[arg-type]
                feature_scale=knn_state["scale"],  # type: ignore[arg-type]
                k=int(knn_state["k"]),
                vote_threshold=float(knn_state["vote_threshold"]),
            )
        else:
            raise ValueError(f"Unknown policy: {policy}")
        gap = float(curve[depth] - curve[fixed_depth])
        savings = 100.0 * (fixed_depth - depth) / max(fixed_depth, 1)
        cell_rows.append(
            {
                "policy": policy,
                "split": str(row["split"]),
                "seed": float(row["seed"]),
                "snr_db": snr_db,
                "sample_index": float(row["sample_index"]),
                "selected_depth": float(depth),
                "gate_nmse_db": float(curve[depth]),
                "fixed_depth_nmse_db": float(curve[fixed_depth]),
                "gap_vs_fixed_db": gap,
                "depth_savings_percent": savings,
                "passes_sample_gate": float(savings >= 25.0 and gap <= tolerance_db),
            }
        )
        for curve_depth, nmse_db in enumerate(curve):
            sample_rows.append(
                {
                    "policy": policy,
                    "split": str(row["split"]),
                    "seed": float(row["seed"]),
                    "snr_db": snr_db,
                    "sample_index": float(row["sample_index"]),
                    "curve_depth": float(curve_depth),
                    "nmse_db": float(nmse_db),
                    "selected_depth": float(depth),
                    "gap_vs_fixed_db": gap,
                    "depth_savings_percent": savings,
                }
            )
    return cell_rows, sample_rows


def summarize_policy_snr(
    rows: list[dict[str, float | str]],
    *,
    policies: list[str],
    snr_values: list[float],
) -> list[dict[str, float | str]]:
    summary_rows: list[dict[str, float | str]] = []
    for policy in policies:
        for snr_db in snr_values:
            subset = [
                row
                for row in rows
                if row["policy"] == policy and abs(float(row["snr_db"]) - snr_db) < 1e-9
            ]
            savings = [float(row["depth_savings_percent"]) for row in subset]
            gaps = [float(row["gap_vs_fixed_db"]) for row in subset]
            passes = [float(row["passes_sample_gate"]) for row in subset]
            summary_rows.append(
                {
                    "policy": policy,
                    "snr_db": float(snr_db),
                    "mean_depth_savings_percent": finite_mean(savings),
                    "min_depth_savings_percent": float(min(savings)),
                    "mean_nmse_gap_db": finite_mean(gaps),
                    "max_nmse_gap_db": float(max(gaps)),
                    "sample_pass_rate": finite_mean(passes),
                    "n_samples": float(len(subset)),
                }
            )
    return summary_rows


def select_snr_scalar_thresholds(
    train_curves: list[dict[str, float | int | list[float] | str]],
    *,
    snr_values: list[float],
    thresholds: list[float],
    min_depth: int,
    fixed_depth: int,
    tolerance_db: float,
) -> dict[float, float]:
    selected: dict[float, float] = {}
    for snr_db in snr_values:
        curves = [
            row["curve"]
            for row in train_curves
            if abs(float(row["snr_db"]) - snr_db) < 1e-9
        ]
        selected_threshold, _, _ = choose_threshold(
            curves,  # type: ignore[arg-type]
            thresholds=thresholds,
            min_depth=min_depth,
            fixed_depth=fixed_depth,
            tolerance_db=tolerance_db,
        )
        selected[float(snr_db)] = float(selected_threshold)
    return selected


def tune_knn_policy(
    train_curves: list[dict[str, float | int | list[float] | str]],
    *,
    min_depth: int,
    fixed_depth: int,
    tolerance_db: float,
) -> dict[str, object]:
    features_raw, labels, _, _ = build_knn_training(
        train_curves,
        min_depth=min_depth,
        fixed_depth=fixed_depth,
        tolerance_db=tolerance_db,
    )
    raw_features_unscaled = []
    for row in train_curves:
        curve = row["curve"]
        assert isinstance(curve, list)
        for depth in range(min_depth, fixed_depth + 1):
            raw_features_unscaled.append(
                curve_feature(
                    curve,
                    snr_db=float(row["snr_db"]),
                    depth=depth,
                    fixed_depth=fixed_depth,
                )
            )
    raw_matrix = np.vstack(raw_features_unscaled)
    scale = np.std(raw_matrix, axis=0)
    scale[scale < 1e-9] = 1.0
    features = raw_matrix / scale
    best_state: dict[str, object] | None = None
    best_score = (-1.0, -1.0)
    for k in [1, 3, 5, 7]:
        for vote_threshold in [0.35, 0.5, 0.65, 0.8]:
            state = {
                "features": features,
                "labels": labels,
                "scale": scale,
                "k": int(k),
                "vote_threshold": float(vote_threshold),
            }
            rows, _ = evaluate_depth_policy(
                train_curves,
                policy="curve_feature_knn_train",
                fixed_depth=fixed_depth,
                min_depth=min_depth,
                tolerance_db=tolerance_db,
                knn_state=state,
            )
            savings = finite_mean([float(row["depth_savings_percent"]) for row in rows])
            max_gap = max(float(row["gap_vs_fixed_db"]) for row in rows)
            feasible = max_gap <= tolerance_db
            score = (savings if feasible else -max_gap, -max_gap)
            if score > best_score:
                best_score = score
                best_state = state
                best_state["train_mean_savings_percent"] = savings
                best_state["train_max_gap_db"] = max_gap
                best_state["train_feasible"] = float(feasible)
    assert best_state is not None
    return best_state


def write_evaluation_summary(
    output_dir: Path,
    *,
    metrics: dict[str, object],
    summary_rows: list[dict[str, float | str]],
    elapsed_seconds: float,
) -> Path:
    learner_rows = [row for row in summary_rows if row["policy"] == "curve_feature_knn_train"]
    oracle_rows = [row for row in summary_rows if row["policy"] == "per_curve_quality_oracle"]
    scalar_rows = [row for row in summary_rows if row["policy"] == "snr_scalar_train"]
    learner_min_savings = min(float(row["mean_depth_savings_percent"]) for row in learner_rows)
    learner_max_gap = max(float(row["max_nmse_gap_db"]) for row in learner_rows)
    oracle_min_savings = min(float(row["mean_depth_savings_percent"]) for row in oracle_rows)
    oracle_max_gap = max(float(row["max_nmse_gap_db"]) for row in oracle_rows)
    scalar_min_savings = min(float(row["mean_depth_savings_percent"]) for row in scalar_rows)
    scalar_max_gap = max(float(row["max_nmse_gap_db"]) for row in scalar_rows)
    tolerance_db = float(metrics["nmse_tolerance_db"])
    if learner_min_savings >= 25.0 and learner_max_gap <= tolerance_db:
        claim_update = "supported-diagnostic"
        mechanism_note = (
            "The feature-aware sequential gate clears the SNR-axis mean-savings and max-gap gates "
            "in this local diagnostic."
        )
        next_action = "Promote the learned gate to a larger seed sweep and then update the A4 claim if it remains stable."
    elif oracle_min_savings >= 25.0 and oracle_max_gap <= tolerance_db:
        claim_update = "learner-inconclusive-oracle-feasible"
        mechanism_note = (
            "A per-curve quality oracle has enough early-stop room, but the lightweight kNN gate does not reliably "
            "recover it; the issue is model calibration rather than total absence of savings."
        )
        next_action = "Try a stronger learned policy or more training curves before broadening A4."
    else:
        claim_update = "refuted-under-current-curves"
        mechanism_note = (
            "Even the per-curve quality oracle cannot clear the tested SNR cells, so this A4 contract lacks enough "
            "early-stop room under the current curves."
        )
        next_action = "Do not widen A4 across SNR; keep it restricted to the high-L core-SNR result or redesign the refinement schedule."
    lines = [
        "# Stage 3 A4 SNR-Aware Gate Diagnostic",
        "",
        "## Outcome Summary",
        "",
        (
            "This diagnostic tests whether replacing a scalar plateau threshold with an SNR- and "
            "curve-feature-aware sequential policy can rescue the A4 SNR-axis early-stop claim."
        ),
        "",
        "## evaluation_summary",
        "",
        "- `research_question`: Can an SNR/curve-feature-aware gate meet the >=25% depth-savings and <=0.5 dB gap contract across SNR={10,20,30} dB at L=32?",
        f"- `claim_update`: {claim_update}.",
        "- `baseline_relation`: Fixed-depth K=8 repeated off-grid refinement remains the quality comparator; scalar threshold and per-curve quality oracle are diagnostic comparators.",
        "- `failure_mode`: No execution failure if complete; any negative result is methodological under this local synthetic contract.",
        f"- `mechanism_note`: {mechanism_note}",
        f"- `next_action`: {next_action}",
        "- `evidence_level`: Writing-facing A4 boundary diagnostic, not a deployment-ready learned policy.",
        "",
        "## Key Metrics",
        "",
        f"- SNR-aware kNN min SNR mean savings: {learner_min_savings:.4f}%",
        f"- SNR-aware kNN max SNR gap: {learner_max_gap:.4f} dB",
        f"- SNR-scalar min SNR mean savings: {scalar_min_savings:.4f}%",
        f"- SNR-scalar max SNR gap: {scalar_max_gap:.4f} dB",
        f"- Per-curve oracle min SNR mean savings: {oracle_min_savings:.4f}%",
        f"- Per-curve oracle max SNR gap: {oracle_max_gap:.4f} dB",
        f"- Selected k: {metrics['selected_knn_k']}",
        f"- Selected vote threshold: {float(metrics['selected_knn_vote_threshold']):.4f}",
        f"- Wall-clock elapsed time: {elapsed_seconds:.2f} s",
        "",
        "## Policy/SNR Summary",
        "",
        "| Policy | SNR (dB) | Mean savings (%) | Min savings (%) | Mean gap (dB) | Max gap (dB) | Sample pass rate |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary_rows:
        lines.append(
            "| "
            f"{row['policy']} | "
            f"{float(row['snr_db']):.1f} | "
            f"{float(row['mean_depth_savings_percent']):.4f} | "
            f"{float(row['min_depth_savings_percent']):.4f} | "
            f"{float(row['mean_nmse_gap_db']):.4f} | "
            f"{float(row['max_nmse_gap_db']):.4f} | "
            f"{float(row['sample_pass_rate']):.4f} |"
        )
    path = output_dir / "evaluation_summary.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    shape = (128, 16, 32)
    n_targets = 32
    snr_values = [10.0, 20.0, 30.0]
    seeds = [20260624, 20260625]
    n_train = 2
    n_test = 2
    offset_radius = 0.35
    radii = [0.45, 0.28, 0.18, 0.11, 0.07, 0.045, 0.03, 0.02]
    search_points = 3
    fixed_depth = len(radii)
    min_depth = 3
    tolerance_db = 0.5
    thresholds = [0.005, 0.01, 0.02, 0.035, 0.05, 0.075, 0.1, 0.15, 0.2, 0.25, 0.35, 0.5, 0.75, 1.0]
    started = time.perf_counter()

    curve_rows: list[dict[str, float | int | list[float] | str]] = []
    for seed in seeds:
        rng = seed_all(seed + 33000)
        for snr_db in snr_values:
            for split, count in (("train", n_train), ("test", n_test)):
                for sample_index in range(count):
                    curve = run_depth_curve(
                        rng=rng,
                        shape=shape,
                        n_targets=n_targets,
                        snr_db=snr_db,
                        offset_radius=offset_radius,
                        radii=radii,
                        search_points=search_points,
                    )
                    curve_rows.append(
                        {
                            "split": split,
                            "seed": seed,
                            "snr_db": snr_db,
                            "sample_index": sample_index,
                            "curve": curve,
                        }
                    )
    train_curves = [row for row in curve_rows if row["split"] == "train"]
    test_curves = [row for row in curve_rows if row["split"] == "test"]
    scalar_thresholds_by_snr = select_snr_scalar_thresholds(
        train_curves,
        snr_values=snr_values,
        thresholds=thresholds,
        min_depth=min_depth,
        fixed_depth=fixed_depth,
        tolerance_db=tolerance_db,
    )
    knn_state = tune_knn_policy(
        train_curves,
        min_depth=min_depth,
        fixed_depth=fixed_depth,
        tolerance_db=tolerance_db,
    )
    policies = [
        "snr_scalar_train",
        "curve_feature_knn_train",
        "per_curve_quality_oracle",
    ]
    all_policy_rows: list[dict[str, float | str]] = []
    all_sample_rows: list[dict[str, float | str]] = []
    for policy in policies:
        policy_rows, sample_rows = evaluate_depth_policy(
            test_curves,
            policy=policy,
            fixed_depth=fixed_depth,
            min_depth=min_depth,
            tolerance_db=tolerance_db,
            scalar_thresholds_by_snr=scalar_thresholds_by_snr,
            knn_state=knn_state,
        )
        all_policy_rows.extend(policy_rows)
        all_sample_rows.extend(sample_rows)
    summary_rows = summarize_policy_snr(all_policy_rows, policies=policies, snr_values=snr_values)
    elapsed_seconds = time.perf_counter() - started

    output_dir = ROOT / "05_results" / "stage3_a4_snr_aware_gate_diagnostic"
    output_dir.mkdir(parents=True, exist_ok=True)
    policy_csv = output_dir / "stage3_a4_snr_aware_gate_policy_samples.csv"
    with policy_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(all_policy_rows[0].keys()))
        writer.writeheader()
        writer.writerows(all_policy_rows)
    curves_csv = output_dir / "stage3_a4_snr_aware_gate_curves.csv"
    curve_flat_rows: list[dict[str, float | str]] = []
    for row in curve_rows:
        curve = row["curve"]
        assert isinstance(curve, list)
        for depth, nmse_db in enumerate(curve):
            curve_flat_rows.append(
                {
                    "split": str(row["split"]),
                    "seed": float(row["seed"]),
                    "snr_db": float(row["snr_db"]),
                    "sample_index": float(row["sample_index"]),
                    "depth": float(depth),
                    "nmse_db": float(nmse_db),
                }
            )
    with curves_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(curve_flat_rows[0].keys()))
        writer.writeheader()
        writer.writerows(curve_flat_rows)
    summary_csv = output_dir / "stage3_a4_snr_aware_gate_summary.csv"
    with summary_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    learner_rows = [row for row in summary_rows if row["policy"] == "curve_feature_knn_train"]
    oracle_rows = [row for row in summary_rows if row["policy"] == "per_curve_quality_oracle"]
    scalar_rows = [row for row in summary_rows if row["policy"] == "snr_scalar_train"]
    metrics: dict[str, object] = {
        "tensor_shape": "128x16x32",
        "n_targets": n_targets,
        "snr_values_db": snr_values,
        "seeds": seeds,
        "n_train": n_train,
        "n_test": n_test,
        "fixed_depth": fixed_depth,
        "min_depth": min_depth,
        "nmse_tolerance_db": tolerance_db,
        "threshold_candidates_db": thresholds,
        "scalar_thresholds_by_snr": scalar_thresholds_by_snr,
        "selected_knn_k": int(knn_state["k"]),
        "selected_knn_vote_threshold": float(knn_state["vote_threshold"]),
        "knn_train_mean_savings_percent": float(knn_state["train_mean_savings_percent"]),
        "knn_train_max_gap_db": float(knn_state["train_max_gap_db"]),
        "knn_train_feasible": float(knn_state["train_feasible"]),
        "knn_min_snr_mean_depth_savings_percent": min(
            float(row["mean_depth_savings_percent"]) for row in learner_rows
        ),
        "knn_max_snr_nmse_gap_db": max(float(row["max_nmse_gap_db"]) for row in learner_rows),
        "scalar_min_snr_mean_depth_savings_percent": min(
            float(row["mean_depth_savings_percent"]) for row in scalar_rows
        ),
        "scalar_max_snr_nmse_gap_db": max(float(row["max_nmse_gap_db"]) for row in scalar_rows),
        "oracle_min_snr_mean_depth_savings_percent": min(
            float(row["mean_depth_savings_percent"]) for row in oracle_rows
        ),
        "oracle_max_snr_nmse_gap_db": max(float(row["max_nmse_gap_db"]) for row in oracle_rows),
        "elapsed_seconds": elapsed_seconds,
    }
    notes = [
        "Writing-facing A4 diagnostic after scalar-threshold frontier failure.",
        "The learned gate is a lightweight kNN sequential stopping policy using SNR, depth, recent improvement, and cumulative gain features.",
        "The per-curve quality oracle is a diagnostic upper bound that can use fixed-depth quality after the fact; it is not deployable.",
    ]
    manifest_path = write_run_manifest(
        output_dir,
        run_id="stage3_a4_snr_aware_gate_diagnostic_20260625",
        command="python 04_experiments/eval/run_stage3_a4_snr_aware_gate_diagnostic.py",
        config={
            "shape": shape,
            "n_targets": n_targets,
            "snr_values_db": snr_values,
            "seeds": seeds,
            "n_train": n_train,
            "n_test": n_test,
            "offset_radius": offset_radius,
            "radii": radii,
            "search_points": search_points,
            "fixed_depth": fixed_depth,
            "min_depth": min_depth,
            "nmse_tolerance_db": tolerance_db,
            "threshold_candidates_db": thresholds,
            "selected_knn_k": int(knn_state["k"]),
            "selected_knn_vote_threshold": float(knn_state["vote_threshold"]),
        },
        metrics=metrics,
        notes=notes,
        cwd=ROOT,
    )
    summary_path = write_summary_md(
        output_dir,
        title="Stage 3 A4 SNR-Aware Gate Diagnostic",
        config_hash="stage3-a4-snr-aware-gate-diagnostic-20260625",
        metrics=metrics,
        notes=notes,
        artifacts=[
            str(policy_csv.relative_to(ROOT)),
            str(curves_csv.relative_to(ROOT)),
            str(summary_csv.relative_to(ROOT)),
            str(manifest_path.relative_to(ROOT)),
        ],
    )
    evaluation_path = write_evaluation_summary(
        output_dir,
        metrics=metrics,
        summary_rows=summary_rows,
        elapsed_seconds=elapsed_seconds,
    )
    print(f"Wrote {policy_csv.relative_to(ROOT)}")
    print(f"Wrote {curves_csv.relative_to(ROOT)}")
    print(f"Wrote {summary_csv.relative_to(ROOT)}")
    print(f"Wrote {summary_path.relative_to(ROOT)}")
    print(f"Wrote {manifest_path.relative_to(ROOT)}")
    print(f"Wrote {evaluation_path.relative_to(ROOT)}")
    print(
        "knn_min_snr_mean_depth_savings_percent="
        f"{float(metrics['knn_min_snr_mean_depth_savings_percent']):.4f}"
    )
    print(f"knn_max_snr_nmse_gap_db={float(metrics['knn_max_snr_nmse_gap_db']):.4f}")
    print(
        "oracle_min_snr_mean_depth_savings_percent="
        f"{float(metrics['oracle_min_snr_mean_depth_savings_percent']):.4f}"
    )
    print(f"oracle_max_snr_nmse_gap_db={float(metrics['oracle_max_snr_nmse_gap_db']):.4f}")


if __name__ == "__main__":
    main()
