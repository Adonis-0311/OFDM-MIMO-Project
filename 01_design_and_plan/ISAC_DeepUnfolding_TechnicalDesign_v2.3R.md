# 毫米波 MIMO-OFDM ISAC 信道与目标参数联合估计

## 基于物理约束 Tensor-OMP 深度展开网络的 v2.3R 证据约束版技术设计

> 版本：v2.3R
> 生成日期：2026-06-25
> 状态：论文主线候选文档；以 `05_results/v2_3r_paper_evidence_table/paper_evidence_table.md` 为当前证据边界。
> 首投定位：IEEE Sensors Journal；备选 IEEE Systems Journal / IEEE TVT / Signal Processing。

---

## 0. v2.3R 总原则

v2.3R 不是在 v2.2 上继续加功能，而是把 v2.3 的扩张计划压回可验证、可投稿、可防守的论文线。当前文档遵循三条规则：

1. **主张受证据约束**：所有纸面 claim 必须能指向结果目录、manifest、审计文件或明确的外部阻塞。
2. **数学错误显式修正**：删除 v2.3 中错误的 Lemma 2 闭式最优深度推导，改为 depth-identifiability trade-off 与计算代价驱动的操作目标。
3. **贡献压回四项**：C1-C4 保留；A6/MAML 删除为 future work；MOMPnet/DDA-Net 精确复现不再作为主图依赖。

当前 paper-facing 证据入口：

```text
05_results/v2_3r_paper_evidence_table/paper_evidence_table.md
01_design_and_plan/V2_3R_PROGRESS_AUDIT_2026_06_25.md
01_design_and_plan/V2_3R_STAGE1_CURRENT_BOARD.md
01_design_and_plan/V2_3R_STAGE2_CURRENT_BOARD.md
01_design_and_plan/V2_3R_STAGE3_CURRENT_BOARD.md
```

---

## 1. 论文定位与贡献

### 1.1 拟题

**Sparse Tensor-OMP Deep Unfolding with Bounded Off-Grid Refinement for Joint Channel and Target Parameter Estimation in mmWave MIMO-OFDM ISAC**

中文：基于物理约束 Tensor-OMP 深度展开的毫米波 MIMO-OFDM ISAC 信道与目标参数联合估计。

### 1.2 四个核心贡献

**C1：三维稀疏张量统一建模。**  
构建毫米波 MIMO-OFDM ISAC 中角度、时延、多普勒三维稀疏核张量模型，将通信信道估计与雷达目标参数估计统一为同一张量稀疏恢复问题。

**C2：T-OMP-Net 与物理 bounded off-grid refinement。**  
提出与 Tensor-OMP 迭代对应的模型驱动展开网络，并在每层中引入物理有界的 off-grid refinement。当前本地证据显示，在 `128x16x32` 锁定张量尺度、SNR=20 dB、L={2,4,8} 条件下，T-OMP-Net 相对 grid Tensor-OMP 的平均 L-cell NMSE 增益为 `6.1726 dB`，最小 L-cell 增益为 `4.4735 dB`。

证据：

```text
05_results/stage2_torch_locked_scale_g2_seed_sweep/
```

**C3：高负载样本的可辨识性感知早停 + permutation-invariant 联合损失。**  
Hungarian permutation-invariant 损失使多目标参数估计不依赖目标排列；在此基础上，v2.3R 仅保留**高 L/platform 样本早停**这一收窄后的 IA-AUD 叙述。跨 L 证据显示，在 SNR=20 dB 且 L>=32 时，plateau gate 的最小平均深度/FLOPs 节省为 `25.0000%`，最大 NMSE gap 为 `0.4008 dB`。L=16 为边界样本，不进入正向主 claim。新增 SNR={10,20,30} 敏感性 sweep 显示，最小 SNR-cell 平均节省降至 `21.8750%`，最大 gap 达 `0.6834 dB`，因此不能写成 broad SNR-robust early-stop claim。

证据：

```text
05_results/stage3_a4_cross_l_plateau_gate_seed_sweep/
05_results/stage3_a4_snr_plateau_gate_seed_sweep/
```

