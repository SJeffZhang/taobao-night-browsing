"""PHASE2 figures: 07 = hourly survival (1h/3h/24h windows); 08 = cold vs hot items. Run from inside src/."""
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from fig_style import apply as fig_apply
fig_apply()

from pathlib import Path
EXT = Path(__file__).resolve().parents[1]
RES = EXT / 'results'; FIG = EXT / 'figures'


def fig07():
    m = pd.read_csv(RES / 'survival_hourly_models_full.csv')
    c = pd.read_csv(RES / 'survival_hourly_cumulative_full.csv').set_index('hour')

    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6))
    ax = axes[0]
    hours = np.arange(24)
    for win, col in [('w1h', '#7C3A47'), ('w3h', '#C98A95'), ('w24h', '#403737')]:
        sub = m[(m.model == f'M2_hour_{win}') & (m.term.str.startswith('h'))].set_index('term')
        hr = [1.0 if h == 14 else sub.loc[f'h{h:02d}', 'hr'] for h in hours]
        lo = [np.nan if h == 14 else sub.loc[f'h{h:02d}', 'hr_ci_low'] for h in hours]
        hi = [np.nan if h == 14 else sub.loc[f'h{h:02d}', 'hr_ci_high'] for h in hours]
        ax.errorbar(hours, hr, yerr=[np.array(hr) - np.array(lo), np.array(hi) - np.array(hr)],
                    fmt='o-', ms=3, lw=1, capsize=2, color=col,
                    label={'w1h': 'buy within 1h', 'w3h': 'buy within 3h', 'w24h': 'buy within 24h'}[win])
    ax.axhline(1.0, color='grey', ls='--', lw=0.8)
    ax.axvline(14, color='grey', ls=':', lw=0.8)
    ax.set_xticks(hours); ax.set_xticklabels([f'{h}' for h in hours], fontsize=7)
    ax.set_yscale('log'); ax.set_ylim(0.45, 1.45)
    ax.set_xlabel('hour of first view'); ax.set_ylabel('hazard ratio vs 14:00 (log scale)')
    ax.set_title('A. Purchase hazard by hour and window\n(Cox M2, train buckets 0–59, 30.8M episodes)')
    ax.legend(fontsize=8, frameon=False)
    ax = axes[1]
    for w, col, lab in [(1, '#7C3A47', 'within 1h'), (3, '#C98A95', 'within 3h'), (24, '#403737', 'within 24h')]:
        ax.plot(hours, c[f'cum_buy_pct_{w:g}h'], 'o-', ms=3, lw=1, color=col, label=lab)
    ax.axvline(14, color='grey', ls=':', lw=0.8)
    ax.set_xticks(hours); ax.set_xticklabels([f'{h}' for h in hours], fontsize=7)
    ax.set_xlabel('hour of first view'); ax.set_ylabel('cumulative purchase (%)')
    ax.set_title('B. Cumulative purchase by hour and window\n(test buckets 80–99)')
    ax.legend(fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(FIG / '07_survival_hourly.png', dpi=150)
    fig.savefig(FIG / '07_survival_hourly.svg', bbox_inches='tight')
    plt.close(fig)


def fig08():
    d = pd.read_csv(RES / 'cold_hot_items_descriptive.csv')
    f = pd.read_csv(RES / 'cold_hot_items_fe_late_summary.csv')
    xl = [('−1\n(viewed\nonce)', -1)] + [(str(i), i) for i in range(10)]
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.4))
    xs = np.arange(11)
    ax = axes[0]
    for col, lab, ls in [('day_y1_pct', 'day, buy within 1h', '-'), ('late_y1_pct', 'late, buy within 1h', '--'),
                         ('day_y2_pct', 'day, buy within 24h', '-'), ('late_y2_pct', 'late, buy within 24h', '--')]:
        ax.plot(xs, d[col], ls, marker='o', ms=3, label=lab,
                color={'day_y1_pct': '#403737', 'late_y1_pct': '#7C3A47',
                       'day_y2_pct': '#1b5e20', 'late_y2_pct': '#7C3A47'}[col])
    ax.set_xticks(xs); ax.set_xticklabels([l for l, _ in xl], fontsize=8)
    ax.set_ylabel('purchase rate (%)'); ax.set_xlabel('item popularity decile (cold → hot)')
    ax.set_title('A. Conversion by item popularity\n(day vs late, raw)')
    ax.legend(fontsize=7.5, frameon=False)
    ax = axes[1]
    y1 = f[f.outcome == 'y1']; y2 = f[f.outcome == 'y2']
    ax.errorbar(np.arange(10), y1.coef, yerr=1.96 * y1.se, fmt='o-', color='#7C3A47', ms=4, capsize=3, label='buy within 1h')
    ax.errorbar(np.arange(10), y2.coef, yerr=1.96 * y2.se, fmt='s-', color='#D8A7AF', ms=4, capsize=3, label='buy within 24h')
    ax.axhline(0, color='grey', ls='--', lw=0.8)
    ax.set_xticks(np.arange(10)); ax.set_xticklabels([str(i) for i in range(10)], fontsize=8)
    ax.set_xlabel('item popularity decile (cold → hot)'); ax.set_ylabel('late vs day (pp, FE-adjusted)')
    ax.set_title('B. Night loss by popularity\n(fixed effects, user+item+day)')
    ax.legend(fontsize=7.5, frameon=False)
    ax = axes[2]
    ax.plot(np.arange(10), y1.relative_pct, 'o-', color='#7C3A47', ms=4, label='buy within 1h')
    ax.plot(np.arange(10), y2.relative_pct, 's-', color='#D8A7AF', ms=4, label='buy within 24h')
    ax.axhline(-24, color='grey', ls=':', lw=0.8)
    ax.set_xticks(np.arange(10)); ax.set_xticklabels([str(i) for i in range(10)], fontsize=8)
    ax.set_xlabel('item popularity decile (cold → hot)')
    ax.set_ylabel('night loss as % of day rate')
    ax.set_title('C. Relative night loss by popularity\n(FE coef / day reference mean)')
    ax.legend(fontsize=7.5, frameon=False)
    fig.tight_layout()
    fig.savefig(FIG / '08_cold_hot_items.png', dpi=150)
    fig.savefig(FIG / '08_cold_hot_items.svg', bbox_inches='tight')
    plt.close(fig)


if __name__ == '__main__':
    fig07()
    fig08()
    print('figures 07, 08 written')
