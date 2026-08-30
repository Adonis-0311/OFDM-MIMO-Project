# Self-contained LaTeX source

The source tree contains the files required to compile the main manuscript and supporting material. The two PDFs in `latex/` are verified standalone-build outputs included for comparison.

From the `source/latex` directory, run:

```powershell
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
latexmk -pdf -interaction=nonstopmode -halt-on-error supplement_tsp.tex
```

The main manuscript uses IEEEtran, five active vector PDF figures, eight section files, two bibliography databases, and the profile-results table. The supporting material reuses the same source tree and adds expanded tables for reviewers who wish to inspect the evidence in greater detail.
