"""Build a self-contained Chinese HTML report (images embedded as base64).

Run from inside src/:  <python> 14_build_web.py
Output: web/analysis_zh.html
"""
import base64
from pathlib import Path

EXT = Path(__file__).resolve().parents[1]
FIG = EXT / 'figures'
OUT = EXT / 'web'
OUT.mkdir(exist_ok=True)


def img(name):
    b = (FIG / f'{name}.png').read_bytes()
    return 'data:image/png;base64,' + base64.b64encode(b).decode()


CSS = """
:root{
  --maroon:#7C3A47; --maroon2:#A85D68; --rose:#C98A95; --pink:#F6EDEF;
  --edge:#E7DADD; --soft:#FBF7F8; --band:#F2E0E4; --ink:#403737;
  --body:#4A4545; --gray:#9A8F8F;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:#fff;color:var(--body);
  font-family:"Calibri","PingFang SC","Helvetica Neue",system-ui,sans-serif;
  font-size:17px;line-height:1.8;-webkit-font-smoothing:antialiased}
h1,h2,h3,.serif{font-family:Georgia,"Songti SC","Times New Roman",serif;color:var(--ink)}
.wrap{max-width:1060px;margin:0 auto;padding:0 26px}
a{color:var(--maroon);text-decoration:none}
nav{position:sticky;top:0;z-index:50;background:rgba(255,255,255,.94);
  backdrop-filter:blur(8px)}
nav .wrap{display:flex;align-items:center;gap:18px;height:56px;max-width:1120px}
.brand{font-family:Georgia,"Songti SC",serif;font-weight:700;color:var(--maroon);font-size:18px;letter-spacing:.3px;white-space:nowrap}
.brand small{font-family:"Calibri","PingFang SC",sans-serif;font-weight:400;color:var(--gray);font-size:12px;margin-left:8px}
nav ul{display:flex;gap:4px;margin:0 0 0 auto;padding:0;list-style:none}
nav li a{display:block;padding:6px 12px;border-radius:999px;font-size:13px;color:var(--gray);
  border:1px solid transparent}
nav li a:hover{color:var(--maroon);border-color:var(--edge)}
nav li a.on{color:var(--maroon);border-color:var(--maroon);font-weight:600}
.hero{background:linear-gradient(180deg,var(--pink) 0%,#fff 78%);border-bottom:1px solid var(--edge)}
.hero .wrap{padding:86px 26px 64px}
.kicker{font-size:13px;letter-spacing:.18em;text-transform:uppercase;color:var(--maroon);font-weight:700}
.hero h1{font-size:clamp(34px,5.4vw,60px);line-height:1.16;margin:18px 0 16px;color:var(--maroon)}
.hero p.lead{font-size:19px;color:var(--body);max-width:760px;margin:0 0 26px}
.chips{display:flex;flex-wrap:wrap;gap:10px}
.chip{border:1px solid var(--edge);background:#fff;border-radius:999px;padding:7px 15px;font-size:13px;color:var(--body)}
.chip b{color:var(--maroon)}
section{padding:66px 0;border-bottom:1px solid var(--edge)}
section:last-of-type{border-bottom:none}
h2{font-size:clamp(24px,3.2vw,32px);margin:0 0 8px}
.rule{width:76px;height:5px;background:var(--maroon);border-radius:3px;margin:0 0 30px}
h3{font-size:19px;margin:0 0 6px}
p{margin:0 0 14px}
.muted{color:var(--gray);font-size:14px}
.grid{display:grid;gap:18px}
.g2{grid-template-columns:repeat(2,1fr)}
.g3{grid-template-columns:repeat(3,1fr)}
.g4{grid-template-columns:repeat(4,1fr)}
@media(max-width:860px){.g2,.g3,.g4{grid-template-columns:1fr}}
.card{background:var(--soft);border:1px solid var(--edge);border-radius:14px;padding:22px}
.card h3{color:var(--ink)}
.card p{margin:0;font-size:15px;line-height:1.75}
.card.maroon{background:var(--maroon);border-color:var(--maroon);color:#F7EDEF}
.card.maroon h3,.card.maroon .big{color:#fff}
.card.strong{background:#fff;border-color:var(--maroon);border-width:1.5px}
.big{font-family:Georgia,"Songti SC",serif;font-size:44px;line-height:1.1;color:var(--maroon);font-weight:700}
.stat{background:#fff;border:1px solid var(--edge);border-radius:14px;padding:20px}
.stat .n{font-family:Georgia,"Songti SC",serif;font-size:36px;color:var(--maroon);font-weight:700;line-height:1.1}
.stat .l{font-weight:700;color:var(--ink);font-size:15px;margin-top:4px}
.stat .s{color:var(--gray);font-size:13px;margin-top:2px}
.callout{background:var(--maroon);color:#fff;border-radius:16px;padding:26px 30px}
.callout b{color:#fff}
.callout .lab{font-size:12px;letter-spacing:.16em;text-transform:uppercase;color:var(--band)}
.tip{background:var(--pink);border:1px solid var(--edge);border-left:5px solid var(--maroon);
  border-radius:10px;padding:14px 18px;font-size:15px}
ul.clean{list-style:none;padding:0;margin:0}
ul.clean li{position:relative;padding-left:24px;margin:0 0 10px}
ul.clean li:before{content:"◆";position:absolute;left:0;top:0;color:var(--maroon);font-size:11px}
table{width:100%;border-collapse:collapse;font-size:15px;margin:6px 0 10px}
th{background:var(--maroon);color:#fff;text-align:left;padding:12px 14px;font-weight:600}
td{padding:12px 14px;border-bottom:1px solid var(--edge)}
tbody tr:nth-child(even){background:var(--soft)}
td:first-child{color:var(--maroon);font-weight:700}
figure{margin:0}
figure.zoom{border:1px solid var(--edge);border-radius:16px;padding:16px;background:#fff}
figure img{display:block;width:100%;height:auto;border-radius:6px;cursor:zoom-in}
figcaption{color:var(--gray);font-size:13px;margin-top:10px}
.fig{display:grid;gap:26px}
.fig .head{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}
.method{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:8px 0 0}
.badge{font-size:12px;font-weight:700;color:var(--maroon);border:1px solid var(--maroon);
  border-radius:999px;padding:3px 11px;white-space:nowrap;background:#fff}
.mtext{font-size:13px;color:var(--gray)}
.fig .num{font-family:Georgia,serif;font-size:15px;color:var(--maroon);font-weight:700;
  border:1px solid var(--maroon);border-radius:999px;padding:2px 11px}
.fig .txt{display:grid;gap:16px;grid-template-columns:1.55fr 1fr}
@media(max-width:900px){.fig .txt{grid-template-columns:1fr}}
.take{background:var(--pink);border-radius:12px;padding:18px 20px;font-size:15px}
.take b{color:var(--maroon)}
.two{display:grid;gap:18px;grid-template-columns:1fr 1fr}
@media(max-width:820px){.two{grid-template-columns:1fr}}
.bad{border:1px dashed #C9B9BD;background:#fff;border-radius:14px;padding:22px}
.good{border:1.5px solid var(--maroon);background:#fff;border-radius:14px;padding:22px}
.tag{display:inline-block;font-size:12px;font-weight:700;letter-spacing:.06em;
  padding:3px 10px;border-radius:999px;margin-bottom:10px}
.tag.no{background:#EFE9EA;color:var(--gray)}
.tag.yes{background:var(--pink);color:var(--maroon)}
footer{background:var(--maroon);color:#F4E6E9;padding:36px 0;font-size:13px}
footer .wrap{display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap}
#lightbox{position:fixed;inset:0;background:rgba(30,20,24,.92);display:none;
  align-items:center;justify-content:center;z-index:100;padding:30px}
#lightbox.on{display:flex}
#lightbox img{max-width:96vw;max-height:90vh;border-radius:8px;background:#fff}
@media(max-width:900px){
  nav ul{gap:0}
  nav li a{padding:6px 8px;font-size:12px}
}
@media(max-width:760px){
  nav ul{display:none}
  .brand small{display:none}
  nav .wrap{height:50px}
  body{font-size:16px}
  .hero .wrap{padding:54px 20px 42px}
  section{padding:46px 0}
  h2{font-size:23px}
  .big{font-size:34px}
  .stat .n{font-size:30px}
  table{font-size:13.5px}
  th,td{padding:9px 10px}
}
@media print{
  nav,#lightbox{display:none!important}
  section{page-break-inside:avoid;padding:26px 0}
  .hero{background:#fff}
  body{font-size:13px}
}
"""

