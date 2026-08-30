# v2.2 方向重新评估：SOTA 对标、可行性、创新性与下一步详细计划

> 评估时间：2026-06-24
> 评估方法：8 组 WebSearch 横扫 2024-2026 SCI 文献（IEEE Xplore / arXiv / Elsevier / MDPI / Springer / SIAM），覆盖 v2.2 §2.4 全部 4 类 + 4 个交叉方向，命中实证文献 60+ 篇，重点精读 8 篇与 v2.2 最贴近的工作。
> 评估范围：v2.2 大纲的方向正确性、实验可操作性、与 2024-2026 SOTA 的创新差异度、目标期刊命中率重估。

---

## 1. 关键发现总览（先看结论）

| 维度 | v2.1 立项时（2025） | v2.2 起草时（2025-Q4） | **当前实证（2026-06）** |
|---|---|---|---|
| 方向正确性 | ✓ 切中 6G/ISAC 主线 | ✓ 仍正确 | ✓ **正确但已非蓝海**：deep unfolding × ISAC × 张量 已是 2025 主流 |
| 实验可操作性 | 中（接口未闭合） | 中（六组 smoke 已落地） | ✓ **可操作**：MOMPnet/DDA-Net/Tensor-ISAC 三系开源/公开方法可对照实现 |
| 创新性（独立看） | 4 要素融合"未充分研究" | 同 | **下降**：单要素均已有 SCI 文献；Tensor-OMP 展开 + 物理 off-grid 已被 MOMPnet 几乎完整覆盖 |
| 价值性 | 高（6G+车载/低空雷达） | 高 | 高（无变化）— ISAC 是 5G-A/6G PHY 主线 |
| Signal Processing 命中率（v2.2 自估 75%） | — | 75% | **重估 35-45%**：除非加强差异度，否则 Q2 投稿风险显著 |
| DSP（Elsevier）命中率（v2.2 自估 85%） | — | 85% | **重估 55-65%** |

**最关键的红色发现**（直接威胁 v2.2 创新性的两篇）：

1. **MOMPnet（arXiv 2601.10771，2026-01）—"Physically constrained unfolded multi-dimensional OMP for large MIMO systems"**
   - 已实现：unfolded 多维 OMP + 物理约束 + 可学习字典 + mmWave 信道估计 + 定位
   - 与 v2.2 §4（T-OMP-Net）核心架构高度重合
   - 唯一缺：v2.2 增加的"显式 ISAC 双输出 + Hungarian permutation-invariant + Lemma 1 + Kruskal 消融"
2. **DDA-Net（arXiv 2604.05389，2026-04）—"Accurate TDD Channel Estimation via Deep Unfolding the Doppler-Delay-Angle"**
   - 已实现：3D Doppler-Delay-Angle 深度展开 + ADMM unrolling + 延迟域过采样 + off-grid 缓解
   - 在 QuaDRiGa UMa-NLOS 上 10 dB SNR 提升 NMSE 5 dB，3GPP CDL-B 零样本 1.5 dB lead
   - 它做的是 TDD 通信侧；不做 ISAC、不做 Hungarian、不做 5L CRLB；这是 v2.2 当前唯一明确的差异口

如果 v2.2 不主动针对这两篇做差异化叙述并写入 §2.4，审稿人会直接卡"contribution 已被覆盖"。

---

## 2. SOTA 对标表（取代 v2.2 §2.4 占位）

下表填入实证文献，按 v2.2 §2.4 的五列勾选规则评分。