**C4：鲁棒性、可辨识性与泛化边界的防守证据。**  
当前 C4 不是一个单一强 claim，而是一组边界清楚的支撑证据：

- Paper-scale on-grid Kruskal proxy：bound = `87`，max L/Lmax = `0.7356`，min support recall = `1.0000`。
- Synthetic cross-scene portability：min target gain vs grid = `5.8504 dB`，max gap vs target oracle = `0.4077 dB`。
- Sionna CDL-A/C/D：5 seed × 50 samples/profile/seed 的 `128 × 16` 诊断中，min exact support recall = `0.4188`，min oracle top-k energy efficiency = `0.9886`；CIR-grounded grid baseline 的 delay/projected-angle RMSE 为 `180.23 ns / 28.63 deg`，clean-grid floor 为 `141.32 ns / 28.45 deg`。归类为 energy-supported/exact-bin-weak，训练估计器比较仍未完成。
- 5L CRLB trend：max FIM relative error = `5.73e-10`，30 dB mean RMSE/CRLB = `1.0067`。
- A5/HIR-JL：降级为 appendix/high-stress robustness；nominal combined degradation = `4.4395 dB`，未过主门控；high-stress degradation = `6.6036 dB` 可作为 failure-mode/robustness boundary。
- DeepMIMO Set E proxy：开源数据接入已就绪（`4188` files）；5 seed × 100 用户的标量 source-alpha 代理评估中，O1_60 为 `weak`（增益 `1.3235 dB`，95% CI `[1.2538, 1.3931]`），I3_60 为 `partial`（增益 `6.7014 dB`，但最差 cell `-0.2412 dB`）。当前不能声称完整训练模型或最终 Set E 性能。

证据：

```text
05_results/stage3_paper_scale_kruskal_proxy/
05_results/stage3_synthetic_cross_scene_generalization/
05_results/sionna_cdl_profile_generalization_scaled/
05_results/sionna_cdl_physical_metrics_grid_baseline/
05_results/stage3_crlb_asymptotic_tightness/
05_results/stage3_a5_combined_impairment_presmoke/
05_results/deepmimo_set_e_access_audit/
05_results/deepmimo_source_alpha_seed_campaign/
```

---

## 2. 研究空白与相关工作边界

本文不声称 Tensor-OMP、deep unfolding、ISAC 张量建模或 off-grid refinement 中任一单项为绝对首次。v2.3R 的 novelty boundary 是：

1. 在 MIMO-OFDM ISAC 的角度-时延-多普勒三维张量恢复问题中，将 Tensor-OMP 展开网络、物理 bounded off-grid refinement、permutation-invariant 联合损失组织成同一可解释估计器。
2. 在高目标数/高负载条件下，把自适应深度叙述收窄为可操作的 early-stop 机制，而非全局最优深度理论。
3. 用 Kruskal proxy、CRLB trend、synthetic cross-scene、scaled Sionna CDL diagnostic 和 scaled DeepMIMO scalar-alpha proxy 显式界定模型能力与证据边界。

### 2.1 论文中必须避免的过度表述

- 不写“全局 IA-AUD 最优深度”。
- 不写“任意 L 均满足 >=25% FLOPs 节省”。
- 不写“H​​IR-JL 是主贡献并已通过 nominal robustness gate”。
- 不写“完整 DeepMIMO 外部验证已完成”；仅允许报告 weak/partial 标量-alpha 代理结论及其限制。
- 不把 synthetic cross-scene portability 等同于 ray-traced 或 standards-aligned CDL 验证。
- 不把 single-target CRLB trend 写成 full multi-target asymptotic efficiency。

### 2.2 Related Work 当前缺口

v2.3R 仍需要在正式论文阶段补齐 2024-2026 的具名引用和 BibTeX。Related Work 表格应保留如下对比维度：

| 方法族 | 3D tensor | Deep unfolding | Bounded off-grid | ISAC joint loss | Hungarian/permutation |
|---|---:|---:|---:|---:|---:|
| Classical CS / OMP / SOMP | partial | no | usually no | partial | no |
| Tensor ISAC estimation | yes | no | partial | partial | no |
| Deep unfolding JCAS | partial | yes | usually no | partial | no |
| End-to-end DL channel/positioning | no/partial | no | no | partial | no |
| v2.3R T-OMP-Net | yes | yes | yes | yes | yes |

