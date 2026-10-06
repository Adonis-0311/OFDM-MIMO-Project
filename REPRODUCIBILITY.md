# Reproduce the 2026-08-30 T-SP submission

The authoritative upload set is
[submission_tsp_2026-08-30](06_paper_and_delivery/submission_tsp_2026-08-30).
Working sources and figure/table builders are under
[manuscript_tsp_2026](06_paper_and_delivery/manuscript_tsp_2026).
Use `main` for the public entry point. The original submission snapshot is
`8429794ebbdf72eb7c01570d6362137731041a38`.

## Paths printed in the supplement

Run Python commands from the repository root. Every abbreviated Python
filename in the supplement lives in `04_experiments/eval/`. The printed
`manuscript_tsp_2026/matlab_figures/generate_tsp_figures.m` path omits the
`06_paper_and_delivery/` prefix.

| Evidence | Script under `04_experiments/eval/` | Registered directory under `05_results/` |
|---|---|---|
| Common local family, 1200 test + 480 validation scenes | `run_tsp_controlled_local_family_baselines.py` | `tsp_controlled_local_family_paper/` |
| Common end-to-end timing | `run_tsp_unified_runtime_benchmark.py` | `tsp_unified_runtime_paper/` |
| Full fractional-bin interval and radius sweep | `run_tsp_full_offset_sweep.py` | `tsp_full_offset_sweep_paper/` |
| Support, collisions, conditioning | `run_tsp_support_quality_stratification.py` | `tsp_support_quality_stratification_paper/` |
| 48-cell separation / near-far / SNR study | `run_tsp_candan_stress_zeta_audit.py` | `tsp_candan_stress_zeta_audit_paper/` |
| Ungated CDL comparator | `run_tsp_candan_cdl_audit.py` | `tsp_candan_cdl_audit_paper/` |
| Frozen CDL source rows | `run_tsp_candan_route_audit.py` | `tsp_candan_route_audit_paper/` |
| Projection-selection protocols | `run_tsp_candan_gate_protocol_audit.py` | `tsp_candan_gate_protocol_seventh_round/` |
| Dedicated projection runtime | `run_tsp_projection_gate_runtime.py` | `tsp_projection_gate_runtime_seventh_round/` |
| 9000-scene physical / quotient-stability replay | `run_tsp_candan_physical_zeta_audit.py` | `tsp_candan_physical_zeta_audit_paper/` |

The independent implementation is
`04_experiments/matlab/exp6_candan_independent_audit.m`; its two
`candan_independent_*.csv` files are in `05_results/matlab_taes_supplement/`.
Python uses `03_active_modules/data/offgrid_tensor.py` for synthetic scenes
and `generate_profile_channels` in
`04_experiments/eval/run_sionna_cdl_profile_generalization.py` for CDL scenes.
MATLAB uses `04_experiments/matlab/common/gen_offgrid_sample.m` and its portable
RNG helpers.

## Environment and replay order

The recorded Python is 3.12.10 and NumPy is 2.5.0. CPU timing uses complex128,
one thread, one warm-up, and three repetitions on an Intel Core Ultra 7 265KF.
Timing on another machine is expected to differ. `environment.txt` and the
manifests preserve the measured environment.

An installation recipe for an isolated environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ./03_active_modules "sionna==2.0.1" "numpy==2.5.0"
python 04_experiments/eval/run_tsp_controlled_local_family_baselines.py --help
```

This is not a complete dependency lock or a verified fresh-environment install.
The historical `requirements_sensors.txt` pins NumPy 2.2.6 and does not describe
the measured T-SP environment. The omitted four-file synthetic generator package has been restored from
existing workspace source. All ten entries passed `--help` after repair with
installed editable-workspace fallbacks disabled.

Replay a listed script with `python 04_experiments/eval/<script>`, following
its `command.txt` and configuration, or the embedded `command` and `config`
in its manifest. Defaults write into registered result directories; use a
separate checkout to preserve the distributed outputs.

Run the controlled-family campaign before unified runtime, which reads its
threshold. Run the CDL route audit before the protocol audit and physical
replay. Run the protocol audit before dedicated projection runtime, which
reads its `summary.json`. All prerequisite artifacts are already distributed;
inspection and paper rebuilding do not require regenerating them.

For the proposed calibration-free rule, select protocol
`theory_fixed_tau_zero_no_calibration` in
`tsp_candan_gate_protocol_seventh_round/test_incremental_metrics.csv`.
The CSV also includes calibrated comparators; the entry named
`primary_ac_only_zero_shot_d` is a calibrated audit comparator.

## Tables, figures, and manuscript

Rebuild the eight tables consumed by the main paper and supplement:

```powershell
python 06_paper_and_delivery/manuscript_tsp_2026/scripts/build_tsp_tables.py
```

The audited builder reproduces all eight committed tables byte for byte from
registered CSVs and selects the calibration-free protocol. Historical table
functions remain available but are not invoked by the default entry point.

From the repository root in MATLAB R2025a:

```matlab
addpath(fullfile(pwd,'06_paper_and_delivery','manuscript_tsp_2026','matlab_figures'));
generate_tsp_figures;
```

This generates five quantitative/mechanism bundles. The page-wide overview
has an editable Visio source; the supplement's statement that all figures
are generated by MATLAB needs this correction. From the repository root on
a machine with Microsoft Visio:

```powershell
powershell -ExecutionPolicy Bypass -File 06_paper_and_delivery/manuscript_tsp_2026/visio_figures/build_visio_diagrams.ps1
```

The earlier `scripts/build_tsp_figures.py` targets historical layouts and
unpublished exploratory ledgers and is not the current figure entry point.
Submitted vector PDFs are included for readers without MATLAB or Visio.
MATLAB/Visio exports were inspected statically, not executed in this audit.

Run only the independent 1200-scene replication in MATLAB:

```matlab
addpath(fullfile(pwd,'04_experiments','matlab'));
exp6_candan_independent_audit;
```

It uses `table` and `writetable`; the older package README's general GNU Octave
compatibility claim is not verified for Experiment 6. Its confidence interval
uses normal 1.96 over five seed means, whereas the Python campaigns use their
documented Student-t intervals. Preserve that distinction when interpreting
the supplementary interval descriptions.

For the packaged LaTeX source, change to
`06_paper_and_delivery/submission_tsp_2026-08-30/source/latex` and run:

```powershell
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
latexmk -pdf -interaction=nonstopmode -halt-on-error supplement_tsp.tex
```

## Provenance limits

The controlled-family manifest embeds command, configuration, seeds,
environment, and Git identifier, but lacks the separate metadata sidecars
used by later releases. The independent MATLAB output has rows and summaries
but lacks a complete run manifest. Both have their implementation and results.

Several manifests identify `c50a603`, an earlier committed base, although
released scripts were committed later. That identifier alone does not capture
the exact executed source. Some audits also record code/input SHA256 values;
the route input digest was verified. A complete environment lock and exact
executed-source archive would strengthen provenance without adding experiments.

See the [audit report](07_ops/reproducibility_audit_2026-10-06/README.md) for
branch coverage, documentation errors, missing historical artifacts, and
verification limits. The full test suite also has a known collection failure: a gate test imports
`run_tsp_crossfit_predictive_gate.py`, which is not committed. The audit passed
25 existing generator/recovery and local-refinement tests in isolation.
This audit did not replay the numerical experiments.
