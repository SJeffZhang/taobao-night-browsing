"""Build the Chinese mid-term deck (v2) in the CityU-style visual language:
maroon + charcoal, serif headings, pill section tabs, rounded cards.

Run from inside src/:  <python> 13_build_slides_zh.py
Output: slides/night_browsing_midterm_zh.pptx
"""
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from PIL import Image

EXT = Path(__file__).resolve().parents[1]
FIG = EXT / 'figures'
OUT = EXT / 'slides'
OUT.mkdir(exist_ok=True)

# ---------------------------------------------------------------- palette / type
MAROON = RGBColor(0x7C, 0x3A, 0x47)
MAROON_MID = RGBColor(0xA8, 0x5D, 0x68)
PINK_FILL = RGBColor(0xF6, 0xED, 0xEF)
PINK_EDGE = RGBColor(0xE7, 0xDA, 0xDD)
PINK_SOFT = RGBColor(0xFB, 0xF7, 0xF8)
BAND = RGBColor(0xF2, 0xE0, 0xE4)
CHARCOAL = RGBColor(0x4A, 0x45, 0x45)
DARK = RGBColor(0x40, 0x37, 0x37)
GRAY = RGBColor(0x9A, 0x8F, 0x8F)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

HEAD_L, HEAD_E = 'Georgia', 'Songti SC'
BODY_L, BODY_E = 'Calibri', 'PingFang SC'

W, H = 13.333, 7.5
M = 0.55                     # page margin
CW = W - 2 * M               # content width
SECTIONS = ['研究问题', '数据', '方法', '结果', '结论']


# ---------------------------------------------------------------- primitives
def _apply_font(run, size, bold, color, head):
    lat, ea = (HEAD_L, HEAD_E) if head else (BODY_L, BODY_E)
    f = run.font
    f.size = Pt(size); f.bold = bold; f.color.rgb = color; f.name = lat
    rPr = run._r.get_or_add_rPr()
    for tag, face in (('a:ea', ea), ('a:cs', ea)):
        el = rPr.find(qn(tag))
        if el is None:
            el = rPr.makeelement(qn(tag), {})
            rPr.append(el)
        el.set('typeface', face)


def tb(s, x, y, w, h, lines, size=15, color=CHARCOAL, bold=False, head=False,
       align=PP_ALIGN.LEFT, spacing=1.3, gap=6, anchor=MSO_ANCHOR.TOP):
    box = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Emu(0)
    for i, item in enumerate(lines):
        txt, o = (item, {}) if isinstance(item, str) else item
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = o.get('align', align)
        p.line_spacing = o.get('spacing', spacing)
        p.space_after = Pt(o.get('gap', gap))
        if o.get('bullet'):
            _diamond(p)
        else:
            p.space_before = Pt(o.get('before', 0))
        r = p.add_run(); r.text = txt
        _apply_font(r, o.get('size', size), o.get('bold', bold), o.get('color', color), o.get('head', head))
    return box


def _diamond(p):
    pPr = p._p.get_or_add_pPr()
    pPr.set('marL', str(int(Inches(0.30))))
    pPr.set('indent', str(int(-Inches(0.30))))
    for tag in ('a:buClr', 'a:buSzPct', 'a:buFont', 'a:buChar'):
        el = pPr.makeelement(qn(tag), {})
        if tag == 'a:buClr':
            el.append(el.makeelement(qn('a:srgbClr'), {'val': '7C3A47'}))
        elif tag == 'a:buSzPct':
            el.set('val', '85000')
        elif tag == 'a:buFont':
            el.set('typeface', 'Arial')
        else:
            el.set('char', '◆')
        pPr.append(el)


def rect(s, x, y, w, h, fill=None, line=None, radius=None, lw=0.75):
    shp = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE,
                             Inches(x), Inches(y), Inches(w), Inches(h))
    if radius:
        shp.adjustments[0] = radius
    if fill is None:
        shp.fill.background()
    else:
        shp.fill.solid(); shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line; shp.line.width = Pt(lw)
    shp.shadow.inherit = False
    for el in shp._element.findall(qn('p:style')):
        shp._element.remove(el)
    return shp


def pill(s, x, y, w, h, text, active=False, size=10.5):
    shp = rect(s, x, y, w, h, fill=WHITE, line=MAROON if active else PINK_EDGE,
               radius=0.5, lw=1.0 if active else 0.75)
    tf = shp.text_frame
    tf.word_wrap = False
    tf.margin_left = tf.margin_right = Emu(0)
    tf.margin_top = tf.margin_bottom = Emu(0)
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = text
    _apply_font(r, size, active, MAROON if active else GRAY, False)
    return shp


def header(s, active=None):
    tb(s, M, 0.12, 1.1, 0.3, [('IS5312', {'head': True, 'bold': True, 'color': MAROON, 'size': 17})],
       spacing=1.0, gap=0)
    rect(s, 1.72, 0.16, 0.012, 0.26, fill=PINK_EDGE)
    tb(s, 1.84, 0.17, 2.9, 0.26, [('Analytical Programming with Python', {'size': 9.5, 'color': GRAY})],
       spacing=1.0, gap=0)
    tw, gap = 1.70, 0.06
    x = W - M - (5 * tw + 4 * gap)
    for i, name in enumerate(SECTIONS):
        pill(s, x + i * (tw + gap), 0.13, tw, 0.30, name, active=(i == active))


