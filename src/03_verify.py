"""Independent checks: (1) rebuild episodes for 400 random users with plain row-wise pandas, (2) local-hour anchor,
(3) FE estimator vs explicit-dummy OLS on a small subsample."""
from pathlib import Path
import json, sys
import numpy as np, pandas as pd
from datetime import datetime, timezone, timedelta

EXT = Path(__file__).resolve().parents[1]
BASE = EXT
sys.path.insert(0, str(EXT / 'src'))
sys.path.insert(0, str(BASE / 'src'))
RES = EXT / 'results'
START, END, DAY = 1511539200, 1512316800, 86400
SH = timezone(timedelta(hours=8))


def rebuild(ev_u):
    rows = []
    for (uid, iid), g in ev_u.groupby(['user_id', 'item_id']):
        pv = g[g.behavior == 1]
        if pv.empty:
            continue
        t0 = int(pv.ts.min())
        if t0 < START + DAY or t0 + DAY > END:
            continue
        if (g[(g.behavior != 1)].ts < t0).any():
            continue
        buys = g[(g.behavior == 4) & (g.ts >= t0)].ts
        lt = datetime.fromtimestamp(t0, SH)
        uall = ev_u[ev_u.user_id == uid]
        rows.append({'user_id': uid, 'item_id': iid, 't0': t0, 'buy_delay_s': int(buys.min() - t0) if len(buys) else -1,
                     'hour': lt.hour, 'day': (lt.date() - datetime(2017, 11, 25).date()).days,
                     'hist_pv24': int(((uall.behavior == 1) & (uall.ts >= t0 - DAY) & (uall.ts < t0)).sum()),
                     'hist_pv1h': int(((uall.behavior == 1) & (uall.ts >= t0 - 3600) & (uall.ts < t0)).sum()),
                     'hist_buy24': int(((uall.behavior == 4) & (uall.ts >= t0 - DAY) & (uall.ts < t0)).any())})
    return pd.DataFrame(rows)


def main():
    out = {}
    assert datetime.fromtimestamp(START, SH).isoformat() == '2017-11-25T00:00:00+08:00'
    out['start_anchor'] = datetime.fromtimestamp(START, SH).isoformat()
    ep = pd.read_parquet(EXT / 'data/episodes_hour.parquet')
    rng = np.random.default_rng(5312)
    users = rng.choice(ep.user_id.unique(), 400, replace=False)
    ev = pd.read_parquet(BASE / 'data/processed/events_clean.parquet', columns=['user_id', 'item_id', 'behavior', 'ts'],
                         filters=[('user_id', 'in', users.tolist())])
    ref = rebuild(ev)
    pipe = ep[ep.user_id.isin(users)]
    cols = ['buy_delay_s', 'hour', 'day', 'hist_pv24', 'hist_pv1h', 'hist_buy24']
    mg = pipe.merge(ref, on=['user_id', 'item_id'], how='outer', suffixes=('_p', '_r'), indicator=True)
    out['rebuild'] = {'users': 400, 'pipeline_episodes': len(pipe), 'reference_episodes': len(ref),
                      'only_one_side': int((mg._merge != 'both').sum()),
                      'field_mismatches': {c: int((mg[f'{c}_p'] != mg[f'{c}_r']).sum()) for c in cols + ['t0']},
                      'buys_within_24h': int(((ref.buy_delay_s >= 0) & (ref.buy_delay_s < DAY)).sum())}
    # pop24 independent recount for 300 random episodes
    smp = pipe.sample(300, random_state=1)
    ev_i = pd.read_parquet(BASE / 'data/processed/events_clean.parquet', columns=['item_id', 'behavior', 'ts'],
                           filters=[('item_id', 'in', smp.item_id.unique().tolist()), ('behavior', '==', 1)])
    pop = [int(((ev_i.item_id == r.item_id) & (ev_i.ts >= r.t0 - DAY) & (ev_i.ts < r.t0)).sum()) for r in smp.itertuples()]
    out['pop24_mismatches_of_300'] = int((np.array(pop) != smp.pop24.to_numpy()).sum())

    # FE estimator vs explicit dummies (user + day FE, small subsample, single cluster set)
    import importlib
    m = importlib.import_module('02_models')
    import statsmodels.api as sm
    d = m.derive(ep[ep.bucket == 40].copy())
    d = d[d.user_id.isin(d.user_id.drop_duplicates().sample(1500, random_state=2))].copy()
    r = m.fit_multi(d, m.DUM + m.CTRL, ['user_id', 'day'], ['y1'], 'check', clusters=(('user_id',),))
    dd = d.loc[d.groupby('user_id').y1.transform('size') > 1]
    X = pd.concat([dd[m.DUM + m.CTRL], pd.get_dummies(dd.user_id, prefix='u', dtype=float),
                   pd.get_dummies(dd.day, prefix='d', drop_first=True, dtype=float)], axis=1)
    ols = sm.OLS(dd.y1.to_numpy(), X.to_numpy()).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(dd.user_id)[0]})
    b = pd.Series(ols.params[:len(m.DUM + m.CTRL)], index=m.DUM + m.CTRL)
    s = pd.Series(ols.bse[:len(m.DUM + m.CTRL)], index=m.DUM + m.CTRL)
    rr = r.set_index('term')
    out['fe_vs_dummies'] = {'n': len(dd), 'max_abs_coef_diff': float((rr.coef - b).abs().max()),
                            'se_ratio_min': float((rr.se / s).min()), 'se_ratio_max': float((rr.se / s).max())}
    (RES / 'verification.json').write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    main()
