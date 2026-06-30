from __future__ import annotations

import csv
import json
from pathlib import Path

import torch
from sionna.phy import config as sionna_config
from sionna.phy.channel import cir_to_ofdm_channel, subcarrier_frequencies
from sionna.phy.channel.tr38901.antenna import PanelArray
from sionna.phy.channel.tr38901.cdl import CDL


ROOT = Path(__file__).resolve().parents[2]


def shape_text(tensor: torch.Tensor) -> str:
    return "x".join(str(dim) for dim in tensor.shape)


def main() -> None:
    config = {
        "profile": "A",
        "carrier_frequency_hz": 60e9,
        "delay_spread_s": 100e-9,
        "subcarrier_spacing_hz": 120e3,
        "num_subcarriers": 64,
        "batch_size": 2,
        "num_time_steps": 1,
        "sampling_frequency_hz": 64 * 120e3,
        "device": "cpu",
        "direction": "downlink",
        "ut_array": "1x1 single-polarized omni",
        "bs_array": "1x4 single-polarized 38.901",
        "seed": 20260626,
    }
    torch.manual_seed(int(config["seed"]))
    sionna_config.seed = int(config["seed"])

    carrier_frequency = float(config["carrier_frequency_hz"])
    ut_array = PanelArray(
        num_rows_per_panel=1,
        num_cols_per_panel=1,
        polarization="single",
        polarization_type="V",
        antenna_pattern="omni",
        carrier_frequency=carrier_frequency,
        device=str(config["device"]),
    )
    bs_array = PanelArray(
        num_rows_per_panel=1,
        num_cols_per_panel=4,
        polarization="single",
        polarization_type="V",
        antenna_pattern="38.901",
        carrier_frequency=carrier_frequency,
        device=str(config["device"]),
    )
    model = CDL(
        model=str(config["profile"]),
        delay_spread=float(config["delay_spread_s"]),
        carrier_frequency=carrier_frequency,
        ut_array=ut_array,
        bs_array=bs_array,
        direction=str(config["direction"]),
        min_speed=0.0,
        max_speed=0.0,
        device=str(config["device"]),
    )

    h_cir, tau = model(
        batch_size=int(config["batch_size"]),
        num_time_steps=int(config["num_time_steps"]),
        sampling_frequency=float(config["sampling_frequency_hz"]),
    )
    frequencies = subcarrier_frequencies(
        int(config["num_subcarriers"]),
        float(config["subcarrier_spacing_hz"]),
        device=str(config["device"]),
    )
    h_ofdm = cir_to_ofdm_channel(frequencies, h_cir, tau, normalize=True)

    # Sionna shape: [batch, rx, rx_ant, tx, tx_ant, time, subcarrier].
    # T-OMP-Net-facing smoke tensor: [batch, subcarrier, tx_ant, rx_ant].
    tomp_tensor = h_ofdm[:, 0, 0, 0, :, 0, :].permute(0, 2, 1).unsqueeze(-1)
    finite = bool(torch.isfinite(tomp_tensor.real).all() and torch.isfinite(tomp_tensor.imag).all())
    mean_power = float(torch.mean(torch.abs(tomp_tensor) ** 2).item())
    max_abs = float(torch.max(torch.abs(tomp_tensor)).item())
    metrics = {
        "status": "ok" if finite else "non_finite",
        "h_cir_shape": shape_text(h_cir),
        "tau_shape": shape_text(tau),
        "h_ofdm_shape": shape_text(h_ofdm),
        "tomp_tensor_shape": shape_text(tomp_tensor),
        "finite": finite,
        "mean_power": mean_power,
        "max_abs": max_abs,
        "torch_version": torch.__version__,
    }

    output_dir = ROOT / "05_results" / "sionna_cdl_smoke"
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "sionna_cdl_smoke.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(metrics.keys()))
        writer.writeheader()
        writer.writerow(metrics)

    manifest = {
        "run_id": "sionna_cdl_smoke_20260626",
        "command": "python 04_experiments/eval/run_sionna_cdl_smoke.py",
        "config": config,
        "metrics": metrics,
        "notes": [
            "Sionna 2.x API path is sionna.phy.channel.tr38901.cdl.CDL.",
            "This smoke validates profile CDL-A generation and conversion from CIR to OFDM subcarrier response.",
            "The smoke tensor is shaped for later adapter work, not yet a full E1 profile-generalization experiment.",
        ],
    }
    manifest_path = output_dir / "run_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "# Sionna CDL Smoke",
        "",
        f"- Status: `{metrics['status']}`",
        f"- Profile: `CDL-{config['profile']}`",
        f"- Carrier frequency: `{config['carrier_frequency_hz']}` Hz",
        f"- Subcarriers: `{config['num_subcarriers']}`",
        f"- CIR shape: `{metrics['h_cir_shape']}`",
        f"- OFDM channel shape: `{metrics['h_ofdm_shape']}`",
        f"- T-OMP-Net-facing tensor shape: `{metrics['tomp_tensor_shape']}`",
        f"- Mean power after normalization: `{metrics['mean_power']:.6g}`",
        f"- Max magnitude: `{metrics['max_abs']:.6g}`",
        "",
        "## Interpretation",
        "",
        "Sionna CDL-A generation is available through the open-source Python route. The next E1 script can lift this smoke into CDL-A/C/D profile sweeps and metric evaluation against Tensor-OMP/T-OMP-Net baselines.",
        "",
    ]
    (output_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {csv_path.relative_to(ROOT)}")
    print(f"wrote {manifest_path.relative_to(ROOT)}")
    print(f"status={metrics['status']}")
    if metrics["status"] != "ok":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
