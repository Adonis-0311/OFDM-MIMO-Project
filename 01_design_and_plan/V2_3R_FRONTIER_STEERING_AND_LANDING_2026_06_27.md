# v2.3R 前沿对标与论文落地指导（Frontier Steering & Landing Guide）

> 生成时间：2026-06-27
> 适用版本：v2.3R（Lemma 2 已修正；贡献压回 C1–C4；A6/MAML 移除）
> **首投目标：IEEE Sensors Journal**（双栏 IEEEtran；≤8 页起，超页 $175/页强制收费；graphical abstract 现为必需）
> 回退阶梯：IEEE Systems Journal → IEEE TVT → IEEE TSP（证据再扩张后）
> 本文件作用：在现有 `V2_3R_PROGRESS_AUDIT` + `V2_3R_SENSORS_SUBMISSION_PLAN` 之上，**叠加一层 2024–2026 工程前沿对标**，把"还差什么"重排为"按落地价值排序的单一关键路径"，并标出必须由人决策的分叉点。
> 证据边界仍以 `05_results/v2_3r_paper_evidence_table/paper_evidence_table.md` 为唯一真值，本文不放宽任何 claim。

> **2026-06-28 执行回写**：Gate-1 已由 scaled held-out CDL-A/C 训练控制器结果通过；IEEEtran 已压至 8 页；系统模型、T-OMP-Net 架构、CDL 五种子图与 graphical abstract 已完成视觉验收；引用已从 26 扩至 42 条并加入最近邻对比表；E4 已补齐可执行 ESPRIT/PARAFAC 复杂度行，但真实 profiler FLOPs 与 matched accuracy Pareto 仍属边界。

> **2026-06-29 深度审阅回写（当前真值）**：代码与结果审计确认现有证据对应三条不同路径：G2 是单标量 bounded interpolation；CDL 是独立的 10--16--2、210 参数特征控制器；A4 是确定性半径序列与标量 plateau gate。旧稿把三者画成统一 K-stage T-OMP-Net，存在方法身份过度整合。论文现已改题为 *Learned Bounded Off-Grid Refinement for Sparse Tensor-OMP in mmWave MIMO-OFDM ISAC*，正文新增可执行公式与小样本边界，禁止继续声称已验证的完整深度展开网络。四幅主图已在源分辨率和 IEEE 双栏 PDF 中复核：系统模型的 Outputs 越框已修复，架构图无重叠，G2/A4 图取消双轴并改为门限平面。IEEEtran 仍为 8 页、42 条引用。下一科研关键路径更新为：E11 统一多阶段估计器（若要恢复 T-OMP-Net 身份）→ E12 matched-accuracy NOMP/off-grid SBL 比较 → E13 扩大 G2/A4 统计量 → E14 trained DeepMIMO physical evaluation。

---

## 0. 一页结论（先读这页）

**项目已不在"能不能跑"阶段，而在"能不能在被别人抢先前以可防守的证据投出去"阶段。**

- 论文骨架完整：8 节 evidence-led 草稿 + 摘要 + 可编译 LaTeX（generic article，~13 页）。方法（G1/G2）已 accepted 并 5-seed 加固；理论（Lemma 1/2、CRLB）已修正并自洽；claim 纪律是本项目最强资产。
- **真正卡住落地的只有一件事：完整训练估计器的外部信道证据仍未闭环。** 当前 DeepMIMO / Sionna CDL 只到"数据接入 + 标量 source-alpha 代理 + grid/clean-floor 基线"，**没有把训练好的 T-OMP-Net 接到 physical angle/delay RMSE 上**。这是 §6.4 的 G3 未完成原因，也是与前沿差距的核心。
- **前沿在加速逼近，时间窗在收窄。** Delay–Doppler–Angle 域的 deep unfolding 正在密集出文：**DDA-Net（arXiv 2604.05389，2026-04）已经用 QuaDRiGa + CDL-B zero-shot 跑出 >5 dB 外部结果**；AirFM-DDA（2605.00020，2026-05）把同一表示推到 foundation model。我们"外部验证 blocked"的姿态，半年后会从"诚实 limitation"变成"竞争劣势"。
- **可防守的 novelty 已经从"单点首次"收缩为"ISAC 联合估计的特定组合"**：Tensor-OMP 贪婪展开 + 物理 bounded off-grid refinement + Hungarian 排列不变多目标损失 + 可辨识性感知早停 + Kruskal/CRLB 理论边界。必须显式对标 DDA-Net / NOMP 并讲清差异，否则会被审稿人当作增量。

