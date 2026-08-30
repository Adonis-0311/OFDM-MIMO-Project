# v2.3R 稳妥执行版：审稿意见接受 + 数学修正 + 我的补充判断

> 输入：`V2_3_INNOVATION_AND_CODEX_PLAN.md`（我）+ `V2.3 修改要点总结.pdf`（外部 review）
> 时间：2026-06-24
> 本文件作用：把 v2.3 → v2.3R 的所有差量落到一份文档；v2.3R 取代 v2.3 成为活跃执行版本。

---

## 1. 我对外部 review 的判断（先表态）

| Review 论点 | 我的判断 | 处理 |
|---|---|---|
| v2.3 加料过多，主线发散 | **接受** | 4 贡献版本，A6 降级 |
| **Lemma 2 闭式 K\*(L) 推导数学错误** | **接受，严重错误** | 必须改写，见 §3.1 |
| A4 IA-AUD 机制本身保留，理论改成 trade-off 解释 | 接受 | 见 §3.1 |
| A5 HIR-JL 互耦改为物理约束参数化 $C_{ij}=\rho^{|i-j|}e^{j\phi_{ij}}$ | 接受 + 强化 | 见 §3.2 |
| A6 MAML 降级 | **接受** | 主线删除，仅留 future work 一句 |
| MOMPnet / DDA-Net 复现降级为 best-effort appendix | **接受** | 主图不依赖；保留差异表 |
| 贡献从 5 压回 4 | 接受 | 见 §2 |
| 投稿顺序改 Sensors → Systems → TVT → SP → IoT-J | 接受 | 见 §5 |
| Codex Pack 分阶段，不一次推进 | 接受 + 加门控 | 见 §6 |

**外部 review 抓得最准的一点是 Lemma 2 的数学错误**——我原写的：

$$\mathbb{E}[\text{NMSE}_K] \leq C_2 e^{-\beta K} + C_3 \frac{L^2}{(L_{\max}-L)^2}$$

的第二项与 K 无关，从这里推不出有限 $K^*(L)$。审稿人会直接打回。

这处错误必须以"我没注意到"的姿态接受，不要嘴硬。

---

## 2. 4 贡献版本（C1-C4）

**C1（建模）**：mmWave MIMO-OFDM ISAC 系统的角度-时延-多普勒三维稀疏张量统一模型；通信信道估计与雷达目标参数估计统一为稀疏核张量恢复问题。

**C2（算法 + 物理 off-grid）**：T-OMP-Net 模型驱动深度展开网络；每层结构与 Tensor-OMP 迭代一一对应；引入物理 bounded off-grid refinement（tanh 重参数化）；Off-Grid Mismatch Lemma（Lemma 1）形式化离网修正后的一阶误差界。

**C3（可辨识性感知 + 联合损失）**：IA-AUD 可辨识性感知自适应展开深度（trade-off 解释，非闭式最优）；Hungarian permutation-invariant ISAC 联合损失（NMSE + Param + Sparse + Off-grid 四项）。

**C4（鲁棒性 + 跨场景验证）**：HIR-JL 硬件失真鲁棒训练（相位噪声 + IQ 不平衡 + 物理参数化互耦）；DeepMIMO 外部泛化验证（限定为 channel NMSE + 角度/时延 RMSE，不承担速度）；Kruskal 可辨识性 + 字典过采样消融；5L 联合 CRLB 渐近紧致性。

→ C1/C2 是机制独占点；C3 是设计独占点；C4 是工程鲁棒性 + 防守证据。MAML 与精确复现 MOMPnet/DDA-Net **从主贡献删除**。

---

## 3. 数学与机制层修正

### 3.1 Lemma 2 重写：从"最优深度"到"两项 trade-off + 操作目标"

**旧版本（错误）**：声称 $K^*(L) = \frac{1}{\beta}\log\frac{C_2\beta(L_{\max}-L)^2}{2C_3 L^2}$ 是 NMSE 单目标最优深度——但 NMSE 第二项与 K 无关，不存在这样的 NMSE 最优 K。