这张表是定位表，不是性能表。性能表必须来自当前证据或后续可复现实验。

---

## 3. System Model and Problem Formulation

系统采用单站 mmWave MIMO-OFDM ISAC 结构。发射端 ULA，接收端 ULA，经正交发射形成虚拟阵列；接收信号在角度、时延、多普勒三维上呈稀疏结构。v2.3R 沿用 v2.2 的主模型：

```text
measurement tensor -> grid Tensor-OMP coarse support -> bounded off-grid refinement -> channel/target parameter estimates
```

### 3.1 正交波形与 FDMA 边界

FDMA 仍作为主算法推导路径，因为其虚拟阵列模型清楚、实现与复现实验稳定。论文中必须保留 FDMA 的频谱效率 trade-off：

- FDMA 牺牲 Tx 间频谱复用，换取零失真的虚拟阵列分离。
- DDM/TDM 可作为扩展讨论，但不作为 v2.3R 主实验证据。
- 如果未来转 IEEE Systems Journal，可补系统级 DDM/TDM 对照或讨论图。

### 3.2 参数范围

当前 paper-facing 实验主尺度为：

```text
tensor shape: 128 x 16 x 32
SNR: 20 dB for G2/A4 core positive evidence
L values:
  G2: {2,4,8}
  A4 cross-L: {16,32,64}, positive high-L claim only for L>=32 at 20 dB
  A4 SNR sensitivity: {10,20,30}, boundary evidence only under current scalar gate
```

这意味着主文可写为“paper-scale local synthetic/off-grid evaluation”，但不能写成真实外部信道验证。

---

## 4. Proposed Method

### 4.1 Tensor-OMP baseline

Tensor-OMP 作为可解释基线：在三维字典上选择相关性最大的支撑原子，随后求解 least-squares 系数并更新残差。v2.3R 继续把 grid Tensor-OMP 作为比较基线，而不是引入未验证的外部深度模型复现。

### 4.2 T-OMP-Net

T-OMP-Net 将 Tensor-OMP 的迭代过程展开为有限层网络。每层保留 coarse support selection 和 LS reconstruction 结构，同时引入少量可学习参数控制 off-grid refinement。

当前实现证据使用 PyTorch `nn.Module` + Adam，在锁定尺度 `128x16x32` 下完成多 seed 训练/测试。G2 的可写结论是：

> In local synthetic off-grid evaluation, the trainable bounded refinement layer consistently improves measurement-domain NMSE over grid Tensor-OMP at the locked tensor scale.

不能写成：

> The method has been validated on external ray-traced or real channels.

### 4.3 Bounded off-grid refinement

bounded off-grid refinement 使用物理有界偏移，避免自由学习导致参数失去角度、时延、多普勒含义。论文中应强调其两个作用：

1. 减少 grid quantization error。
2. 保留可解释参数空间，使估计结果仍可映射到目标角度、距离、速度。

### 4.4 Hungarian permutation-invariant ISAC loss

多目标估计存在排列不确定性。v2.3R 保留 Hungarian matching，使目标参数损失对排列不敏感。该损失也为 early-stop gate 提供稳定的 per-sample 反馈信号：若损失/重建收益趋于 plateau，则高 L 样本可提前停止。

### 4.5 A4：高 L/platform early-stop gate

v2.3R 不再把 A4 写成“全局自适应深度模块”。当前可写机制是：

- 固定深度为 K=8。
- plateau gate 观察逐层 NMSE 改善。
- 若改善低于训练得到的阈值且已达到最小深度，则停止。
- depth 作为 FLOPs proxy，因为每层使用相同 local-search kernel。

当前证据：

| L | Mean savings | Min savings | Mean gap | Max gap | 论文用途 |
|---:|---:|---:|---:|---:|---|
| 16 | 28.1250% | 18.7500% | 0.4220 dB | 0.5480 dB | boundary/diagnostic |
| 32 | 28.1250% | 25.0000% | 0.3769 dB | 0.4008 dB | high-L support |
| 64 | 25.0000% | 25.0000% | 0.2922 dB | 0.3297 dB | high-L support |

