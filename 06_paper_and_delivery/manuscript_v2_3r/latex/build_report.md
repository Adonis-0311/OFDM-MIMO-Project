# v2.3R IEEEtran Build Report

Generated: 2026-06-30

## Verification gate

- Build: `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex` passed.
- PDF: `main.pdf`, IEEEtran journal, two columns, 10 pages.
- Venue budget: within IEEE Systems Journal's 12-page review limit and TVT's 14-page initial-submission limit.
- Bibliography: 42 cited entries; every entry has DOI or URL metadata where applicable.
- Cross-references/citations: resolved; no overfull boxes. Underfull warnings are non-blocking.
- Tests: 28 passed.

## Evidence landed

- G2: 5 seeds, 30 held-out scenes per L/seed; mean gain 5.8956 dB, minimum L-cell 5.3863 dB, seed-mean 95% CI [5.7830, 6.0083] dB.
- E12: 1200 paired scenes; NOMP-inspired mean advantage over the learned scalar 42.1756 dB and median runtime ratio 8.106x.
- PARAFAC: 1200 matched rows, mean NMSE -16.8550 dB, zero numerical failures. FB-ESPRIT is explicitly timing-only because cross-axis pairing is unavailable.
- A4: 5 seeds and 5 test curves/cell; L>=32 minimum mean saving 26.5% and maximum seed-cell mean gap 0.4957 dB; L=16 remains boundary evidence.

## Visual QA

The PDF was rendered at 140 dpi. The revised two-panel compute-accuracy figure was inspected both at source resolution and at its actual double-column PDF size. No text overlaps, clipped labels, marker-label collisions, or out-of-frame elements remain. The dashed line identifies only non-dominated methods; the caption explicitly states that the learned scalar is not Pareto-optimal under end-to-end wall-clock.

## Remaining author-side metadata

Author names, affiliations, ORCIDs, funding information, and final target-journal fields must be filled before portal submission. Integrated K-stage estimation and trained DeepMIMO physical evaluation are deferred future work, not blockers for the narrowed paper.
