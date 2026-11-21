"""Figures for the advanced methods: cumulative purchase curves, piecewise Cox HRs, Causal Forest GATES and CATE distribution."""
import json
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from adv_common import EXT, RES
from fig_style import apply as fig_apply
fig_apply()

FIG = EXT / 'figures'; FIG.mkdir(exist_ok=True)
COL = {'day': '#403737', 'evening': '#A85D68', 'late': '#7C3A47', 'small': '#D8A7AF', 'morning': '#C98A95'}
LAB = {'day': 'Day 09-17 (ref)', 'evening': 'Evening 18-21', 'late': 'Late 22-01', 'small': 'Small hours 02-05', 'morning': 'Morning 06-08'}


def save(fig, name):
    fig.savefig(FIG / f'{name}.png', dpi=150, bbox_inches='tight'); fig.savefig(FIG / f'{name}.svg', bbox_inches='tight')
    plt.close(fig)


def fig_cumulative():
    c = pd.read_csv(RES / 'survival_cumulative_by_bin_full.csv').set_index('bin')
    hrs = [0, 1 / 6, 1, 3, 6, 12, 24]
    cols = ['cum_buy_pct_0.166667h', 'cum_buy_pct_1h', 'cum_buy_pct_3h', 'cum_buy_pct_6h', 'cum_buy_pct_12h', 'cum_buy_pct_24h']
    fig, ax = plt.subplots(figsize=(7, 4.2))
    for b in ['day', 'evening', 'late', 'small', 'morning']:
        ax.plot(hrs, [0] + c.loc[b, cols].tolist(), marker='o', ms=4, color=COL[b], label=LAB[b], lw=2 if b in ('day', 'late') else 1.3)
    ax.axvline(1, color='k', lw=.6, ls=':')
    ax.set_xlabel('Hours since first view'); ax.set_ylabel('Cumulative purchase rate (%)')
    ax.set_title('Test set: cumulative purchase after first view, by hour of first view')
    ax.set_xticks([0, 1, 3, 6, 12, 24]); ax.legend(fontsize=8, loc='lower right'); ax.grid(alpha=.2)
    save(fig, '04_cumulative_purchase_by_bin')


def fig_piecewise():
    m = pd.read_csv(RES / 'survival_models_full.csv')
    terms = ['evening', 'late', 'small', 'morning']
    fig, ax = plt.subplots(figsize=(7, 3.8))
    for j, (mod, lab, mk) in enumerate([('M2_controls', '0-24h (M2)', 'o'), ('PW_0_1h', '0-1h', 's'), ('PW_1h_24h', '1-24h (at risk at 1h)', '^')]):
        r = m[(m.model == mod)].set_index('term').loc[terms]
        y = np.arange(len(terms)) + (j - 1) * .22
        ax.errorbar(r.hr, y, xerr=[r.hr - r.hr_ci_low, r.hr_ci_high - r.hr], fmt=mk, capsize=3, label=lab)
    ax.axvline(1, color='k', lw=.8)
    ax.set_yticks(range(len(terms))); ax.set_yticklabels([LAB[t] for t in terms])
    ax.set_xlabel('Hazard ratio vs day 09-17 (95% CI, user-clustered)')
    ax.set_title('Cox models fitted on train (30.8M episodes)'); ax.legend(fontsize=8); ax.grid(axis='x', alpha=.2)
    save(fig, '05_cox_piecewise_hr')


def fig_cf():
    p = RES / 'causal_forest_full.json'
    if not p.exists():
        return False
    cf = json.loads(p.read_text())['test']
    g = pd.DataFrame(cf['gates'])
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4))
    a1.errorbar(g.quintile, g.coef, yerr=1.96 * g.se, fmt='o', capsize=4, color='#7C3A47', label='GATES (residual regression)')
    a1.plot(g.quintile, g.tau_hat_mean, 'x--', color='gray', label='mean predicted CATE')
    a1.axhline(cf['dml_ate']['coef'], color='#7C3A47', ls=':', lw=1, label='test ATE')
    a1.axhline(0, color='k', lw=.8)
    a1.set_xlabel('Quintile of predicted CATE (1 = most negative)'); a1.set_ylabel('Late vs day effect on 1h purchase (pp)')
    a1.set_title('(a) Test set GATES'); a1.legend(fontsize=8); a1.grid(alpha=.2)
    q = pd.read_csv(RES / 'cate_quantiles_full.csv')
    q = q[(q['quantile'] >= .01) & (q['quantile'] <= .99)]
    a2.plot(q.cate_pp, q['quantile'], color='#7C3A47')
    a2.axvline(0, color='k', lw=.8)
    a2.set_xlabel('Predicted CATE (pp)'); a2.set_ylabel('Cumulative share of test episodes')
    a2.set_title('(b) Distribution of predicted CATE (1st-99th pct)'); a2.grid(alpha=.2)
    save(fig, '06_causal_forest_gates')
    return True


if __name__ == '__main__':
    fig_cumulative(); fig_piecewise()
    print('cf figure', fig_cf())