def h1(s, text, size=26):
    tb(s, M, 0.74, CW, 0.62, [(text, {'head': True, 'bold': True, 'color': DARK, 'size': size})],
       spacing=1.05, gap=0)
    rect(s, M, 1.44, 1.15, 0.065, fill=MAROON)


def footer(s, idx):
    tb(s, 0, 7.16, W, 0.24,
       [('IS5312 Analytical Programming with Python  ·  中期汇报', {'size': 9, 'color': GRAY, 'align': PP_ALIGN.CENTER})],
       spacing=1.0, gap=0)
    tb(s, W - M - 0.7, 7.16, 0.7, 0.24,
       [(str(idx), {'size': 9, 'color': GRAY, 'align': PP_ALIGN.RIGHT})], spacing=1.0, gap=0)


def notes(s, text):
    s.notes_slide.notes_text_frame.text = text


def figure_card(s, name, x, y, w, h, pad=0.12):
    rect(s, x, y, w, h, fill=WHITE, line=PINK_EDGE, radius=0.05, lw=0.9)
    p = FIG / f'{name}.png'
    iw, ih = Image.open(p).size
    sc = min((w - 2 * pad) / iw, (h - 2 * pad) / ih)
    iw2, ih2 = iw * sc, ih * sc
    s.shapes.add_picture(str(p), Inches(x + (w - iw2) / 2), Inches(y + (h - ih2) / 2),
                         Inches(iw2), Inches(ih2))


def _cell_border(cell, color='E7DADD', w=9525):
    tcPr = cell._tc.get_or_add_tcPr()
    for tag in ('a:lnL', 'a:lnR', 'a:lnT', 'a:lnB'):
        el = tcPr.find(qn(tag))
        if el is not None:
            tcPr.remove(el)
    for tag in ('a:lnB', 'a:lnT', 'a:lnR', 'a:lnL'):
        ln = tcPr.makeelement(qn(tag), {'w': str(w), 'cap': 'flat', 'cmpd': 'sng', 'algn': 'ctr'})
        fill = ln.makeelement(qn('a:solidFill'), {})
        fill.append(fill.makeelement(qn('a:srgbClr'), {'val': color}))
        ln.append(fill)
        tcPr.insert(0, ln)


def table(s, rows, x, y, w, col_ratio, header_h=0.44, row_h=0.66, size=11.5):
    nr, nc = len(rows), len(rows[0])
    heights = [header_h] + [row_h] * (nr - 1)
    gf = s.shapes.add_table(nr, nc, Inches(x), Inches(y), Inches(w), Inches(sum(heights)))
    t = gf.table
    tblPr = t._tbl.tblPr
    for el in tblPr.findall(qn('a:tableStyleId')):
        tblPr.remove(el)
    for i, r in enumerate(col_ratio):
        t.columns[i].width = Inches(w * r)
    for i, hh in enumerate(heights):
        t.rows[i].height = Inches(hh)
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            c = t.cell(ri, ci)
            c.fill.solid()
            c.fill.fore_color.rgb = MAROON if ri == 0 else (WHITE if ri % 2 else PINK_SOFT)
            c.margin_left = Inches(0.12); c.margin_right = Inches(0.08)
            c.margin_top = c.margin_bottom = Inches(0.03)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = c.text_frame; tf.word_wrap = True
            p = tf.paragraphs[0]; p.line_spacing = 1.05
            r = p.add_run(); r.text = val
            _apply_font(r, size, ri == 0 or ci == 0,
                        WHITE if ri == 0 else (MAROON if ci == 0 else CHARCOAL), False)
            _cell_border(c)
    return t


prs = Presentation()
prs.slide_width = Inches(W)
prs.slide_height = Inches(H)
prs.core_properties.title = '深夜刷淘宝，真的更容易下单吗？—— 中期汇报'
prs.core_properties.author = 'IS5312 小组'

TOTAL = 19
blank = lambda: prs.slides.add_slide(prs.slide_layouts[6])

# ------------------------------------------------------------------ 1 cover
s = blank()
rect(s, 0, 0, W, 0.10, fill=MAROON)
tb(s, M, 0.30, 6.0, 0.3, [('IS5312  Analytical Programming with Python', {'size': 11.5, 'color': GRAY})],
   spacing=1.0, gap=0)
tb(s, W - M - 3.2, 0.30, 3.2, 0.3,
   [('中期汇报  ·  2026 年 10 月 23 日', {'size': 11.5, 'color': GRAY, 'align': PP_ALIGN.RIGHT})],
   spacing=1.0, gap=0)
rect(s, 0, 2.55, W, 2.30, fill=BAND)
rect(s, 0, 2.55, 0.22, 2.30, fill=MAROON)
tb(s, 0.95, 2.78, 11.4, 1.40,
   [('深夜刷淘宝，', {'head': True, 'bold': True, 'color': MAROON, 'size': 42, 'spacing': 1.0}),
    ('真的更容易下单吗？', {'head': True, 'bold': True, 'color': MAROON, 'size': 42, 'spacing': 1.0})],
   spacing=1.0, gap=2)
