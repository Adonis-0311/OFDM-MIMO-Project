# v2.3R Sensors 投稿规划指引（Phase-Next Execution Plan）

> 生成时间：2026-06-25（初版）
> **最近更新：2026-06-27（rev.4）—— Sionna CDL 已补 CIR-grounded physical delay/projected-angle grid baseline 与 clean-grid floor。**
> **执行补充：论文交付需生成英文 Sensors 投稿版与中文并行版。**
> 适用版本：v2.3R（Lemma 2 已修正；4 个贡献 C1–C4；A6 移除）
> 第一目标投稿：**MDPI Sensors**（Special Issue: Integrated Sensing and Communication 或 mmWave Sensing）
> 备选阶梯：IEEE Systems Journal → IEEE TVT → IEEE TSP（若证据再扩张）
> 本文件作用：把当前 v2.3R 证据边界 → Sensors 第一稿提交所需差量，一次性写清。

## Rev.1 关键变更（2026-06-25）

1. **完全放弃 5G Toolbox 依赖**：CDL 信道与 OFDM 链路改用 **Sionna**（Python/TF，NVIDIA，开源 Apache-2.0）作为主路径，**QuaDRiGa**（HHI，MATLAB+开源学术许可）作为交叉校验副路径。
2. **DeepMIMO 数据已就位**：O1_60 与 I3_60 已下载至 `90_archive/2025_thesis_materials/参考/DeepMIMO-5GNR/DeepMIMO_dataset/`。E0 解锁阻塞消除，E2 立即可启动。
3. 工程任务从"MATLAB 主链 + Python 评估"重排为"**Python 全栈链 (Sionna + DeepMIMO + PyTorch)**"，与现 `04_experiments/eval/run_stage2_torch_*` 同栈，便于 seed/CI 复现。
4. 风险矩阵与时间表同步刷新：W1 关键路径由"等 license"改为"装 Sionna + 跑通 deepmimo Python 加载器"。

## Rev.2 进度更新（2026-06-27）

1. **E2/E3 计划规模代理评估已完成**：O1_60 与 I3_60 均完成 5 seed × 100 用户 × SNR {0,10,20,30} dB × L {4,8,16}，各 seed 独立保留 manifest、cell CSV 与 sample CSV。
2. **O1_60 结论为 weak**：source-alpha 相对 grid 的平均 channel NMSE 增益为 1.3235 dB，seed-mean 95% CI 为 [1.2538, 1.3931] dB，最差 cell 增益仍为 0.8554 dB。
3. **I3_60 结论为 partial**：平均增益为 6.7014 dB，95% CI 为 [6.4660, 6.9368] dB，但最差 cell 为 -0.2412 dB，且最小支持召回为 0.3063；不得以总体均值覆盖局部失效。
4. **证据边界不变**：本轮仅转移 Stage-2 标量 alpha，不等同于完整训练 G2/T-OMP-Net；delay/TX-bin 指标也不等同于物理 angle/delay RMSE。完整 E2/E3 仍需接入训练模型与物理参数评价。
5. **可追溯输出**：聚合结果位于 `05_results/deepmimo_source_alpha_seed_campaign/`，并已写回论文证据表与 C4 ledger。

## Rev.3 进度更新（2026-06-27）

1. **E1 计划规模已完成**：CDL-A/C/D × 5 seeds × 50 samples/profile/seed × SNR {0,10,20,30} dB × L {4,8,16}，共 9000 个 sample rows；评估网格由开发期 `64 × 4` 扩展至与论文尺度更接近的 `128 × 16`。
2. **分辨率修正有效但未完全过门**：最低 exact support recall 从开发期 `0.1719` 提升至 `0.4188`，仍低于 `0.5` 门槛，因此 E1 不得标为最终支持。
3. **失败模式已定位**：A/C 的最低 exact recall 约为 `0.86/0.85`；弱点集中在 CDL-D、0 dB、L=16。该 profile 的 95% 能量平均仅需约 `1.81` 个 bin，强制 L=16 属于 over-budgeted support。
4. **能量恢复稳定**：所有 cell 的 clean-oracle top-k 能量效率至少为 `0.9886`，说明 exact-bin 失配主要发生在弱/近等能 bin，不是主能量恢复崩溃。结论归类为 `energy-supported-exact-bin-weak`。
5. **剩余 E1 硬门**：加入 physical path delay/angle RMSE，并接入完整训练估计器；当前结果仅作为 supporting/appendix evidence。

## Rev.4 进度更新（2026-06-27）

