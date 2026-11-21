"""Independent row-wise recount of the pre-t0 features for 300 random episodes, plus a split-overlap check."""
import json
import numpy as np, pandas as pd
from adv_common import DATA, RES, EXT

START, DAY = 1511539200, 86400


def main():
    ep = pd.read_parquet(DATA / 'episodes_features.parquet')
    s = ep.sample(300, random_state=11)
    ev = pd.read_parquet(EXT / 'data/processed/events_clean.parquet', columns=['user_id', 'item_id', 'behavior', 'ts'],
                         filters=[('user_id', 'in', s.user_id.unique().tolist())])
    evi = pd.read_parquet(EXT / 'data/processed/events_clean.parquet', columns=['item_id', 'behavior', 'ts'],
                          filters=[('item_id', 'in', s.item_id.unique().tolist()), ('behavior', '==', 4)])
    mism = {c: 0 for c in ['u_pv_cum', 'u_fav_cum', 'u_cart_cum', 'u_buy_cum', 'i_buy24']}
    for r in s.itertuples():
        u = ev[(ev.user_id == r.user_id) & (ev.ts >= START) & (ev.ts < r.t0)]
        for code, c in [(1, 'u_pv_cum'), (2, 'u_fav_cum'), (3, 'u_cart_cum'), (4, 'u_buy_cum')]:
            mism[c] += int((u.behavior == code).sum() != getattr(r, c))
        mism['i_buy24'] += int(((evi.item_id == r.item_id) & (evi.ts >= r.t0 - DAY) & (evi.ts < r.t0)).sum() != r.i_buy24)
    users = {k: set(ep.user_id[ep.bucket.between(lo, hi)]) for k, (lo, hi) in [('train', (0, 59)), ('val', (60, 79)), ('test', (80, 99))]}
    out = {'feature_mismatches_of_300': mism,
           'split_user_overlap': {f'{a}&{b}': len(users[a] & users[b]) for a, b in [('train', 'val'), ('train', 'test'), ('val', 'test')]},
           'split_sizes': {k: int(ep.bucket.between(lo, hi).sum()) for k, (lo, hi) in [('train', (0, 59)), ('val', (60, 79)), ('test', (80, 99))]},
           'split_users': {k: len(v) for k, v in users.items()}}
    (RES / 'features_verification.json').write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    main()
