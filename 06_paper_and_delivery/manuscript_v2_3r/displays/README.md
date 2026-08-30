# v2.3R Displays

Generated: 2026-06-29

This directory contains the current paper-facing display candidates for the v2.3R manuscript.

## Figures

- `figures/v2_3r_system_model.{pdf,png}`
- `figures/v2_3r_refinement_paths.{pdf,png}`
- `figures/v2_3r_evidence_summary.png`
- `figures/v2_3r_evidence_summary.pdf`
- `figures/v2_3r_cdl_profile_evidence.{pdf,png}`
- `figures/v2_3r_graphical_abstract.{pdf,png}`
- `captions.md`
- `FIGURE_QA_2026_06_29.md`

Purpose: show the current empirical story in one compact display:

1. The system and architecture figures make the physical tensor model and unfolded estimator explicit.
2. G2 bounded off-grid refinement is locally supported for L={2,4,8}.
3. A4 plateau early stopping is positive only for high-L cells at the core 20 dB setting.
4. Held-out CDL-A/C is positive in aggregate, while zero-shot CDL-D remains a visible failure boundary.
5. The graphical abstract packages the method/evidence story as a separate submission asset.

## Tables

- `tables/v2_3r_main_result_table.md`
- `tables/v2_3r_a4_snr_sensitivity_table.md`
- `tables/v2_3r_g2_l_summary.csv`
- `tables/v2_3r_a4_cross_l_summary.csv`
- `tables/v2_3r_a4_snr_summary.csv`

## Reproducibility

Regenerate all displays with:

```text
python 06_paper_and_delivery/manuscript_v2_3r/displays/scripts/build_v2_3r_paper_displays.py
python 06_paper_and_delivery/manuscript_v2_3r/displays/scripts/build_v2_3r_landing_figures.py
```

Source data are listed in `figure_catalog.json`.
