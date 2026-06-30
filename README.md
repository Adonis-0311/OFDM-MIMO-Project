# mmWave ISAC T-OMP-Net 研究工作区

本仓库按项目推进逻辑整理：先看技术路线，再查文献与参考资料，随后进入模块开发、可复现实验、结果归档、论文交付和历史资料归档。

当前技术主线基线为：

```text
01_design_and_plan/ISAC_DeepUnfolding_TechnicalDesign_v2.3R.md # 当前 paper-facing 主技术文档
05_results/v2_3r_paper_evidence_table/paper_evidence_table.md  # 当前证据/claim 边界总表
02_literature_and_refs/v2_3r_references.bib                    # 当前 Related Work 引用草案
01_design_and_plan/V2_3R_PROGRESS_AUDIT_2026_06_25.md          # v2.3R 进度审计与下一步
01_design_and_plan/V2_3R_STEADY_EXECUTION_PLAN.md              # v2.3R 稳妥执行计划
01_design_and_plan/ISAC_DeepUnfolding_TechnicalDesign_v2.2.md
01_design_and_plan/PROGRESS_AUDIT_v2_2.md              # 实验/章节进度审计
01_design_and_plan/V2_2_DIRECTION_REVALIDATION.md      # 2024-2026 SOTA 重评估
```

> v2.3 增量计划文件已被 v2.3R 取代（Lemma 2 数学错误已修正、贡献压回 4 个、A6 降级）。当前 v2.3R 主文档以 evidence table 为边界：A4 仅保留 L>=32 高负载早停主张，A5 降级为 appendix/high-stress，DeepMIMO Set E 仍为外部数据阻塞。

## 目录结构

```text
01_design_and_plan/        技术设计文档与路线版本
02_literature_and_refs/    文献跟踪与外部参考记录
03_active_modules/         当前规划模块：baseline、tompnet、train
04_experiments/            可复现 MATLAB 实验与审计脚本
05_results/                可再生成的实验结果、图表与 manifest
06_paper_and_delivery/     论文素材、整理笔记与 paper2 独立交付包
07_ops/                    运维辅助脚本，例如 GitHub 发布脚本
90_archive/                历史实验、旧工程与私有毕设材料
```

私有毕设资料已归档到：

```text
90_archive/2025_thesis_materials/
```

该目录已在 Git 中忽略，因为其中包含个人材料、大文件参考包和不适合公开上传的文档。

## 复现实验

在 MATLAB 中一键运行当前 v2.2 的六组轻量补充实验/审计：

```matlab
run('04_experiments/eval/run_all_v2_2_supplemental_experiments.m')
```

也可以单独运行某个实验：

```matlab
run('04_experiments/eval/run_oversampling_offgrid_ablation.m')
run('04_experiments/eval/run_kruskal_identifiability_ablation.m')
run('04_experiments/eval/run_offgrid_mismatch_lemma_validation.m')
run('04_experiments/eval/run_cdl_profile_generalization_smoke.m')
run('04_experiments/eval/run_crlb_delay_asymptotic_smoke.m')
run('04_experiments/eval/run_deepmimo_set_e_access_audit.m')
```

在 PowerShell 中调用本机 MATLAB：

```powershell
& 'D:\E\MATLAB\bin\matlab.exe' -batch "run('D:\E\OFDM-MIMO_Radar_Estimation\04_experiments\eval\run_all_v2_2_supplemental_experiments.m')"
```

实验输出目录：

```text
05_results/
```

当前汇总证据索引：

```text
05_results/v2_2_supplemental_manifest.md
```

## v2.3R Python 复现实验

当前 paper-facing 证据表可由以下脚本重新生成：

```text
python 04_experiments/eval/aggregate_v2_3r_paper_evidence_table.py
```

关键 v2.3R 结果目录：

```text
05_results/stage2_torch_locked_scale_g2_seed_sweep/
05_results/stage3_a4_cross_l_plateau_gate_seed_sweep/
05_results/stage3_a4_snr_plateau_gate_seed_sweep/
05_results/stage3_paper_scale_kruskal_proxy/
05_results/stage3_synthetic_cross_scene_generalization/
05_results/stage3_crlb_asymptotic_tightness/
05_results/stage3_a5_combined_impairment_presmoke/
05_results/deepmimo_set_e_access_audit/
05_results/v2_3r_paper_evidence_table/
```

## 论文交付材料

论文层面的活跃笔记目前保留在：

```text
06_paper_and_delivery/paper_notes/usable_content_inventory.md
```

新的 paper-facing 主入口为：

```text
01_design_and_plan/ISAC_DeepUnfolding_TechnicalDesign_v2.3R.md
05_results/v2_3r_paper_evidence_table/paper_evidence_table.md
02_literature_and_refs/v2_3r_literature_sprint_2026_06_25.md
02_literature_and_refs/v2_3r_references.bib
06_paper_and_delivery/manuscript_v2_3r/main.md
06_paper_and_delivery/manuscript_v2_3r/displays/figures/v2_3r_evidence_summary.pdf
06_paper_and_delivery/manuscript_v2_3r/paper_experiment_matrix.md
06_paper_and_delivery/manuscript_v2_3r/claim_evidence_ledger.json
```

历史的 `paper2_package` 旧版扁平包已与根目录全量重复（含已废弃路径），于 2026-06 清理删除；其唯一未重复的本科原型与历史图片仍保存在 `90_archive/old_experiment/`。

## 归档约束（重要）

`90_archive/` 是本科毕业设计阶段产物的只读归档，**不进入 v2.2 论文的实际产出**：

```text
90_archive/2025_thesis_materials/   私有毕设原稿、答辩 PPT、合同、文献 PDF、外部参考压缩包
90_archive/old_experiment/          本科 MATLAB 原型（接口未闭合，仅作素材）
90_archive/design_history/          v1.0 / v2.0 / v2.1 技术设计旧版
```

v2.2 论文产出全部在 `01_-07_` 编号目录内组织。

## 上传策略

建议纳入 Git 历史的内容：

- 技术设计 Markdown。
- MATLAB 源码与可复现实验脚本。
- 轻量实验结果、图表、CSV 和 summary。
- 论文素材清单与项目说明文档。

默认不上传的内容：

- 私有毕设材料、合同、评分表、Word/PDF 原稿。
- 外部参考压缩包、下载数据集和大型中间文件。
- `.mat` 模型、数据或可再生成的运行中间件。

## 发布到 GitHub

先完成 GitHub CLI 登录：

```powershell
gh auth login
```

然后运行发布脚本：

```powershell
.\07_ops\scripts\publish_to_github.ps1
```

当 `origin` 不存在时，脚本会创建私有仓库 `mmwave-isac-tompnet` 并推送当前分支。可按需使用 `-RepoName` 指定仓库名，或用 `-Visibility public` 改为公开仓库。
