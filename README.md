# IEEE T-SP reproducibility materials

**Projection-Selected Multidimensional Candan Refinement after FFT Tensor Support Selection**

This is the public entry point for the **2026-08-30 T-SP submission**. The submission materials were originally committed on `codex/submission-ready-v2.3r` at `8429794ebbdf72eb7c01570d6362137731041a38`; `main` now carries that snapshot and the audited reproduction entry points.

- [Main manuscript PDF](06_paper_and_delivery/submission_tsp_2026-08-30/TSP_main_manuscript.pdf)
- [Supplementary material PDF](06_paper_and_delivery/submission_tsp_2026-08-30/TSP_supplementary_material.pdf)
- [Reproduction guide: exact paths, commands, dependencies, and limitations](REPRODUCIBILITY.md)
- [Self-contained manuscript source](06_paper_and_delivery/submission_tsp_2026-08-30/source/README.md)
- [Branch and path audit](07_ops/reproducibility_audit_2026-10-06/README.md)

## Find the materials promised in the paper

| Material | Public location |
|---|---|
| Synthetic and CDL generators | [Synthetic tensor generator](03_active_modules/data/offgrid_tensor.py), [CDL generator](04_experiments/eval/run_sionna_cdl_profile_generalization.py) |
| Controlled local-family evaluation | [Python entry point](04_experiments/eval/run_tsp_controlled_local_family_baselines.py), [registered rows and summary](05_results/tsp_controlled_local_family_paper) |
| Projection selection and runtime | [Protocol audit](04_experiments/eval/run_tsp_candan_gate_protocol_audit.py), [runtime entry point](04_experiments/eval/run_tsp_projection_gate_runtime.py), [protocol ledgers](05_results/tsp_candan_gate_protocol_seventh_round), [runtime ledgers](05_results/tsp_projection_gate_runtime_seventh_round) |
| Aggregate tables | [Paper tables](06_paper_and_delivery/manuscript_tsp_2026/tables), [table generator](06_paper_and_delivery/manuscript_tsp_2026/scripts/build_tsp_tables.py) |
| Independent MATLAB implementation | [Experiment 6](04_experiments/matlab/exp6_candan_independent_audit.m), [1200-scene rows](05_results/matlab_taes_supplement/candan_independent_rows.csv), [summary](05_results/matlab_taes_supplement/candan_independent_summary.csv) |
| Figure sources | [MATLAB quantitative figures](06_paper_and_delivery/manuscript_tsp_2026/matlab_figures), [editable Visio overview](06_paper_and_delivery/manuscript_tsp_2026/visio_figures), [submitted vector figures](06_paper_and_delivery/submission_tsp_2026-08-30/source/figures) |

The guide maps every supplementary reproduction entry to its full repository path. Reviewers can inspect the registered CSV/JSON evidence and rebuild the eight current tables without rerunning the experiments.

The older T-OMP-Net/TAES workspace remains for provenance; its previous root README is [archived here](90_archive/design_history/README_pre_tsp_2026-10-06.md).