1. **物理 delay 指标已落地**：真值直接使用 Sionna CIR `tau`，单位为 ns；grid baseline 全 cell 平均 RMSE 为 `180.23 ns`，SNR≥20 dB 为 `141.32 ns`。
2. **可辨识角度指标已落地**：对 1×16 半波长 ULA 报告 effective projected broadside angle，而不是不可由该阵列单独辨识的 AoD/ZoD 二元角；全 cell 平均 RMSE 为 `28.63 deg`。
3. **clean-grid floor 已量化**：delay/angle floor 分别为 `141.32 ns / 28.45 deg`；高 SNR noisy baseline 已基本落在该下限，说明继续调噪声阈值不能解决 E1。
4. **失败边界保留**：CDL-D、0 dB、过预算 L 的 exact-bin 与 physical delay 仍最弱；NMS 诊断对 A/C 无一致收益，未并入正式支路。
5. **剩余 E1 硬门收窄**：将完整训练/离网估计器接到同一 CIR-grounded physical metric contract，并证明其相对 grid floor 的改进。

---

## 0. 总体判断与时间窗

当前主稿（13 页 LaTeX、5-seed G2 主结果、A4 高负载早停、CRLB 单目标 pilot、Kruskal/cross-scene/HIR-JL 附录）距离 Sensors 第一稿 **缺 4 项硬指标**：

1. **完整外部信道证据**（DeepMIMO 或 CDL-A/C/D 全闭环）——当前已有 Sionna CDL 开发链和 DeepMIMO 计划规模标量-alpha 代理证据，但仍缺完整训练估计器与物理 angle/delay 指标，尚不能作为最终 Set E 结论。
2. **图表数量**——目前 1 张主图 + 4 张表，Sensors 期刊典型 5–6 主图 + 3–4 表，缺 3–4 张图。
3. **参考文献广度**——26 条偏少，Sensors 典型 40–60 条；缺 2024–2026 最新 ISAC/JCAS、tensor sensing、deep unfolding 工作。
4. **复杂度/运行时报告**——Sensors 偏工程，缺 FLOPs/参数量/wall-clock 对比表。

**判断**：开源工具链、DeepMIMO 数据接入和计划规模代理运行已打通。当前关键路径转为：完整训练 G2/T-OMP-Net 的 E2/E3 接入、E1 支持恢复改进、物理 angle/delay 指标以及 E4 缺失比较器。

---

## 1. Sensors 投稿格式要求（必须先锁定）

| 项目 | Sensors 期刊要求 | 当前状态 | 待办 |
|---|---|---|---|
| 模板 | LaTeX `Sensors.cls`（MDPI 官网下载） | 通用 `article` | 切换；保留现有 sections 内容 |
| 参考文献样式 | MDPI 数字格式，DOI 强制 | bibtex 26 条无 DOI 校验 | 全部补 DOI + URL，扩到 ~45 条 |
| 论文输出语言 | 英文投稿稿 + 中文并行稿 | 当前以英文草稿为主 | 每次生成 venue-facing paper 输出时同步产出 English/Chinese 双版本 |
| 摘要 | 200 词以内 | 当前约 230 词 | 压到 200 词内，保留 G2+A4 边界 |
| 关键词 | 5–7 个 | 暂无 | 起草："integrated sensing and communication; deep unfolding; tensor sparse recovery; mmWave MIMO-OFDM; off-grid estimation; Cramér–Rao bound; OMP" |
| 章节 | Introduction → Materials and Methods → Results → Discussion → Conclusions | 8 节学术风格 | 调整：把 §3/§4/§5 合并为 "Materials and Methods"，§6 → Results，§7 → Discussion |
| 字数 | 8000–12000 词主体（不算 ref） | 当前 LaTeX ~8500 词 | 扩到 10000–11000 词 |
| 图分辨率 | 300 dpi PDF / TIFF | PDF ok | 颜色复核（避免红绿对比） |
| Data Availability | 必须声明 | 暂无 | 添加：代码 + 合成数据生成脚本公开；DeepMIMO/CDL 引用原始来源 |
| License | CC-BY 4.0（开放获取） | 暂无 | 在 README/`paper2` 添加 license |

---

## 2. 实验证据补强规划（最高优先级）

### 2.1 工具链选型与环境搭建（开源全栈，无 license 阻塞）