BODY_CHECKS = [
    ("q", "问题", "1 · 问题"),
    ("data", "数据", "2 · 数据"),
    ("method", "方法", "3 · 方法"),
    ("result", "结果", "4 · 结果"),
    ("take", "结论", "5 · 结论"),
]

FIGS = [
    ("01", "第一张图", "原始数据里，夜里就是买得少", "01_hourly_shape",
     "左图：一天 24 小时里，看完商品 1 小时内下单的比例。右图：用模型控制住人和商品之后，每个小时相对下午 2 点的差距。",
     ["白天（9–17 点）约 <b>0.77%</b> 会下单，深夜（22–1 点）<b>0.56%</b>，凌晨（2–5 点）<b>0.47%</b>。",
      "拐点很清楚：早上 9–10 点最高，晚上 22–23 点最低。",
      "但这只是原始差异 —— 深夜逛的人可能本来就不爱买，所以要往下做公平比较。"],
     "描述统计 + 固定效应 LPM（M2）",
     "左图无模型（原始转化率）；右图 = 固定效应线性概率模型 M2：用户 FE + 商品 FE + 日期 FE，23 个小时哑变量（参照 14 时）。结果文件 results/hour_shape_M2.csv"),
    ("02", "第二张图", "公平比较后，差距仍然存在", "02_bin_comparison",
     "左：1 小时内购买；右：24 小时内购买。条形越长，说明比白天少得越多（单位：百分点）。",
     ["同一个商品、同一批人：深夜 1 小时内少 <b>0.18</b> 个百分点，24 小时少 <b>0.31</b> 个百分点。",
      "换成直白说法：每 1,000 次浏览，深夜大约少买 <b>2 单</b>（24 小时口径约少 3 单）。",
      "凌晨更明显：约少了 3 成。4 个主检验经过多重检验校正后，p 值仍然小到可以忽略。"],
     "固定效应 LPM（M2 主模型）",
     "线性概率模型：用户 + 商品 + 日期固定效应，4 个控制变量；用户×商品双向聚类标准误；4 个主检验 Holm 校正。结果文件 results/primary_tests.csv"),
    ("03", "第三张图", "换 7 种算法重算，结论一模一样", "03_robustness",
     "每一行是一种「换着法子重算」的设定，橙条是 24 小时结果、蓝条是 1 小时结果。所有横线都在 0 的左边。",
     ["去掉控制变量、换时间窗口、剔除前 1% 重度用户、换另一批人复现…… 7 种做法方向全部一致。",
      "这回答了一个常见的质疑：结论是不是「调参数调出来的」？不是。",
      "这条图在报告里叫「稳健性检验」，作用是给结论加保险。"],
     "固定效应 LPM（7 项稳健性）",
     "同一个 M2 主模型换 7 种设定重算：去控制、换窗口、换聚类、72h 洗出、剔除前 1% 重度用户、独立复现。结果文件 results/robustness.csv"),
    ("04", "第四张图", "深夜是「不买」，凌晨只是「晚点买」", "05_cox_piecewise_hr",
     "三条线分别是：0–24 小时的总体风险、只看前 1 小时、以及「熬过 1 小时之后」的 1–24 小时。",
     ["深夜：1 小时内少买，过了 1 小时<b>仍然</b>更少买 —— 是真的没买。",
      "凌晨：1 小时内少买，但 1 小时后和白天一样 —— 只是把购买推到了睡醒之后。",
      "这是整份报告最有意思的发现：同样是「买得少」，背后是两种完全不同的行为。"],
     "Cox 生存模型（分段）",
     "Cox 比例风险 + 分段 Cox（0–1h、1–24h）；自写 FastCox 实现（Breslow 结点、用户聚类 Lin-Wei 标准误），已对 statsmodels / lifelines 验证。结果文件 results/survival_models_full.csv"),
    ("05", "第五张图", "深夜少掉的单，第二天也没补回来", "04_cumulative_purchase_by_bin",
     "横轴：看了商品之后过了几小时；纵轴：累计有多少比例的人买了。曲线越平，说明那段时间几乎没人买。",
     ["24 小时累计：白天 <b>1.16%</b>，深夜只有 <b>0.80%</b> —— 差距一直没被追上。",
      "深夜 1–6 小时曲线几乎是平的：这段时间大家在睡觉。",
      "凌晨的曲线在 6 点之后明显往上走，和「晚点买」的说法对得上。"],
     "描述统计（无模型）",
     "不做模型，直接统计每个时段在看后 10 分钟 / 1 / 3 / 6 / 12 / 24 小时的累计购买率（测试集）。结果文件 results/survival_cumulative_by_bin_full.csv"),
    ("06", "第六张图", "谁受影响最大？冷门商品和老用户", "06_causal_forest_gates",
     "左：把样本按「预测受深夜影响的程度」分成 5 组，看每组的实际效应。右：预测效应的分布。",
     ["平均效应 <b>−0.18</b> 个百分点，和前面固定效应模型算出来的 <b>−0.179</b> 几乎完全一致 —— 两种方法互相印证。",
      "绝对损失最大的是冷门商品、以及研究期内已经买过东西的老用户。",
      "但按相对比例看，各类人都差不多（少 17%–26%），没有「某类人深夜反而更爱买」。",
      "把品类加进模型重跑，15 个品类哑变量的重要性合计只有 <b>0.0001</b>，商品热度仍是第一（0.54）—— 品类不是主要影响因素。",
      "补充：这里的「商品热度」是<b>算出来的</b>特征——该商品在 t0 前 24 小时内被所有用户浏览的次数（取对数），数据库里没有现成的热度字段。"],
     "Causal Forest（DML）",
     "econml CausalForestDML：1,000 棵树、honest 分裂、按用户分组交叉拟合；报告样本外 ATE、BLP 异质性检验、GATES 五分位。结果文件 results/causal_forest_full.json"),
    ("07", "第七张图", "按小时拆开：睡前最差，上午最好", "07_survival_hourly",
     "左：每个小时的购买风险（三条线对应 1 小时 / 3 小时 / 24 小时三个购买窗口）。右：每个小时的累计购买比例。",
     ["上午 9–11 点，三个窗口都最容易买 —— 一天中的转化黄金时段。",
      "21–23 点，三个窗口都最难买；23 点的 24 小时累计只有 <b>0.68%</b>，全天最低。",
      "0–2 点：当场买得很少，但 24 小时内追了回来 —— 深夜要拆成「睡前」和「午夜后」两段看。"],
     "Cox 生存模型（按小时）",
     "Cox：23 个小时哑变量（参照 14 时）× 三个购买窗口 1h / 3h / 24h，M2 含控制变量与日期。结果文件 results/survival_hourly_models_full.csv"),
    ("08", "第八张图", "热门 ≠ 好卖，长尾商品最怕深夜", "08_cold_hot_items",
     "左：白天与深夜的转化率，按商品被多少人看过分 10 档（越右越热门）。中：每档深夜少掉多少。右：换成相对比例再看一次。",
     ["白天 1 小时内：只被 1 人看过的冷门商品 <b>1.10%</b> 会买，最热门的商品只有 <b>0.42%</b> —— 热门是「围观多、买得少」。",
      "深夜掉的绝对数量：最冷门 <b>−0.44</b> 个百分点，最热门 <b>−0.08</b>。",
      "但按比例看，最冷和最热都在 −20% 上下 —— 主要是规模效应，不过长尾商品确实更敏感。"],
     "描述统计 + 固定效应 LPM",
     "面板 A 为原始转化率；面板 B 为每个热度档单独拟合 M2（用户 + 商品 + 日期 FE）；面板 C 为 B 的系数 ÷ 白天均值。结果文件 results/cold_hot_items_*.csv"),
    ("09", "第九张图", "按品类看：哪类商品都怕深夜", "11_category_night_penalty",
     "把每个 episode 关联上品类，取事件量前 20 的品类、其余 9,400 个归「其他」，每组单独重跑深夜 vs 白天的生存分析。条形越靠左，说明越怕深夜。",
     ["21 组（前 20 品类 + 其他）的深夜风险比 <b>全部 < 1</b>，没有例外 —— 深夜买得少是普适的。",
      "差别不大：最怕深夜的品类 HR <b>0.58</b>、最不怕的 <b>0.81</b>，多数在 0.6–0.75。",
      "三个购买窗口都 < 1；因果森林里 15 个品类哑变量重要性合计仅 0.0001 —— 品类不是主要调节因素。"],
     "Cox 生存模型（按品类）",
     "给 episode 关联 category_id，取事件量前 20 品类 + 其他，每组单独跑 Cox（深夜/凌晨 vs 白天，1h/3h/24h）。结果文件 results/category_survival_summary_full.csv"),
]