**唯一关键路径（按价值排序，不要并行铺开）：**

1. **E1/E2 训练闭环（决定生死）** → 把已训练 T-OMP-Net 接到 Sionna CDL 与 DeepMIMO O1_60 的 **physical delay/angle RMSE** 合同上，证明相对已记录 grid/clean-floor 的改进。
2. **E4 复杂度对标（IEEE 审稿必问）** → 补 ESPRIT/Unitary-ESPRIT、PARAFAC-ALS 比较器与真实 FLOPs/wall-clock。
3. **前沿引用 + 最近邻对比表（防 novelty 质疑）** → 26→40+ 条，必含 DDA-Net、NOMP-OFDM-ISAC、unified-tensor-ISAC、两篇 ISAC+DL 综述。
4. **图件补全（IEEE 双栏 5 图）+ IEEEtran 模板切换 + 控页面（≤8–10 页）**。

**判断：距 IEEE Sensors Journal 第一稿，技术写作完成度约 75%，但"可投"完成度约 60%，瓶颈 100% 落在第 1 步外部训练闭环。**

---

## 1. 进度评估（校准评分卡）

下表是把现有 audit / evidence table 折算成单一可读完成度。百分比为基于证据的工程判断，非精确度量。

| 维度 | 完成度 | 状态判定 | 证据/缺口锚点 |
|---|---:|---|---|
| 技术设计 & claim 纪律 | ~95% | **稳** | v2.3R 设计锁定、禁用过度表述清单完整、Lemma 已修正 |
| 方法实现 G1（Tensor-OMP/off-grid/CRLB 基建） | ~90% | accepted | `tests/`、baseline 模块、FIM rel.err 5.73e-10 |
| 方法实现 G2（T-OMP-Net bounded refinement） | ~90% | accepted+加固 | 5 seed，mean gain **6.1726 dB**，min L-cell **4.4735 dB** |
| 本地合成证据（G2/A4 主结果） | ~85% | 强但 CPU-small | A4 已收窄到 L≥32@20 dB（min savings 25%，max gap 0.4008 dB） |
| **外部信道训练闭环（E1/E2/E3）** | **~35%** | **关键阻塞** | 数据 ready（4188 files）+ 标量 alpha 代理 + grid/clean-floor，但**无训练估计器 physical RMSE** |
| 复杂度/运行时（E4） | ~40% | dev-only | dev 表 9 行；**缺 ESPRIT/PARAFAC 比较器 + 真实 FLOPs** |
| 理论（Lemma 1/2 + CRLB） | ~80% | 自洽但 single-target | CRLB 仅单目标高 SNR trend（30 dB ratio 1.0067） |
| 稿件草稿（8 节 + 摘要 + LaTeX） | ~75% | 骨架齐 | generic article 可编译 ~13 页；待填外部结果 + 切 IEEEtran |
| 图件 | ~30% | 缺 | 现 1 主图；缺系统模型/架构/CDL/DeepMIMO/复杂度共 ~4 张 |
| 参考文献 | ~55% | 偏少且缺 DOI | 26 条；缺 2024–2026 前沿与最近邻 |
| 可复现/CI | ~70% | 良 | manifest 体系强；`pytest` 缺装 |
| **整体"可投" IEEE Sensors Journal** | **~60%** | 瓶颈单点 | 见 §4 关键路径第 1 步 |

**读法**：技术与写作侧（上半部）都在 75–95%，唯独"外部训练闭环"在 35% 且是其它一切的前置条件。先把它从 35% 拉到可写主结果，整体"可投"会从 60% 跳到 ~85%；其余（图、引用、模板）是确定性收尾工作，不含科研风险。

---

## 2. 工程前沿对标（2024–2026）

### 2.1 竞争地图：novelty 正在被三个方向挤压

