# v2.3R Stage 3 Current Board

Generated: 2026-06-25

## Current Mainline

Stage 2 G2 is accepted for the bounded local gate. Stage 3 has A4 IA-AUD and A5 HIR-JL pre-smoke evidence. A4 is viable only as a narrowed high-L/platform-sample early-stop mechanism, not as a global adaptive-depth claim. A5 should be removed from the main Stage-3 gate and kept, at most, as a high-stress robustness appendix.

## Trusted Reusable Assets

- `05_results/stage2_g2_manifest/acceptance_audit.md`: G2 bounded local acceptance audit.
- `05_results/stage2_torch_locked_scale_g2/`: locked-scale PyTorch G2 run at 128x16x32, L={2,4,8}.
- `05_results/stage3_a4_depth_presmoke/`: A4 depth-vs-L pre-smoke at 128x16x32, L={2,8,32}.
- `05_results/stage3_a4_oracle_earlystop/`: A4 oracle early-stop upper-bound run for fixed K=8 vs adaptive K.
- `05_results/stage3_a4_high_l_plateau_gate/`: A4 restricted high-L plateau gate run for L=32.
- `05_results/stage3_a4_high_l_plateau_gate_seed_sweep/`: A4 restricted high-L plateau gate multi-seed strengthening run; mean seed depth savings is 26.0417% with maximum mean NMSE gap 0.3578 dB.
- `05_results/stage3_a4_cross_l_plateau_gate_seed_sweep/`: A4 restricted high-L plateau gate cross-L strengthening run over L={16,32,64}; high-L L>=32 minimum mean depth savings is 25.0000% with maximum mean NMSE gap 0.4008 dB.
- `05_results/stage3_a4_snr_plateau_gate_seed_sweep/`: A4 restricted high-L plateau gate SNR sensitivity run at L=32, SNR={10,20,30}; minimum SNR-cell mean savings is 21.8750% and maximum mean NMSE gap is 0.6834 dB, so SNR robustness is inconclusive.
- `05_results/stage3_a5_hirjl_presmoke/`: A5 phase-noise pre-smoke at 128x16x32, L=8, sigma_phi={0,0.5,1,2,3} degrees.
- `05_results/stage3_a5_combined_impairment_presmoke/`: A5 combined phase-noise/IQ/mutual-coupling pre-smoke.
- `05_results/stage3_presmoke_manifest/`: current Stage-3 pre-smoke aggregation surface.
- `05_results/stage3_paper_scale_kruskal_proxy/`: paper-scale on-grid Kruskal identifiability proxy derived from `paper_scale_tensor_omp_g1`.
- `05_results/stage3_synthetic_cross_scene_generalization/`: local synthetic cross-scene fallback; source-trained alpha keeps target gain versus grid while staying close to target-oracle under controlled synthetic shifts.
- `05_results/stage3_crlb_asymptotic_tightness/`: Stage-3 audit of analytic 5L FIM validation plus single-target Monte Carlo CRLB asymptotic trend.
- `05_results/stage3_g3_manifest/`: current Stage-3/G3 aggregation surface.
- `05_results/stage3_g3_manifest/acceptance_audit.md`: Stage-3 local evidence package acceptance audit.

## Latest Decisive Result

`stage3_crlb_asymptotic_tightness_20260624` converts the existing analytic 5L FIM validation and single-target Monte Carlo pilot into a Stage-3 CRLB trend audit. Max analytic-vs-numeric FIM relative error is 5.7304e-10, 30 dB mean RMSE/CRLB ratio is 1.0067, and mean absolute RMSE slope error versus the expected -0.05 per dB scaling is 0.0067. This supports a single-target high-SNR CRLB trend row, not full multi-target efficiency proof.

## Latest Added A4 Result

`stage3_a4_high_l_plateau_gate_seed_sweep_20260625` repeats the deployable high-L plateau gate across seeds `{20260624,20260625,20260626}` for L=32 at 128x16x32. Mean seed depth/FLOPs savings is 26.0417%, standard deviation is 3.6084%, and maximum seed NMSE gap versus fixed K=8 is 0.3578 dB. This supports A4 only as a narrowed high-L/platform-sample early-stop mechanism, not a global adaptive-depth claim.

`stage3_a4_cross_l_plateau_gate_seed_sweep_20260625` extends the same plateau gate across L={16,32,64}. For L>=32, minimum mean depth/FLOPs savings is 25.0000% and maximum mean NMSE gap is 0.4008 dB. L=16 has mean savings 28.1250% but max gap 0.5480 dB, so it is boundary evidence rather than main support.

`stage3_a4_snr_plateau_gate_seed_sweep_20260625` tests the same restricted gate at L=32 across SNR={10,20,30} dB. It is a useful negative/boundary result: minimum SNR-cell mean depth/FLOPs savings is 21.8750%, maximum mean NMSE gap is 0.6834 dB, and the run status is SNR-robustness inconclusive. This prevents any broad SNR-robust early-stop claim under the current scalar gate.

## Mechanism Boundary