**新版本（修正）—Lemma 2 (Depth-Identifiability Trade-off, Operational Form)**

> 设 K 为 T-OMP-Net 展开层数，L 为目标数，$L_{\max}$ 为 Kruskal 上限。存在常数 $C_1, C_2, C_3 \geq 0$ 与几何收敛率 $\beta>0$，使得：
> $$\mathbb{E}[\text{NMSE}_K \mid \mathcal{E}_{\text{supp}}] \leq C_1 e^{-\beta K} + C_2 \Psi(L, L_{\max}) + C_3 \sigma^2 \tag{5-7}$$
> 其中 $\Psi(L, L_{\max}) = \frac{L^2}{(L_{\max} - L + \epsilon)^2}$ 是可辨识性风险因子，$\mathcal{E}_{\text{supp}}$ 是支撑近似正确事件，$\sigma^2$ 是噪声底。
>
> 上式仅说明：（i）层数增加可压低首项；（ii）当 $L \to L_{\max}$ 时第二项发散，**任何固定深度无法消除**；（iii）噪声底由 $C_3 \sigma^2$ 给定。

**操作目标**（K 真正可优化的地方）：

$$J(K) = \mathbb{E}[\text{NMSE}_K] + \lambda_{\text{FLOPs}} \cdot K$$

最优深度由 FLOPs 代价驱动：

$$K^*(\lambda_{\text{FLOPs}}) \approx \frac{1}{\beta}\log\frac{C_1 \beta}{\lambda_{\text{FLOPs}}}$$

→ 论文叙述变成："Lemma 2 解释为何困难样本需要更多展开层，简单样本可早停降 FLOPs；IA-AUD 学习每样本的早停决策。"

**论文位置**：§5.1.2 改名为 "Depth-Identifiability Trade-off Explanation"；附录 E 不再写"最优深度证明"，改写 $J(K)$ 凸性 + Gumbel-Sigmoid 早停可微化推导。

### 3.2 Lemma 1 边界条件显式化（外部 review 隐含的修正）

Review §二.3 提到 Lemma 1 应聚焦"正确支撑或近似正确支撑条件下"。我接受并显式加入：

**Lemma 1（修订陈述）**：在事件 $\mathcal{E}_{\text{supp}}=\{\hat{\mathcal{S}} \supseteq \mathcal{S}^* \text{ or } d_H(\hat{\mathcal{S}}, \mathcal{S}^*) \leq 1\}$ 下，bounded off-grid refinement 把 $\epsilon_{\text{grid}}$ 从 $O(N_v^2 \Delta_{\text{grid}}^2)$ 阶降至 $O(\sigma^2)$ 阶。

这个修正避免审稿人攻击"支撑选错时 lemma 仍成立吗"。

### 3.3 HIR-JL 互耦参数化修正

接受 review 的 $C_{ij} = \rho^{|i-j|} e^{j\phi_{ij}}$ 物理参数化。但我在此基础上加一层：
- $\rho \in [0, 0.3]$ 可学习（窄阵列实测范围）
- $\phi_{ij}$ 不是逐元自由学习，而是 $\phi_{ij} = \phi_0 \cdot |i-j|$（线性相位累积），$\phi_0$ 可学习

→ 学习参数从 $O(N_v^2)$ 降到 2，进一步压审稿人对"过参数化"的质疑。

---

## 4. 三项创新最终去留

| 项 | v2.3 计划 | v2.3R 最终 | 关键修正 |
|---|---|---|---|
| **A4 IA-AUD** | 主线 + Lemma 2 闭式最优深度 | **主线**（C3 的一半） | Lemma 2 改 trade-off 解释；$K^*$ 由 $J(K) = NMSE + \lambda_{FLOPs}K$ 决定 |
| **A5 HIR-JL** | 主线 + 互耦自由学习 | **主线**（C4 的一半） | 互耦改物理参数化 $\rho^{|i-j|}e^{j\phi_0|i-j|}$；只 2 个可学习参数 |
| **A6 FSMA MAML** | 主线（C5） | **降级为附录 / future work 一句** | 主线删除；§6.7 保留普通 fine-tune 对比；T4.3 暂缓 |