def fig_html(num, label, title, name, hint, bullets, pill, method):
    key = name.split('_')[0]
    bl = '\n'.join(f'<li>{b}</li>' for b in bullets)
    return f'''
<article class="fig" id="fig{key}">
  <div class="head">
    <span class="num">{num}</span>
    <h3 style="margin:0">{title}</h3>
  </div>
  <div class="method"><span class="badge">{pill}</span><span class="mtext">{method}</span></div>
  <div class="txt">
    <figure class="zoom"><img src="@@IMG_{name}@@" alt="{title}">
      <figcaption>点击图片可放大查看</figcaption></figure>
    <div style="display:grid;gap:14px;align-content:start">
      <div class="tip"><b>怎么看：</b>{hint}</div>
      <div class="take"><ul class="clean" style="margin:0">{bl}</ul></div>
    </div>
  </div>
</article>'''


NAV = '\n'.join(f'<li><a href="#{i}" data-t="{i}">{t}</a></li>' for i, _, t in BODY_CHECKS)

row_html = '\n'.join(
    f'<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>'
    for a, b, c in [
        ('固定效应 LPM · M2 主模型', '深夜比白天少 0.18（1 小时）/ 0.31（24 小时）个百分点', '夜里买得更少'),
        ('固定效应 LPM · 7 项稳健性', '方向全部一样，没有一个翻过来', '不是"调"出来的'),
        ('Cox 生存模型 · 分段', '深夜＝不买；凌晨＝晚点买', '两种不同的"少"'),
        ('Causal Forest（DML）', '冷门商品、老用户掉得最多', '按比例其实差不多'),
        ('Cox 生存模型 · 按小时', '睡前最差，上午 9–11 最好', '深夜不是一个整体'),
        ('Cox 生存模型 · 按品类', '21 组全部 HR < 1，差别 0.58–0.81', '品类不是主因'),
    ])