- A4: The depth pre-smoke supports adaptive-depth opportunity, but the oracle upper-bound run does not prove the global >=25% FLOPs/depth-reduction target. The high-L plateau gate passes on L=32 at SNR=20 dB, survives a small L=32 multi-seed strengthening run, and has cross-L support for L>=32 at SNR=20 dB. L=16 is boundary-only because its max NMSE gap exceeds the 0.5 dB tolerance. The new SNR sweep is also boundary-only: it fails a broad SNR-robust claim because 30 dB falls below 25% mean savings and 10/20 dB exceed the 0.5 dB max-gap tolerance in the small sample. The viable story remains restricted sample-dependent early stopping for high-L/platform samples at the core SNR setting.
- A5: The phase-noise pre-smoke contradicts the planned "sigma_phi=1 degree degrades by >8 dB" value trigger. Combined nominal stress still falls below the 5 dB main-gate threshold, while high stress exposes a failure mode. The honest framing is appendix/high-stress robustness, not a main contribution gate.
- Synthetic cross-scene fallback: Source-trained alpha transfers across controlled synthetic shifts with retained gain, but this is not ray-traced, not standards-aligned CDL, and not DeepMIMO Set E evidence.
- 5L CRLB: Analytic derivatives match finite differences and the single-target high-SNR Monte Carlo trend is close to CRLB. The current evidence is not a multi-target or large-sample asymptotic-efficiency proof.
- Kruskal/DeepMIMO: Paper-scale Kruskal is locally supported as an on-grid proxy. DeepMIMO Set E remains external-data blocked: code is present, but scenario files are absent and the 5G Toolbox license check failed in the existing audit.

## Next Decision Scope

Use the local Stage-3 evidence package for narrowed manuscript claims: restricted high-L A4 for L>=32 at SNR=20 dB, A4 SNR sensitivity as appendix/boundary evidence, A5 appendix/high-stress robustness, on-grid paper-scale Kruskal sanity, local synthetic cross-scene portability, and single-target 5L CRLB trend consistency. Full original G3 remains incomplete until DeepMIMO Set E data/toolbox readiness changes and a real channel NMSE plus angle/delay RMSE run is recorded.

## 2026-06-27 E1 Physical-Transfer Update

- The Sionna physical evaluator is now connected to the accepted Stage-2 learned bounded-refinement alpha under a paired A/C/D dev contract.
- Shared-alpha transfer is mixed: mean channel NMSE improves 3.5443 dB and delay RMSE improves 5.2652 ns, but projected-angle RMSE worsens 5.6007 deg; CDL-D is negative overall.
- A single controlled delay-only diagnostic preserves most NMSE/delay benefit and contracts angle degradation to approximately zero, localizing shared-axis coupling. This override is diagnostic only.
- Current blocker: the accepted scalar layer is structurally insufficient for defensible joint physical delay/angle transfer.
- Static-axis follow-up: both the original 128x16x32 source geometry and a geometry-matched 64x4 synthetic source learned effectively identical delay/angle scales (~0.64), so static axis splitting does not solve the coupling failure and will not be scaled.
- Next experiment: train a feature-conditioned per-sample delay/angle refinement controller on geometry-matched synthetic data only, using channel NMSE plus Hungarian parameter supervision; freeze it before one unchanged Sionna CDL physical evaluation.

## 2026-06-27 Scaled CDL Landing Result

- The final controller uses estimator-internal features, dynamic Hungarian supervision, physical broadside-angle loss, and a Nyquist alias lock. Model selection uses disjoint CDL-A/C validation seeds; evaluation seeds are separate.
- Scaled held-out CDL-A/C (5 seeds x 50 samples/profile/seed) is supported: channel NMSE gain 6.2286 dB [95% CI 6.1018, 6.3553], delay RMSE reduction 10.1241 ns [8.6931, 11.5551], and projected-angle RMSE reduction 0.5277 deg [0.3122, 0.7432].
- Scope boundary: L=16 delay reduction averages -0.8112 ns, and aggregate support does not imply every profile/SNR/L cell wins.
- Scaled unseen CDL-D is a stable failure boundary: NMSE gain -1.4862 dB and delay reduction -14.5820 ns, while projected-angle reduction remains positive at 0.9651 deg.
- Paper route: promote A/C to the main external-validation block; retain D and the earlier shared-alpha result as failure/mechanism evidence. The CDL manuscript block and E4 executable comparator coverage are complete; the next deterministic landing work is the missing figure set, graphical abstract, and verified frontier references.

## 2026-06-28 E4 Complexity Comparator Update

- The benchmark now executes 15 rows at tensor shape 128x16x32 over L={4,8,16}: grid FFT top-k, bounded local refinement, the Torch alpha forward path, separable forward-backward ESPRIT, and five-sweep complex PARAFAC-ALS.
- Missing comparator rows are reduced from two to zero. The maximum median CPU wall-clock is 1678.3922 ms for bounded local refinement at L=16.
- Evidence boundary: arithmetic counts are analytical operation proxies rather than profiler FLOPs; the ESPRIT implementation is separable and does not provide cross-axis pairing or claim full Unitary ESPRIT; this timing run does not establish matched estimator accuracy.

## 2026-06-28 Figure and Literature Landing Update

- Added and visually inspected vector system-model, T-OMP-Net architecture, and five-seed CDL profile figures plus a separate graphical abstract.
- Expanded the cited bibliography from 26 to 42 entries after official arXiv/IEEE/3GPP source checks. Related Work now contains an explicit nearest-neighbor table for NOMP-OFDM-ISAC, unified tensor ISAC, PLAIN, DDA-Net, and T-OMP-Net.
- The IEEEtran draft compiles to exactly eight pages with 42 resolved citations, no overfull boxes, and four paper-facing figures. Redundant A4 diagnostic tables remain as supplementary display artifacts rather than consuming main-paper pages.
- Remaining evidence priorities are trained DeepMIMO physical evaluation if retained in scope and matched comparator accuracy only if the paper keeps an NMSE--complexity Pareto claim.
