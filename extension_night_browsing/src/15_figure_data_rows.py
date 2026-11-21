"""Draw 'what one row of the data looks like' — raw events -> one episode row.

Uses a real user (77) and item (4834883) from the Taobao dataset.
Output: figures/09_data_rows.png
"""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.font_manager import FontProperties
import pandas as pd
import pyarrow.dataset as ds
from datetime import datetime, timezone, timedelta

EXT = Path(__file__).resolve().parents[1]
RAW = EXT.parent / 'data/processed/events_clean.parquet'
EP = EXT / 'data/episodes_hour.parquet'
OUT = EXT / 'figures'
SH = timezone(timedelta(hours=8))

CJK = FontProperties(fname='/Library/Fonts/Arial Unicode.ttf')

MAROON, MID, ROSE = '#7C3A47', '#A85D68', '#C98A95'
PALE, LINE, CHAR, GRAY = '#E7DADD', '#B9ABAE', '#4A4545', '#9A8F8F'
GREY_PT = '#B3A6AA'

USER, ITEM = 77, 4834883

ev = pd.read_parquet(RAW, columns=['row_no', 'user_id', 'item_id', 'category_id', 'behavior', 'ts'])
ev = ev[ev.user_id == USER].sort_values('ts').reset_index(drop=True)
ev['dt'] = [datetime.fromtimestamp(t, SH) for t in ev.ts]
B = {1: 'pv', 2: 'fav', 3: 'cart', 4: 'buy'}
STYLE = {'pv': (GREY_PT, 22, 'o'), 'fav': (ROSE, 55, 's'),
         'cart': (MID, 60, '^'), 'buy': (MAROON, 190, '*')}

ep = ds.dataset(EP).to_table(filter=(ds.field('user_id') == USER) & (ds.field('item_id') == ITEM)).to_pandas().iloc[0]

fig = plt.figure(figsize=(12.6, 8.9))

def _mk(ax):
    return lambda x, y, t, **kw: ax.text(x, y, t, transform=ax.transAxes, **kw)
fig.patch.set_facecolor('white')

# ---------------------------------------------------------------- ① raw rows
ax1 = fig.add_axes([0.05, 0.705, 0.92, 0.265]); ax1.axis('off')
t1 = _mk(ax1)
t1(0, 1.02, '① 原始数据：每一行 = 用户的一次操作', fontproperties=CJK, fontsize=15.5,
         color=MAROON, fontweight='bold', va='top')
t1(0, 0.845, '天池 649 · UserBehavior.csv　（100,095,182 行 × 5 列）', fontproperties=CJK,
         fontsize=9.5, color=GRAY, va='top')

lines = ['user_id,item_id,category_id,behavior_type,timestamp']
win = ev[(ev.ts >= 1512191700) & (ev.ts <= 1512192100)]
for r in win.itertuples():
    lines.append(f'{r.user_id},{r.item_id},{r.category_id},{B[r.behavior]},{r.ts}')
t1(0.0, 0.70, '\n'.join(lines), family='monospace', fontsize=10.5, va='top', color=CHAR,
         linespacing=1.75,
         bbox=dict(boxstyle='round,pad=0.6', facecolor='#FBF7F8', edgecolor=PALE))
t1(0.46, 0.70,
         'timestamp 是 Unix 秒：\n'
         '1512191890 → 2017-12-02 13:18:10\n\n'
         'behavior_type 只有 4 种：\n'
         'pv 浏览 / fav 收藏 / cart 加购 / buy 购买\n\n'
         '没有价格、金额、件数、停留时长',
         fontproperties=CJK, fontsize=10, color=CHAR, va='top', linespacing=1.75)

# ---------------------------------------------------------------- ② swim lanes
ax2 = fig.add_axes([0.05, 0.395, 0.92, 0.245])
lanes = {'buy': 0, 'cart': 1, 'fav': 2, 'pv': 3}
for r in ev.itertuples():
    c, s, m = STYLE[B[r.behavior]]
    ax2.scatter(r.dt, lanes[B[r.behavior]], s=s, marker=m, color=c, zorder=3,
                edgecolors='white', linewidths=0.7)
foc = ev[ev.item_id == ITEM]
ax2.scatter([d.to_pydatetime() for d in foc.dt], [lanes['buy']] + [lanes['pv']] * (len(foc) - 1),
            s=260, facecolors='none', edgecolors=MAROON, linewidths=1.4, zorder=4)
