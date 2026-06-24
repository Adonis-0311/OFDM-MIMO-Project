# 基于张量分解与深度展开网络的 OFDM-MIMO 毫米波 ISAC 系统信道与目标参数联合估计

## ——SCI Q2 期刊投稿技术设计报告

> 作者：刘雨辉
> 版本：v1.0
> 目标期刊：IEEE Sensors Journal / Signal Processing (Elsevier) / IEEE Systems Journal / Digital Signal Processing (Elsevier)
> 备选期刊：IEEE Transactions on Vehicular Technology（冲刺）

---

## 0  执行摘要

本报告以你的本科毕设（CS+DL 两阶段 OFDM-MIMO 毫米波信道估计）为基础，提出可达到稳妥 SCI Q2 水平的研究升级方案：将研究定位从"通信信道估计"扩展为**通信-感知一体化（ISAC）下的信道与目标参数联合估计**，核心方法是 **张量分解（Tensor Decomposition）+ 模型驱动深度展开网络（Deep Unfolding Network）**。本报告给出完整的信号模型、算法设计、理论分析框架、仿真方案、实施计划与投稿策略。

**预期建立 3 个核心贡献（Contributions）：**

- **C1**：构建 OFDM-MIMO mmWave ISAC 系统下角度-时延-多普勒三维稀疏张量信号模型，实现通信信道估计与雷达参数估计的统一表述。
- **C2**：提出张量-OMP 深度展开网络 **T-OMP-Net**，将传统张量贪婪追踪算法的每次迭代展开为可学习的网络层，融合 CS 的稀疏先验与 DL 的非线性表征能力，**字典原子、阈值、步长等参数端到端可学习**。
- **C3**：完成 CRLB 推导、复杂度分析与收敛性证明，并在 3 种 3GPP CDL 信道模型 + DeepMIMO 公开数据集上对 **7 种** baseline 进行系统对比，覆盖低 SNR、少导频、高速移动、阵列误差等 4 类鲁棒性场景。

---

## 1  研究定位与创新点

### 1.1 问题陈述

OFDM-MIMO 毫米波系统在 5G/6G 与车载雷达中具有"通信-感知"双重功能。当前主流研究将信道估计与雷达参数（距离、速度、角度）估计分开处理，存在两个问题：

1. **物理本质重复**：毫米波信道的多径参数 $\{\alpha_l, \theta_l, \phi_l, \tau_l, \nu_l\}$ 本身就是雷达目标参数。分别估计造成信息冗余、性能损失。
2. **方法割裂**：CS 类方法可解释性强但依赖先验；DL 方法精度高但是黑箱。已有 CS+DL 级联方案（包括你的毕设）属于"加法式"组合，未真正在算法层面融合。

### 1.2 三大创新点

**C1 角度-时延-多普勒三维稀疏张量模型**

将 OFDM-MIMO ISAC 系统的接收信号建模为 4 阶张量 $\mathcal{Y} \in \mathbb{C}^{N_r \times K \times M \times N_t}$，利用 CP（CANDECOMP/PARAFAC）分解将其表示为有限个外积之和，每个 rank-1 项对应一个物理路径/目标。该统一框架自然实现了信道估计 = 目标参数估计。

**C2 T-OMP-Net 深度展开网络**

将张量正交匹配追踪（Tensor-OMP）的每次迭代展开为一个可学习网络层，每层包含：原子相关性计算 → 学习阈值 soft-shrinkage → 支撑集更新 → LS 投影。**关键创新**：

- 字典原子参数（角度/时延/多普勒网格）作为可学习参数，缓解 off-grid 问题；
- 引入跨层残差连接与 attention 机制，增强长程依赖建模；
- 端到端损失为 NMSE + 雷达参数误差 + 稀疏正则三项联合。

**C3 严格理论分析与全面实验**

- 推导联合估计问题的 Cramér-Rao Lower Bound (CRLB)，作为算法性能的理论下界；
- 给出 T-OMP-Net 的收敛性分析（基于深度展开网络等价于学习型 ISTA/AMP 的理论）；
- 严格 FLOPs/参数量/存储复杂度推导。

### 1.3 目标期刊与对标分析