---

## 5. 期刊定位（接受 review 顺序）

**新主路径**（按 review §五）：

1. **IEEE Sensors Journal**（2 区 / 4.5）— ISAC 目标参数提取 + 硬件鲁棒叙述匹配最高
2. **IEEE Systems Journal**（2 区 / 4.0）— 完整 ISAC pipeline + 系统级验证
3. **IEEE TVT**（2 区 / 7.1）— 车载毫米波 + 高速移动；要求实验更扎实
4. **Signal Processing (Elsevier)**（大类 2 区 / 3.6）— 方法论匹配，但与稀疏恢复 SOTA 正面竞争
5. **IEEE IoT-J**（2 区 / 8.9）— 需重新包装为 vehicular IoT / low-altitude IoT；不作为主投

**永久剔除**：Digital Signal Processing（中科院 3 区）。

**我的补充判断**：第 1 和第 2 顺位之间可以打平。Sensors 周期短（中位 3-4 月），Systems 周期长（中位 6-8 月）。若投 Sensors 被拒，转 Systems 需要补 §6.7 联合 ISAC 场景的系统级实验图——本周写 v2.3R 文档时就把这张图占位画好，避免投稿后临时补料。

---

## 6. Codex 任务包重排（分阶段 + 风险门控）

接受 review 的三阶段优先级，并在每两阶段间加"门控"（gate）：上一阶段不通过验收，下一阶段不启动。

### 阶段 1（W1-W3）—— 基础设施 + 经典 baseline

启动 Pack 0（基础设施）+ Pack 1（数据与信道）+ Pack 2（经典 baseline）+ Pack 7 部分（绘图工厂 + manifest）。

**门控 G1**：Tensor-OMP 在 Set A 上单/多目标恢复 RMSE 接近 CRLB；NMSE / 距离 / 速度 / 角度 RMSE 全部可输出；CRLB 高 SNR 趋势一致。**G1 不通过 → 不启动阶段 2。**

### 阶段 2（W4-W6）—— 最小 T-OMP-Net

启动 Pack 3（T-OMP-Net 骨架 + bounded off-grid + Hungarian loss + 课程）。

**门控 G2**：T-OMP-Net 在 SNR=20 dB 下 NMSE 优于 Tensor-OMP ≥ 3 dB；不同目标排列下 loss / RMSE 一致（permutation-invariance 验证）；off-grid 消融在 $\rho_\theta = 2$ 时把 NMSE 拉低 ≥ 5 dB。**G2 不通过 → 不启动阶段 3，回去定位问题。**

### 阶段 3（W7-W9）—— v2.3R 增强模块（A4 + A5 + 论文尺度 Kruskal + DeepMIMO）

启动 Pack 4 中的 **T4.1 (IA-AUD) + T4.2 (HIR-JL)**；T4.3（MAML）**暂缓不启动**。
启动 Pack 6（实验跑批）+ 论文尺度 §6.5.13 + DeepMIMO Set E。

**门控 G3**：
- IA-AUD 在相近 NMSE 下平均 FLOPs 下降 ≥ 25%；gating 训练收敛
- HIR-JL 在 $\sigma_\phi=2°$ 测试集 NMSE 改善 ≥ 5 dB
- §6.5.13 论文尺度（128×16×32, $L \in \{2,4,8,16,32,64\}$）扫描完成
- DeepMIMO Set E 至少 channel NMSE + angle/delay RMSE 通过

### 阶段 4（W10-W12）—— 论文撰写 + 投稿

