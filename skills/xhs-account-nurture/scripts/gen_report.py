#!/usr/bin/env python3
"""养号会话 HTML 报告生成器 · Nature Distilled 风格

参考风格：report-gallery 06-nature-distilled（陶土色 + 纸纹 + 衬线排版 + 大量留白）。
样式资产：assets/style-nature-distilled.css（从参考稿整体抽取，勿手工改写）。

用法:
    python3 gen_report.py --log /tmp/xhs_session_log.jsonl \
        --out 养号报告.html \
        --start "2026-09-18 14:13:56" --end "2026-09-18 14:44:05" \
        --account "Stephen Yang" --xhshao 1815841999 --mode "仅浏览" --duration 30

输入: browse_note.* 产出的 JSONL（每行：kw/dwell/scrolls/comments/title/url）
输出: 单文件 HTML；图形为内联 SVG；保留筛选/排序/展开/悬浮提示等交互
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
CSS_PATH = os.path.join(HERE, "..", "assets", "style-nature-distilled.css")

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>小红书养号报告 · __DATE__</title>
<meta name="description" content="小红书养号报告 · 会话记录 __DATE__">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,500;0,600;1,400&family=Raleway:wght@400;500;600;700&display=swap">
<style>
__CSS__
/* ---- 交互增强（不改变主风格，仅补充交互所需） ---- */
.tag-btn{cursor:pointer;user-select:none;transition:background .22s var(--ease-out),color .22s var(--ease-out)}
.tag-btn:hover{background:rgba(198,123,92,.22)}
.tag-btn.on{background:var(--clay-deep);border-color:var(--clay-deep);color:var(--cream)}
.tag-btn.dim{opacity:.42}
.kw-row{cursor:pointer}
.kw-row.off .kw-fill{opacity:.3}
.kw-row.off .kw-name,.kw-row.off .kw-num{opacity:.5}
#tip{position:fixed;z-index:90;pointer-events:none;opacity:0;transition:opacity .14s;
  background:var(--ink);color:var(--cream);font-family:var(--font-ui);font-size:.78rem;
  padding:.4rem .62rem;border-radius:8px;white-space:nowrap;box-shadow:0 6px 18px -8px rgba(58,50,42,.6)}
tr.linkrow td{background:rgba(212,196,168,.3);font-size:.8rem;color:var(--ink-soft);padding:.5rem .7rem}
tr.linkrow a{word-break:break-all}
.detail th.th-sort{cursor:pointer}
.detail th.th-sort::after{content:" ⇅";opacity:.45;font-size:.8em}
.detail th.th-sort.asc::after{content:" ↑";opacity:.9}
.detail th.th-sort.desc::after{content:" ↓";opacity:.9}
.dim-row{opacity:.35}
</style>
<script>document.documentElement.classList.replace('no-js','js')</script>
</head>
<body>
<div class="grain" aria-hidden="true"></div>

<header class="topbar">
  <div class="topbar-in">
    <span class="stamp">小红书养号 · 会话记录 __DATE__</span>
    <span class="stamp" id="clock"></span>
  </div>
</header>

<main id="main">

  <!-- 封面 -->
  <section class="cover">
    <div class="wrap cover-in">
      <div>
        <p class="kicker">会话记录 · __DATE__</p>
        <h1>小红书养号报告</h1>
        <p class="deck">__START__ — __END__　·　模式 __MODE__　·　共 __DURATION__ 分钟</p>
        <div class="cover-meta">
          <div class="row"><span class="k">账号</span><span class="v">__ACCOUNT__</span></div>
          <div class="row wide"><span class="k">账号信息</span><span class="v">小红书号 __XHSHAO__　·　本次会话 __TOTAL__ 篇（去重 __UNIQUE__ 篇）　·　互动 __INTERACT__ 次</span></div>
          <div class="row"><span class="k">看评论</span><span class="v">__CMT__ / __TOTAL__ 篇（停留 5–15 秒，模拟真人翻评论）</span></div>
        </div>
        <ul class="tags">
          <li>__MODE__</li><li>__DURATION__ 分钟</li><li>__TOTAL__ 篇</li>
          <li>去重 __UNIQUE__ 篇</li><li>平均停留 __AVG__ 秒</li>
        </ul>
      </div>
      <div class="cover-figure" aria-hidden="true">
        <svg viewBox="0 0 240 320" fill="none" focusable="false">
          <path d="M120 318 C112 252 126 182 118 40" stroke="#6B7B3C" stroke-width="2.4" stroke-linecap="round" opacity=".5"/>
          <ellipse cx="86" cy="262" rx="34" ry="12" transform="rotate(-26 86 262)" fill="#6B7B3C" opacity=".20"/>
          <ellipse cx="154" cy="262" rx="34" ry="12" transform="rotate(26 154 262)" fill="#C67B5C" opacity=".26"/>
          <ellipse cx="88" cy="220" rx="32" ry="11.5" transform="rotate(-26 88 220)" fill="#C67B5C" opacity=".22"/>
          <ellipse cx="152" cy="220" rx="32" ry="11.5" transform="rotate(26 152 220)" fill="#6B7B3C" opacity=".22"/>
          <ellipse cx="92" cy="180" rx="28" ry="10.5" transform="rotate(-26 92 180)" fill="#6B7B3C" opacity=".26"/>
          <ellipse cx="148" cy="180" rx="28" ry="10.5" transform="rotate(26 148 180)" fill="#6B7B3C" opacity=".18"/>
          <ellipse cx="96" cy="142" rx="24" ry="9" transform="rotate(-26 96 142)" fill="#B5651D" opacity=".20"/>
          <ellipse cx="144" cy="142" rx="24" ry="9" transform="rotate(26 144 142)" fill="#6B7B3C" opacity=".24"/>
          <ellipse cx="101" cy="104" rx="19" ry="7.5" transform="rotate(-26 101 104)" fill="#6B7B3C" opacity=".22"/>
          <ellipse cx="139" cy="104" rx="19" ry="7.5" transform="rotate(26 139 104)" fill="#6B7B3C" opacity=".16"/>
          <ellipse cx="105" cy="72" rx="15" ry="6" transform="rotate(-26 105 72)" fill="#6B7B3C" opacity=".2"/>
          <ellipse cx="135" cy="72" rx="15" ry="6" transform="rotate(26 135 72)" fill="#C67B5C" opacity=".2"/>
          <ellipse cx="118" cy="42" rx="9.5" ry="19" transform="rotate(-6 118 42)" fill="#6B7B3C" opacity=".26"/>
          <circle cx="128" cy="240" r="5.5" fill="#C67B5C" opacity=".45"/>
          <circle cx="112" cy="196" r="4.5" fill="#C67B5C" opacity=".4"/>
          <circle cx="130" cy="152" r="4" fill="#C67B5C" opacity=".35"/>
        </svg>
      </div>
    </div>
    <div class="strata" aria-hidden="true">
      <svg viewBox="0 0 1440 90" preserveAspectRatio="none" focusable="false">
        <path d="M0 54 C 170 22 330 78 520 54 C 710 30 880 76 1080 48 C 1240 26 1360 62 1440 44 L1440 90 L0 90 Z" fill="#D4C4A8" opacity=".45"/>
        <path d="M0 66 C 190 42 350 84 540 64 C 730 44 900 82 1090 60 C 1250 42 1370 70 1440 58 L1440 90 L0 90 Z" fill="#6B7B3C" opacity=".16"/>
        <path d="M0 76 C 200 60 360 90 560 74 C 760 58 920 88 1100 72 C 1260 58 1380 80 1440 70 L1440 90 L0 90 Z" fill="#F5F0E1"/>
      </svg>
    </div>
  </section>

  <!-- 摘要 -->
  <section class="band" id="abstract">
    <div class="wrap">
      <header class="sec-head reveal">
        <div class="sec-top"><span class="sec-num" aria-hidden="true">摘</span><h2>一次 __DURATION__ 分钟的只读会话</h2></div>
      </header>
      <p class="lede reveal">
        本报告记录 __START__ — __END__ 的一次「__MODE__」模式会话，共 __DURATION__ 分钟。
        账号 __ACCOUNT__（小红书号 __XHSHAO__）本次浏览笔记 __TOTAL__ 篇，去重后 __UNIQUE__ 篇，
        互动 __INTERACT__ 次，平均停留 __AVG__ 秒。以下为关键指标与由指标直接归纳的结论。
      </p>
      <div class="kpis">__KPIS__</div>
    </div>
  </section>

  <div class="wrap"><div class="rule-leaf" aria-hidden="true">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M11 20A7 7 0 0 1 4 13c0-5 4-9 16-9 0 12-4 16-9 16Z"/><path d="M4 20c3-6 7-9 12-10"/></svg>
  </div></div>

  <!-- 01 时长分布 -->
  <section class="band band-tint" id="s01">
    <div class="wrap">
      <header class="sec-head reveal">
        <div class="sec-top"><span class="sec-num" aria-hidden="true">01</span><h2>阅读时长分布</h2></div>
        <p class="sec-note">停留时长按「多数快刷、少数细读」分布，避免等间隔的机械轨迹。悬停查看区间与篇数。</p>
      </header>
      <div class="fig-split">
        <div class="donut-box reveal" id="donut"></div>
        <ul class="donut-legend reveal" id="donutLegend"></ul>
      </div>
      <figure class="fig reveal">
        <div class="fig-frame" id="hist"></div>
        <figcaption id="histCap"></figcaption>
      </figure>
    </div>
  </section>

  <!-- 02 时序 -->
  <section class="band" id="s02">
    <div class="wrap">
      <header class="sec-head reveal">
        <div class="sec-top"><span class="sec-num" aria-hidden="true">02</span><h2>会话时序</h2></div>
        <p class="sec-note">按浏览顺序绘制每篇停留时长，观察节奏是否前紧后松（真人注意力衰减）。悬停查看标题。</p>
      </header>
      <figure class="fig reveal">
        <div class="fig-frame" id="timeline"></div>
        <figcaption id="tlCap"></figcaption>
      </figure>
    </div>
  </section>

  <!-- 03 关键词 -->
  <section class="band band-tint" id="s03">
    <div class="wrap">
      <header class="sec-head reveal">
        <div class="sec-top"><span class="sec-num" aria-hidden="true">03</span><h2>关键词分布</h2></div>
        <p class="sec-note">本次会话命中的关键词。点击任一关键词可筛选下方明细表，再次点击取消。</p>
      </header>
      <div class="kpis" style="margin-bottom:1.6rem"><ul class="tags" id="chips"></ul></div>
      <div class="fig reveal"><div class="fig-frame"><div class="kw-chart" id="kws"></div></div></div>
    </div>
  </section>

  <!-- 04 明细 -->
  <section class="band" id="s04">
    <div class="wrap">
      <header class="sec-head reveal">
        <div class="sec-top"><span class="sec-num" aria-hidden="true">04</span><h2>浏览明细</h2></div>
        <p class="sec-note">点击表头排序，点击任意行展开完整链接。</p>
      </header>
      <div class="table-wrap reveal">
        <table class="detail" id="tbl">
          <caption>本次会话逐篇记录（共 __TOTAL__ 行）</caption>
          <thead><tr>
            <th class="c-num th-sort" data-k="i">#</th>
            <th class="c-title th-sort" data-k="title">笔记标题</th>
            <th class="c-kw th-sort" data-k="kw">关键词</th>
            <th class="c-dwell th-sort" data-k="dwell">停留</th>
            <th class="c-scroll th-sort" data-k="scrolls">滚动</th>
            <th class="c-cmt th-sort" data-k="comments">评论</th>
          </tr></thead>
          <tbody id="tbody"></tbody>
        </table>
      </div>
    </div>
  </section>

  <!-- 05 踩坑 -->
  <section class="band" id="s05">
    <div class="wrap">
      <header class="sec-head reveal">
        <div class="sec-top"><span class="sec-num" aria-hidden="true">05</span><h2>本次排查到的坑</h2></div>
        <p class="sec-note">已回写进技能知识库，下次不再重复踩。</p>
      </header>
      __PITFALLS__
    </div>
  </section>

  <!-- 06 建议 -->
  <section class="band band-tint" id="s06">
    <div class="wrap">
      <header class="sec-head reveal">
        <div class="sec-top"><span class="sec-num" aria-hidden="true">06</span><h2>下次建议</h2></div>
      </header>
      <div class="reveal">__ADVICE__</div>
    </div>
  </section>

  <!-- 来源 -->
  <section class="band" id="source">
    <div class="wrap">
      <div class="src reveal">
        <h2>数据来源与口径</h2>
        <p class="src-line">日志：browse_note.* 逐篇输出的 JSONL（kw / dwell / scrolls / comments / title / url）。</p>
        <p class="src-line">去重口径：按 URL 去掉 <code>xsec_token</code> 之后的主键比对，会话内与跨会话历史均参与。</p>
        <p class="src-line">停留时长：脚本内随机取值（20–150 秒，按「多数快刷、少数细读」分布），非页面埋点数据。</p>
      </div>
    </div>
  </section>
</main>

<footer class="foot">
  <div class="wrap foot-in">
    <p>由 xhs-account-nurture 技能生成 · 数据来自本次会话日志</p>
    <p class="foot-stamp">STYLE · NATURE DISTILLED</p>
  </div>
</footer>

<div id="tip"></div>
<script>
const DATA = __DATA__;
const tip = document.getElementById('tip');
const show = (e, html) => { tip.innerHTML = html; tip.style.opacity = 1;
  tip.style.left = (e.clientX + 14) + 'px'; tip.style.top = (e.clientY - 10) + 'px'; };
const hide = () => tip.style.opacity = 0;
const NS = 'http://www.w3.org/2000/svg';
const el = (n, a = {}) => { const x = document.createElementNS(NS, n);
  for (const k in a) x.setAttribute(k, a[k]); return x; };
const T = (n, cls, txt) => { const x = el(n, cls ? { class: cls } : {}); x.textContent = txt; return x; };
const C = { terracotta: '#C67B5C', clay: '#B5651D', clayDeep: '#8A4A16', olive: '#6B7B3C', sand: '#D4C4A8', ink: '#3A322A' };

/* 环形图：快刷 / 正常 / 细读 */
(function () {
  const seg = [
    ['快刷 < 45s', DATA.filter(d => d.dwell < 45).length, C.terracotta],
    ['正常 45–90s', DATA.filter(d => d.dwell >= 45 && d.dwell < 90).length, C.olive],
    ['细读 ≥ 90s', DATA.filter(d => d.dwell >= 90).length, C.clay]
  ];
  const total = DATA.length || 1, R = 78, r0 = 52, W = 240, H = 240, cx = 120, cy = 120;
  const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img' });
  let a0 = -Math.PI / 2;
  seg.forEach(([name, v, color]) => {
    if (!v) return;
    const a1 = a0 + 2 * Math.PI * v / total, big = (a1 - a0) > Math.PI ? 1 : 0;
    const p = el('path', {
      d: `M ${cx + R * Math.cos(a0)} ${cy + R * Math.sin(a0)} A ${R} ${R} 0 ${big} 1 ${cx + R * Math.cos(a1)} ${cy + R * Math.sin(a1)} L ${cx + r0 * Math.cos(a1)} ${cy + r0 * Math.sin(a1)} A ${r0} ${r0} 0 ${big} 0 ${cx + r0 * Math.cos(a0)} ${cy + r0 * Math.sin(a0)} Z`,
      fill: color, opacity: .9
    });
    p.addEventListener('mousemove', e => show(e, `<b>${name}</b>　${v} 篇　${(v / total * 100).toFixed(0)}%`));
    p.addEventListener('mouseleave', hide);
    svg.appendChild(p); a0 = a1;
  });
  const num = T('text', 'donut-num', String(DATA.length));
  num.setAttribute('x', cx); num.setAttribute('y', cy + 6); num.setAttribute('text-anchor', 'middle');
  const unit = T('text', 'donut-unit', '篇');
  unit.setAttribute('x', cx); unit.setAttribute('y', cy + 28); unit.setAttribute('text-anchor', 'middle');
  svg.appendChild(num); svg.appendChild(unit);
  document.getElementById('donut').appendChild(svg);

  const ul = document.getElementById('donutLegend');
  seg.forEach(([name, v, color]) => {
    const li = document.createElement('li');
    const dot = document.createElement('span');
    dot.className = 'sw-dot'; dot.style.background = color;
    const t = document.createElement('span'); t.className = 'lg-t'; t.textContent = name;
    const m = document.createElement('span'); m.className = 'lg-m';
    m.textContent = `${v} 篇 · ${(v / total * 100).toFixed(0)}%`;
    li.appendChild(dot); li.appendChild(t); li.appendChild(m); ul.appendChild(li);
  });
})();

/* 直方图 */
(function () {
  const buckets = [[20, 40], [40, 60], [60, 80], [80, 100], [100, 150]];
  const cnt = buckets.map(b => DATA.filter(d => d.dwell >= b[0] && d.dwell < b[1]).length);
  const W = 720, H = 300, pad = { l: 70, r: 20, t: 40, b: 46 };
  const base = 260, top = 60, ih = base - top;
  const max = Math.max(...cnt, 1);
  const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img' });
  const defs = el('defs');
  const lg = el('linearGradient', { id: 'barFill', x1: '0', y1: '0', x2: '0', y2: '1' });
  [[0, '#C67B5C'], [1, '#B5651D']].forEach(([o, c]) => {
    const s = el('stop', { offset: (o * 100) + '%', 'stop-color': c }); lg.appendChild(s);
  });
  defs.appendChild(lg); svg.appendChild(defs);

  for (let g = 0; g <= 3; g++) {
    const y = base - ih * g / 3, v = Math.round(max * g / 3);
    svg.appendChild(el('line', { x1: pad.l, y1: y, x2: W - pad.r, y2: y, class: 'gridline' }));
    const t = T('text', 'ax', String(v));
    t.setAttribute('x', pad.l - 10); t.setAttribute('y', y + 4); t.setAttribute('text-anchor', 'end');
    svg.appendChild(t);
  }
  const yl = T('text', 'ax', '篇数');
  yl.setAttribute('x', pad.l); yl.setAttribute('y', 34); svg.appendChild(yl);

  const gap = (W - pad.l - pad.r) / buckets.length, bw = gap * .58;
  buckets.forEach((b, i) => {
    const h = ih * cnt[i] / max, x = pad.l + gap * i + (gap - bw) / 2, y = base - h;
    const p = el('path', {
      d: `M${x} ${base} L${x} ${y + 8} Q${x} ${y} ${x + 8} ${y} L${x + bw - 8} ${y} Q${x + bw} ${y} ${x + bw} ${y + 8} L${x + bw} ${base} Z`,
      fill: 'url(#barFill)', opacity: String(1 - i * .06)
    });
    p.addEventListener('mousemove', e => show(e, `<b>${b[0]}–${b[1]}s</b>　${cnt[i]} 篇`));
    p.addEventListener('mouseleave', hide);
    svg.appendChild(p);
    const vt = T('text', 'val', String(cnt[i]));
    vt.setAttribute('x', x + bw / 2); vt.setAttribute('y', y - 10); vt.setAttribute('text-anchor', 'middle');
    svg.appendChild(vt);
    const bt = T('text', 'ax', b[0] + '–' + b[1] + 's');
    bt.setAttribute('x', x + bw / 2); bt.setAttribute('y', base + 24); bt.setAttribute('text-anchor', 'middle');
    svg.appendChild(bt);
  });
  svg.appendChild(el('line', { x1: pad.l, y1: base, x2: W - pad.r, y2: base, class: 'baseline' }));
  document.getElementById('hist').appendChild(svg);
  const top1 = cnt.indexOf(Math.max(...cnt));
  document.getElementById('histCap').innerHTML =
    `图 1 · 阅读时长分布：${DATA.length} 篇按停留时长切成 5 个固定区间，<b>${buckets[top1][0]}–${buckets[top1][1]} 秒</b>一档 ${Math.max(...cnt)} 篇。`;
})();

/* 时序折线 */
(function () {
  const W = 720, H = 260, pad = { l: 70, r: 22, t: 30, b: 42 };
  const base = H - pad.b, top = pad.t, ih = base - top, iw = W - pad.l - pad.r;
  const max = Math.max(...DATA.map(d => d.dwell)) * 1.15;
  const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img' });
  for (let g = 0; g <= 3; g++) {
    const y = base - ih * g / 3, v = Math.round(max * g / 3);
    svg.appendChild(el('line', { x1: pad.l, y1: y, x2: W - pad.r, y2: y, class: 'gridline' }));
    const t = T('text', 'ax', v + 's');
    t.setAttribute('x', pad.l - 10); t.setAttribute('y', y + 4); t.setAttribute('text-anchor', 'end');
    svg.appendChild(t);
  }
  const X = i => pad.l + (DATA.length > 1 ? iw * i / (DATA.length - 1) : iw / 2);
  const Y = v => base - ih * v / max;
  svg.appendChild(el('path', {
    d: DATA.map((d, i) => `${i ? 'L' : 'M'} ${X(i)} ${Y(d.dwell)}`).join(' '),
    fill: 'none', stroke: C.terracotta, 'stroke-width': 2, opacity: .6, 'stroke-linejoin': 'round'
  }));
  DATA.forEach((d, i) => {
    const c = el('circle', { cx: X(i), cy: Y(d.dwell), r: 4.2, fill: C.clayDeep, opacity: .85 });
    c.style.cursor = 'pointer';
    c.addEventListener('mousemove', e => show(e, `#${d.i} <b>${d.dwell}s</b><br>${(d.title || '').slice(0, 30)}`));
    c.addEventListener('mouseleave', hide);
    svg.appendChild(c);
  });
  svg.appendChild(el('line', { x1: pad.l, y1: base, x2: W - pad.r, y2: base, class: 'baseline' }));
  const cap = T('text', 'ax', '浏览顺序 →'); cap.setAttribute('x', pad.l); cap.setAttribute('y', H - 12);
  svg.appendChild(cap);
  document.getElementById('timeline').appendChild(svg);
  const half = Math.floor(DATA.length / 2);
  const avg = a => (a.reduce((s, x) => s + x.dwell, 0) / Math.max(a.length, 1)).toFixed(1);
  document.getElementById('tlCap').innerHTML =
    `图 2 · 会话时序：前半程平均 ${avg(DATA.slice(0, half))} 秒，后半程 ${avg(DATA.slice(half))} 秒。`;
})();

/* 关键词条 + 筛选 */
const kwCount = {};
DATA.forEach(d => kwCount[d.kw] = (kwCount[d.kw] || 0) + 1);
const kwList = Object.entries(kwCount).sort((a, b) => b[1] - a[1]);
let filterKw = null, sortKey = 'i', sortAsc = true;

(function () {
  const box = document.getElementById('kws'), chips = document.getElementById('chips');
  const max = Math.max(...kwList.map(k => k[1]));
  kwList.forEach(([kw, v]) => {
    const row = document.createElement('div'); row.className = 'kw-row'; row.dataset.kw = kw;
    const nm = document.createElement('div'); nm.className = 'kw-name'; nm.textContent = kw;
    const tr = document.createElement('div'); tr.className = 'kw-track';
    const fl = document.createElement('div'); fl.className = 'kw-fill';
    fl.style.setProperty('--v', Math.max(4, v / max * 100) + '%');
    tr.appendChild(fl);
    const nu = document.createElement('div'); nu.className = 'kw-num'; nu.textContent = v;
    row.appendChild(nm); row.appendChild(tr); row.appendChild(nu);
    row.addEventListener('click', () => toggleFilter(kw));
    box.appendChild(row);

    const li = document.createElement('li'); li.className = 'tag-btn'; li.dataset.kw = kw;
    li.textContent = `${kw} · ${v}`; li.addEventListener('click', () => toggleFilter(kw));
    chips.appendChild(li);
  });
})();

function toggleFilter(kw) {
  filterKw = (filterKw === kw) ? null : kw;
  document.querySelectorAll('#chips .tag-btn').forEach(c =>
    c.classList.toggle('on', c.dataset.kw === filterKw));
  document.querySelectorAll('.kw-row').forEach(r =>
    r.classList.toggle('off', !!filterKw && r.dataset.kw !== filterKw));
  renderTable();
}

function renderTable() {
  const rows = DATA.filter(d => !filterKw || d.kw === filterKw).slice().sort((a, b) => {
    const va = a[sortKey], vb = b[sortKey];
    const cmp = (typeof va === 'number') ? va - vb : String(va).localeCompare(String(vb), 'zh');
    return sortAsc ? cmp : -cmp;
  });
  const tb = document.getElementById('tbody'); tb.innerHTML = '';
  rows.forEach(d => {
    const tr = document.createElement('tr'); tr.style.cursor = 'pointer';
    tr.innerHTML =
      `<td class="c-num">${d.i}</td>` +
      `<td class="c-title">${d.title || '—'}</td>` +
      `<td class="c-kw"><span class="kw">${d.kw}</span></td>` +
      `<td class="c-dwell">${d.dwell}s</td>` +
      `<td class="c-scroll">${d.scrolls}</td>` +
      `<td class="c-cmt">${d.comments ? '已看' : '—'}</td>`;
    const link = document.createElement('tr'); link.className = 'linkrow'; link.style.display = 'none';
    link.innerHTML = `<td colspan="6">${d.url ? `<a href="${d.url}" target="_blank" rel="noreferrer">${d.url}</a>` : '（无链接记录）'}</td>`;
    tr.addEventListener('click', () => link.style.display = link.style.display === 'none' ? '' : 'none');
    tb.appendChild(tr); tb.appendChild(link);
  });
  document.querySelectorAll('#tbl th.th-sort').forEach(th => {
    th.classList.remove('asc', 'desc');
    if (th.dataset.k === sortKey) th.classList.add(sortAsc ? 'asc' : 'desc');
  });
}
document.querySelectorAll('#tbl th.th-sort').forEach(th => th.addEventListener('click', () => {
  const k = th.dataset.k;
  if (k === sortKey) sortAsc = !sortAsc; else { sortKey = k; sortAsc = true; }
  renderTable();
}));
renderTable();

document.getElementById('clock').textContent = '生成于 ' + new Date().toLocaleString('zh-CN', { hour12: false });

const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }), { threshold: .1 });
document.querySelectorAll('.reveal').forEach(e => io.observe(e));
</script>
</body>
</html>
"""