| 期刊 | 影响因子 | 分区 | 偏好范式 | 命中难度 |
|------|---------|------|---------|---------|
| IEEE Sensors Journal | ~4.3 | Q1/Q2 边界 | 强应用 + 实验充分 | ★★★（稳妥） |
| Signal Processing (Elsevier) | ~3.4 | Q2 | 偏算法/理论 | ★★★（稳妥） |
| Digital Signal Processing | ~2.9 | Q2 | 偏方法创新 | ★★（友好） |
| IEEE Systems Journal | ~4.0 | Q2 | 系统级方案 | ★★★（稳妥） |
| IEEE Trans. Veh. Tech. | ~6.1 | Q2/Q1 边界 | 严格理论 + 实验 | ★★★★（冲刺） |

**对标 SOTA 论文**：

- Wen, F. et al. "Tensor-Based Channel Estimation for Hybrid IRS-Assisted MIMO-OFDM," IEEE TWC, 2021.
- Wei, Y. et al. "Deep Learning-Based Joint Channel Estimation and Symbol Detection," IEEE JSAC, 2021.
- Liu, F. et al. "Integrated Sensing and Communications: Toward Dual-Functional Wireless Networks," IEEE JSAC, 2022.
- He, H. et al. "Model-Driven Deep Learning for MIMO Detection," IEEE TSP, 2020.

---

## 2  系统与信号模型

### 2.1 OFDM-MIMO ISAC 收发信号模型

考虑一个收发共置（mono-static）的 OFDM-MIMO ISAC 系统：

- 发射阵列：$N_t$ 元 ULA（间距 $d_t = \lambda/2$）
- 接收阵列：$N_r$ 元 ULA（间距 $d_r = \lambda/2$）
- 子载波数：$K$，子载波间隔 $\Delta f$
- 每帧 OFDM 符号数：$M$，符号周期 $T_s$
- 载波频率：$f_c$（毫米波频段，如 28/77/140 GHz）

发射端在第 $k$ 个子载波、第 $m$ 个 OFDM 符号上发射符号 $\mathbf{x}[k,m] \in \mathbb{C}^{N_t}$，则接收信号为：

$$
\mathbf{y}[k,m] = \sum_{l=1}^{L} \alpha_l\, \mathbf{a}_R(\phi_l)\, \mathbf{a}_T^H(\theta_l)\, \mathbf{x}[k,m]\, e^{-j2\pi k \Delta f \tau_l}\, e^{j2\pi m T_s \nu_l} + \mathbf{n}[k,m]
$$

其中：
- $L$：有效路径/目标数（稀疏，$L \ll N_t N_r K$）
- $\alpha_l$：第 $l$ 条路径复增益
- $\theta_l, \phi_l$：到达角 AoA、出发角 AoD
- $\tau_l$：时延（对应目标距离 $R_l = c\tau_l/2$）
- $\nu_l$：多普勒频移（对应目标径向速度 $v_l = c\nu_l/(2f_c)$）
- $\mathbf{a}_T, \mathbf{a}_R$：发射/接收阵列响应矢量
- $\mathbf{n}[k,m]$：复高斯白噪声 $\mathcal{CN}(0, \sigma^2 \mathbf{I})$

### 2.2 张量化信号模型

将接收信号在 $\{N_r, K, M, N_t\}$ 四个维度上组织为 4 阶张量 $\mathcal{Y} \in \mathbb{C}^{N_r \times K \times M \times N_t}$，可证明：

$$
\mathcal{Y} = \sum_{l=1}^{L} \alpha_l\, \mathbf{a}_R(\phi_l) \circ \mathbf{p}(\tau_l) \circ \mathbf{d}(\nu_l) \circ \mathbf{a}_T^*(\theta_l) + \mathcal{N}
$$

其中 $\circ$ 表示矢量外积；

$$
\mathbf{p}(\tau_l) = [1, e^{-j2\pi\Delta f \tau_l}, \dots, e^{-j2\pi(K-1)\Delta f \tau_l}]^T
$$
$$
\mathbf{d}(\nu_l) = [1, e^{j2\pi T_s \nu_l}, \dots, e^{j2\pi(M-1)T_s \nu_l}]^T
$$

这是一个**带噪声的低秩 CP 分解**结构，$L$ 即为张量的 CP 秩。

### 2.3 稀疏字典与原子化表示

在角度域、时延域、多普勒域上构造过完备字典：

