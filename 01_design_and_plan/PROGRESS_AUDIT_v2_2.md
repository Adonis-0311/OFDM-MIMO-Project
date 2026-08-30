# v2.2 进度审计与下一步推进计划

> 审计时间：2026-06-24
> 基线文档：`01_design_and_plan/ISAC_DeepUnfolding_TechnicalDesign_v2.2.md`
> 目标期刊（首投顺序）：Signal Processing (Elsevier, Q2) → DSP (Elsevier, Q2) → IEEE Sensors (Q1/Q2) → IEEE Systems (Q2)

---

## 1. 本次整理动作

| 操作 | 结果 |
|---|---|
| 删除 `06_paper_and_delivery/paper2_package/` | 该目录是早期扁平布局（`eval/` `Results/` `paper/` 等）下的整包快照，其内容已 100% 重复于：根目录 `04_experiments`/`05_results`/`07_ops`/`paper_notes`（最新路径）+ `90_archive/old_experiment`（本科原型 `Modules/Config/main.m/untitled*.m/method_comparison*`）。验证手段：`diff -rq` 全量比对。 |
| 归档 v1/v2/v2.1 设计文档 | 移入 `90_archive/design_history/`，活跃目录仅保留 v2.2。v2.2 §0 已含变更对照，不会丢失追溯链。 |
| 改写 `90_archive/old_experiment/README.md` | 移除原 README 误指向 `eval/`、`paper2/` 的错路径，明确：90_archive = 本科毕设阶段产物的只读归档，不计入 v2.2 论文产出。 |
| 改写根 `README.md` | 移除 `paper2_package` 引用；新增"归档约束"段，约束 `90_archive/2025_thesis_materials`、`90_archive/old_experiment`、`90_archive/design_history` 三类历史内容与本论文产出隔离。 |
| 新增 `90_archive/design_history/README.md` | 标记三版历史设计文档用途与替代关系。 |

清理前后文件数：260 → 193（含 .git 之外约 67 个重复/陈旧文件已剔除）。

---

## 2. 当前活跃目录与 v2.2 章节映射

```
01_design_and_plan/    ── ISAC_DeepUnfolding_TechnicalDesign_v2.2.md（唯一活跃技术大纲）
02_literature_and_refs/literature_2024_2025/   ── v2.2 §2.4 SOTA 调研（仅占位 README）
03_active_modules/baseline/    ── §6.3 八种 baseline 规划（仅占位 README）
03_active_modules/tompnet/     ── §4 T-OMP-Net 实现规划（仅占位 README）
03_active_modules/train/       ── §4.2.1 四阶段课程训练规划（仅占位 README）
04_experiments/eval/           ── 6 个 v2.2 补强 smoke 实验脚本（已实现）
05_results/                    ── 6 组 smoke 结果 + manifest（已落盘）
06_paper_and_delivery/paper_notes/   ── usable_content_inventory.md（实验缺口梳理）
07_ops/scripts/                ── GitHub 发布脚本
90_archive/                    ── 本科毕设材料 / 本科 MATLAB 原型 / 历史设计版本（不计入论文产出）
```

---

## 3. 论文章节 × 实验进度状态表

按 v2.2 大纲推演的状态："✓ 完成"代表已有可用产物；"smoke"代表只有轻量验证；"占位"代表只有规划 README；"空"代表完全未启动。

