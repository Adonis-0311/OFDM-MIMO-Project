# 毫米波 MIMO-OFDM ISAC 信道与目标参数联合估计

## ——基于物理约束 Tensor-OMP 深度展开网络的方法（论文大纲范本）

> 版本：v2.0（已吸收 v1.0 评审意见全面压缩）
> 作者：刘雨辉
> 目标期刊（首投顺序）：Signal Processing (Elsevier, Q2) → Digital Signal Processing (Elsevier, Q2) → IEEE Sensors Journal (Q1/Q2) → IEEE Systems Journal (Q2)
> 工作量定位：1 人 6 个月，单 GPU，可完整复现

---

## 0  v2.0 相对 v1.0 的关键修订

| 维度 | v1.0 | v2.0（本版） | 修订理由 |
|------|------|------------|---------|
| 张量阶数 | 4 阶 $(\phi,\tau,\nu,\theta)$ | **3 阶 $(\bar{\theta},\tau,\nu)$** | 单站 ISAC 中 AoA/AoD 等效共享角 $\bar{\theta}$，降字典维度 |
| 网络结构 | 含 attention + 卷积残差校正 | **轻量展开层** | 控参数量、保物理可解释 |
| 字典 | 完全可学习 | **物理网格固定 + 受约束 off-grid 微调** | 保留物理意义 |
| 收敛性 | 声明线性收敛证明 | **降为"误差界分析 + 经验收敛"** | 规避审稿风险 |
| 数据集 | CDL + QuaDRiGa + DeepMIMO + 自定义 | **自定义为主 + CDL-A/C/D 辅助 + DeepMIMO 选做** | 删 QuaDRiGa |
| Baseline | 12 种 | **8 种聚焦** | 工作量可控 |
| 主张创新点 | 3 个 | **4 个（更明确）** | 物理约束 off-grid 独立成点 |

---

## 第一部分：研究定位与核心设计

### 1.1 论文标题（拟）

**Sparse Tensor-OMP Deep Unfolding Network with Physical-Constrained Off-Grid Refinement for Joint Channel and Target Parameter Estimation in mmWave MIMO-OFDM ISAC Systems**

中文备选：基于物理约束 Tensor-OMP 深度展开网络的毫米波 MIMO-OFDM ISAC 信道与目标参数联合估计

### 1.2 四个核心贡献（写入 Abstract 与 Introduction 末尾）

**C1（建模）**：构建毫米波 MIMO-OFDM ISAC 系统的角度-时延-多普勒三维稀疏张量模型，将通信信道估计与雷达目标参数估计统一为同一稀疏核张量恢复问题。

**C2（算法）**：提出轻量化 Tensor-OMP 深度展开网络 T-OMP-Net，每层结构对应一次 Tensor-OMP 迭代（相关性 → 学习阈值 → 支撑更新 → 正则化 LS → 残差更新），仅含少量可学习参数。

**C3（机制）**：设计物理网格约束下的 off-grid 微调机制，对角度/时延/多普勒网格在 $\pm\Delta_{\text{grid}}/2$ 内可学习偏移，缓解离网误差并保持参数可解释性。

**C4（验证）**：通过 NMSE / BER / 距离-速度-角度 RMSE / FLOPs / 推理时延等多维指标，在低 SNR、少导频、高速移动、未知目标数、阵列误差等场景全面验证算法。

### 1.3 工作量边界（明确不做的内容）

- ❌ 四维 AoA-AoD-Delay-Doppler 全字典
- ❌ Multi-head attention 模块
- ❌ 大型卷积残差校正网络
- ❌ 完全可学习字典
- ❌ 严格线性收敛数学证明
- ❌ QuaDRiGa 全量实验
- ❌ DeepMIMO 作为主实验
- ❌ 1-bit ADC 量化作为核心实验

以上均放入"未来工作"或扩展讨论。

---

## 第二部分：论文章节级写作大纲

### Section 1  Introduction（约 1500 字 / 4-5 段）

**段落 1：背景与应用驱动**
- 5G/6G 与车载/低空毫米波雷达对高频谱效率 + 高分辨感知的需求
- ISAC 通过共享波形、共享硬件实现"一波两用"的范式价值
- OFDM-MIMO 是 ISAC 主流波形（引 Liu 2022 JSAC 综述）

