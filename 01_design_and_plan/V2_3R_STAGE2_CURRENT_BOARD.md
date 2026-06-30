# v2.3R Stage 2 Current Board

Generated: 2026-06-24

## Current Mainline

Stage 1 G1 is accepted under the V2.3R gate definition. Stage 2 now has bounded minimal, trainable, PyTorch smoke, locked-scale curriculum-proxy, and locked-scale PyTorch trainable evidence. G2 is accepted for the bounded local Stage-2 gate.

## Trusted Reusable Assets

- `05_results/stage1_g1_manifest/acceptance_audit.md`: trusted G1 acceptance audit.
- `05_results/stage2_minimal_tompnet_smoke/`: trusted minimal Pack 3 smoke artifact with command, config, CSV, summary, and manifest.
- `05_results/stage2_trainable_tompnet_smoke/`: trusted NumPy parameterized train/test smoke artifact.
- `05_results/stage2_torch_tompnet_smoke/`: trusted PyTorch CPU trainable smoke artifact.
- `05_results/stage2_curriculum_tompnet_g2/`: trusted locked-scale curriculum proxy at 128x16x32, L={2,4,8}.
- `05_results/stage2_torch_locked_scale_g2/`: trusted locked-scale PyTorch `nn.Module` + Adam run at 128x16x32, L={2,4,8}.
- `05_results/stage2_torch_locked_scale_g2_seed_sweep/`: trusted multi-seed strengthening run over seeds `{20260624,...,20260628}`; mean L-cell gain is 6.1726 dB and minimum L-cell gain is 4.4735 dB.
- `05_results/stage2_g2_manifest/`: trusted current G2 gate aggregation surface.

## Latest Decisive Result

`stage2_torch_locked_scale_g2_20260624` keeps the Stage-2 locked tensor scale at 128x16x32 and trains a PyTorch `nn.Module` bounded off-grid refinement layer with Adam across L={2,4,8}. It shows a 6.3646 dB average held-out measurement-NMSE gain over grid Tensor-OMP at 20 dB, with minimum L-cell gain 5.1624 dB. Training NMSE improves by 1.0863 dB and the optimized normal-equation PyTorch path runs locally in 8.03 s.

## Latest Added Stability Result

`stage2_torch_locked_scale_g2_seed_sweep_20260625` repeats the locked-scale PyTorch path across five seeds with three held-out samples per L cell. Mean L-cell gain over grid Tensor-OMP is 6.1726 dB, standard deviation is 0.9071 dB, minimum L-cell gain is 4.4735 dB, and minimum per-seed mean gain is 5.7428 dB. This strengthens G2 from single-seed smoke evidence toward paper-usable local statistical evidence.

## Active Blocker

G2 is accepted for the bounded local Stage-2 gate. After the seed sweep, the remaining boundary is still statistical and scope-related rather than infrastructural: evidence is local synthetic/off-grid at CPU-feasible sample counts, not external channel validation.

## Next Decision Scope

Run a short G2 acceptance audit that records the small-sample boundary, then Stage 3 A4/A5 pre-smoke can start without waiting on the old PyTorch scale blocker.
