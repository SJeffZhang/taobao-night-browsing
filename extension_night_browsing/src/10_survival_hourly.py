"""PHASE2 sub-analysis A (revised): survival analysis with ONE GROUP PER HOUR of the day
(24 hourly bins, reference hour 14) and three purchase windows: buy within 1 h, within 3 h,
within 24 h. Event = first buy within the window; later buys are censored at the window end.
Replaces the mis-specified 3-hour time-of-day binning (see POST_PLAN_DEVIATIONS.md).
Run from inside src/.
"""
import argparse, json, time
import numpy as np, pandas as pd
from adv_common import RES, log, load, parse_range
from fastcox import FastCox

CTRL = ['l_hpv24', 'hist_buy24', 'l_pop24']
DAYD = [f'd{k}' for k in range(2, 8)]
CHECKPOINTS_H = [1 / 6, 1, 3, 6, 12, 24]
WINDOWS_H = [1, 3, 24]
REF_HOUR = 14
HOURS = [f'h{h:02d}' for h in range(24) if h != REF_HOUR]


def prep(d, window_h):
    """Event = buy within window_h hours; censored at window_h otherwise. Hourly dummies."""
    w_s = int(window_h * 3600)
    dl = d.buy_delay_s.to_numpy()
    ev = (dl >= 0) & (dl < w_s)
    d['event'] = ev.astype(np.int8)
    d['dur_h'] = np.where(ev, dl / 3600.0, float(window_h))
    for h in range(24):
        if h != REF_HOUR:
            d[f'h{h:02d}'] = (d.hour == h).astype(np.float64)
    dd = np.minimum(d.day.to_numpy(), 7)
    for k in range(2, 8):
        d[f'd{k}'] = (dd == k).astype(np.float64)
    return d


def cox(d, cols, name=''):
    t = time.time()
    f = FastCox(d.dur_h.to_numpy(), d.event.to_numpy(), d[cols].to_numpy(np.float64)).fit()
    f.robust_cov(d.user_id.to_numpy())
    r = f.summary(cols)
    r['model'] = name; r['n'] = len(d); r['events'] = int(d.event.sum()); r['clusters'] = f.n_clusters
    r['n_iter'] = f.n_iter; r['loglik'] = f.loglik
    log(name, 'n', len(d), 'events', int(d.event.sum()), f'{time.time() - t:.0f}s')
    return r


def describe(d):
    """Cumulative purchase rates by hour of day (raw, test set)."""
    out = []
    dl = d.buy_delay_s.to_numpy()
    for h in range(24):
        m = (d.hour == h).to_numpy()
        row = {'hour': h, 'episodes': int(m.sum()), 'users': int(d.user_id[m].nunique())}
        for w in CHECKPOINTS_H:
            row[f'cum_buy_pct_{w:g}h'] = float(((dl[m] >= 0) & (dl[m] < w * 3600)).mean() * 100)
        out.append(row)
    return pd.DataFrame(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--train', default='0-59'); ap.add_argument('--test', default='80-99')
    ap.add_argument('--tag', default='full')
    a = ap.parse_args()
    out_dir = RES if a.tag == 'full' else RES / 'smoke'; out_dir.mkdir(exist_ok=True)
    info = {'args': vars(a), 'timing_s': {}}
    t0 = time.time()
    rows = []
    for w in WINDOWS_H:
        tr = prep(load([parse_range(a.train)]), w)
        for name, cols in [('M1_hour', HOURS), ('M2_hour', HOURS + CTRL + DAYD)]:
            rows.append(cox(tr, cols, f'{name}_w{w}h'))
        del tr
    info['timing_s']['cox'] = time.time() - t0
    te_raw = load([parse_range(a.test)])
    describe(te_raw).to_csv(out_dir / f'survival_hourly_cumulative_{a.tag}.csv', index=False)
    info['n_test'] = len(te_raw)
    pd.concat(rows).to_csv(out_dir / f'survival_hourly_models_{a.tag}.csv', index=False)
    info['timing_s']['total'] = time.time() - t0
    (out_dir / f'survival_hourly_{a.tag}.json').write_text(json.dumps(info, indent=2))
    log('done', round(info['timing_s']['total'], 1), 's')


if __name__ == '__main__':
    main()