- $\mathbf{A}_R \in \mathbb{C}^{N_r \times G_\phi}$：接收角度字典（$G_\phi$ 个网格点）
- $\mathbf{A}_T \in \mathbb{C}^{N_t \times G_\theta}$：发射角度字典
- $\mathbf{P} \in \mathbb{C}^{K \times G_\tau}$：时延字典
- $\mathbf{D} \in \mathbb{C}^{M \times G_\nu}$：多普勒字典

则信号可表示为：

$$
\mathcal{Y} = \mathcal{G} \times_1 \mathbf{A}_R \times_2 \mathbf{P} \times_3 \mathbf{D} \times_4 \mathbf{A}_T^* + \mathcal{N}
$$

其中 $\mathcal{G} \in \mathbb{C}^{G_\phi \times G_\tau \times G_\nu \times G_\theta}$ 为**稀疏核张量**，仅有 $L$ 个非零元，每个非零元对应一条物理路径。$\times_n$ 表示张量第 $n$ 模乘积。

**这是论文最核心的统一模型——信道估计等价于估计稀疏核张量 $\mathcal{G}$，而 $\mathcal{G}$ 的非零位置直接给出目标参数。**

---

## 3  问题建模

### 3.1 联合优化问题

给定接收张量 $\mathcal{Y}$ 与导频图样 $\mathcal{X}$，联合估计稀疏核张量 $\mathcal{G}$：

$$
\min_{\mathcal{G}} \; \|\mathcal{Y} - \mathcal{G} \times_1 \mathbf{A}_R \times_2 \mathbf{P} \times_3 \mathbf{D} \times_4 \mathbf{A}_T^* \cdot \mathcal{X}\|_F^2 + \lambda \|\mathcal{G}\|_0
$$

由于 $\ell_0$ 范数 NP-hard，常用 $\ell_1$ 松弛或贪婪算法（OMP 类）求解。

### 3.2 与已有方法的关键差异

| 方法类别 | 代表算法 | 局限 |
|---------|---------|------|
| 经典 CS | OMP / SOMP / CoSaMP | 矩阵化损失张量结构、依赖网格 |
| 张量 CS | T-OMP, Tensor-ALS | 不学习字典原子参数 |
| 数据驱动 DL | ChannelNet, SF-CNN | 黑箱，无物理解释 |
| CS+DL 级联（你的毕设） | B-OMP + CAE | 阶段独立，未联合优化 |
| **本文 T-OMP-Net** | **深度展开 + 可学习字典** | **统一模型驱动 + 数据驱动** |

---

## 4  核心算法设计

### 4.1 张量 OMP（T-OMP）基础算法

将四维稀疏核张量 $\mathcal{G}$ 向量化为 $\mathbf{g} \in \mathbb{C}^{G_\phi G_\tau G_\nu G_\theta}$，问题转化为：

$$
\min_{\mathbf{g}} \|\mathbf{y} - \mathbf{\Phi}\mathbf{g}\|_2^2 \quad s.t. \quad \|\mathbf{g}\|_0 \leq L
$$

其中 $\mathbf{\Phi} = (\mathbf{A}_T^* \otimes \mathbf{D} \otimes \mathbf{P} \otimes \mathbf{A}_R)\cdot \mathbf{X}_{eq}$ 为感知矩阵，$\otimes$ 为 Kronecker 积。

**T-OMP 算法流程**：

```
输入：观测张量 Y，字典 {A_R, P, D, A_T}，稀疏度 L_max
初始化：残差 R_0 = Y，支撑集 S = ∅
For t = 1, ..., L_max:
   1. 计算各模式下原子相关性：c_i = <vec(R_{t-1}), φ_i> / ||φ_i||
   2. 选择最大相关原子：i_t = argmax_i |c_i|
   3. 更新支撑集：S = S ∪ {i_t}
   4. LS 求解：g_S = (Φ_S^H Φ_S)^{-1} Φ_S^H y
   5. 残差更新：R_t = Y - reshape(Φ_S g_S)
   6. 若 ||R_t||_F^2 / ||Y||_F^2 < ε，break
输出：稀疏核张量 G_hat
```

### 4.2 T-OMP-Net 深度展开网络

将上述迭代过程展开为 $T$ 层网络，每层为一个可学习模块：

**第 $t$ 层结构（Layer $t$）：**

