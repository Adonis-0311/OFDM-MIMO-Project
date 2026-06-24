# paper2 汇总说明

本目录汇总了本次项目整理/生成的可交付内容，来源为当前 Git 跟踪文件。

已包含：

- `README.md` 与 `.gitignore`
- `ISAC_DeepUnfolding_TechnicalDesign*.md` 技术大纲
- `Config/`、`Modules/` 与现有 MATLAB 原型代码
- `eval/` 五组 v2.2 轻量实验脚本与一键复现实验入口
- `Results/` 五组实验结果、图表、CSV、summary 与总 manifest
- `paper/usable_content_inventory.md` 可用内容与实验缺口梳理
- `scripts/publish_to_github.ps1` GitHub 发布辅助脚本
- `baseline/`、`tompnet/`、`train/`、`literature_2024_2025/` 规划目录
- 当前仓库中已纳入版本控制的论文/结果图片与 MATLAB 脚本

未包含：

- `.git/` 仓库内部数据
- `2025刘雨辉毕设/` 个人材料与大文件参考资料
- `*.mat` 可复现实验中间件
- `Data/`、`Libraries/` 等未纳入本次整理交付范围的历史目录

一键复现实验入口：

```matlab
run('eval/run_all_v2_2_supplemental_experiments.m')
```

总实验索引：

```text
Results/v2_2_supplemental_manifest.md
```
