"""Sub-analysis A re-run grouped by product category.

For each of the top-20 categories (by train-episode count) plus an "other" bucket,
re-run the survival analysis: Cox with hour dummies (23, ref hour 14) AND with
5-bin dummies (evening/late/small/morning, ref day), each across three purchase
windows (buy within 1h / 3h / 24h). Mirrors src/10_survival_hourly.py and
src/06_survival.py (FastCox, user-clustered Lin-Wei SE).

Outputs:
  results/category_survival_models_{tag}.csv   all Cox rows
  results/category_survival_summary_{tag}.csv  per-category night penalty + descriptives
"""
import argparse, json, time
from pathlib import Path
import numpy as np, pandas as pd
import pyarrow.dataset as ds

EXT = Path(__file__).resolve().parents[1]
RAW = EXT.parent / 'data/processed/events_clean.parquet'
RES = EXT / 'results'

import sys
sys.path.insert(0, str(EXT / 'src'))
from adv_common import RES as _R, log, load, parse_range  # noqa: E402
from fastcox import FastCox  # noqa: E402

CTRL = ['l_hpv24', 'hist_buy24', 'l_pop24']
DAYD = [f'd{k}' for k in range(2, 8)]
WINDOWS_H = [1, 3, 24]
REF_HOUR = 14
HOURS = [f'h{h:02d}' for h in range(24) if h != REF_HOUR]
BINS = ['evening', 'late', 'small', 'morning']
BIN_HOURS = {'evening': [18, 19, 20, 21], 'late': [22, 23, 0, 1], 'small': [2, 3, 4, 5], 'morning': [6, 7, 8]}
TOP_N = 20


def item_category_map():
    """item_id -> most common category_id (anonymised)."""
    ev = pd.read_parquet(RAW, columns=['item_id', 'category_id'])
    m = ev.groupby('item_id')['category_id'].agg(lambda s: s.mode().iloc[0]).rename('category_id')
    return m


def prep(d, window_h):
    w_s = int(window_h * 3600)
    dl = d.buy_delay_s.to_numpy()
    ev = (dl >= 0) & (dl < w_s)
    d['event'] = ev.astype(np.int8)
    d['dur_h'] = np.where(ev, dl / 3600.0, float(window_h))
    for h in range(24):
        if h != REF_HOUR:
            d[f'h{h:02d}'] = (d.hour == h).astype(np.float64)
    for b in BINS:
        d[b] = d.hour.isin(BIN_HOURS[b]).astype(np.float64)
    dd = np.minimum(d.day.to_numpy(), 7)
    for k in range(2, 8):
        d[f'd{k}'] = (dd == k).astype(np.float64)
    return d


def cox(d, cols, name):
    t = time.time()
    f = FastCox(d.dur_h.to_numpy(), d.event.to_numpy(), d[cols].to_numpy(np.float64)).fit()
    f.robust_cov(d.user_id.to_numpy())
    r = f.summary(cols)
    r['model'] = name; r['n'] = len(d); r['events'] = int(d.event.sum()); r['clusters'] = f.n_clusters
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--train', default='0-59')
    ap.add_argument('--tag', default='full')
    a = ap.parse_args()
    out_dir = RES if a.tag == 'full' else RES / 'smoke'
    out_dir.mkdir(exist_ok=True)

    log('load mapping + episodes')
    catmap = item_category_map()
    d = load([parse_range(a.train)])
    d = d.join(catmap, on='item_id')
    log('episodes', len(d), 'items', d.item_id.nunique())

    # top-N categories by episode count; rest -> OTHER
    counts = d.groupby('category_id').size().sort_values(ascending=False)
    top = list(counts.head(TOP_N).index)
    d['group'] = np.where(d.category_id.isin(top), d.category_id.astype(str), 'OTHER')
    grp_order = [str(c) for c in top] + ['OTHER']

    rows, summ = [], []
    for g in grp_order:
        sub = d[d.group == g]
        cat_id = '其他' if g == 'OTHER' else g
        n, users = len(sub), int(sub.user_id.nunique())
        # descriptives: day vs late 24h cumulative
        day24 = float(((sub.buy_delay_s >= 0) & (sub.buy_delay_s < 86400) & (sub.hour.isin(range(9, 18)))).mean() * 100)
        late24 = float(((sub.buy_delay_s >= 0) & (sub.buy_delay_s < 86400) & (sub.hour.isin([22, 23, 0, 1]))).mean() * 100)
        row = {'group': g, 'label': cat_id, 'n': n, 'users': users, 'share_pct': round(n / len(d) * 100, 2),
               'day_24h_pct': round(day24, 3), 'late_24h_pct': round(late24, 3)}
        for w in WINDOWS_H:
            p = prep(sub.copy(), w)
            for name, cols in [('M2_bins', BINS + CTRL + DAYD), ('M2_hour', HOURS + CTRL + DAYD)]:
                r = cox(p, cols, f'{g}|{name}|w{w}h')
                r['group'] = g; r['cat_label'] = cat_id; r['window'] = w
                rows.append(r)
                if name == 'M2_bins':
                    for term in ['late', 'small']:
                        rr = r[r.term == term].iloc[0]
                        row[f'{term}_HR_w{w}h'] = round(float(rr.hr), 3)
                        row[f'{term}_HRlo_w{w}h'] = round(float(rr.hr_ci_low), 3)
                        row[f'{term}_HRhi_w{w}h'] = round(float(rr.hr_ci_high), 3)
            del p
        summ.append(row)
        log('group', cat_id, 'n', n, f'late_HR_w24h={row.get("late_HR_w24h")}')

    pd.concat(rows).to_csv(out_dir / f'category_survival_models_{a.tag}.csv', index=False)
    pd.DataFrame(summ).to_csv(out_dir / f'category_survival_summary_{a.tag}.csv', index=False)
    log('done', len(grp_order), 'groups')


if __name__ == '__main__':
    main()
