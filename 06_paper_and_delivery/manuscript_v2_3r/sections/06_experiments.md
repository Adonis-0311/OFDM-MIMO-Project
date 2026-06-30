# 6. Experiments and Analysis

The experiments answer three questions. First, does bounded off-grid refinement improve the grid Tensor-OMP baseline under the locked local protocol? Second, does a frozen trained controller improve channel and physical-parameter estimates under standards-aligned CDL channels? Third, can repeated refinement be shortened without turning the result into an unrestricted adaptive-depth claim? Figure 1 and Table 1 carry the local comparisons, while the CDL result adds an external-validation block with an explicit unseen-profile boundary.

## 6.1 Evaluation Protocol

The local experiments use tensor shape `128x16x32`. G2 evaluates L={2,4,8} at SNR=20 dB against grid Tensor-OMP on matched held-out samples. The external experiment uses Sionna CDL frequency responses with 64 subcarriers and a four-element ULA over SNR={0,10,20,30} dB and L={4,8,16}. The controller is trained on CDL-A/C with separate validation seeds; its checkpoint is frozen before evaluation on five new seeds with 50 samples per profile and seed. Delay truth comes from the CIR, while angle is the identifiable projected broadside quantity of the one-dimensional ULA. CDL-D is excluded from training and validation and used only as a zero-shot profile-shift test.

The primary reconstruction metric is measurement-domain NMSE in dB. For A4, depth is used as the FLOPs proxy because each refinement layer performs the same local-search kernel. A cell is treated as positive only when the mean depth saving reaches the planned 25% level and the NMSE gap to fixed K=8 remains within the 0.5 dB tolerance.

## 6.2 Main Result: Bounded Off-Grid Refinement

Figure 1a shows that bounded refinement consistently improves over grid Tensor-OMP across the evaluated target counts. Across five seeds and L={2,4,8}, the mean L-cell gain is 6.1726 dB, and the smallest L-cell gain is 4.4735 dB. Table 1 decomposes this result by target count: L=2, L=4, and L=8 all remain above the 3 dB gate.

This result supports the central local mechanism claim: the gain is not merely from adding a neural block, but from allowing local physical refinement around selected tensor atoms. Standards-aligned external evidence is reported separately below.

## 6.3 Standards-Aligned CDL Evaluation

On held-out CDL-A/C seeds, the frozen controller improves all three aggregate metrics over grid Tensor-OMP. Across five seeds and 50 samples per profile and seed, the channel-NMSE gain is 6.2286 dB (95% seed-level CI [6.1018, 6.3553]), the physical-delay RMSE reduction is 10.1241 ns ([8.6931, 11.5551]), and the projected broadside-angle RMSE reduction is 0.5277 degrees ([0.3122, 0.7432]). Profile A contributes the larger NMSE gain (8.1690 dB), whereas profile C contributes the larger delay reduction (15.8061 ns).

The positive statement is aggregate and profile-scoped. At L=16, the mean delay reduction is -0.8112 ns even though channel and angle metrics remain positive on average, and a few individual profile/SNR/L cells have negative angle deltas. The result therefore supports held-out CDL-A/C performance, not uniform dominance in every cell.

The unseen CDL-D test exposes the generalization boundary. Its channel-NMSE gain is -1.4862 dB and its delay reduction is -14.5820 ns, although projected-angle RMSE improves by 0.9651 degrees. The consistent channel and delay degradation prevents a profile-universal CDL claim and motivates treating D as an explicit failure case rather than averaging it into the supported A/C result.

## 6.4 Efficiency Trade-Off: High-L Early Stopping

Figure 1b evaluates the plateau gate over L={16,32,64} at SNR=20 dB. The high-load cells, L=32 and L=64, satisfy the narrowed early-stop criterion: the minimum mean saving over L>=32 is 25.0000%, and the maximum mean NMSE gap is 0.4008 dB. L=16 is useful boundary evidence because its maximum gap reaches 0.5480 dB, slightly exceeding the tolerance even though its average saving is positive.

The interpretation is therefore deliberately narrow. The result supports a high-load/platform-sample early-stop mechanism at the core SNR setting. It does not support unrestricted IA-AUD, a closed-form optimal-depth theory, or an every-load efficiency guarantee.

## 6.5 Sensitivity Boundary: SNR Sweep

Figure 1c and Table 2 show the boundary of the early-stop result. At L=32 over SNR={10,20,30} dB, the scalar plateau gate is inconclusive as a mechanism across SNR. The minimum SNR-cell mean saving drops to 21.8750%, below the 25% target, while the maximum SNR-cell gap reaches 0.6834 dB, above the 0.5 dB tolerance.

A follow-up threshold-frontier diagnostic tests whether this failure is only a coarse-calibration artifact. It compares the train-selected scalar rule with a guarded train rule and a test-oracle threshold frontier. The result remains negative for a broad scalar-threshold claim: the standard train-selected policy has a minimum SNR mean saving of 15.6250% and a maximum SNR mean gap of 0.6691 dB, while even the diagnostic test-oracle frontier has a minimum SNR mean saving of 0.0000%. This separates a useful 20 dB high-load trade-off from a general SNR-axis depth policy. A stronger learned gate with explicit SNR or uncertainty features would be needed before A4 could be presented as stable across SNR.

## 6.6 Supporting Analyses and Negative Evidence

The supporting package checks several likely reviewer concerns without overstating them. The on-grid Kruskal sanity check gives bound 87, max L/Lmax 0.7356, and minimum support recall 1.0000; this is a structural sanity row, not an off-grid or external-channel proof. The synthetic cross-scene fallback retains a minimum target gain of 5.8504 dB and a maximum target-oracle gap of 0.4077 dB under controlled shifts; this is local portability evidence, not DeepMIMO validation. The CRLB audit validates the analytic FIM against finite differences and gives a 30 dB mean RMSE/CRLB ratio of 1.0067, but only for a single-target high-SNR trend.

Two additional negative results shape the final claim boundary. A5/HIR-JL is downgraded because nominal combined impairment degradation is 4.4395 dB, below the planned main robustness gate; the high-stress degradation of 6.6036 dB is better treated as failure-mode evidence. DeepMIMO O1/I3 access and scalar-transfer proxies are available, but they do not provide the trained physical angle/delay contract established for CDL and are therefore kept out of the main result.
