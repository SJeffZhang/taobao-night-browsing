"""Generate figures: hourly conversion shape, bin comparison, robustness."""
from pathlib import Path
import json
import matplotlib.pyplot as plt, numpy as np, pandas as pd
from fig_style import apply as fig_apply
from matplotlib.font_manager import FontProperties
_CJK_PATH = '/Library/Fonts/Arial Unicode.ttf'
CJK = FontProperties(fname=_CJK_PATH)
fig_apply()


EXT = Path(__file__).resolve().parents[1]; RES = EXT / 'results'; FIG = EXT / 'figures'
FIG.mkdir(exist_ok=True)


def fig1_hourly_shape():
    desc = pd.read_csv(RES / 'descriptives_full.csv')
    hr = desc[desc.grouping == 'hour'].set_index('level')
    hour_shape = pd.read_csv(RES / 'hour_shape_M2.csv')
    hs = hour_shape[(hour_shape.outcome == 'y1') & (hour_shape.cluster == 'user_id+item_id')].set_index('term')
    hs = hs.reindex([f'h{h:02d}' for h in range(24) if h != 14])
    hs['hour'] = [int(t[1:]) for t in hs.index]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    ax1.plot(hr.index, hr.y1_pct, 'o-', color='#7C3A47', lw=1.5)
    # 时段色块：直接用文字标注，避免图例颜色相近分不清
    ax1.axvspan(22, 24, alpha=.12, color='#7C3A47')
    ax1.axvspan(0, 2, alpha=.12, color='#7C3A47')
    ax1.axvspan(2, 6, alpha=.22, color='#C98A95')
    ax1.axvspan(9, 18, alpha=.10, color='#B9ABAE')
    ax1.set_ylim(0.355, 0.90)
    ax1.text(1.0, 0.885, '深夜', ha='center', va='top', fontsize=7.5, color='#7C3A47', fontproperties=CJK)
    ax1.text(23.0, 0.885, '深夜', ha='center', va='top', fontsize=7.5, color='#7C3A47', fontproperties=CJK)
    ax1.text(4.0, 0.885, '凌晨', ha='center', va='top', fontsize=7.5, color='#8E4A57', fontproperties=CJK)
    ax1.text(13.5, 0.368, '白天（参照组）', ha='center', va='bottom', fontsize=7.5, color='#7A6E6E', fontproperties=CJK)
    ax1.set_xlabel('Hour of day (Shanghai)'); ax1.set_ylabel('1-hour purchase rate (%)')
    ax1.set_title('(a) Raw conversion by hour'); ax1.grid(alpha=.2)
    ax2.axhline(0, color='gray', lw=.8, ls='--')
    ax2.errorbar(hs.hour, hs.coef, yerr=1.96 * hs.se, fmt='o', color='#7C3A47', capsize=3, markersize=4)
    ax2.axhline(0, color='k', lw=.5)
    ax2.set_xlabel('Hour (ref: 14)'); ax2.set_ylabel('M2 coef vs hour 14 (pp)')
    ax2.set_title('(b) User/item/day FE + controls'); ax2.grid(alpha=.2)
    plt.tight_layout(); plt.savefig(FIG / '01_hourly_shape.png', dpi=150, bbox_inches='tight')
    plt.savefig(FIG / '01_hourly_shape.svg', bbox_inches='tight'); plt.close()