tb(s, 0.97, 4.28, 11.2, 0.36,
   [('用 1 亿条真实浏览记录，检验一个大家都相信的直觉', {'size': 16, 'color': DARK})], spacing=1.0, gap=0)
tb(s, 0.97, 5.30, 11.6, 0.9,
   [('数据来源：天池 649（淘宝 UserBehavior）公开镜像', {'size': 12.5, 'color': CHARCOAL}),
    ('1.00 亿条行为事件  ·  9 天（2017-11-25 至 12-03）  ·  983,132 名用户', {'size': 12.5, 'color': GRAY})],
   spacing=1.25, gap=3)
rect(s, 0, 7.30, W, 0.10, fill=MAROON)
notes(s, '开场：先抛直觉——深夜更容易冲动消费。然后用 1 亿条记录来检验它。')

# ------------------------------------------------------------------ 2 agenda
s = blank(); header(s)
h1(s, '这次汇报讲什么')
items = [('01', '我们要回答什么', '深夜刷手机，真的会让人冲动下单吗？'),
         ('02', '数据长什么样', '1 亿条浏览与购买记录，9 天，98 万用户'),
         ('03', '怎么比才公平', '固定同一个人、同一个商品，只看时间差别'),
         ('04', '结果是什么', '4 张图看懂：为什么深夜反而买得少'),
         ('05', '钱该怎么花', '按时段调整投放，长尾商品要特殊照顾')]
y = 1.72
for i, (num, head, sub) in enumerate(items):
    rect(s, M, y, CW, 0.92, fill=PINK_FILL if i % 2 == 0 else WHITE, line=PINK_EDGE, radius=0.08)
    tb(s, M + 0.28, y + 0.20, 0.9, 0.5, [(num, {'head': True, 'bold': True, 'color': MAROON, 'size': 24})],
       spacing=1.0, gap=0)
    tb(s, M + 1.20, y + 0.14, 5.0, 0.36, [(head, {'head': True, 'bold': True, 'color': DARK, 'size': 15})],
       spacing=1.0, gap=0)
    tb(s, M + 1.20, y + 0.52, 10.4, 0.30, [(sub, {'size': 11.5, 'color': GRAY})], spacing=1.0, gap=0)
    y += 1.02
footer(s, 2)
notes(s, '五个部分：问题、数据、方法、结果、结论。')

# ------------------------------------------------------------------ 3 question
s = blank(); header(s, 0)
h1(s, '大家都有一个直觉：深夜更容易"手滑"')
cards = [('深夜', '自控力变弱', '很多人相信：越晚越容易冲动下单'),
         ('但凭直觉', '不一定可靠', '记住的，往往只是少数几次'),
         ('所以我们用', '真实记录来查', '1 亿条浏览与下单，不做问卷'),
         ('结果可能', '和直觉相反', '夜里看商品的人，反而买得更少')]
cw, gap = 2.82, 0.30
for i, (lead, strong, sub) in enumerate(cards):
    x = M + i * (cw + gap)
    rect(s, x, 1.78, cw, 1.72, fill=MAROON if i < 3 else MAROON_MID, radius=0.08)
    tb(s, x + 0.22, 1.94, cw - 0.44, 0.26, [(lead, {'size': 10.5, 'color': BAND})], spacing=1.0, gap=0)
    tb(s, x + 0.22, 2.20, cw - 0.44, 0.40, [(strong, {'head': True, 'bold': True, 'color': WHITE, 'size': 16})],
       spacing=1.05, gap=0)
    tb(s, x + 0.22, 2.70, cw - 0.44, 0.66, [(sub, {'size': 10.5, 'color': BAND})], spacing=1.15, gap=0)
    if i < 3:
        ar = s.shapes.add_shape(MSO_SHAPE.CHEVRON, Inches(x + cw + 0.05), Inches(2.52),
                                Inches(0.20), Inches(0.26))
        ar.fill.solid(); ar.fill.fore_color.rgb = RGBColor(0xD8, 0xA7, 0xAF)
        ar.line.fill.background(); ar.shadow.inherit = False
        for el in ar._element.findall(qn('p:style')):
            ar._element.remove(el)
tb(s, M, 3.72, CW, 2.1, [
    ('为什么这事值得花时间？', {'head': True, 'bold': True, 'color': MAROON, 'size': 14, 'gap': 8}),
    ('如果"深夜更容易冲动"成立，夜间流量就该卖得更贵；如果不成立，按时段投放的钱就花错了地方。',
     {'bullet': True, 'size': 15}),
    ('这不是"感觉"问题，而是可以用数据直接回答的问题：同一个商品，白天看和深夜看，买的比例差多少？',
     {'bullet': True, 'size': 15}),
], spacing=1.35)
rect(s, M, 5.98, CW, 0.80, fill=PINK_FILL, line=PINK_EDGE, radius=0.10)
tb(s, M + 0.30, 6.15, CW - 0.6, 0.45,
   [('先记住结论：夜里看商品的人，买的比例明显更低——不管怎么比。', {'size': 14, 'bold': True, 'color': MAROON})],
   spacing=1.0, gap=0)