figs = '\n'.join(fig_html(*f) for f in FIGS)

HTML = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>深夜刷淘宝，真的更容易下单吗？｜淘宝 1 亿条浏览记录分析</title>
<style>{CSS}</style>
</head>
<body>
<nav><div class="wrap">
  <a class="brand" href="#top">IS5312<small>Analytical Programming with Python</small></a>
  <ul>{NAV}</ul>
</div></nav>

<header class="hero" id="top"><div class="wrap">
  <div class="kicker">Mid-term report · 2026.10.23</div>
  <h1>深夜刷淘宝，<br>真的更容易下单吗？</h1>
  <p class="lead">用 1 亿条真实浏览记录，检验一个几乎所有人都相信的直觉。结论和直觉相反：<b>夜里看商品的人，买得更少。</b></p>
  <div class="chips">
    <span class="chip"><b>1.00 亿</b> 条行为记录</span>
    <span class="chip"><b>5,131 万</b> 次"第一次看到"</span>
    <span class="chip"><b>983,132</b> 名用户</span>
    <span class="chip"><b>9 天</b> · 2017-11-25 至 12-03</span>
  </div>
</div></header>

<main>
<section id="q"><div class="wrap">
  <h2>1 · 问题：一个所有人都相信的直觉</h2><div class="rule"></div>
  <p>「夜深了，自控力变差，所以更容易冲动下单。」这句话听起来很有道理，但它其实是一个<b>可以被数据检验</b>的假设。</p>
  <div class="grid g3" style="margin:26px 0">
    <div class="card"><h3>问题一：有没有差异？</h3><p>深夜看商品，和白天看商品，之后买的比例差多少？</p></div>
    <div class="card"><h3>问题二：是哪种"少"？</h3><p>买得少，是因为"根本没买"，还是"晚一点才买"？</p></div>
    <div class="card"><h3>问题三：谁最受影响？</h3><p>哪类商品、哪类人，在深夜掉得最厉害？</p></div>
  </div>
  <div class="callout">
    <div class="lab">One line</div>
    <p style="margin:8px 0 0;font-size:19px">如果直觉错了，那么"夜间流量更值钱"这个假设、以及按它做的投放，就需要重新算一遍。</p>
  </div>