| 工作 | 年份 | 张量结构 | Deep Unfolding | 物理 off-grid | ISAC 联合损失 | Hungarian 配对 | 5L CRLB / 形式化定理 |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **MOMPnet** (arXiv 2601.10771) | 2026 | △ 多维分离字典 | ✓ unfolded | ✓ 物理结构 | ✗ 通信+定位 | ✗ | ✗ |
| **DDA-Net** (arXiv 2604.05389) | 2026 | ✓ 3D 张量 | ✓ ADMM unroll | ✓ 延迟过采样 + 残差 | ✗ TDD comms | ✗ | ✗ |
| **Unified Tensor ISAC** (arXiv 2401.01738) | 2024 | ✓ CP | ✗ | ✗ | ✓ | ✗ | △ |
| **Near-Field Tensor MIMO-OFDM ISAC** (Sensors 2025, 25/16/5050) | 2025 | ✓ 3 阶张量 + Vandermonde | ✗ | ✗ | ✓ | ✗ | △ Kruskal |
| **AFDM-ISAC Angle-Delay-Doppler** (arXiv 2504.06567) | 2025 | ✓ CP + spatial smoothing | ✗ | △ Vandermonde fractional | ✓ | ✗ | △ |
| **OTFS-ISAC ADMM-Net** (WCNC 2024, 10571155) | 2024 | ✗ 矩阵 | ✓ ADMM unroll | △ on/off-grid 分离 | ✓ | ✗ | ✗ |
| **JCAS Hybrid BF Unfolding** (JSTSP 2024, 10684532) | 2024 | ✗ | ✓ PGA unroll | n/a | ✓ comm-sens 权衡 | ✗ | ✗ |
| **MambaCSP / MambaNet** | 2025-26 | ✗ | ✗（attention+SSM） | ✗ | ✗ | ✗ | ✗ |
| **DL-driven Atomic Norm** (Electronics 2024, 15/7/1461) | 2024 | ✗ | △ | ✓ gridless | ✗ | ✗ | ✗ |
| **Tensor TVChannel** (arXiv 2403.02942) | 2024 | ✓ CP | ✗ | ✗ | ✗ | ✗ | ✗ |
| **Deep Unfolding Survey** (arXiv 2502.05952) | 2025 | n/a 综述 | ✓ | — | — | — | — |
| **本文 T-OMP-Net（拟）** | 2026 | ✓ CP/Tucker | ✓ Tensor-OMP unroll | ✓ tanh 物理 bounded | ✓ comm+sens 双输出 | ✓ | ✓ Lemma 1 + 5L CRLB |

读法：
- v2.2 仍是表中**唯一全 ✓ 的方法**——但 5 个 ✓ 中，前三个（张量结构 / Deep Unfolding / 物理 off-grid）都被 MOMPnet 或 DDA-Net 单独占了。
- 真正独占的差异点只剩 **ISAC 联合损失 + Hungarian permutation-invariant + Lemma 1 形式化界 + 5L 联合 CRLB**——必须把论文叙述、贡献 bullet 与实验设计全部围绕这 4 点重写。

---

## 3. 方向正确性评定

### 3.1 大方向（结论：✓ 正确，但已不是蓝海）

证据：
- 2025 综述 "Comprehensive Review of Deep Unfolding for Next-Generation Wireless" (arXiv 2502.05952) 明确把"ISAC + 深度展开"列为 6G 主流方向之一。
- IEEE JSTSP 2024 已发表 JCAS hybrid beamforming via deep unfolding（NIH ID 10684532）。
- WCNC 2024 已发表 OTFS-ISAC ADMM-Net。
- arXiv 2411.17747（2024）"Deep Unfolding-Empowered MmWave Massive MIMO Joint Communications and Sensing" 直接是同一方向。
- 张量化 ISAC 信道-参数统一估计在 arXiv 2401.01738 已经发表。

→ 大方向正确但**已不是 v2.0 立项时的空白领域**。v2.2 §1 段落 4 把"绝对首次"改成"四要素融合仍未充分研究"是非常正确的预判。但今天的措辞还需要再退半步：明确说"本文不主张要素层面的首创，而主张物理约束 Tensor-OMP 展开 + Hungarian-ISAC 联合损失 + Lemma 1 这一具体配方的贡献"。

### 3.2 子方向