ax2.set_yticks(list(lanes.values()))
ax2.set_yticklabels(['购买 buy', '加购 cart', '收藏 fav', '浏览 pv'], fontproperties=CJK, fontsize=10)
ax2.set_ylim(-1.15, 3.6)
ax2.set_xlim(ev.dt.min() - pd.Timedelta(hours=8), ev.dt.max() + pd.Timedelta(hours=8))
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
ax2.xaxis.set_major_locator(mdates.DayLocator())
ax2.tick_params(axis='x', labelsize=9, colors=CHAR, length=3)
ax2.grid(axis='x', color='#F0E9EA', lw=0.6)
for sp in ('top', 'right', 'left'):
    ax2.spines[sp].set_visible(False)
ax2.spines['bottom'].set_color(LINE)
ax2.text(ev.dt.min(), -0.95,
         '◯ 圈出的是同一商品（item 4834883）：12-02 13:18 第一次浏览 → 13:20 下单，相隔 2 分 10 秒；在 9 天的尺度上，两个点几乎重合',
         fontproperties=CJK, fontsize=9.5, color=MAROON, ha='left', va='center')
ax2.set_title('② 同一个用户 9 天里的 20 次操作（泳道图）', fontproperties=CJK, fontsize=13.5,
              color=MAROON, fontweight='bold', loc='left', pad=12)

# ---------------------------------------------------------------- ③ one episode
ax3 = fig.add_axes([0.05, 0.035, 0.92, 0.30]); ax3.axis('off')
t3 = _mk(ax3)
t3(0, 1.02, '③ 建模时，这一对被压成 1 行（episode 表）', fontproperties=CJK, fontsize=15.5,
         color=MAROON, fontweight='bold', va='top')
fields = [('user_id', '77', '谁'), ('item_id', '4834883', '看了哪个商品'),
          ('t0', '13:18:10', '第一次看到的时刻'),
          ('hour', '13', 't0 是几点'), ('day', '7', 't0 是第几天'),
          ('buy_delay_s', '129', '多久之后买（秒）'),
          ('hist_pv24', '9', '此前 24h 他浏览过几件'),
          ('pop24', '71', '该商品此前 24h 被看了几次')]
t3(0.00, 0.86, '字段', fontproperties=CJK, fontsize=9, color=GRAY, va='top')
t3(0.155, 0.86, '值', fontproperties=CJK, fontsize=9, color=GRAY, va='top')
t3(0.275, 0.86, '含义', fontproperties=CJK, fontsize=9, color=GRAY, va='top')
for i, (f, v, m) in enumerate(fields):
    y = 0.745 - i * 0.093
    t3(0.00, y, f, family='monospace', fontsize=9.5, color=CHAR, va='top')
    t3(0.155, y, v, family='monospace', fontsize=9.5, color=MAROON, va='top')
    t3(0.275, y, m, fontproperties=CJK, fontsize=9.5, color=CHAR, va='top')
ax3.plot([0.575, 0.575], [0.05, 0.88], color=PALE, lw=1, transform=ax3.transAxes)
t3(0.60, 0.86, '结果变量由 buy_delay_s 直接算出来', fontproperties=CJK, fontsize=9.5,
         color=CHAR, va='top')
t3(0.60, 0.735, '1 小时内购买 = (0 ≤ 129 < 3600) → 1', fontproperties=CJK, fontsize=9.5,
         color=MAROON, va='top')
t3(0.60, 0.645, '24 小时内购买 = (0 ≤ 129 < 86400) → 1', fontproperties=CJK, fontsize=9.5,
         color=MAROON, va='top')
t3(0.60, 0.50, '如果 9 天里都没买：buy_delay_s = −1，', fontproperties=CJK, fontsize=9,
         color=GRAY, va='top')
t3(0.60, 0.425, '两个结果都记 0。', fontproperties=CJK, fontsize=9, color=GRAY, va='top')
t3(0.60, 0.28, '所以：1.00 亿行原始操作 → 5,131 万个 episode', fontproperties=CJK,
         fontsize=9.5, color=CHAR, va='top')

fig.savefig(OUT / '09_data_rows.png', dpi=150, bbox_inches='tight', facecolor='white')
print('saved', OUT / '09_data_rows.png')
