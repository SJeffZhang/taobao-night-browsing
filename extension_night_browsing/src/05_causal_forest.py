"""Causal Forest (CausalForestDML) for heterogeneity of the late-night vs daytime gap (ANALYSIS_PLAN_ADVANCED.md v2).

Sample: first views at 22-01 (T=1) or 09-17 (T=0). Outcome y1 x 100 (pp). Features: pre-t0 only.
Split by user md5 bucket: train / val / test. Nuisance = LightGBM with early stopping on val.
Test-set evaluation: out-of-sample DML ATE, BLP calibration, GATES quintiles, CLAN, all user-clustered.
"""
import argparse, json, time
import numpy as np, pandas as pd
from adv_common import RES, LATE, DAYH, CF_FEATURES, log, load, parse_range, cluster_ols
import lightgbm as lgb
from econml.dml import CausalForestDML

LGB = dict(learning_rate=0.05, num_leaves=63, min_child_samples=500, subsample=0.8, subsample_freq=1,
           colsample_bytree=0.9, n_jobs=8, verbose=-1, random_state=5312)


def early_stop_rounds(Xtr, ytr, Xva, yva, classifier, cap):
    M = lgb.LGBMClassifier if classifier else lgb.LGBMRegressor
    m = M(n_estimators=cap, **LGB)
    m.fit(Xtr, ytr, eval_set=[(Xva, yva)], callbacks=[lgb.early_stopping(50, verbose=False)])
    return int(m.best_iteration_ or cap)


def residual_reg(yt, tt, groups, extra=None):
    X = tt[:, None] if extra is None else np.column_stack([tt] + extra)
    b, cov, G = cluster_ols(yt, X, groups)
    se = np.sqrt(np.diag(cov))
    return b, se, cov, G