**决策**：放弃 MATLAB 5G Toolbox，改用 **Sionna 为主、QuaDRiGa 为副、DeepMIMO Python 为外部信道源**的开源工具链。
理由：
- **license-free**：Sionna (Apache-2.0)、DeepMIMO Python (MIT-style)、QuaDRiGa (academic free)。审稿人可零成本复现，符合 Sensors 强调的 open science。
- **与现仓库同栈**：现有 `04_experiments/eval/run_stage2_torch_*.py` 已是 PyTorch；Sionna 输出 numpy → torch.tensor 零阻抗。
- **物理一致性**：Sionna 的 `sionna.channel.tr38901.CDL` 直接实现 3GPP TR 38.901 §7.7.1 CDL-A/B/C/D/E，是 nrCDLChannel 的等价开源替代。
- **可交叉校验**：QuaDRiGa 单独跑一次 CDL-D，与 Sionna 输出做 LSP/PDP 比对，写入附录作为"third-party-implementation cross-check"。

**Phase-Next E0（D+0 至 D+2，关键路径）**：

1. **装 Sionna**：`pip install sionna --break-system-packages`。固定版本 `sionna==0.18.0` 或最新稳定版，记入 `04_experiments/requirements_sensors.txt`。同时安装 `tensorflow==2.15.*`（Sionna 依赖）。
2. **装 DeepMIMO Python**：`pip install DeepMIMOv3 --break-system-packages`，并写一段 smoke 脚本 `04_experiments/eval/run_deepmimo_loader_smoke.py` 验证可读已就位的 `O1_60` 与 `I3_60`。
3. **DeepMIMO 数据状态确认**（rev.1 更新）：O1_60 与 I3_60 已下载到 `90_archive/2025_thesis_materials/参考/DeepMIMO-5GNR/DeepMIMO_dataset/`，**E0 数据阻塞已消除**。需做的：
   - 重跑 `04_experiments/eval/run_deepmimo_set_e_access_audit.m`（或改写为 Python 版 `run_deepmimo_set_e_access_audit.py`，避免 MATLAB 依赖），将 `Dataset file count` 与 `O1/O1_60 local asset hits`、`I3/I3_60 local asset hits` 三项从 missing 翻为 ok。
   - 修订 `05_results/deepmimo_set_e_access_audit/summary.md`，readiness 由 `partial` → `ready_open_source`，并显式写明"5G Toolbox 不再为本研究依赖"。
4. **QuaDRiGa 副路径**（可选，但推荐 W3 完成）：从 https://quadriga-channel-model.de 下载 QuaDRiGa v2.8，在 MATLAB 中跑一组 CDL-D 配置，导出 LSP 与 PDP 至 CSV，供附录交叉校验。无需 5G Toolbox。

**输出物**：
- `04_experiments/requirements_sensors.txt`
- `04_experiments/eval/run_deepmimo_loader_smoke.py`（成功读取 O1_60 一个 user 的信道）
- `04_experiments/eval/run_deepmimo_set_e_access_audit.py`（重写自 .m，无 MATLAB 依赖）
- `05_results/deepmimo_set_e_access_audit/summary.md`（readiness=ready_open_source）
- `04_experiments/eval/run_sionna_cdl_smoke.py`（成功生成一个 CDL-A 信道 batch）

### 2.2 必做实验清单（按优先级）

> 标记：★必须进 Sensors 主稿；☆进附录；△可选

**E1. CDL-A/C/D 跨 profile 全闭环（Sionna 实现）★**
- 新脚本：`04_experiments/eval/run_sionna_cdl_profile_generalization.py`
- 使用 `sionna.channel.tr38901.CDL` 直接生成 CDL-A/C/D 三 profile 的 OFDM 频域信道张量，与 `[N_subcarrier, N_tx, N_rx]` 对齐当前 Tensor-OMP 输入接口。
- 设计：
  - profiles：CDL-A（NLOS rich，K-factor=−inf）、CDL-C（NLOS, smaller delay spread）、CDL-D（LOS dominant，K-factor≈9 dB）
  - SNR：{0, 10, 20, 30} dB
  - L：{4, 8, 16}
  - 5 seed × 50 测试样本 / cell
  - 指标：channel NMSE、angle RMSE、delay RMSE、support recall
- 对比：grid Tensor-OMP、Tensor-OMP+oracle off-grid、T-OMP-Net (K=8)
- 老的 `run_cdl_profile_generalization_smoke.m` 不再扩展，保留作 MATLAB legacy；在脚本头注释引导后续维护者使用 Python 版。
- **产出**：Sensors §3.3 主表 + 主图（每个 profile 一组棒形/折线），manifest 存 `05_results/sionna_cdl_profile_generalization/`

