# 淘宝深夜浏览分析（Taobao Night Browsing）

天池 649（淘宝 UserBehavior）公开镜像：**深夜浏览到底是「冲动消费」还是「闲逛」？**

核心结论：数据不支持「深夜更容易冲动下单」，支持「深夜浏览更像闲逛」——深夜（22–01）与凌晨（02–05）浏览的即时与 24 小时购买率都显著低于白天（09–17）。

## 项目结构

- `extension_night_browsing/` —— 完整分析项目（主分析 + 阶段二两个子分析 + 品类扩展）
  - `notebooks/full_pipeline.ipynb` —— **单文件整合**：数据清理 → 建模/实验 → 图片可视化
  - `notebooks/night_browsing_analysis.ipynb` —— 课程 Notebook（英文，读取已保存结果）
  - `slides/night_browsing_midterm_zh.pptx` —— 中期汇报 PPT（18 页）
  - `web/analysis_zh.html` —— 单文件网页版报告
  - `results/` —— 全部结果 CSV/JSON；`figures/` —— 图 01–11
  - `FINDINGS_zh.md` / `FINDINGS_PHASE2_zh.md` —— 中文发现；`ANALYSIS_PLAN*.md` + `POST_PLAN_DEVIATIONS.md` —— 预设计划与偏离记录
- `data/source_manifest.json` —— 数据来源与校验（原始 CSV 的下载地址、sha256 等）
- `results/data_audit.json` —— 原始数据的审计（行数、时间窗、行为类型、重复等）
- `src/common.py` + `vendor/pyhdfe/` —— 固定效应吸收的共享依赖

## 方法

固定效应线性概率模型（FE-LPM，用户/商品/日期三层 FE，双向聚类 SE）、生存分析（自实现 FastCox，Breslow 结点 + Lin-Wei 聚类 SE）、Causal Forest（CausalForestDML），以及按小时 × 三窗口生存、冷门/热门商品、分品类等扩展。

## Data（重要）

本仓库**不包含数据文件**（`.parquet` 已在 `.gitignore`）。原始数据是公开数据集，约 3.67 GB CSV：

- 下载地址与校验：`data/source_manifest.json`
- 原始数据审计：`results/data_audit.json`

重跑需要以下 parquet 数据文件（由原始 CSV 派生）：

| 文件 | 说明 |
|---|---|
| `data/processed/events_clean.parquet` | 清洗后事件表（1 亿行，时间窗过滤 + 去重） |
| `data/processed/user_buckets.parquet` | 用户 md5 分桶（训练/验证/测试划分） |
| `extension_night_browsing/data/episodes_hour.parquet` | 首次浏览 episode 表（由 `01_build.py` 生成） |
| `extension_night_browsing/data/episodes_features.parquet` | 带处理前特征的 episode 表（由 `05_features.py` 生成） |

## 环境与运行

- Python 3.13.9（anaconda）；运行前 `OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2`
- 依赖：numpy / pandas / scipy / statsmodels / matplotlib + vendored `pyhdfe` / `lightgbm` / `econml` / `lifelines`（`vendor/`）
- 完整管线见 `extension_night_browsing/README.md`；整合版 `extension_night_browsing/notebooks/full_pipeline.ipynb` 从头到尾可读，重活用 `TAG='smoke'`（自检）/ `'full'`（全量）切换
