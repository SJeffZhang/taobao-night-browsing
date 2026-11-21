"""Category overview: how many, how concentrated, and what they look like."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np, pandas as pd
from matplotlib.font_manager import FontProperties
from fig_style import apply, MAROON, MAROON_MID, ROSE, PINK, GRAY as PGRAY, CHAR

apply()
CJK = FontProperties(fname='/Library/Fonts/Arial Unicode.ttf')
EXT = Path(__file__).resolve().parents[1]
RAW = EXT / 'data/processed/events_clean.parquet'
OUT = EXT / 'figures'

ev = pd.read_parquet(RAW, columns=['category_id'])
vc = ev.category_id.value_counts()
tot, ncat = len(ev), vc.size
share = vc / tot * 100
cum = share.cumsum()

fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.4, 4.6), gridspec_kw={'width_ratios': [1.05, 1]})

# left: top 12
top = share.head(12)[::-1]
ypos = np.arange(len(top))
a1.barh(ypos, top.values, height=.62, color=[MAROON if i >= 10 else MAROON_MID for i in range(len(top))])
a1.set_yticks(ypos); a1.set_yticklabels([f'{int(i)}' for i in top.index], fontsize=8.5, color=CHAR)
for y, v in zip(ypos, top.values):
    a1.text(v + 0.06, y, f'{v:.2f}%', va='center', fontsize=8, color=CHAR)
a1.set_xlim(0, max(top) * 1.22)
a1.set_xlabel('share of all events (%)', color=CHAR)
a1.set_title('Top 12 categories (anonymised IDs)', fontsize=11, color=CHAR)
a1.grid(axis='x')

# right: cumulative
a2.plot(np.arange(1, ncat + 1), cum.values, color=MAROON, lw=1.6)
a2.set_xscale('log')
a2.set_ylim(0, 101)
for k in [10, 100, 1000]:
    a2.axvline(k, color=PINK, lw=.8, ls=':')
    a2.plot([k], [cum.iloc[k - 1]], 'o', color=MAROON, ms=4)
    a2.annotate(f'top {k}: {cum.iloc[k-1]:.0f}%', xy=(k, cum.iloc[k - 1]),
                xytext=(k * 1.15, cum.iloc[k - 1] - 13), fontsize=8.5, color=MAROON,
                arrowprops=dict(arrowstyle='-', color=MAROON, lw=.6))
a2.set_xlabel('category rank (log scale)', color=CHAR)
a2.set_ylabel('cumulative share of events (%)', color=CHAR)
a2.set_title(f'Long tail: {ncat:,} categories in total', fontsize=11, color=CHAR)
a2.grid(True)

fig.tight_layout()
fig.savefig(OUT / '10_categories.png', dpi=150, bbox_inches='tight', facecolor='white')
print('saved', OUT / '10_categories.png', '| categories:', ncat)
