# 毫米波 MIMO-OFDM ISAC 信道与目标参数联合估计

## ——基于物理约束 Tensor-OMP 深度展开网络的方法（论文大纲范本）

> 版本：v2.1（基于 v2.0 的 6 项技术修订，其余结构保留）
> 作者：刘雨辉
> 目标期刊（首投顺序）：Signal Processing (Elsevier, Q2) → Digital Signal Processing (Elsevier, Q2) → IEEE Sensors Journal (Q1/Q2) → IEEE Systems Journal (Q2)
> 工作量定位：1 人 6 个月，单 GPU，可完整复现

---

## 0  v2.0 相对 v1.0 的关键修订

| 维度 | v1.0 | v2.0 | 修订理由 |
|------|------|------|---------|
| 张量阶数 | 4 阶 $(\phi,\tau,\nu,\theta)$ | **3 阶 $(\bar{\theta},\tau,\nu)$** | 单站 ISAC 中 AoA/AoD 等效共享角 $\bar{\theta}$，降字典维度 |
| 网络结构 | 含 attention + 卷积残差校正 | **轻量展开层** | 控参数量、保物理可解释 |
| 字典 | 完全可学习 | **物理网格固定 + 受约束 off-grid 微调** | 保留物理意义 |
| 收敛性 | 声明线性收敛证明 | **降为"误差界分析 + 经验收敛"** | 规避审稿风险 |
| 数据集 | CDL + QuaDRiGa + DeepMIMO + 自定义 | **自定义为主 + CDL-A/C/D 辅助 + DeepMIMO 选做** | 删 QuaDRiGa |
| Baseline | 12 种 | **8 种聚焦** | 工作量可控 |
| 主张创新点 | 3 个 | **4 个（更明确）** | 物理约束 off-grid 独立成点 |

---

## 0.1  v2.1 相对 v2.0 的技术修订（6 项，本版唯一变更）

| 编号 | 修订位置 | v2.0 状态 | v2.1 修订 |
|------|---------|----------|----------|
| **R1** | §3.1-3.3 | "等效共享角 $\bar\theta$" 含糊 | **严谨推导**：正交波形发射 → MIMO 虚拟阵列 → 3 阶 CP 张量 |
| **R2** | §4.2 | 未交代 argmax/TopK 不可导的训练处理 | 新增 §4.2.1 **支撑集选择训练策略**（Teacher-forcing → Gumbel-Softmax → STE → Hard） |
| **R3** | §4.4 | $\mathcal{L}_{\text{Param}}$ 按下标对齐，未处理排列歧义 | 新增 §4.4.1 **Hungarian 最优配对** + 虚警/漏检惩罚 |
| **R4** | §5.2 | 参数向量 $\boldsymbol\eta$ 混合实/复，4L 维 | 修正为 **5L 维实参数** $[\alpha_l^R, \alpha_l^I, \theta_l, \tau_l, \nu_l]_{l=1}^L$ |
| **R5** | §6.1 | 通信/感知参数混用一张表 | 拆为 **Table 1 通信侧** + **Table 2 感知侧** + **Table 3 共用** |
| **R6** | 全文 | 出现"NMSE 降低 5 dB""改善 ≥ 3 dB"等预言数值 | **全部改为"待实验验证"**，不允许投稿前预填数字 |

---

## 第一部分：研究定位与核心设计

### 1.1 论文标题（拟）

**Sparse Tensor-OMP Deep Unfolding Network with Physical-Constrained Off-Grid Refinement for Joint Channel and Target Parameter Estimation in mmWave MIMO-OFDM ISAC Systems**

中文备选：基于物理约束 Tensor-OMP 深度展开网络的毫米波 MIMO-OFDM ISAC 信道与目标参数联合估计

### 1.2 四个核心贡献（写入 Abstract 与 Introduction 末尾）

**C1（建模）**：构建毫米波单站 MIMO-OFDM ISAC 系统的角度-时延-多普勒三维稀疏张量模型，**经正交波形发射与 MIMO 虚拟阵列推导**，将通信信道估计与雷达目标参数估计统一为同一稀疏核张量恢复问题。

**C2（算法）**：提出轻量化 Tensor-OMP 深度展开网络 T-OMP-Net，每层结构对应一次 Tensor-OMP 迭代（相关性 → 学习阈值 → 支撑更新 → 正则化 LS → 残差更新），仅含少量可学习参数；并设计 **Teacher-forcing → Gumbel-Softmax → STE → Hard** 四阶段支撑集训练课程。

**C3（机制）**：设计物理网格约束下的 off-grid 微调机制，对角度/时延/多普勒网格在 $\pm\Delta_{\text{grid}}/2$ 内可学习偏移，缓解离网误差并保持参数可解释性；引入 **Hungarian 最优配对**保证参数损失对目标排列不变。

**C4（验证）**：通过 NMSE / BER / 距离-速度-角度 RMSE / FLOPs / 推理时延等多维指标，**通信侧与感知侧参数分离**评估，覆盖低 SNR、少导频、高速移动、未知目标数、阵列误差等场景。

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

**核心数据预告**（投稿时根据 Section 6 实测结果回填，**不允许在投稿前预填数字**）：
- "在 SNR = __ dB 下，T-OMP-Net 相比 Tensor-OMP 在 NMSE 与参数 RMSE 上的具体改善幅度——**待 Section 6 实验验证**。"
- "参数量与 FLOPs 复杂度——**待 Section 5.3 推导 + Section 6.5.12 实测给出**。"

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

### Section 3  System Model and Problem Formulation（v2.1 全面重写）

#### 3.1 单站 MIMO OFDM-ISAC 系统模型与正交波形发射

考虑单站（monostatic）MIMO OFDM-ISAC 系统，发射与接收阵列收发共置：

- 发射 ULA：$N_t$ 元，阵元间距 $d_t = N_r \cdot \lambda/2$
- 接收 ULA：$N_r$ 元，阵元间距 $d_r = \lambda/2$
- （上述间距使虚拟阵列填充率最大，等效为 $N_v = N_t N_r$ 元 ULA、间距 $\lambda/2$；参见 Bliss & Forsythe 2003；Li & Stoica 2008）
- OFDM 参数：$K$ 子载波，子载波间距 $\Delta f$；每 CPI 内 $M$ 个 OFDM 符号，符号周期 $T_s$；载波频率 $f_c$