```
输入：上一层残差 R_{t-1}，当前支撑集 S_{t-1}
─────────────────────────────────────
步骤 1（相关性计算 + 注意力加权）：
   c = ATTN_t(Φ^H × vec(R_{t-1}))    // 多头自注意力，捕捉跨维度依赖

步骤 2（学习阈值 soft-shrinkage）：
   c_tilde = sign(c) ⊙ ReLU(|c| - λ_t)    // λ_t 可学习

步骤 3（Top-K 选择 + 支撑集扩展）：
   S_t = S_{t-1} ∪ TopK_t(c_tilde)

步骤 4（带残差的 LS 更新）：
   g_t = (Φ_{S_t}^H Φ_{S_t} + μ_t I)^{-1} Φ_{S_t}^H y    // μ_t 可学习正则项

步骤 5（残差更新 + 残差校正）：
   R_t = Y - Φ_{S_t} g_t + W_t × (R_{t-1} - R_{t-2})    // W_t 为残差校正卷积层
─────────────────────────────────────
输出：R_t, S_t, g_t
```

**可学习参数列表**：

| 参数 | 维度 | 物理含义 |
|------|------|---------|
| $\{\lambda_t\}_{t=1}^T$ | $T$ | 各层阈值 |
| $\{\mu_t\}_{t=1}^T$ | $T$ | 各层正则系数 |
| $\{W_t\}_{t=1}^T$ | 卷积核 | 残差校正网络 |
| $\Delta\mathbf{A}_R, \Delta\mathbf{P}, \Delta\mathbf{D}, \Delta\mathbf{A}_T$ | 字典 | **字典原子精细化修正**（关键创新） |
| $\text{ATTN}_t$ | Multi-head | 跨维度依赖 |

可学习字典 $\tilde{\mathbf{A}}_R = \mathbf{A}_R + \Delta\mathbf{A}_R$ 实现 **off-grid 修正**，缓解传统 CS 网格离散化误差。

### 4.3 端到端联合训练

**损失函数（三项联合）：**

$$
\mathcal{L} = \underbrace{\frac{\|\hat{\mathcal{H}} - \mathcal{H}\|_F^2}{\|\mathcal{H}\|_F^2}}_{\mathcal{L}_{\text{NMSE}}} + \beta_1 \underbrace{\sum_l \rho(|\hat{\tau}_l - \tau_l|, |\hat{\nu}_l - \nu_l|, |\hat{\theta}_l - \theta_l|)}_{\mathcal{L}_{\text{Param}}} + \beta_2 \underbrace{\|\hat{\mathcal{G}}\|_1}_{\mathcal{L}_{\text{Sparse}}}
$$

- $\mathcal{L}_{\text{NMSE}}$：信道重建误差（通信侧指标）
- $\mathcal{L}_{\text{Param}}$：雷达参数误差（感知侧指标，$\rho$ 为 Huber 损失抗野值）
- $\mathcal{L}_{\text{Sparse}}$：稀疏正则

**训练策略**：

1. 预训练阶段：在合成 3GPP CDL 数据上训练 50 epoch，AdamW 优化器，学习率 $1\times 10^{-3}$，warm-up + cosine decay
2. 微调阶段：在 DeepMIMO 数据上微调 20 epoch，学习率 $1\times 10^{-4}$
3. 课程学习：先 SNR=20dB，逐步降到 -5dB，提升鲁棒性

### 4.4 目标参数提取

从估计的稀疏核张量 $\hat{\mathcal{G}}$ 中提取目标参数：

1. 阈值化获得非零元位置 $\{(i_\phi^l, i_\tau^l, i_\nu^l, i_\theta^l)\}_{l=1}^{\hat{L}}$
2. 距离：$\hat{R}_l = c \hat{\tau}_l / 2$
3. 径向速度：$\hat{v}_l = c \hat{\nu}_l / (2f_c)$
4. 角度：直接从字典网格读取，并由可学习 $\Delta\mathbf{A}$ 修正

---

## 5  理论分析

### 5.1 Cramér-Rao Lower Bound (CRLB)

**目标**：给出参数 $\boldsymbol{\eta} = [\alpha_l, \theta_l, \phi_l, \tau_l, \nu_l]_{l=1}^L$ 估计的理论下界。

Fisher 信息矩阵：

$$
[\mathbf{F}(\boldsymbol{\eta})]_{ij} = \frac{2}{\sigma^2} \Re\left\{ \frac{\partial \boldsymbol{\mu}^H}{\partial \eta_i} \frac{\partial \boldsymbol{\mu}}{\partial \eta_j} \right\}
$$

