"""Shared metrics for the TSP off-grid refinement revision experiments."""

from __future__ import annotations

import csv
import json
import math
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.stats import rankdata


def circular_delta(value: float, reference: float, period: int) -> float:
    """Return the signed shortest displacement ``value-reference``."""

    return float((value - reference + period / 2.0) % period - period / 2.0)


def circular_distance(value: float, reference: float, period: int) -> float:
    return abs(circular_delta(value, reference, period))


def assignment_by_normalized_bin_distance(
    estimates: np.ndarray,
    truth: np.ndarray,
    shape: Sequence[int],
) -> tuple[np.ndarray, np.ndarray]:
    """Match estimated and true components using circular normalized distance."""

    estimates = np.asarray(estimates, dtype=float)
    truth = np.asarray(truth, dtype=float)
    if estimates.ndim != 2 or truth.ndim != 2 or estimates.shape[1] != truth.shape[1]:
        raise ValueError("estimates and truth must be two-dimensional with equal axis counts")
    if estimates.shape[0] != truth.shape[0]:
        raise ValueError("component counts must match")
    if estimates.shape[1] != len(shape):
        raise ValueError("shape must contain one period per axis")

    cost = np.zeros((estimates.shape[0], truth.shape[0]), dtype=float)
    for est_idx, estimate in enumerate(estimates):
        for truth_idx, target in enumerate(truth):
            cost[est_idx, truth_idx] = sum(
                (circular_distance(estimate[axis], target[axis], int(shape[axis])) / shape[axis]) ** 2
                for axis in range(len(shape))
            )
    return linear_sum_assignment(cost)


def matched_component_metrics(
    estimates: np.ndarray,
    truth: np.ndarray,
    shape: Sequence[int],
    *,
    tolerance_bins: float = 0.5,
) -> dict[str, object]:
    """Compute matched errors and per-component/all-component hit rates."""

    estimates = np.asarray(estimates, dtype=float)
    truth = np.asarray(truth, dtype=float)
    row_ind, col_ind = assignment_by_normalized_bin_distance(estimates, truth, shape)
    errors = np.zeros_like(truth, dtype=float)
    for est_idx, truth_idx in zip(row_ind, col_ind):
        errors[truth_idx] = [
            circular_delta(estimates[est_idx, axis], truth[truth_idx, axis], int(shape[axis]))
            for axis in range(len(shape))
        ]
    hits = np.all(np.abs(errors) <= tolerance_bins + 1e-12, axis=1)
    return {
        "estimate_indices_by_truth": row_ind[np.argsort(col_ind)],
        "errors_by_truth": errors,
        "hits_by_truth": hits,
        "per_component_hit_rate": float(np.mean(hits)),
        "all_components_hit": bool(np.all(hits)),
        "mean_absolute_bin_error": float(np.mean(np.abs(errors))),
        "maximum_absolute_bin_error": float(np.max(np.abs(errors))),
    }


def distinct_pair_metrics(
    estimates: np.ndarray,
    truth: np.ndarray,
    shape: Sequence[int],
    *,
    pair_truth_indices: tuple[int, int] = (0, 1),
) -> dict[str, float]:
    """Measure recovery of a designated pair beyond independent half-bin hits.

    The strict event requires both truth-assigned estimates to lie within half
    of the true pair separation (capped at half a bin) and the recovered pair
    separation to remain within 50% of the true value.  The accompanying
    separation error remains informative when the strict event is not met.
    """

    estimates = np.asarray(estimates, dtype=float)
    truth = np.asarray(truth, dtype=float)
    first, second = pair_truth_indices
    if first == second or min(first, second) < 0 or max(first, second) >= len(truth):
        raise ValueError("pair_truth_indices must identify two distinct truth components")
    matched = matched_component_metrics(estimates, truth, shape)
    assigned = estimates[np.asarray(matched["estimate_indices_by_truth"], dtype=int)]

    def pair_separation(values: np.ndarray) -> float:
        return float(
            math.sqrt(
                sum(
                    circular_distance(
                        values[first, axis], values[second, axis], int(shape[axis])
                    )
                    ** 2
                    for axis in range(len(shape))
                )
            )
        )

    true_separation = pair_separation(truth)
    estimated_separation = pair_separation(assigned)
    separation_error = abs(estimated_separation - true_separation)
    adaptive_tolerance = min(0.5, true_separation / 2.0)
    errors = np.asarray(matched["errors_by_truth"], dtype=float)[[first, second]]
    assignment_is_precise = bool(
        np.all(np.abs(errors) <= adaptive_tolerance + 1e-12)
    )
    separation_is_faithful = bool(
        true_separation > 0.0
        and 0.5 * true_separation <= estimated_separation <= 1.5 * true_separation
    )
    return {
        "true_pair_separation_bins": true_separation,
        "estimated_pair_separation_bins": estimated_separation,
        "pair_separation_error_bins": separation_error,
        "pair_normalized_separation_error": separation_error / max(true_separation, 1e-12),
        "distinct_pair_recovery": float(assignment_is_precise and separation_is_faithful),
        "distinct_pair_tolerance_bins": adaptive_tolerance,
    }