- Lemma 1 附录 D 完整证明（5 天）
- Lemma 2 trade-off 解释 + $J(K)$ 凸性附录（3 天）
- §2.4 SOTA 差异表（保留即可，不依赖复现）
- 主图回填 + cover letter
- 首投 IEEE Sensors Journal

### 阶段 5（W13-W14）—— 缓冲

预留返修 / 转投 IEEE Systems 准备。

### 暂缓 / 降级（永不在阶段 1-4 内启动）

- T4.3 MAML 元学习（移到 future work 一句）
- T5.1 MOMPnet 精确复现 → 改为"读论文 + 差异表条目 + 算法描述"（不写代码）
- T5.2 DDA-Net 精确复现 → 同上

---

## 7. 我的补充判断（review 没提的 4 点）

### 7.1 实验前置风险闸门（pre-experiment smoke gates）

在 A4 / A5 投入大量训练前，先各做一个 < 100 行的 smoke 验证"问题是否真存在"：

**A4 pre-smoke**：在固定深度 T-OMP-Net 上，画 NMSE vs 深度曲线对 $L \in \{2, 8, 32\}$。若曲线显示"困难样本 L=32 在深度 8 已饱和，简单样本 L=2 在深度 3 已饱和"，则 IA-AUD 有真实空间；若都饱和在同一深度，IA-AUD 是伪命题，立刻删除。

**A5 pre-smoke**：在固定深度 T-OMP-Net 上，clean 训练 → 用 $\sigma_\phi = 0.5°/1°/2°/3°$ 测试集评估。若 $\sigma_\phi < 2°$ 时 NMSE 已经不显著退化，HIR-JL 是伪命题；若 $\sigma_\phi=1°$ 时 NMSE 退化 > 8 dB，HIR-JL 价值显著。

→ pre-smoke 是 1-2 天工作，但能在 A4/A5 投入 1.5-2 周训练之前杀死伪命题。这是我额外加的保险。

### 7.2 Set E 边界声明前移到 §1.2

v2.2 §6.2 已有 DeepMIMO Set E 不承担速度 RMSE 的声明。但 review 强调"DeepMIMO 不一定提供完整动态速度标签"——我建议把这条边界声明**前移到 §1.2 贡献 C4 的脚注**，让审稿人在读贡献时就知道范围，而不是到 §6.2 才发现，避免审稿人质疑"为什么不在 DeepMIMO 上做速度对比"。

### 7.3 C3 内部 IA-AUD + Hungarian 的协同叙述

把 IA-AUD 和 Hungarian 打包进同一个 C3，不是简单并列，而是有协同：Hungarian permutation-invariant 联合损失 → 让每样本损失对目标排列稳定 → 才有可能让 gating module 从这个损失反传出"是否需要更多层"的有效信号。这个协同要在 §4.x 写出来，不是堆 bullet。

### 7.4 v2.2 → v2.3R 重命名而非新版本号

v2.3 文档已经在 `01_design_and_plan/V2_3_INNOVATION_AND_CODEX_PLAN.md`，但还未生成 `ISAC_DeepUnfolding_TechnicalDesign_v2.3.md` 主文档。建议**跳过 v2.3 主文档**，直接生成 `ISAC_DeepUnfolding_TechnicalDesign_v2.3R.md`，避免 v2.3 错误的 Lemma 2 进入版本历史。

---

## 8. v2.3 文档差量表（最终版，取代我之前的差量表）

