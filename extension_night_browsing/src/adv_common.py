"""Shared loading, split and feature helpers for the advanced methods (ANALYSIS_PLAN_ADVANCED.md v2)."""
from pathlib import Path
import sys, time
import numpy as np, pandas as pd
import pyarrow.dataset as ds

EXT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXT / 'vendor'))
DATA = EXT / 'data'; RES = EXT / 'results'

LATE = [22, 23, 0, 1]
DAYH = list(range(9, 18))
BINS = {'day': DAYH, 'evening': [18, 19, 20, 21], 'late': LATE, 'small': [2, 3, 4, 5], 'morning': [6, 7, 8]}
WEEKEND_DAYS = (1, 7, 8)  # day 0 = Sat 2017-11-25
CF_FEATURES = ['l_hpv24', 'l_hpv1h', 'hist_buy24', 'l_pop24', 'l_upv', 'l_ufav', 'l_ucart', 'l_ubuy', 'l_ibuy24',
               'day', 'is_weekend']


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


def parse_range(s):
    lo, hi = map(int, s.split('-'))
    return lo, hi


def load(ranges, hours=None):
    """Episodes whose user bucket falls in any inclusive (lo, hi) range; optional t0-hour filter."""
    f = None
    for lo, hi in ranges:
        g = (ds.field('bucket') >= lo) & (ds.field('bucket') <= hi)
        f = g if f is None else (f | g)
    if hours is not None:
        f = f & ds.field('hour').isin(hours)
    d = ds.dataset(DATA / 'episodes_features.parquet').to_table(filter=f).to_pandas()
    dl = d.buy_delay_s.to_numpy()
    d['y1'] = ((dl >= 0) & (dl < 3600)).astype(np.float64)
    d['y24'] = ((dl >= 0) & (dl < 86400)).astype(np.float64)
    d['l_hpv24'] = np.log1p(d.hist_pv24); d['l_hpv1h'] = np.log1p(d.hist_pv1h); d['l_pop24'] = np.log1p(d.pop24)
    d['l_upv'] = np.log1p(d.u_pv_cum); d['l_ufav'] = np.log1p(d.u_fav_cum); d['l_ucart'] = np.log1p(d.u_cart_cum)
    d['l_ubuy'] = np.log1p(d.u_buy_cum); d['l_ibuy24'] = np.log1p(d.i_buy24)
    d['hist_buy24'] = d.hist_buy24.astype(np.float64)
    d['day'] = d.day.astype(np.int64)
    d['is_weekend'] = d.day.isin(WEEKEND_DAYS).astype(np.float64)
    hb = np.empty(24, dtype=object)
    for name, hs in BINS.items():
        hb[hs] = name
    d['bin'] = hb[d.hour.to_numpy()]
    return d


def split_name(bucket, train, val, test):
    out = np.full(len(bucket), '', dtype=object)
    for name, (lo, hi) in [('train', train), ('val', val), ('test', test)]:
        out[(bucket >= lo) & (bucket <= hi)] = name
    return out


def cluster_ols(y, X, groups):
    """OLS with one-way cluster-robust covariance (CR1). Returns beta, cov."""
    XtX_inv = np.linalg.inv(X.T @ X)
    beta = XtX_inv @ (X.T @ y)
    e = y - X @ beta
    code = pd.factorize(groups)[0]; G = code.max() + 1
    S = np.column_stack([np.bincount(code, weights=X[:, j] * e, minlength=G) for j in range(X.shape[1])])
    n, k = X.shape
    cov = XtX_inv @ (S.T @ S) @ XtX_inv * (G / (G - 1)) * ((n - 1) / (n - k))
    return beta, cov, int(G)