def support_quality_metrics(
    coarse_bins: np.ndarray,
    truth: np.ndarray,
    shape: Sequence[int],
    *,
    neighborhood_bins: float = 0.5,
) -> dict[str, float]:
    """Summarize coarse-support coverage and duplicate neighborhoods."""

    coarse_bins = np.asarray(coarse_bins, dtype=float)
    truth = np.asarray(truth, dtype=float)
    matched = matched_component_metrics(
        coarse_bins,
        truth,
        shape,
        tolerance_bins=neighborhood_bins,
    )

    nearest_truth = []
    for coarse in coarse_bins:
        distances = []
        for target in truth:
            distances.append(
                sum(
                    (circular_distance(coarse[axis], target[axis], int(shape[axis])) / shape[axis]) ** 2
                    for axis in range(len(shape))
                )
            )
        nearest_truth.append(int(np.argmin(distances)))
    duplicate_rate = 1.0 - len(set(nearest_truth)) / max(len(nearest_truth), 1)
    return {
        "q_sup": float(matched["per_component_hit_rate"]),
        "duplicate_neighborhood_rate": float(duplicate_rate),
        "coarse_mean_absolute_bin_error": float(matched["mean_absolute_bin_error"]),
        "coarse_maximum_absolute_bin_error": float(matched["maximum_absolute_bin_error"]),
    }


def refined_collision_rate(
    bins: np.ndarray,
    shape: Sequence[int],
    *,
    tolerance_bins: float = 0.25,
) -> float:
    """Fraction of component pairs whose refined locations nearly coincide."""

    bins = np.asarray(bins, dtype=float)
    collision_count = 0
    pair_count = 0
    for first in range(len(bins)):
        for second in range(first + 1, len(bins)):
            pair_count += 1
            if all(
                circular_distance(bins[first, axis], bins[second, axis], int(shape[axis]))
                <= tolerance_bins
                for axis in range(len(shape))
            ):
                collision_count += 1
    return float(collision_count / pair_count) if pair_count else 0.0


def fourier_coherence_1d(length: int, delta_bins: float) -> float:
    r"""Magnitude of the normalized Fourier-atom inner product."""

    delta = float(delta_bins)
    denominator = length * math.sin(math.pi * delta / length)
    if abs(denominator) < 1e-14:
        nearest_period = round(delta / length)
        return 1.0 if abs(delta - nearest_period * length) < 1e-12 else 0.0
    return float(abs(math.sin(math.pi * delta) / denominator))


def fourier_inner_product_1d(length: int, delta_bins: float) -> complex:
    """Normalized Fourier inner product for a signed bin displacement."""

    delta = float(delta_bins)
    denominator = length * math.sin(math.pi * delta / length)
    if abs(denominator) < 1e-14:
        nearest_period = round(delta / length)
        return 1.0 + 0.0j if abs(delta - nearest_period * length) < 1e-12 else 0.0 + 0.0j
    magnitude_with_sign = math.sin(math.pi * delta) / denominator
    phase = math.pi * (length - 1) * delta / length
    return complex(magnitude_with_sign * np.exp(1j * phase))


def separable_fourier_coherence(shape: Sequence[int], delta_bins: Sequence[float]) -> float:
    """Product coherence of a separable multidimensional Fourier dictionary."""

    if len(shape) != len(delta_bins):
        raise ValueError("shape and delta_bins must have equal lengths")
    value = 1.0
    for length, delta in zip(shape, delta_bins):
        value *= fourier_coherence_1d(int(length), float(delta))
    return float(value)


