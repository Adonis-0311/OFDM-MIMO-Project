> **⚠ 本文件已被 `V2_3R_STEADY_EXECUTION_PLAN.md` 取代（2026-06-24）。**
>
> 关键问题：本文 §2.1 中 Lemma 2 的"闭式最优深度 $K^*(L)$"推导**数学错误**——
> 不等式右侧第二项 $C_3 L^2/(L_{\max}-L)^2$ 与 K 无关，无法从 NMSE 单目标推出有限最优 K。
> 修正方法见 v2.3R §3.1：把 Lemma 2 改写为 trade-off 解释，$K^*$ 由操作目标 $J(K)=\text{NMSE}_K + \lambda_{\text{FLOPs}}K$ 决定。
>
> 此外 v2.3R 还将贡献从 5 压回 4、A6 MAML 降级、SOTA 精确复现降级、Codex Pack 改为分阶段 + 风险门控。
> 本文件保留为决策溯源，不再作为执行版本。

---

# v2.3 增量计划：中科院 2 区+ 投稿定位 + 创新性补强 + Codex 任务包

> 基线：`V2_2_DIRECTION_REVALIDATION.md`（2026-06-24）
> 本文件作用：把 v2.2 → v2.3 的具体差量落到三件事：
> 1. 投稿目标改按**中科院分区**重排（不再按 JCR 单一口径）
> 2. 加 3 项创新性补足（A4 / A5 / A6），抵消 MOMPnet/DDA-Net 抢占造成的差异度下降
> 3. 把可外包的工程量明确切成 Codex 任务包，每个任务自包含、有验收标准

---

## 1. 期刊定位重排（中科院 2 区 +）

### 1.1 旧定位失效项

依据 2025 中科院分区表（已停止更新，2025 为最后一版）：

| 期刊 | 旧 v2.2 定位 | 真实分区 | 处理 |
|---|---|---|---|
| Signal Processing (Elsevier) | "Q2 首投" | 大类工程技术 **2区** / 小类电子电气 3区，IF 3.6 | 保留为候选 |
| **Digital Signal Processing (Elsevier)** | "Q2 第二顺位" | 大类工程技术 **3区** / 小类电子电气 3区，IF 3.0 | **剔除**（不达 2 区底线） |
| IEEE Sensors Journal | "Q1/Q2 第三顺位" | **2区**，IF 4.5 | 升为首投 |
| IEEE Systems Journal | "Q2 第四顺位" | **2区**，IF 4.0 | 保留 |

### 1.2 新的 2 区+ 候选清单（按命中率与 fit 排序）

| # | 期刊 | 中科院 / IF | 适配理由 | 命中率重估 | 风险 |
|---|---|---|---|---|---|
| 1 | **IEEE Sensors Journal** | 2 区 / 4.5 | "ISAC 多目标参数提取 + Hungarian permutation-invariant + 角-时延-多普勒 RMSE"叙述与传感器期刊高度匹配；MOMPnet/DDA-Net 主战场是信道估计而非 ISAC，差异度被放大 | **65-75%** | 个别审稿人质疑"sensing scope = radar"边界 |
| 2 | **IEEE Transactions on Vehicular Technology (TVT)** | 2 区 / 7.1 | 车载毫米波 + ISAC + 高速移动场景与 TVT 命题契合；IF 高，且 TVT 对工程完整度宽容 | **45-55%** | 周期偏长（中位 7-9 月） |
| 3 | **IEEE Internet of Things Journal (IoT-J)** | 2 区（2025 从 1 区 TOP 下调）/ 8.9 | 6G ISAC / 车载 / 低空 IoT 节点感知是 IoT-J 当前主推方向；IF 极高 | **40-50%** | 投稿量爆炸（2025-07 单月超 2000 篇）；初审拒稿率上升 |
| 4 | **Signal Processing (Elsevier)** | 大类 2 区 / 3.6 | 与"deep unfolding × sparse recovery × tensor"主题匹配，且 Elsevier 周期短（中位 3-5 月） | **35-45%** | MOMPnet 极可能首投这里；竞争白热化 |
| 5 | **IEEE Systems Journal** | 2 区 / 4.0 | 适合作"端到端系统集成"叙述（FDMA + 虚拟阵列 + 张量 + ISAC pipeline） | **45-55%** | 需要补 §6.7 联合 ISAC 场景的系统级实验 |