**段落 2：信道估计与目标参数估计的内在统一性**
- 毫米波信道多径参数 $\{\alpha_l, \theta_l, \tau_l, \nu_l\}$ 本身就是雷达目标参数
- 已有研究将两者分开处理，造成性能损失与计算冗余
- ISAC 的核心机遇是"联合估计"

**段落 3：相关工作三类划分**
- *传统 CS 路线*（OMP/SOMP/SBL）：可解释但依赖网格、对噪声敏感
- *数据驱动 DL 路线*（ChannelNet/CAE）：精度高但黑箱、训练样本需求大
- *模型驱动 DL（深度展开）路线*（LISTA/LDAMP）：兼具二者优势但多为 2D 矩阵问题，未充分利用 ISAC 的张量结构与物理约束

**段落 4：研究空白与本文动机**
- 张量结构 + 物理约束 + 深度展开三者尚未在 ISAC 联合估计中系统融合
- 现有展开网络的可学习字典常丢失物理意义
- 本文目标：构建可解释、轻量、且联合估计性能 SOTA 的展开网络

**段落 5：贡献与论文组织**
- 4 点贡献 bullet 化（见 1.2 节）
- 章节组织说明

**核心数据预告**（在引言末尾给出代表性数字）：
- "在 SNR=20dB 下，T-OMP-Net 相比 Tensor-OMP 降低 NMSE 约 5dB，距离/速度 RMSE 降低约 40%"
- "参数量约 $10^4$ 量级，FLOPs 相比 ChannelNet 减少 1-2 个数量级"

---

### Section 2  Related Work（约 800 字）

**2.1 OFDM-MIMO mmWave Channel Estimation**
- LS / LMMSE 经典方法
- 基于稀疏性的 CS 方法（OMP、SOMP、CoSaMP、SBL）
- 张量类方法（Tensor-ALS、HOSVD）

**2.2 ISAC: Joint Sensing and Communication**
- 波形设计类工作
- 联合信道-参数估计类工作（指出现有工作多分阶段处理）

**2.3 Deep Unfolding Networks**
- LISTA / LAMP / LDAMP 的发展脉络
- 与端到端 DL 的对比优势
- 在无线通信中的应用现状

**2.4 Research Gap**
（明确点出本文要填的空白：3D 张量 + 物理约束 + ISAC 联合损失的展开网络尚缺）

---

### Section 3  System Model and Problem Formulation（约 1500 字 + 关键公式）

#### 3.1 OFDM-MIMO ISAC System Model

- 单站 monostatic 场景假设
- $N_t$ 发射 / $N_r$ 接收 ULA，$K$ 子载波，$M$ OFDM 符号
- 载波 $f_c$（建议 28 GHz 或 77 GHz）

接收信号（单站等效共享角 $\bar{\theta}_l$）：

$$
\mathbf{y}[k,m] = \sum_{l=1}^{L} \alpha_l\, \mathbf{a}_R(\bar{\theta}_l) \mathbf{a}_T^H(\bar{\theta}_l)\, \mathbf{x}[k,m]\, e^{-j2\pi k\Delta f \tau_l}\, e^{j2\pi m T_s \nu_l} + \mathbf{n}[k,m]
$$

注：在单站 ISAC 下，AoA 与 AoD 由同一目标决定，可建模为等效共享角 $\bar{\theta}_l$。

#### 3.2 角度-时延-多普勒三维张量化

