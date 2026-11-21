# Taobao: night browsing — idle browsing or impulse buying? (IS5312 lead project)

Read [FINDINGS_zh.md](FINDINGS_zh.md) first (Chinese).

**TL;DR**: First views at 22–01 and 02–05 convert less than daytime views (09–17), both within 1 h and within 24 h.

- **Fixed-effects LPM:** late vs day −0.18 pp on 1 h purchase and −0.31 pp on 24 h purchase.
- **Cox, 30.8 M train episodes:** late-night HR 0.71.
  - Late night: the hazard stays lower after the first hour (HR 0.63 for 1–24 h), so it is fewer purchases, not just later ones.
  - Small hours: only the first hour is lower (1–24 h HR 0.98, CI includes 1), so purchases are mainly delayed.
- **Causal Forest (test ATE −0.18 pp):**
  - Real heterogeneity: BLP β 1.26, GATES Q5−Q1 +0.39 pp.
  - It is mostly scale. The absolute gap is largest for long-tail items and users who already bought, while the relative gap is −17% to −26% in every quintile.

## Pipeline

All scripts are in `src/`. Run them from inside `src/`. Use Python 3.13.9. Install dependencies with `pip install -r requirements.txt` (the fixed-effects and ML libraries were previously vendored and are now pinned in this file).

| Step | Script | Output | Time / peak RAM |
|---|---|---|---|
| 1 | `01_build.py` | `data/episodes_hour.parquet` (51.3 M first-view episodes) | 6.5 min |
| 2 | `02_models.py` | FE models, 4 Holm tests, 7 robustness specs, hour shape | 27 min |
| 3 | `03_verify.py` | 400-user independent rebuild, FE vs dummies | 2 min |
| 4 | `04_figures.py` | figures 01–03 | <1 min |
| 5 | `05_features.py` | `data/episodes_features.parquet` (adds pre-t0 user/item counts) | 2 min |
| 6 | `05_verify_features.py` | 300-episode feature recount, split overlap check | 1 min |
| 7 | `06_verify_fastcox.py` | FastCox vs statsmodels / lifelines | 1 min |
| 8 | `06_survival.py --tag full` | Cox M1–M3, piecewise Cox, Weibull AFT, cumulative curves | 12 min / 17 GB |
| 9 | `05_causal_forest.py --tag full` | CausalForestDML, test ATE / BLP / GATES / CLAN | 51 min / 22 GB |
| 10 | `07_figures_advanced.py` | figures 04–06 | <1 min |
| 11 | `08_build_notebook.py` | `notebooks/night_browsing_analysis.ipynb` (unexecuted) | <1 min |
| 12 | `09_execute_notebook.py` | executes the notebook in a fresh kernel, exports `.html`, writes `notebooks/execution_audit.json` | ~3 min / ~10 GB |
| 13 | `10_survival_hourly.py --tag full` | PHASE2 A: survival with one group per hour × three purchase windows (1h/3h/24h) (`results/survival_hourly_*.csv/json`) | ~8 min |
| 14 | `11_cold_hot_items.py` | PHASE2 B: cold vs hot item night loss (`results/cold_hot_items_*.csv`) | ~3 min |
| 15 | `12_figures_phase2.py` | figures 07–08 | <1 min |
| 16 | `13_build_slides_zh.py` | `slides/night_browsing_midterm_zh.pptx` (18 slides, Chinese, CityU-style) | <1 min |
| 17 | `14_build_web.py` | `web/analysis_zh.html` (single-file report, images embedded) | <1 min |
| 18 | `17_category_survival.py --tag full` | PHASE2 A-by-category: Cox per top-20 category + other (`results/category_survival_*.csv`) | ~8 min |
| 19 | `18_figure_category.py` | figure 11 | <1 min |
| 20 | `19_cf_category.py --tag full` | Causal Forest with category dummies (`results/causal_forest_category_full.json`) | ~60 min / 22 GB |

Steps 13–15 are PHASE2 sub-analyses; steps 16–17 build the deliverable deck and web report; steps 18–19 add the category-stratified survival analysis (plan: `ANALYSIS_PLAN_PHASE2.md`, findings: `FINDINGS_PHASE2_zh.md`). The course notebook (step 12) predates them and was not updated to include them.

The course notebook reads saved results and does not refit the survival models or the Causal Forest. It re-computes live, and asserts equal to the saved files, three things: the full descriptives, the primary M2 FE model, and the test-set cumulative purchase curves.

Set `OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2` before running.

Notes on steps 8 and 9:

- `--tag smoke` with small bucket ranges writes to `results/smoke/` instead.
- The Causal Forest default `--max_samples 0.05` is required on this machine. The econml default of 0.45 pre-allocates about 70 GB of subsample indices (see `POST_PLAN_DEVIATIONS.md`).

## Splits

Users are split by md5 bucket. A user appears in exactly one split, verified with 0 overlap.

- **Train, buckets 0–59:** 30.8 M episodes, 590 k users.
- **Validation, buckets 60–79:** 10.3 M episodes. Used only for LightGBM early stopping and dev checks.
- **Test, buckets 80–99:** 10.3 M episodes, 197 k users. All reported Causal Forest and C-index results come from this split.

The fixed-effects analysis predates this split. It used buckets 40–59 as its main sample and 60–79 for replication.

## Data

The large parquet data files are **not tracked** in this repository (see `.gitignore`). They derive from the public Tianchi 649 / Kaggle mirror dataset (download URL + sha256 in `data/source_manifest.json`; raw-data audit in `results/data_audit.json`).

| File | Produced by |
|---|---|
| `data/processed/events_clean.parquet` | cleaned 100 M events (time-window filter + dedup) |
| `data/processed/user_buckets.parquet` | user md5 buckets (train/val/test split) |
| `data/episodes_hour.parquet` | `01_build.py` |
| `data/episodes_features.parquet` | `05_features.py` |

## Notebooks

- `notebooks/full_pipeline.ipynb` — the consolidated single-file pipeline (data cleaning → models → figures), English.
- `notebooks/night_browsing_analysis.ipynb` — the course notebook (reads saved results; does not refit the survival models or the Causal Forest).

## Plans and disclosure

- `ANALYSIS_PLAN.md` was saved before the FE results. `ANALYSIS_PLAN_ADVANCED.md` v2 was saved before the Causal Forest and survival results. Neither is externally registered.
- `POST_PLAN_DEVIATIONS.md` records every deviation:
  - the Cox implementation swap;
  - a column-name bug fixed after the smoke run;
  - the memory-driven `max_samples` change;
  - the smoke run touching test bucket 80;
  - two corrected statements in an earlier version of the findings.