### 1.3 1 区 stretch 与 letter 备投（非主路径）

| 期刊 | 中科院 / IF | 用途 |
|---|---|---|
| IEEE Transactions on Wireless Communications (TWC) | 1 区 / 10.7 | 若 A4 + A5 + A6 全部落地且 5L CRLB + Lemma 1 都严格，可尝试 stretch 投；预期命中率 15-25% |
| IEEE Wireless Communications Letters (WCL) | 2 区 / Q2 / 5 页 letter | "Lemma 1 形式化 + 1 张紧凑消融图"快速 letter 备投；命中率 35-45% |
| IEEE Trans. Cognitive Communications and Networking (TCCN) | 2 区 / 7.4 | 若把"自适应展开深度 + 跨场景元学习"叙述放在 cognitive 框架下，匹配度上升；命中率 30-40% |

### 1.4 新投稿顺序（取代 v2.2）

> 主路径：**IEEE Sensors → IEEE TVT → IEEE Systems → Signal Processing (Elsevier) → IEEE IoT-J**
> 备投路径（若主线 1 期刊被拒）：转 **IEEE TCCN** 或 **IEEE WCL** letter

DSP (Elsevier) 永久剔除（中科院 3 区）。

### 1.5 投稿信差异化叙述模板

每家期刊 cover letter 必须明确把 v2.3 创新点对位：

```
We submit "Sparse Tensor-OMP Deep Unfolding Network with Identifiability-Aware Adaptive
Depth, Physical-Constrained Off-Grid Refinement, and Hardware-Robust Joint Channel-Target
Estimation for mmWave MIMO-OFDM ISAC Systems" to <JOURNAL>.

We are aware of the very recent MOMPnet (arXiv 2601.10771) and DDA-Net (arXiv 2604.05389),
which address overlapping but distinct problems. Our work differs in four concrete ways:
(1) we provide a closed-form Off-Grid Mismatch Lemma bounding the residual after refinement;
(2) we couple unfolding depth to the Kruskal identifiability bound via an adaptive gating
module (IA-AUD), giving sample-wise depth control;
(3) we train under differentiable hardware-impairment layers (phase noise, IQ imbalance,
array mutual coupling) and report ISAC performance on impaired test sets;
(4) we use a Hungarian permutation-invariant joint loss to align communication NMSE and
sensing range/velocity/angle RMSE under one optimization target.

The manuscript fits <JOURNAL> because <sensing-side framing / vehicular emphasis / system
integration / signal-processing methodology>.
```

---

## 2. 创新性补足（A4 / A5 / A6）

下面三项是把"独占点四元组"扩成"独占点七元组"的具体增量。每项都给出：定位 / 数学动机 / 实验设计 / 论文位置 / 与现有 SOTA 的差异。

### 2.1 A4 — Identifiability-Aware Adaptive Unfolding Depth（IA-AUD）

**定位**：把 Kruskal 可辨识性边界与展开层数耦合。当当前样本估计目标数 $\hat{L}$ 接近 Kruskal 上限 $L_{\max}$ 时，自动增加有效迭代层；远离上限时减少。

**数学动机**：v2.2 §6.5.13(c) 已证明 NMSE 在 $L \to L_{\max}$ 时急剧退化。说明此时需要更多 OMP 迭代以解决严重耦合；但定深网络浪费推理算力。

