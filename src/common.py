"""Shared estimation helpers: absorbed-FE OLS with two-way clustered covariance (Cameron-Gelbach-Miller)."""
from pathlib import Path
import sys, time
import numpy as np, pandas as pd
from scipy import stats

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / 'vendor'))
import pyhdfe  # noqa: E402

PRIMARY = ['lpv', 'fav', 'cart', 'l_scpv', 'l_scit']
CONTROLS = ['l_ocpv', 'l_hpv', 'hist_buy', 'l_pop']
BINS = ['pv2', 'pv3', 'pv45', 'pv6p']


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


def derive(ep):
    d = ep.copy()
    d['y100'] = d.y.astype(float) * 100
    d['y_other100'] = d.y_other_sc.astype(float) * 100
    d['lpv'] = np.log2(d.n_pv)
    d['pv2'] = (d.n_pv == 2).astype(float); d['pv3'] = (d.n_pv == 3).astype(float)
    d['pv45'] = d.n_pv.between(4, 5).astype(float); d['pv6p'] = (d.n_pv >= 6).astype(float)
    d['l_scpv'] = np.log2(1 + d.sc_pv); d['l_scit'] = np.log2(1 + d.sc_items)
    d['l_ocpv'] = np.log2(1 + d.oc_pv); d['l_hpv'] = np.log2(1 + d.hist_pv); d['l_pop'] = np.log2(1 + d.popularity_24h)
    for c in ['fav', 'cart', 'hist_buy']:
        d[c] = d[c].astype(float)
    d['lpv_x_fav'] = d.lpv * d.fav; d['lpv_x_cart'] = d.lpv * d.cart
    return d


def cluster_cov(X, e, groups, k_total):
    n, k = X.shape
    bread = np.linalg.inv(X.T @ X)
    score = X * e[:, None]

    def meat(g):
        code = pd.factorize(g, sort=False)[0]; G = int(code.max() + 1)
        sums = np.column_stack([np.bincount(code, weights=score[:, j], minlength=G) for j in range(k)])
        return sums.T @ sums * (G / (G - 1)) * ((n - 1) / (n - k_total)), G

    M, G = meat(groups[0]); counts = [G]
    if len(groups) == 2:
        M2, G2 = meat(groups[1])
        inter = pd.MultiIndex.from_arrays(groups) if not isinstance(groups[0], np.ndarray) else \
            groups[0].astype(np.int64) * (1 << 32) + groups[1].astype(np.int64)
        M12, G12 = meat(inter)
        M = M + M2 - M12; counts += [G2, G12]
    cov = bread @ M @ bread; cov = (cov + cov.T) / 2
    eig = np.linalg.eigvalsh(cov)
    if eig.min() < 0:  # standard PSD repair for two-way clustering
        w, v = np.linalg.eigh(cov); cov = v @ np.diag(np.clip(w, 0, None)) @ v.T
    return cov, counts, float(eig.min())


def fit(d, xcols, fes, yvar='y100', cluster=('user_id', 'item_id'), name=''):
    t = time.time()
    f = d.dropna(subset=xcols + [yvar])
    if fes:
        ids = np.column_stack([pd.factorize(f[c], sort=False)[0] for c in fes])
        opts = {'tol': 1e-9, 'iteration_limit': 20000, 'transform': 'symmetric', 'acceleration': 'cg'} if len(fes) > 1 else None
        # absorbed df: exact (pairwise) for <=2 FE, conservative level count ('simple') for 3 FE
        algo = pyhdfe.create(ids, drop_singletons=True, compute_degrees=True, degrees_method='pairwise' if len(fes) <= 2 else 'simple',
                             residualize_method='map' if len(fes) > 1 else 'within', options=opts)
        keep = ~algo.singleton_indices if algo.singleton_indices is not None else np.ones(len(f), bool)
        Z = algo.residualize(f[xcols + [yvar]].to_numpy(float))
        X, y = Z[:, :-1], Z[:, -1]
        g = f.loc[keep]
        deg = int(algo.degrees)
    else:
        X = np.column_stack([np.ones(len(f)), f[xcols].to_numpy(float)]); y = f[yvar].to_numpy(float); g = f; deg = 0
    rank = np.linalg.matrix_rank(X)
    assert rank == X.shape[1], (name, rank, X.shape)
    beta = np.linalg.lstsq(X, y, rcond=None)[0]; e = y - X @ beta
    cov, counts, mineig = cluster_cov(X, e, [g[c].to_numpy() for c in cluster], deg + X.shape[1])
    names = (['const'] if not fes else []) + xcols
    se = np.sqrt(np.diag(cov)); dfree = min(counts[:len(cluster)]) - 1
    tcrit = stats.t.ppf(0.975, dfree)
    res = pd.DataFrame({'term': names, 'coef': beta, 'se': se, 'ci_low': beta - tcrit * se, 'ci_high': beta + tcrit * se,
                        'p': 2 * stats.t.sf(np.abs(beta / se), dfree)})
    res['n'] = len(g); res['n_dropped_singletons'] = len(f) - len(g); res['users'] = g.user_id.nunique(); res['items'] = g.item_id.nunique()
    res['y_mean'] = g[yvar].mean(); res['fe'] = '+'.join(fes) if fes else 'none'; res['model'] = name
    res['clusters_user'] = counts[0]; res['clusters_item'] = counts[1] if len(counts) > 1 else np.nan
    res['min_cov_eig'] = mineig
    log(name, 'n', len(g), f'{time.time()-t:.0f}s')
    return res, cov, beta, names


def wald(beta, cov, names, terms, dfree=None):
    idx = [names.index(t) for t in terms]
    b = beta[idx]; V = cov[np.ix_(idx, idx)]
    stat = float(b @ np.linalg.pinv(V) @ b)
    return {'terms': terms, 'chi2': stat, 'df': len(terms), 'p': float(stats.chi2.sf(stat, len(terms)))}


def diff_ci(beta, cov, names, a, b):
    i, j = names.index(a), names.index(b)
    dlt = beta[i] - beta[j]; se = float(np.sqrt(cov[i, i] + cov[j, j] - 2 * cov[i, j]))
    return {'diff': float(dlt), 'se': se, 'ci_low': float(dlt - 1.96 * se), 'ci_high': float(dlt + 1.96 * se)}