因此正文推荐措辞：

> At SNR=20 dB, for high-load cases with L>=32, the plateau gate reduces average unfolding depth by at least 25% while keeping the mean NMSE gap below 0.5 dB relative to fixed K=8.

新增 SNR sensitivity 结果要求进一步收窄：

> The current scalar plateau gate is not yet SNR-robust across SNR={10,20,30} dB.

不推荐措辞：

> IA-AUD reduces FLOPs by at least 25% for all target counts.
> The early-stop gate is robust across SNR without additional calibration.

### 4.6 A5：HIR-JL 降级

A5/HIR-JL 在 v2.3R 中只保留为 appendix/high-stress robustness boundary。现有 evidence 说明：

- phase-noise-only stress 没有提供足够主线价值。
- nominal v2.3R combined impairment degradation 为 `4.4395 dB`，低于 5 dB 主门控。
- high-stress degradation 为 `6.6036 dB`，可作为 failure-mode 与 future robust training 的动机。

因此不应把 A5 写进主贡献，除非后续新增真正的 robust-training 改善结果。

---

## 5. Theoretical Analysis

### 5.1 Lemma 1：Off-grid mismatch under support condition

v2.3R 修订 Lemma 1 的适用条件。该 lemma 只在支撑正确或近似正确事件下成立：

```text
E_supp = { S_hat contains S* or d_H(S_hat, S*) <= 1 }
```

在该事件下，bounded off-grid refinement 将 grid mismatch 主导项从 `O(N_v^2 Delta_grid^2)` 压到由学习残差/噪声主导的项。论文中必须把条件写在 lemma 陈述里，避免暗示支撑完全错误时也有同样保证。

### 5.2 Lemma 2：Depth-identifiability trade-off

v2.3R 删除旧的闭式 `K*(L)`。修订陈述如下：

设 K 为展开层数，L 为目标数，`L_max` 为 Kruskal 上限。存在常数 `C1,C2,C3>=0` 与收敛率 `beta>0`，使得：

```text
E[NMSE_K | E_supp] <= C1 exp(-beta K) + C2 Psi(L,L_max) + C3 sigma^2
Psi(L,L_max) = L^2 / (L_max - L + epsilon)^2
```

解释：

1. 增加 K 可降低第一项。
2. 当 L 接近 `L_max` 时，可辨识性风险上升，固定深度无法消除该项。
3. 噪声底由 `C3 sigma^2` 控制。

真正可优化的是带计算代价的操作目标：

```text
J(K) = E[NMSE_K] + lambda_FLOPs K
```

该目标支持 early stopping，但不支持“仅由 L 推出全局闭式最优深度”的强 claim。

### 5.3 5L CRLB

当前 CRLB 证据为 single-target high-SNR trend consistency：

```text
max analytic-vs-numeric FIM relative error = 5.73e-10
30 dB mean RMSE/CRLB ratio = 1.0067
mean slope error = 0.0067
```

论文中可写：

> The analytic FIM implementation is numerically consistent with finite differences, and the single-target estimator follows the expected high-SNR CRLB trend.

不能写：

> The proposed multi-target estimator is asymptotically efficient in all regimes.

---

## 6. Experiment Program and Current Evidence

### 6.1 Evidence table

当前 manuscript-facing 表：

```text
05_results/v2_3r_paper_evidence_table/paper_evidence_table.md
```

核心行：

| Component | Status | Primary metric | Paper use |
|---|---|---|---|
| G2 T-OMP-Net bounded off-grid | supported-local | mean gain 6.1726 dB; min gain 4.4735 dB | main result |
| A4 high-L early stopping | supported-for-L>=32-at-20db | min mean savings 25.0000%; max gap 0.4008 dB | narrowed main/secondary |
| A4 SNR sensitivity | snr-robustness-inconclusive | min SNR-cell mean savings 21.8750%; max gap 0.6834 dB | appendix/boundary |
| Kruskal on-grid sanity | supported-on-grid-proxy | bound 87; max L/Lmax 0.7356 | sanity row |
| Synthetic cross-scene | local-synthetic-pass | min gain 5.8504 dB | fallback generalization |
| 5L CRLB trend | supported-pilot | 30 dB ratio 1.0067 | theory validation |
| A5 impairment stress | main-gate-downgrade | nominal 4.4395 dB; high-stress 6.6036 dB | appendix |
| DeepMIMO Set E proxy | access-ready; O1 weak; I3 partial | 5 seed × 100 users; O1 gain 1.3235 dB [1.2538, 1.3931]; I3 gain 6.7014 dB [6.4660, 6.9368], min cell -0.2412 dB | supporting/boundary; scalar-alpha proxy only |