</div></section>

<section id="data"><div class="wrap">
  <h2>2 · 数据：9 天里发生的 1 亿次"看"和"买"</h2><div class="rule"></div>
  <div class="grid g3" style="margin-bottom:26px">
    <div class="stat"><div class="n">1.00 亿</div><div class="l">条行为记录</div><div class="s">浏览 / 收藏 / 加购 / 下单</div></div>
    <div class="stat"><div class="n">5,131 万</div><div class="l">次"第一次看到"</div><div class="s">这才是分析单位，不是 1 亿个独立样本</div></div>
    <div class="stat"><div class="n">983,132</div><div class="l">名用户</div><div class="s">2017-11-25 至 12-03，上海时区</div></div>
  </div>
  <div class="grid g2">
    <div class="card">
      <h3>我们怎么定义"一个样本"？</h3>
      <ul class="clean" style="margin-top:10px">
        <li>某人在某一刻<b>第一次看到</b>某个商品，记下这个时刻，叫它 <b>t0</b>。</li>
        <li>然后看：t0 之后 <b>1 小时</b>内有没有买？<b>24 小时</b>内有没有买？</li>
        <li>只用 t0 <b>之前</b>的信息做控制，避免"买了之后又反复看"造成的假象。</li>
        <li>全样本里，1 小时内买的约 <b>0.65%</b>，24 小时内约 <b>0.98%</b>。</li>
      </ul>
    </div>
    <div class="card">
      <h3>数据里有什么、没有什么</h3>
      <ul class="clean" style="margin-top:10px">
        <li><b>有：</b>用户、商品、品类、行为类型、时间戳。</li>
        <li><b>没有：</b>价格、金额、停留时长。</li>
        <li>所以整份报告只说"买没买"，<b>不猜</b>"花了多少钱"。</li>
        <li>数据来自天池 649（淘宝 UserBehavior）公开镜像，字段与时间窗都可核对。</li>
      </ul>
    </div>
  </div>
