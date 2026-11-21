"""Causal Forest with category as a LOW-DIMENSIONAL feature.

Category is anonymised with 9,437 values; one-hotting all would blow up memory. So we
encode it as the top-15 categories (by train-episode count) as binary dummies, with the
remaining ~9,400 long-tail categories as the implicit reference. Everything else
(nuisance LightGBM, 1000 trees, max_samples=0.05, same split, same evaluation) mirrors
src/05_causal_forest.py exactly, so results are comparable.

Outputs:
  results/causal_forest_category_{tag}.json  (includes feature_importances)
  results/cate_quantiles_category_{tag}.csv
"""
import argparse, importlib, json, time
from pathlib import Path
import numpy as np, pandas as pd

EXT = Path(__file__).resolve().parents[1]
RAW = EXT / 'data/processed/events_clean.parquet'
RES = EXT / 'results'

import sys
sys.path.insert(0, str(EXT / 'src'))
from adv_common import LATE, DAYH, CF_FEATURES, log, load, parse_range  # noqa: E402

cfm = importlib.import_module('05_causal_forest')
early_stop_rounds, evaluate, LGB = cfm.early_stop_rounds, cfm.evaluate, cfm.LGB

import lightgbm as lgb  # noqa: E402
from econml.dml import CausalForestDML  # noqa: E402

TOP_K = 15


def item_category_map():
    ev = pd.read_parquet(RAW, columns=['item_id', 'category_id'])
    return ev.groupby('item_id')['category_id'].agg(lambda s: s.mode().iloc[0]).rename('category_id')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--train', default='0-59'); ap.add_argument('--val', default='60-79'); ap.add_argument('--test', default='80-99')
    ap.add_argument('--n_trees', type=int, default=1000); ap.add_argument('--cap', type=int, default=2000)
    ap.add_argument('--tag', default='full'); ap.add_argument('--skip_test', action='store_true')
    ap.add_argument('--max_samples', type=float, default=0.05)
    ap.add_argument('--topk', type=int, default=TOP_K)
    a = ap.parse_args()
    tr, va, te = parse_range(a.train), parse_range(a.val), parse_range(a.test)
    out_dir = RES if a.tag == 'full' else RES / 'smoke'; out_dir.mkdir(exist_ok=True)

    log('load + category map')
    catmap = item_category_map()
    hours = LATE + DAYH
    d_tr = load([tr], hours).join(catmap, on='item_id')
    d_va = load([va], hours).join(catmap, on='item_id')

    # top-K categories by train episode count -> dummies
    top = list(d_tr.groupby('category_id').size().sort_values(ascending=False).head(a.topk).index)
    cat_feats = [f'cat_{int(c)}' for c in top]
    for d in (d_tr, d_va):
        d['treat'] = d.hour.isin(LATE).astype(np.int64)
        for c, f in zip(top, cat_feats):
            d[f] = (d.category_id == c).astype(np.float64)
    FEATURES = CF_FEATURES + cat_feats
    log('features', len(FEATURES), '| top categories', top[:5], '...')

    info = {'args': vars(a), 'features': FEATURES, 'cat_features': cat_feats,
            'top_category_ids': [int(c) for c in top], 'lgb': LGB, 'timing_s': {}}
    t0 = time.time()
    Xtr = d_tr[FEATURES].to_numpy(np.float64); Xva = d_va[FEATURES].to_numpy(np.float64)
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
    imp = dict(zip(FEATURES, map(float, cf.feature_importances_)))
    info['feature_importances'] = imp
    info['category_importance_total'] = float(sum(imp[f] for f in cat_feats))
    info['top_category_shares'] = {int(c): round(float((d_tr.category_id == c).mean() * 100), 2) for c in top}
    del d_tr, Xtr

    ev, _ = evaluate(cf, d_va, FEATURES, 'val'); info['val'] = ev
    log('val ate', ev['dml_ate']['coef'], 'blp beta', round(ev['blp']['beta'], 3))
    del d_va, Xva

    if not a.skip_test:
        d_te = load([te], hours).join(catmap, on='item_id')
        d_te['treat'] = d_te.hour.isin(LATE).astype(np.int64)
        for c, f in zip(top, cat_feats):
            d_te[f] = (d_te.category_id == c).astype(np.float64)
        ev, tau = evaluate(cf, d_te, FEATURES, 'test'); info['test'] = ev
        pd.DataFrame({'quantile': np.linspace(0, 1, 1001), 'cate_pp': np.quantile(tau, np.linspace(0, 1, 1001))}) \
            .to_csv(out_dir / f'cate_quantiles_category_{a.tag}.csv', index=False)
        log('test ate', ev['dml_ate']['coef'], 'blp beta', round(ev['blp']['beta'], 3), 'q5-q1', round(ev['gates_q5_minus_q1']['diff'], 3))
    info['timing_s']['total'] = time.time() - t0
    (out_dir / f'causal_forest_category_{a.tag}.json').write_text(json.dumps(info, indent=2))
    log('done', round(info['timing_s']['total'], 1), 's')


if __name__ == '__main__':
    main()