### 6.2 Main result table plan

正文建议至少放两张表：

**Table 1：G2 local method comparison**

| Method | Scale | L | Metric | Result |
|---|---|---|---|---|
| Grid Tensor-OMP | 128x16x32 | 2/4/8 | baseline | same held-out samples |
| T-OMP-Net bounded refinement | 128x16x32 | 2/4/8 | mean NMSE gain | 6.1726 dB |
| T-OMP-Net bounded refinement | 128x16x32 | 2/4/8 | min L-cell gain | 4.4735 dB |

**Table 2：A4 high-L early-stop**

| L | Mean depth savings | Max NMSE gap | Verdict |
|---:|---:|---:|---|
| 16 | 28.1250% | 0.5480 dB | boundary |
| 32 | 28.1250% | 0.4008 dB | pass |
| 64 | 25.0000% | 0.3297 dB | pass |

Companion appendix row: SNR={10,20,30} sensitivity at L=32; highlight SNR-robustness inconclusive.

### 6.3 Appendix/support table plan

Appendix should include:

- A5 high-stress robustness boundary.
- DeepMIMO access audit, five-seed proxy campaign, and exact weak/partial boundary.
- Synthetic cross-scene settings and why it is not DeepMIMO.
- CRLB finite-difference validation details.
- Kruskal proxy derivation and on-grid limitation.
- Reproducibility table listing scripts and result directories.

### 6.4 Current G3 verdict

Original full G3 is **not** complete, because the DeepMIMO campaign still lacks the full trained estimator and physical angle/delay metrics, while A5 failed to clear the main nominal robustness gate. A narrowed Stage-3 package is usable if and only if the manuscript states:

```text
G3-local = restricted A4 for L>=32
         + A5 appendix/high-stress boundary
         + on-grid Kruskal proxy
         + local synthetic cross-scene fallback
         + single-target CRLB trend
         + scaled DeepMIMO proxy (O1 weak / I3 partial)
         + explicit full-model/physical-metric blocker
```

---

## 7. Manuscript Structure

### 7.1 Main text

1. **Introduction**  
   Motivate mmWave ISAC joint estimation; state the four-element fusion gap; immediately clarify that evidence is local synthetic/off-grid with external validation still blocked.

2. **Related Work**  
   Compare tensor ISAC, deep unfolding JCAS, off-grid sparse recovery, and model-driven ISAC learning. Use the “all features together” positioning, not “first ever” wording.

3. **System Model**  
   Present MIMO-OFDM tensor model, FDMA virtual array, sparse kernel, and parameter extraction.

4. **Method**  
   Describe Tensor-OMP, T-OMP-Net, bounded off-grid refinement, Hungarian loss, and high-L plateau early stopping.

5. **Theory**  
   Lemma 1 with support condition; Lemma 2 trade-off; 5L CRLB.

6. **Experiments**  
   G2 main local result, A4 high-L result, Kruskal/CRLB support, synthetic portability fallback, scaled Sionna CDL diagnostics, and scaled DeepMIMO scalar-alpha proxy evidence. A5, CDL exact-bin weakness, and the DeepMIMO weak/partial boundary are not headline success.

7. **Limitations and Future Work**  
   Sionna 已有 CIR-grounded physical grid baseline，但 Sionna/DeepMIMO full-trained physical-metric comparison 仍未完成；无 hardware validation；无 full multi-target CRLB efficiency proof；A5 robust training 未完成。

### 7.2 Appendix