其中 $\boldsymbol{\mu} = \mathbb{E}[\mathbf{y}]$。对每个参数推导偏导（共 $5L$ 个），构造完整 FIM，CRLB 为 $\mathbf{F}^{-1}$ 对角元。

**推导要点**：
- 角度偏导引入阵列梯度 $\partial \mathbf{a}_R/\partial \phi$
- 时延偏导引入 $-j2\pi k\Delta f$ 因子
- 多普勒偏导引入 $j2\pi m T_s$ 因子

将作为图 NMSE-vs-SNR 曲线的下界绘出，直观展示算法接近最优。

### 5.2 收敛性分析

借鉴 Chen et al. (2018) 与 Liu et al. (2019) 关于 LISTA 收敛性的工作，T-OMP-Net 可视为带学习参数的 ISTA/OMP 混合迭代。

**主要结论**（陈述要严谨，详细证明放附录）：

- 假设：感知矩阵 $\mathbf{\Phi}$ 满足 $L$ 阶 RIP（限制等距性）常数 $\delta_{2L} < \sqrt{2}-1$
- 在合理参数选择下，T-OMP-Net 的输出 $\hat{\mathbf{g}}^{(T)}$ 满足：
$$
\|\hat{\mathbf{g}}^{(T)} - \mathbf{g}^*\|_2 \leq C_1 q^T \|\mathbf{g}^*\|_2 + C_2 \|\mathbf{n}\|_2
$$
其中 $0 < q < 1$ 为收缩因子，与可学习阈值 $\lambda_t$ 相关。
- **线性收敛速率**，且数据驱动的 $\lambda_t$ 可获得比固定阈值更小的 $q$。

### 5.3 复杂度分析

| 算法 | FLOPs（每帧） | 参数量 | 内存 |
|------|--------------|-------|------|
| LS | $O(K N_r N_t)$ | 0 | 低 |
| OMP | $O(L K N_r N_t G)$ | 0 | 中 |
| LDAMP | $O(T_{\text{lay}} G^2)$ | $\sim 10^6$ | 高 |
| ChannelNet | $O(C_h K^2)$ | $\sim 10^7$ | 高 |
| **T-OMP-Net** | $O(T L G \log G)$（FFT 加速字典乘法） | $\sim 10^5$ | **低** |

**关键卖点**：参数量比 ChannelNet 少 2 个数量级，便于车载等边缘部署。

---

## 6  仿真与实验设计

### 6.1 仿真平台

- 语言：MATLAB R2024a + Python 3.10 + PyTorch 2.2
- 硬件：单卡 RTX 4090（24GB）或 A100；CPU baseline 用 Intel i9
- 张量运算库：tensorly（Python）或自实现

### 6.2 仿真参数矩阵

| 参数 | 值 |
|------|---|
| 载波频率 $f_c$ | 28 GHz / 77 GHz |
| 带宽 | 100 MHz / 400 MHz |
| 子载波数 $K$ | 256 |
| OFDM 符号数 $M$ | 64 |
| 发射天线 $N_t$ | 16 / 32 |
| 接收天线 $N_r$ | 64 / 128 |
| 路径/目标数 $L$ | 3 ~ 10 |
| SNR 范围 | -10 ~ 30 dB |

### 6.3 信道与数据集（覆盖度是 Q2 必须）

1. **3GPP TR 38.901 CDL-A / CDL-C / CDL-D**（不同 NLOS/LOS 场景）
2. **QuaDRiGa**（射线追踪，3D 大气衰减）
3. **DeepMIMO**（公开数据集，O1/I3 场景，准实测）
4. **自定义稀疏多目标场景**（雷达侧验证）

### 6.4 对比基线（必须有 7 个以上）

| 类别 | 基线算法 |
|------|---------|
| 传统 | LS, LMMSE |
| 经典 CS | OMP, SOMP, CoSaMP |
| 贝叶斯 | SBL, VAMP |
| 数据驱动 DL | ChannelNet (Soltani 2019), SF-CNN (He 2018) |
| 模型驱动 DL | LDAMP (Metzler 2017), LISTA-Net |
| 张量类 | Tensor-ALS, T-HOSVD |
| **本文** | **T-OMP-Net** |

