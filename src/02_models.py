"""Pre-specified models for the night-browsing extension (ANALYSIS_PLAN.md)."""
from pathlib import Path
import json, sys, time
import numpy as np, pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

EXT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXT / 'src'))
from common import pyhdfe, cluster_cov, log  # noqa: E402

DATA = EXT / 'data'; RES = EXT / 'results'
BINS = {'day': range(9, 18), 'evening': range(18, 22), 'late': [22, 23, 0, 1], 'small': range(2, 6), 'morning': range(6, 9)}
DUM = ['evening', 'late', 'small', 'morning']
CTRL = ['l_hpv24', 'hist_buy24', 'l_pop']
HOURS = [f'h{h:02d}' for h in range(24) if h != 14]
FE_MAIN = ['user_id', 'item_id', 'day']


def derive(ep):
    d = ep
    dl = d.buy_delay_s.to_numpy()
    bought = dl >= 0
    d['y1'] = np.where(bought & (dl < 3600), 100.0, 0.0)
    d['y2'] = np.where(bought & (dl < 86400), 100.0, 0.0)
    d['y10m'] = np.where(bought & (dl < 600), 100.0, 0.0)
    d['y3'] = np.where(bought & (dl >= 3600) & (dl < 86400), 100.0, 0.0)
    hb = pd.Series(index=range(24), dtype=object)
    for name, hs in BINS.items():
        hb[list(hs)] = name
    d['bin'] = hb.to_numpy()[d.hour.to_numpy()]
    for c in DUM:
        d[c] = (d.bin == c).astype(float)
    d['l_hpv24'] = np.log2(1 + d.hist_pv24); d['l_hpv1h'] = np.log2(1 + d.hist_pv1h)
    d['l_pop'] = np.log2(1 + d.pop24); d['hist_buy24'] = d.hist_buy24.astype(float)
    d['dayhour'] = d.day.astype(np.int32) * 24 + d.hour
    return d


def fit_multi(d, xcols, fes, ycols, name, clusters=(('user_id', 'item_id'),)):
    """One residualization, OLS for every outcome and every clustering."""
    t = time.time()
    cols = xcols + ycols
    if fes:
        ids = np.column_stack([pd.factorize(d[c], sort=False)[0] for c in fes])
        opts = {'tol': 1e-9, 'iteration_limit': 20000, 'transform': 'symmetric', 'acceleration': 'cg'} if len(fes) > 1 else None
        algo = pyhdfe.create(ids, drop_singletons=True, compute_degrees=True, degrees_method='pairwise' if len(fes) <= 2 else 'simple',
                             residualize_method='map' if len(fes) > 1 else 'within', options=opts)
        keep = ~algo.singleton_indices if algo.singleton_indices is not None else np.ones(len(d), bool)
        Z = algo.residualize(d[cols].to_numpy(float)); g = d.loc[keep]; deg = int(algo.degrees)
        X = Z[:, :len(xcols)]; Ys = Z[:, len(xcols):]; names = list(xcols)
    else:
        X = np.column_stack([np.ones(len(d)), d[xcols].to_numpy(float)]); Ys = d[ycols].to_numpy(float); g = d; deg = 0
        names = ['const'] + list(xcols)
    assert np.linalg.matrix_rank(X) == X.shape[1], name
    rows = []
    for j, yc in enumerate(ycols):
        y = Ys[:, j]
        beta = np.linalg.lstsq(X, y, rcond=None)[0]; e = y - X @ beta
        ref_mean = float(g.loc[g.bin == 'day', yc].mean()) if 'bin' in g else np.nan
        for cl in clusters:
            cov, counts, mineig = cluster_cov(X, e, [g[c].to_numpy() for c in cl], deg + X.shape[1])
            se = np.sqrt(np.diag(cov)); dfree = min(counts[:len(cl)]) - 1; tc = stats.t.ppf(.975, dfree)
            r = pd.DataFrame({'term': names, 'coef': beta, 'se': se, 'ci_low': beta - tc * se, 'ci_high': beta + tc * se,
                              'p': 2 * stats.t.sf(np.abs(beta / se), dfree)})
            r['outcome'] = yc; r['model'] = name; r['cluster'] = '+'.join(cl); r['n'] = len(g)
            r['n_dropped_singletons'] = len(d) - len(g); r['users'] = g.user_id.nunique(); r['items'] = g.item_id.nunique()
            r['y_mean'] = float(g[yc].mean()); r['day_ref_mean'] = ref_mean; r['fe'] = '+'.join(fes) if fes else 'none'
            r['clusters_1'] = counts[0]; r['clusters_2'] = counts[1] if len(counts) > 1 else np.nan; r['min_cov_eig'] = mineig
            rows.append(r)
    log(name, 'n', len(g), f'{time.time() - t:.0f}s')
    return pd.concat(rows)