def minimum_circular_separation(bins: np.ndarray, shape: Sequence[int]) -> float:
    """Return the smallest Euclidean circular separation in bin coordinates."""

    bins = np.asarray(bins, dtype=float)
    if len(bins) < 2:
        return float("inf")
    minimum = float("inf")
    for first in range(len(bins)):
        for second in range(first + 1, len(bins)):
            distance = math.sqrt(
                sum(
                    circular_distance(bins[first, axis], bins[second, axis], int(shape[axis])) ** 2
                    for axis in range(len(shape))
                )
            )
            minimum = min(minimum, distance)
    return float(minimum)


def candidate_interference_component_diagnostics(
    coarse_bins: np.ndarray,
    truth: np.ndarray,
    gains: np.ndarray,
    shape: Sequence[int],
    *,
    search_radius: float = 0.45,
    search_points: int = 5,
    noise_variance: float = 0.0,
    eta: float = 0.05,
) -> dict[str, object]:
    """Return truth-aligned component terms in the score-gap condition."""

    coarse_bins = np.asarray(coarse_bins, dtype=float)
    truth = np.asarray(truth, dtype=float)
    gains = np.asarray(gains)
    row_ind, col_ind = assignment_by_normalized_bin_distance(coarse_bins, truth, shape)
    offsets = np.linspace(-search_radius, search_radius, search_points)
    ratios_by_truth = np.full(len(truth), np.nan, dtype=float)
    gaps_by_truth = np.full(len(truth), np.nan, dtype=float)
    interference_by_truth = np.full(len(truth), np.nan, dtype=float)
    candidate_count = int(search_points ** len(shape))
    noise_bound = math.sqrt(max(float(noise_variance), 0.0)) * math.sqrt(
        max(math.log(max(candidate_count * len(truth) / eta, 1.0)), 0.0)
    )

    for coarse_idx, truth_idx in zip(row_ind, col_ind):
        candidate_axes = [
            (coarse_bins[coarse_idx, axis] + offsets) % shape[axis]
            for axis in range(len(shape))
        ]
        candidates = np.array(np.meshgrid(*candidate_axes, indexing="ij")).reshape(len(shape), -1).T
        target_scores = []
        interference = []
        for candidate in candidates:
            target_delta = [
                circular_delta(candidate[axis], truth[truth_idx, axis], int(shape[axis]))
                for axis in range(len(shape))
            ]
            target_scores.append(abs(gains[truth_idx]) * separable_fourier_coherence(shape, target_delta))
            bound = 0.0
            for other_idx in range(len(truth)):
                if other_idx == truth_idx:
                    continue
                other_delta = [
                    circular_delta(candidate[axis], truth[other_idx, axis], int(shape[axis]))
                    for axis in range(len(shape))
                ]
                bound += abs(gains[other_idx]) * separable_fourier_coherence(shape, other_delta)
            interference.append(bound)

        target_scores = np.asarray(target_scores, dtype=float)
        best_two = np.partition(target_scores, -2)[-2:] if len(target_scores) >= 2 else target_scores
        gap = float(np.max(best_two) - np.min(best_two)) if len(best_two) == 2 else float(best_two[0])
        interference_bound = float(np.max(interference))
        denominator = 2.0 * (interference_bound + noise_bound)
        ratio = gap / denominator if denominator > 0.0 else float("inf")
        ratios_by_truth[truth_idx] = ratio
        gaps_by_truth[truth_idx] = gap
        interference_by_truth[truth_idx] = interference_bound

    return {
        "theory_ratios_by_truth": ratios_by_truth,
        "noiseless_candidate_gaps_by_truth": gaps_by_truth,
        "interference_envelopes_by_truth": interference_by_truth,
        "noise_envelope": float(noise_bound),
        "eta": float(eta),
        "candidate_count_per_neighborhood": candidate_count,
    }


