"""PHASE2 sub-analysis B: cold vs hot item night-loss heterogeneity.

Sub-proposition from the Causal Forest finding: cold items convert more per view in the
daytime, so their absolute night loss is largest; hot items are 'looked at a lot but
bought rarely', so their absolute night loss is small; relative loss is similar across
popularity. Uses the main FE sample (user buckets 40-59). Run from inside src/.

Design:
- Popularity = item_n = number of first-view episodes (= distinct first-viewers) per item
  in the sample. Deciles are defined over items with item_n >= 2; items viewed by exactly
  one user (item_n == 1) are reported separately (decile = -1): they have no within-item
  comparison, so the fixed-effects part cannot estimate them.
- Descriptive: raw day vs late conversion by decile (all items, incl. decile -1).
- Adjusted: FE LPM identical to the main M2 (user + item + day FE, two-way clustered SE,
  controls l_hpv24, hist_buy24, l_pop) fit within each decile 0..9.
"""
import argparse, importlib, json, sys, time
import numpy as np, pandas as pd
from pathlib import Path

EXT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXT / 'src'))
sys.path.insert(0, str(EXT.parent / 'src'))
from common import log  # noqa: E402

DATA = EXT / 'data'; RES = EXT / 'results'
m2mod = importlib.import_module('02_models')
derive, fit_multi = m2mod.derive, m2mod.fit_multi
DUM, CTRL, FE_MAIN = m2mod.DUM, m2mod.CTRL, m2mod.FE_MAIN


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bucket-lo', type=int, default=40)
    ap.add_argument('--bucket-hi', type=int, default=59)
    a = ap.parse_args()
    log('load')
    full = derive(pd.read_parquet(DATA / 'episodes_hour.parquet'))
    d = full[full.bucket.between(a.bucket_lo, a.bucket_hi)].copy()
    del full
    d['item_n'] = d.groupby('item_id').item_id.transform('size')
    d['decile'] = -1
    mask = d.item_n >= 2
    d.loc[mask, 'decile'] = pd.qcut(d.loc[mask, 'item_n'].rank(method='first'), 10, labels=False)
    d['decile'] = d.decile.astype(int)
    n1 = int((d.item_n == 1).sum())
    log('n', len(d), 'items', d.item_id.nunique(), 'users', d.user_id.nunique(),
        'n1_rows', n1, f'({n1 / len(d) * 100:.1f}%)')

    # --- descriptive: raw day vs late conversion by decile (incl. decile -1) ---
    day, late = d[d.bin == 'day'], d[d.bin == 'late']
    desc_rows = []
    for i in list(range(-1, 10)):
        ds, dys, lts = d[d.decile == i], day[day.decile == i], late[late.decile == i]
        desc_rows.append({
            'decile': int(i),
            'n_episodes': int(len(ds)),
            'n_items': int(ds.item_id.nunique()),
            'n_users': int(ds.user_id.nunique()),
            'item_n_min': int(ds.item_n.min()) if len(ds) else np.nan,
            'item_n_max': int(ds.item_n.max()) if len(ds) else np.nan,
            'mean_pop24': float(ds.pop24.mean()),
            'day_y1_pct': float(dys.y1.mean()),
            'day_y2_pct': float(dys.y2.mean()),
            'late_y1_pct': float(lts.y1.mean()),
            'late_y2_pct': float(lts.y2.mean()),
            'late_minus_day_y1': float(lts.y1.mean() - dys.y1.mean()),
            'late_minus_day_y2': float(lts.y2.mean() - dys.y2.mean()),
        })
    desc = pd.DataFrame(desc_rows)
    desc['relative_late_day_y1_pct'] = desc.late_minus_day_y1 / desc.day_y1_pct * 100
    desc['relative_late_day_y2_pct'] = desc.late_minus_day_y2 / desc.day_y2_pct * 100
    desc.to_csv(RES / 'cold_hot_items_descriptive.csv', index=False)
    log('descriptive saved')

    # --- adjusted: FE LPM (same as main M2) within each decile 0..9 ---
    fe_rows = []
    for i in range(10):
        dsub = d[d.decile == i].copy()
        r = fit_multi(dsub, DUM + CTRL, FE_MAIN, ['y1', 'y2'], f'M2_decile_{i}')
        r['decile'] = i
        fe_rows.append(r)
    fe = pd.concat(fe_rows)
    fe.to_csv(RES / 'cold_hot_items_fe.csv', index=False)
    late_fe = fe[(fe.term == 'late') & (fe.cluster == 'user_id+item_id')].copy()
    late_fe['relative_pct'] = late_fe.coef / late_fe.day_ref_mean * 100
    late_fe[['decile', 'outcome', 'coef', 'se', 'ci_low', 'ci_high', 'p', 'n', 'day_ref_mean',
             'relative_pct']].to_csv(RES / 'cold_hot_items_fe_late_summary.csv', index=False)
    log('fe saved')
    print(desc.round(3).to_string(index=False))


if __name__ == '__main__':
    main()