footer(s, 3)
notes(s, '用四张卡片走一遍推理链，再说明为什么值得研究。')

# ------------------------------------------------------------------ 4 data
s = blank(); header(s, 1)
h1(s, '数据：9 天里发生的 1 亿次"看"和"买"')
kpis = [('1.00 亿', '条行为记录', '浏览 / 收藏 / 加购 / 下单，用户点了什么就记什么'),
        ('5,131 万', '次"第一次看到"', '分析单位：某人第一次看到某商品'),
        ('9 天', '观察窗口', '2017-11-25 至 12-03，上海时间')]
y = 1.70
for big, mid, sub in kpis:
    rect(s, M, y, 4.35, 1.28, fill=PINK_FILL, line=PINK_EDGE, radius=0.08)
    tb(s, M + 0.26, y + 0.14, 3.9, 0.50, [(big, {'head': True, 'bold': True, 'color': MAROON, 'size': 26})],
       spacing=1.0, gap=0)
    tb(s, M + 0.26, y + 0.62, 3.9, 0.26, [(mid, {'size': 11, 'bold': True, 'color': DARK})], spacing=1.0, gap=0)
    tb(s, M + 0.26, y + 0.86, 3.9, 0.30, [(sub, {'size': 9.5, 'color': GRAY})], spacing=1.05, gap=0)
    y += 1.40
rect(s, 5.15, 1.70, 7.63, 4.10, fill=WHITE, line=PINK_EDGE, radius=0.05)
tb(s, 5.45, 1.90, 7.0, 0.40, [('我们怎么定义"一个样本"？', {'head': True, 'bold': True, 'color': MAROON, 'size': 14})],
   spacing=1.0, gap=0)
tb(s, 5.45, 2.36, 7.0, 3.2, [
    ('某人在某一刻第一次看到某个商品 —— 记下这个时刻，叫它 t0。', {'bullet': True, 'size': 13.5}),
    ('然后看：t0 之后 1 小时内，他有没有买这个商品？24 小时内呢？', {'bullet': True, 'size': 13.5}),
    ('只用 t0 之前的信息，避免"买了之后又看"造成的假象。', {'bullet': True, 'size': 13.5}),
    ('结果只有两种：买了 / 没买。全样本里，1 小时内买的约 0.65%，24 小时内约 0.98%。', {'bullet': True, 'size': 13.5}),
], spacing=1.45)
rect(s, 5.15, 5.95, 7.63, 0.78, fill=PINK_FILL, line=PINK_EDGE, radius=0.08)
tb(s, 5.42, 6.10, 7.1, 0.5,
   [('数据里没有价格、金额和停留时长 —— 所以我们只说"买没买"，不猜"花了多少"。', {'size': 12})],
   spacing=1.1, gap=0)
footer(s, 4)
notes(s, '三个数字 + 一个定义，把"样本"讲清楚。')

# ------------------------------------------------------------------ 5 fair comparison
s = blank(); header(s, 1)
h1(s, '直接比不公平，我们换了一种比法')
rect(s, M, 1.72, 5.75, 3.55, fill=PINK_SOFT, line=PINK_EDGE, radius=0.05)
rect(s, 6.95, 1.72, 5.83, 3.55, fill=WHITE, line=MAROON, radius=0.05, lw=1.2)
tb(s, M + 0.30, 1.92, 5.1, 0.34, [('✕  直接比：深夜的人 vs 白天的人', {'head': True, 'bold': True, 'color': GRAY, 'size': 14})],
   spacing=1.0, gap=0)
tb(s, M + 0.30, 2.36, 5.15, 2.6, [
    ('问题：深夜还在逛的人，和白天逛的人，本来就可能不是同一批人', {'bullet': True, 'size': 13}),
    ('有人本来就爱买、有人只看不买，直接比会把"人"的差别算成"时间"的差别', {'bullet': True, 'size': 13}),
    ('就像：拿爱运动的人和不爱运动的人比，说明不了运动有没有用', {'bullet': True, 'size': 13}),
], spacing=1.35)
tb(s, 7.25, 1.92, 5.2, 0.34, [('✓  我们的比法：同一个人、同一个商品', {'head': True, 'bold': True, 'color': MAROON, 'size': 14})],
   spacing=1.0, gap=0)
tb(s, 7.25, 2.36, 5.2, 2.6, [
    ('只比"同一个人在白天看到商品 A"和"同一个人在深夜看到商品 A"', {'bullet': True, 'size': 13}),
    ('人和商品的差别都被固定住，剩下的差异才更像是"时间点"造成的', {'bullet': True, 'size': 13}),
    ('另外固定"哪一天"——避免某天做活动带来的干扰', {'bullet': True, 'size': 13}),
], spacing=1.35)
tb(s, 6.20, 3.30, 0.55, 0.4, [('vs', {'head': True, 'bold': True, 'color': MAROON, 'size': 18, 'align': PP_ALIGN.CENTER})],
   spacing=1.0, gap=0)