### 6.5 评价指标

- **通信侧**：NMSE (dB)、BER、谱效（spectral efficiency）
- **感知侧**：距离 RMSE (m)、速度 RMSE (m/s)、角度 RMSE (deg)、目标检测概率 $P_d$、虚警率 $P_{fa}$
- **系统侧**：FLOPs、参数量、推理延迟（ms）、显存占用

### 6.6 鲁棒性实验（关键，审稿人必看）

1. **低 SNR**：SNR ∈ [-10, 0] dB 下的性能曲线
2. **少导频**：导频密度 ↓ 50% / 75%
3. **未知 $L$**：路径数失配下的算法表现
4. **阵列误差**：天线增益失配 ±1dB、相位误差 ±5°
5. **量化误差**：1-bit / 4-bit ADC
6. **高速移动**：速度 0 ~ 500 km/h
7. **泛化能力**：CDL-A 训练 → CDL-D 测试

### 6.7 消融实验（必做）

- 仅 T-OMP（无网络展开）
- 网络展开但不学字典
- 不带 attention
- 单一 loss vs 三项联合 loss
- 不同展开层数 $T \in \{4,6,8,10\}$

---

## 7  实施计划

### 7.1 时间节点（6 个月）

| 阶段 | 时长 | 关键任务 | 产出 |
|------|------|---------|------|
| M1 文献+建模 | 4 周 | 阅读 30+ 篇近 3 年 SOTA，完成信号模型推导 | 信号模型 .tex 章节 |
| M2 基础算法 | 3 周 | 实现 T-OMP、所有 baseline | MATLAB/Python 代码库 |
| M3 网络设计 | 4 周 | T-OMP-Net 架构搭建、调试 | PyTorch 模型 |
| M4 训练调优 | 3 周 | 在 CDL/DeepMIMO 上训练 | 模型权重 + 训练日志 |
| M5 理论推导 | 3 周 | CRLB、收敛性、复杂度推导 | 理论章节 .tex |
| M6 全量实验 | 4 周 | 7 类 baseline × 4 信道 × 6 鲁棒性场景 | 全部图表 |
| M7 论文撰写 | 3 周 | 全英文论文 + 投稿 | 投稿 PDF |
| M8 回复审稿 | 2 周（含返修） | Response Letter | 录用 |

### 7.2 开发模块顺序

```
信号模型仿真 (M2 周1)
    ↓
LS/OMP/SOMP baseline (M2 周2)
    ↓
T-OMP 基础算法 (M2 周3)
    ↓
T-OMP-Net 单层 prototype (M3 周1)
    ↓
完整网络 + attention (M3 周2-3)
    ↓
训练 pipeline + 数据加载 (M3 周4)
    ↓
SOTA baselines (LDAMP/ChannelNet) (M4 周1)
    ↓
全量训练 + 调参 (M4 周2-3)
    ↓
理论推导 + 鲁棒性实验 (M5-M6)
```

### 7.3 风险与备份方案

| 风险 | 应对 |
|------|------|
| T-OMP-Net 收敛差/精度不达预期 | 简化为 2D 张量（角度-时延），降阶仍可发 Q2 |
| CRLB 推导复杂超出预期 | 仅推导关键参数（时延+角度），其他给数值 CRLB |
| DeepMIMO 数据预处理耗时 | 优先用 3GPP CDL，DeepMIMO 作为 transfer 验证 |
| 与 SOTA 拉不开差距 | 强化鲁棒性 + 复杂度优势，仍可投 Q2（应用类期刊） |
| 投稿被拒 | 准备 3 个备选期刊清单按梯度投稿 |

---

## 8  投稿策略

### 8.1 期刊梯度

**首投**：Signal Processing (Elsevier)（偏方法创新，Q2 稳，审稿 3-5 月）
**次投**：IEEE Sensors Journal（重应用，强调 ISAC 雷达感知，Q1/Q2 边界）
**再投**：Digital Signal Processing (Elsevier)（友好，Q2）
**冲刺备选**：IEEE TVT（若实验扎实，可冲刺）

### 8.2 写作要点