| 章节 | v2.2 关键产物 | 当前状态 | 证据/缺口 |
|---|---|---|---|
| §1 Introduction | 重写 4 段、四要素融合表述、贡献 bullet | 文档已写 | v2.2.md 已包含；论文撰写阶段直接复用 |
| §2.1-2.3 Related Work | 三类相关工作综述 | 文档已写 | v2.2.md 已包含 |
| **§2.4 SOTA 对标表** | 2024-2025 4 类 SOTA 各 2-3 篇具名引用 | **占位** | `02_literature_and_refs/literature_2024_2025/README.md` 只有 4 类关键词，未开始检索；W18-19 前必须完成 |
| §2.5 Research Gap | 全 ✓ 唯一组合定位 | 文档已写 | 依赖 §2.4 实例填空 |
| §3.1-3.4 System Model | FDMA / 虚拟阵列 / 3D 稀疏张量 | 文档已写 | v2.2.md 已含；代码侧无验证 |
| **§3.1.1 FDMA/DDM/TDM SE 表** | trade-off 表 + 选 FDMA 理由 | 文档已写 | v2.2.md 已含；无代码佐证（理论级） |
| §4.1-4.6 T-OMP-Net | Algorithm 1/2、课程、off-grid、Hungarian、提取 | **未实现** | `03_active_modules/tompnet/` 仅占位 README；**这是论文核心算法，目前 0 行可运行代码** |
| **§5.1.1 Off-Grid Mismatch Lemma** | Lemma 1 + Corollary 1 + 附录 D | 文档+smoke ✓ | smoke 拟合系数中位数 0.4978 ≈ 理论 π²/12=0.822 的一半量级；残差修正后 β 比降至 0.010，趋势对；正式版需补附录 D 完整推导 |
| §5.2 CRLB | 5L 联合 FIM | 部分 ✓ | smoke 只验证了单时延、未知复增益 nuisance，SNR≥20 dB 时 RMSE/√CRLB=1.023（紧致性 OK）；**5L 联合 CRLB 仍需推导** |
| §5.3 复杂度 | FLOPs / 推理延迟 | 文档已写 | 无 T-OMP-Net 实现 → 无法实测 |
| §6.1 仿真设置 | Table 1-3 参数 | 文档已写 | v2.2.md 已含 |
| §6.2 Set A | 自定义参数化 ISAC 多目标 | **未实现** | 无端到端数据生成器 |
| §6.2 Set B/C/D | 3GPP CDL-A/C/D | smoke ✓ | `cdl_profile_generalization_smoke` 用 CDL-like 而非标准 3GPP，delay-sparse 相对 full-pilot LS 在 10 dB 改善 5.35 dB；正式版需 MATLAB 5G Toolbox `nrCDLChannel` |
| **§6.2 Set E DeepMIMO** | O1/I3 跨场景泛化（v2.2 改为必做） | **阻塞** | 审计显示：MATLAB 代码包存在、O1 参数模板有，但 O1/I3 场景数据 0、I3 参数引用 0、5G Toolbox license 测试未过；必须先解决数据下载与 license |
| §6.3 Baselines | LS/LMMSE/OMP/SOMP/SBL/Tensor-OMP/CS-DL + 2024-2025 SOTA | **占位** | `03_active_modules/baseline/` 只有规划；本科 `LS_Estimator/ANN_Estimator/CS_DL_Estimator` 接口已知坏（见 usable_content_inventory §"当前代码风险"） |
| §6.4 评价指标 | NMSE/BER/RMSE/FLOPs/延迟 | 文档已写 | 实现绑定 §6.3 |
| §6.5.1-6.5.12 | 主性能/少导频/高速移动/未知 L/阵列误差 | **未启动** | 0 个对应脚本 |
| **§6.5.13(a) 过采样比** | $\rho_\theta/\rho_\tau/\rho_\nu \in \{1,2,4,8\}$ | smoke ✓ | `oversampling_offgrid_ablation`：$\rho=2$ 时 bounded off-grid 把均值 NMSE 从 −8.54 dB 拉到 −55.95 dB；正式版需扩到论文尺度 + FLOPs 测量 |
| **§6.5.13(b,c) Kruskal** | $L \in \{2,4,8,16,32,64\}$ + 退化 | smoke ✓ | `kruskal_identifiability_ablation`：本地张量 32×16×16（界=31），论文目标 128×16×32（界=87）；当前 on-grid + SNR=20 dB，需补 off-grid + 低 SNR 压力 |
| §6.6 消融 A0-A7 | 八组变体 | **未启动** | 依赖 §4 实现 |
| §6.7 跨场景与联合 ISAC | DDM 备选讨论 | **未启动** |  |
| §7 Conclusion | 三个未来方向 | 文档已写 |  |

**总体百分比估计**：写作（章节文字）≈ 70%；实验（脚本+结果）≈ 15%（仅六组 smoke）；核心算法（T-OMP-Net 代码）≈ 0%；外部数据接入（Set E）≈ 0%。