rect(s, M, 5.55, CW, 1.05, fill=MAROON, radius=0.06)
tb(s, M + 0.32, 5.72, CW - 0.64, 0.72,
   [('一句话：比的是"同一个人前后两次看同一商品"，而不是"两拨人"。', {'size': 15, 'bold': True, 'color': WHITE})],
   spacing=1.15, gap=0)
footer(s, 5)
notes(s, '这一页是全场最关键的"方法论"页：为什么不是简单比较。')

# ------------------------------------------------------------------ 6 methods
s = blank(); header(s, 2)
h1(s, '三个模型，从三个角度回答同一个问题')
ms = [('①', '先把人固定住再比', '固定效应模型',
       '把"谁在看、看什么、哪一天"都固定住，只留时间这一个变量在动。'),
      ('②', '再看"多久才买"', '生存分析',
       '不只看"买没买"，还看"多久买"——把"根本没买"和"晚点买"分开。'),
      ('③', '最后看"谁受影响大"', '因果森林',
       '让模型自己去找：哪类商品、哪类人，深夜掉得最狠。')]
ANSWERS = ['回答：同一商品，同一个人白天看 vs 深夜看，买的概率差多少？',
           '回答：买得少，是"根本没买"，还是"晚一点才买"？',
           '回答：哪类商品、哪类人，在深夜掉得最厉害？']
cw2, gap2 = 3.95, 0.30
for i, (num, title, en, body) in enumerate(ms):
    x = M + i * (cw2 + gap2)
    rect(s, x, 1.75, cw2, 2.85, fill=PINK_FILL if i != 1 else WHITE, line=PINK_EDGE, radius=0.06)
    tb(s, x + 0.28, 1.92, 0.8, 0.5, [(num, {'head': True, 'bold': True, 'color': MAROON, 'size': 26})],
       spacing=1.0, gap=0)
    tb(s, x + 0.28, 2.48, cw2 - 0.56, 0.40, [(title, {'head': True, 'bold': True, 'color': DARK, 'size': 15})],
       spacing=1.05, gap=0)
    tb(s, x + 0.28, 2.90, cw2 - 0.56, 0.24, [(en, {'size': 10, 'color': MAROON})], spacing=1.0, gap=0)
    tb(s, x + 0.28, 3.18, cw2 - 0.56, 0.9, [(body, {'size': 12})], spacing=1.35, gap=0)
    tb(s, x + 0.28, 4.08, cw2 - 0.56, 0.45, [(ANSWERS[i], {'size': 10.5, 'color': MAROON})], spacing=1.2, gap=0)
rect(s, M, 4.62, CW, 0.95, fill=WHITE, line=PINK_EDGE, radius=0.05)
tb(s, M + 0.30, 4.74, CW - 0.6, 0.75, [
    ('为什么要用三个模型？', {'head': True, 'bold': True, 'color': MAROON, 'size': 12.5, 'gap': 3}),
    ('三个方法各自独立；如果它们给出同一个答案，我们就更有信心这不是某一方法的"错觉"。', {'size': 12}),
], spacing=1.15)
for i, (lab, txt) in enumerate([('阶段二 A', '按小时拆开 × 三个购买窗口（1h / 3h / 24h），看一天内更细的形状'),
                                ('阶段二 B', '按商品热度分层，验证"冷门商品白天看了就买、深夜跌得最狠"')]):
    cx = M + i * (CW / 2 + 0.08)
    rect(s, cx, 5.75, CW / 2 - 0.08, 0.95, fill=PINK_FILL, line=PINK_EDGE, radius=0.08)
    tb(s, cx + 0.24, 5.86, CW / 2 - 0.56, 0.24, [(lab, {'size': 10.5, 'bold': True, 'color': MAROON})], spacing=1.0, gap=0)
    tb(s, cx + 0.24, 6.10, CW / 2 - 0.56, 0.5, [(txt, {'size': 11})], spacing=1.2, gap=0)
footer(s, 6)
notes(s, '三种方法互相验证，是这份报告可信度的来源。')

# ------------------------------------------------------------------ 7 overview table
s = blank(); header(s, 3)
h1(s, '结果总览：五句话记住全部结论')
rows = [('方法与模型', '结果（直白版）', '一句话'),
        ('固定效应 LPM · M2 主模型', '深夜比白天少 0.18（1 小时）/ 0.31（24 小时）个百分点', '夜里买得更少'),
        ('固定效应 LPM · 7 项稳健性', '方向全部一样，没有一个翻过来', '不是"调"出来的'),
        ('Cox 生存模型 · 分段', '深夜＝不买；凌晨＝晚点买', '两种不同的"少"'),
        ('Causal Forest（DML）', '冷门商品、老用户掉得最多', '按比例其实差不多'),
        ('Cox 生存模型 · 按小时', '睡前最差，上午 9–11 最好', '深夜不是一个整体')]
