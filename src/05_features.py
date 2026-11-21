"""Pre-t0 features for the advanced methods (ANALYSIS_PLAN_ADVANCED.md v2).

Adds to every episode: user pv/fav/cart/buy counts in [START, t0) and item buys by any user in [t0-24h, t0).
The focal pair has no fav/cart/buy before t0 by construction, so item buys before t0 are by other users.
Strictly before t0: same-second events are not counted.
"""
from pathlib import Path
import json, time
import numpy as np, pandas as pd

EXT = Path(__file__).resolve().parents[1]
PROC = EXT / 'data/processed'
DATA = EXT / 'data'; RES = EXT / 'results'
START, DAY = 1511539200, 86400


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


def count_in(sorted_key, base, lo, hi):
    return (np.searchsorted(sorted_key, base + hi, 'left') - np.searchsorted(sorted_key, base + lo, 'left')).astype(np.int32)


def main():
    ep = pd.read_parquet(DATA / 'episodes_hour.parquet')
    ev = pd.read_parquet(PROC / 'events_clean.parquet', columns=['user_id', 'item_id', 'behavior', 'ts'])
    log('loaded', len(ep), 'episodes', len(ev), 'events')
    t0 = ep.t0.to_numpy().astype(np.int64)
    ub = ep.user_id.to_numpy().astype(np.int64) << 32
    u = ev.user_id.to_numpy().astype(np.int64); b = ev.behavior.to_numpy(); ts = ev.ts.to_numpy().astype(np.int64)
    for code, name in [(1, 'u_pv_cum'), (2, 'u_fav_cum'), (3, 'u_cart_cum'), (4, 'u_buy_cum')]:
        m = b == code
        key = np.sort((u[m] << 32) + ts[m])
        ep[name] = count_in(key, ub, np.int64(START), t0)
        log(name, 'mean', float(ep[name].mean()))
        del key
    m = b == 4
    ikey = np.sort((ev.item_id.to_numpy()[m].astype(np.int64) << 32) + ts[m])
    ep['i_buy24'] = count_in(ikey, ep.item_id.to_numpy().astype(np.int64) << 32, t0 - DAY, t0)
    log('i_buy24 mean', float(ep.i_buy24.mean()))
    assert (ep.u_pv_cum >= ep.hist_pv24).all()
    ep.to_parquet(DATA / 'episodes_features.parquet', index=False)
    (RES / 'features_summary.json').write_text(json.dumps(
        {c: {'mean': float(ep[c].mean()), 'p99': float(ep[c].quantile(.99))} for c in ['u_pv_cum', 'u_fav_cum', 'u_cart_cum', 'u_buy_cum', 'i_buy24']}, indent=2))
    log('saved', len(ep))


if __name__ == '__main__':
    main()