</div></section>

<section id="method"><div class="wrap">
  <h2>3 · 方法：为什么不能"直接比"</h2><div class="rule"></div>
  <p>深夜还在逛的人，和白天逛的人，本来就可能不是同一批人。直接比，会把"人的差别"错算成"时间的差别"。</p>
  <div class="two" style="margin:22px 0 26px">
    <div class="bad">
      <span class="tag no">✕ 直接比</span>
      <h3>深夜的人 vs 白天的人</h3>
      <p class="muted" style="margin-top:8px">有人本来就爱买、有人只看不买；直接比说明不了时间的作用。</p>
      <p class="muted">类比：拿爱运动的人和不爱运动的人比较，不能证明运动有没有用。</p>
    </div>
    <div class="good">
      <span class="tag yes">✓ 我们的比法</span>
      <h3>同一个人 · 同一个商品</h3>
      <p class="muted" style="margin-top:8px">只比"同一个人在白天看到商品 A"和"同一个人在深夜看到商品 A"。</p>
      <p class="muted">人和商品的差别被固定住，再加上"哪一天"也固定，剩下的差异才更像时间造成的。</p>
    </div>
  </div>
  <div class="grid g3">
    <div class="card"><h3>① 固定效应模型</h3><p>把"谁在看、看什么、哪一天"都固定住，只留时间一个变量在动。</p></div>
    <div class="card"><h3>② 生存分析</h3><p>不只看"买没买"，还看"多久买"，把"根本没买"和"晚点买"分开。</p></div>
    <div class="card"><h3>③ 因果森林</h3><p>让模型自己去找：哪类商品、哪类人，深夜掉得最狠。</p></div>
  </div>
  <div class="tip" style="margin-top:20px"><b>为什么要三个模型？</b>三个方法各自独立；如果它们给出同一个答案，我们就更有信心这不是某一方法的"错觉"。</div>
</div></section>