table(s, rows, M, 1.68, CW, [0.27, 0.44, 0.29], header_h=0.44, row_h=0.64, size=11)
tb(s, M, 5.56, CW, 0.5, [
    ('注：0.18 个百分点 ≈ 每 1,000 次浏览少买约 2 单。全部为观察性关联，不是随机实验。',
     {'size': 10.5, 'color': GRAY}),
], spacing=1.1, gap=0)
rect(s, M, 6.05, CW, 0.80, fill=PINK_FILL, line=PINK_EDGE, radius=0.10)
tb(s, M + 0.30, 6.22, CW - 0.6, 0.45,
   [('如果只记一句话：深夜的流量更"闲"，不是更"冲"。', {'size': 14.5, 'bold': True, 'color': MAROON})],
   spacing=1.0, gap=0)
footer(s, 7)
notes(s, '先给全景表，后面逐张图展开。')

# ------------------------------------------------------------------ figures 8-15
def chart_slide(idx, title, fig, bullets, note, pill_text, method_text):
    s = blank(); header(s, 3)
    h1(s, title)
    pw = 3.45
    px = W - M - pw
    pillbox = rect(s, px, 0.82, pw, 0.34, fill=WHITE, line=MAROON, radius=0.5, lw=0.9)
    tf = pillbox.text_frame
    tf.word_wrap = False
    tf.margin_left = tf.margin_right = Emu(0)
    tf.margin_top = tf.margin_bottom = Emu(0)
    par = tf.paragraphs[0]; par.alignment = PP_ALIGN.CENTER
    r = par.add_run(); r.text = pill_text
    _apply_font(r, 9, True, MAROON, False)
    figure_card(s, fig, M, 1.60, CW, 4.20)
    tb(s, M, 5.94, CW, 0.95, [(b, {'bullet': True, 'size': 13}) for b in bullets], spacing=1.3, gap=5)
    tb(s, M, 6.84, CW, 0.26, [(method_text, {'size': 9.5, 'color': GRAY})], spacing=1.0, gap=0)
    footer(s, idx)
    notes(s, note)
    return s

chart_slide(8, '第一张图：原始数据里，夜里就是买得少', '01_hourly_shape', [
    '白天（9–17 点）看商品，1 小时内约 0.77% 会下单；深夜（22–1 点）0.56%，凌晨（2–5 点）0.47%',
    '看图方法：横轴是一天中的小时，纵轴是"看完 1 小时内买的比例"；但这只是原始差异，下一张做公平比较',
], '左图原始转化率，右图控制后的系数；这里只讲左图。',
    '描述统计 + 固定效应 LPM（M2）',
    '方法：左图是原始转化率（无模型）；右图是固定效应线性概率模型 M2（用户 + 商品 + 日期固定效应，参照 14 时）。结果：results/hour_shape_M2.csv')

chart_slide(9, '第二张图：公平比较后，深夜仍然买得少', '02_bin_comparison', [
    '同一个人、同一个商品：深夜 1 小时内少 0.18 个百分点（每 1,000 次浏览少约 2 单）；24 小时少 0.31 个百分点',
    '凌晨更明显：少 0.24 个百分点，约等于少了 3 成；这不是运气，p 值小到小数点后十几个 0',
], '主结果页，强调"同人同商品"后差距仍在。',
    '固定效应 LPM（M2 主模型）',
    '方法：线性概率模型；用户 + 商品 + 日期固定效应 + 4 个控制变量；用户×商品双向聚类标准误；4 个主检验 Holm 校正。结果：results/primary_tests.csv')

chart_slide(10, '第三张图：换 7 种算法重算，结论一模一样', '03_robustness', [
    '去掉控制变量、换时间窗口、剔除重度用户、换另一批人复现…… 7 种做法全部还是"深夜买得少"',
    '每条横线都落在 0 的左边，说明结论不是靠某一种设定"调"出来的',
], '稳健性：给结论加保险。',
    '固定效应 LPM（7 项稳健性）',
    '方法：同一个 M2 主模型换 7 种设定重算（去控制、换窗口、换聚类、72h 洗出、剔除前 1% 重度用户、独立复现）。结果：results/robustness.csv')

chart_slide(11, '第四张图：深夜是"不买"，凌晨只是"晚点买"', '05_cox_piecewise_hr', [
    '深夜：1 小时内少买，过了 1 小时仍然更少买 —— 是真的没买，不是买得慢',
    '凌晨：1 小时内少买，但 1 小时后和白天一样 —— 只是把购买推到了睡醒之后',
], '这一页把"少买"拆成两种机制。',
    'Cox 生存模型（分段）',
    '方法：Cox 比例风险 + 分段 Cox（0–1h、1–24h）；自写 FastCox（Breslow 结点，用户聚类 Lin-Wei 标准误）。结果：results/survival_models_full.csv')

