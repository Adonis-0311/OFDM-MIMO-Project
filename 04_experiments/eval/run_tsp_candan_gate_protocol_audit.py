"""Audit leakage-free calibration and incremental value of the Candan gate.

The primary protocol calibrates the scalar residual threshold using CDL-A/C
validation rows only.  CDL-D is excluded from threshold selection and there is
no feature normalization.  A pooled A/C/D protocol is retained as a secondary
same-profile upper bound.  This script consumes the frozen per-scene ledger so
that every protocol is compared on exactly the same channel/noise realizations.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from scipy.stats import t as student_t


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_active_modules"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from common.manifest import write_run_manifest  # noqa: E402
from common.tsp_revision_metrics import write_release_metadata  # noqa: E402


GAIN = "candan_gain_vs_grid_db"
RESIDUAL = "candan_residual_reduction_fraction"
ZETA = "candan_minimum_denominator_stability"
CLIPPING = "candan_clipping_rate"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-csv",
        type=Path,
        default=ROOT / "05_results" / "tsp_candan_route_audit_paper" / "per_scene.csv",
    )
    parser.add_argument(
        "--output-dir-name", default="tsp_candan_gate_protocol_seventh_round"
    )
    return parser.parse_args()


def load_rows(path: Path) -> list[dict[str, object]]:
    numeric = {
        "seed", "sample_index", "snr_db", "l_value", GAIN, RESIDUAL, ZETA,
        CLIPPING,
    }
    rows: list[dict[str, object]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            row: dict[str, object] = dict(raw)
            for key in numeric:
                row[key] = int(raw[key]) if key in {"seed", "sample_index", "l_value"} else float(raw[key])
            rows.append(row)
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def candidate_thresholds(values: np.ndarray, *, include_zero: bool = True) -> np.ndarray:
    candidates = np.quantile(values, np.linspace(0.0, 1.0, 101))
    if include_zero:
        candidates = np.r_[candidates, 0.0]
    return np.unique(candidates)


def gated_gain(rows: list[dict[str, object]], threshold: float) -> np.ndarray:
    gain = np.asarray([float(row[GAIN]) for row in rows])
    residual = np.asarray([float(row[RESIDUAL]) for row in rows])
    return np.where(residual >= threshold, gain, 0.0)


def calibrate(rows: list[dict[str, object]]) -> dict[str, float]:
    values = np.asarray([float(row[RESIDUAL]) for row in rows])
    candidates: list[dict[str, float]] = []
    for threshold in candidate_thresholds(values):
        accepted = values >= threshold
        gains = gated_gain(rows, float(threshold))
        candidates.append(
            {
                "threshold": float(threshold),
                "validation_gated_gain_db": float(np.mean(gains)),
                "validation_increment_db": float(
                    np.mean(gains) - np.mean([float(row[GAIN]) for row in rows])
                ),
                "validation_pass_rate": float(np.mean(accepted)),
            }
        )
    return max(
        candidates,
        key=lambda item: (
            item["validation_gated_gain_db"],
            -item["validation_pass_rate"],
        ),
    )


def seed_interval(rows: list[dict[str, object]], values: np.ndarray) -> tuple[float, float, float]:
    seeds = sorted({int(row["seed"]) for row in rows})
    seed_means = np.asarray(
        [
            np.mean([value for row, value in zip(rows, values) if int(row["seed"]) == seed])
            for seed in seeds
        ],
        dtype=float,
    )
    center = float(np.mean(seed_means))
    if len(seed_means) < 2:
        return center, center, center
    half_width = float(
        student_t.ppf(0.975, len(seed_means) - 1)
        * np.std(seed_means, ddof=1)
        / np.sqrt(len(seed_means))
    )
    return center, center - half_width, center + half_width


def metric_row(
    rows: list[dict[str, object]], *, protocol: str, profile: str, threshold: float,
    stage1_mask: np.ndarray | None = None,
) -> dict[str, object]:
    gain = np.asarray([float(row[GAIN]) for row in rows])
    residual = np.asarray([float(row[RESIDUAL]) for row in rows])
    accepted = residual >= threshold
    if stage1_mask is not None:
        accepted &= stage1_mask
    gated = np.where(accepted, gain, 0.0)
    increment = gated - gain
    beneficial = gain > 0.0
    harmful = gain < 0.0
    false_accept = accepted & harmful
    false_reject = (~accepted) & beneficial
    center, low, high = seed_interval(rows, increment)
    false_accept_loss = -gain[false_accept]
    return {
        "protocol": protocol,
        "profile": profile,
        "scene_count": len(rows),
        "threshold": threshold,
        "ungated_gain_db": float(np.mean(gain)),
        "gated_gain_db": float(np.mean(gated)),
        "paired_increment_db": center,
        "paired_increment_ci95_low_db": low,
        "paired_increment_ci95_high_db": high,
        "median_scene_increment_db": float(np.median(increment)),
        "p05_scene_increment_db": float(np.quantile(increment, 0.05)),
        "pass_rate": float(np.mean(accepted)),
        "beneficial_count": int(np.sum(beneficial)),
        "harmful_count": int(np.sum(harmful)),
        "beneficial_retention": float(np.mean(accepted[beneficial])) if np.any(beneficial) else float("nan"),
        "harmful_rejection": float(np.mean(~accepted[harmful])) if np.any(harmful) else float("nan"),
        "false_accept_count": int(np.sum(false_accept)),
        "false_reject_count": int(np.sum(false_reject)),
        "false_accept_rate_all": float(np.mean(false_accept)),
        "false_reject_rate_all": float(np.mean(false_reject)),
        "false_accept_clean_loss_mean_db": float(np.mean(false_accept_loss)) if false_accept_loss.size else 0.0,
        "false_accept_clean_loss_max_db": float(np.max(false_accept_loss)) if false_accept_loss.size else 0.0,
        "stage1_ls_skip_rate": float(np.mean(~stage1_mask)) if stage1_mask is not None else 0.0,
    }


def grouped_metrics(
    rows: list[dict[str, object]], *, protocol: str, threshold: float,
    stage1_rule: dict[str, float] | None = None,
) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    profiles = sorted({str(row["profile"]) for row in rows})
    for profile in [*profiles, "All"]:
        selected = rows if profile == "All" else [row for row in rows if row["profile"] == profile]
        mask = None
        if stage1_rule is not None:
            mask = np.asarray(
                [
                    float(row[ZETA]) >= stage1_rule["minimum_zeta"]
                    and float(row[CLIPPING]) <= stage1_rule["maximum_clipping_rate"]
                    for row in selected
                ],
                dtype=bool,
            )
        output.append(
            metric_row(
                selected,
                protocol=protocol,
                profile=profile,
                threshold=threshold,
                stage1_mask=mask,
            )
        )
    return output


def calibrate_stage1(rows: list[dict[str, object]], stage2_threshold: float) -> dict[str, float]:
    zeta = np.asarray([float(row[ZETA]) for row in rows])
    clipping = np.asarray([float(row[CLIPPING]) for row in rows])
    gain = np.asarray([float(row[GAIN]) for row in rows])
    residual = np.asarray([float(row[RESIDUAL]) for row in rows])
    zeta_candidates = np.unique(np.r_[-np.inf, np.quantile(zeta, np.linspace(0, 1, 21))])
    clipping_candidates = np.unique(np.r_[np.inf, np.quantile(clipping, np.linspace(0, 1, 21))])
    candidates: list[dict[str, float]] = []
    for minimum_zeta in zeta_candidates:
        for maximum_clipping in clipping_candidates:
            stage1 = (zeta >= minimum_zeta) & (clipping <= maximum_clipping)
            accepted = stage1 & (residual >= stage2_threshold)
            candidates.append(
                {
                    "minimum_zeta": float(minimum_zeta),
                    "maximum_clipping_rate": float(maximum_clipping),
                    "stage2_threshold": float(stage2_threshold),
                    "validation_gated_gain_db": float(np.mean(np.where(accepted, gain, 0.0))),
                    "validation_pass_rate": float(np.mean(accepted)),
                    "validation_ls_skip_rate": float(np.mean(~stage1)),
                }
            )
    return max(
        candidates,
        key=lambda item: (
            item["validation_gated_gain_db"],
            item["validation_ls_skip_rate"],
        ),
    )


def sensitivity_rows(
    calibration: list[dict[str, object]], test: list[dict[str, object]], *, protocol: str,
) -> list[dict[str, object]]:
    values = np.asarray([float(row[RESIDUAL]) for row in calibration])
    output: list[dict[str, object]] = []
    for threshold in candidate_thresholds(values):
        for split, rows in [("validation", calibration), ("test", test)]:
            gain = np.asarray([float(row[GAIN]) for row in rows])
            residual = np.asarray([float(row[RESIDUAL]) for row in rows])
            accepted = residual >= threshold
            output.append(
                {
                    "protocol": protocol,
                    "split": split,
                    "threshold": float(threshold),
                    "is_tau_zero": int(float(threshold) == 0.0),
                    "gated_gain_db": float(np.mean(np.where(accepted, gain, 0.0))),
                    "increment_db": float(np.mean(np.where(accepted, gain, 0.0)) - np.mean(gain)),
                    "pass_rate": float(np.mean(accepted)),
                }
            )
    return output


def main() -> None:
    args = parse_args()
    rows = load_rows(args.source_csv)
    validation = [row for row in rows if row["split"] == "validation"]
    test = [row for row in rows if row["split"] == "test"]
    primary_cal = [row for row in validation if row["profile"] in {"A", "C"}]
    if any(row["profile"] == "D" for row in primary_cal):
        raise AssertionError("CDL-D leaked into primary calibration")

    protocols = {
        "primary_ac_only_zero_shot_d": calibrate(primary_cal),
        "secondary_acd_pooled": calibrate(validation),
    }
    metric_rows: list[dict[str, object]] = []
    sensitivity: list[dict[str, object]] = []
    for name, calibration_rows in [
        ("primary_ac_only_zero_shot_d", primary_cal),
        ("secondary_acd_pooled", validation),
    ]:
        threshold = float(protocols[name]["threshold"])
        metric_rows.extend(grouped_metrics(test, protocol=name, threshold=threshold))
        sensitivity.extend(sensitivity_rows(calibration_rows, test, protocol=name))
    metric_rows.extend(
        grouped_metrics(
            test,
            protocol="theory_fixed_tau_zero_no_calibration",
            threshold=0.0,
        )
    )

    leave_one_seed: list[dict[str, object]] = []
    for seed in sorted({int(row["seed"]) for row in primary_cal}):
        fit = [row for row in primary_cal if int(row["seed"]) != seed]
        heldout = [row for row in primary_cal if int(row["seed"]) == seed]
        rule = calibrate(fit)
        item = metric_row(
            heldout,
            protocol="leave_one_validation_seed_out",
            profile="A/C",
            threshold=float(rule["threshold"]),
        )
        item["heldout_seed"] = seed
        leave_one_seed.append(item)

    leave_one_profile: list[dict[str, object]] = []
    for heldout_profile in ["A", "C"]:
        fit = [row for row in primary_cal if row["profile"] != heldout_profile]
        heldout = [row for row in primary_cal if row["profile"] == heldout_profile]
        rule = calibrate(fit)
        item = metric_row(
            heldout,
            protocol="leave_one_profile_out",
            profile=heldout_profile,
            threshold=float(rule["threshold"]),
        )
        item["fit_profile"] = "C" if heldout_profile == "A" else "A"
        leave_one_profile.append(item)
        d_rows = [row for row in test if row["profile"] == "D"]
        d_item = metric_row(
            d_rows,
            protocol="single_profile_calibration_zero_shot_d",
            profile="D",
            threshold=float(rule["threshold"]),
        )
        d_item["fit_profile"] = item["fit_profile"]
        leave_one_profile.append(d_item)

    stage1 = calibrate_stage1(primary_cal, 0.0)
    stage1_metrics = grouped_metrics(
        test,
        protocol="ac_calibrated_stage1_then_theory_tau_zero_projection",
        threshold=0.0,
        stage1_rule=stage1,
    )
    metric_rows.extend(stage1_metrics)
    base_all = next(
        row for row in metric_rows
        if row["protocol"] == "theory_fixed_tau_zero_no_calibration" and row["profile"] == "All"
    )
    stage1_all = next(row for row in stage1_metrics if row["profile"] == "All")
    stage1["test_supported"] = bool(
        float(stage1_all["gated_gain_db"]) >= float(base_all["gated_gain_db"])
        and float(stage1_all["stage1_ls_skip_rate"]) > 0.0
    )

    output = ROOT / "05_results" / args.output_dir_name
    output.mkdir(parents=True, exist_ok=True)
    write_csv(output / "test_incremental_metrics.csv", metric_rows)
    write_csv(output / "leave_one_validation_seed_out.csv", leave_one_seed)
    write_csv(output / "leave_one_profile_out.csv", leave_one_profile)
    write_csv(output / "threshold_sensitivity.csv", sensitivity)
    write_csv(output / "protocol_rules.csv", [
        {"protocol": name, "calibration_profiles": "A/C" if name.startswith("primary") else "A/C/D", "normalization": "none", **rule}
        for name, rule in protocols.items()
    ] + [{
        "protocol": "theory_fixed_tau_zero_no_calibration",
        "calibration_profiles": "none",
        "normalization": "none",
        "threshold": 0.0,
        "validation_gated_gain_db": "not_applicable",
        "validation_increment_db": "not_applicable",
        "validation_pass_rate": "not_applicable",
    }])
    write_csv(output / "stage1_rule.csv", [stage1])

    digest = hashlib.sha256(args.source_csv.read_bytes()).hexdigest()
    result = {
        "source_csv": str(args.source_csv),
        "source_sha256": digest,
        "protocol_guards": {
            "primary_calibration_profiles": ["A", "C"],
            "primary_test_profiles": ["A", "C", "D"],
            "feature_normalization": "none",
            "d_used_for_primary_threshold": False,
            "d_used_for_primary_normalization": False,
        },
        "protocols": protocols,
        "test_metrics": metric_rows,
        "stage1_rule": stage1,
        "leave_one_validation_seed_out": leave_one_seed,
        "leave_one_profile_out": leave_one_profile,
    }
    (output / "summary.json").write_text(
        json.dumps(result, indent=2, allow_nan=True) + "\n", encoding="utf-8"
    )
    config = {
        "source_csv": str(args.source_csv),
        "source_sha256": digest,
        "output_dir_name": args.output_dir_name,
        "primary_calibration_profiles": ["A", "C"],
        "feature_normalization": "none",
    }
    command = "python 04_experiments/eval/run_tsp_candan_gate_protocol_audit.py"
    write_release_metadata(output, config=config, seeds=[], command=command)
    write_run_manifest(
        output,
        run_id="tsp_candan_gate_protocol_seventh_round_20260829",
        command=command,
        config=config,
        metrics={"source_rows": len(rows), "test_rows": len(test)},
        notes=[
            "Primary threshold uses validation CDL-A/C only; CDL-D is zero-shot.",
            "No feature normalization is applied, so CDL-D cannot enter normalization.",
            "All intervals are paired across the five test seeds.",
        ],
        cwd=ROOT,
    )
    print(json.dumps(result, indent=2, allow_nan=True))


if __name__ == "__main__":
    main()
