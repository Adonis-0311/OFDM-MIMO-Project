# 毕设可用内容与 v2.2 实验缺口梳理

## 操作基线

本轮以 `ISAC_DeepUnfolding_TechnicalDesign_v2.2.md` 为基线。v2.2 的新增硬要求主要集中在三类：

- A3: DeepMIMO Set E 从选做改为必做，但只承担信道 NMSE、角度 RMSE、时延 RMSE、跨场景泛化，不承担速度 RMSE。
- B2: Off-Grid Mismatch Lemma 需要实验支撑，尤其是网格失配与 off-grid 修正后的误差趋势。
- B3: §6.5.13 需要字典过采样比敏感性、Kruskal 可辨识性和复杂度/延迟折中。

## 现有可复用内容

| 类别 | 文件/目录 | 可用性 | 说明 |
|---|---|---:|---|
| 论文/答辩材料 | `2025刘雨辉毕设/` | 高 | 已有本科毕设终稿、答辩 PPT、开题/中期/评分表等，可作为写作素材和图表来源；其中含个人材料，不建议直接上传公开仓库。 |
| 技术路线 | `ISAC_DeepUnfolding_TechnicalDesign_v2.2.md` | 高 | 可作为后续论文升级和实验排期的操作基线。 |
| MATLAB 原型 | `Config/`, `Modules/`, `main.m` | 中 | 已有 OFDM、CDL-like 信道、LS/ANN/CS-DL 命名模块，但接口未完全闭合，需要重构后才能成为主实验 pipeline。 |
| DeepMIMO 参考 | `2025刘雨辉毕设/参考/DeepMIMO-*` | 中 | 有 MATLAB 版本参考代码和 README，可用于后续 Set E 数据接入；场景数据本体仍需确认是否已经下载。 |
| 已有图片 | `method_comparison*.png`, `OMP_performance_comparison.png` | 中 | 可作为本科阶段结果展示素材；v2.2 论文中需重新标注实验设置并尽量复跑。 |
| 文献 PDF | `2025刘雨辉毕设/参考/阅读文献/` | 中 | 覆盖 CS、MIMO-OFDM、DL-CS 等基础文献；v2.2 还需要补 2024-2025 SOTA。 |

## 当前代码风险

- `main.m` 调用 `params.sys.SNR`、`params.pilotIndices` 等字段，但 `SystemParams.m` 未定义这些字段。
- `LS_Estimator.m` 假设 `rxPilot(:,:,sc)`、`txPilot(sc,:)` 的三维/二维形状，但 `OFDM_Transceiver.Transmit` 输出为 `[Nt, NumSubcarriers]`。
- `ANN_Estimator.m` 的方法中直接引用 `params`，应改为 `obj.params`。
- `CS_DL_Estimator.m` 将两个 `classdef` 放在同一文件中，且构造/调用方式与 `main.m` 不一致。
- `PilotManager.InsertPilots` 使用了未传入的 `numSubcarriers`、`dataIndices`。

这些问题说明：现有工程适合保留为本科原型和素材，但 v2.2 主线实验建议新建独立 pipeline，再逐步迁移可用模块。

## 已补实验

新增 `eval/run_oversampling_offgrid_ablation.m`：

- 对应 v2.2 §6.5.13 的字典过采样敏感性。
- 同时支撑 §5.1.1 Off-Grid Mismatch Lemma 的实验直觉。
- 输出目录：`Results/oversampling_offgrid_ablation/`
- 输出文件：CSV、MAT、PNG、PDF、Markdown summary。

该脚本是轻量 smoke/ablation，不声称为最终 T-OMP-Net 训练结果。它隔离单个 angle-delay-Doppler 分量，比较 coarse grid matching 与 bounded local off-grid refinement。

## 下一批实验优先级

| 优先级 | 实验 | 对应大纲 | 目的 |
|---:|---|---|---|
| P0 | 修复主 MATLAB pipeline，统一参数、信道、估计器接口 | §6.1-6.4 | 让 LS/OMP/CS-DL baseline 可批量复跑。 |
| P0 | Tensor-OMP baseline | §4.1, §6.3 | 作为 T-OMP-Net 和 off-grid 的传统可解释 baseline。 |
| P1 | 过采样比完整扫描：`rho_theta/rho_tau/rho_nu={1,2,4,8}` | §6.5.13(a) | 量化推荐 `rho=2` 的性能-复杂度折中。 |
| P1 | Kruskal 可辨识性退化：`L={2,4,8,16,32,64}` | §6.5.13(b,c) | 回应“字典维度和目标数是否合理”。 |
| P1 | CDL-A/C/D 泛化 | §6.2 Set B-D | 通信侧泛化必做。 |
| P2 | DeepMIMO O1/I3 接入 | §6.2 Set E | 外部数据集验证，速度 RMSE 不纳入。 |
| P2 | CRLB 高 SNR 渐近紧致性 | §5.2, §6.5.5 | 支撑理论分析。 |

## Git 上传策略

建议远端仓库名：`mmwave-isac-tompnet`。

本轮默认上传：

- 技术设计 Markdown。
- MATLAB 源码与新增实验脚本。
- 新增实验结果图表/CSV/summary。
- 内容梳理文档。

默认不上传：

- `2025刘雨辉毕设/` 中的个人材料、合同、评分表、论文 Word/PDF、外部参考压缩包。
- `.mat` 模型/数据中间件。
- 大型下载数据集。