**E2. DeepMIMO Set E (O1_60) 闭环（Python loader）★**
- 新脚本：`04_experiments/eval/run_deepmimo_o1_60_g2.py`
- 使用 `DeepMIMOv3` Python 包加载已就位的 O1_60 数据，提取 user grid 的 channel matrix → OFDM 频域信道张量
- 评测：G2 主网络 vs grid Tensor-OMP vs T-OMP-Net+早停门
- 设计：5 seed × 100 用户（grid 抽样） × SNR {0, 10, 20, 30} dB
- 指标：channel NMSE、angle RMSE、delay RMSE
- 注意：DeepMIMO 输出是 ray-traced 复合信道，**不**经过 nrCDLChannel；这正是 Sensors 期望的"非合成、ray-traced"外部证据。
- **产出**：Sensors §3.2 第二张主表 + 一张 NMSE-vs-SNR + 一张 user grid CDF 主图，manifest 存 `05_results/deepmimo_o1_60_g2/`

**E3. I3_60 内场景跨域泛化 ☆**
- 新脚本：`04_experiments/eval/run_deepmimo_i3_60_crossdomain.py`
- 协议：在合成数据（locked scale）上训练得到的 G2 权重，**直接**应用到 I3_60，无 fine-tune
- 同 E2 指标体系
- 若 NMSE 退化 < 3 dB → 写为"weak cross-domain holds"；若 3–6 dB → "partial"；若 > 6 dB → "fails, motivates domain adaptation in future work"。诚实记录。
- **产出**：附录跨域泛化表 + manifest `05_results/deepmimo_i3_60_crossdomain/`

**E4. 复杂度/运行时基准 ★**
- 在 `04_experiments/eval/` 新建 `run_complexity_benchmark.py`
- 测量：每个 forward 的 FLOPs（用 `thop`/`fvcore`）、参数量、CPU/GPU wall-clock、内存占用
- 对比对象：grid Tensor-OMP、ESPRIT/Unitary-ESPRIT、PARAFAC-ALS、T-OMP-Net (K=4/8/16)、T-OMP-Net + 早停门
- **产出**：Sensors §3.5 复杂度主表

**E5. 5L CRLB 全多目标 ☆**
- 当前 5L CRLB 是单目标 pilot；扩到 L=2,4 双/四目标在 SNR={10,20,30} dB 的 RMSE/CRLB ratio
- 仅作为 Theory 校验进附录，不放主图
- **产出**：附录表 + 一张 RMSE-vs-CRLB 趋势图

**E6. A4 SNR-aware 学习门（重试）△**
- 当前 scalar / kNN gate 已被诊断证否；除非 PI/SI 训练目标改写，否则跳过
- 若有时间：尝试 lightweight MLP gate（输入：[平均残差能量, 残差能量斜率, 估计 SNR]）+ Gumbel-Sigmoid
- 若仍失败：写进 Future Work，不再投入

**E7. 鲁棒性消融（HIR-JL 重训练）△**
- 当前 A5 在 main gate 下降级。若 phase noise/IQ imbalance/互耦三项都加入 robust training，是否能拉回主表？跑一组 pre-smoke 即可决策。
- 若仍失败：仅留附录"failure-mode analysis"

**E8. 大 sample 重测 ★**
- 现 G2 仅 5 seed × 小 batch。Sensors 评审会问"统计显著性"。
- 把 G2 seed 数提到 10，每 seed 测试样本 ≥ 500，给出 95% CI。
- **产出**：更新 `paper_evidence_table.md` 的 G2 行，把 CI 写入主表

### 2.3 实验排程（rev.1：5G Toolbox 阻塞消除，整体提前）

| 周次 | 任务 | 输出 |
|---|---|---|
| W1 | E0 (Sionna/DeepMIMOv3 安装 + smoke + audit 重跑) → E1 Sionna CDL-A smoke | requirements_sensors.txt、loader smoke 通过、E1 单 profile manifest |
| W2 | E1 跑齐 CDL-A/C/D × 全 seed → E2 O1_60 闭环 | E1/E2 主表主图 |
| W3 | E3 I3_60 跨域 + E4 复杂度基准 + E8 G2 10-seed CI | E3/E4/E8 manifest |
| W4 | E5 CRLB 多目标 + E7 HIR-JL 重训决策 + QuaDRiGa 副路径交叉校验 | 附录补 + cross-check 一段 |
| W5 | E6 决策 + paper_evidence_table 全量重聚合 + LaTeX 切 Sensors 模板 | v2.3R-Sensors evidence table、Sensors 模板可编译 |