<section id="result"><div class="wrap">
  <h2>4 · 结果总览</h2><div class="rule"></div>
  <table>
    <thead><tr><th>方法与模型</th><th>结果（直白版）</th><th>一句话</th></tr></thead>
    <tbody>{row_html}</tbody>
  </table>
  <p class="muted">注：0.18 个百分点 ≈ 每 1,000 次浏览少买约 2 单。全部为观察性关联，不是随机实验。</p>
  <div class="callout" style="margin-top:8px">
    <div class="lab">记住这一句</div>
    <p style="margin:8px 0 0;font-size:20px">深夜的流量更"闲"，不是更"冲"。</p>
  </div>
  <div class="grid" style="gap:46px;margin-top:54px">{figs}</div>
</div></section>

<section id="take"><div class="wrap">
  <h2>5 · 所以，钱该怎么花？</h2><div class="rule"></div>
  <div class="grid g3" style="margin-bottom:22px">
    <div class="card strong"><div class="big">21–23 点</div><h3 style="margin-top:6px">最该降权</h3><p>三个购买窗口都最差，第二天也补不回来。</p></div>
    <div class="card strong"><div class="big">0–2 点</div><h3 style="margin-top:6px">看次日转化</h3><p>当场不买、睡醒再买；别只用"即时下单"来考核。</p></div>
    <div class="card strong"><div class="big">9–11 点</div><h3 style="margin-top:6px">可以加码</h3><p>三个窗口都最容易买，是全天转化的黄金时段。</p></div>
  </div>
  <div class="card maroon">
    <h3 style="color:#fff">商品层面还有两条结论</h3>
    <p style="margin-top:8px">深夜要保转化，优先照顾<b>长尾冷门商品</b>；热门商品的价值主要在<b>曝光</b>，不在成交 —— 它们白天本来就"围观多、买得少"。</p>
  </div>
</div></section>

<section id="limits"><div class="wrap">
  <h2>6 · 局限与下一步</h2><div class="rule"></div>
  <div class="two">
    <div class="card">
      <h3>这些结论不是"铁证"</h3>
      <ul class="clean" style="margin-top:10px">
        <li>观察数据，不是随机实验：只能说"相关"，不能说"导致"。</li>
        <li>只有 9 天，看不到季节变化；也没有价格，无法排除深夜促销的影响。</li>
        <li>"第一次看到"不等于人生第一次看到，之前的浏览看不到。</li>
      </ul>
    </div>
    <div class="card">
      <h3>下一步</h3>
      <ul class="clean" style="margin-top:10px">
        <li>写最终报告，把方法、结果、验证记录整理成可复现的文档。</li>
        <li>补上商品品类维度，看"哪类商品最怕深夜"。</li>
        <li>用价格代理变量（如品类均价）检验"促销"这个替代解释。</li>
      </ul>
    </div>
  </div>
  <p class="muted" style="margin-top:18px">所有代码、结果表和验证记录都在项目目录里，可随时复算。</p>
</div></section>
</main>

<footer><div class="wrap">
  <div>IS5312 Analytical Programming with Python · Semester A 2026/27</div>
  <div>中期汇报 · 2026-10-23 · Team IS5312</div>
</div></footer>

<div id="lightbox"><img id="lbimg" alt=""></div>
<script>
document.querySelectorAll('figure.zoom img').forEach(function(im){{
  im.addEventListener('click', function(){{
    document.getElementById('lbimg').src = im.src;
    document.getElementById('lightbox').classList.add('on');
  }});
}});
document.getElementById('lightbox').addEventListener('click', function(){{
  this.classList.remove('on');
}});
document.addEventListener('keydown', function(e){{
  if (e.key === 'Escape') document.getElementById('lightbox').classList.remove('on');
}});
var links = Array.prototype.slice.call(document.querySelectorAll('nav a[data-t]'));
var secs = links.map(function(a){{ return document.getElementById(a.dataset.t); }});
function spy(){{
  var y = window.scrollY + 150, cur = 0;
  secs.forEach(function(s, i){{ if (s && s.offsetTop <= y) cur = i; }});
  links.forEach(function(a, i){{ a.classList.toggle('on', i === cur); }});
}}
window.addEventListener('scroll', spy, {{passive:true}}); spy();
</script>
</body>
</html>'''

for name in [f[3] for f in FIGS]:
    HTML = HTML.replace(f'@@IMG_{name}@@', img(name))

OUT.joinpath('analysis_zh.html').write_text(HTML, encoding='utf-8')
print('saved', OUT / 'analysis_zh.html', f'{len(HTML)/1e6:.2f} MB')
