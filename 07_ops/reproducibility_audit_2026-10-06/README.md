# T-SP public reproducibility audit — 2026-10-06

## Scope and branch coverage

GitHub's paginated branch API and `git ls-remote --symref` agreed: the public
repository had exactly two branches at audit time. Default branch: `main`.
The authenticated account had admin and push permissions; neither branch
was protected.

| Branch before repair | Commit | Commit date | Tracked files |
|---|---|---|---:|
| `main` | `04273d4c883ef073d20654ee1d9c5ecba303cdaa` | 2026-06-24 | 136 |
| `codex/submission-ready-v2.3r` | `8429794ebbdf72eb7c01570d6362137731041a38` | 2026-08-30 | 1029 |

There were no additional remote branches to leave unchecked. Local tracking
names, including the older `https-tsp` reference, are not additional GitHub
branches. The latest submission commit was already published remotely.
`main` is an ancestor of the submission commit; promotion can preserve history
with a fast-forward and requires no forced update.

Read-only inspection used both complete committed trees, the main manuscript
and supplement, the assembled submission source, implementation imports,
registered results, metadata, and active figure sources. The current original
working directory has unrelated modified/untracked files; repairs were made
in an isolated checkout of the published snapshot.

## Per-path findings

[branch_path_matrix.csv](branch_path_matrix.csv) lists 229 paths, their source
references, and existence on both original branch heads. 225 exist on the submission branch and are absent from the original `main`.
Four generator-package files are absent from both original branch heads. The inventory
includes every `\path{...}` entry in the T-SP sources after resolving printed
abbreviations, T-SP evaluation scripts, MATLAB/Visio sources, result files,
and the manuscript's TeX sources. This distinguishes the main branch misalignment from a real generator-package
omission on both original branches.

The normalized matrix does not mean the printed abbreviations are valid
repository-root paths. [The guide](../../REPRODUCIBILITY.md) records exact
script/result mappings and path corrections.

| Finding | Evidence and impact | Minimum repair / status |
|---|---|---|
| Default branch points to an old workspace | All audited T-SP paths are off `main` | Promote published `8429794` content to `main`, preserving history |
| Synthetic generator package absent on both branches | Windows `Data/` ignore rule also matched `03_active_modules/data/`; eight isolated entry checks fail without local editable-package fallback | Restore four existing generator source files and scope ignore rule to root `/Data/` |
| Latest branch also has an old root README | Root navigation prioritizes T-OMP-Net, v2.2/v2.3R and machine-specific commands | Replace root navigation with current paper, supplement, evidence and source links; archive previous README |
| Incorrect relative paths in T-SP package README | `../../../05_results/` climbs one level above the repository | Correct to `../../05_results/` |
| Supplement's MATLAB figure path omits a directory | Printed `manuscript_tsp_2026/...` does not exist at root | Supply full `06_paper_and_delivery/...` path in public guide; correct paper text in its next revision |
| Abbreviated Python and MATLAB script paths | Most supplement entries omit the enclosing directory | Explicit mapping in public guide |
| README's table command fails on a fresh published checkout | `gate_cells()` reads absent `tsp_reliability_gate_round2_paper/reliability_gate_cell_summary.csv` | Default builder now calls only functions for the eight current submission tables |
| Profile table source is from an older gate | Old function reads `tsp_candan_route_audit_paper/test_profile_summary.csv`; current table uses theory-fixed zero threshold | Builder now filters `theory_fixed_tau_zero_no_calibration` from protocol metrics and verifies four profile rows |
| Historical Python figure builder is an unsuitable current entry | Calls old layouts and absent reliability/transfer ledgers; can overwrite current figure names | Remove it from recommended build sequence; use active MATLAB and Visio sources |
| Statement that all figures come from MATLAB is inaccurate | `generate_tsp_figures.m` calls five bundles; overview is maintained in `.vsdx` with a PowerShell exporter | Document both sources and export commands; correct supplementary prose later |
| Old dependency recipe differs from measured environment | `requirements_sensors.txt` pins NumPy 2.2.6; paper/release records identify 2.5.0; package metadata omits Sionna | Give scoped install recipe and recorded versions; full lock remains outstanding |
| Controlled-family metadata is not in uniform sidecars | Its `run_manifest.json` embeds command/config/seeds/environment/Git ID | Describe embedded metadata accurately; no implementation/results missing |
| Independent MATLAB provenance is incomplete | Rows and summary exist; no complete run manifest or environment sidecars | State limitation; reconstruct metadata only from retained evidence, not invented values |
| Historical closed-loop metadata is incomplete | `tsp_candan_zeta_closed_loop_paper` lacks several sidecars | Keep separate from primary evidence; not a missing proposed-method entry |
| Full test suite has an absent historical helper | `tests/test_candan_gate_protocol.py` imports `run_tsp_crossfit_predictive_gate.py`, absent on both remote branches | Document collection failure; do not advertise the full test suite as verified |
| Recorded Git IDs do not uniquely identify executed code | Several manifests cite `c50a603`, which predates T-SP scripts | Retain original records; use recorded hashes where available, and archive exact executed source if retained |
| MATLAB statistical/portability caveats | Experiment 6 uses normal 1.96 CI, `table`, and `writetable` | Document distinction from Python Student-t intervals; do not claim verified Octave compatibility |