KPI_ICONS = {
    "leaf": '<path d="M11 20A7 7 0 0 1 4 13c0-5 4-9 16-9 0 12-4 16-9 16Z"/><path d="M4 20c3-6 7-9 12-10"/>',
    "copy": '<circle cx="9.5" cy="12" r="6.2"/><circle cx="14.5" cy="12" r="6.2"/>',
    "clock": '<circle cx="12" cy="12" r="8.4"/><path d="M12 6.8v5.5l3.4 2"/>',
    "gauge": '<path d="M3 14.5h18"/><path d="M6 14.5V11M12 14.5V9.5M18 14.5V11"/><circle cx="9" cy="14.5" r="2.4" fill="currentColor" stroke="none"/>',
    "heart": '<path d="M12 20s-7-4.5-7-9a4 4 0 017-2.6A4 4 0 0119 11c0 4.5-7 9-7 9z"/>',
    "comment": '<path d="M20 15a2 2 0 01-2 2H8l-4 3V6a2 2 0 012-2h12a2 2 0 012 2z"/>',
}


def kpi(icon, val, unit, label):
    return (
        '<div class="kpi reveal">'
        f'<svg class="kpi-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" '
        f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{KPI_ICONS[icon]}</svg>'
        f'<p class="kpi-val"><b>{val}</b><span>{unit}</span></p>'
        f'<p class="kpi-lab">{label}</p></div>'
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--start", default="")
    ap.add_argument("--end", default="")
    ap.add_argument("--account", default="（未填写）")
    ap.add_argument("--xhshao", default="—")
    ap.add_argument("--mode", default="仅浏览")
    ap.add_argument("--duration", type=int, default=0)
    ap.add_argument("--interact", type=int, default=0)
    a = ap.parse_args()

    items = []
    with open(a.log, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except Exception:
                continue
    if not items:
        sys.exit("日志为空或格式不正确")

    for i, d in enumerate(items, 1):
        d["i"] = i
        d["dwell"] = int(d.get("dwell", 0))
        d["scrolls"] = int(d.get("scrolls", 0))
        d["comments"] = int(d.get("comments", 0) or 0)
        d["title"] = re.sub(r"\s*-\s*小红书\s*$", "", (d.get("title") or "").strip())
        d["kw"] = d.get("kw", "—")

    total = len(items)
    uniq = len({(d.get("url") or "").split("?")[0] for d in items if d.get("url")})
    sum_dwell = sum(d["dwell"] for d in items)
    avg = sum_dwell / total
    cmt = sum(1 for d in items if d["comments"])
    duration = a.duration or max(1, round(sum_dwell / 60))

    kpis = "".join([
        kpi("leaf", total, "篇", "浏览笔记"),
        kpi("copy", uniq, "篇", "去重后"),
        kpi("clock", duration, "分", "会话时长"),
        kpi("gauge", f"{avg:.1f}", "秒", "平均停留"),
        kpi("heart", a.interact, "次", "互动"),
        kpi("comment", cmt, "篇", "浏览过评论"),
    ])

    pitfalls = "".join(
        '<div class="fig reveal"><div class="fig-frame">'
        '<h3 style="margin-bottom:.4rem">%s</h3>'
        '<p style="margin:0;color:var(--ink-soft);font-size:.94rem">%s</p></div></div>' % (t, b)
        for t, b in [
            ("300012 拦截页：Chrome for Testing 被识别",
             "agent-browser 默认使用测试版构建，小红书在页面加载前即拦截。必须改用正式版 Chrome 二进制。与网络、代理、沙箱均无关。"),
            ("300031：无 xsec_token 的笔记链接打不开",
             "信息流卡片第一个 &lt;a&gt; 是 /explore/&lt;id&gt;（无 token），打开必失败。必须用 a[href*=xsec_token] 取带 token 的链接，脚本已内置换一篇重试。"),
            ("登录态不在 Cookie 表，而在 Local Storage",
             "用 sqlite 查 Cookies 查不到 xiaohongshu 记录，会误判为未登录。判断是否登录应看页面侧边栏「我」是否有头像。"),
        ]
    )

    advice_items = [
        "下次养号建议间隔 1 天以上，单次不超过 30 分钟。",
        "关键词已改为「7 个主词 + 3 个推断词」随机抽取，避免每次搜索词完全一致。",
        "已加入跨会话 URL 去重（~/.workbuddy/xhs-seen-urls.txt），重复打开不会再出现。",
        "每篇按 70% 概率滚到评论区停留 5–15 秒，提升行为真实性。",
        "会话开头先随机看 2–3 篇首页推荐，再进入关键词搜索，符合真人使用顺序。",
        "当前为零互动；如需提升活跃信号，可改为「仅点赞 + 30% 概率」，仍不涉及评论与关注。",
    ]
    advice = '<ul class="donut-legend">' + "".join(
        '<li><span class="sw-dot" style="background:var(--terracotta)"></span>'
        '<span class="lg-t" style="font-weight:500;font-size:.95rem">%s</span></li>' % t
        for t in advice_items
    ) + "</ul>"

    date = (a.start or datetime.now().strftime("%Y-%m-%d"))[:10]

    try:
        with open(CSS_PATH, encoding="utf-8") as f:
            css = f.read()
    except Exception:
        css = "/* 样式资产缺失，已降级 */ body{background:#F5F0E1;color:#3A322A;font-family:serif}"

    html = (TEMPLATE
            .replace("__CSS__", css)
            .replace("__DATA__", json.dumps(items, ensure_ascii=False))
            .replace("__DATE__", date)
            .replace("__START__", a.start or "—")
            .replace("__END__", a.end or "—")
            .replace("__MODE__", a.mode)
            .replace("__DURATION__", str(duration))
            .replace("__ACCOUNT__", a.account)
            .replace("__XHSHAO__", a.xhshao)
            .replace("__TOTAL__", str(total))
            .replace("__UNIQUE__", str(uniq))
            .replace("__INTERACT__", str(a.interact))
            .replace("__CMT__", str(cmt))
            .replace("__AVG__", f"{avg:.1f}")
            .replace("__KPIS__", kpis)
            .replace("__PITFALLS__", pitfalls)
            .replace("__ADVICE__", advice))

    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"报告已生成: {a.out}（{total} 篇，去重 {uniq} 篇，平均停留 {avg:.1f}s，看评论 {cmt} 篇）")


if __name__ == "__main__":
    main()