def evaluate(cf, d, Xcols, tag):
    """Out-of-sample residuals using the train-fitted nuisance models (fold-averaged)."""
    X = d[Xcols].to_numpy(np.float64)
    y = d.y1.to_numpy() * 100; t = d.treat.to_numpy().astype(np.float64)
    my = np.mean([m.predict(X) for m in cf.models_y[0]], axis=0)
    mt = np.mean([m.predict_proba(X)[:, 1] for m in cf.models_t[0]], axis=0)
    yt, tt = y - my, t - mt
    g = d.user_id.to_numpy()
    tau = cf.effect(X).ravel()
    out = {'sample': tag, 'n': len(d), 'users': int(d.user_id.nunique()), 'treated_share': float(t.mean()),
           'y1_mean_pp': float(y.mean()), 'propensity_range': [float(mt.min()), float(mt.max())]}
    b, se, _, G = residual_reg(yt, tt, g)
    out['dml_ate'] = {'coef': float(b[0]), 'se': float(se[0]), 'ci': [float(b[0] - 1.96 * se[0]), float(b[0] + 1.96 * se[0])],
                      'clusters': G}
    out['cate_pred'] = {'mean': float(tau.mean()), 'sd': float(tau.std()),
                        'pct': {str(p): float(np.percentile(tau, p)) for p in [1, 5, 10, 25, 50, 75, 90, 95, 99]},
                        'share_negative': float((tau < 0).mean())}
    b, se, _, _ = residual_reg(yt, tt, g, [tt * (tau - tau.mean())])
    out['blp'] = {'alpha': float(b[0]), 'alpha_se': float(se[0]), 'beta': float(b[1]), 'beta_se': float(se[1]),
                  'beta_ci': [float(b[1] - 1.96 * se[1]), float(b[1] + 1.96 * se[1])]}
    q = pd.qcut(tau, 5, labels=False, duplicates='drop')
    D = np.column_stack([(q == k) * tt for k in range(5)])
    b, se, cov, _ = residual_reg(yt, D[:, 0], g, [D[:, k] for k in range(1, 5)])
    gates = []
    for k in range(5):
        m = q == k
        row = {'quintile': k + 1, 'n': int(m.sum()), 'coef': float(b[k]), 'se': float(se[k]),
               'ci': [float(b[k] - 1.96 * se[k]), float(b[k] + 1.96 * se[k])], 'tau_hat_mean': float(tau[m].mean()),
               'raw_y1_late_pp': float(y[m & (t == 1)].mean()), 'raw_y1_day_pp': float(y[m & (t == 0)].mean())}
        for c in Xcols:
            row[f'mean_{c}'] = float(d[c].to_numpy()[m].mean())
        gates.append(row)
    dlt = b[4] - b[0]; dse = float(np.sqrt(cov[4, 4] + cov[0, 0] - 2 * cov[0, 4]))
    out['gates'] = gates
    out['gates_q5_minus_q1'] = {'diff': float(dlt), 'se': dse, 'ci': [float(dlt - 1.96 * dse), float(dlt + 1.96 * dse)]}
    return out, tau


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--train', default='0-59'); ap.add_argument('--val', default='60-79'); ap.add_argument('--test', default='80-99')
    ap.add_argument('--n_trees', type=int, default=1000); ap.add_argument('--cap', type=int, default=2000)
    ap.add_argument('--tag', default='full'); ap.add_argument('--skip_test', action='store_true')
    # econml pre-allocates every tree's subsample indices before fitting: 0.45 of 19.5M rows x 1000 trees ~ 70 GB
    ap.add_argument('--max_samples', type=float, default=0.05)
    a = ap.parse_args()
    tr, va, te = parse_range(a.train), parse_range(a.val), parse_range(a.test)
    out_dir = RES if a.tag == 'full' else RES / 'smoke'; out_dir.mkdir(exist_ok=True)
    info = {'args': vars(a), 'features': CF_FEATURES, 'lgb': LGB, 'timing_s': {}}
    hours = LATE + DAYH
    t0 = time.time()
    d_tr = load([tr], hours); d_va = load([va], hours)
    for d in (d_tr, d_va):
        d['treat'] = d.hour.isin(LATE).astype(np.int64)
    log('train', len(d_tr), 'val', len(d_va))
    Xtr = d_tr[CF_FEATURES].to_numpy(np.float64); Xva = d_va[CF_FEATURES].to_numpy(np.float64)
    ny = early_stop_rounds(Xtr, d_tr.y1.to_numpy() * 100, Xva, d_va.y1.to_numpy() * 100, False, a.cap)
    nt = early_stop_rounds(Xtr, d_tr.treat.to_numpy(), Xva, d_va.treat.to_numpy(), True, a.cap)
    info['nuisance_rounds'] = {'y': ny, 't': nt}; info['timing_s']['early_stop'] = time.time() - t0
    log('rounds y', ny, 't', nt)
    cf = CausalForestDML(model_y=lgb.LGBMRegressor(n_estimators=ny, **LGB),
                         model_t=lgb.LGBMClassifier(n_estimators=nt, **LGB),
                         discrete_treatment=True, cv=2, n_estimators=a.n_trees, min_samples_leaf=500,
                         max_samples=a.max_samples, honest=True, inference=True, n_jobs=-1, random_state=5312)
    t1 = time.time()
    cf.fit(d_tr.y1.to_numpy() * 100, d_tr.treat.to_numpy(), X=Xtr, groups=d_tr.user_id.to_numpy())
    info['timing_s']['cf_fit'] = time.time() - t1; log('cf fit', round(info['timing_s']['cf_fit']), 's')
    info['n_train'] = len(d_tr); info['train_users'] = int(d_tr.user_id.nunique())
    info['feature_importances'] = dict(zip(CF_FEATURES, map(float, cf.feature_importances_)))
    del d_tr, Xtr
    ev, _ = evaluate(cf, d_va, CF_FEATURES, 'val'); info['val'] = ev
    log('val ate', ev['dml_ate'], 'blp beta', ev['blp']['beta'])
    del d_va, Xva
    if not a.skip_test:
        d_te = load([te], hours); d_te['treat'] = d_te.hour.isin(LATE).astype(np.int64)
        ev, tau = evaluate(cf, d_te, CF_FEATURES, 'test'); info['test'] = ev
        pd.DataFrame({'quantile': np.linspace(0, 1, 1001), 'cate_pp': np.quantile(tau, np.linspace(0, 1, 1001))}) \
            .to_csv(out_dir / f'cate_quantiles_{a.tag}.csv', index=False)
        log('test ate', ev['dml_ate'], 'blp beta', ev['blp']['beta'], 'q5-q1', ev['gates_q5_minus_q1'])
    info['timing_s']['total'] = time.time() - t0
    (out_dir / f'causal_forest_{a.tag}.json').write_text(json.dumps(info, indent=2))
    log('done', round(info['timing_s']['total']), 's')


if __name__ == '__main__':
    main()
