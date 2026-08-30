# MATLAB TAES supplement campaign

Independent second implementation (MATLAB R2021b+ / GNU Octave 6.4 compatible)
of the synthetic 3-D and 64x4 geometry pipelines. Scene randomness uses a
portable counter-based RNG (`common/pr_stream.m`), so every scene is bit-stable
across MATLAB and Octave and every number is reproducible from a scene seed.

| Script | Paper hook | Output CSV |
|---|---|---|
| `exp1_learning_marginal.m` | §VI-B learned-vs-deterministic re-anchor (T1.3) | `learning_marginal_rows.csv`, `learning_marginal_alpha.csv` |
| `exp2_flops_pareto.m` | §VI-C FLOP Pareto + complexity table (T1.1/T1.2) | `pareto_rows.csv`, `complexity_table.csv` |
| `exp3_fixedpoint_sweep.m` | §VI-F fixed-point feasibility (T3.1) + RTL vectors | `fixedpoint_sweep.csv`, `tb/vectors/tv_*.txt` |
| `exp4_crlb_check.m` | §V-C CRLB cross-check | `crlb_check.csv` |
| `exp5_cdl_geometry_2d.m` | §VI-D axis-coupling mechanism side-evidence | `geometry2d_rows.csv` |
| `exp6_candan_independent_audit.m` | Independent Candan replication | `candan_independent_rows.csv`, `candan_independent_summary.csv` |

Run everything: `run_all_experiments` (all scripts are resumable/idempotent).
Outputs land in `05_results/matlab_taes_supplement/`.

Experiment 6 is a separately written implementation of the complex
three-sample update under the common 3-D FFT, fixed-support, and joint-LS
contract.  Its default campaign contains 1200 scenes.