| 子方向 | 是否仍正确 | 备注 |
|---|---|---|
| §3.1 单站 MIMO-OFDM FDMA + 虚拟阵列 | ✓ | v2.2 §3.1.1 trade-off 表足以应对 |
| §3.3 3D 稀疏张量建模（CP/Tucker） | ✓ | 主流；但需借鉴 arXiv 2504.06567 的 Vandermonde 结构，否则容易被"未利用 Vandermonde"质疑 |
| §4 Tensor-OMP 展开 | ⚠ 已被 MOMPnet 部分覆盖 | 必须强调"OMP-domain 而非 ADMM-domain"+"模板带物理 bound 的 off-grid"双重定位 |
| §4.3 物理 off-grid | ⚠ 已被 MOMPnet 物理结构覆盖 | 区别：MOMPnet 学**整个字典**，T-OMP-Net 仅学**网格内偏移** $\delta\in(-\Delta/2,\Delta/2)$；后者可证（Lemma 1）、前者不可证。这是真正的卖点 |
| §4.4.1 Hungarian permutation-invariant ISAC 损失 | ✓ **独占** | 检索没有命中相同设定；保留为核心创新 |
| §5.1.1 Off-Grid Mismatch Lemma | ✓ **独占** | Lemma 1 在我们检索的 SCI 文献里没有等价命题；保留为形式化贡献 |
| §5.2 5L 联合 CRLB | ✓ | 多数现有 tensor ISAC 工作只给单参 CRLB，5L 完整 FIM 仍稀缺 |
| §6.2 Set E DeepMIMO 跨场景 | ✓ | DDA-Net 用的是 QuaDRiGa+CDL-B；本文用 DeepMIMO O1/I3 + CDL-A/C/D，覆盖面更广 |
| §6.5.13 过采样+Kruskal 消融 | ✓ | Sensors 2025 25/16/5050 给了 Kruskal 但未做过采样消融；这部分仍独占 |

### 3.3 必须撤掉的旧措辞

- "首次提出 3D 稀疏张量 ISAC 建模" —— ✗ 已被 2401.01738 (2024) 占。
- "首次应用 Tensor-OMP 展开" —— ✗ MOMPnet 已实现多维 OMP unfolding。
- "off-grid refinement 用于深度展开" —— ✗ DDA-Net 已有 delay-domain 残差修正。

替代措辞建议（写入 §1 段落 4 与 §2.5）：

> "本文不主张张量 ISAC 建模、深度展开 OMP、或 off-grid 字典修正中任一要素的首创性。已有工作如 MOMPnet[ref]、DDA-Net[ref]、Unified Tensor ISAC[ref] 分别在多维 OMP unfolding、三维角-时延-多普勒展开、张量 ISAC 联合估计三方向取得了重要进展。本文的核心贡献在于（1）将物理约束的 bounded off-grid refinement 与 Tensor-OMP unfolding 同时纳入展开网络，提供可证的离网修正误差界（Lemma 1），（2）以 Hungarian permutation-invariant 联合损失贯通通信信道估计与雷达目标参数估计，使两侧梯度共享；（3）通过 Kruskal 可辨识性消融把字典维度选择从工程经验上升为可解释的设计约束。"

---

## 4. 实验可操作性评定

### 4.1 总体结论：✓ 可操作，但需重置时间预算

按 v2.2 Phase 排期 + 当前 0 行 T-OMP-Net 实现代码 + 2 篇极近期对照工作（MOMPnet/DDA-Net）需要复现作为 baseline，**原 8 个月排期偏紧**。需要调整。

### 4.2 分项可行性

| 实验 | 可行性 | 关键依赖 | 建议处理 |
|---|---|---|---|
| Set A 自定义 ISAC 多目标 pipeline | ✓ 高 | 仅需 MATLAB / PyTorch | P0；2-3 周可达 |
| Tensor-OMP baseline | ✓ 高 | 标准 CP-OMP，文献成熟 | P0；1-2 周 |
| T-OMP-Net 最小版（Teacher Forcing → Hard） | ✓ 中-高 | 课程训练可能不稳定 | P1；4-6 周（含调参） |
| 物理 bounded off-grid（tanh 重参数化） | ✓ 高 | smoke 已验证趋势 | P1；2 周 |
| Hungarian + 联合损失 | ✓ 高 | DETR 实现可移植 | P1；2 周 |
| 5L 联合 CRLB | ✓ 高 | FIM 可数值差分交叉验证 | P2；2 周 |
| Lemma 1 附录证明 | ✓ 高 | 草图已在 v2.2 §5.1.1 | P2；3-5 天 |
| 3GPP CDL-A/C/D | ✓ 高 | 需 MATLAB 5G Toolbox `nrCDLChannel` | P2；2 周 |
| DeepMIMO Set E (O1/I3) | ⚠ 中 | 数据下载 + 5G Toolbox license 阻塞 | P2；先 audit→下载→跑；预留 4 周缓冲 |
| §6.5.13 过采样 + Kruskal 退化 | ✓ 高 | 已有 smoke；扩到论文尺度 | P2；2 周 |
| 对照 MOMPnet（新增 baseline） | ⚠ 中 | 需复现其多维 OMP unfolding | P3；3-4 周 |
| 对照 DDA-Net（新增 baseline） | ⚠ 中 | ADMM unrolling 3D；按论文复现 | P3；3-4 周 |
| MATLAB 5G Toolbox license 不可得 | 阻塞 | 备案：自实现 5G NR 链路或转用 QuaDRiGa | 需要立刻确认 |