| 最近邻工作 | 与本文重叠 | 我们仍可防守的差异 | 处置 |
|---|---|---|---|
| **DDA-Net**（2604.05389, 2026-04）3D deep unfolding，Doppler-Delay-Angle，ADMM 展开 + 学习 Doppler denoiser + delay oversampling 抗 basis-mismatch；**QuaDRiGa + CDL-B zero-shot >5 dB** | 3D、deep unfolding、抗离网失配、跨场景泛化 | 我们是 **greedy Tensor-OMP 展开**（非 ADMM unroll）；做**联合信道+多目标参数**（ISAC，非纯通信信道）；有 **Hungarian 排列不变损失** 与 **可辨识性感知早停 + Kruskal/CRLB 理论** | **最强威胁**。必须显式引用、并在 Related Work 与 §对比表逐格区分；其外部结果是我们必须追平的标杆 |
| **NOMP for OFDM ISAC**（2411.03191, 2024-11）coarse on-grid OMP + Newton 连续域 delay-Doppler refinement | OMP + 离网细化 + OFDM ISAC | 我们的 refinement 是**可学习、物理有界、3D 张量**且嵌入展开层；NOMP 是非学习 2D | 引为"最近邻经典离网-OMP-ISAC"，论证 learned vs Newton 的可解释/复杂度取舍 |
| **Unified Tensor Approach, ISAC Massive MIMO**（联合信道+目标参数, 2024）；**Near-Field Tensor ISAC MIMO-OFDM**（2025） | 统一张量建模联合估计 | 我们叠加 **deep unfolding + bounded off-grid + early-stop**；它们是经典 PARAFAC/ALS | 作为 C1 的 anchor 引用，定位"我们把统一张量从经典分解推进到可解释展开网络" |
| **PLAIN**（2503.21242, 2025-03）可扩展 ISAC 估计架构；**AFDM-ISAC off-grid SBL**（2503.10011 / 2504.06567） | 可扩展/离网 ISAC 估计 | 波形与求解器不同（AFDM vs OFDM；SBL vs unfolding-OMP） | 作为离网/可扩展 ISAC 家族的广度引用 |

### 2.2 三条对落地的硬结论

1. **外部验证已从"加分项"变成"入场券"。** DDA-Net 在 2026-04 就给出了 QuaDRiGa+CDL 的训练估计器结果。IEEE 信号处理审稿人大概率知道这条线。若我们仍只交"标量 alpha 代理 + grid floor"，会被直接质疑"为何不接训练模型"。→ §4 第 1 步不可降级、不可用措辞绕过（设计文档 §9 已明令：scalar gate/threshold frontier/SNR-aware diagnostic 是边界证据，禁止用措辞救活）。

2. **Novelty 叙述必须改为"组合式 + ISAC 专属"。** 单点（3D 张量 / 离网 OMP / 展开网络）均已被 2024–2026 占用。可防守的句式是："首个把 *贪婪 Tensor-OMP 展开 + 物理有界离网细化 + Hungarian 排列不变多目标 ISAC 损失 + 可辨识性感知早停* 组织为同一可解释估计器，并以 Kruskal/CRLB 显式界定能力边界"——且**强调 sensing 侧的多目标参数估计**（这也正好贴合"Sensors"期刊 scope，见 §5）。

3. **选题方向本身被前沿验证为热点（利好但有时钟）。** Delay–Doppler–Angle 域 deep unfolding 是 2025–2026 明确上升的子领域（DDA-Net、AirFM-DDA、多篇 AFDM-ISAC）。方向正确，但"热点 = 拥挤 = 抢发风险"。落地节奏应以**月**为单位，不要再开新增量贡献（A6/foundation-model 等留 future work）。

### 2.3 必补引用（直接喂给 26→40+ 文献扩充；详见附录 A）

- **最近邻（必引必differentiate）**：DDA-Net、NOMP-OFDM-ISAC、Unified-Tensor-ISAC、Near-Field-Tensor-ISAC-OFDM。
- **方法学综述（Intro/Related Work 脊柱）**：Monga–Li–Eldar《Algorithm Unrolling》(SPM 2021)、Shlezinger 等《Model-based Deep Learning》(Proc. IEEE 2023)、《Comprehensive Review of Deep Unfolding for Next-Gen Wireless》(2025)、《Deep Unfolding: Recent Developments, Theory, Design Guidelines》(2025)。
- **ISAC+DL 综述（定位 + 趋势）**：《Deep Learning-based Techniques for ISAC: SOTA, Challenges, Opportunities》(2509.06968)、《High-Resolution Sensing in Communication-Centric ISAC》(2509.02137)。
- **基准/数据集（Data Availability 强制显式引用）**：DeepMIMO、Sionna、QuaDRiGa、3GPP TR 38.901 CDL。