def candidate_interference_diagnostics(
    coarse_bins: np.ndarray,
    truth: np.ndarray,
    gains: np.ndarray,
    shape: Sequence[int],
    *,
    search_radius: float = 0.45,
    search_points: int = 5,
    noise_variance: float = 0.0,
    eta: float = 0.05,
) -> dict[str, float]:
    """Aggregate the component-level Fourier score-gap diagnostics."""

    components = candidate_interference_component_diagnostics(
        coarse_bins,
        truth,
        gains,
        shape,
        search_radius=search_radius,
        search_points=search_points,
        noise_variance=noise_variance,
        eta=eta,
    )
    ratios = np.asarray(components["theory_ratios_by_truth"], dtype=float)
    noiseless_gaps = np.asarray(
        components["noiseless_candidate_gaps_by_truth"], dtype=float
    )
    interference_bounds = np.asarray(
        components["interference_envelopes_by_truth"], dtype=float
    )

    finite_ratios = ratios[np.isfinite(ratios)]
    return {
        "theory_ratio_min": float(np.min(finite_ratios)) if finite_ratios.size else float("inf"),
        "theory_ratio_mean": float(np.mean(finite_ratios)) if finite_ratios.size else float("inf"),
        "theory_condition_fraction": float(np.mean(ratios > 1.0)),
        "theory_any_component_condition": float(np.any(ratios > 1.0)),
        "theory_all_components_condition": float(np.all(ratios > 1.0)),
        "noiseless_candidate_gap_min": float(np.min(noiseless_gaps)),
        "interference_envelope_max": float(np.max(interference_bounds)),
        "noise_envelope": float(components["noise_envelope"]),
        "theory_eta": float(components["eta"]),
    }


def candidate_axis_correctness(
    coarse_bins: np.ndarray,
    refined_bins: np.ndarray,
    truth: np.ndarray,
    shape: Sequence[int],
    *,
    search_radius: float = 0.45,
    search_points: int = 5,
) -> tuple[float, np.ndarray]:
    """Measure how often refinement selects the truth-nearest axis candidate."""

    coarse_bins = np.asarray(coarse_bins, dtype=float)
    refined_bins = np.asarray(refined_bins, dtype=float)
    truth = np.asarray(truth, dtype=float)
    row_ind, col_ind = assignment_by_normalized_bin_distance(coarse_bins, truth, shape)
    offsets = np.linspace(-search_radius, search_radius, search_points)
    correctness = np.zeros_like(truth, dtype=float)
    for coarse_index, truth_index in zip(row_ind, col_ind):
        for axis in range(len(shape)):
            candidates = np.mod(coarse_bins[coarse_index, axis] + offsets, shape[axis])
            candidate_distances = np.asarray(
                [
                    circular_distance(value, truth[truth_index, axis], int(shape[axis]))
                    for value in candidates
                ]
            )
            selected_distances = np.asarray(
                [
                    circular_distance(value, refined_bins[coarse_index, axis], int(shape[axis]))
                    for value in candidates
                ]
            )
            correctness[truth_index, axis] = float(
                int(np.argmin(candidate_distances)) == int(np.argmin(selected_distances))
            )
    return float(np.mean(correctness)), correctness


def design_condition_number(shape: Sequence[int], bins: np.ndarray) -> float:
    """Condition number of normalized separable Fourier atoms at given bins."""

    bins = np.asarray(bins, dtype=float)
    gram = np.ones((len(bins), len(bins)), dtype=np.complex128)
    for first in range(len(bins)):
        for second in range(len(bins)):
            value = 1.0 + 0.0j
            for axis in range(len(shape)):
                delta = circular_delta(
                    bins[second, axis], bins[first, axis], int(shape[axis])
                )
                value *= fourier_inner_product_1d(int(shape[axis]), delta)
            gram[first, second] = value
    eigenvalues = np.linalg.eigvalsh(gram)
    smallest = max(float(np.min(eigenvalues)), 1e-15)
    return float(math.sqrt(max(float(np.max(eigenvalues)), 0.0) / smallest))


def seed_cluster_bootstrap(
    rows: Sequence[Mapping[str, object]],
    seed_key: str,
    statistic,
    *,
    n_bootstrap: int = 10_000,
    random_seed: int = 20260829,
) -> np.ndarray:
    """Bootstrap a statistic by resampling complete seed clusters."""

    clusters: dict[object, list[Mapping[str, object]]] = {}
    for row in rows:
        clusters.setdefault(row[seed_key], []).append(row)
    seeds = list(clusters)
    if not seeds:
        raise ValueError("at least one seed cluster is required")
    rng = np.random.default_rng(random_seed)
    values = np.empty(n_bootstrap, dtype=float)
    for index in range(n_bootstrap):
        selected = rng.choice(seeds, size=len(seeds), replace=True)
        sample = [row for seed in selected for row in clusters[seed]]
        values[index] = float(statistic(sample))
    return values