The old exploratory directories below are absent on **both audited remote
branches**, although copies exist as untracked local files. They are not
required by the current eight-table builder or active MATLAB figures:

- `05_results/tsp_reliability_gate_round2_paper/`
- `05_results/tsp_gate_reliability_curve_paper/`
- `05_results/tsp_cross_geometry_threshold_transfer_paper/`
- `05_results/tsp_seed_cluster_bootstrap_paper/`
- `05_results/tsp_fifth_round_boundary_audit_paper/`
- `05_results/tsp_separable_local_benchmark_paper/`

Untracked local copies were not published as part of this repair. No new
experiments, scene counts, or evidence claims were introduced.

## Verification and limits

- After repair, all ten primary Python entries passed `--help` with local
  editable-package finders disabled;
  see [entry_help_checks.json](entry_help_checks.json). This establishes import
  and argument entry, not complete numerical replay.
- The initial interpreter checks borrowed the missing `data` package from an
  installed editable workspace. Isolated pre-repair checks exposed eight
  failures; see `isolated_before_generator_fix.json`. The corrected static
  dependency scan includes the generator package.
- 25 existing generator/recovery and local-refinement tests passed with editable
  package fallback disabled. The full suite remains unverified: the gate test
  module cannot collect because `run_tsp_crossfit_predictive_gate.py` is absent.
- All 17 LaTeX input occurrences and five figure occurrences resolved.
- Working and assembled submission TeX sources agree except `main.tex`'s
  expected bibliography/graphics path relocations; the supplement agrees.
- The revised table builder completed and regenerated the eight current
  tables byte for byte, leaving all distributed tables unchanged.
- Controlled-family records contain 7200 method rows for 1200 scenes plus
  480 calibration rows. Full-offset records include 1200 test and 480
  validation scenes. Frozen CDL route rows number 14400 including validation;
  physical replay records number 9000; independent MATLAB records number 1200.
- The protocol manifest's route-source SHA256 matches the committed CSV.
  Static results and digests are in [static_validation.json](static_validation.json).
- [audit_inventory.json](audit_inventory.json) preserves result-directory
  coverage, manifests, and missing metadata sidecars. Its findings describe
  the original branch snapshot, before the entry-point repairs.

MATLAB, Visio, fresh-environment package installation, LaTeX compilation,
and full numerical experiment replay were not executed. Submitted PDFs,
LaTeX text, figure outputs, aggregate tables, and registered experiment
results are retained unchanged. The installed audit Python stack was
Python 3.12.10, NumPy 2.5.0, SciPy 1.18.0, Matplotlib 3.11.0,
PyTorch 2.12.1+cu130, Sionna 2.0.1, and pytest 9.1.1.

## Minimum-work repair order

1. Fast-forward `main` to the latest submission content and publish a T-SP root
   README plus exact reproduction map. This aligns the paper's bare URL.
2. Restore the omitted generator package, fix relative paths and default
   table generation, and identify the active
   MATLAB/Visio figure sources. These entry-point repairs accompany promotion.
3. At the next manuscript revision, expand abbreviated paths and correct the
   all-MATLAB and interval-method descriptions. This does not require reruns.
4. If retained execution records permit it, add a complete dependency lock,
   MATLAB run provenance, and exact source snapshot. Do not claim these are
   verified until those records are checked.