---

## 3. 多份 plan 的对齐与失效项（venue 已定 → IEEE Sensors Journal）

现有 `01_design_and_plan/` 下有 11 份文档，存在**版本漂移与一处 venue 冲突**。本节做一次收敛，确立单一真值，避免按过期计划做无用功。

### 3.1 真值与从属关系（自上而下）

```text
ISAC_DeepUnfolding_TechnicalDesign_v2.3R.md   ← 技术与 claim 边界（锁定，勿改）
05_results/.../paper_evidence_table.md         ← 证据真值（每次实验后重聚合）
V2_3R_PROGRESS_AUDIT_2026_06_25.md             ← 进度快照（上一次）
V2_3R_FRONTIER_STEERING_AND_LANDING（本文）     ← 前沿叠加 + 关键路径（当前执行版）
V2_3R_SENSORS_SUBMISSION_PLAN.md               ← 实验/工程任务清单（E0–E8 仍有效，但 venue 段已失效，见 3.2）
V2_3R_STAGE1/2/3_CURRENT_BOARD.md              ← 看板，随执行更新
```

### 3.2 因 venue=IEEE Sensors Journal 而**失效/需改写**的条目

`V2_3R_SENSORS_SUBMISSION_PLAN.md` 是按 **MDPI Sensors** 写的，以下条目现在作废或替换（其余 E0–E8 实验内容与开源工具链**继续有效**）：

| 原 MDPI 条目 | 处置（IEEE Sensors Journal） |
|---|---|
| `Sensors.cls` 模板 | → **IEEEtran.cls 双栏**（journal mode） |
| `\bibliographystyle{mdpi}` + 强制 DOI | → **IEEEtran.bst（数字引用）**；DOI 仍建议补全 |
| CC-BY 4.0 / APC ~2600 CHF / open access 强制 | → **不强制开放获取**；改为关注**超 8 页 $175/页强制超页费** |
| 摘要 ≤200 词 + 章节重排为 Materials and Methods/Results/Discussion | → **保留现有 8 节学术结构**（IEEE 不强制 MDPI 结构，**这反而省掉一次重排**）；摘要 ~150–250 词 |
| 字数扩到 10000–11000 词 / 14 页 | → **反向收紧**：目标 8–10 双栏页，细节下沉 appendix/supplementary，控超页费 |
| 中英双语并行稿（P0） | → 投稿语言为**英文**；中文并行稿降为**可选**（非 IEEE 要求），不占关键路径 |
| graphical abstract（P2，可选） | → **升为必需**（IEEE Sensors Journal 现强制 graphical abstract） |

> 行动：在 `V2_3R_SENSORS_SUBMISSION_PLAN.md` 顶部加一行 `> [SUPERSEDED venue section by FRONTIER_STEERING 2026-06-27: target = IEEE Sensors Journal]`，避免后续误用 MDPI 格式做工。

### 3.3 仍然有效、直接继承的部分

E0–E8 实验定义、Sionna/DeepMIMO/QuaDRiGa 开源工具链、风险矩阵的实验侧、`aggregate_v2_3r_paper_evidence_table.py` 重聚合流程——**全部保留**。本文不重复，只重排优先级（§4）。

---

## 4. 落地关键路径（门控 + 时间盒）

**原则：串行优先级，不要并行铺开。** 第 1 步未过门之前，不投入第 3、4 步的精修（图件/模板可在等实验时穿插，但不得抢占算力与注意力）。每步给**通过门（Gate）**。

### 步骤 1  — 外部训练闭环（P0，生死项）

- **做什么**：把已训练 T-OMP-Net（非 scalar-alpha 代理）接到 **同一 CIR-grounded physical metric 合同**：
  - E1：Sionna CDL-A/C/D，输出 **physical delay RMSE (ns) + projected-angle RMSE (deg)**，对标已记录 grid baseline（180.23 ns / 28.63 deg）与 clean-grid floor（141.32 ns / 28.45 deg）。
  - E2：DeepMIMO O1_60，训练模型的 channel NMSE + physical angle/delay，替换当前 weak 标量代理（1.3235 dB）。