def fig2_bin_comparison():
    prim = pd.read_csv(RES / 'primary_tests.csv')
    bins = ['late', 'small']
    ys = ['y1', 'y2']
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6), sharey=True)
    for j, y in enumerate(ys):
        ax = axes[j]
        sub = prim[prim.outcome == y]
        ypos = np.arange(len(bins))
        cols = ['#7C3A47', '#D8A7AF']
        ax.barh(ypos, sub.coef, height=0.44, color=cols, zorder=3)
        ax.errorbar(sub.coef, ypos, xerr=1.96 * sub.se, fmt='none', ecolor='#403737',
                    capsize=4, lw=0.9, zorder=4)
        for i, r in enumerate(sub.itertuples()):
            ax.text(r.coef / 2, i, f'{r.coef:.2f} pp', va='center', ha='center',
                    fontsize=9.5, color='white' if i == 0 else '#403737',
                    fontweight='bold', zorder=5)
        ax.set_yticks(ypos); ax.set_yticklabels(['late (22-01)', 'small (02-05)'])
        ax.axvline(0, color='#4A4545', lw=0.8)
        ax.set_xlim(min(sub.ci_low) - 0.05, 0.03)
        ax.set_xlabel('coef vs day (pp)')
        ax.set_title(f'({chr(97 + j)}) {"1-hour" if y == "y1" else "24-hour"} purchase')
        ax.grid(axis='x', zorder=0)
    plt.tight_layout(); plt.savefig(FIG / '02_bin_comparison.png', dpi=150, bbox_inches='tight')
    plt.savefig(FIG / '02_bin_comparison.svg', bbox_inches='tight'); plt.close()


def fig3_robustness():
    rob = pd.read_csv(RES / 'robustness.csv')
    keep = ['main', 'S1_no_controls', 'S2_plus_prior_1h_pv', 'S5_washout72', 'S6_excl_top1pct', 'S7_replication']
    label_map = {'main': 'Main', 'S1_no_controls': 'No controls', 'S2_plus_prior_1h_pv': '+ prior 1h pv',
                 'S5_washout72': 'Washout 72h', 'S6_excl_top1pct': 'Excl top 1%', 'S7_replication': 'Replication'}
    r = rob[(rob.robustness.isin(keep)) & (rob.cluster == 'user_id+item_id') & (rob.outcome.isin(['y1', 'y2'])) & (rob.term == 'late')].copy()
    # explicit display order so row i == keep[i]; do NOT sort alphabetically (labels are positional)
    r['pos'] = r.robustness.map({k: i for i, k in enumerate(keep)})
    r = r.sort_values(['pos', 'outcome'])
    fig, ax = plt.subplots(figsize=(8, 4))
    for j, y in enumerate(['y1', 'y2']):
        sub = r[r.outcome == y]
        x = np.arange(len(sub)) + j * .35
        ax.barh(x, sub.coef, xerr=1.96 * sub.se, height=.3, label=f'{"1h" if y == "y1" else "24h"} purchase',
                color='#7C3A47' if y == 'y1' else '#A85D68', capsize=3, alpha=.85)
    ax.axvline(0, color='k', lw=.8)
    ax.set_yticks(np.arange(len(keep)) + .175)
    ax.set_yticklabels([label_map[k] for k in keep])
    ax.set_xlabel('late vs day coef (pp)'); ax.set_title('Robustness: late (22-01) vs day (09-17)')
    ax.legend(loc='lower right'); ax.grid(axis='x', alpha=.2)
    plt.tight_layout(); plt.savefig(FIG / '03_robustness.png', dpi=150, bbox_inches='tight')
    plt.savefig(FIG / '03_robustness.svg', bbox_inches='tight'); plt.close()


def main():
    fig1_hourly_shape()
    fig2_bin_comparison()
    fig3_robustness()
    manifest = [{'name': '01_hourly_shape', 'desc': 'Raw and FE-adjusted hourly conversion'},
                {'name': '02_bin_comparison', 'desc': 'Primary tests: late & small vs day'},
                {'name': '03_robustness', 'desc': 'Robustness checks for late coef'},
                {'name': '04_cumulative_purchase_by_bin', 'desc': 'Test-set cumulative purchase by time bin'},
                {'name': '05_cox_piecewise_hr', 'desc': 'Cox HRs: 0-24h, 0-1h, 1-24h by time bin'},
                {'name': '06_causal_forest_gates', 'desc': 'Causal Forest GATES and CATE distribution'},
                {'name': '07_survival_hourly', 'desc': 'PHASE2 A: hourly survival, 1h/3h/24h purchase windows'},
                {'name': '08_cold_hot_items', 'desc': 'PHASE2 B: cold vs hot item night loss'}]
    (FIG / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    print('3 figures saved')


if __name__ == '__main__':
    main()