---

## 3. 图表扩充计划

### 3.1 主图目标（5 张主图 + 必要时附录扩展）

| 编号 | 内容 | 数据源 | 状态 |
|---|---|---|---|
| **Fig.1** | 系统模型示意图（mmWave MIMO-OFDM ISAC 三维稀疏张量） | 矢量绘制（TikZ 或 Inkscape） | **缺，必须新增** |
| **Fig.2** | T-OMP-Net 展开架构图（K 层 unfolding、bounded off-grid block、Hungarian loss） | TikZ 矢量 | **缺，必须新增** |
| **Fig.3** | 现 evidence summary 图（G2 主结果 + A4 高 L 早停 + SNR sensitivity 三子图） | 已有 | 保留 + 视模板重排 |
| **Fig.4** | CDL profile 跨 profile NMSE/RMSE 棒形图或折线图（A/C/D × SNR） | E1 输出 | **待 E1 完成** |
| **Fig.5** | DeepMIMO O1_60 channel NMSE CDF 或散点 + box plot | E2 输出 | **待 E2 完成** |
| **Fig.6 (可选)** | 复杂度/wall-clock vs NMSE Pareto 散点 | E4 输出 | **待 E4 完成** |

### 3.2 主表目标（4 张主表 + 附录扩展）

| 编号 | 内容 | 状态 |
|---|---|---|
| **Tab.1** | G2 主结果（含 95% CI，5-10 seed） | 现 v2_3r_main_result_table.md，补 CI |
| **Tab.2** | CDL profile 跨 profile 主指标（channel NMSE / angle RMSE / delay RMSE） | **待 E1** |
| **Tab.3** | DeepMIMO Set E 主指标 | **待 E2** |
| **Tab.4** | 复杂度/参数量/wall-clock 对比 | **待 E4** |

附录表：A4 SNR 边界、A4 SNR-aware gate 诊断、Kruskal 边界、A5 失效模式、CRLB 趋势。

---

## 4. 文献扩充计划（26 → 45 条）

### 4.1 必补类别（按优先级）

| 类别 | 目标条数 | 关键搜索词 | 优先关注 |
|---|---:|---|---|
| 2024–2026 ISAC/JCAS 综述与 tutorial | +3 | "integrated sensing and communication 2025/2026", "6G ISAC tutorial" | Liu, Cui, Wei, Eldar 团队近期 |
| Tensor / CPD ISAC 算法 | +4 | "tensor decomposition mmWave channel estimation", "PARAFAC ISAC" | Nion-Sidiropoulos 系列、Wen 团队 |
| Deep unfolding for sparse recovery 2023–2026 | +4 | "deep unfolding OMP", "LISTA mmWave", "learned ISTA channel estimation" | Gregor-LeCun 后续、Eldar 组 |
| Off-grid / atomic norm | +3 | "atomic norm minimization channel estimation", "off-grid super-resolution mmWave" | Yang-Xie, Tang-Bhaskar |
| DeepMIMO / Sionna / QuaDRiGa benchmarks (rev.1 加重) | +4 | "DeepMIMO 2024/2025", "Sionna link-level simulator", "Sionna ray tracing", "QuaDRiGa channel model" | Alkhateeb (DeepMIMO)、Hoydis et al. (Sionna)、Jaeckel et al. (QuaDRiGa) — **每个必须有引用且引用最新版本**；Sionna 与 QuaDRiGa 因 rev.1 改路线，**必须 explicit 引用并写进 Data Availability** |
| 3GPP CDL / 38.901 信道建模 | +2 | "3GPP TR 38.901 CDL", "open-source 3GPP NR PHY" | 3GPP TR 38.901 V17.0.0 必须引用 |
| Hungarian / permutation-invariant loss | +1 | "Hungarian matching multi-target deep learning" | DETR 系列 |
| CRLB 估计理论 | +1 | "joint angle delay Doppler CRLB", "Bayesian CRLB ISAC" | Bekkerman-Tabrikian |
| 实测 mmWave 平台/USRP | +1 | "mmWave channel sounder ISAC measurement" | 强化 limitation 论证 |
| Hardware impairment | +1 | "phase noise IQ imbalance OFDM ISAC" | 支持 HIR-JL 附录 |

**总计：+24 条 → 50 条**（rev.1 因开源工具链多 +1），超过 Sensors 典型上限，可在最终稿压缩到 **42–45 条**。