| 章节 | 修订内容 | 与 review §八 是否一致 |
|---|---|---|
| §0 | 加 0.4 v2.3R vs v2.2，明确 A4/A5 主线 + A6 future work + 复现降级 | 一致 |
| §1.2 | 4 贡献 C1-C4 重写；C4 脚注声明 Set E 范围（新增我的补判 7.2） | 一致 + 加脚注 |
| §1 段落 4 | 用 V2_2_DIRECTION_REVALIDATION §3.3 新措辞 | 一致 |
| §2.4 | 实证 SOTA 表（不依赖复现）；MOMPnet / DDA-Net 进 Related Work 和差异表 | 一致 |
| §4.0 | 新增"与 MOMPnet/DDA-Net/Unified Tensor ISAC 差异化论证" | 一致 |
| §4.3a | 新增 IA-AUD adaptive depth + gating module；**删除 Lemma 2 闭式最优深度** | 一致 |
| §4.4 | Hungarian + 4 项联合损失（NMSE + Param + Sparse + Off-grid） | 一致 |
| §4.4a | 新增 HIR-JL；互耦改 $\rho^{|i-j|}e^{j\phi_0|i-j|}$ 2 参数物理形式（强化我的补判 3.3） | 一致 + 强化 |
| §4.5 | 训练策略汇总；MAML 移到 future work 一句 | 一致 |
| §5.1.1 | Lemma 1 加事件 $\mathcal{E}_{\text{supp}}$ 条件（我的补判 3.2） | review 隐含 |
| §5.1.2 | 改名 "Depth-Identifiability Trade-off Explanation"；写 trade-off 不写最优；引出 $J(K)$ | 一致 |
| §5.2 | 5L 联合 CRLB（保持 v2.2） | 不变 |
| §6.2 | Set E 范围限定（v2.2 已有，前置到 §1.2 脚注） | 一致 + 我的补判 7.2 |
| §6.5.13 | 论文尺度过采样 + Kruskal 退化 | 不变 |
| §6.5.14 | HIR-JL 鲁棒性实验 | 一致 |
| §6.5.15 | IA-AUD 自适应深度 FLOPs 对比 | 一致 |
| §6.7 | 普通 cross-scene fine-tune（不做 MAML） | 一致 |
| 附录 D | Lemma 1 完整证明 | 一致 |
| 附录 E | 改名 $J(K)$ 凸性 + Gumbel-Sigmoid 早停可微化（不再是 Lemma 2 闭式证明） | 一致 |
| 附录 F（新增） | A4 pre-smoke + A5 pre-smoke 结果（我的补判 7.1） | review 未提 |

---

## 9. 本周（2026-06-25 起）落地动作（取代 V2_3 §5）

| # | 动作 | 责任 | 验收 |
|---|---|---|---|
| 1 | 起草 `ISAC_DeepUnfolding_TechnicalDesign_v2.3R.md`（跳过 v2.3 主文档） | 人工 | 文件落盘 |
| 2 | 8 篇核心文献 BibTeX + 一页阅读笔记 | 人工 | 8 个 .md |
| 3 | DeepMIMO O1/I3 下载 + 5G Toolbox license 测试 | 人工 | audit / 降级方案 |
| 4 | 启动 Codex Pack 0 + Pack 1 + Pack 2 + Pack 7 部分（**阶段 1**） | Codex | G1 门控 |
| 5 | **本周不启动 Pack 3 任何任务**；等阶段 1 验收通过 | — | G1 通过 |
| 6 | git commit + tag `v2.3R-steady-2026-06`，把本文件与 v2.2 一起固化 | 人工 | git log |
| 7 | 把 `V2_3_INNOVATION_AND_CODEX_PLAN.md` 顶部加一行"已被 v2.3R 取代，错误的 Lemma 2 闭式推导已修正"，保留为决策溯源 | 人工 | 注解可见 |

---

## 10. 一句话总结

接受外部 review 全部判断；Lemma 2 数学错误是我的责任，必须改写；A4/A5 留主线但 A4 的理论框架改为操作目标 $J(K)$ 驱动，A5 的互耦改为 2 参数物理形式；A6 与精确 SOTA 复现降级；4 贡献结构 + IEEE Sensors 首投 + Codex 分阶段三门控；额外加 pre-experiment smoke gates 杀伪命题、Set E 范围前置、IA-AUD + Hungarian 协同叙述、跳过 v2.3 主文档直出 v2.3R。
