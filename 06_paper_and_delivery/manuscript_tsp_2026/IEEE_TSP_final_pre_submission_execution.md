# IEEE TSP Final Pre-Submission Execution

Date: 2026-08-29

The minimal pre-submission revision was executed with the existing paper identity, theory, algorithm, and experiment suite held fixed.

## Completed Changes

- Figure 3 proposed point: `Projection-selected Candan`, `11.24 ms`.
- Legacy `18.98 ms` implementation: retained only as `Explicit two-residual implementation` in the supplementary runtime table.
- Supplementary Table I: removed the repeated runtime column and redundant legacy Cartesian row; defined `Improved` as the scene fraction with lower clean-channel NMSE than grid.
- Discussion: added one compact paragraph on reconstruction versus parameter metrics and one compact paragraph on controlled-pair interpretation.
- Figure 5(a): renamed to `Projection-selected minus Candan gain (dB)`.
- Terminology: active manuscript uses `projection-selected Candan`, `projection selection`, and `fitted-energy difference` consistently.

## Final Verification

- Main manuscript: 8 pages.
- Supplementary material: 5 pages.
- Python tests: 47 passed.
- MATLAB Code Analyzer: zero findings across the active generator, six figure makers, and shared helpers.
- LaTeX logs: no overfull boxes, undefined citations/references, LaTeX errors, or infinite-glue warnings.
- BibTeX: zero warnings.
- Six active MATLAB figure bundles: PDF, SVG, PNG, and TIFF exports present.
- Page-level visual inspection: Figure 3, Figure 5, Discussion, and Supplementary Table I passed.

The manuscript package is ready for the journal's official LaTeX Analyzer, Reference Preparation Assistant, and PDF Checker during submission upload.
