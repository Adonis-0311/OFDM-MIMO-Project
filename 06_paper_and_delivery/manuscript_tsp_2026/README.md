# TSP submission package

This directory contains the strengthened manuscript **“Projection-Selected Multidimensional Candan Refinement after FFT Tensor Support Selection.”**

## Submission files

- `latex/main.pdf`: IEEEtran manuscript.
- `latex/supplement_tsp.pdf`: optional expanded evidence and reproducibility material.
- `cover_letter_tsp.md`: cover letter.
- `prior_scope_rejection_statement.md`: separate prior-submission disclosure.
- `submission_compliance_2026-08-30.md`: current official-rule and package checklist.
- `submission_metadata.md`: title, abstract, keywords, EDICS suggestions, and upload descriptions.

The upload-ready files are assembled separately under
`../submission_tsp_2026-08-30/`. Internal revision records and QA renders are
kept in the working package and are not part of the journal upload set.

## Executed evidence

- `../../05_results/tsp_controlled_local_family_paper/`: 1200-scene controlled local-family comparison.
- `../../05_results/tsp_unified_runtime_paper/`: single end-to-end timing ledger with identical scenes, dtype, thread count, warm-up, and output boundary.
- `../../05_results/tsp_full_offset_sweep_paper/`: complete fractional-bin range and radius sweep.
- `../../05_results/tsp_support_quality_stratification_paper/`: support-coverage, collision, conditioning, and gain strata.
- `../../05_results/tsp_candan_stress_zeta_audit_paper/`: pure-Candan 48-cell separation–dynamic-range–SNR study with all-component, pair, strict, strong/weak, clipping, and stability metrics.
- `../../05_results/tsp_candan_cdl_audit_paper/`: true Candan comparator on the frozen CDL test geometry.
- `../../05_results/tsp_candan_gate_protocol_seventh_round/`: calibration-free zero-threshold selection, paired increments, and protocol audits.
- `../../05_results/tsp_projection_gate_runtime_seventh_round/`: projection-energy equivalence and optimized runtime ledger.
- `../../05_results/tsp_candan_physical_zeta_audit_paper/`: 9000-scene physical-parameter and quotient-stability replay.
- `../../05_results/matlab_taes_supplement/candan_independent_*.csv`: independent 1200-scene MATLAB replication.

See [the repository reproduction guide](../../REPRODUCIBILITY.md) for full paths, dependency order, registered ledgers, and provenance limitations. The controlled-family metadata is embedded in its run manifest; the independent MATLAB output does not contain a complete run manifest.

## Build

From the repository root:

```powershell
python 06_paper_and_delivery/manuscript_tsp_2026/scripts/build_tsp_tables.py
```

The table command rebuilds the eight tables consumed by the current submission. Quantitative figure sources are in `matlab_figures/`; the overview source is in `visio_figures/`. See the root guide for their portable commands. The older Python figure builder targets historical layouts and missing exploratory ledgers.

Then from `06_paper_and_delivery/manuscript_tsp_2026/latex`:

```powershell
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
latexmk -pdf -interaction=nonstopmode -halt-on-error supplement_tsp.tex
```

The audit verified 25 tests in `tests/test_stage1_modules.py` and `tests/test_local_refinement_baselines.py`. The full `pytest -q` suite is not currently a valid public entry: `tests/test_candan_gate_protocol.py` imports an unpublished historical crossfit script. See the root audit for the collection failure.