def roc_auc(scores: Sequence[float], labels: Sequence[int | bool]) -> float:
    """Area under the ROC curve with average ranks for tied scores."""

    scores_array = np.asarray(scores, dtype=float)
    labels_array = np.asarray(labels, dtype=bool)
    positive = int(np.sum(labels_array))
    negative = len(labels_array) - positive
    if positive == 0 or negative == 0:
        return float("nan")
    ranks = rankdata(scores_array, method="average")
    rank_sum = float(np.sum(ranks[labels_array]))
    return float((rank_sum - positive * (positive + 1) / 2.0) / (positive * negative))


def average_precision(scores: Sequence[float], labels: Sequence[int | bool]) -> float:
    """Non-interpolated average precision for a high-score positive class."""

    scores_array = np.asarray(scores, dtype=float)
    labels_array = np.asarray(labels, dtype=bool)
    positive = int(np.sum(labels_array))
    if positive == 0:
        return float("nan")
    order = np.argsort(-scores_array, kind="mergesort")
    sorted_labels = labels_array[order]
    precision = np.cumsum(sorted_labels) / np.arange(1, len(sorted_labels) + 1)
    return float(np.sum(precision[sorted_labels]) / positive)


def fit_monotone_quantile_calibrator(
    scores: Sequence[float],
    labels: Sequence[int | bool],
    *,
    n_bins: int = 10,
) -> list[dict[str, float]]:
    """Fit an increasing empirical probability map using quantile bins and PAV."""

    scores_array = np.asarray(scores, dtype=float)
    labels_array = np.asarray(labels, dtype=float)
    if len(scores_array) != len(labels_array) or len(scores_array) == 0:
        raise ValueError("scores and labels must be nonempty and equally sized")
    order = np.argsort(scores_array, kind="mergesort")
    groups: list[dict[str, float]] = []
    for indices in np.array_split(order, min(n_bins, len(order))):
        if len(indices) == 0:
            continue
        groups.append(
            {
                "lower": float(np.min(scores_array[indices])),
                "upper": float(np.max(scores_array[indices])),
                "weight": float(len(indices)),
                "positive_rate": float(np.mean(labels_array[indices])),
            }
        )
    blocks: list[dict[str, float]] = []
    for group in groups:
        blocks.append(group.copy())
        while len(blocks) >= 2 and blocks[-2]["positive_rate"] > blocks[-1]["positive_rate"]:
            right = blocks.pop()
            left = blocks.pop()
            weight = left["weight"] + right["weight"]
            blocks.append(
                {
                    "lower": left["lower"],
                    "upper": right["upper"],
                    "weight": weight,
                    "positive_rate": (
                        left["weight"] * left["positive_rate"]
                        + right["weight"] * right["positive_rate"]
                    )
                    / weight,
                }
            )
    return blocks


def apply_monotone_calibrator(
    scores: Sequence[float], calibrator: Sequence[Mapping[str, float]]
) -> np.ndarray:
    """Map scores to empirical probabilities from a fitted calibrator."""

    if not calibrator:
        raise ValueError("calibrator must contain at least one block")
    upper = np.asarray([float(block["upper"]) for block in calibrator])
    rates = np.asarray([float(block["positive_rate"]) for block in calibrator])
    indices = np.searchsorted(upper, np.asarray(scores, dtype=float), side="left")
    return rates[np.clip(indices, 0, len(rates) - 1)]


def write_csv(path: Path, rows: Iterable[Mapping[str, object]]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_release_metadata(
    output_dir: Path,
    *,
    config: Mapping[str, object],
    seeds: Sequence[Mapping[str, object]] | Sequence[int],
    command: str,
) -> None:
    """Write the compact reproducibility bundle used by revision experiments."""

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    seed_rows = [dict(item) if isinstance(item, Mapping) else {"seed": item} for item in seeds]
    write_csv(output_dir / "seeds.csv", seed_rows)
    environment = {
        "python": sys.version,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "numpy": np.__version__,
        "omp_num_threads": os.environ.get("OMP_NUM_THREADS", ""),
        "mkl_num_threads": os.environ.get("MKL_NUM_THREADS", ""),
        "openblas_num_threads": os.environ.get("OPENBLAS_NUM_THREADS", ""),
    }
    (output_dir / "environment.txt").write_text(
        "\n".join(f"{key}: {value}" for key, value in environment.items()) + "\n",
        encoding="utf-8",
    )
    (output_dir / "command.txt").write_text(command.strip() + "\n", encoding="utf-8")
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        commit = "unavailable"
    (output_dir / "git_commit.txt").write_text(commit + "\n", encoding="utf-8")