# ------------------------------------------------------------------ 12 fig04 (side layout)
s = blank(); header(s, 3)
h1(s, '第五张图：深夜少掉的单，第二天也没补回来')
pillbox = rect(s, W - M - 3.45, 0.82, 3.45, 0.34, fill=WHITE, line=MAROON, radius=0.5, lw=0.9)
tf = pillbox.text_frame; tf.word_wrap = False
tf.margin_left = tf.margin_right = Emu(0); tf.margin_top = tf.margin_bottom = Emu(0)
par = tf.paragraphs[0]; par.alignment = PP_ALIGN.CENTER
r = par.add_run(); r.text = '描述统计（无模型）'
_apply_font(r, 9, True, MAROON, False)
figure_card(s, '04_cumulative_purchase_by_bin', M, 1.60, 7.35, 4.20)
tb(s, 8.20, 1.78, 4.58, 4.0, [
    ('看曲线：横轴是"看了之后过了几小时"，纵轴是累计买的比例', {'bullet': True, 'size': 12.5}),
    ('24 小时累计：白天 1.16%，深夜只有 0.80% —— 差距一直没追上', {'bullet': True, 'size': 12.5}),
    ('深夜 1–6 小时曲线几乎是平的 —— 这段时间大家在睡觉', {'bullet': True, 'size': 12.5}),
    ('凌晨的曲线在 6 点之后明显往上走，和"晚点买"对得上', {'bullet': True, 'size': 12.5}),
], spacing=1.35, gap=8)
tb(s, M, 6.02, 7.35, 0.5, [('方法：不做模型，直接统计每段时间后 10 分钟 / 1 / 3 / 6 / 12 / 24 小时的累计购买率。结果：results/survival_cumulative_by_bin_full.csv',
                            {'size': 9, 'color': GRAY})], spacing=1.1, gap=0)
footer(s, 12)
notes(s, '累计曲线把"睡觉"和"追回"分开看。')

chart_slide(13, '第六张图：谁受影响最大？冷门商品和老用户', '06_causal_forest_gates', [
    '独立再算一遍，平均效应还是 −0.18 个百分点，和前面两张图完全对得上',
    '冷门商品（商品热度低 = t0 前 24h 被浏览得少）、老用户绝对损失最大；但按比例都是少 17%–26%',
    '把品类加进模型重跑：15 个品类哑变量重要性合计 ≈ 0.0001，商品热度仍是第一（0.54）——品类不是主要因素',
], '异质性：不是某一类人特殊，而是"转化高的地方绝对损失大"。',
    'Causal Forest（DML）',
    '方法：econml CausalForestDML，1,000 棵树、honest 分裂、按用户分组交叉拟合；报告样本外 ATE / BLP / GATES。结果：results/causal_forest_full.json')

chart_slide(14, '第七张图：按小时拆开，睡前最差、上午最好', '07_survival_hourly', [
    '上午 9–11 点：1 小时 / 3 小时 / 24 小时三个窗口都最容易买；21–23 点三个窗口都最难买',
    '0–2 点：当场买得很少，但 24 小时内追了回来 —— "深夜"要拆成"睡前"和"午夜后"两段看',
], '阶段二 A：按小时 × 三个购买窗口。',
    'Cox 生存模型（按小时）',
    '方法：Cox，23 个小时哑变量（参照 14 时）× 三个购买窗口 1h / 3h / 24h，M2 含控制变量与日期。结果：results/survival_hourly_models_full.csv')

chart_slide(15, '第八张图：热门 ≠ 好卖，长尾商品最怕深夜', '08_cold_hot_items', [
    '白天 1 小时内：只被 1 人看过的冷门商品 1.10% 会买，最热门的商品只有 0.42%',
    '深夜掉的绝对数量：最冷门 −0.44 个百分点，最热门 −0.08；但按比例都是 −20% 上下',
], '阶段二 B：冷热门商品分层，验证一个反直觉的发现。',
    '描述统计 + 固定效应 LPM',
    '方法：面板 A 为原始转化率；面板 B 为每个热度档单独拟合 M2（用户 + 商品 + 日期固定效应）；面板 C 为 B 的系数 ÷ 白天均值。结果：results/cold_hot_items_*.csv')

chart_slide(16, '第九张图：按品类看，哪类商品都怕深夜', '11_category_night_penalty', [
    '前 20 个品类（其余 9,400 个归"其他"）各自重跑深夜 vs 白天：21 组 HR 全部 < 1，没有例外',
    '差别不大：最怕深夜的品类 HR 0.58、最不怕的 0.81，多数在 0.6–0.75',
    '三个窗口都 < 1；因果森林里 15 个品类哑变量重要性合计仅 0.0001——品类不是主因',
], '阶段二 A 扩展：按品类分层重跑生存分析。',
    'Cox 生存模型（按品类）',
    '方法：给 episode 关联 category_id，取事件量前 20 品类 + 其他，每组单独跑 Cox（深夜/凌晨 vs 白天，1h / 3h / 24h）。结果：results/category_survival_summary_full.csv')

# ------------------------------------------------------------------ 17 conclusions
s = blank(); header(s, 4)
h1(s, '所以，钱该怎么花？')
acts = [('21–23 点', '最该降权', '三个购买窗口都最差，第二天也补不回来'),
        ('0–2 点', '看次日转化', '当场不买、睡醒再买，别只用"即时下单"考核'),
        ('9–11 点', '可以加码', '三个窗口都最容易买，是全天转化黄金时段')]
