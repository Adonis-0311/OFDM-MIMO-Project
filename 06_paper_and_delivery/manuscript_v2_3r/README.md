# v2.3R Manuscript Workspace

This directory is the active manuscript workspace for the v2.3R paper line.

Authoritative controls:

- `../../01_design_and_plan/ISAC_DeepUnfolding_TechnicalDesign_v2.3R.md`
- `../paper_notes/v2_3r_section_plan.md`
- `../../05_results/v2_3r_paper_evidence_table/paper_evidence_table.md`

Delivery language requirement:

- The active venue-facing output is the English IEEEtran manuscript for IEEE Systems Journal / IEEE TVT. The former MDPI Sensors template and Chinese parallel-output requirement are superseded for this submission round.

Current state:

- `latex/main.tex` and `latex/main.pdf` are the canonical identity-corrected manuscript.
- `main.md` is a current navigation and abstract checkpoint.
- `sections/*.md` are historical drafting snapshots; active section prose is under `latex/sections/`.
- `displays/` contains current paper-facing figure/table candidates.
- `paper_experiment_matrix.md` maps paper claims to result artifacts.
- `claim_evidence_ledger.json` records claim support and boundaries.
- `latex/` contains an eight-page IEEEtran journal draft and `latex/main.pdf`.
- `../../05_results/deepmimo_source_alpha_seed_campaign/` contains the scaled five-seed, 100-user O1_60/I3_60 scalar source-alpha robustness evidence.
- `../../05_results/sionna_cdl_profile_generalization_scaled/` contains the five-seed, 50-sample/profile/seed CDL-A/C/D support-resolution diagnostic.
- `../../05_results/sionna_cdl_physical_metrics_grid_baseline/` contains CIR-grounded delay/projected-angle grid metrics and the clean-grid representation floor.
- `../../05_results/sionna_cdl_ac_alias_lock_selected_scaled/` contains the scaled held-out CDL-A/C trained-controller result.
- `../../05_results/sionna_cdl_d_alias_lock_selected_zero_shot_scaled/` contains the matching-scale unseen CDL-D failure boundary.

Do not promote blocked or downgraded evidence into main claims:

- The local G2 scalar, the CDL 210-parameter controller, and the deterministic A4 diagnostic are separate executable paths; do not describe them as one validated deep K-stage T-OMP-Net.
- A4 is limited to high-L/platform early stopping for `L>=32` at the core 20 dB setting; SNR sensitivity, scalar-threshold frontier, and SNR-aware gate diagnostics are boundary evidence.
- A5/HIR-JL is appendix/high-stress only.
- DeepMIMO access and the scaled scalar-alpha proxy campaign are ready: O1_60 is `weak`, while I3_60 remains `partial` because its worst cell has negative gain and low support recall.
- Do not promote the DeepMIMO proxy campaign to final Set E performance until the full trained estimator and physical angle/delay metrics are available.
- Sionna CDL-A/C now carries a scaled trained-estimator result: channel, delay, and projected-angle aggregate improvements all have positive seed-level confidence intervals. CDL-D remains a zero-shot channel/delay failure boundary, so the claim is profile-scoped.
- CRLB evidence is single-target high-SNR trend consistency, not full multi-target efficiency.

Next writing pass:

- Audit remaining accepted-paper metadata and replace provisional arXiv fields when final issue data become available.
- Complete a matched comparator-accuracy study only if an NMSE--complexity Pareto claim is retained.
- Treat any future A4 expansion as a refinement-schedule or training-objective redesign problem before retesting cross-SNR early stopping.