- **Gate-1（任一即可解锁主结果写作）**：训练 T-OMP-Net 在 **SNR≥20 dB** 至少一个 profile/场景上，physical delay 或 angle RMSE **显著优于 grid baseline 且向 clean-floor 收敛**；并保留失败 cell（CDL-D/0 dB/L=16；I3 负增益 cell）作为诚实边界。
- **若 Gate-1 失败**：按设计文档 §4.5/§9，先**重设 refinement schedule 或训练目标**，再重测；不得用措辞把代理结果包装成训练结果。同时启动 §10 回退（Systems Journal 容忍度更高）。

### 步骤 2 — 复杂度/运行时对标（P0–P1，IEEE 审稿必问）

- 在 `run_complexity_benchmark.py` 补 **ESPRIT/Unitary-ESPRIT、PARAFAC-ALS** 比较器（现 evidence table 明列这 2 行为 not-implemented gap），用 `thop`/`fvcore` 给**真实 FLOPs/参数量/CPU-GPU wall-clock**。
- **Gate-2**：产出一张"NMSE vs 复杂度"Pareto 表/图，且比较器为**同 K 层展开但无 off-grid block** 的公平参照（风险矩阵已警示不可拿手写慢实现取胜）。

### 步骤 3 — 前沿引用 + 最近邻对比表（P1，防 novelty 质疑）

- 26→40+ 条，按附录 A 注入；**Related Work 必须出现 DDA-Net、NOMP、unified-tensor-ISAC 的逐格差异表**（设计文档 §2.2 的定位表升级为含具名最近邻的版本）。
- **Gate-3**：审稿人能在 Related Work 一页内看清"我们 vs DDA-Net/NOMP"的方法学差异与各自验证范围。

### 步骤 4 — 图件 + IEEEtran 模板 + 控页（P1）

- 补 4 张图：**Fig.1 系统模型（3D 稀疏张量）**、**Fig.2 T-OMP-Net 展开架构**（TikZ 矢量）、**Fig.4 CDL 跨 profile**（待步骤 1）、**Fig.5 DeepMIMO**（待步骤 1）；现 evidence summary 重排为 Fig.3；复杂度 Pareto 为可选 Fig.6。
- 切 IEEEtran 双栏，**graphical abstract 必做**，全文压到 ≤8–10 页（每超 1 页 $175）。
- **Gate-4**：IEEEtran 编译无 error，页数与超页预算明确，5 张主图齐备。

### 时间盒（理想串行，按算力可压缩）

| 周 | 主线 | 穿插（等实验时） | 出口 |
|---|---|---|---|
| W1 | 步骤 1：E1 训练闭环（CDL-A 先打通）| Fig.1/Fig.2 矢量图、附录 A 引用注入 | E1 单 profile physical RMSE manifest 过 Gate-1 试探 |
| W2 | 步骤 1：E1 CDL-A/C/D 全 + E2 O1_60 训练 | Related Work 最近邻对比表 | Gate-1 通过；主结果可写 |
| W3 | 步骤 2：E4 ESPRIT/PARAFAC + 真实 FLOPs | G2 10-seed CI（E8）扩跑 | Gate-2 通过 |
| W4 | 步骤 4：IEEEtran 切换 + graphical abstract + 控页 | DOI 补全、`pytest` 装好 | Gate-3/4 通过 |
| W5 | 终稿：evidence table 全量重聚合 + cover letter + 自查 DoD | QuaDRiGa CDL-D 第三方交叉校验（附录） | 可投 |

---

## 5. 风险登记与必须由人决策的分叉点

### 5.1 新增/升级风险（前沿叠加后）

| 风险 | 等级 | 缓解 |
|---|---|---|
| **被抢发 / novelty 贬值**（DDA-Net、AirFM-DDA 同域高产） | **高** | 以月为节奏落地；novelty 改为"ISAC 联合估计组合式"；尽快挂 arXiv 占位 |
| **外部训练闭环失败**（Gate-1 不过） | **高** | refinement schedule / 训练目标重设后再测；否则回退 Systems Journal 并把外部证据写成 honest limitation |
| **IEEE Sensors Journal scope 质疑**（算法味偏重、像 TSP/TVT 选题） | 中–高 | 框架显式偏向 **sensing/target-parameter estimation 与 ISAC 系统**，弱化"纯通信信道估计"叙述；Intro 用 Sensors 友好的传感动机 |
| **超页费失控**（现 13 页 generic → 双栏可能 ≥10 页） | 中 | 细节下沉 supplementary；每图/表问"是否进主文"；预算或压缩到 8–9 页 |
| 比较器不公平被质疑 | 中 | 同 K 层无 off-grid 参照；引用 ESPRIT/PARAFAC 标准实现 |
| CRLB 仅单目标 | 中 | 维持"single-target high-SNR trend"措辞；多目标进附录或 future work |
| Lemma 2 trade-off 再被质疑 | 低 | 交付前数学过一遍 §5.2；已删闭式 K* |