def describe(full):
    out = []
    for g in ['hour', 'bin']:
        t = full.groupby(g).agg(episodes=('y1', 'size'), users=('user_id', 'nunique'), y1_pct=('y1', 'mean'), y2_pct=('y2', 'mean'),
                                y10m_pct=('y10m', 'mean')).reset_index().rename(columns={g: 'level'})
        nb = full[full.y1 == 0].groupby(g).y3.agg(['size', 'mean']).rename(columns={'size': 'not_bought_1h', 'mean': 'y3_pct_given_no_1h'})
        t = t.join(nb, on='level')
        t['share_of_episodes_pct'] = t.episodes / t.episodes.sum() * 100
        t['share_of_24h_buys_pct'] = (t.y2_pct * t.episodes) / (t.y2_pct * t.episodes).sum() * 100
        t['grouping'] = g; out.append(t)
    return pd.concat(out)


def main():
    log('load')
    full = derive(pd.read_parquet(DATA / 'episodes_hour.parquet'))
    describe(full).to_csv(RES / 'descriptives_full.csv', index=False)
    coefs = [fit_multi(full, DUM, [], ['y1', 'y2'], 'M0_full')]
    main_s = full[full.bucket.between(40, 59)].copy(); rep_s = full[full.bucket.between(60, 79)].copy()
    del full
    summ = {s: {'episodes': len(d), 'users': int(d.user_id.nunique())} for s, d in [('main', main_s), ('replication', rep_s)]}
    coefs.append(fit_multi(main_s, DUM, [], ['y1', 'y2'], 'M0_main'))
    coefs.append(fit_multi(main_s, DUM, ['user_id'], ['y1', 'y2'], 'M1_main'))
    m2 = fit_multi(main_s, DUM + CTRL, FE_MAIN, ['y1', 'y2', 'y10m'], 'M2_main',
                   clusters=(('user_id', 'item_id'), ('user_id', 'dayhour')))
    coefs.append(m2)
    coefs.append(fit_multi(rep_s, DUM + CTRL, FE_MAIN, ['y1', 'y2'], 'M2_replication'))
    coefs = pd.concat(coefs); coefs.to_csv(RES / 'model_coefficients.csv', index=False)

    base = m2[(m2.cluster == 'user_id+item_id')]
    prim = pd.concat([base[(base.term == t) & (base.outcome == y)] for t in ['late', 'small'] for y in ['y1', 'y2']])
    prim['p_holm'] = multipletests(prim.p, method='holm')[1]
    prim['coef_over_day_ref_pct'] = prim.coef / prim.day_ref_mean * 100
    prim.to_csv(RES / 'primary_tests.csv', index=False)

    rob = [base[base.outcome.isin(['y1', 'y2'])].assign(robustness='main'),
           base[base.outcome == 'y10m'].assign(robustness='S3_y1_10min'),
           m2[m2.cluster == 'user_id+dayhour'].assign(robustness='S4_cluster_user_dayhour')]
    rob.append(fit_multi(main_s, DUM, FE_MAIN, ['y1', 'y2'], 'S1_no_controls').assign(robustness='S1_no_controls'))
    rob.append(fit_multi(main_s, DUM + CTRL + ['l_hpv1h'], FE_MAIN, ['y1', 'y2'], 'S2_session').assign(robustness='S2_plus_prior_1h_pv'))
    rob.append(fit_multi(main_s[main_s.day >= 3].copy(), DUM + CTRL, FE_MAIN, ['y1', 'y2'], 'S5_washout72').assign(robustness='S5_washout72'))
    rob.append(fit_multi(main_s[main_s.top1pct_user == 0].copy(), DUM + CTRL, FE_MAIN, ['y1', 'y2'], 'S6_excl_top1').assign(robustness='S6_excl_top1pct'))
    rob.append(coefs[coefs.model == 'M2_replication'].assign(robustness='S7_replication'))
    pd.concat(rob).to_csv(RES / 'robustness.csv', index=False)

    nb = main_s[main_s.y1 == 0].copy()
    fit_multi(nb, DUM + CTRL, FE_MAIN, ['y3'], 'Y3_deferred_given_no_1h').to_csv(RES / 'secondary_y3.csv', index=False)

    for h in range(24):
        if h != 14:
            main_s[f'h{h:02d}'] = (main_s.hour == h).astype(float)
    fit_multi(main_s, HOURS + CTRL, FE_MAIN, ['y1', 'y2'], 'M2_hour_shape').to_csv(RES / 'hour_shape_M2.csv', index=False)
    (RES / 'model_summary.json').write_text(json.dumps(summ, indent=2))
    log('done')


if __name__ == '__main__':
    main()