1. **Abstract 4 句话结构**：背景 → 已有方法不足 → 本文方法 → 主要数值结果
2. **Introduction 5 段式**：领域背景 → 应用驱动 → 已有工作 3 类划分 → 已有工作不足 → 本文贡献（C1/C2/C3 bullet 化）
3. **图表 ≥ 15 个**：系统框图、网络结构图、消融柱状图、NMSE-SNR 曲线、参数 RMSE 曲线、复杂度雷达图、鲁棒性热力图等
4. **数学符号严格统一**，建议附符号表
5. **代码开源**：GitHub 仓库链接，提升录用概率与引用

### 8.3 审稿人可能的关键问题及预案

| 问题 | 预案 |
|------|------|
| Q：与已有 LISTA/LDAMP 区别？ | A：本文核心是张量结构 + 可学习字典 + ISAC 联合 loss，三者均为新增 |
| Q：稀疏度 $L$ 实际未知怎么办？ | A：提供路径数估计方案（基于残差能量门限），并做未知 $L$ 鲁棒性实验 |
| Q：是否在实际硬件验证？ | A：用 DeepMIMO 射线追踪准实测数据；指出未来工作可结合 TI AWR2243 EVM |
| Q：计算复杂度是否真的低？ | A：给出 FLOPs 详细推导 + 实测推理延迟表 |
| Q：CRLB 推导是否严格？ | A：附录给完整 FIM 元素，参考 Bekkerman & Tabrikian (2006) 推导框架 |
| Q：训练数据需求是否过大？ | A：做 few-shot 实验（500/1000/5000 样本对比），论证小样本可行性 |

---

## 9  下一步立即可做的事

1. **本周**：建 GitHub 仓库，把毕设代码迁移整理
2. **下周**：阅读 Wen 2021 (IEEE TWC) + Liu 2022 (JSAC ISAC overview) + He 2020 (TSP) 3 篇核心文献
3. **第 3 周**：完成新信号模型 MATLAB 仿真，跑通 LS+OMP baseline，对比毕设结果
4. **第 4 周**：开始 T-OMP 编码
5. 并行：建议联系导师，争取实验室 GPU 资源（4090 或更高）

---

## 10  参考文献清单（首批必读 15 篇）

1. Heath, R. W. et al. "An Overview of Signal Processing Techniques for Millimeter Wave MIMO Systems," IEEE JSTSP, 2016.
2. Liu, F. et al. "Integrated Sensing and Communications: Toward Dual-Functional Wireless Networks for 6G and Beyond," IEEE JSAC, 2022.
3. Wen, F. et al. "Tensor-Based Channel Estimation for Hybrid IRS-Assisted MIMO-OFDM," IEEE TWC, 2021.
4. He, H. et al. "Model-Driven Deep Learning for MIMO Detection," IEEE TSP, 2020.
5. Metzler, C. A. et al. "Learned D-AMP: Principled Neural Network Based Compressive Image Recovery," NeurIPS, 2017.
6. Gregor, K. & LeCun, Y. "Learning Fast Approximations of Sparse Coding," ICML, 2010.
7. Chen, X. et al. "Theoretical Linear Convergence of Unfolded ISTA and Its Practical Weights and Thresholds," NeurIPS, 2018.
8. Soltani, M. et al. "Deep Learning-Based Channel Estimation," IEEE Comm. Letters, 2019.
9. Wei, Y. et al. "Deep Learning-Based Joint Channel Estimation and Symbol Detection for OFDM," IEEE JSAC, 2021.
10. Mishra, K. V. et al. "Toward Millimeter-Wave Joint Radar Communications," IEEE Signal Processing Magazine, 2019.
11. Bekkerman, I. & Tabrikian, J. "Target Detection and Localization Using MIMO Radars and Sonars," IEEE TSP, 2006.
12. Roemer, F. et al. "Tensor-Based Channel Estimation and Iterative Refinements for Two-Way Relaying," IEEE TSP, 2014.
13. Wang, X. et al. "Compressed Sensing-Based Channel Estimation for mmWave MIMO Systems," IEEE TWC, 2018.
14. Dong, P. et al. "Deep CNN-Based Channel Estimation for mmWave Massive MIMO Systems," IEEE JSTSP, 2019.
15. 3GPP TR 38.901 v17.0.0, "Study on channel model for frequencies from 0.5 to 100 GHz," 2022.

---

**——本设计报告完——**

如需细化任何一节（如 T-OMP-Net 网络层的 PyTorch 伪代码、CRLB 公式完整推导、或某个特定鲁棒性实验设计），可随时进一步展开。