cw3, gap3 = 3.95, 0.30
for i, (when, what, why) in enumerate(acts):
    x = M + i * (cw3 + gap3)
    rect(s, x, 1.75, cw3, 2.15, fill=WHITE, line=PINK_EDGE, radius=0.06)
    chip = rect(s, x + 0.28, 1.95, 1.05, 0.10, fill=MAROON, radius=0.5)
    tb(s, x + 0.28, 2.15, cw3 - 0.56, 0.42, [(when, {'head': True, 'bold': True, 'color': MAROON, 'size': 21})],
       spacing=1.0, gap=0)
    tb(s, x + 0.28, 2.60, cw3 - 0.56, 0.34, [(what, {'head': True, 'bold': True, 'color': DARK, 'size': 14})],
       spacing=1.0, gap=0)
    tb(s, x + 0.28, 2.98, cw3 - 0.56, 0.85, [(why, {'size': 11.5})], spacing=1.35, gap=0)
rect(s, M, 4.15, CW, 1.00, fill=PINK_FILL, line=PINK_EDGE, radius=0.06)
tb(s, M + 0.30, 4.28, CW - 0.6, 0.8, [
    ('还有两条商品层面的结论：', {'head': True, 'bold': True, 'color': MAROON, 'size': 12.5, 'gap': 3}),
    ('深夜保转化，优先照顾长尾冷门商品；热门商品的价值主要在曝光，不在成交。', {'size': 12.5}),
], spacing=1.15)
rect(s, M, 5.40, CW, 0.95, fill=MAROON, radius=0.06)
tb(s, M + 0.32, 5.58, CW - 0.64, 0.6,
   [('一句话：深夜的流量更"闲"，不是更"冲"。', {'size': 16, 'bold': True, 'color': WHITE})],
   spacing=1.0, gap=0)
footer(s, 17)
notes(s, '结论落到可执行的三件事，再给两条商品层面的结论。')

# ------------------------------------------------------------------ 18 limits
s = blank(); header(s, 4)
h1(s, '需要说明的局限，和下一步')
rect(s, M, 1.72, 5.75, 3.90, fill=PINK_SOFT, line=PINK_EDGE, radius=0.05)
tb(s, M + 0.30, 1.90, 5.15, 0.34, [('局限：这些结论不是"铁证"', {'head': True, 'bold': True, 'color': MAROON, 'size': 14})],
   spacing=1.0, gap=0)
tb(s, M + 0.30, 2.32, 5.15, 3.1, [
    ('观察数据，不是随机实验：只能说"深夜和不买相关"，不能说"深夜导致不买"', {'bullet': True, 'size': 12.5}),
    ('只有 9 天，看不到季节变化；也没有价格，无法排除深夜促销的影响', {'bullet': True, 'size': 12.5}),
    ('"第一次看到"不等于人生第一次看到，以前的浏览看不到', {'bullet': True, 'size': 12.5}),
], spacing=1.45, gap=8)
rect(s, 6.95, 1.72, 5.83, 3.90, fill=WHITE, line=MAROON, radius=0.05, lw=1.1)
tb(s, 7.25, 1.90, 5.2, 0.34, [('下一步：把它做成能用的东西', {'head': True, 'bold': True, 'color': MAROON, 'size': 14})],
   spacing=1.0, gap=0)
tb(s, 7.25, 2.32, 5.2, 3.1, [
    ('写最终报告，把方法、结果、验证记录整理成可复现的文档', {'bullet': True, 'size': 12.5}),
    ('（已完成）按品类拆解，看"哪类商品最怕深夜" —— 见第九张图', {'bullet': True, 'size': 12.5}),
    ('用价格代理变量（如品类均价）检验"促销"这个替代解释', {'bullet': True, 'size': 12.5}),
], spacing=1.45, gap=8)
tb(s, M, 5.85, CW, 0.5, [('所有代码、结果表和验证记录都在项目目录里，可随时复算。', {'size': 11, 'color': GRAY})],
   spacing=1.1, gap=0)
footer(s, 18)
notes(s, '主动讲局限，比被问出来好。')

# ------------------------------------------------------------------ 19 Q&A
s = blank()
rect(s, 0, 0, W, 0.10, fill=MAROON)
rect(s, 0, 7.40, W, 0.10, fill=MAROON)
tb(s, 0, 2.75, W, 1.10, [('Q & A', {'head': True, 'bold': True, 'color': DARK, 'size': 54, 'align': PP_ALIGN.CENTER})],
   spacing=1.0, gap=0)
rect(s, (W - 1.6) / 2, 3.95, 1.6, 0.06, fill=MAROON)
tb(s, 0, 4.25, W, 0.40, [('谢谢  ——  IS5312 小组', {'size': 17, 'color': MAROON, 'align': PP_ALIGN.CENTER})],
   spacing=1.0, gap=0)
tb(s, 0, 4.85, W, 0.35,
   [('IS5312 Analytical Programming with Python  |  Semester A 2026/27',
     {'size': 11.5, 'color': GRAY, 'align': PP_ALIGN.CENTER})], spacing=1.0, gap=0)

prs.save(OUT / 'night_browsing_midterm_zh.pptx')
print('saved', OUT / 'night_browsing_midterm_zh.pptx', 'slides:', len(prs.slides))