**机制**：每层后接一个 gating module $g_k(\hat{\mathcal{H}}_k, \hat{L}_k) \to [0,1]$。当 $g_k < \tau$ 时早停。训练用 Gumbel-Sigmoid 让 $g$ 可微。

**理论 hook**：扩展 Lemma 1 → **Lemma 2（Depth-Identifiability Tradeoff）**

$$
\mathbb{E}[\text{NMSE}_K] \leq \underbrace{C_2 \cdot \exp(-\beta K)}_{\text{展开收敛}} + \underbrace{C_3 \cdot \frac{L^2}{(L_{\max} - L)^2}}_{\text{可辨识失败惩罚}}
$$

最优深度 $K^*(L) = \frac{1}{\beta}\log\frac{C_2 \beta (L_{\max}-L)^2}{2 C_3 L^2}$ —— 显示深度应随 $L$ 增长。

**实验**：
- 在 §6.5.13(c) 同设定下，让 IA-AUD 自适应深度；记录平均深度 vs $L$ 曲线
- 验证：固定深度 8 层 vs IA-AUD 自适应；同 NMSE 下 IA-AUD 推理 FLOPs 降 25-40%

**论文位置**：v2.3 §4.3a（新增）+ §5.1.2 Lemma 2 + §6.5.13(e)

**与 SOTA 差异**：MOMPnet、DDA-Net、Unified Tensor ISAC 均为**固定层数**；自适应深度展开在 vision 领域有先例（DEQ、ALISTA），但**耦合 Kruskal 界**是无 SCI 命中的新点。

**预期工作量**：2 周（含理论 + 实验）

---

### 2.2 A5 — Hardware-Impairment-Robust Joint Loss（HIR-JL）

**定位**：把"相位噪声 + IQ 不平衡 + 阵列互耦"三类硬件失真做成可微层，纳入训练。

**数学动机**：MOMPnet 文摘提到"mitigating hardware impairments"但只对字典做了对齐补偿；本文以"端到端鲁棒训练 + 测试 set 含失真"双轨证明 ISAC 联合输出的鲁棒性。

**机制**：在 Set A 数据生成器中增加 3 个差分模块：

```
H_distorted = MutualCoupling(IQImbalance(PhaseNoise(H_clean)))
```

参数随机采样：
- 相位噪声 $\sigma_\phi \sim U[0.5°, 3°]$
- IQ 增益失配 $\alpha \sim U[0.95, 1.05]$、相位失配 $\theta \sim U[-3°, 3°]$
- 互耦矩阵 $C \in \mathbb{C}^{N_v\times N_v}$，按近邻指数衰减，自学习

**实验**：
- §6.5.14（新增）：固定 SNR=15 dB，扫描 $\sigma_\phi \in [0,5°]$ 与 IQ 不平衡幅度
- 对比 baseline：纯 clean 训练 vs HIR-JL 训练；后者在失真测试集上 NMSE 与 RMSE 全面优于前者
- 预期 NMSE 改善：5-8 dB 在 $\sigma_\phi = 2°$；角度 RMSE 改善 30-40%

**论文位置**：v2.3 §4.4a（损失项扩展）+ §6.5.14

**与 SOTA 差异**：MOMPnet 仅对字典补偿；DDA-Net 完全不处理硬件；本文是 **ISAC 双输出在硬件失真下的鲁棒训练**，叙述首创。

**预期工作量**：1.5 周

---

### 2.3 A6 — Few-Shot Meta-Adaptation for Cross-Scene Generalization（FSMA）

**定位**：MAML 风格外循环，跨多种 CDL profile 与 DeepMIMO 场景训练；新场景 5-shot 微调即可适应。

**数学动机**：DDA-Net 报告"20-sample few-shot 仍能保 1.5 dB lead"。我们用 MAML 把这个数字从 20 降到 5，并在 ISAC 双输出上同步达成。

