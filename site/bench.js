/* Benchmarks page (bench.html), built from the design canvas (project/Bench.dc.html).
   Reads only the published files: data/benches.json (list, titles, groups, tab order), data/bench-compare.json
   (one row per bench x style x setting), data/external-scores.json, and data/bench-<name>.json (answers, review,
   notes, prompt styles) when a bench is opened. A new bench appears when its data file is published.
   The view lives in the URL hash: #bench=compare | #bench=<name>&tab=results|review|answers|method
   [&style=terse|normal|both&config=&q=&grade=&answer=<question>__<style>__<config>]. */
(function () {
  'use strict';
  var h = Site.h;
  var ORDER = ['exact', 'native', 'd030', 'd030t12', 'd040t12', 'd050'];
  var SHORT = { exact: 'exact', native: 'native', d030: 'skip 0.3', d030t12: 'skip 0.3', d040t12: 'skip 0.4', d050: 'skip 0.5' };
  var SHORT_U = { exact: '', native: 'thinking on', d030: '', d030t12: '12 threads', d040t12: '12 threads', d050: '' };
  var CMP_COLS = 'minmax(130px, 1.4fr) minmax(150px, 1.3fr) 64px 124px 84px 92px 88px 64px';
  var RES_COLS = 'minmax(170px, 1.6fr) 70px 90px 96px 100px 100px 90px 72px';
  var REV_COLS = 'minmax(150px, 1fr) minmax(150px, 1fr) 120px 110px minmax(240px, 2.4fr) 110px';
  var WHAT = {
    exact: { colibri: 'Reads every expert the model routes to. The reference output.', ollama: 'Thinking off, temperature 0, 128 tokens. Comparable with Colibri runs.' },
    native: 'The model’s defaults: thinking on, one sample, up to 4,096 tokens.',
    d030: 'Skips experts with routing weight below 0.3 that are not in memory.', d050: 'Skips experts with routing weight below 0.5 that are not in memory.',
    d030t12: 'Skip 0.3 with 12 CPU threads instead of 2.', d040t12: 'Skip 0.4 with 12 CPU threads instead of 2.'
  };

  var D = { benches: [], labels: {}, cmp: [], ext: null, files: {} };
  var S = { bench: 'compare', tab: 'results', style: null, config: 'all', q: 'all', grade: 'all', answer: '', page: 0,
            cmpStyle: 'terse', sortKey: 'model', sortDir: 'asc', menuOpen: false };
  var focusTab = null;

  // ---------- helpers ----------
  function kindOf(c) { return c === 'exact' ? 'exact' : c === 'native' ? 'native' : 'lossy'; }
  function tagFor(c) {
    var k = kindOf(c);
    return { cls: k === 'exact' ? 'tag-exact' : k === 'native' ? 'tag-native' : 'tag-lossy',
             text: k === 'exact' ? 'exact' : k === 'native' ? 'thinking on, 4,096 tokens' : 'changes output' };
  }
  function tag(c, extra) { var t = tagFor(c); return h('span', { class: 'tag ' + t.cls, style: extra }, h('i'), t.text); }
  function label(c) { return D.labels[c] || c; }
  function fTok(v) { return v == null ? '—' : v >= 10 ? v.toFixed(1) : v.toFixed(2); }
  function fSec(v) { return v == null ? '—' : v >= 100 ? String(Math.round(v)) : v.toFixed(1); }
  function bench(n) { return D.benches.filter(function (b) { return b.name === n; })[0]; }
  function rowsOf(n) { return D.cmp.filter(function (r) { return r[0] === n; }); }
  function row(n, s, c) { return D.cmp.filter(function (r) { return r[0] === n && r[1] === s && r[2] === c; })[0]; }
  function stat(r) { return r ? r[3] + '/' + r[4] + ' correct, ' + fTok(r[7]) + ' tok/s, ' + fSec(r[5]) + ' s median answer' : 'not measured'; }
  function cfgOrder(a, b) { var i = ORDER.indexOf(a), j = ORDER.indexOf(b); return (i < 0 ? 99 : i) - (j < 0 ? 99 : j); }
  function styleOrder(a, b) { return a[1] < b[1] ? 1 : a[1] > b[1] ? -1 : 0; }   // terse before normal
  function isOllamaLike(b) { return b.engine !== 'Colibri'; }
  function groups() {
    var out = [];
    D.benches.forEach(function (b) { var g = out.filter(function (x) { return x.title === b.group; })[0]; if (!g) out.push(g = { title: b.group, items: [] }); g.items.push(b); });
    return out;
  }
  function sec(id, title, n, copyAria, copyHash, extra) {
    return h('div', { class: 'sec-h' }, h(n ? 'h2' : 'h3', { id: id }, n ? h('span', { class: 'n num', text: n }) : null, title),
      copyAria ? Site.copyButton(copyAria, copyHash) : null, extra || null);
  }
  function busy(text) { return h('aside', { class: 'cond', 'aria-label': 'Test conditions' }, h('strong', { class: 'sc', text: 'Busy machine' }), h('span', { text: text })); }
  function table(aria, minWidth, cols, headCells, rows, freeze) {
    return h('div', { class: 'tblbox' }, h('div', { class: 'bt' + (freeze === false ? '' : ' freeze'), role: 'table', 'aria-label': aria, style: { minWidth: minWidth + 'px' } },
      h('div', { class: 'bt-r bt-h', role: 'row', style: { gridTemplateColumns: cols } }, headCells),
      h('div', { role: 'rowgroup' }, rows)));
  }
  function th(t, u, cls) { return h('div', { class: 'bt-c' + (cls ? ' ' + cls : ''), role: 'columnheader' }, t, u ? h('span', { class: 'u', text: u }) : null); }
  function td(content, cls, role) { return h('div', { class: 'bt-c' + (cls ? ' ' + cls : ''), role: role || 'cell' }, content); }

  // ---------- URL ----------
  function parseHash() {
    var raw = location.hash.replace(/^#/, '');
    if (raw === 'answers') return { bench: 'v1', tab: 'answers' };
    if (raw === 'data') return { bench: 'v1', tab: 'method' };
    var p = {}; raw.split('&').forEach(function (kv) { var i = kv.indexOf('='); if (i > 0) p[decodeURIComponent(kv.slice(0, i))] = decodeURIComponent(kv.slice(i + 1)); });
    return p;
  }
  function fromHash() {
    var p = parseHash();
    S.bench = p.bench && (p.bench === 'compare' || bench(p.bench)) ? p.bench : 'compare';
    S.tab = ['results', 'review', 'answers', 'method'].indexOf(p.tab) >= 0 ? p.tab : 'results';
    S.answer = /^[\w-]+__(terse|normal)__[\w.-]+$/.test(p.answer || '') ? p.answer : '';
    S.style = ['terse', 'normal', 'both'].indexOf(p.style) >= 0 ? p.style : null;
    S.config = /^[\w.-]+$/.test(p.config || '') ? p.config : 'all';
    S.q = /^[\w-]+$/.test(p.q || '') ? p.q : 'all';
    S.grade = ['correct', 'incorrect', 'reviewed'].indexOf(p.grade) >= 0 ? p.grade : 'all';
    S.page = 0; S.menuOpen = false;
  }
  function aStyle() { return S.style || (S.answer ? S.answer.split('__')[1] : 'terse'); }
  function hashFor(kind) {
    if (S.bench === 'compare') return '#bench=compare';
    var x = '#bench=' + S.bench + '&tab=' + S.tab;
    if (S.tab === 'answers') {
      x += '&style=' + aStyle();
      ['config', 'q', 'grade'].forEach(function (k) { if (S[k] !== 'all') x += '&' + k + '=' + S[k]; });
      if (kind !== 'view' && S.answer) x += '&answer=' + S.answer;
    }
    return x;
  }
  function go(change, push) {
    Object.assign(S, change);
    var x = hashFor('answer');
    if (x !== location.hash) history[push ? 'pushState' : 'replaceState'](null, '', x);
    render();
  }
  function pickBench(n) {
    return function (e) { if (e) e.preventDefault(); go({ bench: n, tab: S.tab === 'review' ? 'results' : S.tab, answer: '', style: null, config: 'all', q: 'all', grade: 'all', page: 0, menuOpen: false }, true); window.scrollTo(0, document.querySelector('.bwrap').offsetTop - 12); };
  }

  // ---------- bench switcher ----------
  function drawSwitcher() {
    var nav = document.getElementById('bnav'), sel = document.getElementById('bsel');
    var exSpeed = function (b) { var ex = row(b.name, 'terse', 'exact'); return ex ? fTok(ex[7]) + ' tok/s' : ''; };
    Site.fill(nav, 
      h('ul', {}, h('li', {}, h('a', { href: '#bench=compare', 'aria-current': S.bench === 'compare' ? 'page' : null, onclick: pickBench('compare') },
        h('span', { text: 'Compare all benches' }), h('span', { class: 'meta', text: D.benches.length + ' benches' })))),
      groups().map(function (g) {
        return h('div', { style: { display: 'flex', flexDirection: 'column', gap: '4px' } }, h('h2', { text: g.title }),
          h('ul', {}, g.items.map(function (b) {
            return h('li', {}, h('a', { href: '#bench=' + b.name, 'aria-current': b.name === S.bench ? 'page' : null, onclick: pickBench(b.name) },
              h('span', { text: b.title }), h('span', { class: 'meta num' }, h('span', { class: 'sr', text: 'exact speed ' }), exSpeed(b))));
          })));
      }),
      h('p', { class: 'note', text: 'Speed: exact setting, terse answers. A new bench appears here when its data file is published.' }));
    var B = bench(S.bench);
    var listId = 'bsel-list';
    var btn = h('button', { type: 'button', class: 'btn', 'aria-expanded': String(S.menuOpen), 'aria-controls': listId, 'aria-describedby': 'bsel-l',
      style: { justifyContent: 'space-between', width: '100%', minHeight: '44px', fontSize: '16px' }, onclick: function () { S.menuOpen = !S.menuOpen; drawSwitcher(); } },
      h('span', { style: { display: 'flex', flexDirection: 'column', alignItems: 'flex-start', textAlign: 'left' } },
        h('strong', { style: { fontWeight: '600' }, text: B ? B.title : 'Compare all benches' }), h('span', { class: 'note', text: B ? B.group : D.benches.length + ' benches, side by side' })),
      h('span', { 'aria-hidden': 'true', text: S.menuOpen ? '▴' : '▾' }));
    var row2 = function (href, cur, text, meta, onclick, strong) {
      return h('a', { href: href, 'aria-current': cur ? 'page' : null, onclick: onclick,
        style: { padding: '10px 14px', minHeight: '44px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px', color: 'var(--fg)', textDecoration: 'none', background: cur ? 'var(--tint)' : 'transparent', fontWeight: strong ? '600' : null } },
        h('span', { text: text }), meta ? h('span', { class: 'note num', text: meta }) : null);
    };
    Site.fill(sel, h('span', { class: 'note', id: 'bsel-l', text: 'Bench' }), btn,
      S.menuOpen ? h('div', { id: listId, style: { border: '1px solid var(--fg)', borderTop: '0', padding: '8px 0', display: 'flex', flexDirection: 'column', gap: '10px' } },
        row2('#bench=compare', S.bench === 'compare', 'Compare all benches', '', pickBench('compare'), true),
        groups().map(function (g) {
          return h('div', { style: { display: 'flex', flexDirection: 'column' } }, h('span', { class: 'sc note', style: { padding: '4px 14px', borderTop: '1px solid var(--hair)' }, text: g.title }),
            g.items.map(function (b) { return row2('#bench=' + b.name, b.name === S.bench, b.title, exSpeed(b), pickBench(b.name)); }));
        })) : null);
  }

  // ---------- compare ----------
  function drawCompare(box) {
    var e4b = 'gemma4-e4b-ollama', g26 = 'gemma4-26b-ollama', g31 = 'gemma4-31b-ollama', q = 'qwen38-27b-ollama';
    var R = function (n, s, c) { return row(n, s, c); };
    var e4t = R(e4b, 'terse', 'exact'), e4n = R(e4b, 'normal', 'native'), g26n = R(g26, 'normal', 'native'), g31n = R(g31, 'normal', 'native');
    var v1t = R('v1', 'terse', 'exact'), v1n = R('v1', 'normal', 'exact'), iq2 = R('glm-5.3-iq2m', 'normal', 'exact');
    var qn = R(q, 'normal', 'native'), qt = R(q, 'terse', 'exact'), qtn = R(q, 'terse', 'native'), qx = R(q, 'normal', 'exact');
    var sc = function (r) { return r ? r[3] + '/' + r[4] : '—'; };
    var recs = [
      e4t && { need: 'Fast everyday answers', pick: 'Gemma 4 E4B · terse · thinking off', lossy: false,
        text: stat(e4t) + (e4n ? '. Its native normal setting scored ' + sc(e4n) + ' at ' + fTok(e4n[7]) + ' tok/s, ' + fSec(e4n[5]) + ' s median.' : '.') },
      g26n && { need: 'Best Gemma score with normal-length answers', pick: 'Gemma 4 26B · native', lossy: false,
        text: stat(g26n) + (g31n ? '. The 31B model scored ' + sc(g31n) + ' and took ' + fSec(g31n[5]) + ' s median; this test gives no reason to prefer it.' : '.') },
      R('v1', 'terse', 'd030t12') && { need: 'GLM everyday setting (the owner’s choice)', pick: 'GLM-5.3 int4 · terse · skip 0.3 · 12 threads', lossy: true,
        text: stat(R('v1', 'terse', 'd030t12')) + (v1t ? '. Exact, the reference, also scored ' + sc(v1t) + ' at ' + fTok(v1t[7]) + ' tok/s, ' + fSec(v1t[5]) + ' s median: short answers are dominated by reading the prompt, so faster generation saves little waiting.' : '.') },
      R('glm-5.3-mtp', 'normal', 'd030t12') && { need: 'GLM with normal-length answers', pick: 'int4 + MTP head · skip 0.3 · 12 threads', lossy: true,
        text: stat(R('glm-5.3-mtp', 'normal', 'd030t12')) + ', against ' + stat(v1n) + ' for exact.' + (iq2 ? ' The 2-bit IQ2_M exact run scored best (' + sc(iq2) + ') but took ' + fSec(iq2[5]) + ' s median.' : '') + ' No single GLM setting wins on both.' }
    ].filter(Boolean);
    var qwen = qn && qt && qtn && qx ? 'Qwen3.8-27B (Ollama’s qwen3.8:27b-mlx). Native normal answers: ' + stat(qn) + ', ' + (qn[9] ? qn[9] + ' cut off' : 'no answer cut off') +
      (g26n ? '. That matches Gemma 4 26B’s score, which answered in ' + fSec(g26n[5]) + ' s median at ' + fTok(g26n[7]) + ' tok/s' : '') + '. Terse with thinking off: ' + stat(qt) +
      (e4t ? '; Gemma 4 E4B matched that score at ' + fSec(e4t[5]) + ' s' : '') + '. Native terse: ' + sc(qtn) + ' at ' + fTok(qtn[7]) + ' tok/s. Normal short-budget answers scored ' + sc(qx) +
      ' but ' + qx[9] + ' of 24 were cut off, so that is not a clean measure. On this small prompt set Qwen shows no speed or score advantage over the recommended Gemma settings.' : null;

    Site.put(box, 
      h('section', { class: 'sec', 'aria-labelledby': 'c-use' }, sec('c-use', 'Which should I use?', null, 'Copy link to the comparison', '#bench=compare'),
        h('div', { style: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(300px, 100%), 1fr))', gap: '0 32px', borderTop: '2px solid var(--rule)', borderBottom: '2px solid var(--rule)' } },
          recs.map(function (r) {
            return h('div', { style: { padding: '14px 0', borderBottom: '1px solid var(--hair)', display: 'flex', flexDirection: 'column', gap: '4px' } },
              h('span', { class: 'sc note', text: r.need }),
              h('p', { style: { fontSize: '18px', lineHeight: '26px', fontWeight: '600', display: 'flex', flexWrap: 'wrap', gap: '4px 10px', alignItems: 'baseline' } },
                h('span', { text: r.pick }), r.lossy ? h('span', { class: 'tag tag-lossy', style: { fontWeight: '400' } }, h('i'), 'changes output') : null),
              h('p', { style: { fontSize: '15px', lineHeight: '24px' }, text: r.text }));
          }))),
      qwen ? h('section', { class: 'sec', 'aria-labelledby': 'c-qwen', style: { maxWidth: '760px' } }, sec('c-qwen', 'Where Qwen fits'), h('p', { style: { fontSize: '16px', lineHeight: '26px' }, text: qwen })) : null,
      h('section', { class: 'sec', 'aria-labelledby': 'c-read', style: { maxWidth: '760px' } }, sec('c-read', 'How to read this'),
        h('ul', { style: { paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '15px', lineHeight: '24px' } },
          h('li', { text: '24 fixed questions, graded automatically: a smoke test, not a general intelligence ranking. Terse and normal ask the same questions with different instructions; they are not independent repeats.' }),
          h('li', { text: 'Speed is the mean generation rate per answer. Median answer time includes reading the prompt and excludes loading the model. Single runs; no confidence intervals.' }),
          h('li', {}, 'Ollama ', h('em', { text: 'exact' }), ': thinking off, temperature 0, 128 tokens, comparable with Colibri. ', h('em', { text: 'Native' }), ': the model’s defaults with thinking on and up to 4,096 tokens, one sample.'),
          h('li', {}, 'Colibri ', h('em', { text: 'skip' }), ' settings skip experts below a weight threshold: they always change output. Quantized formats (IQ3, IQ2) also change weights.')),
        busy('Times come from the owner’s everyday Mac with other apps running, not a controlled machine; real performance may be better. Compare settings within one bench before comparing benches.')),
      figure1(),
      table1(),
      externalScores());
    placeBadges();
  }

  // Figure 1: correct (of 24, from 12) against generation speed (log), terse and normal panels; under 12 in a strip.
  var X0 = Math.log10(0.1), X1 = Math.log10(200), Y0 = 12, Y1 = 24;
  function xp(v) { return Math.max(0, Math.min(100, (Math.log10(Math.max(v || 0.1, 0.1)) - X0) / (X1 - X0) * 100)); }
  function cnt(r) { return r[3] / r[4] * 24; }
  function yp(r) { return (cnt(r) - Y0) / (Y1 - Y0) * 100; }
  function ptCls(r) { var k = kindOf(r[2]); return k === 'exact' ? 'ex' : k === 'native' ? 'na' : 'ls'; }
  function figure1() {
    var num = {}; D.benches.forEach(function (b, i) { num[b.name] = i + 1; });
    var tFull = D.cmp.filter(function (r) { return r[1] === 'terse' && r[3] === r[4]; }).length, tAll = D.cmp.filter(function (r) { return r[1] === 'terse'; }).length;
    var panels = [['terse', 'Terse answers'], ['normal', 'Normal answers']].map(function (s) {
      var rows = D.cmp.filter(function (r) { return r[1] === s[0]; });
      var inPlot = rows.filter(function (r) { return cnt(r) >= Y0; }), outs = rows.filter(function (r) { return cnt(r) < Y0; });
      var full = rows.filter(function (r) { return r[3] === r[4]; }).length;
      var alt = s[1] + ': ' + rows.length + ' points; ' + full + ' answered all 24 correctly' +
        (outs.length ? '; under 12 correct: ' + outs.map(function (r) { return bench(r[0]).title + ' ' + label(r[2]) + ' ' + r[3] + '/' + r[4]; }).join(', ') : '') + '. Every value is in Table 1.';
      var best = D.benches.map(function (b) {
        var r = inPlot.filter(function (x) { return x[0] === b.name; }).sort(function (a, c) { return (cnt(c) - cnt(a)) || (c[7] - a[7]); })[0];
        return r ? { n: num[b.name], r: r } : null;
      }).filter(Boolean);
      var plot = h('div', { class: 'plot', style: { height: '300px' } },
        [12, 15, 18, 21, 24].map(function (v) { var pos = ((v - Y0) / (Y1 - Y0) * 100).toFixed(2) + '%'; return [h('span', { class: 'gl', style: { bottom: pos } }), h('span', { class: 'yl', style: { bottom: pos }, text: String(v) })]; }),
        inPlot.map(function (r) { return h('span', { class: 'pt ' + ptCls(r), style: { left: xp(r[7]) + '%', bottom: yp(r) + '%' } }); }));
      plot._badges = best;
      var strip = h('div', { class: 'plot-out', style: { height: '30px' } }, h('span', { class: 'yl', text: '<12' }),
        outs.map(function (r) {
          return [h('span', { class: 'pt ' + ptCls(r), style: { left: xp(r[7]) + '%', bottom: '15px' } }),
                  h('span', { class: 'out-lab num', style: { left: xp(r[7]) + '%' } }, h('span', { class: 'badge', text: String(num[r[0]]) }), r[3] + '/' + r[4])];
        }),
        [[0.1, '0.1'], [1, '1'], [10, '10'], [100, '100']].map(function (t) { return h('span', { class: 'xl', style: { left: xp(t[0]) + '%' }, text: t[1] }); }));
      return h('div', { style: { display: 'flex', flexDirection: 'column', gap: '8px' } },
        h('h3', { class: 'sc', style: { fontSize: '15px', lineHeight: '20px', fontWeight: '700' }, text: s[1] }),
        h('div', { role: 'img', 'aria-label': alt, style: { margin: '40px 0 0 44px' } }, plot, strip));
    });
    return h('section', { class: 'sec', 'aria-labelledby': 'c-fig' }, sec('c-fig', 'Correct answers against speed', '1'),
      h('p', { style: { maxWidth: '760px', fontSize: '16px', lineHeight: '26px' }, text: 'With terse answers, ' + tFull + ' of ' + tAll + ' settings answered all 24 questions correctly, so the choice there is about speed. Normal-length answers separate the models more, and cut-off answers pull scores down.' }),
      h('div', { class: 'legend' },
        h('span', {}, h('i', { style: { background: 'var(--fg)', borderRadius: '50%' } }), 'exact'),
        h('span', {}, h('i', { class: 'hatch' }), 'skip setting, changes output'),
        h('span', {}, h('i', { style: { boxShadow: 'inset 0 0 0 2px var(--fg)', borderRadius: '50%' } }), 'Ollama native (thinking on, 4,096 tokens)'),
        h('span', {}, h('span', { class: 'badge', text: '1' }), 'model, see key')),
      h('figure', { class: 'fig' },
        h('div', { style: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(380px, 100%), 1fr))', gap: '32px 40px' } }, panels),
        h('p', { class: 'note', style: { textAlign: 'center', paddingTop: '18px' }, text: 'Horizontal: generation speed, tokens per second, log scale · vertical: answers graded correct, of 24 · below the line: under 12' }),
        h('ol', { class: 'fkey', 'aria-label': 'Model key' }, D.benches.map(function (b, i) {
          return h('li', {}, h('span', { class: 'badge', text: String(i + 1) }), h('span', { text: b.title }), h('span', { class: 'note', text: b.engine }));
        })),
        h('figcaption', { class: 'cap' }, h('b', { text: 'Figure 1.' }), ' One point per model, setting and answer style; the number marks each model’s best point (most correct, then fastest). GLM-5.3 on Colibri stays below 2 tok/s because experts are read from the SSD; the Ollama models run fully in RAM. Every point is listed in Table 1.')));
  }
  /* Number badges next to each model's best point, placed at the real plot size so none covers a point or another badge.
     Candidates go sideways first, then upward into the margin above the top line; the least-overlapping one wins otherwise. */
  function placeBadges() {
    document.querySelectorAll('.plot').forEach(function (plot) {
      if (!plot._badges) return;
      plot.querySelectorAll('.pbadge').forEach(function (b) { b.remove(); });
      var W = plot.clientWidth, H = plot.clientHeight, BW = 17, BH = 17, PAD = 2;
      var boxes = [];
      plot.querySelectorAll('.pt').forEach(function (p) {
        var x = parseFloat(p.style.left) / 100 * W, y = (1 - parseFloat(p.style.bottom) / 100) * H;
        boxes.push([x - 6, y - 6, 12, 12]);
      });
      var tries = [];
      [[12, 0], [-12, 0], [0, -14], [12, -14], [-12, -14], [24, 0], [-24, 0], [0, 14], [12, 14], [-12, 14], [0, -28], [14, -28], [-14, -28], [28, -14], [-28, -14],
       [0, -42], [16, -42], [-16, -42], [36, 0], [-36, 0], [0, 28], [30, -28], [-30, -28]].forEach(function (t) { tries.push(t); });
      function overlap(a, b) { var w = Math.min(a[0] + a[2], b[0] + b[2]) - Math.max(a[0], b[0]), hh = Math.min(a[1] + a[3], b[1] + b[3]) - Math.max(a[1], b[1]); return w > 0 && hh > 0 ? w * hh : 0; }
      plot._badges.forEach(function (bd) {
        var cx = xp(bd.r[7]) / 100 * W, cy = (1 - yp(bd.r) / 100) * H, bestT = null, bestCost = Infinity;
        for (var i = 0; i < tries.length; i++) {
          var bx = cx + tries[i][0] - BW / 2, by = cy + tries[i][1] - BH / 2;
          if (bx < 0 || bx + BW > W + 4 || by < -44 || by + BH > H) continue;
          var box = [bx - PAD, by - PAD, BW + 2 * PAD, BH + 2 * PAD], cost = 0;
          boxes.forEach(function (q) { cost += overlap(box, q); });
          if (cost === 0) { bestT = tries[i]; bestCost = 0; break; }
          if (cost < bestCost) { bestCost = cost; bestT = tries[i]; }
        }
        bestT = bestT || [12, 0];
        var bx2 = cx + bestT[0] - BW / 2, by2 = cy + bestT[1] - BH / 2;
        boxes.push([bx2, by2, BW, BH]);
        plot.appendChild(h('span', { class: 'badge pbadge', 'aria-hidden': 'true', style: { left: bx2 + 'px', top: by2 + 'px' }, text: String(bd.n) }));
      });
    });
  }
  var resizeTimer;
  window.addEventListener('resize', function () { clearTimeout(resizeTimer); resizeTimer = setTimeout(placeBadges, 120); });

  function table1() {
    var cs = S.cmpStyle, sk = S.sortKey, sd = S.sortDir;
    var shown = D.cmp.filter(function (r) { return cs === 'both' || r[1] === cs; });
    var order = D.benches.map(function (b) { return b.name; });
    var keyFns = { correct: function (r) { return r[3] / r[4]; }, tok: function (r) { return r[7]; }, ans: function (r) { return r[5]; }, cpm: function (r) { return r[8]; } };
    shown = shown.slice().sort(function (a, b) {
      if (!keyFns[sk]) return (order.indexOf(a[0]) - order.indexOf(b[0])) || styleOrder(a, b) || cfgOrder(a[2], b[2]);
      var d = keyFns[sk](a) - keyFns[sk](b);
      return sd === 'asc' ? d : -d;
    });
    function bestOf(fn, max) { var vs = shown.map(fn); return max ? Math.max.apply(null, vs) : Math.min.apply(null, vs); }
    var bc = bestOf(keyFns.correct, true), bt = bestOf(keyFns.tok, true), ba = bestOf(keyFns.ans, false), bp = bestOf(keyFns.cpm, true);
    function head(id, t, u, cls) {
      if (!id) return th(t, u, cls);
      var cur = sk === id;
      return h('div', { class: 'bt-c' + (cls ? ' ' + cls : ''), role: 'columnheader', 'aria-sort': cur ? (sd === 'asc' ? 'ascending' : 'descending') : 'none' },
        h('button', { type: 'button', class: 'sortb', onclick: function () { S.sortDir = cur ? (sd === 'asc' ? 'desc' : 'asc') : (id === 'model' || id === 'ans' ? 'asc' : 'desc'); S.sortKey = id; redrawTable1(); } },
          h('span', {}, t, h('span', { class: 'arrow', 'aria-hidden': 'true', text: cur ? (sd === 'asc' ? ' ▲' : ' ▼') : '' })), h('span', { class: 'u', text: u })));
    }
    var prev = null;
    var rows = shown.map(function (r) {
      var b = bench(r[0]), first = sk !== 'model' || r[0] !== prev; prev = r[0];
      return h('div', { class: 'bt-r ' + (sk === 'model' ? (first ? 'grp-top grp' : '') : 'grp'), role: 'row', style: { gridTemplateColumns: CMP_COLS } },
        td(first ? [h('a', { href: '#bench=' + b.name, onclick: pickBench(b.name), style: { fontWeight: '600', color: 'var(--fg)' }, text: b.title }), h('span', { class: 'note', style: { display: 'block' }, text: b.engine })] : null, '', 'rowheader'),
        td(h('span', { style: { display: 'flex', flexDirection: 'column', gap: '2px' } }, h('span', { text: label(r[2]) }), tag(r[2]))),
        td(r[1]),
        td([r[3] + '/' + r[4], h('span', { class: 'mini', 'aria-hidden': 'true' }, h('b', { style: { width: (r[3] / r[4] * 100).toFixed(1) + '%' } }))], 'n' + (r[3] / r[4] === bc ? ' best' : '')),
        td(fTok(r[7]), 'n' + (r[7] === bt ? ' best' : '')), td(fSec(r[5]), 'n' + (r[5] === ba ? ' best' : '')),
        td(r[8].toFixed(2), 'n' + (r[8] === bp ? ' best' : '')), td(r[9] ? String(r[9]) : '—', 'n'));
    });
    var seg = h('div', { class: 'seg', role: 'group', 'aria-label': 'Answer style shown' }, ['terse', 'normal', 'both'].map(function (v) {
      return h('button', { type: 'button', 'aria-pressed': String(cs === v), onclick: function () { S.cmpStyle = v; redrawTable1(); }, text: v[0].toUpperCase() + v.slice(1) });
    }));
    return h('section', { class: 'sec', 'aria-labelledby': 'c-tbl', id: 'table1' }, sec('c-tbl', 'Every model and setting', '2'),
      h('div', { style: { display: 'flex', flexWrap: 'wrap', gap: '10px 20px', alignItems: 'center' } }, seg, h('span', { class: 'note num', text: shown.length + ' of ' + D.cmp.length + ' rows' })),
      table('Table 1. Every model, setting and answer style', 860, CMP_COLS,
        [head('model', 'Model', 'engine'), th('Setting'), th('Style'), head('correct', 'Correct', 'of graded', 'n'), head('tok', 'Speed', 'tok/s, mean', 'n'),
         head('ans', 'Answer time', 's, median', 'n'), head('cpm', 'Correct', 'per minute', 'n'), th('Cut off', 'answers', 'n')], rows),
      h('p', { class: 'cap' }, h('b', { text: 'Table 1.' }), ' Bold: best in the rows shown. Correct is out of the graded answers (24). Cut off: answers that hit the output budget before finishing; their grade says little about the model. Lossy settings carry the hatched tag.'));
  }
  function redrawTable1() { var old = document.getElementById('table1'); if (old) old.replaceWith(table1()); }

  function externalScores() {
    var E = D.ext;
    if (!E || !E.rows || !E.rows.length) return null;
    return h('section', { class: 'reported', 'aria-labelledby': 'c-ext', style: { maxWidth: '760px' } },
      h('h2', { id: 'c-ext', class: 'h-small' }, 'Published intelligence scores ', h('span', { style: { fontWeight: '400', color: 'var(--fg-2)' }, text: '· reported by others, not measured here' })),
      E.rows.map(function (e) {
        return h('div', { class: 'hbar' }, h('span', { class: 'lab', text: e.model }),
          h('span', { class: 'track', 'aria-hidden': 'true' }, h('b', { style: { width: (e.score / 60 * 100).toFixed(1) + '%', boxShadow: 'inset 0 0 0 1px var(--fg)', background: 'var(--tint)' } })),
          h('span', { class: 'num', style: { textAlign: 'right' }, text: String(e.score) }));
      }),
      h('p', { class: 'note' }, h('a', { href: E.source, text: E.name + ' ' + E.version }), ', fetched ' + E.fetched + '. Scores describe the full models as served by their makers, not the int4 or quantized copies benched on this Mac, whose quality can be lower. Context only; the tables above are this lab’s own measure.'));
  }

  // ---------- one bench ----------
  function loadBench(B) {
    if (D.files[B.name]) return Promise.resolve(D.files[B.name]);
    return Site.getJSON('data/' + B.file).then(function (f) {
      var ans = {}, prompts = {};
      (f.answers || []).forEach(function (a) { ans[a.id + '__' + a.style + '__' + a.config] = a; prompts[a.id] = prompts[a.id] || [a.kind, a.prompt]; });
      var ids = Object.keys(prompts).sort();
      var cfgs = []; (f.answers || []).forEach(function (a) { if (cfgs.indexOf(a.config) < 0) cfgs.push(a.config); }); cfgs.sort(cfgOrder);
      var reviewed = f.review || {};
      return (D.files[B.name] = { raw: f, ans: ans, prompts: prompts, ids: ids, cfgs: cfgs, review: reviewed, notes: f.review_notes || [], styles: f.prompt_styles || {} });
    });
  }
  function drawBench(box, B) {
    var F = D.files[B.name];
    if (!F) {
      Site.put(box, h('p', { class: 'note', text: 'Loading ' + B.title + '…' }));
      loadBench(B).then(render, function (e) { Site.fill(box, h('p', { role: 'alert', text: 'Could not load data/' + B.file + ': ' + e.message })); });
      return;
    }
    var hasReview = Object.keys(F.review).length > 0;
    if (S.tab === 'review' && !hasReview) S.tab = 'results';
    var isO = isOllamaLike(B);
    var version = B.colibri_commit ? B.colibri_commit.slice(0, 8) : (B.ollama_version || '').replace(/^ollama version is\s*/, 'Ollama ');
    var metaLine = (isO ? B.engine + ' · ' + B.model + (version ? ' · ' + version : '') : 'Colibri · commit ' + version + ' · ' + B.sub) + ' · ' + B.answers + ' answers · ' + F.ids.length + ' questions';
    var tabs = [['results', 'Results', ''], ['review', 'Manual review', hasReview ? String(Object.keys(F.review).length) : ''], ['answers', 'Answers', String(B.answers)], ['method', 'Method and data', '']]
      .filter(function (t) { return t[0] !== 'review' || hasReview; });
    var ids = tabs.map(function (t) { return t[0]; });
    var tablist = h('div', { class: 'tabs', role: 'tablist', 'aria-label': 'Bench sections' }, tabs.map(function (t) {
      return h('button', { type: 'button', role: 'tab', class: 'tab', id: 'tab-' + t[0], 'aria-selected': String(t[0] === S.tab), 'aria-controls': 'panel', tabindex: t[0] === S.tab ? '0' : '-1',
        onclick: function () { go({ tab: t[0] }, true); },
        onkeydown: function (e) {
          var i = ids.indexOf(S.tab), j;
          if (e.key === 'ArrowRight') j = (i + 1) % ids.length; else if (e.key === 'ArrowLeft') j = (i - 1 + ids.length) % ids.length;
          else if (e.key === 'Home') j = 0; else if (e.key === 'End') j = ids.length - 1; else return;
          e.preventDefault(); focusTab = 'tab-' + ids[j]; go({ tab: ids[j] }, true);
        } }, t[1], t[2] ? h('span', { class: 'cnt num', text: t[2] }) : null);
    }));
    var panel = h('div', { id: 'panel', role: 'tabpanel', 'aria-labelledby': 'tab-' + S.tab, tabindex: '0', style: { display: 'flex', flexDirection: 'column', gap: '22px' } });
    Site.put(box, h('div', { style: { display: 'flex', flexDirection: 'column', gap: '4px' } },
      h('p', { class: 'sc note', text: B.group }),
      h('div', { class: 'sec-h' }, h('h2', { style: { fontSize: '28px', lineHeight: '34px' }, text: B.title }), Site.copyButton('Copy link to this bench', function () { return '#bench=' + B.name + '&tab=' + S.tab; })),
      h('p', { class: 'note num', text: metaLine })), tablist, panel);
    if (S.tab === 'results') drawResults(panel, B, isO);
    else if (S.tab === 'review') drawReview(panel, B, F);
    else if (S.tab === 'answers') drawAnswers(panel, B, F, isO);
    else drawMethod(panel, B, F, isO, version, hasReview);
  }

  function drawResults(panel, B, isO) {
    var rr = rowsOf(B.name).slice().sort(function (a, b) { return styleOrder(a, b) || cfgOrder(a[2], b[2]); });
    function best(fn, max) { var vs = rr.map(fn); return max ? Math.max.apply(null, vs) : Math.min.apply(null, vs); }
    var bc = best(function (r) { return r[3] / r[4]; }, true), bt = best(function (r) { return r[7]; }, true), ba = best(function (r) { return r[5]; }, false), bp = best(function (r) { return r[8]; }, true);
    var last = null;
    var rows = rr.map(function (r) {
      var grp = r[1] !== last; last = r[1];
      return h('div', { class: 'bt-r ' + (grp ? 'grp-top grp' : ''), role: 'row', style: { gridTemplateColumns: RES_COLS } },
        td(h('span', { style: { display: 'flex', flexDirection: 'column', gap: '2px' } }, h('span', { text: label(r[2]) }), tag(r[2])), '', 'rowheader'),
        td(r[1]), td(r[3] + '/' + r[4], 'n' + (r[3] / r[4] === bc ? ' best' : '')), td(fTok(r[7]), 'n' + (r[7] === bt ? ' best' : '')),
        td(fSec(r[5]), 'n' + (r[5] === ba ? ' best' : '')), td(fSec(r[6]), 'n'), td(r[8].toFixed(2), 'n' + (r[8] === bp ? ' best' : '')), td(r[9] ? String(r[9]) : '—', 'n'));
    });
    var maxAns = Math.max.apply(null, rr.map(function (r) { return r[5]; }));
    function share(s) {
      var v = rr.filter(function (r) { return r[1] === s; }).map(function (r) { return Math.min(r[6], r[5]) / r[5] * 100; });
      return v.length ? Math.round(Math.min.apply(null, v)) + '–' + Math.round(Math.max.apply(null, v)) + '%' : '—';
    }
    var tEx = row(B.name, 'terse', 'exact');
    var lead = 'Reading the prompt takes ' + share('terse') + ' of the median terse answer in this bench' + (tEx ? ' (exact: ' + fSec(Math.min(tEx[6], tEx[5])) + ' of ' + fSec(tEx[5]) + ' s)' : '') +
      ', and ' + share('normal') + ' of a normal one. ' + (isO ? 'Generation dominates here; thinking and longer answers are what cost time.' : 'For short answers, a faster generation setting saves little time.');
    Site.put(panel, h('div', { style: { display: 'flex', flexDirection: 'column', gap: '26px' } },
      busy('Answer times were measured on the owner’s everyday Mac with other apps running. Compare settings within this bench; real performance may be better.'),
      table('Table 2. Results per setting and answer style', 780, RES_COLS,
        [th('Setting'), th('Style'), th('Correct', 'of graded', 'n'), th('Speed', 'tok/s, mean', 'n'), th('Answer time', 's, median', 'n'), th('Prompt read', 's, median', 'n'), th('Correct', 'per minute', 'n'), th('Cut off', 'answers', 'n')], rows),
      h('p', { class: 'cap' }, h('b', { text: 'Table 2.' }), ' ' + B.title + ', one row per setting and answer style. Bold: best in this bench. ', h('a', { href: '#bench=compare', onclick: pickBench('compare'), text: 'Compare with the other benches' }), '.'),
      h('figure', { class: 'fig' },
        h('p', { style: { maxWidth: '760px', fontSize: '16px', lineHeight: '26px' }, text: lead }),
        h('div', { class: 'legend' }, h('span', {}, h('i', { class: 'seg-read' }), 'reading the prompt'), h('span', {}, h('i', { style: { background: 'var(--fg)' } }), 'generating, exact'),
          h('span', {}, h('i', { class: 'hatch' }), 'generating, changes output'), h('span', {}, h('i', { style: { boxShadow: 'inset 0 0 0 1.5px var(--fg)' } }), 'generating, Ollama native')),
        h('div', { style: { display: 'flex', flexDirection: 'column', gap: '18px' } }, ['terse', 'normal'].map(function (s) {
          return h('div', { style: { display: 'flex', flexDirection: 'column', gap: '6px' } }, h('h3', { class: 'sc', style: { fontSize: '15px', lineHeight: '20px', fontWeight: '700' }, text: s === 'terse' ? 'Terse answers' : 'Normal answers' }),
            rr.filter(function (r) { return r[1] === s; }).map(function (r) {
              var k = kindOf(r[2]), pre = Math.min(r[6], r[5]), gen = Math.max(0, r[5] - pre);
              return h('div', { class: 'hbar hbar-2' }, h('span', { class: 'lab', text: label(r[2]) }),
                h('span', { class: 'track', 'aria-hidden': 'true' }, h('b', { class: 'seg-read', style: { width: (pre / maxAns * 100).toFixed(1) + '%' } }),
                  h('b', { class: k === 'exact' ? 'solid' : k === 'native' ? 'outl' : 'hatch', style: { left: (pre / maxAns * 100).toFixed(1) + '%', width: (gen / maxAns * 100).toFixed(1) + '%' } })),
                h('span', { class: 'num', style: { textAlign: 'right' } }, fSec(r[5]) + ' s', h('span', { class: 'note', style: { display: 'block' }, text: fSec(pre) + ' s reading' })),
                h('span', { class: 'sr', text: label(r[2]) + ', ' + s + ': ' + fSec(r[5]) + ' s median answer, of which about ' + fSec(pre) + ' s reading the prompt' }));
            }));
        })),
        h('figcaption', { class: 'cap' }, h('b', { text: 'Figure 2.' }), ' Median time to a full answer, in seconds, split into the median time reading the prompt and the rest (generating the answer). Medians are taken separately, so the split is approximate. Values are in Table 2.'))));
  }

  function openAnswer(key, F) {
    return function (e) { if (e) e.preventDefault(); var id = key.split('__')[0]; go({ tab: 'answers', answer: key, style: key.split('__')[1], config: 'all', q: 'all', grade: 'all', page: Math.max(0, Math.floor(F.ids.indexOf(id) / 20)) }, true); };
  }
  function drawReview(panel, B, F) {
    var keys = Object.keys(F.review);
    Site.put(panel, h('div', { style: { display: 'flex', flexDirection: 'column', gap: '16px' } },
      h('p', { style: { maxWidth: '760px', fontSize: '16px', lineHeight: '26px' }, text: 'A person read the answers where the automatic grade looked doubtful. ' + keys.length + ' answers were checked; where the review disagrees with the grader, the review is the better guide.' }),
      table('Manual review', 820, REV_COLS, [th('Question'), th('Style · setting'), th('Grader'), th('Review'), th('Why'), th(h('span', { class: 'sr', text: 'Answer' }))],
        keys.map(function (k) {
          var p = k.split('__'), a = F.ans[k], r = F.review[k];
          return h('div', { class: 'bt-r grp', role: 'row', style: { gridTemplateColumns: REV_COLS } },
            td(p[0], 'mono', 'rowheader'), td(p[1] + ' · ' + label(p[2])), td(a ? (a.correct === true ? '✓ correct' : a.correct === false ? '✗ incorrect' : 'not graded') : '—'),
            h('div', { class: 'bt-c', role: 'cell', style: { fontWeight: '600' }, text: r.reviewed || r.verdict || '' }), h('div', { class: 'bt-c', role: 'cell', style: { whiteSpace: 'normal' }, text: r.why || r.note || '' }),
            td(h('a', { href: '#bench=' + B.name + '&tab=answers&answer=' + k, onclick: openAnswer(k, F), text: 'Open answer' })));
        })),
      F.notes.map(function (t) { return h('p', { class: 'note', style: { maxWidth: '760px' }, text: t }); })));
  }

  function drawAnswers(panel, B, F, isO) {
    var st = aStyle(), styles = st === 'both' ? ['terse', 'normal'] : [st];
    if (S.config !== 'all' && F.cfgs.indexOf(S.config) < 0) S.config = 'all';
    if (S.q !== 'all' && !F.prompts[S.q]) S.q = 'all';
    var cols = S.config === 'all' ? F.cfgs : [S.config];
    var rev = F.review;
    function matches(a, key) {
      if (!a) return false;
      if (S.grade === 'correct') return a.correct === true;
      if (S.grade === 'incorrect') return a.correct === false;
      if (S.grade === 'reviewed') return !!rev[key];
      return true;
    }
    var qids = F.ids.filter(function (id) { return S.q === 'all' || id === S.q; });
    if (S.grade !== 'all') qids = qids.filter(function (id) { return styles.some(function (s) { return cols.some(function (c) { var k = id + '__' + s + '__' + c; return matches(F.ans[k], k); }); }); });
    var pages = Math.max(1, Math.ceil(qids.length / 20)), page = Math.min(S.page || 0, pages - 1);
    if (S.answer && qids.indexOf(S.answer.split('__')[0]) >= 0) page = Math.floor(qids.indexOf(S.answer.split('__')[0]) / 20);
    S.page = page;
    var pageIds = qids.slice(page * 20, page * 20 + 20);
    var nCols = styles.length * cols.length, AX = 'minmax(150px, 1.4fr) repeat(' + nCols + ', minmax(66px, 1fr))';
    function setF(k) { return function (e) { var c = {}; c[k] = e.target.value; c.page = 0; c.answer = ''; go(c, false); }; }
    function select(id, lab, value, opts, onchange) {
      return h('div', { class: 'fld' }, h('label', { for: id, text: lab }),
        h('select', { id: id, onchange: onchange }, opts.map(function (o) { return h('option', { value: o[0], selected: o[0] === value ? true : null, text: o[1] }); })));
    }
    var cfgOpts = [['all', 'All settings']].concat(F.cfgs.map(function (c) { return [c, c === 'exact' && isO ? 'exact (thinking off)' : label(c)]; }));
    var qOpts = [['all', 'All ' + F.ids.length + ' questions']].concat(F.ids.map(function (id) { return [id, id]; }));
    var filters = h('div', { class: 'filters', role: 'group', 'aria-label': 'Filter answers' },
      h('div', { class: 'fld' }, h('span', { class: 'lbl', id: 'f-style-l', text: 'Style' }),
        h('div', { class: 'seg', role: 'group', 'aria-labelledby': 'f-style-l' }, ['terse', 'normal', 'both'].map(function (v) {
          return h('button', { type: 'button', 'aria-pressed': String(st === v), onclick: function () { go({ style: v, page: 0, answer: '' }, false); }, text: v[0].toUpperCase() + v.slice(1) });
        }))),
      select('f-config', 'Setting', S.config, cfgOpts, setF('config')),
      select('f-q', 'Question', S.q, qOpts, setF('q')),
      select('f-grade', 'Grade', S.grade, [['all', 'All grades'], ['correct', 'Correct'], ['incorrect', 'Incorrect'], ['reviewed', 'Reviewed by a person']], setF('grade')),
      h('button', { type: 'button', class: 'btn', disabled: S.config === 'all' && S.q === 'all' && S.grade === 'all' ? true : null, onclick: function () { go({ config: 'all', q: 'all', grade: 'all', page: 0, answer: '' }, false); }, text: 'Reset' }));
    var headStyle = h('div', { class: 'bt-r bt-h', role: 'row', style: { gridTemplateColumns: AX, borderBottom: '1px solid var(--hair)' } },
      h('div', { class: 'bt-c', role: 'columnheader' }, h('span', { class: 'sr', text: 'Question' })),
      styles.map(function (s) { return h('div', { class: 'bt-c', role: 'columnheader', style: { gridColumn: 'span ' + cols.length, textAlign: 'center', borderLeft: '1px solid var(--hair)' }, text: s === 'terse' ? 'Terse answers' : 'Normal answers' }); }));
    var headCols = h('div', { class: 'bt-r bt-h', role: 'row', style: { gridTemplateColumns: AX } }, h('div', { class: 'bt-c', role: 'columnheader', text: 'Question' }),
      styles.map(function () {
        return cols.map(function (c, ci) {
          var t = tagFor(c);
          return h('div', { class: 'bt-c', role: 'columnheader', style: { textAlign: 'center', whiteSpace: 'normal', fontWeight: '600', borderLeft: ci === 0 ? '1px solid var(--hair)' : null } },
            h('span', { style: { display: 'inline-flex', gap: '4px', alignItems: 'center' } }, h('span', { class: 'tag ' + t.cls, style: { fontSize: '0' } }, h('i'), h('span', { class: 'sr', text: t.text })), SHORT[c] || c),
            h('span', { class: 'u', text: SHORT_U[c] || ' ' }));
        });
      }));
    var openRow = null;
    var body = pageIds.map(function (id) {
      var cells = [];
      styles.forEach(function (s) {
        cols.forEach(function (c, ci) {
          var key = id + '__' + s + '__' + c, a = F.ans[key], isOpen = key === S.answer;
          var g = !a ? '' : a.correct === true ? '✓' : a.correct === false ? '✗' : '–';
          cells.push(h('div', { class: 'bt-c cell', role: 'cell', style: { borderLeft: ci === 0 ? '1px solid var(--hair)' : null } },
            h('button', { type: 'button', class: 'axb ' + (a && a.correct === false ? 'bad ' : '') + (isOpen ? 'open ' : '') + (S.grade !== 'all' && !matches(a, key) ? 'dim' : ''),
              'aria-expanded': String(isOpen), 'aria-label': id + ', ' + s + ', ' + label(c) + ': ' + (!a ? 'no answer' : a.correct === true ? 'correct' : a.correct === false ? 'incorrect' : 'not graded') + (a ? ', ' + fSec(a.answer_s) + ' seconds' : '') + (rev[key] ? ', reviewed by a person' : ''),
              onclick: function () { go({ answer: isOpen ? '' : key }, false); } },
              h('span', { class: 'g', 'aria-hidden': 'true', text: g }), h('span', { class: 't', text: a ? fSec(a.answer_s) + ' s' : 'none' }), rev[key] ? h('span', { class: 'rv', 'aria-hidden': 'true', text: 'rev' }) : null)));
        });
      });
      var wrap = h('div', { style: { display: 'flex', flexDirection: 'column' } },
        h('div', { class: 'bt-r grp', role: 'row', style: { gridTemplateColumns: AX } }, h('div', { class: 'bt-c', role: 'rowheader' }, h('span', { class: 'mono', style: { fontSize: '13px' }, text: id }), h('span', { class: 'note', style: { display: 'block' }, text: F.prompts[id][0] })), cells));
      if (S.answer && S.answer.split('__')[0] === id && F.ans[S.answer] && styles.indexOf(S.answer.split('__')[1]) >= 0 && cols.indexOf(S.answer.split('__')[2]) >= 0) {
        var a = F.ans[S.answer], pk = S.answer.split('__'), suffix = F.styles[pk[1]] || '', r = rev[S.answer];
        openRow = h('article', { class: 'ans', 'aria-label': 'Answer to ' + id + ', ' + pk[1] + ', ' + label(pk[2]), tabindex: '-1' },
          h('div', { style: { display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', gap: '6px 12px', alignItems: 'baseline' } },
            h('h3', { style: { fontSize: '17px', lineHeight: '24px', fontWeight: '600' } }, h('span', { class: 'mono', text: id }), ' · ' + pk[1] + ' · ' + label(pk[2])),
            h('div', { style: { display: 'flex', gap: '8px' } }, Site.copyButton('Copy link to this answer', hashFor('answer')),
              h('button', { type: 'button', class: 'btn', style: { minHeight: '30px' }, onclick: function () { go({ answer: '' }, false); }, text: 'Close' }))),
          h('p', { style: { fontSize: '15px', lineHeight: '23px' } }, h('span', { class: 'sc note', text: 'Question ' }), F.prompts[id][1], suffix ? h('span', { style: { color: 'var(--fg-2)' }, text: suffix }) : null),
          h('div', { class: 'ans-meta num' }, h('strong', { text: a.correct === true ? '✓ Correct (automatic)' : a.correct === false ? '✗ Incorrect (automatic)' : 'Not graded' }), tag(pk[2]),
            h('span', { text: fSec(a.answer_s) + ' s answer' }), h('span', { text: fSec(a.prefill_s) + ' s prompt read' }), h('span', { text: (a.output_tokens == null ? '—' : a.output_tokens) + ' tokens' }), h('span', { text: fTok(a.decode_tok_s) + ' tok/s' })),
          r ? h('p', { class: 'review' }, h('strong', { text: 'Reviewed: ' + (r.reviewed || r.verdict || '') + '.' }), ' ' + (r.why || r.note || '')) : null,
          h('pre', { text: a.text || '(no answer saved)' }));
        Site.put(wrap, h('div', { style: { padding: '6px 0 14px', position: 'sticky', left: '0', maxWidth: 'min(860px, calc(100vw - 40px))' } }, openRow));
      }
      return wrap;
    });
    Site.put(panel, h('div', { style: { display: 'flex', flexDirection: 'column', gap: '14px' } }, filters,
      h('div', { style: { display: 'flex', flexWrap: 'wrap', gap: '6px 18px', alignItems: 'center', justifyContent: 'space-between' } },
        h('p', { class: 'note num', role: 'status', text: qids.length ? 'Questions ' + (page * 20 + 1) + '–' + (page * 20 + pageIds.length) + ' of ' + qids.length + ' · ' + pageIds.length * nCols + ' answers shown. Open a cell to read the answer.' : 'No answer matches these filters. Reset shows every answer.' }),
        h('div', { class: 'legend' }, h('span', {}, h('strong', { style: { color: 'var(--fg)' }, text: '✓' }), ' correct'), h('span', {}, h('strong', { style: { color: 'var(--fg)' }, text: '✗' }), ' incorrect (shaded)'),
          h('span', {}, h('span', { class: 'sc', style: { color: 'var(--fg)' }, text: 'rev' }), ' reviewed by a person'))),
      h('div', { class: 'tblbox' }, h('div', { class: 'bt freeze ax', role: 'table', 'aria-label': 'Answers by question, style and setting. Open a cell to read the answer.', style: { minWidth: (170 + nCols * 70) + 'px' } },
        headStyle, headCols, h('div', { role: 'rowgroup' }, body))),
      h('div', { class: 'pager' },
        h('button', { type: 'button', class: 'btn', disabled: page === 0 ? true : null, onclick: function () { go({ page: page - 1, answer: '' }, false); }, text: 'Previous' }),
        h('span', { class: 'num', text: 'Page ' + (page + 1) + ' of ' + pages }),
        h('button', { type: 'button', class: 'btn', disabled: page >= pages - 1 ? true : null, onclick: function () { go({ page: page + 1, answer: '' }, false); }, text: 'Next 20' }))));
    if (openRow && pendingScroll) { pendingScroll = false; setTimeout(function () { openRow.scrollIntoView({ block: 'center' }); openRow.focus({ preventScroll: true }); }, 0); }
  }

  function drawMethod(panel, B, F, isO, version, hasReview) {
    var kinds = {}; F.ids.forEach(function (id) { var k = F.prompts[id][0]; kinds[k] = (kinds[k] || 0) + 1; });
    var terse = (F.styles.terse || '').trim();
    var rows = [
      ['Engine', isO ? (version || B.engine) + ', model fully in RAM' : 'Colibri, commit ' + version + '; experts streamed from the SSD'],
      ['Model', isO ? B.title + ' · ' + B.model : B.title + ' · ' + B.sub],
      ['Questions', F.ids.length + ' fixed prompts: ' + Object.keys(kinds).map(function (k) { return kinds[k] + ' ' + k; }).join(', ')],
      ['Answer styles', 'normal: the prompt as written · terse: appends “' + terse + '”'],
      ['Grading', 'Automatic. Maths: the last number in the answer; code: the first code block, run against tests; facts and logic: accepted text. Explanations are not scored.'],
      ['Output budget', isO ? 'exact: 128 tokens, thinking off, temperature 0 · native: up to 4,096 tokens, model defaults' : '128 tokens, greedy; context 1,024 tokens; RAM budget 18 GB'],
      ['Runs', 'One run per question, style and setting; no repeats']
    ];
    Site.put(panel, h('div', { style: { display: 'flex', flexDirection: 'column', gap: '18px', maxWidth: '760px' } },
      h('dl', { style: { display: 'grid', gridTemplateColumns: 'minmax(130px, max-content) 1fr', gap: '8px 20px', fontSize: '15px', lineHeight: '24px' } },
        rows.map(function (m) { return [h('dt', { style: { fontStyle: 'italic' }, text: m[0] }), h('dd', { style: { overflowWrap: 'anywhere' }, text: m[1] })]; })),
      h('div', { style: { display: 'flex', flexDirection: 'column', gap: '6px' } }, h('h3', { class: 'h-small', text: 'Settings in this bench' }),
        F.cfgs.map(function (c) {
          var w = WHAT[c]; w = w && typeof w === 'object' ? (isO ? w.ollama : w.colibri) : w;
          return h('p', { style: { fontSize: '15px', lineHeight: '24px', display: 'flex', flexWrap: 'wrap', gap: '4px 10px', alignItems: 'baseline' } }, h('strong', { text: label(c) }), tag(c), h('span', { style: { color: 'var(--fg-2)' }, text: w || '' }));
        })),
      F.notes.map(function (t) { return h('p', { class: 'note', text: t }); }),
      busy('Every time on this page comes from the owner’s everyday Mac with other apps running; real performance may be better.'),
      h('p', { style: { fontSize: '15px' } }, 'Data: ', h('a', { href: 'data/' + B.file, text: 'data/' + B.file }), ' (summary, every answer with prompt, grade and times' + (hasReview ? ', manual review' : '') + ').')));
  }

  // ---------- render ----------
  var pendingScroll = false;
  function render() {
    drawSwitcher();
    var box = document.getElementById('bench-view');
    Site.fill(box);
    if (S.bench === 'compare') drawCompare(box); else drawBench(box, bench(S.bench));
    if (focusTab) { var t = document.getElementById(focusTab); focusTab = null; if (t) t.focus(); }
  }
  function onNav() { fromHash(); pendingScroll = !!S.answer; render(); }

  Promise.all([Site.getJSON('data/benches.json'), Site.getJSON('data/bench-compare.json'), Site.getJSON('data/external-scores.json').catch(function () { return null; })])
    .then(function (r) {
      D.benches = r[0].benches;
      D.labels = r[1].labels || {};
      D.cmp = r[1].rows.map(function (x) { return [x.bench, x.style, x.config, x.correct, x.graded, x.median_answer_s, x.median_prefill_s, x.mean_tok_s, x.correct_per_min, x.truncated]; });
      D.ext = r[2];
      document.getElementById('total-answers').textContent = D.benches.reduce(function (a, b) { return a + b.answers; }, 0).toLocaleString('en-US');
      document.getElementById('bench-count').textContent = D.benches.length;
      onNav();
      window.addEventListener('popstate', onNav);
      window.addEventListener('hashchange', onNav);
    }, function (e) {
      Site.fill(document.getElementById('bench-view'), h('p', { role: 'alert', text: 'Could not load the bench data: ' + e.message }));
    });
})();