**正交波形设计（FDMA-MIMO，使虚拟阵列模型严格成立）**：

将子载波集合 $\{0,1,\dots,K-1\}$ 按发射天线交织划分：
$$
\mathcal{K}_q = \{q,\, q+N_t,\, q+2N_t,\,\dots\}, \quad q=0,1,\dots,N_t-1
$$
第 $q$ 个发射天线**仅在** $\mathcal{K}_q$ 上发射导频/数据。由 $\mathcal{K}_q \cap \mathcal{K}_{q'} = \emptyset$（$q\neq q'$），不同 Tx 在频域正交，接收端可解耦。

**接收端基带等效模型**：

在第 $n_r$ 个接收天线、第 $m$ 个 OFDM 符号、属于 $\mathcal{K}_q$ 的第 $k$ 个子载波上，经 CP 移除与 FFT 后：

$$
y_{n_r,k,m}^{(q)} = \sum_{l=1}^{L} \alpha_l\, [\mathbf{a}_T(\theta_l)]_q\, [\mathbf{a}_R(\theta_l)]_{n_r}\, x_{q,k,m}\, e^{-j2\pi k\Delta f \tau_l}\, e^{j2\pi m T_s \nu_l} + w_{n_r,k,m}^{(q)}
\tag{3-1}
$$

单站几何约束下 **AoD = AoA = $\theta_l$**，每条路径/目标由 4 参数 $(\alpha_l, \theta_l, \tau_l, \nu_l)$ 完整刻画。$w_{n_r,k,m}^{(q)} \sim \mathcal{CN}(0,\sigma_w^2)$。

#### 3.2 MIMO 虚拟阵列与三维数据立方体

**虚拟阵元构造**：定义索引 $v = q \cdot N_r + n_r$，$v \in \{0,1,\dots,N_v-1\}$，$N_v = N_t N_r$。在 $d_t = N_r\lambda/2,\ d_r = \lambda/2$ 配置下，虚拟阵列响应矢量为：

$$
[\mathbf{a}_v(\theta)]_v = [\mathbf{a}_T(\theta)]_q \cdot [\mathbf{a}_R(\theta)]_{n_r} = e^{j2\pi (q d_t + n_r d_r)\sin\theta/\lambda} = e^{j\pi (q N_r + n_r)\sin\theta}
\tag{3-2}
$$

即**等效为间距 $\lambda/2$ 的 $N_v$ 元 ULA**，孔径为标准均匀线阵的 $N_t N_r$ 倍——这是 MIMO 雷达虚拟阵列的经典结论。

**导频均衡得到信道立方体**：导频 $x_{q,k,m}$ 已知，对 $k\in\mathcal{K}_q$ 做点除：
$$
\tilde h_{v,k,m} \triangleq \frac{y_{n_r,k,m}^{(q)}}{x_{q,k,m}} = \sum_{l=1}^L \alpha_l\, [\mathbf{a}_v(\theta_l)]_v\, e^{-j2\pi k\Delta f\tau_l}\, e^{j2\pi m T_s\nu_l} + \tilde w_{v,k,m}
\tag{3-3}
$$

**子载波对齐处理**：由 FDMA 交织，每个虚拟阵元 $v$ 仅在 $\mathcal{K}_q$（$|\mathcal{K}_q|=K/N_t$）上有原始观测。三维数据立方体的构造有两种方案：

- **方案 A（推荐）**：在 $\mathcal{K}_q$ 子集上做处理，等价于子载波数 $K'=K/N_t$ 的张量信号——保守、严格。
- **方案 B**：跨 Tx 间用 DFT/相位补偿对齐至同一 $K$ 维频域栅格（详见附录 A，含插值误差分析）。

主文采用方案 A，得**信道立方体** $\tilde{\mathcal{H}} \in \mathbb{C}^{N_v \times K' \times M}$。

#### 3.3 三维稀疏张量信号模型与稀疏字典化

**张量 CP 分解形式**：将 $\tilde h_{v,k,m}$ 按 $(v,k,m)$ 组织为 3 阶张量：

$$
\boxed{\tilde{\mathcal{H}} \;=\; \sum_{l=1}^L \alpha_l\, \mathbf{a}_v(\theta_l)\,\circ\,\mathbf{p}(\tau_l)\,\circ\,\mathbf{d}(\nu_l)\;+\;\mathcal{N}}
\tag{3-4}
$$

其中 $\circ$ 为矢量外积；

$$
\mathbf{a}_v(\theta_l)\in\mathbb{C}^{N_v},\quad \mathbf{p}(\tau_l)=[e^{-j2\pi k_q\Delta f\tau_l}]_{k_q\in\mathcal{K}_q}\in\mathbb{C}^{K'},\quad \mathbf{d}(\nu_l)=[e^{j2\pi m T_s\nu_l}]_{m=0}^{M-1}\in\mathbb{C}^{M}
$$

$L$ 即 $\tilde{\mathcal{H}}$ 的 CP rank。每个 rank-1 项严格对应一个物理目标/路径。

**稀疏字典构造（物理网格，固定）**：

- 角度字典：$\mathbf{A}_v\in\mathbb{C}^{N_v\times G_\theta}$，第 $g$ 列 $=\mathbf{a}_v(\theta_g)$，$\theta_g=-\pi/2+g\Delta\theta_{\text{grid}}$
- 时延字典：$\mathbf{P}\in\mathbb{C}^{K'\times G_\tau}$，第 $g$ 列对应 $\tau_g\in[0,\tau_{\max}]$
- 多普勒字典：$\mathbf{D}\in\mathbb{C}^{M\times G_\nu}$，第 $g$ 列对应 $\nu_g\in[-\nu_{\max},\nu_{\max}]$

则信号 Tucker 形式：

$$
\boxed{\tilde{\mathcal{H}} \;=\; \mathcal{G} \times_1 \mathbf{A}_v \times_2 \mathbf{P} \times_3 \mathbf{D} \;+\; \mathcal{N}}
\tag{3-5}
$$

$\mathcal{G}\in\mathbb{C}^{G_\theta\times G_\tau\times G_\nu}$ 为**稀疏核张量**，恰有 $L$ 个非零元。

**核张量 ↔ 物理参数严格对应**：

| 核张量元素 | 对应物理含义 |
|---------|------------|
| $\mathcal{G}(g_\theta,g_\tau,g_\nu)\neq 0$ | 存在目标位于网格 $(\theta_{g_\theta},\tau_{g_\tau},\nu_{g_\nu})$ |
| $\mathcal{G}(g_\theta,g_\tau,g_\nu)$ 取值 | 该目标复增益 $\alpha_l$ 估计 |
| $\hat R_l = c\hat\tau_l/2$ | 目标距离 |
| $\hat v_l = c\hat\nu_l/(2f_c)$ | 目标径向速度 |

#### 3.4 问题表述

$$
\boxed{\min_{\mathcal{G}}\;\|\tilde{\mathcal{H}} - \mathcal{G}\times_1\mathbf{A}_v\times_2\mathbf{P}\times_3\mathbf{D}\|_F^2\;+\;\lambda\|\mathcal{G}\|_0}
\tag{3-6}
$$

$\ell_0$ 范数 NP-hard，主流途径：（i）$\ell_1$ 松弛 + ISTA/AMP；（ii）贪婪 Tensor-OMP。本文采用 (ii) 并展开为深度网络（§4）。

**单站等效共角假设的有效性边界**（v2.1 新增声明）：

本模型在严格单站、目标点散射条件下成立。以下场景作为**未来工作**：
- 双站 bi-static ISAC（AoA ≠ AoD）
- 扩展目标（多散射中心，需 cluster 模型）
- 部分校准/混合阵列结构

#### 3.5 与已有工作的对比定位

用一张表对比 4-5 个代表方法（LS、OMP、SOMP、LISTA、本文）在以下维度：张量结构利用 / 物理可解释性 / 端到端训练 / off-grid 处理。

**关键图（Fig. 1）**：系统框图 — 发射端（含 FDMA 子载波交织）→ 信道（含 $L$ 个目标/路径，标注 $\theta,\tau,\nu$）→ 接收端（含虚拟阵列构造）→ 张量化 → T-OMP-Net → 双输出（信道估计 + 目标参数列表）

---

### Section 4  Proposed T-OMP-Net（约 2400 字）

#### 4.1 Tensor-OMP 基础迭代

将稀疏核张量向量化 $\mathbf{g} = \text{vec}(\mathcal{G})$，感知矩阵 $\mathbf{\Phi} = \mathbf{D} \otimes \mathbf{P} \otimes \mathbf{A}_v$。

**Tensor-OMP 算法（Algorithm 1）**：

```
Input: 张量 H_tilde, 物理字典 {A_v, P, D}, 最大稀疏度 L_max, 残差门限 ε
Init: 残差 R_0 = H_tilde, 支撑集 S_0 = ∅
For t = 1, ..., L_max:
   1. c_t = vec(R_{t-1})^H Φ                              # 相关性
   2. i_t = argmax_i |c_t(i)|                             # 选最大原子
   3. S_t = S_{t-1} ∪ {i_t}
   4. g_{S_t} = (Φ_{S_t}^H Φ_{S_t})^{-1} Φ_{S_t}^H vec(H_tilde)
   5. R_t = H_tilde - reshape(Φ_{S_t} g_{S_t})
   6. If ||R_t||_F / ||H_tilde||_F < ε: break
Output: G_hat
```

#### 4.2 T-OMP-Net 网络结构（核心创新）

将上述迭代展开为固定 $T$ 层网络，每层 1 次迭代。

**OMP-Layer-t 结构（Algorithm 2）**：

```
输入：上一层残差 R_{t-1}, 支撑集 S_{t-1}, 当前字典 {A_v,t, P_t, D_t}
────────────────────────────────────
Step 1 (相关性计算):
   c_t = vec(R_{t-1})^H Φ_t
Step 2 (可学习软阈值 λ_t):
   c_tilde = sign(c_t) ⊙ max(|c_t| - λ_t, 0)
Step 3 (支撑集更新，TopK):
   S_t = S_{t-1} ∪ TopK(c_tilde, K_t)
Step 4 (正则化 LS, 可学习 μ_t):
   g_t = (Φ_{S_t,t}^H Φ_{S_t,t} + μ_t I)^{-1} Φ_{S_t,t}^H vec(H_tilde)
Step 5 (残差更新, 可学习步长 γ_t):
   R_t = R_{t-1} - γ_t · reshape(Φ_{S_t,t} g_t - Φ_{S_{t-1},t} g_{t-1})
────────────────────────────────────
输出：R_t, S_t, g_t
```

**每层可学习参数（仅 4 个标量 + 字典偏移）**：

| 参数 | 维度 | 物理含义 | 初始化 |
|------|------|---------|-------|
| $\lambda_t$ | 1 | 软阈值 | $\sigma\sqrt{2\log N}$ |
| $\mu_t$ | 1 | LS 正则 | $10^{-3}$ |
| $\gamma_t$ | 1 | 残差步长 | 1.0 |
| $K_t$（可选） | 1 整数 | Top-K | 1 |
| $\{\Delta\theta_g,\Delta\tau_g,\Delta\nu_g\}$ | $G_\theta+G_\tau+G_\nu$ | off-grid 偏移 | 0 |

**总参数量推导**（$T=8$, $G_\theta=128$, $G_\tau=64$, $G_\nu=32$）：
$$N_{\text{params}} = 4T + (G_\theta+G_\tau+G_\nu) = 32 + 224 = 256 \text{ 个标量}$$

该参数量推导仅基于网络结构本身；与基线方法（如典型 CNN）的实测复杂度差距**待 §6.5.12 给出**。

#### 4.2.1 支撑集选择的训练策略（v2.1 新增）

**问题**：Algorithm 2 的 Step 3 中 `TopK` 与底层 `argmax` 不可导，直接反向传播时梯度无法穿过支撑集选择，使前面各层的 $\lambda_t,\mu_t,\gamma_t$ 与字典偏移无法被有效训练。

**策略 1 — Teacher Forcing（仅训练初期）**：

仿真数据中真值支撑集 $\mathcal{S}^{\text{GT}}$ 已知（由真实目标参数 $(\theta_l,\tau_l,\nu_l)$ 映射到字典网格）。训练初期直接代入：
$$\mathcal{S}_t^{\text{train}} \leftarrow \mathcal{S}^{\text{GT}}, \quad t=1,\dots,T$$
保证早期网络在"正确"支撑上学习剩余参数，避免发散。

**策略 2 — Gumbel-Softmax 软选择（中期）**：

将 hard argmax 替换为带 Gumbel 噪声的可微 softmax：
$$
\mathbf{w}_t = \text{softmax}\!\left(\frac{|c_t| + \mathbf{g}}{\tau_T}\right),\quad \mathbf{g}_i\overset{\text{iid}}{\sim}\text{Gumbel}(0,1)
$$
$\mathbf{w}_t$ 接近 one-hot 但保留梯度。$\tau_T$ 从 1.0 退火到 0.1。

**策略 3 — Straight-Through Estimator (STE)（后期）**：

前向使用 hard TopK 与推理一致；反向把 hard 选择视作"等同于"软选择，使梯度从 $\mathbf{w}_t$（soft）流回：
- Forward: $\mathbf{s}_t = \text{onehot}(\arg\max_i |c_t|)$
- Backward: $\partial \mathbf{s}_t / \partial \mathbf{c}_t \approx \partial \mathbf{w}_t / \partial \mathbf{c}_t$

**策略 4 — Hard（fine-tune）**：

最后阶段完全使用 hard TopK，与推理完全一致，确保部署时无 train-test mismatch。

**推荐四阶段训练课程**：

| 阶段 | Epoch 区间 | 支撑选择 | 温度 $\tau_T$ | 备注 |
|------|-----------|---------|--------------|------|
| Warm-up | 1 – 20 | Teacher Forcing（GT 支撑） | — | 稳定字典偏移与阈值的初始学习 |
| Soft | 21 – 50 | Gumbel-Softmax | 1.0 → 0.3 退火 | 引入探索性 |
| Anneal | 51 – 70 | STE | 0.3 → 0.1 退火 | 训练-推理一致性过渡 |
| Hard | 71 – 80 | Hard TopK | — | Fine-tune，最终性能 |

**实现要点**：
- Teacher forcing 阶段对真实场景部署无影响，仅训练期使用
- Gumbel 噪声仅在训练态加入，推理时关闭
- STE 阶段需冻结部分参数（如字典偏移）以稳定

#### 4.3 物理约束 Off-Grid Refinement（Contribution 3 核心）

字典原子修正：
$$
\tilde\theta_g = \theta_g + \Delta\theta_g, \quad |\Delta\theta_g| \leq \frac{\Delta\theta_{\text{grid}}}{2}
$$
时延、多普勒同理。**约束实现**：硬约束 tanh 重参数化：
$$
\Delta\theta_g = \frac{\Delta\theta_{\text{grid}}}{2}\tanh(w_g),\quad w_g \in \mathbb{R}
$$
$w_g$ 为底层无约束可学习参数，自动微分顺畅。

**关键写作要点**：强调"网格点仍对应物理角度/时延/多普勒，仅在 grid spacing 内做亚网格修正"，可解释性完全保留。

#### 4.4 联合损失函数

$$
\boxed{\mathcal{L} \;=\; \mathcal{L}_{\text{NMSE}} + \beta_1\,\mathcal{L}_{\text{Param}} + \beta_2\,\mathcal{L}_{\text{Sparse}} + \beta_3\,\mathcal{L}_{\text{Off-grid}}}
\tag{4-1}
$$

- **信道重建**：$\mathcal{L}_{\text{NMSE}} = \|\hat{\mathcal{H}} - \mathcal{H}\|_F^2 / \|\mathcal{H}\|_F^2$
- **参数误差**：$\mathcal{L}_{\text{Param}}$ — 见 §4.4.1（Hungarian 配对）
- **稀疏正则**：$\mathcal{L}_{\text{Sparse}} = \|\hat{\mathcal{G}}\|_1$
- **off-grid 正则**：$\mathcal{L}_{\text{Off-grid}} = \|\Delta\boldsymbol\theta\|_2^2 + \|\Delta\boldsymbol\tau\|_2^2 + \|\Delta\boldsymbol\nu\|_2^2$

权重 $\beta_1=1.0,\beta_2=10^{-3},\beta_3=10^{-2}$ 为初始值，敏感性分析放消融。

#### 4.4.1 参数损失的最优配对（Hungarian Matching，v2.1 新增）

**问题**：估计目标集 $\hat{\mathcal{P}}=\{(\hat\alpha_i,\hat\theta_i,\hat\tau_i,\hat\nu_i)\}_{i=1}^{\hat L}$ 与真值集 $\mathcal{P}=\{(\alpha_j,\theta_j,\tau_j,\nu_j)\}_{j=1}^{L}$ 均为**无序**集合。按下标对齐计算损失会引入非物理的排列错误，必须先求最优一一配对。

**步骤 1 — 构造代价矩阵** $\mathbf{C}\in\mathbb{R}^{\hat L\times L}$：

$$
C_{ij} = w_\theta\cdot\frac{|\hat\theta_i - \theta_j|}{\theta_{\text{range}}} + w_\tau\cdot\frac{|\hat\tau_i - \tau_j|}{\tau_{\max}} + w_\nu\cdot\frac{|\hat\nu_i - \nu_j|}{\nu_{\max}}
\tag{4-2}
$$

权重默认 $w_\theta=w_\tau=w_\nu=1/3$（敏感性放消融）。

**步骤 2 — Hungarian 算法求最优配对**：

$$
\pi^* = \arg\min_\pi \sum_i C_{i,\pi(i)},\quad \pi:\{1,\dots,\min(\hat L,L)\}\to\{1,\dots,L\}\ \text{单射}
$$

复杂度 $O((\max(\hat L,L))^3)$，$L\leq 10$ 实际开销可忽略。
实现：训练时调用 `scipy.optimize.linear_sum_assignment`；可选 differentiable Sinkhorn（端到端梯度）。

**步骤 3 — 失配惩罚（$\hat L\neq L$）**：

- 虚警 $n_{\text{FA}}=\max(\hat L-L,0)$ 个未配对估计目标，每个贡献固定惩罚 $c_{\text{FA}}$
- 漏检 $n_{\text{Miss}}=\max(L-\hat L,0)$ 个未配对真值目标，每个贡献固定惩罚 $c_{\text{Miss}}$

**最终参数损失**：

$$
\mathcal{L}_{\text{Param}} = \frac{1}{L}\!\!\sum_{(i,j)\in\pi^*}\!\!\Big[\rho_H(\hat\theta_i\!-\!\theta_j) + \lambda_\tau\rho_H(\hat\tau_i\!-\!\tau_j) + \lambda_\nu\rho_H(\hat\nu_i\!-\!\nu_j)\Big] + \frac{c_{\text{FA}}n_{\text{FA}} + c_{\text{Miss}}n_{\text{Miss}}}{L}
\tag{4-3}
$$

$\rho_H(\cdot)$ 为 Huber 损失（抗野值）。推荐 $c_{\text{FA}}=c_{\text{Miss}}=1.0$。

**训练实现要点**：
- $\pi^*$ 在每个 minibatch 内独立求解
- $\pi^*$ 本身为离散变量，不参与反向；仅其指定的配对参与梯度计算
- 保证损失对目标编号的 permutation-invariance

#### 4.5 训练策略汇总

- 优化器：AdamW，初始学习率 $1\times 10^{-3}$，cosine decay
- Batch size：32
- 训练样本：自定义参数化 ISAC 场景 50,000 组
- 总 Epoch：80（按 §4.2.1 四阶段课程）
- SNR 课程：训练 SNR 20 → -5 dB，每 20 epoch 降 5 dB
- 早停：验证集 NMSE 连续 10 epoch 不下降则停

#### 4.6 目标参数提取（推理阶段）

```
1. 阈值化 G_hat: 保留 |G_hat(i,j,k)| > η · max(|G_hat|) 的位置
2. 对每个非零位置 (i*, j*, k*):
   - θ_hat = θ_{i*} + Δθ_{i*}
   - τ_hat = τ_{j*} + Δτ_{j*}
   - ν_hat = ν_{k*} + Δν_{k*}
3. 换算物理量:
   - R_hat = c · τ_hat / 2
   - v_hat = c · ν_hat / (2 f_c)
```

**关键图（Fig. 2）**：T-OMP-Net 整体架构图（输入 → T 层 OMP-Layer → 双输出：估计信道 + 目标参数列表），每层内部展开为 5 个 step 的小子图。

---

### Section 5  Theoretical Analysis（约 1300 字）

#### 5.1 Error Bound Analysis（误差界分析）

**写作策略**：避开严格收敛证明，定位为"借助经典 CS 理论的误差界继承性分析"。

**Proposition 1（推荐表述）**：

> Suppose the sensing matrix $\mathbf{\Phi}$ satisfies the $L$-th order Restricted Isometry Property (RIP) with constant $\delta_{2L} < \sqrt{2}-1$. Then the output of the unfolded T-OMP-Net inherits the residual-reduction property of classical Tensor-OMP. The learnable thresholds $\{\lambda_t\}$ and regularization coefficients $\{\mu_t\}$ provide additional flexibility to **empirically** tighten the recovery error bound, which we verify numerically in Section 6.

引 Davenport & Wakin 2010 关于 OMP 在 RIP 下的误差界引理作为继承基础。

**Proposition 2（off-grid 误差界）**：物理约束 off-grid 偏移在 $\pm\Delta_{\text{grid}}/2$ 内时，离网误差从 $O(\Delta_{\text{grid}})$ 量级降至与噪声 $O(\sigma_{\text{noise}})$ 同阶。数值验证放 §6 消融。

#### 5.2 CRLB 推导（v2.1 修正：5L 维实参数向量）

**参数向量重新定义**：将复增益 $\alpha_l = \alpha_l^R + j\alpha_l^I$ 拆为两个独立实参数，避免复数 Fisher 矩阵处理的二义性。定义 **5L 维实参数向量**：

$$
\boxed{\boldsymbol{\eta} \;=\; \big[\,\alpha_1^R,\alpha_1^I,\theta_1,\tau_1,\nu_1,\;\dots,\;\alpha_L^R,\alpha_L^I,\theta_L,\tau_L,\nu_L\,\big]^T \;\in\; \mathbb{R}^{5L}}
\tag{5-1}
$$

Fisher 信息矩阵 $\mathbf{F}\in\mathbb{R}^{5L\times 5L}$：

$$
[\mathbf{F}(\boldsymbol{\eta})]_{ij} = \frac{2}{\sigma^2}\Re\!\left\{\frac{\partial\boldsymbol{\mu}^H}{\partial\eta_i}\frac{\partial\boldsymbol{\mu}}{\partial\eta_j}\right\}
\tag{5-2}
$$

其中 $\boldsymbol{\mu} = \mathbb{E}[\text{vec}(\tilde{\mathcal{H}})] \in \mathbb{C}^{N_v K' M}$。

**关键偏导（附录 B 完整推导）**：

记第 $l$ 条路径贡献 $\boldsymbol{\mu}_l = \alpha_l\,\mathbf{a}_v(\theta_l)\circ\mathbf{p}(\tau_l)\circ\mathbf{d}(\nu_l)$，则：

$$
\frac{\partial\boldsymbol{\mu}_l}{\partial\alpha_l^R} = \mathbf{a}_v(\theta_l)\circ\mathbf{p}(\tau_l)\circ\mathbf{d}(\nu_l)
\tag{5-3a}
$$
$$
\frac{\partial\boldsymbol{\mu}_l}{\partial\alpha_l^I} = j\,\mathbf{a}_v(\theta_l)\circ\mathbf{p}(\tau_l)\circ\mathbf{d}(\nu_l)
\tag{5-3b}
$$
$$
\frac{\partial\boldsymbol{\mu}_l}{\partial\theta_l} = \alpha_l\,\dot{\mathbf{a}}_v(\theta_l)\circ\mathbf{p}(\tau_l)\circ\mathbf{d}(\nu_l)
\tag{5-3c}
$$
其中 $\dot{\mathbf{a}}_v(\theta) = \partial\mathbf{a}_v/\partial\theta$，元素 $[\dot{\mathbf{a}}_v]_v = j\pi(qN_r+n_r)\cos\theta\cdot[\mathbf{a}_v]_v$。
$$
\frac{\partial\boldsymbol{\mu}_l}{\partial\tau_l} = -j2\pi\Delta f\,\alpha_l\,\mathbf{a}_v(\theta_l)\circ\big(\mathbf{k}\odot\mathbf{p}(\tau_l)\big)\circ\mathbf{d}(\nu_l),\quad \mathbf{k}=[k_q]_{k_q\in\mathcal{K}_q}
\tag{5-3d}
$$
$$
\frac{\partial\boldsymbol{\mu}_l}{\partial\nu_l} = j2\pi T_s\,\alpha_l\,\mathbf{a}_v(\theta_l)\circ\mathbf{p}(\tau_l)\circ\big(\mathbf{m}\odot\mathbf{d}(\nu_l)\big),\quad \mathbf{m}=[0,1,\dots,M-1]^T
\tag{5-3e}
$$

**CRLB 计算**：

$$
\text{CRLB}(\eta_i) = [\mathbf{F}^{-1}]_{ii}
$$

**派生物理量 CRLB（通过 Jacobian 传递）**：
- 距离：$R_l = c\tau_l/2 \;\Rightarrow\; \text{CRLB}(R_l) = (c/2)^2\,\text{CRLB}(\tau_l)$
- 速度：$v_l = c\nu_l/(2f_c) \;\Rightarrow\; \text{CRLB}(v_l) = (c/(2f_c))^2\,\text{CRLB}(\nu_l)$
- 复增益模与相位的 CRLB 由 $\{\alpha_l^R,\alpha_l^I\}$ 块的 $2\times 2$ 子矩阵给出

**Fig. 7** 中绘制 $\sqrt{\text{CRLB}(\theta_l)}$、$\sqrt{\text{CRLB}(R_l)}$、$\sqrt{\text{CRLB}(v_l)}$ vs SNR，与各算法 RMSE 比较。

#### 5.3 复杂度分析

| 算法 | 每帧 FLOPs | 参数量 |
|------|-----------|-------|
| LS | $O(KN_rN_t)$ | 0 |
| OMP | $O(LKN_rN_tG)$ | 0 |
| Tensor-OMP | $O(LG_\theta G_\tau G_\nu(N_v+K'+M))$ | 0 |
| LDAMP | $O(TG^2)$ | $\sim 10^6$ |
| ChannelNet | $O(CK^2)$ | $\sim 10^7$ |
| **T-OMP-Net** | $O(TLG_\theta G_\tau G_\nu)$ | $\sim 10^2 \sim 10^3$ |

FLOPs 详细推导（每项操作的乘加次数累加）放附录 C。实测复杂度对比**待 §6.5.12 给出**。

---

### Section 6  Simulation Results（约 2500 字）

#### 6.1 Simulation Setup（v2.1 修订：通信/感知/共用三表分离）

通信侧与感知侧的工作频段、SNR 定义、子载波分配差异显著，分别给出独立参数表。

**Table 1 — Communication-side simulation parameters**

| 参数 | 取值 | 说明 |
|------|------|------|
| 载波频率 $f_c^{\text{c}}$ | 28 GHz | mmWave 通信主流 |
| 带宽 $B^{\text{c}}$ | 100 MHz | 单 BWP 典型 |
| 子载波数 $K^{\text{c}}$ | 256 | 通信密集子载波 |
| 子载波间距 $\Delta f^{\text{c}}$ | 390 kHz | $B/K$ |
| OFDM 符号数 $M^{\text{c}}$ | 14 | 1 个 slot |
| 发射 / 接收天线 $N_t^{\text{c}}/N_r^{\text{c}}$ | 4 / 4 | UE-级别 |
| 导频图样 | 1/4 comb pilot | 4 子载波 1 导频 |
| 调制方式 | 16-QAM / 64-QAM | — |
| 信道模型 | 3GPP TR 38.901 CDL-A/C/D | NLOS+ / LOS |
| SNR 定义 | $E_s/N_0$（接收端） | — |
| SNR 范围 | -10 ~ 30 dB（步长 5 dB） | — |
| 评价指标 | NMSE (on data subcarriers), BER, SE | — |

**Table 2 — Sensing-side simulation parameters**

| 参数 | 取值 | 说明 |
|------|------|------|
| 载波频率 $f_c^{\text{s}}$ | 77 GHz | 车载雷达频段 |
| 带宽 $B^{\text{s}}$ | 200 MHz | 高距离分辨 |
| 子载波数 $K^{\text{s}}$ | 128 | — |
| 子载波间距 $\Delta f^{\text{s}}$ | 1.5625 MHz | — |
| 符号周期 $T_s^{\text{s}}$ | $\approx 10\,\mu$s | 含 CP |
| OFDM 符号数 $M^{\text{s}}$ | 32 | 1 个 CPI |
| 发射 / 接收天线 $N_t^{\text{s}}/N_r^{\text{s}}$ | 8 / 16 | — |
| 虚拟阵元数 $N_v$ | 128 | $=N_t N_r$ |
| 子载波分配 | FDMA 交织（按 §3.1） | 全照射 |
| 目标数 $L$ | 1 ~ 10（基础 $L=4$） | — |
| 距离范围 | 0 ~ 100 m | — |
| 速度范围 | $\pm$50 m/s | — |
| 理论距离分辨率 | $c/(2B) \approx 0.75$ m | — |
| 理论速度分辨率 | $c/(2f_c MT_s) \approx 0.6$ m/s | — |
| 理论角度分辨率 | $\approx 2/N_v \approx 0.9°$ | — |
| SNR 定义 | 单目标回波 SNR（post-CPI 增益前） | — |
| SNR 范围 | -10 ~ 30 dB（步长 5 dB） | — |
| 评价指标 | 距离/速度/角度 RMSE, $P_d$, $P_{fa}$ | — |

**Table 3 — Shared training & network parameters**

| 参数 | 取值 |
|------|------|
| 角度字典网格 $G_\theta$ | 128 |
| 时延字典网格 $G_\tau$ | 64 |
| 多普勒字典网格 $G_\nu$ | 32 |
| T-OMP-Net 展开层数 $T$ | 8（默认；消融 $T\in\{4,6,8,10\}$） |
| 训练样本数 | 50,000 |
| Batch size | 32 |
| 优化器 / 学习率 | AdamW / $1\times 10^{-3}$ |
| Epochs | 80（Warm-up/Soft/Anneal/Hard 四阶段） |
| 训练 SNR 课程 | 20 → -5 dB（每 20 epoch 降 5 dB） |
| 硬件 | 单卡 RTX 4090（24 GB） |

**联合 ISAC 场景**（§6.7）单独给定折中参数：$f_c=77$ GHz、$B=150$ MHz、$N_t/N_r=8/16$、含导频与感知双任务。

#### 6.2 Channel Configurations

| 编号 | 来源 | 用途 |
|------|------|------|
| Set A | 自定义参数化 ISAC 多目标场景 | **主实验**（参数 RMSE） |
| Set B | 3GPP TR 38.901 CDL-A（NLOS） | 通信泛化 |
| Set C | 3GPP TR 38.901 CDL-C（NLOS+） | 通信泛化 |
| Set D | 3GPP TR 38.901 CDL-D（LOS） | 通信泛化 |
| Set E（选做） | DeepMIMO O1/I3 | 跨场景泛化 |

#### 6.3 Baselines（8 种）

| 类别 | 算法 | 来源 |
|------|------|------|
| 经典 | LS | — |
| 经典 | LMMSE | — |
| 矩阵 CS | OMP | Tropp 2007 |
| 多测量 CS | SOMP | Tropp 2006 |
| 张量 CS | Tensor-OMP | Caiafa & Cichocki 2013 |
| 展开网络 | LISTA / LDAMP | Gregor 2010 / Metzler 2017 |
| 数据驱动 DL | CAE | 本作者毕设 |
| **本文** | **T-OMP-Net** | — |

#### 6.4 评价指标

- 通信侧：NMSE (dB)，BER（公式略，按 Table 1 在数据子载波上计算）
- 感知侧：距离/速度/角度 RMSE，$P_d$, $P_{fa}$（按 Table 2 配置）
- 系统侧：参数量、FLOPs、推理延迟 (ms)、显存

#### 6.5 实验设计与对应图表

| Exp | 实验内容 | 横轴 | 纵轴 | 图编号 |
|-----|---------|------|------|-------|
| 6.5.1 | NMSE vs SNR（通信侧 + 感知侧） | SNR -10~30 dB | NMSE (dB) | Fig. 3 |
| 6.5.2 | BER vs SNR（通信侧） | 同上 | BER | Fig. 4 |
| 6.5.3 | 距离 RMSE vs SNR | 同上 | m | Fig. 5 |
| 6.5.4 | 速度 RMSE vs SNR | 同上 | m/s | Fig. 6 |
| 6.5.5 | 角度 RMSE vs SNR（叠加 CRLB） | 同上 | deg | Fig. 7 |
| 6.5.6 | 少导频 | 导频比 {5,10,15,20,25}% | NMSE / RMSE | Fig. 8 |
| 6.5.7 | 高速移动 | 速度 {0,60,120,240,360,500} km/h | NMSE / 速度 RMSE | Fig. 9 |
| 6.5.8 | 未知 $L$ | $L\in\{2,4,6,8,10\}$ | NMSE / $P_d$ | Fig. 10 |
| 6.5.9 | 阵列误差 | ±1dB / ±5° / 阵元扰动 | NMSE | Table II |
| 6.5.10 | 消融 | 8 种变体 | NMSE / 参数 RMSE | Table III |
| 6.5.11 | 展开层数 | $T\in\{4,6,8,10\}$ | NMSE / FLOPs | Fig. 11 |
| 6.5.12 | 复杂度 | 8 种算法 | 参数/FLOPs/延迟 | Table IV |

#### 6.6 消融实验

| 变体 | 说明 |
|------|------|
| A0 | Tensor-OMP（无学习） |
| A1 | T-OMP-Net 仅可学阈值 $\lambda_t$ |
| A2 | A1 + 正则 $\mu_t$ |
| A3 | A2 + 残差步长 $\gamma_t$ |
| A4 | A3 + off-grid 但无 $\mathcal{L}_{\text{Off-grid}}$ 约束 |
| **A5（Full）** | **A3 + 物理约束 off-grid + 全部 4 项损失（含 Hungarian）** |
| A6 | A5 移除 $\mathcal{L}_{\text{Param}}$（联合损失必要性） |
| A7 | A5 移除 $\mathcal{L}_{\text{Sparse}}$ |

**关键卖点表述**：A0→A5 各组件对 NMSE/RMSE 的累积贡献（**待实验验证**）；A5 vs A6 用于量化参数损失项对感知精度的具体贡献（**待实验验证**）。

#### 6.7 跨场景泛化（Set A 训练 → Set B/C/D 测试），及 §6.7 联合 ISAC 场景验证

#### 6.8 结果讨论要点

- 显著领先 baseline 的 SNR 区间（**待实验验证**）
- off-grid 修正在哪类参数（角度/时延/多普勒）效益最大（**待实验验证**）
- 复杂度/参数量优势的工程意义（**待 §6.5.12 给出**）
- 极端条件下方法局限（诚实指出）

---

### Section 7  Conclusion（约 400 字）

- 总结四点贡献
- 给出代表性数值结果（呼应 Introduction，**投稿前由实验回填**）
- 未来方向：
  1. 扩展到双站 bi-static ISAC（AoA ≠ AoD）
  2. 引入 RIS 辅助
  3. 硬件实测验证（TI mmWave EVM 或 USRP）

---

## 第三部分：实施计划（6 个月）

### Phase 1（M1, 4 周）：模型与 Baseline

| 周 | 任务 |
|----|------|
| W1 | 自定义 ISAC 信号生成（含真值标签）、3GPP CDL 数据导入 |
| W2 | LS / LMMSE / OMP / SOMP 实现 |
| W3 | Tensor-OMP 实现，跑通完整 pipeline |
| W4 | 评价指标统一封装（NMSE/BER/RMSE） |

**退出标准**：Tensor-OMP 在 SNR=20 dB 下可正常输出完整 NMSE-SNR 曲线（具体数值**待实验验证**）。

### Phase 2（M2, 4 周）：T-OMP-Net 最小版本

| 周 | 任务 |
|----|------|
| W5 | T-OMP-Net 网络层 PyTorch 实现（无 off-grid，无 Hungarian） |
| W6 | 四阶段训练课程实现（Teacher Forcing → Gumbel → STE → Hard） |
| W7 | 调参 + 单损失 $\mathcal{L}_{\text{NMSE}}$ 训练，验证 > Tensor-OMP |
| W8 | 加入 Hungarian + $\mathcal{L}_{\text{Param}}$ 联合训练 |

**退出标准**：T-OMP-Net 稳定收敛，相比 Tensor-OMP 在多个 SNR 点的 NMSE 有改善（具体幅度**待实验验证**）。

### Phase 3（M3, 3 周）：Off-Grid 物理约束

| 周 | 任务 |
|----|------|
| W9 | tanh 重参数化 off-grid 偏移 |
| W10 | $\mathcal{L}_{\text{Off-grid}}$ 约束损失加入 |
| W11 | 有/无 off-grid 的参数 RMSE 对比 |

### Phase 4（M4-M5, 6 周）：全量实验

- W12-13：基础性能曲线
- W14：少导频
- W15：高速移动 + 未知 $L$ + 阵列误差
- W16：消融 + 展开层数
- W17：复杂度统计 + 跨场景泛化

### Phase 5（M6, 4 周）：理论与论文撰写

- W18：CRLB 推导成稿（按 §5.2 5L 实参数）
- W19-20：Introduction / Related Work / System Model
- W21：Proposed Method / Theoretical Analysis
- W22：Simulation Results + 图表
- W23：通稿润色 + 投稿

---

## 第四部分：投稿与风险管理

### 4.1 投稿梯度

| 顺序 | 期刊 | IF | 偏好 |
|------|------|----|------|
| 1 | Signal Processing (Elsevier) | ~3.4 | 方法/理论 |
| 2 | Digital Signal Processing (Elsevier) | ~2.9 | 方法创新 |
| 3 | IEEE Sensors Journal | ~4.3 | 应用 + 实验 |
| 4 | IEEE Systems Journal | ~4.0 | 系统方案 |

### 4.2 审稿人潜在问题及预案

| 问题 | 预案 |
|------|------|
| Q：相比 Tensor-OMP 提升来源？ | A：A0 vs A5 消融量化每个学习模块贡献 |
| Q：仅做仿真，无实测？ | A：DeepMIMO 准实测补充；未来工作指向 TI EVM |
| Q：单站 monostatic 假设是否过强？ | A：§3.4 明确假设边界；扩展至双站为未来工作 |
| Q：FDMA 子载波分配的频谱效率代价？ | A：对感知任务无影响；通信侧已有研究表明可在子载波交织上叠加 OFDM 数据 |
| Q：Hungarian 匹配训练时是否引入梯度问题？ | A：$\pi^*$ 离散，不参与反向；仅其指定配对的连续量参与梯度，permutation-invariant 损失 |
| Q：支撑选择训练能否真的收敛？ | A：4 阶段课程（Teacher Forcing → Gumbel → STE → Hard）逐步过渡，文献多有先例 |
| Q：可学习参数 $\lambda_t/\mu_t/\gamma_t$ 学到了什么？ | A：附录可视化各层参数随训练演化曲线 |
| Q：未知 $L$ 鲁棒性？ | A：§6.5.8 实验已覆盖 |
| Q：CRLB 是否严格？ | A：5L 实参数 FIM 完整 + 数值差分交叉验证 |

### 4.3 关键风险

| 风险 | 应对 |
|------|------|
| 支撑选择训练发散 | 四阶段课程 + Teacher Forcing 兜底 |
| Hungarian 训练慢 | $L\leq 10$ 时 scipy 实现已足够；超出则换 Sinkhorn |
| T-OMP-Net 性能差距小 | 强化复杂度优势 + off-grid 优势 + Hungarian 带来的参数估计提升 |
| CRLB 推导出错 | 数值差分 Fisher 矩阵交叉验证 |
| 时间超期 | DeepMIMO 改选做；联合 ISAC 场景 §6.7 选做 |

---

## 第五部分：本周可立即执行

1. **建 Git 仓库**：`mmwave-isac-tompnet`
   ```
   /data       /baseline    /tompnet
   /train      /eval        /paper
   ```
2. **完成自定义 ISAC 信号生成器**（按 §3.1 FDMA 交织 + §3.2 虚拟阵列）
3. **下载 3GPP CDL-A/C/D 配置**
4. **阅读 5 篇核心文献**：
   - Bliss & Forsythe 2003（MIMO 虚拟阵列）
   - Caiafa & Cichocki 2013（Tensor-OMP）
   - Chen et al. 2018（LISTA 收敛性）
   - Jang & Gu 2017（Gumbel-Softmax）
   - Carion et al. 2020（DETR 中 Hungarian Matching）

---

## 附录：v2.1 对照 v2.0 差异速查

| 论文章节 | v2.0 | v2.1 变化 |
|---------|------|----------|
| §3.1 | 等效共享角 $\bar\theta$ | 单站 + FDMA 正交波形 + 虚拟阵列严谨推导 |
| §3.2 | 张量化（含糊） | 虚拟阵元构造 + 子载波对齐处理 |
| §3.3 | 稀疏字典 | CP 分解 + 物理参数严格对应表 |
| §4.2 | 算法 + 参数表 | + §4.2.1 四阶段支撑选择训练课程 |
| §4.4 | $\mathcal{L}_{\text{Param}}$ 简化 | + §4.4.1 Hungarian 配对 + FA/Miss 惩罚 |
| §5.2 | $\boldsymbol\eta\in\mathbb{C}^{4L}$ 混合 | $\boldsymbol\eta\in\mathbb{R}^{5L}$ 实参数 + 完整偏导 |
| §6.1 | 单一参数表 | Table 1 通信 + Table 2 感知 + Table 3 共用 |
| 全文数值 | "降低 5 dB""改善 ≥ 3 dB" | 全部 → "待实验验证" |

---

**—— v2.1 大纲完 ——**

> 本版本仅对 6 项指定位置做技术修订，未触及其他章节结构。任一修订点如需进一步细化（如附录 A 子载波对齐插值方案、附录 B 完整 CRLB 偏导、Gumbel-Softmax 温度退火细节、Hungarian 的 Sinkhorn 可微实现等），可单独展开。