**机制**：
- 任务集合 $\mathcal{T} = \{\text{Set A}_{\text{multi-target}}, \text{CDL-A}, \text{CDL-C}, \text{CDL-D}, \text{DeepMIMO-O1}, \text{DeepMIMO-I3}\}$
- 内循环：单任务 $\theta' = \theta - \alpha \nabla_\theta \mathcal{L}_{\mathcal{T}_i}(\theta)$ ，1-5 步
- 外循环：$\theta \leftarrow \theta - \beta \sum_i \nabla_\theta \mathcal{L}_{\mathcal{T}_i}(\theta'_i)$

**实验**：
- §6.7.x（扩展现有跨场景节）：在 Set A 训练 + CDL-A/C/D + O1 元训练后，I3 5-shot 微调
- 对比：纯 Set A 训练直接迁移 vs MAML 元训练
- 预期 NMSE 改善：3-5 dB；角度 RMSE 改善 25-35%

**论文位置**：v2.3 §4.5（训练策略汇总加 MAML 子节）+ §6.7.x

**与 SOTA 差异**：DDA-Net 是普通 fine-tune；本文是 MAML 元学习；且 ISAC 双输出元目标。

**预期工作量**：2 周

---

### 2.4 v2.3 核心贡献新陈述（替换 v2.2 C2-C3）

**C1（建模，保持）**：3D 稀疏张量 ISAC 模型 + FDMA 虚拟阵列。

**C2（算法）**：T-OMP-Net 展开网络 + **A4 IA-AUD 自适应深度** + 四阶段课程训练。

**C3（机制）**：物理 bounded off-grid（Lemma 1 形式化界）+ **Lemma 2 深度-可辨识性权衡** + Hungarian permutation-invariant ISAC 联合损失。

**C4（鲁棒与泛化）**：**HIR-JL 硬件失真鲁棒训练** + **FSMA few-shot 元适配** + DeepMIMO 跨场景验证。

**C5（验证，原 C4）**：通信侧 NMSE/BER + 感知侧 5L RMSE + FLOPs/延迟 + Kruskal 可辨识性消融 + 5L 联合 CRLB 渐近紧致性。

→ 论文从"4 贡献"扩成"5 贡献"，每条都有独占性证据（Lemma + 实验 + 与 SOTA 数值对比）。

---

## 3. Codex 任务包（可外包工程量）

> 思路：Codex / o1-codex 适合做规格明确、有参考实现、有验收标准的工程任务；不适合做架构决策、定理证明、SOTA 差异叙述。下面把工程主线切成 7 个 pack、27 个任务，每个独立可派单。

### 3.1 Codex 适合做 / 不适合做

| ✓ 适合 | ✗ 不适合 |
|---|---|
| dataclass / config / IO 模板 | T-OMP-Net 架构核心选型 |
| 经典算法实现（OMP/SOMP/SBL/CP-OMP） | Lemma 1 / Lemma 2 证明撰写 |
| PyTorch nn.Module 套壳 + forward 函数 | SOTA 差异化叙述（§4.0） |
| 单元测试与冒烟脚本 | 期刊投稿信 |
| matplotlib 绘图脚本 | 创新点是否成立的判断 |
| LaTeX 表格自动生成 | Lemma 1 数值拟合是否符合理论 |
| FIM 数值差分交叉验证 | MOMPnet/DDA-Net 复现细节争议（需人工把关） |
| 配置 hash + 种子追踪 | 论文图表选择 |

### 3.2 Pack 0 — 协议与基础设施（W1，必须先做）

**T0.1 项目骨架 + 依赖锁定**
- 验收：`pyproject.toml` / `requirements.txt` 锁定 PyTorch≥2.3 / scipy / numpy / matplotlib / einops / pyyaml；MATLAB 侧锁 R2024a + 5G Toolbox
- 输出：`03_active_modules/pyproject.toml`、`03_active_modules/environment.md`

**T0.2 配置 + 种子管理**
- 输入：YAML 配置示例 + 字段表
- 验收：`Config.load(path) → dataclass`；`seed_all(seed: int)` 同时设 numpy/torch/python `random`；配置 hash 写入每个 result 的 summary.md
- 输出：`03_active_modules/common/config.py`、`common/seed.py`、`common/manifest.py`

**T0.3 接口规范文档**
- 输出：`03_active_modules/INTERFACES.md`，明确所有模块的输入输出 dataclass，禁止字符串字段约定

---

### 3.3 Pack 1 — 数据与信道（W1-W2）

**T1.1 Set A 数据生成器**
- 输入规格：v2.2 §3.1（FDMA）+ §3.2（虚拟阵列）+ §3.3（CP 张量）
- 验收：单元测试逐项匹配 v2.2 公式 3-1～3-5；多目标场景 ground truth 与 channel taps 双轨输出；100 蒙特卡洛 < 30 s
- 输出：`03_active_modules/data/set_a_generator.py` + `tests/test_set_a.py`

**T1.2 3GPP CDL-A/C/D 包装器**
- 输入规格：调用 MATLAB `nrCDLChannel`（首选）或 QuaDRiGa（备案）；统一输出 Channel struct
- 验收：3 个 profile 各 100 个 realization 与官方参考波形 NMSE < -40 dB
- 输出：`03_active_modules/data/cdl_wrappers.py`

**T1.3 DeepMIMO O1 / I3 加载器**
- 输入规格：`90_archive/2025_thesis_materials/参考/DeepMIMO-*` 已有 MATLAB 接口；将其封装为 Python loader（或 MATLAB → npy 中转）
- 验收：O1 / I3 各取 20 用户位置 → 统一 Channel struct
- 输出：`03_active_modules/data/deepmimo_loader.py`

**T1.4 硬件失真层（HIR-JL 用）**
- 输入规格：A5 §2.2 中 3 个失真模块
- 验收：可关闭、可链式、梯度可微（PhaseNoise / IQImbalance / MutualCoupling）；单元测试覆盖各失真量级
- 输出：`03_active_modules/data/impairments.py`

---

### 3.4 Pack 2 — 经典 baselines（W2-W3）

**T2.1 LS / LMMSE 信道估计**
- 验收：Set A 上 NMSE 与解析参考一致；FLOPs/延迟实测
- 输出：`03_active_modules/baseline/ls_lmmse.py`

**T2.2 OMP / SOMP / SBL 稀疏恢复**
- 参考：现有库 `pylops.OMP`、`spgl1`、`bayesian_compressive`
- 验收：单目标 + L=3 多目标场景恢复 RMSE 与 CRLB 接近
- 输出：`03_active_modules/baseline/sparse_recovery.py`

**T2.3 Tensor-OMP（Algorithm 1）**
- 输入规格：v2.2 §4.1 Algorithm 1
- 验收：与 v2.2 §6.5.13 中的 smoke 结果数值对齐
- 输出：`03_active_modules/baseline/tensor_omp.py`

**T2.4 5L 联合 CRLB 数值 FIM**
- 输入规格：v2.2 §5.2 偏导 5-3a～5-3e
- 验收：解析 FIM 与数值差分 FIM 误差 < 1e-3；高 SNR 渐近紧致性曲线
- 输出：`03_active_modules/baseline/crlb_5L.py`

---

### 3.5 Pack 3 — T-OMP-Net 网络骨架（W3-W4）

**T3.1 单层展开模块**
- 输入规格：v2.2 §4.2 Algorithm 2 每层结构；可学习参数：步长、阈值、字典扰动
- 验收：单层前向数值与 Tensor-OMP 一致（梯度截断版）；100 层堆叠不发散
- 输出：`03_active_modules/tompnet/layer.py`

**T3.2 物理 bounded off-grid 模块**
- 输入规格：v2.2 §4.3 tanh 重参数化；$\delta \in (-\Delta_{\text{grid}}/2, \Delta_{\text{grid}}/2)$
- 验收：smoke 实验复跑：$\epsilon_{\text{grid}}$ 拟合系数中位数 0.5（已有）
- 输出：`03_active_modules/tompnet/offgrid.py`

**T3.3 Hungarian + 联合损失**
- 输入规格：v2.2 §4.4-4.4.1
- 验收：多目标场景下，RMSE 与目标排列无关；梯度仅作用配对量
- 输出：`03_active_modules/tompnet/hungarian_loss.py`

**T3.4 四阶段课程调度器**
- 输入规格：v2.2 §4.2.1 Teacher Forcing → Gumbel → STE → Hard
- 验收：训练曲线 4 段平滑过渡；收敛 NMSE ≤ Tensor-OMP - 3 dB
- 输出：`03_active_modules/train/curriculum.py`

---

### 3.6 Pack 4 — 创新性补足（W4-W5）

**T4.1 IA-AUD 自适应深度 gating（A4）**
- 输入规格：本文档 §2.1
- 验收：自适应深度 vs 固定深度同 NMSE 下 FLOPs 降 ≥ 25%；Gumbel-Sigmoid 训练稳定
- 输出：`03_active_modules/tompnet/adaptive_depth.py`

**T4.2 HIR-JL 训练管线（A5）**
- 输入规格：本文档 §2.2 + T1.4 失真层
- 验收：失真测试集 NMSE 改善 ≥ 5 dB @ $\sigma_\phi = 2°$
- 输出：`03_active_modules/train/hir_train.py`

**T4.3 FSMA MAML 元学习管线（A6）**
- 输入规格：本文档 §2.3
- 验收：I3 场景 5-shot 微调后 NMSE 改善 ≥ 3 dB（vs 直接迁移）
- 输出：`03_active_modules/train/maml_train.py`

---

### 3.7 Pack 5 — SOTA 复现（W5-W6，风险项）

**T5.1 MOMPnet 复现（best-effort）**
- 输入：arXiv 2601.10771 算法描述（无官方代码假设）
- 验收：在 Set A 上跑通；声明"参考复现，未必精确"
- 输出：`03_active_modules/baseline/mompnet_reference.py` + `REPRODUCTION_NOTES.md`
- 备案：若不能复现，按论文报告值"图上参照线"处理

**T5.2 DDA-Net 复现（best-effort）**
- 输入：arXiv 2604.05389 算法描述
- 验收：在 CDL-A 上 NMSE 与论文报告值 ±2 dB 内
- 输出：`03_active_modules/baseline/ddanet_reference.py` + `REPRODUCTION_NOTES.md`

---

### 3.8 Pack 6 — 实验运行与结果聚合（W6-W7）

**T6.1 主实验跑批脚本**
- 输入规格：v2.2 §6.5.1-6.5.12 + §6.5.13 + §6.5.14（新增 A5）+ §6.7.x（新增 A6）
- 验收：每张主图都有独立可复跑入口，写入 `05_results/<exp_name>/`
- 输出：`04_experiments/eval/run_main_experiments.py`

**T6.2 §6.5.13 论文尺度过采样 + Kruskal 扫描**
- 输入：升级 smoke 至 128×16×32 张量；$L \in \{2,4,8,16,32,64\}$
- 验收：on-grid + off-grid + 低 SNR 三组压力设置
- 输出：`04_experiments/eval/run_paper_scale_oversampling.py`

**T6.3 manifest 聚合器扩展**
- 输入：现有 `run_all_v2_2_supplemental_experiments.m` 模式
- 验收：跨 Python / MATLAB 双轨；生成 Markdown + CSV manifest
- 输出：`04_experiments/eval/aggregate_manifest.py`

---

### 3.9 Pack 7 — 论文图表与可复现性（W7-W8）

**T7.1 统一绘图样式工厂**
- 输入：Q2 期刊常见图表样式（serif font / colorblind-safe / 一致 marker / 2 列 + 1.5 列两种宽度）
- 验收：所有主图调用同一 `figure_factory.create(...)`
- 输出：`03_active_modules/common/figure_factory.py`

**T7.2 CSV → LaTeX 表格自动生成**
- 验收：所有 §6 表格直接由实验 CSV 生成；带 booktabs + siunitx 格式
- 输出：`03_active_modules/common/latex_table.py`

**T7.3 端到端冒烟测试**
- 验收：CI / 本地一键跑通从数据 → 网络 → 评估 → 图表全链；耗时 < 10 min
- 输出：`tests/e2e_smoke.py`

**T7.4 配置 hash + 种子写入每个 result**
- 验收：每个 `05_results/<exp_name>/summary.md` 自动含 git commit / config sha / seed / runtime / GPU
- 输出：`03_active_modules/common/manifest.py` 扩展

---

### 3.10 Codex 派单总览

| Pack | 任务数 | 总工时（估） | 关键风险 |
|---|---|---|---|
| 0 基础设施 | 3 | 3 天 | 无 |
| 1 数据与信道 | 4 | 7 天 | DeepMIMO O1/I3 数据下载阻塞、5G Toolbox license |
| 2 经典 baseline | 4 | 6 天 | SBL 实现可能需手写；CRLB 解析推导仍由人工 |
| 3 T-OMP-Net 骨架 | 4 | 8 天 | Hungarian 梯度路径正确性需人工 review |
| 4 创新性补足 | 3 | 9 天 | IA-AUD gating 稳定性需调参；Codex 输出后人工调整 |
| 5 SOTA 复现 | 2 | 10 天 | **高风险**：无官方代码假设；可能"复现失败"是常态 |
| 6 实验运行 | 3 | 5 天 | 需 GPU 资源 |
| 7 图表与可复现性 | 4 | 4 天 | 无 |
| **合计** | **27** | **52 天** ≈ 10 周 | — |

10 周 Codex 主线 + 人工对 Pack 3-5 关键模块 review + Pack 4 创新性数学正确性把关 + Pack 5 复现失败时的"参照线"叙述写法。

---

### 3.11 Codex prompt 模板（每张任务派单时直接复用）

```
# 任务：T<X.Y> <任务名>

## 背景
本任务隶属于 mmWave ISAC T-OMP-Net 项目，主线设计文档：
`01_design_and_plan/ISAC_DeepUnfolding_TechnicalDesign_v2.3.md`
本任务直接对应 v2.3 中的 <§章节> 或 V2_3_INNOVATION_AND_CODEX_PLAN.md 中的 <Pack>.<Tx.y>。

## 输入规格
（粘贴本文档对应 Tx.y 的输入规格段落）

## 验收标准
（粘贴本文档对应 Tx.y 的验收段落）

## 输出文件位置
（粘贴本文档对应 Tx.y 的输出路径）

## 框架与依赖约定
- Python 3.11 / PyTorch ≥ 2.3 / scipy / numpy / matplotlib / einops / pyyaml
- 不引入 localStorage / 浏览器 API（项目纯仿真）
- 不使用 print；所有日志通过 `logging` 模块
- 所有 dataclass 必须 frozen=True
- 所有随机数使用 `seed_all(seed)` 入口
- 所有 IO 路径使用 `pathlib.Path`，禁止字符串拼接

## 不要做
- 不重写本文档已锁定的接口规范
- 不修改 `90_archive/` 任何文件
- 不假设 GPU 一定可用（检测 fallback CPU）
- 不主动重写 v2.3 大纲或贡献叙述

## 单元测试要求
- 至少 3 个测试用例覆盖核心 forward / IO / 数值边界
- 测试文件位于 `tests/` 同名子目录
- pytest 一键跑通

## 完成后请提交
- 主代码文件
- 单元测试
- 一句话 "what was implemented" / "what was skipped / why" 的 PR 说明
```

---

## 4. v2.2 → v2.3 文档差量清单（写入 v2.3 时的具体修订位置）

| 章节 | 修订内容 | 类别 |
|---|---|---|
| §0 | 加 0.4 v2.3 vs v2.2 表（A4/A5/A6） | 新增 |
| §1.2 | C2/C3/C4 改写为 5 贡献版本（C5 新增） | 改写 |
| §1 段落 4 | 用 V2_2_DIRECTION_REVALIDATION.md §3.3 的新措辞 | 改写 |
| §2.4 | 用 V2_2_DIRECTION_REVALIDATION.md §2 的实证表替换占位 | 替换 |
| §4.0 | 新增"与 MOMPnet/DDA-Net/Unified Tensor ISAC 的差异化论证" | 新增 |
| §4.3a | 新增 IA-AUD 自适应深度 | 新增 |
| §4.4a | 新增 HIR-JL 联合损失扩展 | 新增 |
| §4.5 | 加 MAML 子节 | 扩 |
| §5.1.2 | 新增 Lemma 2 深度-可辨识性权衡 | 新增 |
| §6.5.14 | 新增 HIR-JL 鲁棒性实验 | 新增 |
| §6.5.15 | 新增 IA-AUD 自适应深度 FLOPs 对比 | 新增 |
| §6.7.x | 扩 FSMA few-shot 对比 | 扩 |
| §4.1 投稿目标 | 改用本文件 §1.4 顺序 | 替换 |
| 附录 D | Lemma 1 完整证明 | 落字 |
| 附录 E | Lemma 2 完整证明 | 新增 |

---

## 5. 本周（2026-06-25 起）落地动作（替换 V2_2_DIRECTION_REVALIDATION.md §7）

| # | 动作 | 人/Codex | 验收 |
|---|---|---|---|
| 1 | 起草 `ISAC_DeepUnfolding_TechnicalDesign_v2.3.md`，应用本文件 §4 全部差量 | 人工 | 文件落盘 + 自洽阅读 |
| 2 | 8 篇核心文献 BibTeX + 一页阅读笔记落 `02_literature_and_refs/literature_2024_2025/` | 人工 | 8 个 .md |
| 3 | 启动 DeepMIMO O1/I3 下载 + `license('test','5G_Toolbox')` 测试 | 人工 | audit 通过/降级方案确定 |
| 4 | 启动 Codex Pack 0（T0.1 / T0.2 / T0.3） | Codex | 验收清单全过 |
| 5 | 启动 Codex Pack 1（T1.1 / T1.2 / T1.3） | Codex | Set A + CDL + DeepMIMO 三套 Channel 出第一帧数据 |
| 6 | Codex Pack 2 中 T2.1 + T2.3 + T2.4 启动（LS、Tensor-OMP、CRLB） | Codex | 三个 baseline 在 Set A 上跑出结果 |
| 7 | 完成本评估 + v2.3 patch 文档 git commit；tag `v2.3-revalidation-2026-06` | 人工 | git log |

---

## 6. 总结

- **期刊定位**：DSP 剔除（中科院 3 区），主路径改为 **IEEE Sensors → IEEE TVT → IEEE Systems → Signal Processing → IEEE IoT-J**。
- **创新补足三件套**：A4 自适应深度耦合 Kruskal、A5 硬件失真鲁棒训练、A6 MAML 元学习跨场景；每项都有独占点 + Codex 可实现 + 论文位置已锁定。
- **Codex 任务包**：27 个任务分 8 个 pack，10 周可完成；高风险项是 Pack 5 SOTA 复现（备案：报告值参照线）+ Pack 4 IA-AUD gating 稳定性（人工调参 fallback）。
- **本周落地**：v2.3 文档起草 + 8 篇文献入库 + 阻塞解锁 + Codex Pack 0/1/2 启动。
