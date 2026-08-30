# IEEE TSP Final Build and Verification Report

Date: 2026-08-30

## Deliverables

- Main manuscript: `latex/main.pdf` (8 pages, 627481 bytes).
- Supplementary material: `latex/supplement_tsp.pdf` (6 pages, 249156 bytes).
- Formal upload package: `../submission_tsp_2026-08-30/`.
- Self-contained source archive: `../submission_tsp_2026-08-30/TSP_source.zip`.
- MATLAB evidence-figure entry point: `matlab_figures/generate_tsp_figures.m`.
- Visio workflow-diagram entry point: `visio_figures/build_visio_diagrams.ps1`.

## Verification

- Python test suite: 47 passed.
- MATLAB Code Analyzer: zero findings across all 20 manuscript figure source files; the separate safety scan found no high-risk behavior and export writes are confined to the manuscript figure directory.
- Microsoft Visio 16.0 redraw: editable VSDX plus PDF/SVG/PNG exports generated successfully for the consolidated page-wide estimator overview.
- Working and standalone-source LaTeX builds: successful with `latexmk`.
- Log audit: no overfull boxes, undefined citations/references, or LaTeX errors.
- PDF audit: Letter format and all fonts embedded in the manuscript, supplementary material, cover letter, and prior-submission disclosure.
- Main-body self-containment scan: no references to supplementary material or appendices.
- AI wording scan: no specific AI product or model names; the acknowledgment states only language-polishing use.
- Abstract: 212 source-counted words.
- Source ZIP audit: no auxiliary logs, QA renders, TIFF files, or temporary build files.
- Package integrity: SHA-256 checksums verified for all five upload artifacts.

## Final Content Closure

- Defined the vectorized observation, tensor design matrix, coordinate matrices, orthogonal projectors, and numerical denominator constant used by the joint-LS and projection rule.
- Defined reconstruction gain and tenth-, quarter-, and half-bin all-axis accuracy in the main manuscript.
- Added the exact quadratic, Cartesian, and one-step Newton comparator contracts and the CPU/software timing environment.
- Aligned headline evidence with the local Candan stage and the complete projection-selected estimator.
- Framed the theory as triplet-perturbation analysis after FFT neighborhood selection and used the controlled campaign as complementary support evidence.
- Reorganized the four main figures into overview, theory mechanism, matched-scene headline evidence, and controlled-stress robustness; all are cited explicitly in the main text and appear before the references.
- Moved the profile visualization to the supplementary material while preserving the exact profile table in the self-contained main paper.
- Consolidated the duplicated system-model and method-flow drawings, widened both return blocks, and rerouted the projection-selection branches in Visio; final-size page inspection shows no text overflow or connector-label overlap.
- Replaced the former crowded Fig. 3 with seed-paired gain intervals, an SNR--target-count gain map, and separately accounted runtime evidence.
- Balanced the final reference page at references [25]--[31], eliminating the former one-line ninth page.