---

## 4. 关键瓶颈与风险

按对论文命中率的影响排序：

1. **T-OMP-Net 主算法代码不存在**（最大瓶颈）
   - §4.1–4.6 / §6.3 / §6.5.1–6.5.12 / §6.6 全部依赖此实现
   - 当前 6 个 smoke 全部规避了真正的展开网络；任何对算法层贡献的实验断言都无证据
   - v2.2 排期把 Phase 2 (M2, 4 周) 划给最小版本 T-OMP-Net；目前 Phase 2 = 0 进度

2. **本科 MATLAB 原型不能直接利用**
   - `LS_Estimator/ANN_Estimator/CS_DL_Estimator/PilotManager` 与 `SystemParams/OFDM_Transceiver` 接口未闭合
   - usable_content_inventory 已给出 5 项具体故障点
   - 必须新建独立 pipeline（而非 patch），把可用模块迁移过来

3. **DeepMIMO Set E 阻塞**（v2.2 把它从选做改成了必做）
   - O1/I3 场景数据未下载、5G Toolbox license 未确认
   - 影响 A3 主线补强；若失败，必须降级到"扩充自定义场景"并在投稿信中说明

4. **§2.4 SOTA 对标表无内容**
   - v2.2 提升命中率的关键支柱之一
   - 若直到投稿前才检索，时间风险高

5. **Lemma 1 附录 D 完整推导未落字**
   - smoke 已有数值印证，但论文需要正式证明文档

6. **5L 联合 CRLB 未推导**
   - smoke 只覆盖单时延 nuisance 模型，与 v2.2 §5.2 要求差一阶

---

## 5. 推进计划（按 v2.2 Phase 排期对齐当前节点）

按"代码主线 + 文档主线 + 数据主线"三轨并进。建议两周内逐项启动。

### 5.1 P0 —— 解锁主线（未来 2-4 周）

P0-1：**最小可运行 ISAC pipeline（Set A）**
- 位置：新建 `03_active_modules/baseline/` 下 MATLAB 模块，不要 patch `90_archive/old_experiment`
- 目标：参数化生成发射 OFDM 信号、虚拟阵列接收、3D 数据立方体、单/多目标 ground truth
- 验收：能跑通从 SystemParams → Transceiver → 3D 张量输出 → 简单 LS baseline 估计 → NMSE 数字
- 风险点：和 v2.2 §3.1/3.2 公式严格一一对照（FDMA 子载波交织、虚拟阵列对齐）

P0-2：**Tensor-OMP 经典 baseline 实现**
- 位置：`03_active_modules/baseline/tensor_omp/`
- 目标：v2.2 Algorithm 1（不带可学习参数）
- 验收：在 Set A 上对单目标和 L=3 多目标的角度/时延/多普勒恢复 RMSE 与 CRLB 接近
- 价值：是 §6.6 中 A0 baseline；也直接对应 §6.5.13 中"w/o off-grid"对照

P0-3：**修复 `06_paper_and_delivery/paper_notes/usable_content_inventory.md` 内的接口故障清单**
- 把 5 个故障点（params 字段、rxPilot 形状、obj.params、双 classdef、PilotManager 字段）标记为：A 直接遗弃，B 重构后迁入新 pipeline
- 已有 method_comparison 图作为对比素材标注实验设置后可继续引用

### 5.2 P1 —— 论文核心算法（未来 4-8 周，对应 Phase 2-3）

P1-1：**T-OMP-Net 最小版本**（v2.2 §4.1-4.2）
- 位置：`03_active_modules/tompnet/`
- 范围：先实现"硬支撑 + 固定字典"的展开层；课程仅启用 Teacher Forcing 阶段
- 验收：训练后 NMSE 不低于 Tensor-OMP

P1-2：**Off-grid 物理约束模块**（v2.2 §4.3, §5.1.1）
- tanh 重参数化、$\pm \Delta_{grid}/2$ 界
- W11 验收点（v2.2 排期）：**实测 ε_grid vs (δθ)² 拟合系数 vs C₁N_v²cos²θ\***（直接落地 Lemma 1 实证）
- 当前 smoke 已经初步做到，未来需在端到端 pipeline 中复测