### 5.2 必须由你拍板的决策点

1. **[已决] 首投 = IEEE Sensors Journal。** → 本文 §3.2 的格式改写随之生效。
2. **外部验证策略**：Gate-1 给自己几周？给一个硬截止（建议 W2 末）；到期未过则**触发回退到 Systems Journal**，而不是无限期等 CDL/DeepMIMO 调好。
3. **是否先挂 arXiv 预印本**抢时间戳：鉴于 §2.2 抢发风险，建议在 Gate-1 通过、主结果稳定后**立即挂 arXiv**，再正式投刊。
4. **中文并行稿**：IEEE 不需要；确认是否仍要中文版（若仅为存档/汇报，降到非关键路径）。
5. **A4 是否再尝试 learned SNR-aware gate**：设计文档已证否当前曲线族；除非重设 refinement schedule，否则**写进 future work，不再投入**。

---

## 6. 本周（W1）可立即执行动作清单

- [ ] 在 `V2_3R_SENSORS_SUBMISSION_PLAN.md` 顶部标注 venue superseded（§3.2）。
- [ ] 启动 E1 训练闭环：在现 `run_sionna_cdl_profile_generalization.py` 基础上，接已训练 T-OMP-Net 到 physical delay/angle 合同，先打通 **CDL-A 单 profile**。
- [ ] 画 **Fig.1 系统模型** 与 **Fig.2 T-OMP-Net 架构**（TikZ 矢量，等实验时做，不占算力）。
- [ ] 按附录 A 注入 **DDA-Net、NOMP、unified-tensor-ISAC、两篇 ISAC+DL 综述** 到 `v2_3r_references.bib`，并起草 Related Work 最近邻对比表。
- [ ] `pip install pytest thop --break-system-packages`，恢复单元测试与 FLOPs 计量工具链。
- [ ] 设定 Gate-1 硬截止日期（建议 W2 末）并写入 Stage-3 看板。

---

## 7. 提交前 Definition-of-Done（IEEE Sensors Journal 版）

- [ ] IEEEtran 双栏编译无 error；页数与超页费预算明确（目标 ≤8–10 页）。
- [ ] **Graphical abstract 完成**（IEEE 强制）。
- [ ] 主图 ≥5（系统模型、架构、evidence summary、CDL、DeepMIMO），矢量 PDF。
- [ ] 主表 ≥3（G2 含 CI、外部信道 physical RMSE、复杂度对比）。
- [ ] 参考文献 ≥40，含 DDA-Net/NOMP/unified-tensor-ISAC 与综述脊柱；DOI 尽量补全。
- [ ] 摘要 150–250 词，含**一个外部信道（CDL 或 DeepMIMO）的训练估计器数字结论**。
- [ ] Index Terms 5–8 个。
- [ ] **外部训练闭环过 Gate-1**：至少一个 profile/场景 physical RMSE 优于 grid baseline 并向 clean-floor 收敛；失败 cell 诚实保留。
- [ ] 复杂度表含 ESPRIT/PARAFAC 真实 FLOPs/wall-clock（E4 gap 关闭）。
- [ ] Lemma 1（support condition）/ Lemma 2（trade-off，无闭式 K*）数学复核通过。
- [ ] 禁用过度表述自查（设计文档 §2.1）：无"全局 IA-AUD 最优深度 / 任意 L≥25% / HIR-JL 主贡献 / 完整 DeepMIMO 验证已完成 / 多目标渐近有效"。
- [ ] Data Availability：GitHub 仓库 + DeepMIMO/Sionna/QuaDRiGa/3GPP 38.901 显式引用。
- [ ] Cover letter + 推荐审稿人 3–5 名；（建议）arXiv 预印本已挂。
- [ ] evidence table 全量重聚合，claim_evidence_ledger.json 同步。
- [ ] iThenticate 查重 ≤15%。

