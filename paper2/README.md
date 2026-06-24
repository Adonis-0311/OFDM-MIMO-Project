# mmWave ISAC T-OMP-Net Thesis Workspace

This repository is a cleaned research workspace for the graduation-design-to-paper upgrade:

> Sparse Tensor-OMP Deep Unfolding Network with Physical-Constrained Off-Grid Refinement for Joint Channel and Target Parameter Estimation in mmWave MIMO-OFDM ISAC Systems

The operational baseline is `ISAC_DeepUnfolding_TechnicalDesign_v2.2.md`.

## Current Status

- Existing MATLAB prototype: OFDM/MIMO channel-estimation modules under `Config/` and `Modules/`.
- Existing thesis materials are kept locally under `2025刘雨辉毕设/` but are ignored by Git because they include personal documents and large reference archives.
- First v2.2 supplemental experiment is implemented in `eval/run_oversampling_offgrid_ablation.m`.

## Reproduce the First Supplemental Experiment

From MATLAB:

```matlab
run('eval/run_oversampling_offgrid_ablation.m')
```

To rerun all lightweight v2.2 supplemental experiments and regenerate the manifest:

```matlab
run('eval/run_all_v2_2_supplemental_experiments.m')
```

From PowerShell with the local MATLAB installation:

```powershell
& 'D:\E\MATLAB\bin\matlab.exe' -batch "run('D:\E\OFDM-MIMO_Radar_Estimation\eval\run_oversampling_offgrid_ablation.m')"
```

Outputs are written to:

```text
Results/oversampling_offgrid_ablation/
```

The current outputs include:

- `oversampling_offgrid_ablation.csv`
- `oversampling_offgrid_ablation.png`
- `oversampling_offgrid_ablation.pdf`
- `summary.md`

The Kruskal/target-count degradation smoke experiment can be run with:

```matlab
run('eval/run_kruskal_identifiability_ablation.m')
```

It writes results to:

```text
Results/kruskal_identifiability_ablation/
```

The off-grid mismatch lemma validation can be run with:

```matlab
run('eval/run_offgrid_mismatch_lemma_validation.m')
```

It writes results to:

```text
Results/offgrid_mismatch_lemma/
```

The CDL-A/C/D-like communication generalization smoke experiment can be run with:

```matlab
run('eval/run_cdl_profile_generalization_smoke.m')
```

It writes results to:

```text
Results/cdl_profile_generalization_smoke/
```

The combined evidence index is written to:

```text
Results/v2_2_supplemental_manifest.md
```

## Repository Layout

```text
Config/                  MATLAB configuration prototype
Modules/                 Existing channel/model/algorithm/evaluation modules
baseline/                Planned classical baselines: LS, OMP, Tensor-OMP, CRLB
tompnet/                 Planned T-OMP-Net and off-grid modules
train/                   Planned training scripts
eval/                    Reproducible evaluation and ablation scripts
paper/                   Design notes, usable-content inventory, manuscript assets
literature_2024_2025/    Planned SOTA tracking notes
Results/                 Regenerable experiment outputs
```

## Upload Policy

The Git history should include source code, design Markdown, reproducible experiment scripts, and lightweight result artifacts. It should not include private graduation paperwork, contracts, compressed reference packages, downloaded datasets, or `.mat` model/data blobs.

## Publish To GitHub

After authenticating GitHub CLI:

```powershell
gh auth login
.\scripts\publish_to_github.ps1
```

The script creates a private `mmwave-isac-tompnet` repository when `origin` is missing, then pushes the current branch. Use `-RepoName` or `-Visibility public` if needed.
