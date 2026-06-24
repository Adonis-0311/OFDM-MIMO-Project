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

新增 `eval/run_kruskal_identifiability_ablation.m`：

- 对应 v2.2 §6.5.13(b,c) 的 Kruskal 可辨识性与目标数退化实验。
- 使用轻量 on-grid 多目标张量与 Tensor-OMP 风格逐次检测，扫描 `L={2,4,8,16,24,32}`。
- 输出目录：`Results/kruskal_identifiability_ablation/`
- 输出文件：CSV、MAT、PNG、PDF、Markdown summary。
- 当前 smoke run 的本地张量尺寸为 `32 x 16 x 16`，本地 Kruskal 界为 31；v2.2 论文尺度 `128 x 16 x 32` 的理论界仍为 87。
- 由于该 smoke run 是 on-grid 且 SNR=20 dB，`P_d` 不一定在接近界限时急剧下降；更适合作为“NMSE、精确支撑率、运行时间随 L 增长”的早期证据。最终论文版仍需补 off-grid、多目标间隔受限、低 SNR 等更强压力设置。

新增 `eval/run_offgrid_mismatch_lemma_validation.m`：

- 对应 v2.2 §5.1.1 Off-Grid Mismatch Lemma 与 Phase 3 的实证 Lemma 1。
- 扫描 `Nv={16,32,64,128}` 与角度中心 `{-45,-20,0,20,45}`，拟合 `epsilon_grid ≈ beta * delta_theta^2`。
- 对比拟合系数与 `(pi^2/12) * Nv^2 * cos(theta)^2` 的理论尺度，并验证残差修正后的系数约按残差比例平方下降。
- 输出目录：`Results/offgrid_mismatch_lemma/`
- 输出文件：summary CSV、sample CSV、PNG、PDF、Markdown summary。

新增 `eval/run_cdl_profile_generalization_smoke.m`：

- 对应 v2.2 §6.2 Set B-D 的 CDL-A/C/D 通信侧泛化 smoke 实验。
- 使用 compact CDL-like 生成器区分 delay spread、路径数与 LOS K-factor，比较 full-pilot LS 与 delay-sparse denoising 的 NMSE。
- 输出目录：`Results/cdl_profile_generalization_smoke/`
- 输出文件：CSV、PNG、PDF、Markdown summary。
- 边界：该脚本不是完整 3GPP TR 38.901 实现；最终论文版应替换为标准 CDL 或 MATLAB 5G Toolbox pipeline，并接入 T-OMP-Net inference。

新增 `eval/run_crlb_delay_asymptotic_smoke.m`：

- 对应 v2.2 §5.2 与 §6.5.5 的 CRLB 高 SNR 渐近紧致性 smoke 实验。
- 使用单路径时延估计模型，在未知复增益 nuisance 参数下计算 CRLB，并用 ML/NLS 搜索估计 RMSE。
- 输出目录：`Results/crlb_delay_asymptotic_smoke/`
- 输出文件：CSV、PNG、PDF、Markdown summary。
- 边界：该脚本不是完整 5L 联合 range-velocity-angle CRLB，只验证 CRLB 曲线与图表管线。

新增 `eval/run_deepmimo_set_e_access_audit.m`：

- 对应 v2.2 §6.2 Set E 的 DeepMIMO 外部数据接入审计。
- 检查本地 DeepMIMO MATLAB/5GNR 代码包、参数文件、O1/I3 场景数据、MATLAB 5G Toolbox 许可与 `nrCDLChannel` 可用性。
- 当前审计结论：代码包与 O1 参数模板存在，但 O1/I3 场景数据缺失，I3 参数引用缺失，5G Toolbox license test 未通过；Set E 性能实验仍为 partial/blocked 状态。
- 输出目录：`Results/deepmimo_set_e_access_audit/`
- 输出文件：CSV、Markdown summary。

新增 `eval/run_all_v2_2_supplemental_experiments.m`：

- 一键复跑当前六组 v2.2 轻量补充实验/审计。
- 生成 `Results/v2_2_supplemental_manifest.md` 与 `Results/v2_2_supplemental_manifest.csv`。
- 汇总每组实验的目标章节、状态、耗时、summary 路径和关键证据。

## 下一批实验优先级

| 优先级 | 实验 | 对应大纲 | 目的 |
|---:|---|---|---|
| P0 | 修复主 MATLAB pipeline，统一参数、信道、估计器接口 | §6.1-6.4 | 让 LS/OMP/CS-DL baseline 可批量复跑。 |
| P0 | Tensor-OMP baseline | §4.1, §6.3 | 作为 T-OMP-Net 和 off-grid 的传统可解释 baseline。 |
| P1 | 过采样比完整扫描：`rho_theta/rho_tau/rho_nu={1,2,4,8}` | §6.5.13(a) | 已有轻量版本；下一步扩到论文尺度并补 FLOPs。 |
| P1 | Kruskal 可辨识性退化：`L={2,4,8,16,32,64}` | §6.5.13(b,c) | 已有轻量版本；下一步补低 SNR / off-grid 压力设置。 |
| P1 | Off-grid mismatch lemma 验证 | §5.1.1, Phase 3 | 已有轻量版本；下一步合并进理论章节图表。 |
| P1 | CDL-A/C/D 泛化 | §6.2 Set B-D | 已有轻量 CDL-like smoke；下一步替换为标准 3GPP CDL pipeline。 |
| P2 | DeepMIMO O1/I3 接入 | §6.2 Set E | 已有接入审计；需下载 O1/I3 场景数据并确认 5G Toolbox 许可后才能跑性能。 |
| P2 | CRLB 高 SNR 渐近紧致性 | §5.2, §6.5.5 | 已有单延迟 smoke；下一步扩展为完整 5L 联合 CRLB。 |

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