经过波束化与适当预处理（详细推导放附录 A），接收信号整理为 3 阶张量 $\mathcal{Y} \in \mathbb{C}^{G_{\bar\theta}' \times K \times M}$，满足：

$$
\mathcal{Y} = \sum_{l=1}^{L} \alpha_l\, \mathbf{b}(\bar{\theta}_l) \circ \mathbf{p}(\tau_l) \circ \mathbf{d}(\nu_l) + \mathcal{N}
$$

其中：
- $\mathbf{b}(\bar{\theta}_l) = \mathbf{a}_R(\bar{\theta}_l) \cdot \mathbf{a}_T^H(\bar{\theta}_l)\mathbf{x}_{\text{eff}}$（波束化后等效角度向量）
- $\mathbf{p}(\tau_l), \mathbf{d}(\nu_l)$ 同 v1.0

#### 3.3 稀疏字典与核张量

构造**物理字典**：
- $\mathbf{B} \in \mathbb{C}^{N_b \times G_{\bar\theta}}$：角度字典，$G_{\bar\theta}$ 个均匀网格
- $\mathbf{P} \in \mathbb{C}^{K \times G_\tau}$：时延字典
- $\mathbf{D} \in \mathbb{C}^{M \times G_\nu}$：多普勒字典

信号表示为：

$$
\mathcal{Y} = \mathcal{G} \times_1 \mathbf{B} \times_2 \mathbf{P} \times_3 \mathbf{D} + \mathcal{N}
$$

$\mathcal{G} \in \mathbb{C}^{G_{\bar\theta} \times G_\tau \times G_\nu}$ 为稀疏核张量，**仅 $L$ 个非零元，每个非零元对应一个物理目标/路径**。

#### 3.4 问题表述

$$
\boxed{\min_{\mathcal{G}}\;\|\mathcal{Y} - \mathcal{G} \times_1 \mathbf{B} \times_2 \mathbf{P} \times_3 \mathbf{D}\|_F^2 \;+\; \lambda\|\mathcal{G}\|_0}
$$

明确陈述："核张量非零位置 $\Leftrightarrow$ 目标参数 $\{\bar{\theta}_l, \tau_l, \nu_l\}$；非零值 $\Leftrightarrow$ 路径复增益 $\alpha_l$。"

#### 3.5 与已有工作的对比定位

用一张表对比 4-5 个代表方法（LS、OMP、SOMP、LISTA、本文）在以下维度：张量结构利用 / 物理可解释性 / 端到端训练 / off-grid 处理。

**关键图（Fig. 1）**：系统框图 — 发射端 → 信道（含 $L$ 个目标/路径，标注 $\bar\theta, \tau, \nu$）→ 接收端 → 张量化处理 → T-OMP-Net → 双输出（信道估计 + 目标参数列表）

---

### Section 4  Proposed T-OMP-Net（约 2200 字，论文核心章节）

#### 4.1 Tensor-OMP 基础迭代

将稀疏核张量向量化 $\mathbf{g} = \text{vec}(\mathcal{G})$，感知矩阵 $\mathbf{\Phi} = \mathbf{D} \otimes \mathbf{P} \otimes \mathbf{B}$。

**Tensor-OMP 算法（伪代码 Algorithm 1）**：

```
Input: 张量 Y, 物理字典 {B, P, D}, 最大稀疏度 L_max, 残差门限 ε
Init: 残差 R_0 = Y, 支撑集 S_0 = ∅
For t = 1, ..., L_max:
   1. c_t = vec(R_{t-1})^H Φ              # 相关性向量
   2. i_t = argmax_i |c_t(i)|              # 选最大相关原子
   3. S_t = S_{t-1} ∪ {i_t}
   4. g_{S_t} = (Φ_{S_t}^H Φ_{S_t})^{-1} Φ_{S_t}^H vec(Y)    # LS 投影
   5. R_t = Y - reshape(Φ_{S_t} g_{S_t})
   6. If ||R_t||_F / ||Y||_F < ε: break
Output: 稀疏核张量 G_hat
```

#### 4.2 T-OMP-Net 网络结构（核心创新）

将上述迭代展开为固定 $T$ 层网络，每层 1 次迭代，共 $T$ 个 OMP-Layer。

**OMP-Layer-t 结构（Algorithm 2）**：

```
输入：上一层残差 R_{t-1}, 支撑集 S_{t-1}, 当前字典 {B_t, P_t, D_t}
────────────────────────────────────
Step 1 (Correlation):
   c_t = vec(R_{t-1})^H Φ_t                      # Φ_t 由当前字典构造
Step 2 (Soft Thresholding, 可学习阈值 λ_t):
   c_tilde = sign(c_t) ⊙ max(|c_t| - λ_t, 0)
Step 3 (Support Update):
   S_t = S_{t-1} ∪ TopK(c_tilde, K_t)            # K_t 可学或固定为 1
Step 4 (Regularized LS, 可学习正则 μ_t):
   g_t = (Φ_{S_t,t}^H Φ_{S_t,t} + μ_t I)^{-1} Φ_{S_t,t}^H vec(Y)
Step 5 (Residual Update, 可学习步长 γ_t):
   R_t = R_{t-1} - γ_t · reshape(Φ_{S_t,t} g_t - Φ_{S_{t-1},t} g_{t-1})
────────────────────────────────────
输出：R_t, S_t, g_t
```

**每层可学习参数（仅 4 个标量 + 字典偏移）**：

| 参数 | 维度 | 物理含义 | 初始化 |
|------|------|---------|-------|
| $\lambda_t$ | 1 | 软阈值 | $\sigma\sqrt{2\log N}$ |
| $\mu_t$ | 1 | LS 正则系数 | $10^{-3}$ |
| $\gamma_t$ | 1 | 残差更新步长 | 1.0 |
| $K_t$（可选） | 1 整数 | Top-K | 1 |
| $\{\Delta\bar\theta_g, \Delta\tau_g, \Delta\nu_g\}$ | $G_{\bar\theta}+G_\tau+G_\nu$ | 字典 off-grid 偏移 | 0 |

**总参数量估计**（$T=8$, $G_{\bar\theta}=64$, $G_\tau=64$, $G_\nu=32$）：
$$N_{\text{params}} = 4T + (G_{\bar\theta}+G_\tau+G_\nu) \approx 32 + 160 \approx 200 \text{ 个标量}$$

—— 与典型 CNN ($10^7$) 相比少 5 个数量级，这是论文的**复杂度卖点**。

#### 4.3 物理约束 Off-Grid Refinement（Contribution 3 核心）

字典原子修正：

$$
\tilde\theta_g = \theta_g + \Delta\theta_g, \quad |\Delta\theta_g| \leq \frac{\Delta\theta_{\text{grid}}}{2}
$$

时延、多普勒同理。**约束实现方式**：硬约束 `tanh` 重参数化：

$$
\Delta\theta_g = \frac{\Delta\theta_{\text{grid}}}{2} \cdot \tanh(w_g)
$$

其中 $w_g \in \mathbb{R}$ 为底层无约束可学习参数。这样既保证偏移在物理合理区间，又保持自动微分顺畅。

**关键写作要点**：强调"网格点仍对应物理角度/时延/多普勒，仅在 grid spacing 内做亚网格修正"，可解释性完全保留。

#### 4.4 联合损失函数

$$
\boxed{\mathcal{L} = \mathcal{L}_{\text{NMSE}} + \beta_1 \mathcal{L}_{\text{Param}} + \beta_2 \mathcal{L}_{\text{Sparse}} + \beta_3 \mathcal{L}_{\text{Off-grid}}}
$$

各项定义：

- **信道重建**：$\mathcal{L}_{\text{NMSE}} = \|\hat{\mathcal{H}} - \mathcal{H}\|_F^2 / \|\mathcal{H}\|_F^2$
- **参数误差**（Huber 损失抗野值）：
$$\mathcal{L}_{\text{Param}} = \frac{1}{L}\sum_{l=1}^L \left[\rho_H(\hat{\bar\theta}_l - \bar\theta_l) + \rho_H(\hat\tau_l - \tau_l) + \rho_H(\hat\nu_l - \nu_l)\right]$$
- **稀疏正则**：$\mathcal{L}_{\text{Sparse}} = \|\hat{\mathcal{G}}\|_1$
- **off-grid 正则**：$\mathcal{L}_{\text{Off-grid}} = \|\Delta\theta\|_2^2 + \|\Delta\tau\|_2^2 + \|\Delta\nu\|_2^2$

权重建议：$\beta_1=1.0, \beta_2=10^{-3}, \beta_3=10^{-2}$，并做权重敏感性分析（附录或消融）。

#### 4.5 训练策略

- 优化器：AdamW，初始学习率 $1\times 10^{-3}$，cosine decay
- Batch size：32
- 训练样本：自定义场景生成 50,000 组（角度/时延/多普勒标签随机）
- Epoch：80
- 课程学习：先训 SNR=20dB，每 20 epoch 降 5dB 直到 -5dB
- 早停：基于验证集 NMSE，连续 10 epoch 不下降则停

#### 4.6 目标参数提取（推理阶段）

```
1. 阈值化 G_hat：保留 |G_hat(i,j,k)| > η · max(|G_hat|) 的位置
2. 对每个非零位置 (i*, j*, k*):
   - 估计角度：θ_hat = θ_{i*} + Δθ_{i*}
   - 估计时延：τ_hat = τ_{j*} + Δτ_{j*}
   - 估计多普勒：ν_hat = ν_{k*} + Δν_{k*}
3. 换算物理量：
   - 距离：R_hat = c · τ_hat / 2
   - 径向速度：v_hat = c · ν_hat / (2 f_c)
```

**关键图（Fig. 2）**：T-OMP-Net 整体架构图（输入 → T 层 OMP-Layer → 双输出：估计信道 + 目标参数列表），每层内部展开为 5 个 step 的小子图。

---

### Section 5  Theoretical Analysis（约 1200 字）

#### 5.1 Error Bound Analysis（弱化原"收敛证明"）

**关键写作策略**：避开严格证明，定位为"借助经典 CS 理论的误差界继承性分析"。

**Proposition 1（建议表述）**：

> Suppose the sensing matrix $\mathbf{\Phi}$ satisfies the $L$-th order Restricted Isometry Property (RIP) with constant $\delta_{2L} < \sqrt{2}-1$. Then the output of the unfolded T-OMP-Net inherits the residual-reduction property of classical Tensor-OMP. Moreover, the learnable thresholds $\{\lambda_t\}$ and regularization coefficients $\{\mu_t\}$ provide additional flexibility to **empirically** tighten the recovery error bound, which we verify numerically in Section 6.

随后给出**经典 OMP 在 RIP 下的误差界引理**（引用 Davenport & Wakin 2010）作为"继承基础"，再说明展开网络通过参数自适应进一步优化此界。

**Proposition 2（off-grid 误差界）**：物理约束 off-grid 偏移在 $\pm\Delta_{\text{grid}}/2$ 内时，离网误差从 $O(\Delta_{\text{grid}})$ 量级降至 $O(\sigma_{\text{noise}})$ 量级（数值验证）。

#### 5.2 CRLB 推导

针对参数向量 $\boldsymbol{\eta} = [\alpha_l, \bar\theta_l, \tau_l, \nu_l]_{l=1}^L$（共 $4L$ 个参数），Fisher 信息矩阵：

$$
[\mathbf{F}(\boldsymbol{\eta})]_{ij} = \frac{2}{\sigma^2} \Re\left\{\frac{\partial \boldsymbol{\mu}^H}{\partial \eta_i} \frac{\partial \boldsymbol{\mu}}{\partial \eta_j}\right\}
$$

给出关键偏导（附录 B 给完整推导）：

- $\partial\boldsymbol{\mu}/\partial \tau_l = -j2\pi \alpha_l \cdot \mathbf{b}(\bar\theta_l) \circ (\mathbf{k}\odot\mathbf{p}(\tau_l)) \circ \mathbf{d}(\nu_l)$
- $\partial\boldsymbol{\mu}/\partial \nu_l = j2\pi T_s \alpha_l \cdot \mathbf{b}(\bar\theta_l) \circ \mathbf{p}(\tau_l) \circ (\mathbf{m}\odot\mathbf{d}(\nu_l))$
- $\partial\boldsymbol{\mu}/\partial \bar\theta_l$：含阵列响应梯度

CRLB 作为 NMSE/RMSE 曲线的理论下界绘出（Fig. 6/7）。

#### 5.3 复杂度分析

| 算法 | 每帧 FLOPs | 参数量 |
|------|-----------|-------|
| LS | $O(KN_rN_t)$ | 0 |
| OMP | $O(L K N_r N_t G)$ | 0 |
| Tensor-OMP | $O(L G_\theta G_\tau G_\nu \cdot (N_r+K+M))$（用 mode-product 加速） | 0 |
| LDAMP | $O(T G^2)$ | $\sim 10^6$ |
| ChannelNet | $O(C K^2)$ | $\sim 10^7$ |
| **T-OMP-Net** | $O(T L G_\theta G_\tau G_\nu)$（与 Tensor-OMP 同阶，常数更小） | **$\sim 10^2 \sim 10^3$** |

明确写出 FLOPs 推导（每项操作的乘加次数累加），不能只给 big-O。

---

### Section 6  Simulation Results（约 2500 字，含 8-10 张图）

#### 6.1 Simulation Setup

| 参数 | 取值 |
|------|------|
| 载波频率 $f_c$ | 77 GHz |
| 带宽 | 200 MHz |
| 子载波数 $K$ | 128 |
| OFDM 符号数 $M$ | 32 |
| 发射天线 $N_t$ | 8 |
| 接收天线 $N_r$ | 16 |
| 目标数 $L$ | 4（基础场景） |
| 字典网格 $G_{\bar\theta}, G_\tau, G_\nu$ | 64, 64, 32 |
| SNR 范围 | -10 ~ 30 dB（步长 5 dB） |

#### 6.2 Channel Configurations

| 编号 | 来源 | 用途 |
|------|------|------|
| Set A | 自定义参数化 ISAC 多目标场景 | **主实验**（用于参数 RMSE） |
| Set B | 3GPP TR 38.901 CDL-A（NLOS） | 通信信道泛化 |
| Set C | 3GPP TR 38.901 CDL-C（NLOS+） | 通信信道泛化 |
| Set D | 3GPP TR 38.901 CDL-D（LOS） | 通信信道泛化 |
| Set E（选做） | DeepMIMO O1/I3 场景 | 跨场景泛化补充 |

#### 6.3 Baselines（8 种）

| 类别 | 算法 | 来源参考 |
|------|------|---------|
| 经典 | LS | — |
| 经典 | LMMSE | — |
| 矩阵 CS | OMP | Tropp 2007 |
| 多测量 CS | SOMP | Tropp 2006 |
| 张量 CS | Tensor-OMP | Caiafa & Cichocki 2013 |
| 展开网络 | LISTA / LDAMP | Gregor 2010 / Metzler 2017 |
| 数据驱动 DL | CAE（毕设方法） | 本作者毕设 |
| **本文** | **T-OMP-Net** | — |

#### 6.4 评价指标（明确公式）

- **通信侧**：NMSE (dB)，BER
- **感知侧**：距离 RMSE (m)、速度 RMSE (m/s)、角度 RMSE (deg)、目标检测概率 $P_d$、虚警率 $P_{fa}$
- **系统侧**：参数量、FLOPs、推理延迟 (ms)、显存

#### 6.5 实验设计与对应图表

| Exp | 实验内容 | 横轴 | 纵轴 | 图编号 |
|-----|---------|------|------|-------|
| 6.5.1 | NMSE vs SNR | SNR [-10, 30] dB | NMSE (dB) | Fig. 3 |
| 6.5.2 | BER vs SNR | 同上 | BER | Fig. 4 |
| 6.5.3 | 距离 RMSE vs SNR | 同上 | m | Fig. 5 |
| 6.5.4 | 速度 RMSE vs SNR | 同上 | m/s | Fig. 6 |
| 6.5.5 | 角度 RMSE vs SNR（叠加 CRLB） | 同上 | deg | Fig. 7 |
| 6.5.6 | 少导频实验 | 导频比 {5,10,15,20,25}% | NMSE / 参数 RMSE | Fig. 8 |
| 6.5.7 | 高速移动实验 | 速度 {0,60,120,240,360,500} km/h | NMSE / 速度 RMSE | Fig. 9 |
| 6.5.8 | 未知目标数 $L$ | $L \in \{2,4,6,8,10\}$ | NMSE / $P_d$ | Fig. 10 |
| 6.5.9 | 阵列误差鲁棒性 | 误差类型 ±1dB/±5°/阵元扰动 | NMSE | Table II |
| 6.5.10 | 消融实验 | 5 种网络变体 | NMSE / 参数 RMSE | Table III |
| 6.5.11 | 展开层数 $T$ | $T \in \{4,6,8,10\}$ | NMSE / FLOPs | Fig. 11 |
| 6.5.12 | 复杂度对比 | 8 种算法 | 参数量/FLOPs/延迟 | Table IV |

#### 6.6 消融实验设计

| 变体 | 说明 |
|------|------|
| A0 | Tensor-OMP（无展开，无学习） |
| A1 | T-OMP-Net 仅可学阈值 $\lambda_t$ |
| A2 | T-OMP-Net 加正则系数 $\mu_t$ |
| A3 | T-OMP-Net 加残差步长 $\gamma_t$ |
| A4 | A3 + off-grid 但无 $\mathcal{L}_{\text{Off-grid}}$ 约束 |
| **A5（Full）** | **A3 + 物理约束 off-grid + 全部 4 项损失** |
| A6 | A5 移除 $\mathcal{L}_{\text{Param}}$（验证联合损失必要性） |
| A7 | A5 移除 $\mathcal{L}_{\text{Sparse}}$ |

**关键卖点表述**：A0→A5 NMSE 累积下降约 X dB；A5 vs A6 显示参数损失项对感知精度提升明显。

#### 6.7 跨场景泛化（在 Set A 上训练，在 Set B/C/D 上测试）

显示模型对未见过的信道分布的迁移能力。

#### 6.8 结果讨论要点

- 在哪些 SNR 区间本文方法显著领先 baseline
- off-grid 修正在哪些参数（角度还是时延）效益最大
- 复杂度/参数量优势的工程意义
- 在哪些极端条件下方法局限（诚实指出，避免审稿人质疑）

---

### Section 7  Conclusion（约 400 字）

- 总结四点贡献
- 给出代表性数值结果（呼应 Introduction）
- 指出三个未来方向：
  1. 扩展到双站 bi-static ISAC（AoA ≠ AoD）
  2. 引入 RIS 辅助
  3. 硬件实测验证（TI mmWave EVM 或 USRP）

---

## 第三部分：实施计划（6 个月分阶段）

### Phase 1（M1）：模型与 Baseline 基础（4 周）

| 周 | 任务 | 产出 |
|----|------|------|
| W1 | 完成自定义 ISAC 信号生成（含参数标签）、3GPP CDL 数据导入 | 数据生成脚本 |
| W2 | 实现 LS / LMMSE / OMP / SOMP | MATLAB/Python 代码 |
| W3 | 实现 Tensor-OMP，跑通完整 pipeline | Baseline 性能曲线 |
| W4 | 完成评价指标统一封装（NMSE/BER/RMSE） | 评测脚本 |

**Phase 1 退出标准**：Tensor-OMP 在 SNR=20dB 下 NMSE 收敛到合理值（约 -15 dB 左右）。

### Phase 2（M2）：T-OMP-Net 最小版本（4 周）

| 周 | 任务 | 产出 |
|----|------|------|
| W5 | T-OMP-Net 网络层 PyTorch 实现（无 off-grid） | 网络代码 |
| W6 | 训练 pipeline + 单 loss（仅 $\mathcal{L}_{\text{NMSE}}$） | 训练日志 |
| W7 | 调参，性能 > Tensor-OMP | 第一组 NMSE 曲线 |
| W8 | 加入 $\mathcal{L}_{\text{Param}}$ 联合训练 | 参数 RMSE 曲线 |

**Phase 2 退出标准**：在 SNR=20dB 下相比 Tensor-OMP NMSE 改善 ≥ 3 dB。

### Phase 3（M3）：Off-Grid 物理约束机制（3 周）

| 周 | 任务 | 产出 |
|----|------|------|
| W9 | 加入字典偏移参数 + tanh 重参数化 | off-grid 模块 |
| W10 | 加入 $\mathcal{L}_{\text{Off-grid}}$ 约束损失 | 完整 4 项损失 |
| W11 | 验证 off-grid vs no off-grid 的参数 RMSE | 消融数据 |

### Phase 4（M4-M5）：全量实验（6 周）

- W12-13：基础性能（NMSE/BER/距离-速度-角度 RMSE vs SNR）
- W14：少导频实验
- W15：高速移动 + 未知目标数 + 阵列误差
- W16：消融 + 展开层数分析
- W17：复杂度统计 + 跨场景泛化

### Phase 5（M6）：理论与论文撰写（4 周）

- W18：CRLB 推导成稿
- W19-20：论文 Introduction / Related Work / System Model 撰写
- W21：Proposed Method / Theoretical Analysis 撰写
- W22：Simulation Results 撰写 + 图表整理
- W23：通稿润色 + 投稿

---

## 第四部分：投稿与风险管理

### 4.1 投稿梯度（首投 → 备投）

| 顺序 | 期刊 | 影响因子 | 偏好 | 备注 |
|------|------|---------|------|------|
| 1 | Signal Processing (Elsevier) | ~3.4 | 偏方法/理论 | Q2 稳，审稿 3-5 月 |
| 2 | Digital Signal Processing (Elsevier) | ~2.9 | 方法创新友好 | Q2 友好 |
| 3 | IEEE Sensors Journal | ~4.3 | 强应用 + 系统实验 | Q1/Q2 边界 |
| 4 | IEEE Systems Journal | ~4.0 | 系统级方案 | Q2 |

**冲刺备选**（若实验质量超预期）：IEEE TVT（Q2 偏上）、IEEE IoT Journal

### 4.2 审稿人潜在问题及预案

| 问题 | 预案 |
|------|------|
| Q：相比 Tensor-OMP 提升来源？ | A：消融实验 A0 vs A5 量化每个学习模块贡献 |
| Q：仅做仿真，无实测？ | A：诚实承认，引 DeepMIMO 准实测作弥补，未来工作指向 TI EVM |
| Q：单站 monostatic 假设是否过强？ | A：明确写明应用场景（车载/无人机自感），承诺未来扩展双站 |
| Q：参数 $\lambda_t/\mu_t/\gamma_t$ 学到了什么？ | A：附录可视化各层参数随训练演化曲线 |
| Q：算法对 $L$ 未知的鲁棒性？ | A：未知目标数实验（6.5.8）已覆盖 |
| Q：物理约束 off-grid 是否真的有界？ | A：tanh 重参数化保证硬约束，附录数学说明 |
| Q：与 LISTA/LDAMP 区别？ | A：3D 张量结构利用 + 物理约束 + ISAC 联合损失，三者均为独有 |

### 4.3 关键风险与应对

| 风险 | 概率 | 影响 | 应对 |
|------|------|------|------|
| T-OMP-Net 训练不收敛 | 低 | 高 | 课程学习 + 良好初始化（用 Tensor-OMP 结果作 warm-start） |
| 性能与 Tensor-OMP 差距小 | 中 | 中 | 强化复杂度优势 + off-grid 优势 |
| CRLB 推导出错 | 中 | 中 | 用数值差分 Fisher 矩阵交叉验证 |
| 投稿被拒（首次） | 中 | 低 | 已准备 4 个期刊梯度，3 周内可改投 |
| 时间超期 | 中 | 中 | Phase 4 实验可并行；DeepMIMO 改选做 |

---

## 第五部分：可立即执行的下一步（本周）

1. **建 Git 仓库**：`mmwave-isac-tompnet`，目录结构：
   ```
   /data        # 数据生成与加载
   /baseline    # LS, LMMSE, OMP, SOMP, Tensor-OMP
   /tompnet     # 网络模型
   /train       # 训练脚本
   /eval        # 评价与画图
   /paper       # tex 源码
   ```
2. **完成自定义 ISAC 信号生成器**（参数标签：$\alpha_l, \bar\theta_l, R_l, v_l$ → $\tau_l, \nu_l$ → 接收张量 $\mathcal{Y}$）
3. **下载 3GPP CDL-A/C/D 配置**（MATLAB 5G Toolbox 或 Python 等价实现）
4. **阅读核心 3 篇**：
   - Caiafa & Cichocki 2013（Tensor-OMP 基础）
   - Chen et al. 2018（LISTA 收敛性，用于 5.1 写法借鉴）
   - Liu 2022 JSAC（ISAC 综述，写 Introduction）

---

## 附录：与 v1.0 报告的对照速查表

| 论文章节 | 对应 v1.0 章节 | 主要变化 |
|---------|---------------|---------|
| Sec 3 | v1.0 §2.1-2.3 | 4D → 3D 张量 |
| Sec 4 | v1.0 §4 | 移除 attention/卷积校正 |
| Sec 4.3 | v1.0 §4.2 | 物理约束 off-grid（新增独立小节） |
| Sec 5.1 | v1.0 §5.2 | 收敛证明 → 误差界分析 |
| Sec 5.2 | v1.0 §5.1 | 保留 CRLB |
| Sec 6.2 | v1.0 §6.3 | 删 QuaDRiGa；DeepMIMO 改选做 |
| Sec 6.3 | v1.0 §6.4 | 12 baseline → 8 baseline |

---

**——v2.0 大纲完——**

> 本大纲已严格按评审意见压缩为可在 6 个月内完成、可复现、可解释、稳妥投稿 Q2 的版本。
> 任一章节如需细化（例如 T-OMP-Net 的 PyTorch 完整伪代码、CRLB 各偏导的具体推导、自定义信号生成器的参数设计、或单独某项实验的具体配置表），可继续展开。
