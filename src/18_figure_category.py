"""Figure 11: night penalty by category — ranked late-vs-day HR (24h window)."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np, pandas as pd
from matplotlib.font_manager import FontProperties
from fig_style import apply, MAROON, MAROON_MID, ROSE, PINK, GRAY, CHAR

apply()
CJK = FontProperties(fname='/Library/Fonts/Arial Unicode.ttf')
EXT = Path(__file__).resolve().parents[1]
RES = EXT / 'results'; OUT = EXT / 'figures'

s = pd.read_csv(RES / 'category_survival_summary_full.csv')
s = s.sort_values('late_HR_w24h').reset_index(drop=True)

fig, ax = plt.subplots(figsize=(12.2, 5.6))
labels = [('其他（9,400 个小品类）' if g == '其他' else str(g)) for g in s.label]
ypos = np.arange(len(s))[::-1]
colors = [PINK if g == '其他' else MAROON for g in s.label]
ax.barh(ypos, s.late_HR_w24h, height=.66, color=colors, zorder=3)
ax.errorbar(s.late_HR_w24h, ypos,
            xerr=[s.late_HR_w24h - s.late_HRlo_w24h, s.late_HRhi_w24h - s.late_HR_w24h],
            fmt='none', ecolor=CHAR, capsize=2, lw=.8, zorder=4)
for y, v in zip(ypos, s.late_HR_w24h):
    ax.text(v + .008, y, f'{v:.2f}', va='center', fontsize=7.5, color=CHAR)
ax.axvline(1.0, color='#4A4545', ls='--', lw=1.1)
ax.set_yticks(ypos)
ax.set_yticklabels(labels, fontsize=8.5, color=CHAR, fontproperties=CJK)
ax.set_xlim(0.40, 1.06)
ax.set_xlabel('late vs day hazard ratio（24h 窗口，HR < 1 = 深夜买得更少）',
              color=CHAR, fontsize=9, fontproperties=CJK)
ax.set_title('按品类看：21 组（前 20 品类 + 其他）的深夜购买风险比',
             fontproperties=CJK, fontsize=12, color=CHAR, pad=12)
ax.grid(axis='x')
ax.text(0.985, 0.35, 'HR = 1\n（与白天持平）', fontsize=7.5, color=GRAY,
        ha='right', va='bottom', fontproperties=CJK)

fig.tight_layout()
fig.savefig(OUT / '11_category_night_penalty.png', dpi=150, bbox_inches='tight', facecolor='white')
print('saved', OUT / '11_category_night_penalty.png')