### 4.3 关键工程红线（防止重蹈本科原型覆辙）

usable_content_inventory.md 已记录本科原型 5 项接口故障。**新 pipeline 必须**：
- 使用 PyTorch（建议）或 MATLAB Deep Learning Toolbox，单一框架贯通 baseline + 展开网络。
- Config / Modules / Algorithms 接口全部由数据类（dataclass / struct）声明，不允许字符串字段约定。
- 单元测试：每个模块独立可跑 + 整体 pipeline 5 SNR × 3 baseline × 100 蒙特卡洛冒烟。
- 随机种子 / 配置 hash 写入每个 results/*/summary.md，保证复现。

---

## 5. 创新性与价值性评定

### 5.1 创新性矩阵（与最近 SOTA 对齐后的实际差异）

| 候选贡献 | 与 MOMPnet 差异 | 与 DDA-Net 差异 | 与 Unified Tensor ISAC 差异 | 最终独占度 |
|---|---|---|---|---|
| Tensor-OMP unfolding 架构 | 形式接近，OMP-domain vs 多维 OMP | 显著（OMP vs ADMM） | 显著（unfolding vs 纯 CP） | 中 |
| **物理 bounded off-grid（含 Lemma 1）** | MOMPnet 学整个字典，无界，无证明 | DDA-Net 残差修正无形式界 | 无 off-grid 概念 | **高** |
| **Hungarian + 联合 ISAC 损失** | 无 ISAC、无配对 | 无 ISAC、无配对 | 有联合但无 Hungarian | **高** |
| **5L 联合 CRLB + 渐近紧致性** | 无 | 无 | 无完整 5L FIM | **高** |
| Kruskal 可辨识性 + 过采样消融 | 无 | 无 | Sensors 2025 有 Kruskal、无过采样 | 中-高 |
| FDMA/DDM/TDM SE trade-off 完整表 | 无 | 无 | 无 | 中 |
| DeepMIMO Set E 跨场景 + 3GPP CDL-A/C/D | DDA-Net 用 QuaDRiGa | DDA-Net 用 CDL-B 单一 | 无外部数据 | 中 |

→ **真正独占的贡献集中在第 2、3、4 项**。剩下的需要靠"工程完整度 + 论文叙述"加分。

### 5.2 价值性（独立于创新性）

- 6G ISAC 是 IEEE/3GPP 优先方向；2025-2026 期刊收稿量持续上升；价值无质疑。
- 车载毫米波雷达 + 低空经济 + V2X 是工业应用拉力；价值高。
- T-OMP-Net 设计本身（可解释 + 轻量 + 模型驱动）有 6G PHY 的工程实用价值，不会因创新性下降而失去价值。

### 5.3 期刊命中率重估（基于 2026-06 文献环境）

| 顺序 | 期刊 | v2.2 自估 | **重估** | 重估依据 |
|---|---|:---:|:---:|---|
| 1 | Signal Processing (Elsevier, Q2) | 75% | **35-45%** | MOMPnet/DDA-Net 已落地，审稿人会比对；除非差异化叙述落到位 |
| 2 | DSP (Elsevier, Q2) | 85% | **55-65%** | 同上，但 DSP 对工程完整度更宽容 |
| 3 | IEEE Sensors Journal (Q1/Q2) | 55% | **60-70%** | "ISAC 多目标参数估计 + Hungarian 配对"叙述 → Sensors 角度更契合，反而上升 |
| 4 | IEEE Systems Journal (Q2) | 70% | **55-65%** | Systems 更看系统集成度，需要补 §6.7 联合 ISAC 场景实验 |
| (新增) | IEEE WCL (Wireless Comm Letters, Q1/Q2) | — | **40-50%** | 适合作为"Lemma 1 + 紧凑 ablation"的快投 letter 备选 |
| (新增) | IEEE TVT (Q1) | — | **30-40%** | 车载场景叙述加强后可投，但 TVT 周期长 |

**新的首投顺序建议**：IEEE Sensors → DSP → Signal Processing → Systems → WCL（letter 备选）。理由：把"ISAC 多目标参数估计"作为首要叙述比"信道估计"更与 Sensors 契合，且 MOMPnet/DDA-Net 主战场都是信道估计而非 ISAC 双输出，差异度在 Sensors 视角下被放大。

---

## 6. 下一步详细计划（重置版本，覆盖 6 个月窗口）

> 假设投稿目标在 2026-12 月（半年）。原 v2.2 排期是 8 个月，但 Phase 1-2 已耗费 6 个月（Set A pipeline / T-OMP-Net 仍未实现），需要压缩。

### 6.1 Phase A — 立论与对照重置（2 周，2026-06-25 至 2026-07-08）

**A1：v2.2 → v2.3 文档升级**
- 在 `01_design_and_plan/` 新建 `ISAC_DeepUnfolding_TechnicalDesign_v2.3.md`，把本评估章节 2、3、5 的修订全部并入。
- §1 段落 4 改写为"不主张任一要素首创"的稳健叙述。
- §2.4 SOTA 表用本文件第 2 节的实证 12 行替换 v2.2 占位。
- 在 §4 开头增加新一节 §4.0：**"Differentiation from MOMPnet, DDA-Net, Unified Tensor ISAC"**，明确 3 段差异化论证。
- §6.3 baselines 中新增对照 MOMPnet 与 DDA-Net（仅在通信侧 NMSE 对比）；声明 ISAC 侧无可直接对照的 SOTA。

**A2：文献库初始化**
- 在 `02_literature_and_refs/literature_2024_2025/` 下建立 8 个引用条目（BibTeX + 1-page 阅读笔记）：
  - MOMPnet 2601.10771
  - DDA-Net 2604.05389
  - Unified Tensor ISAC 2401.01738
  - Near-Field Sensors 2025 25/16/5050
  - AFDM-ISAC 2504.06567
  - OTFS-ISAC ADMM-Net WCNC 2024 10571155
  - JCAS Beamforming Unfolding JSTSP 2024 10684532
  - Deep Unfolding Survey 2502.05952
- 同时建立追踪文件 `tracking_2026.md`，每 2 周扫一次 arXiv `cs.IT`, `eess.SP` 的 ISAC + deep unfolding 新文。

**A3：DeepMIMO 与 5G Toolbox 阻塞解锁**
- 立刻下载 DeepMIMO O1 与 I3 raw 场景数据（按 `run_deepmimo_set_e_access_audit` 报告的清单）。
- 用 `lic = license('test','5G_Toolbox')` 在 MATLAB 中确认 license；若不可得，立即切换至 QuaDRiGa 备案（DDA-Net 即用 QuaDRiGa，社区可信）。

### 6.2 Phase B — 核心算法实现（6 周，2026-07-09 至 2026-08-19）

**B1：ISAC 数据生成器（Set A）**（W1-W2）
- 位置：`03_active_modules/data/` 新增 PyTorch / MATLAB 数据类
- FDMA + 虚拟阵列 + 3D 数据立方体；多目标 ground truth 与 channel taps 双轨输出
- 单元测试：检查与 v2.2 §3.1-3.3 公式逐项一致

**B2：Tensor-OMP baseline**（W2-W3）
- 位置：`03_active_modules/baseline/tensor_omp/`
- Algorithm 1 实现；在 Set A 上验证单目标和 L=3 多目标恢复 RMSE 接近 CRLB

**B3：T-OMP-Net 主网络**（W3-W6）
- 位置：`03_active_modules/tompnet/`
- 阶段 1（W3-W4）：硬支撑 + 固定字典 + Teacher Forcing；不带 off-grid；保证 NMSE 收敛超 Tensor-OMP
- 阶段 2（W5）：加入物理 bounded off-grid（tanh 重参数化）+ 实测 ε_grid vs (δθ)²
- 阶段 3（W6）：Gumbel-Softmax → STE → Hard 四阶段课程
- 训练日志全部写入 `05_results/training_curriculum/`

**B4：Hungarian + 联合损失**（W6）
- 复用 PyTorch `scipy.optimize.linear_sum_assignment`；permutation-invariant 反向梯度仅作用在配对量
- 验收：多目标场景 RMSE 与目标数量解耦

### 6.3 Phase C — 主实验矩阵（5 周，2026-08-20 至 2026-09-23）

**C1：8 baseline + 2 新 SOTA 实测**（W7-W9）
- LS / LMMSE / OMP / SOMP / SBL / Tensor-OMP / CS-DL / ANN（已有名）+ MOMPnet（复现）+ DDA-Net（复现）= 10
- MOMPnet/DDA-Net 复现是高风险项；如复现失败，按"参考报告值 + 不在同一实验上比较"处理

**C2：§6.5 实验 1-12**（W9-W11）
- 基础性能 / 少导频 / 高速移动 / 未知 L / 阵列误差 / 联合 ISAC 场景

**C3：§6.5.13 论文尺度过采样 + Kruskal**（W11）
- 升级 smoke：128×16×32 张量、$L \in \{2,4,8,16,32,64\}$、加 off-grid 与低 SNR 压力

**C4：§6.2 Set B/C/D + Set E 跨场景**（W12）
- nrCDLChannel 标准 CDL-A/C/D；DeepMIMO O1/I3 训练 → 测试

### 6.4 Phase D — 理论闭环（3 周，2026-09-24 至 2026-10-14）

**D1：Lemma 1 附录 D 完整证明落字**（5 天）
- 已有草图；只需补严格 Taylor 展开 + 常数 C₁ 推导 + PAC 论证 + 数值拟合表

**D2：5L 联合 CRLB**（W13-W14）
- $\eta \in \mathbb{R}^{5L}$ FIM；偏导式 5-3a~5-3e；数值差分交叉验证
- 高 SNR 渐近紧致性曲线

**D3：复杂度统计**（W14-W15）
- T-OMP-Net 实测 FLOPs / 推理延迟 / 内存
- 与 Tensor-OMP、MOMPnet、DDA-Net 对比

### 6.5 Phase E — 论文撰写（5 周，2026-10-15 至 2026-11-18）

**E1：Introduction + Related Work**（W15-W17）
- 段落 4 新措辞落字
- §2.4 SOTA 表全部用实证文献替换

**E2：System Model / Method**（W17-W18）
- §3 全部公式回填实测尺度；§3.1.1 SE 表标注实验
- §4 增加 §4.0 差异化论证；图 1 系统框图重绘

**E3：Theory + Sim**（W18-W19）
- §5 Lemma 1 + Corollary + 5L CRLB 全部落字
- §6 全部图表回填，A0-A7 消融实测数字

**E4：通稿润色 + 投稿信**（W20）
- 投稿信明确写"我们不主张要素首创，主张配方 + Lemma 1 + Hungarian-ISAC 损失"
- 首投 IEEE Sensors Journal

### 6.6 Phase F — 缓冲与备投（4 周）

- W21-W22 缓冲
- W23-W24 若 Sensors 拒，1 周内转投 DSP 并按审稿意见微调

### 6.7 风险登记表

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| MOMPnet/DDA-Net 复现失败 | 中 | 高 | 提前 1 个月启动复现；失败时改"按报告值参照"并在投稿信说明 |
| 5G Toolbox license 不可得 | 中 | 中 | 切换 QuaDRiGa（DDA-Net 已用） |
| T-OMP-Net 课程训练发散 | 中 | 高 | 阶段 1 即冻结展开层数，先收敛再加 off-grid |
| Set E O1/I3 数据下载失败 | 低 | 中 | 用 O1 + 自定义场景；说明范围 |
| §2.4 SOTA 文献再被新文超越 | 中 | 中 | tracking_2026.md 每 2 周扫；W18-19 前不冻结引用 |
| 投稿后被"已被 MOMPnet 覆盖"卡 | 中 | 高 | §4.0 差异化论证 + 在投稿信首段直接回应 |
| 时间溢出 | 中 | 中 | Phase F 4 周缓冲；任一阶段超 1 周即压缩 §6.5 实验数量到 8 组主图 |

---

## 7. 本周（2026-06-25 至 2026-07-01）立即可执行清单

| # | 动作 | 输出 | 责任优先级 |
|---|---|---|---|
| 1 | 起草 `ISAC_DeepUnfolding_TechnicalDesign_v2.3.md`（含 §1 段落 4 新措辞 + §2.4 SOTA 实证表 + §4.0 差异化段） | 文档 | P0 |
| 2 | 在 `02_literature_and_refs/literature_2024_2025/` 建立 8 篇核心文献条目（PDF + BibTeX + 阅读笔记） | 8 个 .md 文件 | P0 |
| 3 | 启动 DeepMIMO O1 / I3 raw 数据下载 + 在 MATLAB 中跑 `license('test','5G_Toolbox')` | audit 输出 | P0 |
| 4 | 在 `03_active_modules/data/` 写 Python `dataclass` 或 MATLAB struct 接口规范，**不**复用本科原型字段 | 接口规范 | P0 |
| 5 | 启动 `03_active_modules/baseline/tensor_omp/` 实现（标准 CP-OMP，不带学习） | 第一个 MATLAB / Python 模块 | P1 |
| 6 | 把本评估文档与 v2.2 一起提交 git；标记本次评估为 "post-MOMPnet/DDA-Net revalidation 2026-06" | git commit + tag | P0 |

---

## 8. 总结

| 项 | 一句话结论 |
|---|---|
| 方向是否正确 | ✓ 正确，但 2025-2026 SOTA 已大量挤入；不再是蓝海 |
| 实验是否可操作 | ✓ 可操作；T-OMP-Net 代码主线建议在 6 周内打通 |
| 创新性 | ⚠ 单要素全部被覆盖；独占点只剩 **物理 bounded off-grid + Lemma 1 + Hungarian-ISAC 联合损失 + 5L CRLB** 四元组的配方 |
| 价值性 | ✓ 高，不受创新性下降影响 |
| 首投建议 | **IEEE Sensors Journal**（ISAC 多目标参数估计叙述命中率最高），DSP / Signal Processing 作为 2/3 顺位 |
| 命中率重估 | Sensors ~60-70%、DSP ~55-65%、SP ~35-45% |
| 关键防御点 | §4.0 写清与 MOMPnet/DDA-Net 的差异；§5.1.1 Lemma 1 是唯一形式化贡献，必须写实写完整 |
| 时间预算 | 实施 ≈ 5 个月（B+C+D+E）+ 1 个月缓冲；如要在 2026-12 投出，本周必须开始 Phase A+B |

---

**附：本评估检索的实证文献清单（按方向）**

A. 张量化 ISAC 统一估计：arXiv 2401.01738 (2024)；MDPI Sensors 25/16/5050 (2025)；arXiv 2504.06567 (2025)；arXiv 2403.02942 (2024)；Frontiers IT/EE FITEE.2400472 (2025)
B. Deep unfolding for JCAS/ISAC：arXiv 2601.10771 MOMPnet (2026)；arXiv 2604.05389 DDA-Net (2026)；IEEE JSTSP 10684532 (2024)；IEEE Xplore 10571155 OTFS-ISAC ADMM-Net (WCNC 2024)；arXiv 2411.17747 (2024)
C. Off-grid / 物理约束：DOI 10.3390/electronics15071461 atomic-norm DL (2024)；DDA-Net；arXiv 2602.13988 Tucker XL-IRS off-grid (2025)；OMPBR 历史工作
D. Near-field & SSM：arXiv 2508.00403 Mamba wireless survey (2025)；arXiv 2604.21957 MambaCSP (2026)；arXiv 2601.17108 MambaNet (2026)；MDPI Sensors 25/16/5050
E. Kruskal / 配对：SIAM J. Matrix Anal. Appl. 140964813；arXiv 1304.8087；Sidiropoulos 2006；DETR Carion 2020
F. 综述：arXiv 2502.05952 Deep Unfolding Wireless Comprehensive Review (2025)；arXiv 2509.06968 DL-ISAC Survey (2025)；arXiv 2509.02137 High-Resolution ISAC DL (2025)