- Appendix A: Reproducibility manifest and script map.
- Appendix B: Extra G2 seed/cell table.
- Appendix C: A4 cross-L, L=16 boundary, and SNR sensitivity boundary.
- Appendix D: Lemma 1 proof details.
- Appendix E: Lemma 2 `J(K)` trade-off and early-stop differentiability note.
- Appendix F: A5 stress profiles and downgrade rationale.
- Appendix G: DeepMIMO access audit and five-seed scalar-alpha proxy campaign.
- Appendix H: Sionna CDL-A/C/D scaled support、effective-sparsity diagnostic、CIR-grounded physical grid baseline 与 clean-grid floor。

---

## 8. Reviewer Risk Register

| Risk | Current status | Required handling |
|---|---|---|
| Overclaiming A4 | high risk if wording is broad | Write only L>=32 high-L/platform early stopping |
| A5 not passing main gate | known downgrade | Move to appendix/high-stress boundary |
| DeepMIMO overclaim | access ready, O1 weak, I3 partial | Report the five-seed CI and negative I3 cell; do not claim full trained Set E performance |
| CDL support overclaim | energy-supported but exact-bin-weak; physical grid floor recorded | Report the CDL-D 0 dB/L=16 failure cell, projected-angle definition, and absence of trained-estimator comparison |
| Small sample counts | moderate risk | Use “local synthetic/off-grid”; SNR sweep is now boundary evidence, not positive robustness |
| Missing 2024-2026 citations | open writing task | Add BibTeX and named closest-work table before submission |
| CRLB scope | moderate risk | Single-target high-SNR trend only |
| FDMA spectral efficiency | known reviewer concern | Keep FDMA/DDM/TDM trade-off paragraph |

---

## 9. Immediate Next Actions

1. Draft paper section plan under `06_paper_and_delivery/` using this v2.3R document and the evidence table.
2. Add a references/BibTeX sprint for 2024-2026 tensor ISAC, deep unfolding JCAS, off-grid sparse recovery, and DeepMIMO papers.
3. If A4 needs a broader efficiency claim, redesign the refinement schedule or training objective before retesting cross-SNR early stopping. The scalar plateau SNR sweep, scalar threshold frontier, and lightweight SNR-aware gate diagnostic are boundary evidence and must not be rescued by wording.
4. Attach the full trained G2/T-OMP-Net path to DeepMIMO and add physical angle/delay metrics; preserve the O1 weak and I3 partial proxy results as boundary evidence.
5. Attach the trained estimator to the CIR-grounded Sionna metric contract and demonstrate improvement over the recorded grid/clean-grid floors before treating E1 as a main external-channel result.

---

## 10. Current Paper-Ready Claim Set

The current v2.3R paper can defensibly claim:

1. A physically constrained Tensor-OMP unfolding path improves local synthetic/off-grid estimation over grid Tensor-OMP at locked paper scale.
2. At SNR=20 dB, a high-L plateau early-stop rule reduces unfolding depth/FLOPs for L>=32 while staying within a small NMSE gap to fixed K=8; SNR robustness remains unproven.
3. The tensor model is supported by on-grid Kruskal sanity, analytic FIM validation, and single-target high-SNR CRLB trend consistency.
4. Synthetic cross-scene transfer provides fallback portability evidence, but not external ray-traced validation.
5. At five seeds × 50 samples/profile/seed, Sionna CDL-A/C/D has stable top-k energy recovery, an explicit exact-bin limitation in over-budgeted low-SNR CDL-D cells, and a reproducible CIR-grounded physical grid baseline with quantified representation floor.
6. Across five 100-user seeds, the fixed scalar source-alpha proxy has weak O1_60 support and partial I3_60 support; this is supporting ray-traced evidence, not the full trained estimator result.

The current v2.3R paper cannot yet claim:

1. DeepMIMO Set E performance.
2. Sensors-ready CDL physical angle/delay performance from the full trained estimator.
3. Full nominal HIR-JL robustness as a main contribution.
4. Global IA-AUD optimal-depth behavior.
5. Full multi-target CRLB asymptotic efficiency.
6. Hardware or real-world measured validation.

This is the stable writing boundary for the next manuscript pass.