### 4.2 具体执行步骤

1. 在 `02_literature_and_refs/literature_2024_2025/` 下按上述 9 个类别建子文件夹，存 PDF。
2. 用 Semantic Scholar API + Google Scholar 双源校对 2024–2026 顶刊与顶会（TSP、TWC、TVT、JSAC、ICASSP、CISS、SAM）。
3. 每条 bib 必须包含：DOI、URL、year ≥ 2018（综述类例外）。
4. 在 `02_literature_and_refs/v2_3r_literature_sprint_2026_06_25.md` 追加"Sensors-sprint addendum"段落记录新增条目与查证日期。
5. 不在主稿引用的非核心文献放入 `appendix/bibliography_extended.bib`，仅留在 supplementary materials 引用清单。

---

## 5. 章节内容补强（按 Sensors 风格调整）

### 5.1 摘要重写
- **必须**：开头一句强调 "We address [problem] in mmWave MIMO-OFDM ISAC by..."（Sensors 强调动机句）
- 量化结论必须包含：CDL 或 DeepMIMO 上的具体数字（待 E1/E2 完成后填）
- 末句明确给出"代码与脚本可在 GitHub 仓库取得"

### 5.2 Introduction（§1）
- 现状：18 行 evidence-led。Sensors 偏好 1.5–2 页 introduction：
  - 第一段：ISAC 背景与 6G 趋势（引 2024–2026 综述）
  - 第二段：mmWave MIMO-OFDM 联合估计的具体挑战（off-grid、复杂度、多目标）
  - 第三段：相关工作的不足（model-driven vs data-driven 对照）
  - 第四段：本文贡献 4 条（C1–C4，与现 v2.3R 对齐）
  - 第五段：文章结构

### 5.3 Materials and Methods（合并 §3+§4+§5）
- §2.1 System Model（保留现 §3 内容）
- §2.2 Tensor-OMP 基线 + 提出方法 T-OMP-Net（合并现 §4）
- §2.3 Theoretical bounds（Lemma 1 修订 + Lemma 2 trade-off 形式，保留现 §5）
- §2.4 Training and evaluation protocol（新增子节，明确：数据生成、loss 公式、超参表、硬件、随机种子策略、统计推断）

### 5.4 Results（替换现 §6）
- §3.1 Local synthetic baseline (G2)，更新 CI
- §3.2 **CDL profile generalization（E1，新核心）**
- §3.3 **DeepMIMO Set E (E2，新核心)**
- §3.4 Adaptive depth at high load（A4，保留现窄边界）
- §3.5 Complexity benchmark（E4，新）
- §3.6 Ablation：Kruskal、off-grid bound、CRLB 趋势

### 5.5 Discussion（替换现 §7）
- §4.1 Why bounded off-grid wins over grid OMP（机制讨论）
- §4.2 Why scalar plateau gate fails across SNR（A4 边界讨论 + 引诊断证据）
- §4.3 Limitations：external validation now narrowed to CDL+DeepMIMO Set E；real-measured platform 仍未覆盖
- §4.4 Future work：A5 robust training redesign、A6 meta-learning revisit、real measurement campaign

### 5.6 Conclusions（替换现 §8）
- 保留 1 页内
- 必须把 Sensors 实用价值显式写出："The proposed estimator is plug-compatible with 3GPP CDL profiles and the DeepMIMO O1 ray-traced scenarios..."

---

## 6. 工程任务清单