P1-3：**Hungarian 配对联合损失**（v2.2 §4.4.1）
- 验收：和 §6.2 Set A 上的多目标 RMSE 一并出曲线

P1-4：**四阶段课程**（v2.2 §4.2.1）
- Gumbel-Softmax → STE → Hard
- 训练日志、loss 曲线、收敛性能落 `05_results/training_curriculum/`

### 5.3 P2 —— 外部数据与理论闭环（M5-M6，对应 Phase 4-5）

P2-1：**3GPP CDL-A/C/D 标准实现**
- 把 `cdl_profile_generalization_smoke` 升级为 `nrCDLChannel`
- 验收：NMSE 与本文 T-OMP-Net 直接对接，Set B/C/D 各出一组曲线

P2-2：**DeepMIMO Set E 解锁**
- 步骤 1：下载 O1、I3 场景 raw 数据（v2.2 §6.2 必做）
- 步骤 2：确认 5G Toolbox license（access audit 中标红）
- 步骤 3：扩展 `run_deepmimo_set_e_access_audit` 到性能脚本
- 若 Toolbox license 不可得，立即启用 "纯射线追踪 → 自实现 5G NR 链路"备案

P2-3：**5L 联合 CRLB 完整推导**
- 由 v2.2 §5.2 给出 FIM 偏导
- smoke 升级为完整 $\eta \in \mathbb{R}^{5L}$ 数值差分交叉验证
- 用于 §6.5.5

P2-4：**Lemma 1 附录 D 完整证明**
- v2.2 §5.1.1 已给草图；落字仅需 2-3 天
- 配套 §6.5.13(a) 数据拟合系数对比图

### 5.4 P3 —— 文献与撰写（W18-W23）

- §2.4 SOTA 表：4 类 × 2-3 篇 = 8-12 篇 IEEE Xplore/arXiv 检索 + 引用入库
- §6.5.13(b,c) 升级到 128×16×32 + off-grid + 低 SNR 压力设置
- 全文图表回填、Section 7 数值替换占位

### 5.5 缓冲（M7-M8）

v2.2 已留 8 周。建议优先吸收：T-OMP-Net 训练超期、DeepMIMO 接入超期、SOTA 文献检索超期。

---

## 6. 立即可执行（本周）

1. **代码侧**：开 `03_active_modules/baseline/` 子目录，开始 P0-1 的 SystemParams 与 OFDM/虚拟阵列模块；不要再 touch `90_archive/old_experiment`。
2. **文档侧**：把本审计文档作为 `01_design_and_plan/PROGRESS_AUDIT_v2_2.md` 提交；后续每月 1 日刷新状态表。
3. **数据侧**：发起 DeepMIMO O1/I3 场景下载请求 + 确认 5G Toolbox license；阻塞要尽早暴露。
4. **文献侧**：用 v2.2 §2.4 给的 4 组关键词每周做一次 Google Scholar/arXiv 检索，结果直接落 `02_literature_and_refs/literature_2024_2025/`，最迟 W18 闭合。
5. **Git 侧**：本次清理后做一次提交，把 `paper2_package` 删除、设计文档归档、README 改写一并固化。

---

## 7. 关键命中率风险（与 v2.2 §4.1 比对）

v2.2 预估 Signal Processing 命中率从 v2.1 的 40% 提升到 75%。该提升的支撑全部依赖：

- A1 SOTA 对标表 —— **当前 0%**
- A2 段落 4 重写 —— ✓ 已落字
- A3 DeepMIMO 必做 —— **当前 0%**，且阻塞
- B1 SE trade-off 表 —— ✓ 已落字
- B2 Lemma 1 形式化 —— 推导草图✓，附录 D 未写，smoke 已有方向性验证
- B3 §6.5.13 字典严谨性 —— smoke ✓，论文尺度未跑

若 A1/A3 不能在 W17-W19 前补齐，命中率回落到 v2.1 水平（约 40%）；其余三项目前进度可控。
