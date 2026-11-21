"""Survival analysis of time from first view to purchase (ANALYSIS_PLAN_ADVANCED.md v2).

Event: first focal buy in [t0, t0+24h); buys at >= 24h are censored at 24h. Time in hours.
Cox: FastCox (Breslow ties, user-clustered Lin-Wei SE; verified against statsmodels/lifelines in 06_verify_fastcox.py).
Piecewise: [0,1h) censored at 1h, and [1h,24h) among episodes still at risk at 1h.
AFT Weibull: lifelines. C-index: lifelines on 500k random test episodes (seed 5312).
Fit on train buckets, evaluate on test buckets. Val is not used here.
"""
import argparse, json, time
import numpy as np, pandas as pd
from adv_common import RES, BINS, log, load, parse_range
from fastcox import FastCox
from lifelines import WeibullAFTFitter
from lifelines.utils import concordance_index

DUM = ['evening', 'late', 'small', 'morning']
CTRL = ['l_hpv24', 'hist_buy24', 'l_pop24']
DAYD = [f'd{k}' for k in range(2, 8)]  # ref day 1; day 8 (156 episodes at Dec 3 00:00) merged into day 7
CHECKPOINTS_H = [1 / 6, 1, 3, 6, 12, 24]


def prep(d):
    dl = d.buy_delay_s.to_numpy()
    ev = (dl >= 0) & (dl < 86400)
    d['event'] = ev.astype(np.int8)
    d['dur_h'] = np.where(ev, dl / 3600.0, 24.0)
    for c in DUM:
        d[c] = (d.bin == c).astype(np.float64)
    dd = np.minimum(d.day.to_numpy(), 7)
    for k in range(2, 8):
        d[f'd{k}'] = (dd == k).astype(np.float64)
    return d


def cox(d, cols, dur, event, strata=None, name=''):
    t = time.time()
    f = FastCox(d[dur].to_numpy(), d[event].to_numpy(), d[cols].to_numpy(np.float64),
                None if strata is None else d[strata].to_numpy()).fit()
    f.robust_cov(d.user_id.to_numpy())
    r = f.summary(cols)
    r['model'] = name; r['n'] = len(d); r['events'] = int(d[event].sum()); r['clusters'] = f.n_clusters
    r['n_iter'] = f.n_iter; r['loglik'] = f.loglik
    log(name, 'n', len(d), 'events', int(d[event].sum()), 'iter', f.n_iter, f'{time.time() - t:.0f}s',
        'late HR', round(float(r.loc[r.term == 'late', 'hr'].iloc[0]), 4))
    return r, f


def cindex(beta, d, cols, n=500_000):
    s = d.sample(min(n, len(d)), random_state=5312)
    return float(concordance_index(s.dur_h, -(s[cols].to_numpy(np.float64) @ beta), s.event))


def describe(d):
    out = []
    dl = d.buy_delay_s.to_numpy()
    for b in BINS:
        m = (d.bin == b).to_numpy()
        row = {'bin': b, 'episodes': int(m.sum()), 'users': int(d.user_id[m].nunique())}
        for h in CHECKPOINTS_H:
            row[f'cum_buy_pct_{h:g}h'] = float(((dl[m] >= 0) & (dl[m] < h * 3600)).mean() * 100)
        buyers = dl[m][(dl[m] >= 0) & (dl[m] < 86400)]
        row['buyers_24h'] = int(len(buyers))
        row['median_delay_min_buyers24h'] = float(np.median(buyers) / 60)
        row['share_of_24h_buys_within_1h_pct'] = float((buyers < 3600).mean() * 100)
        out.append(row)
    return pd.DataFrame(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--train', default='0-59'); ap.add_argument('--test', default='80-99')
    ap.add_argument('--tag', default='full'); ap.add_argument('--aft_user_frac', type=float, default=1.0)
    a = ap.parse_args()
    out_dir = RES if a.tag == 'full' else RES / 'smoke'; out_dir.mkdir(exist_ok=True)
    info = {'args': vars(a), 'timing_s': {}}
    t0 = time.time()
    tr = prep(load([parse_range(a.train)]))
    tr['user_decile'] = pd.qcut(tr.groupby('user_id').user_id.transform('size').rank(method='first'), 10, labels=False)
    tr['item_decile'] = pd.qcut(tr.groupby('item_id').item_id.transform('size').rank(method='first'), 10, labels=False)
    tr['stratum'] = tr.user_decile * 1000 + tr.item_decile * 10 + np.minimum(tr.day, 7)
    log('train', len(tr), 'events', int(tr.event.sum()), 'strata', tr.stratum.nunique())
    M1, M2 = DUM, DUM + CTRL + DAYD
    M3 = DUM + CTRL  # day is part of the stratum, so day dummies are not identified within strata
    rows, betas = [], {}
    for name, cols, strata in [('M1_bins', M1, None), ('M2_controls', M2, None), ('M3_stratified', M3, 'stratum')]:
        r, f = cox(tr, cols, 'dur_h', 'event', strata, name); rows.append(r); betas[name] = (f.beta, cols)
    p1 = tr[['user_id', 'dur_h', 'event'] + M2].copy()
    p1['ev_0_1h'] = ((p1.event == 1) & (p1.dur_h < 1)).astype(np.int8); p1['dur_0_1h'] = np.minimum(p1.dur_h, 1.0)
    r, _ = cox(p1, M2, 'dur_0_1h', 'ev_0_1h', None, 'PW_0_1h'); rows.append(r)
    p2 = p1[p1.dur_h >= 1].copy(); p2['dur_1h_24h'] = p2.dur_h - 1.0
    r, _ = cox(p2, M2, 'dur_1h_24h', 'event', None, 'PW_1h_24h'); rows.append(r)
    del p1, p2
    info['timing_s']['cox'] = time.time() - t0
    t1 = time.time()
    aft_d = tr
    if a.aft_user_frac < 1.0:
        us = tr.user_id.drop_duplicates().sample(frac=a.aft_user_frac, random_state=5312)
        aft_d = tr[tr.user_id.isin(us)]
    aft = WeibullAFTFitter()
    aft.fit(aft_d[['dur_h', 'event'] + M2], duration_col='dur_h', event_col='event')
    s = aft.summary.reset_index()
    s = s[s.param == 'lambda_'][['covariate', 'coef', 'se(coef)', 'p']].rename(columns={'covariate': 'term', 'se(coef)': 'se'})
    s['time_ratio'] = np.exp(s.coef); s['model'] = 'AFT_weibull_naive_se'; s['n'] = len(aft_d); s['events'] = int(aft_d.event.sum())
    rows.append(s); info['aft_rho'] = float(np.exp(aft.params_.loc[('rho_', 'Intercept')]))
    info['timing_s']['aft'] = time.time() - t1; log('aft', round(info['timing_s']['aft']), 's')
    del tr, aft_d
    te = prep(load([parse_range(a.test)]))
    describe(te).to_csv(out_dir / f'survival_cumulative_by_bin_{a.tag}.csv', index=False)
    info['c_index_test'] = {k: cindex(b, te, c) for k, (b, c) in betas.items() if k != 'M3_stratified'}
    info['n_test'] = len(te); info['test_events'] = int(te.event.sum())
    pd.concat(rows).to_csv(out_dir / f'survival_models_{a.tag}.csv', index=False)
    info['timing_s']['total'] = time.time() - t0
    (out_dir / f'survival_{a.tag}.json').write_text(json.dumps(info, indent=2))
    log('done', round(info['timing_s']['total']), 's', info['c_index_test'])


if __name__ == '__main__':
    main()