---

## 附录 A：前沿引用清单（arXiv ID + 用途）

> 用途标注：**[diff]** = 必引且逐格区分；**[anchor]** = 定位锚点；**[spine]** = 方法学/综述脊柱；**[bench]** = 基准/数据集显式引用。

| 工作 | 标识 | 用途 |
|---|---|---|
| DDA-Net: Deep Unfolding Doppler-Delay-Angle（2026-04） | arXiv 2604.05389 | **[diff]** 最强最近邻；3D unfolding + 外部 QuaDRiGa/CDL |
| Newtonized OMP, High-Res Target Detection, Sparse OFDM ISAC（2024-11） | arXiv 2411.03191 | **[diff]** 最近邻经典离网-OMP-ISAC |
| Unified Tensor Approach, ISAC Massive MIMO（channel+target, 2024） | ResearchGate 377482987 | **[anchor]** C1 统一张量建模 |
| Near-Field Tensor ISAC MIMO-OFDM Localization（2025） | ResearchGate 394544667 | **[anchor]** 同题张量-ISAC-OFDM |
| PLAIN: Scalable Estimation for ISAC（2025-03） | arXiv 2503.21242 | **[anchor]** 可扩展 ISAC 估计 |
| AFDM-ISAC off-grid SBL（2025-03） | arXiv 2503.10011 | 离网 ISAC 家族广度 |
| Angle-Delay-Doppler AFDM-ISAC 近/远场（2025-04） | arXiv 2504.06567 | 离网 3 维 ISAC 广度 |
| Algorithm Unrolling（Monga, Li, Eldar, SPM 2021） | IEEE SPM 38(2) | **[spine]** 展开方法学 |
| Model-based Deep Learning（Shlezinger 等, Proc. IEEE 2023） | Proc. IEEE 111(5) | **[spine]** 模型驱动学习 |
| Comprehensive Review of Deep Unfolding, Next-Gen Wireless（2025） | arXiv 2502.05952 | **[spine]** 最新展开综述 |
| Deep Unfolding: Developments, Theory, Design Guidelines（2025） | arXiv 2512.03768 | **[spine]** 设计准则 |
| Deep Learning for ISAC: SOTA, Challenges, Opportunities（2025-09） | arXiv 2509.06968 | **[spine]** ISAC+DL 综述 |
| High-Resolution Sensing in Comm-Centric ISAC（2025-09） | arXiv 2509.02137 | **[spine]** 传感侧定位 |
| AirFM-DDA: DDA-domain Foundation Model（2026-05） | arXiv 2605.00020 | 趋势/抢发风险佐证（future work 对照） |
| Learned Trimmed-Ridge Regression, mmWave Massive MIMO（2024） | arXiv 2408.02934 | learned 信道估计对照 |
| DL-aided ALS for Tensor CPD, Massive MIMO（2023） | arXiv 2305.13947 | learned 张量分解对照 |
| DeepMIMO / Sionna / QuaDRiGa / 3GPP TR 38.901 CDL | 官方来源 | **[bench]** Data Availability 强制引用 |

> 注：arXiv 编号前两位为 YYMM（26xx = 2026 年），与当前 2026-06 时间线一致；正式投稿前请逐条用官方页核对最终卷期/DOI。

## 附录 B：与现有文档的对接

- 本文**不**修改 `ISAC_DeepUnfolding_TechnicalDesign_v2.3R.md` 与 `paper_evidence_table.md`，二者仍为技术与证据真值。
- 本文是 `V2_3R_PROGRESS_AUDIT_2026_06_25.md` 的**前沿叠加 + 关键路径重排**版，取代其 "Next Experiment Steering" 的优先级排序。
- 本文使 `V2_3R_SENSORS_SUBMISSION_PLAN.md` 的 **venue/格式段失效**（§3.2），但保留其 E0–E8 实验与工具链定义。
- 每完成一步（尤其 Gate-1），按既有流程：`05_results/` 新建目录 → 重跑 `aggregate_v2_3r_paper_evidence_table.py` → 追加 evidence 行 → 同步 ledger → 更新 Stage 看板。
