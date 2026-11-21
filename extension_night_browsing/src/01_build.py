"""Build user-item first-view episodes with t0 hour and first-buy delay (ANALYSIS_PLAN.md).

No landmark: immediate buys are kept. Eligibility: no fav/cart/buy of the pair strictly before t0,
t0 >= START + 1 day, t0 + 24h <= END. Same-second events are simultaneous.
"""
from pathlib import Path
import json, time
import numpy as np, pandas as pd

EXT = Path(__file__).resolve().parents[1]
BASE = EXT.parent
PROC = BASE / 'data/processed'
OUT = EXT / 'data'; RES = EXT / 'results'
START, END, DAY, HOUR = 1511539200, 1512316800, 86400, 3600
PV, BUY = 1, 4


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


def window_count(sorted_key, base, lo, hi):
    """Count of sorted_key values in [base+lo, base+hi)."""
    return (np.searchsorted(sorted_key, base + hi, 'left') - np.searchsorted(sorted_key, base + lo, 'left')).astype(np.int32)


def main():
    OUT.mkdir(exist_ok=True); RES.mkdir(exist_ok=True)
    ev = pd.read_parquet(PROC / 'events_clean.parquet', columns=['user_id', 'item_id', 'behavior', 'ts'])
    u = ev.user_id.to_numpy().astype(np.int64); it = ev.item_id.to_numpy().astype(np.int64)
    b = ev.behavior.to_numpy(); ts = ev.ts.to_numpy().astype(np.int64)
    assert u.max() < 2 ** 20 and it.max() < 2 ** 23
    key = (u << 23) | it
    log('events', len(ev))

    pv = b == PV
    first_pv = pd.Series(ts[pv]).groupby(key[pv]).min()
    nonpv = ~pv
    first_nonpv = pd.Series(ts[nonpv]).groupby(key[nonpv]).min()
    isbuy = b == BUY
    first_buy = pd.Series(ts[isbuy]).groupby(key[isbuy]).min()
    log('pairs with pv', len(first_pv))

    k = first_pv.index.to_numpy(); t0 = first_pv.to_numpy()
    fn = first_nonpv.reindex(k).to_numpy()
    fb = first_buy.reindex(k).to_numpy()
    wf = [('user_item_pairs_with_pv', len(k))]
    m = t0 >= START + DAY; wf.append(('t0_after_1d_washout', int(m.sum())))
    m &= t0 + DAY <= END; wf.append(('complete_24h_outcome_window', int(m.sum())))
    m &= ~(fn < t0); wf.append(('no_fav_cart_buy_before_t0', int(m.sum())))
    k, t0, fb = k[m], t0[m], fb[m]
    assert not (fb < t0).any()

    ep = pd.DataFrame({'user_id': (k >> 23).astype(np.int32), 'item_id': (k & (2 ** 23 - 1)).astype(np.int32), 't0': t0})
    ep['buy_delay_s'] = np.where(np.isnan(fb), -1, fb - t0).astype(np.int64)
    ep['hour'] = (((t0 - START) % DAY) // HOUR).astype(np.int8)
    ep['day'] = ((t0 - START) // DAY).astype(np.int8)

    # user history (other items only: the focal pair has no event before t0 by construction)
    uk_pv = np.sort((u[pv] << 32) + ts[pv]); uk_buy = np.sort((u[isbuy] << 32) + ts[isbuy])
    ub = ep.user_id.to_numpy().astype(np.int64) << 32
    ep['hist_pv24'] = window_count(uk_pv, ub, t0 - DAY, t0)
    ep['hist_pv1h'] = window_count(uk_pv, ub, t0 - HOUR, t0)
    ep['hist_buy24'] = (window_count(uk_buy, ub, t0 - DAY, t0) > 0).astype(np.int8)
    del uk_pv, uk_buy
    ik_pv = np.sort((it[pv] << 32) + ts[pv])
    ep['pop24'] = window_count(ik_pv, ep.item_id.to_numpy().astype(np.int64) << 32, t0 - DAY, t0)
    del ik_pv

    bk = pd.read_parquet(PROC / 'user_buckets.parquet').set_index('user_id').bucket
    ep['bucket'] = bk.reindex(ep.user_id.to_numpy()).to_numpy().astype(np.int16)
    cnt = pd.Series(u).value_counts()
    thr = float(cnt.quantile(.99))
    ep['top1pct_user'] = ep.user_id.isin(cnt.index[cnt > thr]).astype(np.int8)
    ep.to_parquet(OUT / 'episodes_hour.parquet', index=False)
    summary = {'waterfall': wf, 'episodes': len(ep), 'users': int(ep.user_id.nunique()), 'items': int(ep.item_id.nunique()),
               'top1pct_user_event_threshold': thr, 'top1pct_users': int((cnt > thr).sum())}
    (RES / 'sample_waterfall.json').write_text(json.dumps(summary, indent=2))
    log(summary)


if __name__ == '__main__':
    main()