| 任务 | 优先级 | 负责文件 | 验收 |
|---|---|---|---|
| 切换 Sensors LaTeX 模板 | P0 | `06_paper_and_delivery/manuscript_v2_3r/latex/` 新建 `latex_sensors/` | 编译通过，13→14 页内 |
| 生成论文中英文双版本 | P0 | `06_paper_and_delivery/manuscript_v2_3r/latex_sensors_en/` 与 `latex_sensors_zh/`（或同等双语目录） | 英文投稿版与中文并行版内容、图表、证据边界同步 |
| 套用 MDPI bibtex 样式 | P0 | `latex_sensors/main.tex` 改 `\bibliographystyle{mdpi}` | bibtex 通过 |
| ~~解锁 5G Toolbox license~~（rev.1 移除） | — | — | 由开源 Sionna 替代 |
| 安装 Sionna + DeepMIMOv3 并冻结版本 | P0 | `04_experiments/requirements_sensors.txt` | `pip install -r` 全部成功，import 无报错 |
| ~~下载 DeepMIMO O1_60 / I3_60~~（rev.1 已完成） | — | `90_archive/.../DeepMIMO_dataset/` | 数据已在位 |
| 重写 DeepMIMO access audit 为 Python 版 | P0 | `04_experiments/eval/run_deepmimo_set_e_access_audit.py` | 输出 readiness=ready_open_source |
| 写 `run_sionna_cdl_profile_generalization.py`（E1） | P0 | `04_experiments/eval/` | A/C/D 5×50 与 CIR-grounded physical grid baseline 已完成；训练估计器比较仍待接入 |
| ~~写 `run_deepmimo_o1_60_g2.py`（E2 代理链已完成）~~ | P0 | `04_experiments/eval/` | 已输出 5 seed × 100 用户 manifest/CSV；完整训练模型仍待接入 |
| ~~写 `run_deepmimo_i3_60_crossdomain.py`（E3 代理链已完成）~~ | P1 | `04_experiments/eval/` | 已输出 5 seed × 100 用户 manifest/CSV；完整训练跨域模型仍待接入 |
| 写 `run_complexity_benchmark.py`（E4） | P1 | `04_experiments/eval/` | 输出 FLOPs/wall-clock 表 |
| G2 10-seed 重跑 + 95% CI（E8） | P1 | `04_experiments/eval/run_stage2_torch_locked_scale_g2_seed_sweep.py` 改 N_seed=10 | 主表更新 |
| 写 `run_5l_crlb_multitarget.py`（E5） | P2 | `04_experiments/eval/` | 附录 CRLB 趋势图 |
| HIR-JL robust training 决策实验（E7） | P2 | `04_experiments/eval/` 新 | 30 分钟 smoke，决定是否纳入主表 |
| QuaDRiGa CDL-D 交叉校验（副路径） | P2 | `04_experiments/eval/run_quadriga_cdl_cross_check.m` | LSP/PDP CSV 比对 |
| 新增系统模型图（Fig.1） | P0 | `06_paper_and_delivery/manuscript_v2_3r/displays/figures/` | TikZ 或 矢量 PDF |
| 新增 T-OMP-Net 架构图（Fig.2） | P0 | 同上 | TikZ 矢量 PDF |
| 重排 evidence summary 图 | P1 | 改 `build_v2_3r_paper_displays.py` | 三子图清晰、字号 ≥ 8pt |
| 安装 pytest 并跑单元测试 | P1 | `04_experiments/tests/` | `pytest -q` 全部 pass |
| 起草 cover letter | P2 | `06_paper_and_delivery/manuscript_v2_3r/cover_letter.md` | 含 novelty 4 点 + 推荐审稿人 3–5 名 |
| 起草 Data Availability statement | P0 | `latex_sensors/sections/09_data_availability.tex` | 含 GitHub 仓库 URL + DeepMIMO 引用 + Sionna/QuaDRiGa 引用 |
| 完成 graphical abstract | P2 | `displays/figures/graphical_abstract.pdf` | 单图 200 字内可读 |

---

## 7. 风险与门控

| 风险 | 等级 | 缓解策略 |
|---|---|---|
| ~~5G Toolbox license 无法解决~~（rev.1 消除） | — | 已转 Sionna 主链 + QuaDRiGa 副链 |
| ~~DeepMIMO O1_60 数据下载缓慢/失败~~（rev.1 消除） | — | 数据已在位 |
| Sionna/TensorFlow 与现 PyTorch 栈冲突 | 中 | Sionna 只用作"信道生成器"，输出 numpy；下游 estimation 仍在 PyTorch 内进行；TF 与 PyTorch 同进程共存可行但需关 TF GPU memory growth (`tf.config.experimental.set_memory_growth`) |
| Sionna 版本升级破坏 API（如 0.18 → 1.x） | 中 | 在 `requirements_sensors.txt` 显式 pin 版本；CI 不允许浮动 |
| DeepMIMOv3 与已下载 5GNR 数据 schema 不匹配 | 中 | W1 第一件事：跑 `run_deepmimo_loader_smoke.py`，若 schema 不兼容，回退到 `DeepMIMOv2` (legacy) 或自写 `.mat` 直接读取器 |
| CDL 跑通后 NMSE 不达预期 | 中 | 已在 E7 准备 HIR-JL robust training；同时保留 local synthetic 主结果作为防守 |
| 10-seed 重测时 G2 CI 跨越 0 dB | 低 | 现 5-seed min gain 已 4.47 dB，远大于 0；扩到 10 seed 风险很低 |
| 复杂度对比对手不公平 | 中 | 选择 **同 K 层 unfolding 但无 off-grid block** 的 reference 模型作为对照，避免拿手写慢实现欺负他人 |
| Sensors 评审要求 measurement-based 验证 | 中 | 明确 limitation；引用近期 USRP/CIR sounder 工作，承诺 future work；DeepMIMO ray-traced 已经回应了"非合成"层面的质疑 |
| Lemma 2 trade-off 措辞被再次质疑 | 低 | 现 v2.3R 已修正；交付前请数学审过 §5.1.2 一次 |
| Sionna CDL 与 nrCDLChannel 数值差异被质疑 | 低 | W4 用 QuaDRiGa CDL-D 做 third-party LSP/PDP 比对，写入附录"open-source CDL cross-implementation check" |

