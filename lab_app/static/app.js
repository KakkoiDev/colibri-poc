/* GLM lab control app. All data comes from lab_app/server.py's /api/*; the design system is
   lab.css (documented in docs/lab-app/design-system.md). Text from the lab (answers, logs,
   titles) is always inserted as text, never as HTML.
   Main tasks get the primary navigation: Run benchmarks, Results, Models. Everything else
   lives under "More tools". */
(function () {
  'use strict';

  var GH = 'https://github.com/KakkoiDev/colibri-poc/blob/main/';
  var ICON = {
    dashboard: 'M7 4.5v15l12-7.5z', results: 'M4 5h16M4 12h16M4 19h16M9 5v14',
    models: 'M21 8l-9-5-9 5 9 5 9-5zM3 8v8l9 5 9-5V8M12 13v8',
    now: 'M3 12h4l3-8 4 16 3-8h4', leaderboard: 'M4 20V10M10 20V4M16 20v-7M2 20h20',
    experiments: 'M9 3h6M10 3v6L4 19a1 1 0 0 0 1 1.5h14A1 1 0 0 0 20 19l-6-10V3',
    benches: 'M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z', runs: 'M4 17l6-5-6-5M12 19h8',
    research: 'M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14zM21 21l-5-5',
    queue: 'M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01', install: 'M12 3v12M7 10l5 5 5-5M4 21h16',
    settings: 'M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12M14 4v4M8 10v4M16 16v4'
  };
  var SCREENS = [['dashboard', 'Run benchmarks'], ['results', 'Results'], ['models', 'Models'], ['phone', 'Open on phone']];
  var ADVANCED = [['queue', 'Queue and logs'], ['now', 'Machine status'], ['runs', 'Engine runs'],
                  ['leaderboard', 'Leaderboard'], ['experiments', 'Experiments'], ['research', 'Research'], ['settings', 'Settings']];
  var CFG = { exact: 'exact', d030: 'skip 0.3', d050: 'skip 0.5', d030t12: 'skip 0.3 · 12 threads', d040t12: 'skip 0.4 · 12 threads',
              native: 'Ollama defaults (thinking on)' };
  var timer = null;

  // ---------- tiny DOM helpers ----------
  function h(tag, attrs) {
    var e = document.createElement(tag);
    for (var k in attrs || {}) {
      if (attrs[k] == null || attrs[k] === false) continue;
      if (k === 'text') e.textContent = attrs[k];
      else if (k.indexOf('on') === 0) e.addEventListener(k.slice(2), attrs[k]);
      else e.setAttribute(k, attrs[k]);
    }
    for (var i = 2; i < arguments.length; i++) add(e, arguments[i]);
    return e;
  }
  function add(e, c) {
    if (c == null || c === false) return;
    if (Array.isArray(c)) { c.forEach(function (x) { add(e, x); }); return; }
    e.appendChild(typeof c === 'string' || typeof c === 'number' ? document.createTextNode(String(c)) : c);
  }
  function put(e) { for (var i = 1; i < arguments.length; i++) add(e, arguments[i]); }
  function svgIcon(d, size) {
    var ns = 'http://www.w3.org/2000/svg', s = document.createElementNS(ns, 'svg'), p = document.createElementNS(ns, 'path');
    s.setAttribute('width', size || '18'); s.setAttribute('height', size || '18'); s.setAttribute('viewBox', '0 0 24 24'); s.setAttribute('aria-hidden', 'true');
    p.setAttribute('d', d); s.appendChild(p); return s;
  }
  var f2 = function (v, d) { return v == null || v === '' || isNaN(v) ? '—' : Number(v).toFixed(d == null ? 2 : d); };
  var pct = function (a, b) { return b ? Math.round(a / b * 100) : 0; };
  function dur(s) {
    if (s == null) return '—';
    var hh = Math.floor(s / 3600), mm = Math.floor(s % 3600 / 60);
    return hh ? hh + ' h ' + mm + ' min' : mm ? mm + ' min' : Math.round(s) + ' s';
  }
  function at(s) {
    var d = new Date(Date.now() + s * 1000), t = ('0' + d.getHours()).slice(-2) + ':' + ('0' + d.getMinutes()).slice(-2);
    var days = Math.round((new Date(d).setHours(0, 0, 0, 0) - new Date().setHours(0, 0, 0, 0)) / 864e5);
    return days === 0 ? t : days === 1 ? 'tomorrow ' + t : d.toLocaleDateString(undefined, { weekday: 'short' }) + ' ' + t;
  }
  function cap(w) { w = String(w || ''); return w.charAt(0).toUpperCase() + w.slice(1); }
  function chip(cls, word) { return h('span', { class: 'chip ' + cls, text: cap(word) }); }
  function verdict(v) {
    var m = { 'improves': ['v-improves', '▲ Improves'], 'no clear change': ['v-same', '= No clear change'], 'worse': ['v-worse', '▼ Worse'],
              'failed': ['v-failed', '✗ Failed'] }[v] || ['v-pending', cap(v)];
    return h('span', { class: 'verdict ' + m[0], text: m[1] });
  }
  function lossyTag() { return h('span', { class: 'tag tag-lossy', text: 'changes output' }); }
  function exactTag() { return h('span', { class: 'tag tag-exact', text: 'exact' }); }
  function ghLink(path, label) { return h('a', { href: GH + path, target: '_blank', rel: 'noopener', text: label || path }); }
  /* GET a lab API. A dropped connection (Safari: "Load failed", e.g. right after the Mac wakes) is retried once;
     an answer from the server, even an error, is not. */
  function api(path, retried) {
    return fetch(path, { cache: 'no-store' }).then(function (r) {
      return r.json().then(function (j) { if (!r.ok) throw new Error(j.error || r.status); return j; });
    }, function (e) {
      if (retried) throw e;
      return new Promise(function (ok) { setTimeout(ok, 800); }).then(function () { return api(path, true); });
    });
  }
  function post(path, body) {
    return fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Lab-Action': '1' }, body: JSON.stringify(body || {}) })
      .then(function (r) { return r.json().then(function (j) { if (!r.ok) throw new Error(j.error || r.status); return j; }); });
  }
  // Toasts: short, announced, dismissible. Errors stay until dismissed.
  function toast(msg, bad, link) {
    var box = document.getElementById('toasts') || document.body;
    var t = h('div', { class: 'toast' + (bad ? ' bad' : ''), role: bad ? 'alert' : 'status' },
      h('span', { style: 'flex:1', text: msg }), link ? h('a', { href: link[0], text: link[1] }) : null,
      h('button', { type: 'button', 'aria-label': 'Dismiss', text: '×', onclick: function () { t.remove(); } }));
    box.appendChild(t);
    if (!bad) setTimeout(function () { t.remove(); }, 7000);
  }
  // Confirmation dialog: names exactly what will happen. Keeps focus inside; Esc or Cancel closes.
  function confirmDialog(o) {
    return new Promise(function (resolve) {
      var prev = document.activeElement;
      var scrim = h('div', { class: 'scrim' });
      function close(v) { scrim.remove(); document.removeEventListener('keydown', key); if (prev && prev.focus) prev.focus(); resolve(v); }
      function key(e) {
        if (e.key === 'Escape') close(false);
        if (e.key === 'Tab') {
          var f = dlg.querySelectorAll('button, a[href], input, select');
          if (!f.length) return;
          if (e.shiftKey && document.activeElement === f[0]) { e.preventDefault(); f[f.length - 1].focus(); }
          else if (!e.shiftKey && document.activeElement === f[f.length - 1]) { e.preventDefault(); f[0].focus(); }
        }
      }
      var cancel = h('button', { type: 'button', class: 'btn', onclick: function () { close(false); }, text: 'Cancel' });
      var ok = h('button', { type: 'button', class: 'btn ' + (o.danger ? 'btn-danger-solid' : 'btn-primary'), onclick: function () { close(true); }, text: o.confirm });
      var dlg = h('div', { class: 'dialog', role: 'dialog', 'aria-modal': 'true', 'aria-labelledby': 'dlg-t', 'aria-describedby': o.sub ? 'dlg-s' : null },
        h('div', { class: 'dialog-head' }, o.eyebrow ? h('span', { class: 'eyebrow', text: o.eyebrow }) : null, h('h2', { id: 'dlg-t', text: o.title }),
          o.sub ? h('p', { id: 'dlg-s', class: 'muted', style: 'font-size:13px', text: o.sub }) : null),
        h('div', { class: 'dialog-body' }, h('dl', { class: 'kv' }, (o.rows || []).map(function (r) { return [h('dt', { text: r[0] }), h('dd', { class: r[2] ? 'mono' : null, text: r[1] })]; })),
          o.note ? h('div', { class: o.warn ? 'notice notice-warn' : 'notice', text: o.note }) : null),
        h('div', { class: 'dialog-foot' }, cancel, ok));
      scrim.addEventListener('click', function (e) { if (e.target === scrim) close(false); });
      scrim.appendChild(dlg); document.body.appendChild(scrim); document.addEventListener('keydown', key);
      (o.danger ? cancel : ok).focus();   // a destructive dialog opens on Cancel
    });
  }
  function stopJob(j) {
    return confirmDialog({ eyebrow: 'Stop a job', title: 'Stop PID ' + j.pid + '?', danger: true, confirm: 'Stop PID ' + j.pid,
      sub: 'Only this job and the processes it started are stopped. Nothing else is touched.',
      rows: [['Job', j.kind + ' · ' + j.title], ['Process', j.command, true], ['Running for', dur(j.elapsed_s)],
             ['Holds', j.holds_lock ? '.bench.lock' : 'no lock'], ['Engine child', j.engine_pid ? 'PID ' + j.engine_pid : 'none']],
      note: j.kind === 'Quality bench' ? 'Finished answers stay saved; queue the same bench again to resume where it stopped.' :
            j.kind === 'Download' ? 'The download is resumable: start it again from Models to continue.' : 'The current run is lost; finished results stay saved.' })
      .then(function (ok) {
        if (!ok) return;
        return post('/api/stop', { pid: j.pid }).then(function (r) { toast('Stopped PID ' + r.stopped.join(', ')); route(); }, function (e) { toast(e.message, true); });
      });
  }
  function runOrQueue(kind, args, label, queueOnly) {
    return post(queueOnly ? '/api/queue/add' : '/api/run', { kind: kind, args: args }).then(function (r) {
      toast(r.started ? 'Started: ' + r.started.title + ' (PID ' + r.started.pid + ')' : (r.note ? r.note + ': ' : 'Queued: ') + (r.queued ? r.queued.title : label), false, ['#queue', 'View queue']);
      route();
    }, function (e) { toast(e.message, true); });
  }
  // Header cells: 'Text' or { t: 'Text', n: numeric, u: 'unit' }.
  function th(x) {
    var n = typeof x === 'object';
    return h('th', { class: n && x.n ? 'n' : null, scope: 'col' }, n ? x.t : x, n && x.u ? h('span', { class: 'u', text: x.u }) : null);
  }
  function table(headers, rows, caption) {
    var t = h('table', { class: 't' }, caption ? h('caption', { class: 'sr-only', text: caption }) : null);
    t.appendChild(h('thead', {}, h('tr', {}, headers.map(th))));
    var tb = h('tbody'); rows.forEach(function (r) { tb.appendChild(r); }); t.appendChild(tb);
    return h('div', { class: 'table-wrap' }, t);
  }
  function td(content, cls) { return h('td', { class: cls || null }, content); }
  function header(title, sub, extra) {
    return h('header', { class: 'head' }, h('div', { class: 'stack' }, h('h1', { text: title }), sub ? h('p', { class: 'muted', text: sub }) : null), extra || null);
  }
  function section(title, right, body) {
    return h('section', { class: 'stack' }, h('div', { class: 'sec-title' }, h('h2', { text: title }), right || null), body);
  }
  function card(children, pad) { return h('div', { class: 'card', style: 'padding:' + (pad || '16px 20px') + ';display:flex;flex-direction:column;gap:12px' }, children); }
  function meter(done, total, label) {
    return h('div', { class: 'meter', role: 'progressbar', 'aria-label': label || 'Progress', 'aria-valuemin': 0, 'aria-valuemax': total, 'aria-valuenow': done },
      h('span', { style: 'width:' + Math.min(100, pct(done, total)) + '%' }));
  }
  function empty(text, action) { return h('div', { class: 'empty' }, h('p', { text: text }), action ? h('div', { style: 'margin-top:12px' }, action) : null); }
  function errorBox(e, retry, wait) {
    var lost = e instanceof TypeError;   // fetch could not reach the server at all
    return h('div', { class: 'err', role: 'alert' },
      h('span', { text: lost ? 'Could not reach the lab server (' + (e.message || e) + '). ' : 'Could not load data: ' + (e.message || e) + '. ' }),
      h('span', { text: lost ? 'Trying again' + (wait ? ' in ' + Math.round(wait / 1000) + ' s' : '') + '. If it keeps failing, check that the lab app service is running (make lab-app-install). ' : '' }),
      retry ? h('button', { type: 'button', class: 'btn btn-sm', onclick: retry, text: 'Try again' }) : null);
  }
  // "Quality bench v1 on GLM-5.3 int4 g64: exact, d030 · terse" -> what / model / detail
  function jobParts(title) {
    var m = /^(.*?) on (.*?)(?:: (.*))?$/.exec(title || '');
    if (!m) return { what: title || '', model: '', detail: '' };
    var detail = (m[3] || '').replace(/\b(exact|d030t12|d040t12|d030|d050|native)\b/g, function (c) { return CFG[c] || c; });
    return { what: m[1].replace(/^Quality bench \S+$/, 'Quality bench').replace(/^Ram bench/, 'RAM bench'), model: m[2], detail: detail };
  }

  // ---------- nav / theme ----------
  function renderNav(active) {
    var nav = document.getElementById('nav'); nav.textContent = '';
    function link(s) { return h('a', { href: '#' + s[0], 'aria-current': s[0] === active ? 'page' : null }, svgIcon(ICON[s[0]] || ICON.benches), h('span', { text: s[1] })); }
    SCREENS.forEach(function (s) { nav.appendChild(link(s)); });
    var adv = ADVANCED.some(function (s) { return s[0] === active; });
    nav.appendChild(h('details', { class: 'advanced-nav', open: adv ? '' : null }, h('summary', { text: 'More tools' }), ADVANCED.map(link)));
  }
  function setGpu(now) {
    var c = document.getElementById('gpu-chip'), d = document.getElementById('gpu-detail');
    var gpu = (now.jobs || []).filter(function (j) { return j.gpu; });
    if (gpu.length) {
      c.className = 'chip st-running'; c.textContent = 'GPU busy';
      d.textContent = gpu[0].title + ' · PID ' + gpu[0].pid;
    } else { c.className = 'chip st-done'; c.textContent = 'GPU free'; d.textContent = (now.jobs || []).length ? now.jobs.length + ' other job(s)' : 'Nothing running'; }
  }
  (function theme() {
    var sel = document.getElementById('theme'), saved = 'auto';
    try { saved = localStorage.getItem('glm-lab-theme') || 'auto'; } catch (e) {}
    document.body.setAttribute('data-theme', saved); sel.value = saved;
    sel.addEventListener('change', function () {
      document.body.setAttribute('data-theme', sel.value);
      try { localStorage.setItem('glm-lab-theme', sel.value); } catch (e) {}
    });
  })();

  // The skip link must not change the hash (the hash is the router).
  (function skip() {
    var a = document.querySelector('.skip'); if (!a) return;
    a.addEventListener('click', function (e) { e.preventDefault(); var m = document.getElementById('main'); if (m) { m.focus(); m.scrollIntoView(); } });
  })();
  // ---------- legacy live screens (More tools) ----------
  function jobCard(j) {
    var p = j.progress, unit = p && p.unit ? ' ' + p.unit : '';
    return card([
      h('div', { class: 'row' }, chip(j.foreign ? 'st-blocked' : 'st-running', j.foreign ? 'Not from the lab' : 'Running'), h('span', { class: 'tag', text: j.kind }),
        j.holds_lock ? h('span', { class: 'hint mono', text: 'holds .bench.lock' }) : null, j.gpu ? null : h('span', { class: 'hint', text: 'no GPU' })),
      h('h3', { class: 'num', style: 'font-size:18px;line-height:24px', text: j.title }),
      h('p', { class: 'muted', style: 'font-size:13px', text: j.detail || '' }),
      p && p.items ? h('p', { class: 'num', style: 'font-size:13px', text: p.done + ' of ' + p.total + ' answers · ' + (p.eta_s ? '~' + dur(p.eta_s) + ' left, done ~' + at(p.eta_s) : 'finishing') +
        (p.per_answer_s ? ' · ' + p.per_answer_s + ' s per answer this run' : '') }) : null,
      p && p.items ? benchStrip(p) : null,
      p && p.total && !p.items ? h('div', { class: 'stack', style: 'gap:6px' }, meter(p.done, p.total),
        h('div', { class: 'num hint row between' }, h('span', { text: f2(p.done, unit ? 1 : 0) + ' of ' + p.total + unit + ' · ' + pct(p.done, p.total) + '%' }),
          h('span', { text: unit ? 'downloaded so far' : 'finished answers are saved as they complete' }))) : null,
      h('div', { class: 'well', style: 'padding:8px 10px;display:flex;flex-direction:column;gap:2px' },
        h('span', { class: 'num', style: 'font-size:13px;font-weight:600', text: 'PID ' + j.pid + (j.engine_pid ? ' · engine PID ' + j.engine_pid : '') + ' · running ' + dur(j.elapsed_s) }),
        h('span', { class: 'mono muted', style: 'overflow-wrap:anywhere', text: j.command })),
      j.stoppable ? h('div', { class: 'row' }, h('button', { type: 'button', class: 'btn btn-danger', onclick: function () { stopJob(j); }, text: 'Stop PID ' + j.pid + '…' }))
        : h('p', { class: 'hint', text: 'Not started by the lab (e.g. your own Colibri session): the app never stops it. Stop it yourself if needed.' })
    ]);
  }

  function screenNow(main) {
    return api('/api/now').then(function (d) {
      setGpu(d);
      var m = d.machine;
      var jobs = d.jobs.length ? d.jobs.map(jobCard) : [card([h('div', { class: 'row' }, chip('st-waiting', 'Idle'), h('span', { class: 'hint', text: 'GPU free · nothing running' })),
        h('p', { class: 'muted', text: 'Nothing is running. Ready planned experiments are listed below.' })])];
      var health = card([
        h('div', { class: 'row between' }, h('h2', { class: 'eyebrow', text: 'Machine health' }), chip(m.quiet ? 'st-done' : 'st-blocked', m.quiet ? 'Quiet' : 'Busy · not quiet')),
        h('div', { class: 'row between' }, h('span', { text: 'Free RAM' }), h('strong', { class: 'num' }, f2(m.free_gb, 1) + ' ', h('span', { class: 'unit', text: 'of 32 GB' }))),
        meter(m.free_gb, 32),
        h('span', { class: 'hint', text: 'Quiet needs ≥ ' + m.quiet_threshold_gb + ' GB free; runs now are recorded as ' + (m.quiet ? 'quiet.' : 'busy.') }),
        h('dl', { class: 'kv2' }, [['Swap used', f2(m.swap_used_mb / 1024, 1) + ' GB'], ['Free disk', m.disk_free_gb + ' GB'], ['Load', m.load_avg.join(' · ')], ['Processes', m.process_count]]
          .map(function (x) { return h('div', {}, h('dt', { text: x[0] }), h('dd', { text: x[1] })); })),
        h('div', { class: 'stack', style: 'gap:4px' }, h('span', { class: 'hint', text: 'Largest apps by memory' }),
          m.top_apps.map(function (a) { return h('div', { class: 'row between', style: 'font-size:13px' }, h('span', { text: a.name }), h('span', { class: 'num', text: f2(a.rss_gb, 2) + ' GB' })); }))
      ]);
      var sb = d.scoreboard, target = sb.target_tok_s || 5;
      var score = card([h('div', { class: 'row between' }, h('h2', { class: 'eyebrow', text: 'Scoreboard · target ' + target + ' tok/s' }), h('a', { href: '#leaderboard', text: 'Leaderboard' })),
        [['best_exact', 'Best exact', false], ['everyday', 'Everyday setting', true], ['best_usable_lossy', 'Best usable lossy', true]].map(function (k) {
          var x = sb[k[0]]; if (!x) return null;
          return h('div', { class: 'score stack', style: 'gap:4px' },
            h('div', { class: 'row between' }, h('div', { class: 'row' }, h('strong', { text: k[1] }), k[2] ? lossyTag() : exactTag()),
              h('span', { class: 'num' }, f2(x.tok_s) + ' ', h('span', { class: 'unit', text: 'tok/s' }), h('span', { class: 'muted', text: ' · ' + x.pct_of_target + '% of target' }))),
            h('div', { class: 'track', 'aria-hidden': 'true' }, h('span', { class: k[2] ? 'hatch' : null, style: 'width:' + Math.min(100, x.pct_of_target) + '%' })),
            h('span', { class: 'hint', text: x.title + ' · run ' + x.runs.join(', ') + ' · single run' }));
        })]);
      var planned = card([h('div', { class: 'row between' }, h('h2', { class: 'eyebrow', text: 'Planned experiments' }), h('a', { href: '#experiments', text: 'Experiments' })),
        d.planned.length ? d.planned.map(function (p) {
          return h('div', { class: 'row between', style: 'border-top:1px solid var(--line);padding-top:6px' },
            h('div', { class: 'stack', style: 'gap:0;min-width:0;flex:1' }, h('span', { text: p.title }), p.why ? h('span', { class: 'hint', text: p.why }) : null),
            h('div', { class: 'row' }, chip(p.ready ? 'st-done' : 'st-blocked', p.ready ? 'Ready' : 'Blocked'),
              p.ready ? h('button', { type: 'button', class: 'btn btn-sm', onclick: function () { runOrQueue('planned', { id: p.id }, p.title, true); }, text: 'Queue' }) : null));
        }) : h('p', { class: 'muted', text: 'No planned experiments.' }),
        h('p', { class: 'hint', text: 'Queued jobs start one at a time when the GPU is free.' })]);
      var queueCard = timelineCard(d.timeline, true);
      var recent = card([h('div', { class: 'row between' }, h('h2', { class: 'eyebrow', text: 'Recent results' }), h('a', { href: '#experiments', text: 'All experiments' })),
        d.recent.map(function (r) {
          return h('div', { class: 'row between', style: 'border-top:1px solid var(--line);padding-top:6px;flex-wrap:nowrap' },
            h('div', { class: 'row', style: 'min-width:0' }, verdict(r.verdict), h('span', { text: r.title }), r.lossy ? lossyTag() : null),
            h('span', { class: 'num', style: 'white-space:nowrap', text: f2(r.ref_tok_s) + ' → ' + f2(r.tok_s) + ' tok/s' }));
        })]);
      put(main, header('Now', 'What the Mac is doing, what we learned, what is planned · ' + d.time + ' · updates every 5 s'),
        h('div', { class: 'grid2' }, h('section', { class: 'stack', 'aria-label': 'Now running' }, h('h2', { class: 'eyebrow', text: 'Now running · one GPU job at a time' }), jobs), health),
        h('div', { class: 'grid2' }, score, queueCard), h('div', { class: 'grid2' }, planned, recent));
    });
  }

  function benchStrip(p) {
    var strip = h('div', { role: 'img', 'aria-label': p.done + ' of ' + p.total + ' answers done', style: 'display:flex;flex-wrap:wrap;gap:3px' });
    p.items.forEach(function (i) {
      var st = i.status === 'done' ? (i.correct === false ? 'background:var(--bad)' : 'background:var(--fg)')
        : i.status === 'running' ? 'background:repeating-linear-gradient(135deg,var(--fg) 0 1.5px,var(--bg) 1.5px 4px);box-shadow:inset 0 0 0 1px var(--fg)'
        : 'box-shadow:inset 0 0 0 1px var(--fg-2)';
      strip.appendChild(h('span', { title: i.prompt + ' · ' + i.style + ' · ' + (CFG[i.config] || i.config) + ' · ' + i.status +
        (i.answer_s ? ' · ' + Math.round(i.answer_s) + ' s' : '') + (i.correct === false ? ' · incorrect (auto)' : i.correct ? ' · correct' : ''), style: 'width:12px;height:12px;' + st }));
    });
    var next = p.items.filter(function (i) { return i.status !== 'done'; }).slice(0, 5);
    return h('div', { class: 'stack', style: 'gap:6px' }, strip,
      h('span', { class: 'hint', text: '■ done · ▨ running · □ waiting · red = graded incorrect (auto). Hover a square for details.' }),
      next.length ? h('div', { class: 'stack', style: 'gap:2px' }, h('span', { class: 'hint', text: 'Running and next:' }),
        h('ol', { style: 'margin:0;padding-left:18px;font-size:13px' }, next.map(function (i) {
          return h('li', { style: i.status === 'running' ? 'font-weight:600' : null, text: i.prompt + ' · ' + i.style + ' · ' + (CFG[i.config] || i.config) + (i.status === 'running' ? ' (running now)' : '') });
        }))) : null);
  }
  function timelineCard(tl, compact) {
    var rows = [];
    if (tl.current) rows.push(h('li', { class: 'row between', style: 'flex-wrap:nowrap' }, h('span', {}, h('strong', { text: 'Now: ' }), tl.current.title + ' · PID ' + tl.current.pid),
      h('span', { class: 'num hint', style: 'white-space:nowrap', text: tl.current.eta_s != null ? 'done in ~' + dur(tl.current.eta_s) + ' (' + at(tl.current.eta_s) + ')' : 'ETA unknown' })));
    tl.queue.slice(0, compact ? 5 : 100).forEach(function (q, k) {
      rows.push(h('li', { class: 'row between', style: 'flex-wrap:nowrap' }, h('span', {}, h('span', { class: 'num muted', text: (k + 1) + '. ' }), q.title + (q.only_when_quiet ? ' · when quiet' : '')),
        h('span', { class: 'num hint', style: 'white-space:nowrap', text: '~' + dur(q.est_s) + (q.starts_in_s != null ? ' · starts ~' + at(q.starts_in_s) : '') })));
    });
    var ready = tl.ready_not_queued || [];
    return card([h('div', { class: 'row between' }, h('h2', { class: 'eyebrow', text: 'Up next · timeline' }), h('span', { class: 'row', style: 'gap:12px' }, h('a', { href: '#dashboard', text: 'Start benches' }), h('a', { href: '#queue', text: 'Queue · ' + tl.queue.length + ' waiting' + (tl.paused ? ' · paused' : '') }))),
      rows.length ? h('ol', { class: 'stack', style: 'margin:0;padding:0;list-style:none;gap:6px;font-size:13px' }, rows) : h('p', { class: 'muted', text: 'Nothing running and nothing queued.' }),
      tl.queue.length ? h('span', { class: 'hint', text: tl.total_s != null ? 'Everything queued done ~' + at(tl.total_s) + ' (estimates from past answer and run times).' : 'Times appear once the current job reports progress.' })
        : h('span', { class: 'hint', text: 'Nothing queued after the current job.' }),
      ready.length ? h('div', { class: 'stack', style: 'gap:6px;border-top:1px solid var(--line);padding-top:8px' },
        h('span', { class: 'hint', text: ready.length + ' ready planned experiment' + (ready.length > 1 ? 's are' : ' is') + ' not queued: ' + ready.map(function (r) { return r.title; }).join(' · ') }),
        h('div', { class: 'row' }, h('button', { type: 'button', class: 'btn btn-sm', text: 'Queue all ready (' + ready.length + ')', onclick: function (e) {
          e.target.disabled = true;
          ready.reduce(function (pr, r) { return pr.then(function () { return post('/api/queue/add', { kind: 'planned', args: { id: r.id } }); }); }, Promise.resolve())
            .then(function () { toast('Queued ' + ready.length + ' planned experiments; they start after the current job.'); route(); }, function (er) { toast(er.message, true); route(); });
        } }))) : null]);
  }

  function covCell(c, onRun) {
    var map = { done: ['st-done', 'Done'], running: ['st-running', 'Running'], missing: ['st-missing', 'Missing'], failed: ['st-failed', 'Failed'], queued: ['st-queued', 'Queued'] }[c.status];
    return h('div', { class: 'cov' + (c.status === 'missing' ? ' missing' : '') }, h('span', { class: 'chip ' + map[0], style: 'align-self:flex-start', text: map[1] }), h('span', { class: 'hint num', text: c.detail || '' }),
      onRun ? h('button', { type: 'button', class: 'btn btn-sm', style: 'align-self:flex-start', onclick: onRun, text: c.status === 'done' ? 'Queue again' : 'Queue' }) : null);
  }
  // Queue job args for one standard bench on one model (defaults match how each bench is usually run).
  function benchJob(bench, m, opts) {
    opts = opts || {};
    if (bench === 'quality') return { kind: 'bench', args: { name: opts.name || (m.owner_model ? 'v1' : m.id), configs: opts.configs || ['exact', 'd030t12'], styles: opts.styles || ['terse'], model: m.id } };
    if (bench === 'quiet') return { kind: 'quiet', args: { flags: ['skip-original'] }, only_when_quiet: true };
    return { kind: 'suite', args: { bench: bench, model: m.id }, only_when_quiet: bench === 'ram' };
  }
  function queueBench(bench, m, opts, now) {
    var j = benchJob(bench, m, opts);
    return post(now ? '/api/run' : '/api/queue/add', { kind: j.kind, args: j.args, only_when_quiet: !now && j.only_when_quiet })
      .then(function (r) { toast(r.started ? 'Started: ' + r.started.title + ' (PID ' + r.started.pid + ')' : (r.note ? r.note + ': ' : 'Queued: ') + r.queued.title + (r.queued.only_when_quiet ? ' (when quiet)' : '')); route(); },
            function (e) { toast(e.message, true); });
  }


  // ---------- sortable data table ----------
  // cols: [{ t, u, n, key, cell(row) -> node|string, best: 'max'|'min', sortable }]; rows: plain objects.
  // o.freeze: keep the first column (the row's name) visible while the table scrolls sideways.
  // o.onSort(key, dir): called when a header changes the order, so a "Sort by" control can follow.
  function dataTable(o) {
    var wrap = h('div', { class: 'table-wrap' + (o.freeze ? ' freeze' : '') });
    var st = { key: o.sortKey || null, dir: o.dir || 'desc' };
    function val(r, c) { var v = typeof c.key === 'function' ? c.key(r) : r[c.key]; return v == null || v === '' || (typeof v === 'number' && isNaN(v)) ? null : v; }
    function draw() {
      var rows = o.rows.slice();
      var col = o.cols.filter(function (c) { return c.id === st.key; })[0];
      if (col) rows.sort(function (a, b) {
        var x = val(a, col), y = val(b, col);
        if (x == null) return 1; if (y == null) return -1;
        var d = typeof x === 'number' ? x - y : String(x).localeCompare(String(y));
        return st.dir === 'asc' ? d : -d;
      });
      var best = {};
      o.cols.forEach(function (c) {
        if (!c.best) return;
        var vs = rows.map(function (r) { return val(r, c); }).filter(function (v) { return typeof v === 'number'; });
        if (vs.length > 1) best[c.id] = c.best === 'max' ? Math.max.apply(null, vs) : Math.min.apply(null, vs);
      });
      var t = h('table', { class: 't' }, o.caption ? h('caption', { class: 'sr-only', text: o.caption }) : null);
      t.appendChild(h('thead', {}, h('tr', {}, o.cols.map(function (c) {
        var label = [c.t, c.u ? h('span', { class: 'u', text: c.u }) : null];
        if (!c.id || c.sortable === false) return h('th', { scope: 'col', class: c.n ? 'n' : null }, label);
        var sorted = st.key === c.id;
        return h('th', { scope: 'col', class: (c.n ? 'n ' : '') + 'sort-th', 'aria-sort': sorted ? (st.dir === 'asc' ? 'ascending' : 'descending') : null },
          h('button', { type: 'button', class: 'sort', onclick: function () {
            if (st.key === c.id) st.dir = st.dir === 'asc' ? 'desc' : 'asc'; else { st.key = c.id; st.dir = c.n ? (c.best === 'min' ? 'asc' : 'desc') : 'asc'; }
            draw(); if (o.onSort) o.onSort(st.key, st.dir);
            var b = wrap.querySelector('th[aria-sort] .sort'); if (b) b.focus({ preventScroll: true }); reveal();
          } }, h('span', {}, label)));
      }))));
      var tb = h('tbody');
      if (!rows.length) tb.appendChild(h('tr', {}, h('td', { colspan: o.cols.length }, h('span', { class: 'muted', text: o.emptyText || 'No rows match these filters.' }))));
      rows.forEach(function (r) {
        tb.appendChild(h('tr', { class: o.rowClass ? o.rowClass(r) : null }, o.cols.map(function (c) {
          var isBest = c.id in best && val(r, c) === best[c.id];
          return h('td', { class: [c.n ? 'n' : '', c.wrap ? 'wrap' : '', isBest ? 'best' : ''].join(' ').trim() || null, title: isBest ? 'Best value in this table' : null },
            c.cell ? c.cell(r) : (val(r, c) == null ? '—' : String(val(r, c))), isBest ? h('span', { class: 'sr-only', text: ' (best)' }) : null);
        })));
      });
      t.appendChild(tb);
      wrap.textContent = ''; wrap.appendChild(t);
    }
    // The column the rows are ordered by must be on screen, also when the table is wider than the page.
    function reveal() {
      var th = wrap.querySelector('th[aria-sort]'); if (!th || wrap.scrollWidth <= wrap.clientWidth) return;
      var first = o.freeze ? wrap.querySelector('th').offsetWidth : 0;
      if (th.offsetLeft < wrap.scrollLeft + first || th.offsetLeft + th.offsetWidth > wrap.scrollLeft + wrap.clientWidth)
        wrap.scrollLeft = Math.max(0, th.offsetLeft - first - 8);
    }
    draw();
    requestAnimationFrame(reveal);
    return wrap;
  }
  function selectField(id, label, options, value, onchange) {
    var sel = h('select', { class: 'input', id: id, onchange: function () { onchange(sel.value); } },
      options.map(function (x) { return h('option', { value: x[0], selected: x[0] === value ? '' : null, text: x[1] }); }));
    return h('div', { class: 'field' }, h('label', { for: id, text: label }), sel);
  }
  function uniq(list) { return list.filter(function (v, i, x) { return v != null && x.indexOf(v) === i; }); }
  function envText(env) { var k = Object.keys(env || {}); return k.length ? k.map(function (x) { return x + '=' + (typeof env[x] === 'object' ? JSON.stringify(env[x]) : env[x]); }).join(' ') : 'none'; }

  // ---------- results ----------
  var resultsState = { model: 'all', style: 'all', kind: 'all', speedOk: true, speedQ: '', qualityOrder: 'quality', speedOrder: 'saved',
                       qSort: { key: 'pct', dir: 'desc' }, sSort: { key: 'i', dir: 'desc' } };
  // "Sort by" presets <-> table header order. A header click that matches no preset shows "Column header".
  var ORDER_PRESETS = { quality: ['pct', 'desc'], fastest: ['tok_s', 'desc'], slowest: ['tok_s', 'asc'], saved: ['i', 'desc'] };
  function presetFor(sort) {
    for (var k in ORDER_PRESETS) if (ORDER_PRESETS[k][0] === sort.key && ORDER_PRESETS[k][1] === sort.dir) return k;
    return 'custom';
  }
  function orderField(id, presets, sort, redraw) {
    var opts = presets.concat([['custom', 'Column header (click a header)']]);
    var f = selectField(id, 'Sort by', opts, presetFor(sort), function (v) {
      if (v === 'custom') return; sort.key = ORDER_PRESETS[v][0]; sort.dir = ORDER_PRESETS[v][1]; redraw();
    });
    f.querySelector('option[value="custom"]').disabled = true;
    f.sync = function () { f.querySelector('select').value = presetFor(sort); };
    return f;
  }
  function screenResults(main, tab) {
    tab = tab === 'speed' || tab === 'coverage' ? tab : 'quality';
    return Promise.all([api('/api/benches'), api('/api/runs'), api('/api/models')]).then(function (res) {
      var d = res[0], runs = res[1].runs, models = res[2].models;
      var benchModel = {};
      models.forEach(function (m) { benchModel[m.id] = m.name; (m.bench_names || []).forEach(function (n) { benchModel[n] = m.name; }); });
      function modelOf(r) {
        if (benchModel[r.name]) return benchModel[r.name];
        if (r.settings && r.settings.ollama_model) return 'Ollama ' + r.settings.ollama_model;
        return r.name;
      }
      var quality = [];
      d.results.forEach(function (r) {
        r.summary.forEach(function (s) {
          quality.push({ model: modelOf(r), bench: r.name, style: s.style, config: s.config, lossy: s.config !== 'exact' && s.config !== 'native',
            correct: s.correct, graded: s.graded, pctCorrect: s.graded ? s.correct / s.graded * 100 : null, same: s.same_as_exact, ok: s.ok,
            answer_s: s.answer_s, prefill_s: s.prefill_s, tokens: s.output_tokens, tok_s: s.decode_tok_s, runs: s.runs });
        });
      });
      var tabs = h('nav', { class: 'tabs', 'aria-label': 'Result views' }, [['quality', 'Answer quality', quality.length], ['speed', 'Speed runs', runs.length], ['coverage', 'Coverage', d.models.length]].map(function (t) {
        return h('a', { class: 'tab', href: '#results' + (t[0] === 'quality' ? '' : '/' + t[0]), 'aria-current': t[0] === tab ? 'page' : null }, t[1], h('span', { class: 'count', text: t[2] }));
      }));
      var body = tab === 'quality' ? qualityView(quality, d) : tab === 'speed' ? speedView(runs) : coverageView(d);
      put(main, header('Results', 'Measured values from saved benchmark runs. Every number is a single run on this Mac unless marked otherwise.',
        h('a', { class: 'btn', href: '#dashboard', text: 'Run a benchmark' })), tabs, body);
    });
  }

  function qualityView(rows, d) {
    var st = resultsState, out = h('div', { class: 'stack' }), tblBox = h('div'), count = h('p', { class: 'hint', role: 'status' });
    function draw() {
      var shown = rows.filter(function (r) {
        return (st.model === 'all' || r.model === st.model) && (st.style === 'all' || r.style === st.style) &&
          (st.kind === 'all' || (st.kind === 'exact') === !r.lossy);
      });
      count.textContent = shown.length + ' of ' + rows.length + ' setting × style combinations. Bold = best value among the rows shown.';
      tblBox.textContent = '';
      tblBox.appendChild(dataTable({ caption: 'Answer quality and speed per bench, setting and style', freeze: true, sortKey: st.qSort.key, dir: st.qSort.dir, rows: shown,
        onSort: function (k, d) { st.qSort.key = k; st.qSort.dir = d; order.sync(); },
        rowClass: function (r) { return r.lossy ? 'lossy' : null; },
        cols: [
          { id: 'model', t: 'Model', u: 'bench · answer style', key: 'model', cell: function (r) { return h('div', { class: 'cell-name' }, h('strong', { text: r.model }), h('span', { class: 'hint', text: r.bench + ' · ' + r.style })); } },
          { id: 'config', t: 'Setting', key: function (r) { return CFG[r.config] || r.config; }, cell: function (r) { return h('div', { class: 'cell-setting' }, h('span', { text: CFG[r.config] || r.config }), r.lossy ? lossyTag() : r.config === 'exact' ? exactTag() : null); } },
          { id: 'pct', t: 'Correct', u: '% graded', n: 1, best: 'max', key: 'pctCorrect', cell: function (r) { return h('span', {}, h('strong', { text: f2(r.pctCorrect, 0) + '%' }), h('span', { class: 'hint', text: ' ' + r.correct + '/' + r.graded })); } },
          { id: 'tok_s', t: 'Speed', u: 'tok/s', n: 1, best: 'max', key: 'tok_s', cell: function (r) { return f2(r.tok_s); } },
          { id: 'answer', t: 'Answer time', u: 's, mean', n: 1, best: 'min', key: 'answer_s', cell: function (r) { return f2(r.answer_s, 1); } },
          { id: 'same', t: 'Same as exact', u: 'answers', n: 1, key: function (r) { return r.ok ? r.same / r.ok : null; }, cell: function (r) { return r.config === 'exact' ? h('span', { class: 'hint', text: 'reference' }) : r.same + '/' + r.ok; } },
          { id: 'prefill', t: 'Prompt read', u: 's', n: 1, best: 'min', key: 'prefill_s', cell: function (r) { return f2(r.prefill_s, 1); } },
          { id: 'tokens', t: 'Output', u: 'tokens', n: 1, key: 'tokens', cell: function (r) { return f2(r.tokens, 0); } },
          { t: 'Answers', cell: function (r) { return h('a', { href: '#bench/' + encodeURIComponent(r.bench) + '?style=' + encodeURIComponent(r.style) + '&config=' + encodeURIComponent(r.config), 'aria-label': 'Answers for ' + r.model + ', ' + (CFG[r.config] || r.config) + ', ' + r.style, text: 'Answers (' + r.runs + ')' }); } }
        ] }));
    }
    var order = orderField('f-quality-order', [['quality', 'Correct: highest first'], ['fastest', 'Speed: fastest first'], ['slowest', 'Speed: slowest first']], st.qSort, function () { draw(); });
    var models = uniq(rows.map(function (r) { return r.model; })), styles = uniq(rows.map(function (r) { return r.style; }));
    var filters = h('div', { class: 'filters', role: 'group', 'aria-label': 'Filter results' },
      selectField('f-model', 'Model', [['all', 'All models']].concat(models.map(function (m) { return [m, m]; })), st.model, function (v) { st.model = v; draw(); }),
      selectField('f-style', 'Answer style', [['all', 'All styles']].concat(styles.map(function (m) { return [m, cap(m)]; })), st.style, function (v) { st.style = v; draw(); }),
      selectField('f-kind', 'Output', [['all', 'Exact and lossy'], ['exact', 'Exact only'], ['lossy', 'Changes output only']], st.kind, function (v) { st.kind = v; draw(); }),
      order);
    draw();
    var settings = section('How each bench was run', null, h('div', { class: 'stack', style: 'gap:8px' }, d.results.map(function (r) {
      var s = r.settings || {};
      var rowsKv = [['Started', r.started ? r.started.replace('T', ' ').replace('Z', ' UTC') : '—'], ['Backend', s.backend === 'ollama' ? 'Ollama ' + (s.ollama_model || '') + (s.ollama_version ? ' (' + s.ollama_version.replace('ollama version is ', 'v') + ')' : '') : 'Colibri' + (s.colibri_commit ? ' @ ' + s.colibri_commit : '')],
        ['RAM budget', s.ram_gb ? s.ram_gb + ' GB' : '—'], ['Context', s.ctx ? s.ctx + ' tokens' : '—'], ['Answer limit', s.max_tokens ? s.max_tokens + ' tokens (normal style)' : '—'],
        ['Base environment', envText(s.base_env), true]];
      Object.keys(s.configs || {}).forEach(function (c) { rowsKv.push(['Setting · ' + (CFG[c] || c), envText(s.configs[c]), true]); });
      Object.keys(s.styles || {}).forEach(function (k) { rowsKv.push(['Style · ' + k, s.styles[k] ? 'appends: "' + s.styles[k].trim() + '"' : 'prompt as written']); });
      return h('details', { class: 'x card disclosure' }, h('summary', {}, h('strong', { text: modelOf2(r) }), h('span', { class: 'hint', text: ' · bench ' + r.name + ' · ' + r.answers + ' answers' })),
        h('div', { class: 'stack', style: 'padding-top:8px' }, h('dl', { class: 'kv' }, rowsKv.map(function (x) { return [h('dt', { text: x[0] }), h('dd', { class: x[2] ? 'mono' : null, text: x[1] })]; })),
          h('div', { class: 'row' }, h('a', { href: '#bench/' + encodeURIComponent(r.name), text: 'All ' + r.answers + ' answers' }), r.review ? ghLink(r.review, 'Manual review') : null),
          r.notes.length ? h('p', { class: 'hint', text: 'Notes in the results folder: ' + r.notes.join(', ') }) : null));
      function modelOf2(x) { var m = rows.filter(function (q) { return q.bench === x.name; })[0]; return m ? m.model : x.name; }
    })));
    put(out, filters, count, tblBox,
      h('p', { class: 'hint', text: 'Correct: automatic grading (facts and logic by expected answer, maths by final number, code by running tests). Normal answers are capped at 128 tokens, so long answers can be under-counted. Rows marked "changes output" use lossy settings.' }),
      settings);
    return out;
  }

  function speedView(runs) {
    var st = resultsState, out = h('div', { class: 'stack' }), box = h('div'), count = h('p', { class: 'hint', role: 'status' });
    var rows = runs.map(function (r, i) {
      var num = function (k) { return r[k] === '' || r[k] == null ? null : Number(r[k]); };
      return { i: i, run: r.run, backend: r.backend, threads: num('omp_threads'), tok_s: num('tok_s'), prefill_s: num('prefill_s'), tokens: num('decode_tokens'), hit: num('hit_pct'), rss: num('rss_gb'),
        io: num('io_pct'), status: r.status, config: r.config, env: r.env };
    }).reverse();
    function draw() {
      var q = st.speedQ.toLowerCase();
      var shown = rows.filter(function (r) { return (!st.speedOk || r.status === 'ok') && (!q || (r.run + ' ' + r.backend + ' ' + r.env).toLowerCase().indexOf(q) >= 0); });
      count.textContent = shown.length + ' of ' + rows.length + ' runs. Bold = best value among the runs shown.';
      box.textContent = '';
      box.appendChild(dataTable({ caption: 'Engine speed runs', freeze: true, rows: shown, sortKey: st.sSort.key, dir: st.sSort.dir,
        onSort: function (k, d) { st.sSort.key = k; st.sSort.dir = d; sOrder.sync(); },
        cols: [
          { id: 'run', t: 'Run', u: 'backend', key: 'run', cell: function (r) { return h('div', { class: 'cell-name' }, h('span', { class: 'mono', text: r.run }), h('span', { class: 'hint', text: r.backend })); } },
          { id: 'i', t: 'Saved', u: 'order', n: 1, key: 'i', cell: function (r) { return h('span', { class: 'hint', text: String(r.i + 1) }); } },
          { id: 'tok_s', t: 'Speed', u: 'tok/s', n: 1, best: 'max', key: 'tok_s', cell: function (r) { return f2(r.tok_s); } },
          { id: 'prefill', t: 'Prompt read', u: 's', n: 1, best: 'min', key: 'prefill_s', cell: function (r) { return f2(r.prefill_s, 1); } },
          { id: 'rss', t: 'Memory', u: 'GB, process', n: 1, key: 'rss', cell: function (r) { return f2(r.rss, 1); } },
          { id: 'threads', t: 'Threads', n: 1, key: 'threads' },
          { id: 'hit', t: 'Expert hits', u: '%, cache', n: 1, key: 'hit', cell: function (r) { return f2(r.hit, 1); } },
          { id: 'tokens', t: 'Generated', u: 'tokens', n: 1, key: 'tokens', cell: function (r) { return r.tokens == null ? '—' : String(r.tokens); } },
          { id: 'status', t: 'Status', key: 'status', cell: function (r) { return r.status === 'ok' ? chip('st-done', 'OK') : chip('st-failed', r.status); } },
          { t: 'Settings', cell: function (r) {
            return h('details', { class: 'x' }, h('summary', { text: 'Show', 'aria-label': 'Settings for run ' + r.run }),
              h('dl', { class: 'kv', style: 'margin-top:6px;min-width:280px;white-space:normal' }, [['Engine', r.config], ['Environment', r.env]].map(function (x) { return [h('dt', { text: x[0] }), h('dd', { class: 'mono', text: x[1] || '—' })]; })));
          } }
        ] }));
    }
    var sOrder = orderField('f-speed-order', [['saved', 'Newest saved first'], ['fastest', 'Speed: fastest first'], ['slowest', 'Speed: slowest first']], st.sSort, function () { draw(); });
    var search = h('input', { class: 'input', id: 'f-run', type: 'search', placeholder: 'e.g. skip050, metal, t12', value: st.speedQ, oninput: function () { st.speedQ = search.value; draw(); } });
    var ok = h('input', { type: 'checkbox', id: 'f-ok', checked: st.speedOk ? '' : null, onchange: function () { st.speedOk = ok.checked; draw(); } });
    draw();
    put(out, h('div', { class: 'filters', role: 'group', 'aria-label': 'Filter runs' },
        h('div', { class: 'field' }, h('label', { for: 'f-run', text: 'Search runs' }), search),
        h('label', { class: 'check', for: 'f-ok' }, ok, h('span', { text: 'Successful runs only' })),
        sOrder),
      count, box,
      h('p', { class: 'hint', text: 'One row per engine run (results/runs.csv). Decode speed is generated tokens per second after the prompt is read. Open "Settings" for the exact engine flags and environment. Generated answers for quality benches are under Answer quality.' }));
    return out;
  }

  function coverageView(d) {
    var suite = d.suite.benches;
    var cov = table([{ t: 'Model' }].concat(suite.map(function (b) { return { t: b.name }; })), d.models.map(function (m) {
      return h('tr', {}, td(h('div', { class: 'stack', style: 'gap:2px' }, h('strong', { text: m.name }),
          h('span', { class: 'hint', text: m.installed ? 'Installed · ' + m.covered + ' of ' + suite.length + ' benches' : (m.download ? 'Downloading ' + pct(m.download.done, m.download.total) + '%' : 'Not installed') }),
          !m.installed && !m.download ? h('a', { href: '#models', text: 'Download in Models' }) : null)),
        suite.map(function (b) {
          var c = m.coverage[b.id];
          var can = m.installed && c.status !== 'running' && (b.id === 'quiet' ? m.owner_model : m.suite);
          return td(covCell(c, can ? function () { queueBench(b.id, m); } : null));
        }));
    }), 'Which standard benches each model has');
    var suiteTbl = table(['Bench', 'What it measures', { t: 'Duration', u: 'int4, busy Mac' }, 'Runs with'], suite.map(function (b) {
      return h('tr', {}, td(h('strong', { text: b.name })), td(b.what, 'wrap'), td(b.duration), td(h('span', { class: 'mono', text: b.runs_with })));
    }), 'Standard bench definitions');
    return h('div', { class: 'stack' }, h('p', { class: 'muted', text: 'The standard benches every model gets, so models are comparable. "Queue" adds the bench to the end of the queue; it starts when the GPU is free.' }),
      cov, section('Bench definitions', null, suiteTbl));
  }

  function screenBench(main, spec) {
    var q = (spec || '').split('?'), name = decodeURIComponent(q[0]), params = new URLSearchParams(q[1] || '');
    return api('/api/bench?name=' + encodeURIComponent(name)).then(function (d) {
      var state = { style: params.get('style') || 'all', config: params.get('config') || 'all', correct: params.get('grade') || 'all' };
      var list = h('div', { class: 'stack' }), count = h('p', { class: 'hint', role: 'status' });
      var vals = function (k) { return uniq(d.answers.map(function (a) { return a[k]; })); };
      function draw() {
        var rows = d.answers.filter(function (a) {
          return (state.style === 'all' || a.style === state.style) && (state.config === 'all' || a.config === state.config) &&
            (state.correct === 'all' || String(a.correct) === state.correct);
        });
        count.textContent = rows.length + ' of ' + d.answers.length + ' answers';
        list.textContent = '';
        list.appendChild(table(['Prompt', 'Style', 'Setting', 'Grade', { t: 'Answer time', u: 's', n: 1 }, { t: 'Output', u: 'tokens', n: 1 }, 'Answer'], rows.map(function (a) {
          var lossy = a.config !== 'exact' && a.config !== 'native';
          var det = h('details', { class: 'x' }, h('summary', { text: 'Show answer', 'aria-label': 'Show answer to ' + a.id + ', ' + a.style + ', ' + (CFG[a.config] || a.config) }),
            h('p', { class: 'hint', style: 'white-space:normal;max-width:60ch', text: a.prompt || '' }), h('pre', { class: 'ans', text: a.text || '(no answer: the run failed or was refused)' }));
          return h('tr', { class: lossy ? 'lossy' : null }, td(h('span', { class: 'mono', style: 'white-space:nowrap', text: a.id })), td(a.style), td(h('span', { class: 'row', style: 'gap:6px;flex-wrap:nowrap' }, CFG[a.config] || a.config, lossy ? lossyTag() : null)),
            td(a.correct === true ? h('span', { class: 'verdict v-improves', text: '✓ Correct' }) : a.correct === false ? h('span', { class: 'verdict v-worse', text: '✗ Incorrect (auto)' }) : h('span', { class: 'verdict v-pending', text: 'Not graded' })),
            td(f2(a.answer_s, 1), 'n'), td(a.output_tokens == null ? '—' : a.output_tokens, 'n'), td(det));
        }), 'Answers of bench ' + name));
      }
      var filters = h('div', { class: 'filters', role: 'group', 'aria-label': 'Filter answers' },
        selectField('a-style', 'Style', [['all', 'All styles']].concat(vals('style').map(function (v) { return [v, cap(v)]; })), state.style, function (v) { state.style = v; draw(); }),
        selectField('a-config', 'Setting', [['all', 'All settings']].concat(vals('config').map(function (v) { return [v, CFG[v] || v]; })), state.config, function (v) { state.config = v; draw(); }),
        selectField('a-grade', 'Grade', [['all', 'All grades'], ['true', 'Correct'], ['false', 'Incorrect'], ['null', 'Not graded']], state.correct, function (v) { state.correct = v; draw(); }));
      put(main, header('Answers · bench ' + name, 'Every generated answer with its automatic grade. A manual review may correct grader errors.', h('a', { class: 'btn', href: '#results', text: '← Results' })), filters, count, list);
      draw();
    });
  }

  function screenRuns(main) {
    return api('/api/runs').then(function (d) {
      var q = { text: '', status: 'all' }, body = h('div', { class: 'stack' });
      function draw() {
        body.textContent = '';
        var rows = d.runs.filter(function (r) {
          return (q.status === 'all' || r.status === q.status) && (!q.text || (r.run + ' ' + r.env + ' ' + r.config).toLowerCase().indexOf(q.text) >= 0);
        });
        body.appendChild(h('p', { class: 'hint', text: rows.length + ' of ' + d.runs.length + ' runs' }));
        body.appendChild(table(['Run', 'Backend', { t: 'Thr.', n: 1 }, { t: 'Tok.', n: 1 }, { t: 'tok/s', n: 1 }, { t: 'Prompt read s', n: 1 }, { t: 'Hit %', n: 1 }, 'Time shares', 'Status', 'Output'], rows.map(function (r) {
          var lossy = /DEGRADE_ZERO=1/.test(r.config + r.env) || /^(l[1-9]|q[1-9]|f\d-d|r2-k|t-metal-skip|v4|v5)/.test(r.run);
          var s = [r.io_pct, r.matmul_pct, r.attn_pct, r.other_pct].map(Number);
          var bar = r.io_pct ? h('div', { class: 'bar', role: 'img', 'aria-label': 'SSD ' + s[0] + '%, math ' + s[1] + '%, attention ' + s[2] + '%, other ' + s[3] + '%', title: 'SSD ' + s[0] + '% · math ' + s[1] + '% · attention ' + s[2] + '% · other ' + s[3] + '%', style: 'min-width:120px' },
            h('span', { style: 'width:' + s[0] + '%;background:var(--fg)' }), h('span', { class: 'hatch', style: 'width:' + s[1] + '%;box-shadow:none' }),
            h('span', { style: 'width:' + s[2] + '%;background:var(--fg-2)' }), h('span', { style: 'width:' + s[3] + '%;background:var(--line)' })) : h('span', { class: 'hint', text: '—' });
          var out = h('details', { class: 'x' }, h('summary', { text: 'Show' }));
          out.addEventListener('toggle', function () {
            if (out.open && !out.dataset.loaded) {
              out.dataset.loaded = 1;
              api('/api/run-output?run=' + encodeURIComponent(r.run)).then(function (o) { out.appendChild(h('pre', { class: 'ans', text: o.text || '(no answer text)' })); });
            }
          });
          return h('tr', { class: lossy ? 'lossy' : null },
            td(h('div', { class: 'stack', style: 'gap:2px' }, h('span', { class: 'mono', text: r.run }), lossy ? lossyTag() : null)), td(r.backend), td(r.omp_threads || '—', 'n'),
            td(r.decode_tokens || '—', 'n'), td(h('strong', { text: r.tok_s || '—' }), 'n'), td(r.prefill_s || '—', 'n'), td(r.hit_pct || '—', 'n'), td(bar),
            td(chip(r.status === 'ok' ? 'st-done' : 'st-failed', r.status === 'ok' ? 'Done' : r.status)), td(out));
        })));
      }
      put(main, header('Runs and results', 'Every published engine run. Raw logs stay on this Mac; published copies never contain home paths.', ghLink('published-results/glm-20261018/runs.csv', 'runs.csv on GitHub')),
        h('div', { class: 'filters', role: 'toolbar', 'aria-label': 'Filters' },
          h('input', { class: 'input', type: 'search', placeholder: 'Filter by run or setting', 'aria-label': 'Filter runs', oninput: function (e) { q.text = e.target.value.toLowerCase(); draw(); } }),
          h('select', { class: 'input', 'aria-label': 'Status', onchange: function (e) { q.status = e.target.value; draw(); } }, ['all', 'ok', 'failed', 'refused (RAM)'].map(function (v) { return h('option', { value: v, text: v === 'all' ? 'All statuses' : v }); })),
          h('span', { class: 'hint', style: 'margin-left:auto', text: 'Time shares: solid SSD wait · hatched math · grey attention · light other' })),
        body, h('p', { class: 'hint', text: 'tok/s = generation only. Single runs; differences under ~10% are noise. Runs on a busy machine unless made with glm_quiet.py.' }));
      draw();
    });
  }

  /* Not-run helpers shared by Experiments and the home card. Everything queued from either waits for a quiet machine. */
  function about(s) { return s == null ? '' : s >= 3600 ? 'about ' + (s / 3600).toFixed(1).replace('.0', '') + ' h' : 'about ' + Math.max(1, Math.round(s / 60)) + ' min'; }
  function newBadge() { return h('span', { class: 'new-badge', text: 'new' }); }
  function quietHint(d) {
    return 'Everything queued from here waits for a quiet machine (≥ ' + ((d && d.quiet_threshold_gb) || 20) + ' GB free for ' +
      Math.round(((d && d.quiet_hold_s) || 120) / 60) + ' min), then runs one at a time, after anything already queued.';
  }
  function queueNotRun(x) {
    if (x.queue && x.queue.selection) return post('/api/queue/add-selection', { ids: [x.queue.selection], only_when_quiet: true });
    return post('/api/queue/add', { kind: 'planned', args: { id: x.id }, only_when_quiet: true });
  }
  // Queue several in order; a long batch (over an hour or more than ten items) asks first.
  function queueAllNotRun(list, d, done) {
    var total = list.reduce(function (a, x) { return a + (x.est_s || 0); }, 0);
    var ask = total > 3600 || list.length > 10 ? confirmDialog({ eyebrow: 'Queue all ready', title: 'Queue ' + list.length + ' items, ' + about(total) + '?',
      sub: quietHint(d), confirm: 'Queue ' + list.length,
      rows: [['Items', list.length + ' (' + list.map(function (x) { return x.title; }).slice(0, 3).join(', ') + (list.length > 3 ? ', …' : '') + ')'],
             ['Time', about(total) + ' of GPU time in all'], ['Changes later', 'remove any of them from Queue and logs']] }) : Promise.resolve(true);
    return ask.then(function (ok) {
      if (!ok) return done(false);
      return list.reduce(function (pr, x) { return pr.then(function () { return queueNotRun(x); }); }, Promise.resolve())
        .then(function () { toast('Queued ' + list.length + ' (' + about(total) + '). They start when the machine is quiet.', false, ['#queue', 'View queue']); done(true); },
              function (er) { toast(er.message, true); done(true); });
    });
  }
  function prepLink(x, label) {
    return x.needs_model || x.prep_cmd ? h('a', { class: 'btn btn-sm', href: '#install', text: label || 'Models' }) : null;
  }

  // ---------- Experiments: not run yet (ready / needs / ideas) and done ----------
  var VTXT = { improves: ['v-improves', '▲ improves'], worse: ['v-worse', '▼ worse'], failed: ['v-failed', '✗ failed'], 'no clear change': ['v-same', '= no clear change'] };
  var DONE_COLS = 'minmax(260px, 2.6fr) 150px 140px 90px 100px 100px';
  var expTab = 'notrun';
  function screenExperiments(main) {
    return Promise.all([api('/api/experiments'), api('/api/not-run')]).then(function (res) {
      var d = res[0], nr = res[1];
      var notRun = d.entries.filter(function (e) { return e.verdict === 'not run' && e.status; });
      var done = d.entries.filter(function (e) { return e.verdict !== 'not run'; }).sort(function (a, b) { return (b.date || '').localeCompare(a.date || ''); });
      var ready = notRun.filter(function (e) { return e.status === 'ready'; })
        .sort(function (a, b) { return (!!b.queued - !!a.queued) || (a.queue_pos || 0) - (b.queue_pos || 0); });   // queued in line order first
      var needs = notRun.filter(function (e) { return e.status === 'needs'; });
      var ideas = notRun.filter(function (e) { return e.status === 'idea'; });
      var toQueue = ready.filter(function (e) { return !e.queued; });
      var newIds = {};
      nr.experiments.forEach(function (x) { if (x.new) newIds[x.id] = 1; });
      var body = h('div'), tabs = h('div', { class: 'tabs', role: 'tablist', 'aria-label': 'Experiments' });

      function titleLine(e, size) {
        return h('div', { class: 'row', style: 'gap:6px 10px' }, h('h3', { class: 'xtitle', id: 'x-' + e.id, style: size ? 'font-size:' + size + 'px' : null, text: e.title }),
          newIds[e.id] ? newBadge() : null, e.lossy ? h('span', { class: 'tag tag-lossy', text: size ? 'changes output' : 'changes output, check quality after' }) : null);
      }
      function why(e, clamp) { return e.hypothesis ? h('p', { class: clamp ? 'clamp2' : null, style: 'font-size:14px;line-height:21px' }, h('span', { class: 'muted', text: 'Why: ' }), e.hypothesis) : null; }
      function setting(e) {
        return h('p', { class: 'hint', style: 'overflow-wrap:anywhere' }, e.change ? ['Setting ', h('span', { class: 'mono', style: 'font-size:11px', text: e.change }), ' · '] : null,
          (e.category || '').replace(/-/g, ' '), ' · ', h('span', { class: 'mono', style: 'font-size:11px', text: e.id }));
      }
      function readyRow(e) {
        return h('article', { class: 'xrow', 'aria-labelledby': 'x-' + e.id }, h('div', { class: 'xmain' }, titleLine(e), why(e), setting(e)),
          h('div', { class: 'xside' },
            h('div', { class: 'row', style: 'gap:8px' }, h('span', { class: 'chip ' + (e.queued ? 'st-queued' : 'st-done'), text: e.queued ? 'queued' : 'ready' }), h('span', { class: 'hint num', text: about(e.est_s) })),
            e.queued ? h('span', { class: 'hint' }, (e.queue_pos ? 'Queued, number ' + e.queue_pos + ' in line. ' : 'Queued. '), h('a', { href: '#queue', text: 'Open queue' }))
              : h('div', { class: 'row', style: 'gap:6px' },
                h('button', { type: 'button', class: 'btn btn-sm btn-primary', 'aria-label': 'Queue ' + e.title, text: 'Queue', onclick: function (ev) {
                  ev.target.disabled = true;
                  queueNotRun(e).then(function () { toast('Queued: ' + e.title + '. It starts when the machine is quiet.', false, ['#queue', 'View queue']); route(); },
                    function (er) { ev.target.disabled = false; toast(er.message, true); });
                } }),
                h('button', { type: 'button', class: 'btn btn-sm', 'aria-label': 'Run now: ' + e.title, text: 'Run now', onclick: function () { runOrQueue('planned', { id: e.id }, e.title, false); } }))));
      }
      function needsRow(e) {
        return h('article', { class: 'xrow', 'aria-labelledby': 'x-' + e.id }, h('div', { class: 'xmain' }, titleLine(e), why(e), setting(e)),
          h('div', { class: 'xside' },
            h('div', { class: 'row', style: 'gap:8px' }, h('span', { class: 'chip st-blocked', text: 'needs something' }), h('span', { class: 'hint num', text: about(e.est_s) })),
            h('p', { style: 'font-size:13px;line-height:19px;overflow-wrap:anywhere' }, h('strong', { text: 'Needs: ' }), e.needs),
            e.needs_model || e.prep_cmd ? h('div', { class: 'stack', style: 'gap:4px' }, prepLink(e, 'Prepare it in Models'),
              e.prep_cmd ? h('span', { class: 'hint' }, 'or in a terminal: ', h('span', { class: 'mono', style: 'font-size:11px', text: e.prep_cmd })) : null) : null));
      }
      function ideaRow(e) {
        var long = (e.needs || '').length > 140;
        return h('article', { class: 'xrow', style: 'padding:12px 0', 'aria-labelledby': 'x-' + e.id },
          h('div', { class: 'xmain' }, titleLine(e, 15), why(e, true),
            h('p', { class: 'hint' }, h('span', { class: 'mono', style: 'font-size:11px', text: e.id }), ' · ' + (e.category || '').replace(/-/g, ' '))),
          h('div', { class: 'xside' }, h('span', { class: 'chip st-idea', text: 'idea' }),
            e.needs ? h('p', { class: 'clamp2', style: 'font-size:13px;line-height:19px' }, h('strong', { text: 'Waiting for: ' }), e.needs) : null,
            long ? h('details', { class: 'hint' }, h('summary', { style: 'cursor:pointer', text: 'Full note' }), h('p', { style: 'padding-top:4px;font-size:13px;line-height:19px;color:var(--fg)', text: e.needs })) : null,
            prepLink(e)));
      }
      function group(id, chipCls, chipText, title, items, right, hint, rowFn) {
        return h('section', { class: 'stack', style: 'gap:4px', 'aria-labelledby': id },
          h('div', { class: 'grp-h' }, h('h2', { id: id }, h('span', { class: 'chip ' + chipCls, style: 'vertical-align:3px;margin-right:8px', text: chipText }), title, h('span', { class: 'count num', text: items.length })), right),
          hint ? h('p', { class: 'hint', style: 'padding-top:4px', text: hint }) : null,
          items.length ? items.map(rowFn) : h('p', { class: 'hint', style: 'padding:14px 0', text: 'None right now.' }));
      }
      function drawNotRun() {
        var total = toQueue.reduce(function (a, e) { return a + (e.est_s || 0); }, 0);
        var qAll = h('button', { type: 'button', class: 'btn btn-primary', disabled: toQueue.length ? null : '',
          text: toQueue.length ? 'Queue all ready (' + toQueue.length + ', ' + about(total) + ')' : 'All ready experiments are queued',
          onclick: function (ev) { ev.target.disabled = true; queueAllNotRun(toQueue, nr, function (didQueue) { if (didQueue) route(); else ev.target.disabled = false; }); } });
        var nNew = notRun.filter(function (e) { return newIds[e.id]; }).length;
        return h('div', { class: 'stack', style: 'gap:30px' },
          h('p', { style: 'font-size:15px;line-height:23px;max-width:760px' },
            notRun.length + ' experiments have never run: ' + ready.length + ' ready (' + (ready.length - toQueue.length) + ' queued), ' + needs.length + ' need' + (needs.length === 1 ? 's' : '') +
            ' something first, ' + ideas.length + ' are ideas. ' + nNew + ' were added in the last ' + nr.new_days + ' days. ',
            h('a', { href: '#experiments', 'data-jump': 'g-ready', text: 'Ready' }), ' · ', h('a', { href: '#experiments', 'data-jump': 'g-needs', text: 'Needs something' }), ' · ',
            h('a', { href: '#experiments', 'data-jump': 'g-ideas', text: 'Ideas' })),
          group('g-ready', 'st-done', 'ready', 'Ready to run ', ready, qAll, quietHint(nr) + ' The quiet run also picks up ready experiments.', readyRow),
          group('g-needs', 'st-blocked', 'needs something', 'Needs something first ', needs, null, null, needsRow),
          group('g-ideas', 'st-idea', 'idea', 'Ideas ', ideas, h('span', { class: 'hint', text: 'Not runnable unattended yet: each says what it is waiting for.' }), null, ideaRow),
          h('p', { class: 'hint' }, 'Standard benches an installed model has never had show as “never run” in the ', h('a', { href: '#dashboard', text: 'Run benchmarks' }), ' grid.'));
      }
      function drawDone() {
        var head = h('div', { class: 'tr', role: 'row', style: 'grid-template-columns:' + DONE_COLS },
          [['Experiment'], ['Verdict'], ['tok/s, ref → new', 1], ['Change', 1], ['Output'], ['Date']].map(function (c) {
            return h('div', { class: 'th', role: 'columnheader', style: c[1] ? 'text-align:right' : null, text: c[0] });
          }));
        var rows = done.map(function (e) {
          var m = e.metrics || {}, v = VTXT[e.verdict] || ['v-pending', e.verdict];
          var det = h('details', { class: 'x' }, h('summary', { text: 'Why and result' }),
            h('dl', { class: 'kv', style: 'font-size:13px' }, [['Change', e.change], ['Why', e.hypothesis], ['Result', e.conclusion || (e.effects || []).join('; ')], ['Tradeoffs', e.tradeoffs], ['Reference', e.ref], ['Runs', (e.runs || []).join(', ')]]
              .filter(function (x) { return x[1]; }).map(function (x) { return [h('dt', { text: x[0] }), h('dd', { text: x[1] })]; })));
          return h('div', { class: 'tr' + (e.lossy ? ' lossy' : ''), role: 'row', style: 'grid-template-columns:' + DONE_COLS },
            h('div', { class: 'td stack', role: 'rowheader', style: 'gap:2px' },
              h('span', { class: 'row', style: 'gap:4px 8px' }, h('strong', { text: e.title }), e.lossy ? lossyTag() : null,
                e.everyday ? h('span', { class: 'tag tag-usable', text: 'everyday · by owner' }) : e.usable ? h('span', { class: 'tag tag-usable', text: 'usable · by owner' }) : null),
              h('span', { class: 'mono muted', style: 'font-size:11px', text: e.id }), det),
            h('div', { class: 'td', role: 'cell' }, h('span', { class: 'verdict ' + v[0], text: v[1] })),
            h('div', { class: 'td num', role: 'cell', style: 'text-align:right', text: m.tok_s == null ? '—' : (m.ref_tok_s == null ? '' : f2(m.ref_tok_s) + ' → ') + f2(m.tok_s) }),
            h('div', { class: 'td num', role: 'cell', style: 'text-align:right', text: m.speed_change_pct == null ? '—' : (m.speed_change_pct > 0 ? '+' : '') + Math.round(m.speed_change_pct) + '%' }),
            h('div', { class: 'td', role: 'cell', text: m.output && m.output !== 'n/a' ? m.output : '—' }),
            h('div', { class: 'td num muted', role: 'cell', text: e.date || '' }));
        });
        return h('div', { class: 'stack', style: 'gap:10px' },
          h('p', { class: 'hint', text: 'Verdicts compare each run with its reference run; changes under about 10% are noise on this busy machine.' }),
          h('div', { style: 'overflow-x:auto' }, h('div', { class: 'tbl', role: 'table', 'aria-label': 'Finished experiments', style: 'min-width:860px' }, head, rows)));
      }
      function draw() {
        fill(tabs, [['notrun', 'Not run yet', notRun.length], ['done', 'Done', done.length]].map(function (t) {
          return h('button', { type: 'button', class: 'tab', role: 'tab', 'aria-selected': t[0] === expTab ? 'true' : 'false', onclick: function () { expTab = t[0]; draw(); } },
            t[1], h('span', { class: 'count num', text: t[2] }));
        }));
        fill(body, expTab === 'done' ? drawDone() : drawNotRun());
      }
      // in-page jumps; the hash stays the route
      body.addEventListener('click', function (ev) {
        var a = ev.target.closest('a[data-jump]');
        if (!a) return;
        ev.preventDefault();
        var t = document.getElementById(a.getAttribute('data-jump'));
        if (t) t.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
      put(main, header('Experiments', 'Ideas to make GLM-5.3 faster on this Mac: what each one tries, and whether it can run.'), tabs, body);
      draw();
    });
  }

  function screenLeaderboard(main) {
    return Promise.all([api('/api/benches'), api('/api/runs'), api('/api/models'), api('/api/external')]).then(function (res) {
      var benches = res[0], runs = res[1].runs, models = res[2].models, ext = res[3];
      var benchModel = {};
      models.forEach(function (m) { (m.bench_names || []).forEach(function (n) { benchModel[n] = m.name; }); });
      var strong = [];
      benches.results.forEach(function (r) {
        r.summary.forEach(function (s) { strong.push(Object.assign({ bench: r.name, model: benchModel[r.name] || '?' }, s)); });
      });
      strong.sort(function (a, b) { return (b.correct / b.graded) - (a.correct / a.graded) || a.answer_s - b.answer_s; });
      var strongTbl = table(['Model', 'Bench', 'Style', 'Config', { t: '% correct (auto)', n: 1 }, { t: 'Mean answer s', n: 1 }, { t: 'Decode tok/s', n: 1 }], strong.map(function (s) {
        var lossy = s.config !== 'exact';
        return h('tr', { class: lossy ? 'lossy' : null }, td(s.model), td(s.bench), td(s.style), td(h('span', { class: 'row' }, CFG[s.config] || s.config, lossy ? lossyTag() : null)),
          td(pct(s.correct, s.graded) + '%', 'n'), td(f2(s.answer_s, 1), 'n'), td(f2(s.decode_tok_s), 'n'));
      }));
      var ok = runs.filter(function (r) { return r.status === 'ok' && r.tok_s; }).sort(function (a, b) { return b.tok_s - a.tok_s; }).slice(0, 25);
      var fastTbl = table(['Run', 'Backend', { t: 'Thr.', n: 1 }, { t: 'tok/s', n: 1 }, { t: 'Prompt read s', n: 1 }, 'Output'], ok.map(function (r) {
        var lossy = /DEGRADE_ZERO=1/.test(r.config + r.env) || /^(l[1-9]|q[1-9]|f\d-d|r2-k|t-metal-skip|v4|v5)/.test(r.run);
        return h('tr', { class: lossy ? 'lossy' : null }, td(h('span', { class: 'mono', text: r.run })), td(r.backend), td(r.omp_threads || '—', 'n'), td(h('strong', { text: r.tok_s }), 'n'), td(r.prefill_s, 'n'),
          td(lossy ? lossyTag() : exactTag()));
      }));
      var notBenched = models.filter(function (m) { return !(m.bench_names || []).length; }).map(function (m) { return m.name; });
      var intel = null;
      if (ext && ext.aa_index) {
        var aa = ext.aa_index, top = Math.max.apply(null, aa.rows.map(function (r) { return r.score; }));
        var bars = aa.rows.map(function (r) {
          return h('div', { class: 'stack', style: 'gap:3px' },
            h('div', { class: 'row between' }, h('div', { class: 'row' }, h('span', { style: r.lab ? 'font-weight:600' : null, text: r.model }),
              h('span', { class: 'pill', text: r.open_weights ? 'open weights' : 'closed' }), r.lab ? h('span', { class: 'tag tag-review', text: 'runs in this lab' }) : null),
              h('span', { class: 'num', text: r.score })),
            h('div', { class: 'score' }, h('div', { class: 'track', 'aria-hidden': 'true' }, h('span', { class: r.open_weights ? 'hatch' : null, style: 'width:' + (r.score / top * 100) + '%' }))));
        });
        var vt = ext.vendor_table, vrows = vt.rows.map(function (row) {
          var vals = row.slice(1), best = Math.max.apply(null, vals.filter(function (v) { return v != null; }));
          return h('tr', {}, td(row[0]), vals.map(function (v, i) {
            var txt = v == null ? '—' : (typeof v === 'number' && v < 1000 ? v.toFixed(1) : String(v));
            return td(h('span', { style: v === best ? 'font-weight:700' : (i === 0 ? 'text-decoration:underline' : null), text: txt }), 'n');
          }));
        });
        var dt = ext.aa_detail;
        intel = section('Intelligence vs frontier models · reported, not measured here', h('span', { class: 'hint', text: 'fetched ' + ext.fetched }),
          h('div', { class: 'stack' },
            h('div', { class: 'banner', text: ext.note }),
            card([h('div', { class: 'row between' }, h('h3', { style: 'font-size:15px', text: aa.name + ' ' + aa.version }), h('a', { href: aa.source, target: '_blank', rel: 'noopener', text: 'Source' })),
              h('span', { class: 'hint', text: 'Solid = closed frontier models, hatched = open weights. Higher is better.' }), bars,
              h('p', { class: 'hint', text: aa.caveats.join(' ') })]),
            h('div', { class: 'stack' }, h('div', { class: 'row between' }, h('h3', { style: 'font-size:15px', text: 'Vendor benchmark table (' + vt.reported_by + ')' }), h('a', { href: vt.source, target: '_blank', rel: 'noopener', text: 'Source' })),
              table(['Benchmark'].concat(vt.models.map(function (m) { return { t: m, n: 1 }; })), vrows),
              h('p', { class: 'hint', text: vt.note + ' Bold = best in row; underlined = GLM-5.3.' })),
            h('div', { class: 'stack' }, h('div', { class: 'row between' }, h('h3', { style: 'font-size:15px', text: 'GLM-5.3-Flash vs GLM-5.3 (Artificial Analysis ' + dt.version + ')' }), h('a', { href: dt.source, target: '_blank', rel: 'noopener', text: 'Source' })),
              table(['Evaluation'].concat(dt.models.map(function (m) { return { t: m, n: 1 }; })), dt.rows.map(function (r) { return h('tr', {}, td(r[0]), td(String(r[1]), 'n'), td(String(r[2]), 'n')); })))));
      }
      put(main, header('Leaderboard', 'Strongest (quality bench) and fastest (generation speed). Lossy results always carry "changes output".'), intel,
        section('Strongest · quality bench', null, h('div', { class: 'stack' }, strongTbl,
          h('p', { class: 'hint', text: 'Not benched yet: ' + (notBenched.join(', ') || 'none') + '. Automatic grades; see the manual review for corrections.' }))),
        section('Fastest · top 25 runs by generation speed', null, h('div', { class: 'stack' }, fastTbl, h('p', { class: 'hint', text: 'Single runs on a busy machine; the sky/code prompts differ in length, so compare like with like.' }))));
    });
  }

  function screenResearch(main) {
    return api('/api/research').then(function (d) {
      var dec = 'all', body = h('div', { class: 'stack' }), tabs = h('div', { class: 'tabs', role: 'tablist' });
      var key = function (x) { return (x.decision.match(/^(tested|candidate|watch|rejected|reference)/) || ['other'])[0]; };
      function draw() {
        tabs.textContent = ''; body.textContent = '';
        ['all', 'candidate', 'watch', 'tested', 'rejected', 'reference'].forEach(function (k) {
          var n = d.items.filter(function (x) { return k === 'all' || key(x) === k; }).length;
          tabs.appendChild(h('button', { class: 'tab', role: 'tab', 'aria-selected': k === dec ? 'true' : 'false', onclick: function () { dec = k; draw(); } }, k, h('span', { class: 'count', text: n })));
        });
        body.appendChild(table(['Item', 'Type', 'What it does', 'Relevance here', 'Decision', 'Reviewed'], d.items.filter(function (x) { return dec === 'all' || key(x) === dec; }).map(function (x) {
          return h('tr', {}, td(x.link ? h('a', { href: x.link, target: '_blank', rel: 'noopener', text: x.item.replace(/`/g, '') }) : x.item.replace(/`/g, ''), 'wrap'),
            td(x.type), td(x.what, 'wrap'), td(x.relevance, 'wrap'), td(h('strong', { text: x.decision })), td(x.reviewed, 'n'));
        })));
      }
      put(main, header('Research', 'The research watch list (research/watchlist.md). Next scheduled scan: ' + (d.next_scan || '—') + '.', ghLink('research/watchlist.md', 'Watch list on GitHub')),
        tabs, body, section('Scan log', null, table(['Date', 'Scope', 'By'], d.scans.map(function (s) { return h('tr', {}, td(s.date), td(s.scope, 'wrap'), td(s.by)); }))));
      draw();
    });
  }


  function screenQueue(main) {
    return Promise.all([api('/api/queue'), api('/api/now'), api('/api/experiments')]).then(function (res) {
      var q = res[0], now = res[1], exps = res[2].entries;
      setGpu(now);
      var running = now.jobs.filter(function (j) { return j.gpu; });
      var items = q.items.map(function (it, i) {
        return h('tr', {}, td(String(i + 1), 'n'), td(h('div', { class: 'stack', style: 'gap:2px' }, h('strong', { text: it.title }),
          h('span', { class: 'hint', text: it.kind + ' · added ' + it.added + (it.only_when_quiet ? ' · only when quiet (≥ 20 GB free)' : '') }))),
          td(h('div', { class: 'row' },
            h('button', { type: 'button', class: 'icon-btn', 'aria-label': 'Move up', disabled: i === 0 ? '' : null, onclick: function () { post('/api/queue/move', { qid: it.qid, dir: 'up' }).then(route); }, text: '↑' }),
            h('button', { type: 'button', class: 'icon-btn', 'aria-label': 'Move down', disabled: i === q.items.length - 1 ? '' : null, onclick: function () { post('/api/queue/move', { qid: it.qid, dir: 'down' }).then(route); }, text: '↓' }),
            h('button', { type: 'button', class: 'btn btn-sm btn-danger', onclick: function () { post('/api/queue/remove', { qid: it.qid }).then(function () { toast('Removed: ' + it.title); route(); }); }, text: 'Remove' }))));
      });
      // add forms
      var benchName = h('input', { class: 'input', id: 'bn', value: 'v2', style: 'width:120px', 'aria-label': 'Bench name' });
      var cfgs = ['exact', 'd030', 'd050', 'd030t12', 'd040t12'], styles = ['normal', 'terse'];
      var cbox = function (v, checked, label) { return h('label', { class: 'row', style: 'gap:4px;font-size:13px' }, h('input', { type: 'checkbox', value: v, checked: checked ? '' : null }), label || CFG[v] || v); };
      var cfgBox = h('div', { class: 'row' }, cfgs.map(function (c) { return cbox(c, c === 'd030t12'); }));
      var styBox = h('div', { class: 'row' }, styles.map(function (s) { return cbox(s, s === 'terse'); }));
      var vals = function (box) { return Array.prototype.filter.call(box.querySelectorAll('input'), function (i) { return i.checked; }).map(function (i) { return i.value; }); };
      var benchForm = card([h('h3', { style: 'font-size:15px', text: 'Add a quality bench' }),
        h('div', { class: 'field' }, h('label', { for: 'bn', text: 'Results name (results/glm-bench-NAME; reuse a name to resume or add configs)' }), benchName),
        h('div', { class: 'field' }, h('span', { class: 'hint', text: 'Configs' }), cfgBox), h('div', { class: 'field' }, h('span', { class: 'hint', text: 'Prompt styles' }), styBox),
        h('div', { class: 'row' }, h('button', { type: 'button', class: 'btn btn-primary', text: 'Add to queue', onclick: function () {
          post('/api/queue/add', { kind: 'bench', args: { name: benchName.value.trim(), configs: vals(cfgBox), styles: vals(styBox) } })
            .then(function (r) { toast('Queued: ' + r.queued.title); route(); }, function (e) { toast(e.message, true); });
        } }))]);
      var qFlags = h('div', { class: 'row' }, [['ram-sweep', true, 'RAM sweep'], ['skip-original', true, 'skip original engine'], ['experiments-only', false, 'planned experiments only']]
        .map(function (f) { return cbox(f[0], f[1], f[2]); }));
      var quietForm = card([h('h3', { style: 'font-size:15px', text: 'Add a quiet run' }), qFlags,
        h('p', { class: 'hint', text: 'Waits until at least 20 GB is free; close apps to let it start.' }),
        h('div', { class: 'row' }, h('button', { type: 'button', class: 'btn btn-primary', text: 'Add to queue (when quiet)', onclick: function () {
          post('/api/queue/add', { kind: 'quiet', args: { flags: vals(qFlags) }, only_when_quiet: true }).then(function (r) { toast('Queued: ' + r.queued.title); route(); }, function (e) { toast(e.message, true); });
        } }))]);
      var ready = exps.filter(function (e) { return e.verdict === 'not run' && e.plan; });
      var expSel = h('select', { class: 'input', 'aria-label': 'Planned experiment' }, ready.map(function (e) { return h('option', { value: e.id, text: e.title }); }));
      var expForm = card([h('h3', { style: 'font-size:15px', text: 'Add a planned experiment' }), expSel,
        h('p', { class: 'hint', text: 'Blocked experiments (missing model or engine) are skipped with the reason in their log.' }),
        h('div', { class: 'row' }, h('button', { type: 'button', class: 'btn btn-primary', text: 'Add to queue', onclick: function () { runOrQueue('planned', { id: expSel.value }, expSel.value, true); } }))]);
      var jobsTbl = table(['Job', 'Started', 'Status', 'Log'], q.jobs.map(function (j) {
        var det = h('details', { class: 'x' }, h('summary', { text: 'Show log' }));
        det.addEventListener('toggle', function () {
          if (det.open && !det.dataset.loaded) { det.dataset.loaded = 1; api('/api/job-log?id=' + encodeURIComponent(j.id)).then(function (l) { det.appendChild(h('pre', { class: 'log', text: l.tail.join('\n') })); }); }
        });
        var cls = { running: 'st-running', done: 'st-done', finished: 'st-done', failed: 'st-failed' }[j.status] || 'st-waiting';
        return h('tr', {}, td(h('div', { class: 'stack', style: 'gap:2px' }, h('span', { text: j.title }), h('span', { class: 'hint mono', text: 'PID ' + j.pid + ' · ' + j.source }))),
          td(j.started), td(chip(cls, j.status + (j.exit != null && j.status !== 'done' ? ' (' + j.exit + ')' : ''))), td(h('div',{class:'stack'},resumeButton(j,q.items),det), 'wrap'));
      }));
      put(main, header('Queue', 'GPU jobs run one after another. The runner starts the first item when the GPU lock is free and no engine is running.',
          h('button', { type: 'button', class: 'btn', text: q.paused ? 'Resume queue' : 'Pause queue', onclick: function () { post('/api/queue/pause', { paused: !q.paused }).then(route); } })),
        h('div', { class: 'banner', text: 'Runner: ' + (q.runner || '—') + (q.paused ? ' · queue paused' : '') + ' · Running now: ' + (running.length ? running.map(function (j) { return j.title + ' (PID ' + j.pid + ')'; }).join(', ') : 'nothing') }),
        timelineCard(q.timeline, false),
        section('Waiting · ' + q.items.length, null, q.items.length ? table([{ t: '#', n: 1 }, 'Job', 'Order'], items) : h('p', { class: 'muted', text: 'Nothing waiting.' })),
        h('div', { class: 'grid3' }, benchForm, quietForm, expForm),
        section('Recent jobs started by the app', null, q.jobs.length ? jobsTbl : h('p', { class: 'muted', text: 'None yet.' })));
    });
  }


  // ---------- models: disk, downloads, install and remove ----------
  function screenModels(main) {
    return Promise.all([api('/api/models'), api('/api/now'), api('/api/storage')]).then(function (res) {
      var ms = res[0].models, nSuite = res[0].suite.benches.length, now = res[1], store = res[2];
      var free = store.disk_free_gb != null ? store.disk_free_gb : now.machine.disk_free_gb;
      setGpu(now);
      var stored = {}; store.models.forEach(function (s) { stored[s.id] = s; });
      var labGb = store.models.reduce(function (a, m) { return a + (m.gb || 0); }, 0);
      var otherGb = store.other.reduce(function (a, m) { return a + (m.gb || 0); }, 0);
      var dlJobs = now.jobs.filter(function (j) { return j.kind === 'Download'; });
      var gpuBusy = now.jobs.some(function (j) { return j.gpu; });
      var pending = ms.filter(function (m) { return !m.installed && m.download_gb; }).reduce(function (a, m) { return a + m.download_gb - (m.download ? m.download.done : 0); }, 0);
      var gb = function (v) { return v >= 100 ? Math.round(v) + ' GB' : f2(v, 1) + ' GB'; };

      function remove(m, s) {
        confirmDialog({ eyebrow: 'Move to Trash', title: 'Move ' + m.name + ' to the Trash?', danger: true, confirm: 'Move ' + gb(s.gb) + ' to the Trash',
          sub: 'Its folders move to the macOS Trash. Nothing is deleted yet: you can restore them until you empty the Trash, which frees the space.',
          rows: s.folders.filter(function (f) { return f.gb > 0 || s.folders.length === 1; }).map(function (f) { return ['Folder', f.path + ' · ' + gb(f.gb), true]; })
            .concat([['Benchmark results', 'Kept (they live in the lab repo)']]),
          note: 'Benchmarks that need this model are blocked until it is downloaded again (~' + (m.download_gb || m.size_gb) + ' GB).', warn: true })
          .then(function (ok) {
            if (ok) post('/api/remove', { model: m.id }).then(function (r) { toast('Moved to the Trash: ' + r.moved.map(function (x) { return x.src; }).join(', ')); route(); }, function (e) { toast(e.message, true); });
          });
      }
      function download(m) {
        var left = m.download_gb - (m.download ? m.download.done : 0), after = Math.round(free - left);
        confirmDialog({ eyebrow: m.download ? 'Resume download' : 'Download', title: m.name, confirm: (m.download ? 'Resume' : 'Download') + ' ~' + Math.round(left) + ' GB',
          rows: [['Source', m.source, true], ['Download size', '~' + m.download_gb + ' GB' + (m.download ? ' (' + f2(m.download.done, 1) + ' GB already here)' : '')], ['Kept on disk', '~' + m.size_gb + ' GB'],
                 ['Free disk after', '~' + after + ' GB'], ['Saved to', '~/' + (m.download_path || m.path), true], ['Runs', m.prep, true], ['Unlocks', (m.unlocks || []).join(', ') || '—']],
          warn: after < 30 || gpuBusy,
          note: after < 30 ? 'This would leave less than 30 GB free.' : gpuBusy ? 'A benchmark is running: the download will slow it and skew its timings (answers and grades are unaffected).' : 'Resumable: if it stops, start it again here.' })
          .then(function (ok) {
            if (!ok) return;
            toast('Starting the download… checking that it really runs (about 6 s).');
            post('/api/download', { model: m.id }).then(function (r) { toast('Download running: ' + r.started.title + (r.started.pid ? ' (PID ' + r.started.pid + ')' : '') + '.'); route(); },
              function (e) { toast('Download did not start: ' + e.message, true); route(); });
          });
      }

      // Disk overview: lab models / other model folders / free, to scale.
      var total = labGb + otherGb + free;
      var low = free < 30, lowAfter = free - pending < 30;
      var disk = h('section', { class: 'card', 'aria-labelledby': 'disk-h', style: 'padding:16px 20px;display:flex;flex-direction:column;gap:12px' },
        h('div', { class: 'card-head' }, h('h2', { id: 'disk-h', text: 'Disk' }), h('span', { class: 'hint', text: 'Measured now · warns below 30 GB free' })),
        h('dl', { class: 'kv2' }, [['Free', gb(free)], ['Lab models', gb(labGb)], ['Other model folders', gb(otherGb)], ['Still to download', pending ? '~' + gb(pending) : 'nothing']]
          .map(function (x) { return h('div', {}, h('dt', { text: x[0] }), h('dd', { text: x[1] })); })),
        h('div', { class: 'disk-bar', role: 'img', 'aria-label': 'Lab models ' + gb(labGb) + ', other folders ' + gb(otherGb) + ', free ' + gb(free) },
          h('span', { class: 'seg-models', style: 'width:' + (labGb / total * 100) + '%' }), h('span', { class: 'seg-other', style: 'width:' + (otherGb / total * 100) + '%' })),
        h('div', { class: 'legend', 'aria-hidden': 'true' }, h('span', {}, h('i', { style: 'background:var(--fg)' }), 'Lab models'), h('span', {}, h('i', { style: 'background:var(--fg-2)' }), 'Other folders in ~/colibri-models'),
          h('span', {}, h('i', { style: 'background:var(--sunk);box-shadow:inset 0 0 0 1px var(--line-strong)' }), 'Free')),
        low ? h('div', { class: 'notice notice-warn', role: 'alert', text: 'Less than 30 GB free. Move an unused model to the Trash and empty the Trash before downloading.' })
          : lowAfter && pending ? h('div', { class: 'notice notice-warn', text: 'Downloading every remaining model would leave ~' + gb(free - pending) + ' free.' }) : null,
        store.other.length ? h('p', { class: 'hint', text: 'Not managed by the lab: ' + store.other.map(function (o) { return o.path + ' (' + gb(o.gb) + ')'; }).join(', ') + '.' }) : null);

      // Downloads in progress
      function jobFor(m) { return dlJobs.filter(function (x) { return x.title === m.name || (x.command || '').indexOf(' ' + m.id) >= 0; })[0]; }
      var dlRows = dlJobs.map(function (j) { return { j: j, m: ms.filter(function (m) { return jobFor(m) === j; })[0] }; })
        .concat(ms.filter(function (m) { return m.download && !jobFor(m); }).map(function (m) { return { j: null, m: m }; }));
      var downloads = h('section', { class: 'card', 'aria-labelledby': 'dl-h', style: 'padding:16px 20px;display:flex;flex-direction:column;gap:12px' },
        h('div', { class: 'card-head' }, h('h2', { id: 'dl-h', text: 'Downloads' }), dlJobs.length ? chip('st-running', 'Downloading') : chip('st-waiting', 'Idle')),
        dlRows.length ? dlRows.map(function (x) {
          var j = x.j, m = x.m, p = j && j.progress && j.progress.total ? j.progress : m && m.download ? m.download : null;
          var name = m ? m.name : j.title;
          return h('div', { class: 'stack', style: 'gap:6px' },
            h('div', { class: 'row between' }, h('strong', { text: name }), p ? h('span', { class: 'num', text: pct(p.done, p.total) + '%' }) : null),
            p ? meter(p.done, p.total, 'Download of ' + name) : null,
            h('div', { class: 'row between hint num' }, h('span', { text: p ? f2(p.done, 1) + ' of ' + f2(p.total, 0) + ' GB' + (p.eta_s ? ' · ~' + dur(p.eta_s) + ' left' : '') : (j.detail || '') }),
              h('span', { text: j ? 'PID ' + j.pid + ' · running ' + dur(j.elapsed_s) : 'Stopped · resume it in the table' })),
            j && j.detail ? h('span', { class: 'hint', text: j.detail }) : null,
            j && j.stoppable ? h('div', { class: 'row' }, h('button', { type: 'button', class: 'btn btn-sm btn-danger', text: 'Stop download…', onclick: function () { stopJob(j); } }),
              h('span', { class: 'hint', text: 'Resumable: downloaded parts are kept.' })) : null);
        }) : h('p', { class: 'muted', text: 'No download running. Start one from the table below; one download runs at a time.' }));

      // Unified table
      var rows = ms.map(function (m) {
        var s = stored[m.id] || { gb: 0, folders: [], in_use: false, removable: false };
        var job = jobFor(m), jp = job && job.progress && job.progress.total ? job.progress : m.download;
        var status = job ? chip('st-running', 'Downloading' + (jp ? ' ' + pct(jp.done, jp.total) + '%' : ''))
          : m.owner_model ? chip('st-done', 'Installed · your model') : m.installed && s.in_use ? chip('st-running', 'Installed · in use')
          : m.installed ? chip('st-done', 'Installed') : m.download ? chip(dlJobs.length ? 'st-running' : 'st-paused', (dlJobs.length ? 'Downloading ' : 'Partial ') + pct(m.download.done, m.download.total) + '%')
          : chip('st-missing', 'Not installed');
        var action = job ? h('span', { class: 'hint', text: 'Downloading now · stop it above' }) : m.owner_model ? h('span', { class: 'hint', text: 'Protected: never changed by the app' })
          : m.installed ? (s.in_use ? h('span', { class: 'hint', text: 'In use by a running job: stop it first' })
            : s.removable ? h('button', { type: 'button', class: 'btn btn-sm btn-danger', 'aria-label': 'Move ' + m.name + ' to the Trash', onclick: function () { remove(m, s); }, text: 'Move to Trash…' }) : h('span', { class: 'hint', text: '—' }))
          : !m.prep ? h('span', { class: 'hint', text: 'No download step' })
          : dlJobs.length ? h('span', { class: 'hint', text: 'Wait for the running download' })
          : h('button', { type: 'button', class: 'btn btn-sm btn-primary', 'aria-label': (m.download ? 'Resume download of ' : 'Download ') + m.name, onclick: function () { download(m); }, text: (m.download ? 'Resume…' : 'Download…') });
        var ld = m.last_download;
        var details = h('details', { class: 'x' }, h('summary', { text: 'Details', 'aria-label': 'Details for ' + m.name }),
          h('dl', { class: 'kv', style: 'margin-top:6px;white-space:normal;min-width:260px' }, [['Family', m.family], ['Parameters', m.params], ['Engine', m.engine], ['Source', m.source, true],
            ['Folders', s.folders.length ? s.folders.map(function (f) { return f.path + ' · ' + gb(f.gb) + (f.in_use ? ' · in use' : ''); }).join('\n') : '~/' + m.path, true],
            ['Prepared with', m.prep, true], ['Unlocks', (m.unlocks || []).join(', ')], ['Quality benches', (m.bench_names || []).join(', ') || 'none yet']]
            .filter(function (x) { return x[1]; }).map(function (x) { return [h('dt', { text: x[0] }), h('dd', { class: x[2] ? 'mono' : null, style: 'white-space:pre-line', text: x[1] })]; })),
          ld && ld.status === 'failed' ? h('div', { class: 'stack', style: 'gap:4px;margin-top:8px' }, h('span', { class: 'chip st-failed', text: 'Last download failed · ' + ld.started + ' · exit ' + ld.exit }), h('pre', { class: 'log', text: (ld.tail || []).join('\n') })) : null);
        return h('tr', {}, td(h('div', { class: 'stack', style: 'gap:2px;min-width:200px' }, h('strong', { text: m.name }), h('span', { class: 'hint', text: [m.format, m.mtp ? 'MTP head' : null].filter(Boolean).join(' · ') }))),
          td(status), td(m.installed || m.download ? gb(s.gb || (m.download ? m.download.done : 0)) : '—', 'n'), td(m.download_gb ? '~' + m.download_gb + ' GB' : '—', 'n'),
          td(h('span', { class: 'num', text: m.covered + ' of ' + nSuite }), 'n'), td(action), td(details));
      });
      var tbl = table(['Model', 'Status', { t: 'On disk', u: 'measured', n: 1 }, { t: 'Download', u: 'size', n: 1 }, { t: 'Benches run', u: 'standard set', n: 1 }, 'Action', ''], rows, 'Models: status, size and actions');

      put(main, header('Models', 'What is installed, how much space it uses, and what you can download or remove. Removing moves folders to the Trash; results are kept.'),
        h('div', { class: 'grid2' }, disk, downloads),
        section('All models · ' + ms.length, h('span', { class: 'hint', text: ms.filter(function (m) { return m.installed; }).length + ' installed' }), tbl),
        h('p', { class: 'hint', text: 'Ollama models are managed by Ollama (ollama pull / ollama rm) and are not listed here.' }));
    });
  }

  function screenPhone(main) {
    return api('/api/settings').then(function(d) {
      var body=card([h('h2',{text:'Open on your phone or tablet'}),h('p',{text:'Connect the other device to Tailscale using your account, then scan this code or open the address.'})]);
      if(d.phone) {
        var qr=window.LabQRCode(0,'M'); qr.addData(d.phone); qr.make();
        var canvas=h('canvas',{width:256,height:256,role:'img','aria-label':'QR code for '+d.phone,style:'width:256px;max-width:100%;height:auto;align-self:flex-start;border:1px solid var(--line);'});
        var ctx=canvas.getContext('2d'), size=qr.getModuleCount(), cell=Math.floor(256/(size+8)), edge=Math.floor((256-size*cell)/2);
        ctx.fillStyle='#fff';ctx.fillRect(0,0,256,256);ctx.fillStyle='#000';
        for(var y=0;y<size;y++)for(var x=0;x<size;x++)if(qr.isDark(y,x))ctx.fillRect(edge+x*cell,edge+y*cell,cell,cell);
        put(body,canvas,h('a',{href:d.phone,text:d.phone,style:'overflow-wrap:anywhere;'}),
          h('button',{class:'btn',text:'Copy address',onclick:function(){navigator.clipboard.writeText(d.phone).then(function(){toast('Address copied');}).catch(function(){toast('Select the address above to copy it.',true);});}}),
          h('p',{class:'hint',text:'Private access for your configured Tailscale login. The Mac must be awake. The lab starts automatically after macOS login.'}));
      } else put(body,h('p',{text:'Phone access has not been configured on this Mac.'}),h('pre',{class:'log',text:'.venv/bin/python scripts/lab_app_phone.py enable'}));
      put(main,header('Open on phone','Your private lab address and QR code.'),body);
    });
  }

  function screenSettings(main) {
    return api('/api/settings').then(function (d) {
      put(main, header('Settings and rules', 'Read-only. Paths and rules the app follows.'),
        card([h('dl', { class: 'kv' }, [['Lab repo', d.repo], ['Owner engine', d.engine + ' (never changed by the app)'], ['Models', d.models], ['App state', d.state_dir + ' (queue, jobs, logs; git-ignored)'],
          ['Address', 'http://127.0.0.1:' + d.port + ' (this Mac only)'], ['Quiet threshold', d.quiet_threshold_gb + ' GB free']].map(function (r) { return [h('dt', { text: r[0] }), h('dd', { class: 'mono', text: r[1] })]; }))]),
        section('Keep the app running', null, card([
          h('p', { text: d.service_installed ? 'Installed as a login service: it starts when you log in and restarts if it stops.' : 'Not installed as a service: the app runs only while `make lab-app` runs.' }),
          h('pre', { class: 'log', text: d.service_installed ? 'make lab-app-uninstall   # remove the login service' : 'make lab-app-install     # start at login, restart if it stops\nmake lab-app-uninstall   # remove it again' })])),
        section('Rules', null, card([h('ul', { style: 'margin:0;padding-left:18px' }, d.rules.map(function (r) { return h('li', { text: r }); }))])));
    });
  }

  // ---------- start benches (picker) ----------
  // Canvas: Lab-Bench-Picker.dc.html. The server's /api/bench-catalog is the only list; the page sends ids only.
  // Primary workflow: choose a model + one bench, then launch with one action.
  function resumeButton(j, queuedItems) {
    if (!j.resume) return null;
    var queued=(queuedItems || []).some(function(q){return q.kind===j.kind && (j.kind==='bench' ? q.args.name===j.args.name : q.args.model===j.args.model && q.args.bench===j.args.bench);});
    var button = h('button', {type:'button', class:'btn btn-sm', disabled:queued ? '' : null, text:queued ? 'Resume queued' : 'Resume · '+j.resume.remaining+' remaining',
      'aria-label':'Resume unfinished: '+j.title, onclick:function () {
        button.disabled=true; button.textContent='Queueing…';
        post('/api/job/resume', {id:j.id}).then(function () {
          toast('Resume queued. Saved successful cases will be kept.'); route();
        }).catch(function (e) { button.disabled=false; button.textContent='Resume unfinished'; toast(e.message,true); });
      }});
    return button;
  }

  // ---------- Run benchmarks (home) ----------
  // One workflow: select cells in the Run matrix, then Run. Below it: what runs now, the queue in order, and what just finished.
  var launchChoice = { last: null };
  /* The Run matrix: installed models x benches. Each cell shows its last result or why it cannot run; clicking cells
     selects them (a finished one runs again), and the bar at the bottom queues the selection. */
  var runSel = { ids: {}, style: 'terse', when: 'quiet', pending: false };
  var CELL_WORD = { done: 'run again', never: 'never run', partial: 'resume', failed: 'failed', ready: 'ready' };
  function selectable(c) { return c && (c.state === 'done' || c.state === 'never' || c.state === 'partial' || c.state === 'failed' || c.state === 'ready'); }
  function drawMatrix(box, onQueued) {
    return api('/api/run-matrix').then(function (d) {
      var cols = d.columns.filter(function (c) { return c.group === 'Standard' || d.rows.some(function (r) { return r.cells[c.id + ':' + runSel.style]; }); });
      function cellOf(r, c) { return r.cells[c.group === 'Standard' ? c.id : c.id + ':' + runSel.style]; }
      var all = {};
      d.rows.forEach(function (r) { Object.keys(r.cells).forEach(function (k) { all[r.cells[k].id] = r.cells[k]; }); });
      d.extra.forEach(function (e) { if (e.cell) all[e.id] = e.cell; });
      Object.keys(runSel.ids).forEach(function (id) { if (!selectable(all[id])) delete runSel.ids[id]; });   // queued since, or gone
      function chosen() { return Object.keys(runSel.ids).map(function (id) { return all[id]; }).filter(Boolean); }
      function toggle(ids, on) { ids.forEach(function (id) { if (on) runSel.ids[id] = 1; else delete runSel.ids[id]; }); draw(); }
      function visibleCells(pred) {
        var out = [];
        d.rows.forEach(function (r) { cols.forEach(function (c) { var x = cellOf(r, c); if (selectable(x) && pred(x, r, c)) out.push(x.id); }); });
        return out;
      }

      function cellButton(x) {
        if (!x) return h('td', { class: 'mx-na', 'aria-label': 'not available for this model' }, '—');
        var sel = !!runSel.ids[x.id], can = selectable(x);
        var top = x.state === 'done' ? x.result : x.state === 'queued' ? 'queued #' + x.queue_pos : x.state === 'running' ? 'running'
          : x.state === 'blocked' ? 'can’t run' : x.state === 'partial' ? x.result : CELL_WORD[x.state];
        var sub = x.state === 'done' ? [x.sub, x.date ? x.date.slice(5).replace('-', '/') : null].filter(Boolean).join(' · ')
          : x.state === 'blocked' ? x.why : can ? about(x.est_s) : '';
        var inner = [h('span', { class: 'mx-top num', text: top }), sub ? h('span', { class: 'mx-sub', text: sub }) : null,
          sel ? h('span', { class: 'mx-pick', text: '✓ ' + (x.state === 'done' ? 'run again' : x.state === 'partial' ? 'resume' : 'selected') }) : null];
        return h('td', { class: 'mx-c is-' + x.state + (sel ? ' sel' : '') + (x.lossy ? ' lossy' : '') },
          can ? h('button', { type: 'button', 'aria-pressed': sel ? 'true' : 'false', title: x.title + (x.state === 'done' ? ' · select to run again' : ''),
            onclick: function () { toggle([x.id], !sel); } }, inner) : h('div', { title: x.why || x.title }, inner));
      }
      var table = h('table', { class: 'mx' });
      var bar = h('div', { class: 'run-bar', role: 'region', 'aria-label': 'Selection' });
      var extraBox = h('div', { class: 'stack', style: 'gap:6px' });

      function draw() {
        cols = d.columns.filter(function (c) { return c.group === 'Standard' || d.rows.some(function (r) { return r.cells[c.id + ':' + runSel.style]; }); });
        var std = cols.filter(function (c) { return c.group === 'Standard'; }), q = cols.filter(function (c) { return c.group !== 'Standard'; });
        fill(table,
          h('thead', {},
            h('tr', {}, h('th', { class: 'mx-model', rowspan: '2', scope: 'col', text: 'Model' }),
              h('th', { colspan: String(std.length), scope: 'colgroup', class: 'mx-grp', text: 'Standard benches' }),
              h('th', { colspan: String(q.length), scope: 'colgroup', class: 'mx-grp', text: 'Quality bench · 24 graded prompts · ' + runSel.style + ' answers' })),
            h('tr', {}, cols.map(function (c) {
              var ids = visibleCells(function (x, r, cc) { return cc === c; });
              return h('th', { scope: 'col', class: 'mx-col' }, h('button', { type: 'button', class: 'mx-head', disabled: ids.length ? null : '',
                title: 'Select the whole column', onclick: function () { toggle(ids, !ids.every(function (id) { return runSel.ids[id]; })); } },
                c.title, c.lossy ? h('span', { class: 'mx-lossy', title: 'changes output', text: '≈' }) : null));
            }))),
          h('tbody', {}, d.rows.map(function (r) {
            var cs = cols.map(function (c) { return cellOf(r, c); }), live = cs.filter(Boolean);
            var why = live.length && live.every(function (x) { return x.state === 'blocked' && x.why === live[0].why; }) ? live[0] : null;
            var ids = visibleCells(function (x, rr) { return rr === r; });
            var head = h('th', { scope: 'row', class: 'mx-model' },
              h('button', { type: 'button', class: 'mx-head', disabled: ids.length ? null : '', title: 'Select the whole row',
                onclick: function () { toggle(ids, !ids.every(function (id) { return runSel.ids[id]; })); } },
                h('span', { class: 'mx-name', text: r.title }), h('span', { class: 'mx-sub', text: r.engine + (r.main ? ' · main model' : '') })));
            if (why) return h('tr', {}, head, h('td', { colspan: String(cols.length), class: 'mx-why' }, 'Can’t run yet: ' + why.why + ' ',
              why.needs_model ? h('a', { href: '#install', text: 'Models' }) : null));
            return h('tr', {}, head, cs.map(cellButton));
          })));
        fill(extraBox, ['quiet', 'planned'].map(function (g) {
          var es = d.extra.filter(function (e) { return e.group === g && e.cell; });
          if (!es.length) return null;
          return h('div', { class: 'stack', style: 'gap:4px' },
            h('h3', { class: 'eyebrow', text: g === 'quiet' ? 'Quiet runs on the main model' : 'Planned experiments' }),
            h('div', { class: 'xtra' }, es.map(function (e) {
              var x = e.cell, can = selectable(x), sel = !!runSel.ids[x.id];
              return h('label', { class: 'xtra-i' + (can ? '' : ' off'), title: e.what },
                h('input', { type: 'checkbox', checked: sel ? '' : null, disabled: can ? null : '', onchange: function () { toggle([x.id], !sel); } }),
                h('span', { class: 'stack', style: 'gap:0;min-width:0' }, h('span', { text: e.title }),
                  h('span', { class: 'hint', text: x.state === 'queued' ? 'queued #' + x.queue_pos : x.state === 'running' ? 'running' : x.state === 'blocked' ? x.why : about(x.est_s) })));
            })));
        }));
        drawBar();
      }
      function drawBar() {
        var list = chosen(), total = list.reduce(function (a, x) { return a + (x.est_s || 0); }, 0);
        var again = list.filter(function (x) { return x.state === 'done'; }).length;
        bar.classList.toggle('on', list.length > 0);
        var whenSel = h('select', { class: 'input', 'aria-label': 'When may it start?', onchange: function () { runSel.when = whenSel.value; } },
          h('option', { value: 'quiet', selected: runSel.when === 'quiet' ? '' : null, text: 'Start on a quiet machine (≥ ' + d.quiet_threshold_gb + ' GB free for ' + Math.round(d.quiet_hold_s / 60) + ' min)' }),
          h('option', { value: 'ready', selected: runSel.when === 'ready' ? '' : null, text: 'Start as soon as the GPU is free' }));
        fill(bar, list.length ? [
          h('div', { class: 'stack', style: 'gap:0' }, h('strong', { class: 'num', text: list.length + ' selected · ' + about(total) }),
            h('span', { class: 'hint', text: again ? again + ' already ran and will be measured again; old answers are kept' : 'Runs one at a time, after anything already queued' })),
          h('div', { class: 'row', style: 'gap:8px' }, whenSel,
            h('button', { type: 'button', class: 'btn', text: 'Clear', onclick: function () { runSel.ids = {}; draw(); } }),
            h('button', { type: 'button', class: 'btn btn-primary', disabled: runSel.pending ? '' : null, text: runSel.pending ? 'Queueing…' : 'Run ' + list.length,
              onclick: function () { run(list, total); } }))]
          : h('span', { class: 'hint', text: 'Click cells to select them: never-run, failed or finished (to run again). Click a model or a column title to select its whole row or column.' }));
      }
      function run(list, total) {
        var ask = total > 3600 || list.length > 10 ? confirmDialog({ eyebrow: 'Run', title: 'Queue ' + list.length + ' benches, ' + about(total) + '?',
          sub: runSel.when === 'quiet' ? 'They wait for a quiet machine, then run one at a time.' : 'They start as soon as the GPU is free, one at a time.',
          confirm: 'Queue ' + list.length, rows: list.slice(0, 8).map(function (x) { return [x.state === 'done' ? 'run again' : CELL_WORD[x.state] || x.state, x.title]; })
            .concat(list.length > 8 ? [['…', (list.length - 8) + ' more']] : []) }) : Promise.resolve(true);
        ask.then(function (ok) {
          if (!ok) return;
          runSel.pending = true; drawBar();
          post('/api/queue/add-selection', { ids: list.map(function (x) { return x.id; }), schedule: runSel.when }).then(function (r) {
            runSel.pending = false; runSel.ids = {};
            toast('Queued ' + r.queued.length + ' job' + (r.queued.length === 1 ? '' : 's') + ' (' + about(total) + ').' + (runSel.when === 'quiet' ? ' They start when the machine is quiet.' : ''), false, ['#queue', 'View queue']);
            onQueued(); drawMatrix(box, onQueued);
          }, function (e) { runSel.pending = false; drawBar(); toast(e.message, true); });
        });
      }
      function shortcut(label, pred) {
        return h('button', { type: 'button', class: 'btn btn-sm', text: label, onclick: function () { toggle(visibleCells(pred), true); } });
      }
      var styleSw = h('div', { class: 'seg', role: 'group', 'aria-label': 'Quality answers' }, d.styles.map(function (st) {
        return h('button', { type: 'button', 'aria-pressed': st === runSel.style ? 'true' : 'false', text: st, onclick: function () {
          runSel.style = st; styleSw.querySelectorAll('button').forEach(function (b) { b.setAttribute('aria-pressed', b.textContent === st ? 'true' : 'false'); }); draw(); } });
      }));
      fill(box, h('section', { class: 'card stack', style: 'padding:16px 20px;gap:12px', 'aria-labelledby': 'mx-h' },
        h('div', { class: 'row between', style: 'gap:10px 16px;align-items:flex-end' },
          h('div', { class: 'stack', style: 'gap:2px' }, h('h2', { id: 'mx-h', style: 'font-size:19px;line-height:26px;font-weight:600', text: 'Benches' }),
            h('p', { class: 'hint', text: 'Every installed model and bench, with its last result. Select cells, then Run.' })),
          h('div', { class: 'row', style: 'gap:8px' }, h('span', { class: 'hint', text: 'Quality answers' }), styleSw,
            shortcut('Select never run', function (x) { return x.state === 'never' || x.state === 'partial'; }),
            shortcut('Select failed', function (x) { return x.state === 'failed'; }),
            h('button', { type: 'button', class: 'btn btn-sm', text: 'Clear', onclick: function () { runSel.ids = {}; draw(); } }))),
        h('div', { class: 'mx-wrap' }, table),
        d.not_installed.length ? h('p', { class: 'hint' }, d.not_installed.length + ' models not installed (' + d.not_installed.map(function (m) { return m.title; }).join(', ') + '). ',
          h('a', { href: '#install', text: 'Models' })) : null,
        extraBox, bar));
      draw();
      return d;
    });
  }
  function fill(el) { el.textContent = ''; for (var i = 1; i < arguments.length; i++) put(el, arguments[i]); }

  function screenDashboard(main) {
    var requestedHash = location.hash;
    return Promise.all([api('/api/now'), api('/api/queue')]).then(function (res) {
      if (location.hash !== requestedHash) return;
      var current = res[0], queue = res[1];

      function gpuJob() { return current.jobs.filter(function (j) { return j.gpu; })[0]; }

      // -- live column
      var live = h('div', { class: 'live-row', id: 'live-jobs' });
      var tiles = h('div', { class: 'tiles', 'aria-label': 'Summary' });
      function drawTiles() {
        tiles.textContent = '';
        var j = gpuJob(), m = current.machine, p = j && j.progress;
        put(tiles,
          h('div', { class: 'tile' }, h('span', { class: 'eyebrow', text: 'Running now' }),
            h('span', { class: 'big', text: j ? jobParts(j.title).what || j.title : 'Nothing' }),
            h('span', { class: 'hint', text: j ? (p && p.total ? pct(p.done, p.total) + '% · ' : '') + (p && p.eta_s ? 'done ~' + at(p.eta_s) : 'running ' + dur(j.elapsed_s)) : 'GPU free' })),
          h('div', { class: 'tile' }, h('span', { class: 'eyebrow', text: 'Queue' }),
            h('span', { class: 'big num', text: queue.items.length + ' waiting' }),
            h('span', { class: 'hint', text: queue.paused ? 'Paused — nothing starts' : queue.timeline && queue.timeline.total_s != null && queue.items.length ? 'All done ~' + at(queue.timeline.total_s) : 'Runs one at a time' })),
          h('div', { class: 'tile' }, h('span', { class: 'eyebrow', text: 'Machine' }),
            h('span', { class: 'big', text: m.quiet ? 'Quiet' : 'Busy' }),
            h('span', { class: 'hint num', text: f2(m.free_gb, 1) + ' GB RAM free · quiet needs ≥ ' + m.quiet_threshold_gb + ' GB' })));
      }
      function runningCard() {
        var j = gpuJob();
        if (!j) return h('section', { class: 'card live-card', 'aria-labelledby': 'run-h' },
          h('div', { class: 'card-head' }, h('h2', { id: 'run-h', text: 'Running now' }), chip('st-done', 'GPU free')),
          h('p', { class: 'muted', text: queue.items.length ? (queue.paused ? 'The queue is paused, so nothing starts.' : 'The next job starts on its own when its start condition is met.') : 'Nothing is running. Select benches in the grid above and Run.' }));
        var p = j.progress || {}, parts = jobParts(j.title), bench = p.name;
        return h('section', { class: 'card live-card', 'aria-labelledby': 'run-h' },
          h('div', { class: 'card-head' }, h('h2', { id: 'run-h', text: 'Running now' }), j.foreign ? chip('st-blocked', 'Not started by the lab') : chip('st-running', 'Running')),
          h('div', { class: 'stack', style: 'gap:2px' }, h('span', { class: 'job-title', text: j.kind === 'Quality bench' && bench ? 'Quality bench “' + bench + '”' : (parts.what || j.title) }),
            h('span', { class: 'hint', text: j.detail || '' })),
          p.total ? h('div', { class: 'stack', style: 'gap:6px' }, meter(p.done, p.total, 'Benchmark progress'),
            h('div', { class: 'progress-line num' }, h('span', { text: f2(p.done, p.unit ? 1 : 0) + ' of ' + p.total + (p.unit ? ' ' + p.unit : ' answers') + ' · ' + pct(p.done, p.total) + '%' }),
              h('span', { text: p.eta_s ? '~' + dur(p.eta_s) + ' left · done ~' + at(p.eta_s) : 'finishing' }))) : null,
          p.current ? h('p', { class: 'current-case' }, h('span', { class: 'hint', text: 'Now answering ' }), p.current.replace(/__/g, ' · ').replace(/\b(d030t12|d040t12|d030|d050)\b/g, function (c) { return CFG[c]; }),
            p.per_answer_s ? h('span', { class: 'hint', text: ' · ' + p.per_answer_s + ' s per answer' }) : null) : null,
          h('dl', { class: 'kv' }, h('dt', { text: 'Process' }), h('dd', { class: 'num', text: 'PID ' + j.pid + (j.engine_pid ? ' · engine PID ' + j.engine_pid : '') + ' · running ' + dur(j.elapsed_s) })),
          h('div', { class: 'row' },
            bench ? h('a', { class: 'btn btn-sm', href: '#bench/' + encodeURIComponent(bench), text: 'Answers so far' }) : null,
            p.items ? h('details', { class: 'x', style: 'flex-basis:100%' }, h('summary', { text: 'Every case in this bench' }), benchStrip(p)) : null,
            j.stoppable ? h('button', { type: 'button', class: 'btn btn-danger btn-sm', text: 'Stop…', 'aria-label': 'Stop PID ' + j.pid, onclick: function () { stopJob(j); } })
              : h('p', { class: 'hint', text: 'Not started by the lab (e.g. your own Colibri session): the app never stops it.' })));
      }
      function queueCard() {
        var items = queue.items, show = items.slice(0, 6);
        var mine = (launchChoice.last && launchChoice.last.qids) || [];
        return h('section', { class: 'card live-card', 'aria-labelledby': 'q-h' },
          h('div', { class: 'card-head' }, h('h2', { id: 'q-h' }, 'Up next ', h('span', { class: 'count', text: String(items.length) })),
            items.length ? h('button', { type: 'button', class: 'btn btn-sm', text: queue.paused ? 'Resume queue' : 'Pause queue',
              onclick: function () { post('/api/queue/pause', { paused: !queue.paused }).then(refreshLive).catch(function (e) { toast(e.message, true); }); } }) : null),
          queue.paused ? h('div', { class: 'notice notice-warn', role: 'status' }, chip('st-paused', 'Paused'), h('span', { text: 'Nothing queued starts until you resume.' })) : null,
          items.length ? h('ol', { class: 'up-next' }, show.map(function (q, n) {
            var parts = jobParts(q.title), cond = q.only_when_quiet ? chip('st-blocked', 'Waits for quiet') : null;
            return h('li', { class: n === 0 ? 'next' : null, 'aria-current': mine.indexOf(q.qid) >= 0 ? 'true' : null },
              h('span', { class: 'pos', 'aria-label': 'Position ' + (n + 1), text: String(n + 1) }),
              h('div', { style: 'min-width:0' }, h('div', { class: 'job-title' }, parts.what, parts.model ? h('span', { class: 'muted', style: 'font-weight:400', text: ' · ' + parts.model }) : null),
                h('div', { class: 'job-meta' }, parts.detail ? h('span', { text: parts.detail }) : null, cond,
                  h('span', { class: 'num', text: '~' + dur(q.est_s) + (q.starts_in_s != null && !queue.paused ? ' · starts ~' + at(q.starts_in_s) : '') }),
                  mine.indexOf(q.qid) >= 0 ? h('span', { class: 'badge', text: 'just added' }) : null)),
              h('button', { type: 'button', class: 'icon-btn', 'aria-label': 'Remove ' + q.title + ' from the queue', title: 'Remove from queue',
                onclick: function () { removeQueued(q); } }, svgIcon('M6 6l12 12M18 6L6 18', 14)));
          })) : h('p', { class: 'muted', text: 'Nothing waiting. Queued benchmarks appear here in the order they will run.' }),
          items.length > show.length ? h('a', { href: '#queue', text: 'All ' + items.length + ' queued jobs, reorder and logs' }) : h('a', { href: '#queue', text: 'Reorder and view logs' }));
      }
      function removeQueued(q) {
        confirmDialog({ eyebrow: 'Queue', title: 'Remove from the queue?', confirm: 'Remove', danger: true,
          rows: [['Job', q.title], ['Estimated time', '~' + dur(q.est_s)]], note: 'Nothing is deleted: saved answers stay, and you can queue it again later.' })
          .then(function (ok) { if (ok) post('/api/queue/remove', { qid: q.qid }).then(function () { toast('Removed from the queue: ' + q.title); return refreshLive(); }).catch(function (e) { toast(e.message, true); }); });
      }
      function finishedSection() {
        var hist = (queue.jobs || []).filter(function (j) { return j.status !== 'running'; }).slice(0, 6);
        var outcome = function (j) {
          if (j.status === 'failed') return chip('st-failed', 'Failed' + (j.exit != null ? ' · exit ' + j.exit : ''));
          if (j.status === 'finished') return chip('st-waiting', 'Ended · no exit code');
          return chip('st-done', 'Done');
        };
        return section('Recently finished', h('a', { href: '#results', text: 'Measured results' }),
          hist.length ? table(['Job', 'Model', 'Started', 'Outcome', ''], hist.map(function (j) {
            var parts = jobParts(j.title);
            return h('tr', {}, td(h('div', { class: 'stack', style: 'gap:0' }, h('strong', { text: parts.what || j.title }), parts.detail ? h('span', { class: 'hint', text: parts.detail }) : null)),
              td(parts.model || '—'), td(h('span', { class: 'num', style: 'white-space:nowrap', text: j.started })), td(outcome(j)),
              td(h('div',{class:'row'},resumeButton(j,queue.items),j.kind === 'bench' && j.args && j.args.name ? h('a', { href: '#bench/' + encodeURIComponent(j.args.name), text: 'Answers' }) : h('a', { href: '#queue', text: 'Log' }))));
          }), 'Recently finished jobs') : empty('Finished benchmarks appear here.'));
      }
      function renderLive() {
        setGpu(current); drawTiles();
        live.textContent = '';
        put(live, runningCard(), queueCard());
        fin.replaceWith(fin = finishedSection());
      }
      var refreshing = false;
      function refreshLive() {
        if (refreshing) return Promise.resolve(); refreshing = true;
        return Promise.all([api('/api/now'), api('/api/queue')]).then(function (r) {
          current = r[0]; queue = r[1]; renderLive();
          var key = queue.items.length + '|' + ((gpuJob() || {}).pid || '');
          if (key !== lastQueue) { lastQueue = key; drawMatrix(matrix, refreshLive); }   // a job started or ended: cells changed
        })
          .catch(function (e) { toast('Live status could not update: ' + e.message, true); }).finally(function () { refreshing = false; });
      }

      var fin = h('div');
      var matrix = h('div', { id: 'run-matrix' });
      put(main, header('Run benchmarks', 'Pick what to measure in the grid, then Run. Jobs run one at a time, in order.'),
        tiles, matrix, live, fin);
      var lastQueue = queue.items.length + '|' + ((gpuJob() || {}).pid || '');
      drawMatrix(matrix, refreshLive);
      renderLive();
      timer = setInterval(function () { if (main.isConnected && !document.querySelector('.scrim') && !document.querySelector('#live-jobs details[open]')) refreshLive(); }, 5000);
    });
  }


  // ---------- router ----------
  var ROUTES = { dashboard: screenDashboard, results: screenResults, models: screenModels, install: screenModels, benches: function (m) { return screenResults(m, 'coverage'); },
                 phone: screenPhone, now: screenNow, queue: screenQueue, settings: screenSettings, runs: screenRuns, experiments: screenExperiments,
                 leaderboard: screenLeaderboard, research: screenResearch, start: screenDashboard };
  var NAV_OF = { bench: 'results', benches: 'results', install: 'models', start: 'dashboard' };
  function route() {
    clearInterval(timer);
    var hash = (location.hash || '#dashboard').slice(1), parts = hash.split('/'), name = parts[0];
    var fn = name === 'bench' ? function (m) { return screenBench(m, parts.slice(1).join('/')); }
      : name === 'results' ? function (m) { return screenResults(m, parts[1]); } : ROUTES[name] || screenDashboard;
    renderNav(NAV_OF[name] || (ROUTES[name] ? name : 'dashboard'));
    var title = { dashboard: 'Run benchmarks', results: 'Results', bench: 'Answers', models: 'Models', install: 'Models', phone: 'Open on phone' }[name] ||
      (ADVANCED.filter(function (s) { return s[0] === name; })[0] || [0, 'Run benchmarks'])[1];
    document.title = title + ' · GLM lab';
    function load(keepScroll, focus) {
      var y = window.scrollY, fresh = h('main', { id: 'main', tabindex: '-1' });
      return fn(fresh).then(function () {
        if ((location.hash || '#dashboard').slice(1) !== hash) return;
        fresh.setAttribute('data-ready', ''); fresh.setAttribute('data-route', hash); route.fails = 0;
        var cur = document.getElementById('main'); cur.replaceWith(fresh);
        if (keepScroll) window.scrollTo(0, y);
        else if (focus) { window.scrollTo(0, 0); fresh.focus({ preventScroll: true }); }
      }).catch(function (e) {
        if ((location.hash || '#dashboard').slice(1) !== hash) return;
        /* keep trying while this error is on screen: 3 s, 6 s, 12 s, then every 30 s; a successful load ends it */
        var wait = Math.min(30000, 3000 * Math.pow(2, route.fails || 0)); route.fails = (route.fails || 0) + 1;
        var cur = document.getElementById('main'); cur.textContent = ''; cur.setAttribute('data-ready', ''); cur.setAttribute('data-route', hash);
        put(cur, errorBox(e, function () { clearTimeout(route.retryTimer); route(); }, wait));
        clearTimeout(route.retryTimer);
        route.retryTimer = setTimeout(function () { if ((location.hash || '#dashboard').slice(1) === hash && document.querySelector('#main .err')) route(); }, wait);
      });
    }
    load(false, route.started);
    route.started = true;
    if (fn === screenNow || fn === screenQueue) timer = setInterval(function () { if (!document.querySelector('.scrim') && !document.querySelector('details.x[open]') && !(document.activeElement && /INPUT|SELECT/.test(document.activeElement.tagName))) load(true); }, fn === screenNow ? 5000 : 10000);
    if (fn !== screenNow && fn !== screenDashboard) api('/api/now').then(setGpu).catch(function () {});
  }
  window.addEventListener('hashchange', route);
  /* after sleep, a closed Dock app or a lost connection: refresh when the app is in front again */
  function wake() { if (document.visibilityState === 'visible' && document.querySelector('#main .err')) { clearTimeout(route.retryTimer); route(); } }
  document.addEventListener('visibilitychange', wake);
  window.addEventListener('pageshow', function (e) { if (e.persisted) wake(); });
  window.addEventListener('online', wake);
  route();
})();