---

## 8. 提交前 Definition-of-Done 清单

- [ ] LaTeX 用 Sensors 官方模板，编译无 error/warning（允许 layout polish）
- [ ] 论文输出包含英文 Sensors 投稿版与中文并行版，且 claim/evidence 边界一致
- [ ] 主图 ≥ 5，每图独立标题与说明，PDF 矢量
- [ ] 主表 ≥ 4，含 95% CI 或 std
- [ ] 参考文献 ≥ 40，全部含 DOI
- [ ] 摘要 ≤ 200 词、含一个 CDL/DeepMIMO 数字结论
- [ ] 关键词 5–7
- [ ] Data Availability statement
- [ ] Conflict of Interest 声明
- [ ] Author Contribution 声明
- [ ] Code repo 公开（GitHub），README 含一键复现脚本
- [ ] DeepMIMO Set E (O1_60) 至少 channel NMSE 主结果通过（DeepMIMOv3 Python loader）
- [x] DeepMIMO I3_60 跨域代理结果已明确归类为 `partial`（完整训练 E3 仍待完成）
- [ ] CDL 至少 A/C/D 三种 profile 主结果通过（Sionna；5×50、physical grid baseline 与 clean floor 已完成，训练模型比较仍待完成）
- [ ] QuaDRiGa CDL-D 第三方交叉校验存档（即便仅作附录）
- [ ] Cover letter 起草 + 推荐审稿人 3 名
- [ ] 全文 plagiarism check（iThenticate / Turnitin） ≤ 15%

---

## 9. 与 v2.3R 现有主文档的对接关系

- 本规划**不**修改 `ISAC_DeepUnfolding_TechnicalDesign_v2.3R.md`，技术设计依旧锁定 v2.3R。
- 本规划**追加**到 `01_design_and_plan/`，与 `V2_3R_PROGRESS_AUDIT_2026_06_25.md` 平行，作为下一阶段执行版。
- 每完成一个 E1–E8 实验，需要：
  1. 在 `05_results/` 新建对应目录
  2. 重新跑 `aggregate_v2_3r_paper_evidence_table.py`
  3. 更新 `paper_evidence_table.md`（追加新行而不是改写旧 G2/A4 行）
  4. 同步 `claim_evidence_ledger.json`
- 论文层面新增章节统一进 `06_paper_and_delivery/manuscript_v2_3r/latex_sensors_en/` 与 `latex_sensors_zh/`（或等价双语目录），与现 `latex/` 平行，避免污染当前可编译版本；两版必须共用同一证据表与 claim ledger。

---

## 10. 投稿阶梯回退策略

| 投稿阶段 | 触发条件 | 行动 |
|---|---|---|
| Sensors 第一稿（首选） | E1+E2+E4+E8 全部通过 | 按本规划提交 |
| Sensors 被拒（major revision） | 评审要求 measurement 数据 | 增补 Sionna ray tracing 或公开 5G NR sounder 数据集（如 NIST mmWave）作为补充实验，重投 |
| Sensors 被拒（不可重投） | 拒稿原因为 scope mismatch | 转 IEEE Systems Journal（容忍度更高、scope 接近） |
| Systems Journal 也不顺 | — | 转 IEEE TVT；同时增补 vehicular ISAC 用例与多普勒维实验 |
| 长期 | 若 measurement-based 数据 + robust training 都准备好 | 冲 IEEE TSP / TWC，作为期刊扩展版 |

---

## 附：本规划评估签字位

- 数学/Lemma 复核：______
- 实验编排复核：______
- 文献策略复核：______
- 投稿模板复核：______
- 最终提交批准：______

> 评估人补充意见（手写或追加 PR）：
