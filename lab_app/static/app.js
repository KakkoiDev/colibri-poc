/* GLM lab control app, v1 (read-only). Screens follow the designer's canvas
   (project/Lab-*.dc.html). All data comes from lab_app/server.py's /api/*.
   Text from the lab (answers, logs, titles) is always inserted as text, never HTML. */
(function () {
  'use strict';

  var GH = 'https://github.com/KakkoiDev/colibri-poc/blob/main/';
  var ICON = {
    now: 'M3 12h4l3-8 4 16 3-8h4', models: 'M21 8l-9-5-9 5 9 5 9-5zM3 8v8l9 5 9-5V8M12 13v8',
    leaderboard: 'M4 20V10M10 20V4M16 20v-7M2 20h20', experiments: 'M9 3h6M10 3v6L4 19a1 1 0 0 0 1 1.5h14A1 1 0 0 0 20 19l-6-10V3',
    benches: 'M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z', runs: 'M4 17l6-5-6-5M12 19h8',
    research: 'M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14zM21 21l-5-5',
    queue: 'M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01', install: 'M12 3v12M7 10l5 5 5-5M4 21h16',
    settings: 'M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12M14 4v4M8 10v4M16 16v4'
  };
  var SCREENS = [['now', 'Now'], ['queue', 'Queue'], ['models', 'Models'], ['leaderboard', 'Leaderboard'], ['experiments', 'Experiments'],
                 ['benches', 'Benches'], ['install', 'Install'], ['runs', 'Runs'], ['research', 'Research'], ['settings', 'Settings']];
  var CFG = { exact: 'exact', d030: 'skip 0.3', d050: 'skip 0.5', d030t12: 'skip 0.3 · 12 thr', d040t12: 'skip 0.4 · 12 thr' };
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
  function svgIcon(d) {
    var ns = 'http://www.w3.org/2000/svg', s = document.createElementNS(ns, 'svg'), p = document.createElementNS(ns, 'path');
    s.setAttribute('width', '18'); s.setAttribute('height', '18'); s.setAttribute('viewBox', '0 0 24 24'); s.setAttribute('aria-hidden', 'true');
    p.setAttribute('d', d); s.appendChild(p); return s;
  }
  var f2 = function (v, d) { return v == null || isNaN(v) ? '—' : Number(v).toFixed(d == null ? 2 : d); };
  var pct = function (a, b) { return b ? Math.round(a / b * 100) : 0; };
  function dur(s) {
    if (s == null) return '—';
    var hh = Math.floor(s / 3600), mm = Math.floor(s % 3600 / 60);
    return hh ? hh + ' h ' + mm + ' m' : mm ? mm + ' m' : Math.round(s) + ' s';
  }
  function chip(cls, word) { return h('span', { class: 'chip ' + cls, text: word }); }
  function verdict(v) {
    var m = { 'improves': ['v-improves', '▲ improves'], 'no clear change': ['v-same', '= no clear change'], 'worse': ['v-worse', '▼ worse'],
              'failed': ['v-failed', '✗ failed'] }[v] || ['v-pending', v];
    return h('span', { class: 'verdict ' + m[0], text: m[1] });
  }
  function lossyTag() { return h('span', { class: 'tag tag-lossy', text: 'changes output' }); }
  function exactTag() { return h('span', { class: 'tag tag-exact', text: 'exact' }); }
  function ghLink(path, label) { return h('a', { href: GH + path, target: '_blank', rel: 'noopener', text: label || path }); }
  function api(path) {
    return fetch(path, { cache: 'no-store' }).then(function (r) {
      return r.json().then(function (j) { if (!r.ok) throw new Error(j.error || r.status); return j; });
    });
  }
  function post(path, body) {
    return fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Lab-Action': '1' }, body: JSON.stringify(body || {}) })
      .then(function (r) { return r.json().then(function (j) { if (!r.ok) throw new Error(j.error || r.status); return j; }); });
  }
  function toast(msg, bad) {
    var t = h('div', { role: 'status', class: bad ? 'err' : 'banner', style: 'position:fixed;right:16px;bottom:16px;max-width:420px;z-index:20;background:var(--surface)', text: msg });
    document.body.appendChild(t); setTimeout(function () { t.remove(); }, 6000);
  }
  // Confirmation dialog: names exactly what will happen. Resolves true on confirm.
  function confirmDialog(o) {
    return new Promise(function (resolve) {
      var prev = document.activeElement;
      var scrim = h('div', { class: 'scrim', style: 'position:fixed' });
      function close(v) { scrim.remove(); document.removeEventListener('keydown', esc); if (prev) prev.focus(); resolve(v); }
      function esc(e) { if (e.key === 'Escape') close(false); }
      var ok = h('button', { type: 'button', class: 'btn ' + (o.danger ? 'btn-danger-solid' : 'btn-primary'), onclick: function () { close(true); }, text: o.confirm });
      var dlg = h('div', { class: 'dialog', role: 'dialog', 'aria-modal': 'true', 'aria-labelledby': 'dlg-t' },
        h('div', { class: 'dialog-head' }, o.eyebrow ? h('span', { class: 'eyebrow', text: o.eyebrow }) : null, h('h2', { id: 'dlg-t', style: 'font-size:18px;line-height:24px', text: o.title }),
          o.sub ? h('p', { class: 'muted', style: 'font-size:13px', text: o.sub }) : null),
        h('div', { class: 'dialog-body' }, h('dl', { class: 'kv' }, (o.rows || []).map(function (r) { return [h('dt', { text: r[0] }), h('dd', { class: r[2] ? 'mono' : null, style: 'overflow-wrap:anywhere', text: r[1] })]; })),
          o.note ? h('div', { class: o.warn ? 'err' : 'well', style: 'padding:10px 12px;font-size:13px', text: o.note }) : null),
        h('div', { class: 'dialog-foot' }, h('button', { type: 'button', class: 'btn', onclick: function () { close(false); }, text: 'Cancel' }), ok));
      scrim.addEventListener('click', function (e) { if (e.target === scrim) close(false); });
      scrim.appendChild(dlg); document.body.appendChild(scrim); document.addEventListener('keydown', esc); ok.focus();
    });
  }
  function stopJob(j) {
    return confirmDialog({ eyebrow: 'Confirmation · stop', title: 'Stop PID ' + j.pid + '?', danger: true, confirm: 'Stop PID ' + j.pid,
      sub: 'Only this job and the processes it started are stopped. Nothing else is touched.',
      rows: [['Job', j.kind + ' · ' + j.title], ['Process', j.command, true], ['Running for', dur(j.elapsed_s)],
             ['Holds', j.holds_lock ? '.bench.lock' : 'no lock'], ['Engine child', j.engine_pid ? 'PID ' + j.engine_pid : 'none']],
      note: j.kind === 'Quality bench' ? 'Finished answers stay saved; re-queue the same bench to resume where it stopped.' :
            j.kind === 'Download' ? 'The download is resumable: start it again from Install to continue.' : 'The current run is lost; finished results stay saved.' })
      .then(function (ok) {
        if (!ok) return;
        return post('/api/stop', { pid: j.pid }).then(function (r) { toast('Stopped PID ' + r.stopped.join(', ')); route(); }, function (e) { toast(e.message, true); });
      });
  }
  function runOrQueue(kind, args, label, queueOnly) {
    return post(queueOnly ? '/api/queue/add' : '/api/run', { kind: kind, args: args }).then(function (r) {
      toast(r.started ? 'Started: ' + r.started.title + ' (PID ' + r.started.pid + ')' : (r.note ? r.note + ': ' : 'Queued: ') + (r.queued ? r.queued.title : label));
      route();
    }, function (e) { toast(e.message, true); });
  }
  function table(headers, rows) {
    var t = h('table', { class: 't' });
    t.appendChild(h('thead', {}, h('tr', {}, headers.map(function (x) {
      var n = typeof x === 'object'; return h('th', { class: n && x.n ? 'n' : null, scope: 'col', text: n ? x.t : x });
    }))));
    var tb = h('tbody'); rows.forEach(function (r) { tb.appendChild(r); }); t.appendChild(tb);
    return h('div', { class: 'card scroll' }, t);
  }
  function td(content, cls) { return h('td', { class: cls || null }, content); }
  function header(title, sub, extra) {
    return h('header', { class: 'head' }, h('div', { class: 'stack', style: 'gap:2px' }, h('h1', { text: title }), sub ? h('p', { class: 'muted', style: 'font-size:13px', text: sub }) : null), extra || null);
  }
  function section(title, right, body) {
    return h('section', { class: 'stack' }, h('div', { class: 'sec-title' }, h('h2', { text: title }), right || null), body);
  }
  function card(children, pad) { return h('div', { class: 'card', style: 'padding:' + (pad || '16px 18px') + ';display:flex;flex-direction:column;gap:10px' }, children); }
  function meter(done, total) {
    return h('div', { class: 'meter', role: 'progressbar', 'aria-valuemin': 0, 'aria-valuemax': total, 'aria-valuenow': done },
      h('span', { style: 'width:' + Math.min(100, pct(done, total)) + '%' }));
  }
  function errorBox(e) { return h('div', { class: 'err', role: 'alert', text: 'Could not load data: ' + (e.message || e) + '. Is lab_app/server.py running?' }); }

  // ---------- nav / theme ----------
  function renderNav(active) {
    var nav = document.getElementById('nav'); nav.textContent = '';
    SCREENS.forEach(function (s) {
      nav.appendChild(h('a', { href: '#' + s[0], 'aria-current': s[0] === active ? 'page' : null }, svgIcon(ICON[s[0]]), h('span', { text: s[1] })));
    });
  }
  function setGpu(now) {
    var c = document.getElementById('gpu-chip'), d = document.getElementById('gpu-detail');
    var gpu = (now.jobs || []).filter(function (j) { return j.gpu; });
    if (gpu.length) {
      c.className = 'chip st-running'; c.textContent = 'GPU busy';
      d.textContent = gpu[0].title + ' · PID ' + gpu[0].pid;
    } else { c.className = 'chip st-done'; c.textContent = 'GPU free'; d.textContent = (now.jobs || []).length ? now.jobs.length + ' other job(s)' : 'nothing running'; }
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

  // ---------- screens ----------
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

  function at(s) { var d = new Date(Date.now() + s * 1000); return ('0' + d.getHours()).slice(-2) + ':' + ('0' + d.getMinutes()).slice(-2); }
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
    return card([h('div', { class: 'row between' }, h('h2', { class: 'eyebrow', text: 'Up next · timeline' }), h('a', { href: '#queue', text: 'Queue · ' + tl.queue.length + ' waiting' + (tl.paused ? ' · paused' : '') })),
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

  function covCell(c) {
    var map = { done: ['st-done', 'Done'], running: ['st-running', 'Running'], missing: ['st-missing', 'Missing'], failed: ['st-failed', 'Failed'], queued: ['st-queued', 'Queued'] }[c.status];
    return h('div', { class: 'cov' + (c.status === 'missing' ? ' missing' : '') }, h('span', { class: 'chip ' + map[0], style: 'align-self:flex-start', text: map[1] }), h('span', { class: 'hint num', text: c.detail || '' }));
  }

  function screenBenches(main) {
    return api('/api/benches').then(function (d) {
      var suite = d.suite.benches;
      var cov = table([{ t: 'Model' }].concat(suite.map(function (b) { return { t: b.name }; })), d.models.map(function (m) {
        var quietMissing = m.owner_model && (m.coverage.quiet.status === 'missing' || m.coverage.ram.status === 'missing');
        return h('tr', {}, td(h('div', { class: 'stack', style: 'gap:2px' }, h('strong', { text: m.name }),
          h('span', { class: 'hint', text: m.installed ? 'installed · ' + m.covered + ' of ' + suite.length + ' benches' : (m.download ? 'downloading ' + pct(m.download.done, m.download.total) + '%' : 'not installed') }),
          quietMissing ? h('button', { type: 'button', class: 'btn btn-sm', style: 'align-self:flex-start', text: 'Queue quiet run + RAM sweep',
            onclick: function () { post('/api/queue/add', { kind: 'quiet', args: { flags: ['ram-sweep', 'skip-original'] }, only_when_quiet: true }).then(function () { toast('Queued: quiet run (starts when ≥ 20 GB free)'); route(); }, function (e) { toast(e.message, true); }); } }) : null,
          !m.installed && !m.download ? h('a', { class: 'btn btn-sm', style: 'align-self:flex-start', href: '#install', text: 'Install first' }) : null)),
          suite.map(function (b) { return td(covCell(m.coverage[b.id])); }));
      }));
      var suiteTbl = table(['Bench', 'What it measures', 'Duration (int4, busy)', 'Runs with'], suite.map(function (b) {
        return h('tr', {}, td(h('strong', { text: b.name })), td(b.what), td(b.duration, 'n'), td(h('span', { class: 'mono', text: b.runs_with })));
      }));
      var results = d.results.map(function (r) {
        var rows = r.summary.map(function (s) {
          var lossy = s.config !== 'exact';
          return h('tr', { class: lossy ? 'lossy' : null }, td(s.style), td(h('span', { class: 'row' }, CFG[s.config] || s.config, lossy ? lossyTag() : exactTag())),
            td(s.correct + '/' + s.graded, 'n'), td(s.same_as_exact + '/' + s.ok, 'n'), td(f2(s.answer_s, 1), 'n'), td(f2(s.prefill_s, 1), 'n'),
            td(f2(s.output_tokens, 1), 'n'), td(f2(s.decode_tok_s), 'n'));
        });
        return section('Bench ' + r.name + ' · ' + r.answers + ' answers', h('div', { class: 'row' },
          r.review ? ghLink(r.review, 'Manual review') : null, h('a', { href: '#bench/' + r.name, text: 'All answers' })),
          h('div', { class: 'stack' },
            table(['Style', 'Config', { t: 'Correct (auto)', n: 1 }, { t: 'Same text as exact', n: 1 }, { t: 'Mean answer s', n: 1 }, { t: 'Prompt read s', n: 1 }, { t: 'Output tokens', n: 1 }, { t: 'Decode tok/s', n: 1 }], rows),
            h('p', { class: 'hint', text: 'Automatic grades: facts/logic by expected answer, maths by final number, code by running tests; normal answers capped at 128 tokens, so long answers can be under-counted. Single runs.' }),
            r.notes.length ? h('p', { class: 'hint', text: 'Notes in the results folder: ' + r.notes.join(', ') + ' (e.g. downloads that ran during the bench).' }) : null));
      });
      put(main, header('Benches', 'The standard suite every model gets, so models are comparable. Suite ' + d.suite.version + '.'),
        section('Coverage · models × benches', h('div', { class: 'row' }, chip('st-done', 'Done'), chip('st-running', 'Running'), chip('st-missing', 'Missing')), cov),
        section('Standard suite ' + d.suite.version, null, suiteTbl), results);
    });
  }

  function screenBench(main, name) {
    return api('/api/bench?name=' + encodeURIComponent(name)).then(function (d) {
      var state = { style: 'all', config: 'all', correct: 'all' };
      var list = h('div', { class: 'stack' });
      function opt(sel, vals) { vals.forEach(function (v) { sel.appendChild(h('option', { value: v, text: v === 'all' ? 'all' : (CFG[v] || v) })); }); return sel; }
      var uniq = function (k) { return ['all'].concat(d.answers.map(function (a) { return a[k]; }).filter(function (v, i, x) { return x.indexOf(v) === i; })); };
      function draw() {
        list.textContent = '';
        var rows = d.answers.filter(function (a) {
          return (state.style === 'all' || a.style === state.style) && (state.config === 'all' || a.config === state.config) &&
            (state.correct === 'all' || String(a.correct) === state.correct);
        });
        list.appendChild(h('p', { class: 'hint', text: rows.length + ' answers' }));
        list.appendChild(table(['Prompt', 'Style', 'Config', 'Grade', { t: 'Answer s', n: 1 }, { t: 'Tokens', n: 1 }, 'Answer'], rows.map(function (a) {
          var lossy = a.config !== 'exact';
          var det = h('details', { class: 'x' }, h('summary', { text: 'Show' }), h('p', { class: 'hint', text: a.prompt || '' }), h('pre', { class: 'ans', text: a.text || '(no answer: run failed or was refused)' }));
          return h('tr', { class: lossy ? 'lossy' : null }, td(h('span', { class: 'mono', text: a.id })), td(a.style), td(CFG[a.config] || a.config),
            td(a.correct === true ? h('span', { class: 'verdict v-improves', text: '✓ correct' }) : a.correct === false ? h('span', { class: 'verdict v-worse', text: '✗ incorrect (auto)' }) : h('span', { class: 'verdict v-pending', text: 'not graded' })),
            td(f2(a.answer_s, 1), 'n'), td(a.output_tokens == null ? '—' : a.output_tokens, 'n'), td(det));
        })));
      }
      var filters = h('div', { class: 'filters', role: 'toolbar', 'aria-label': 'Filters' },
        h('label', { class: 'hint' }, 'Style ', opt(h('select', { class: 'input', onchange: function (e) { state.style = e.target.value; draw(); } }), uniq('style'))),
        h('label', { class: 'hint' }, 'Config ', opt(h('select', { class: 'input', onchange: function (e) { state.config = e.target.value; draw(); } }), uniq('config'))),
        h('label', { class: 'hint' }, 'Grade ', opt(h('select', { class: 'input', onchange: function (e) { state.correct = e.target.value; draw(); } }), ['all', 'true', 'false'])));
      put(main, header('Bench ' + name + ' · answers', 'Every answer with its automatic grade. A manual review may correct grader errors.', h('a', { class: 'btn', href: '#benches', text: '← Benches' })), filters, list);
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

  function screenExperiments(main) {
    return api('/api/experiments').then(function (d) {
      var groups = {
        Planned: function (e) { return e.verdict === 'not run' && e.plan; },
        Done: function (e) { return e.metrics && e.metrics.measured; },
        'Ideas not run': function (e) { return (e.verdict === 'not run' && !e.plan) || e.verdict === 'in progress'; },
        All: function () { return true; }
      };
      var tab = 'Done', body = h('div', { class: 'stack' }), tabs = h('div', { class: 'tabs', role: 'tablist' });
      function draw() {
        tabs.textContent = ''; body.textContent = '';
        Object.keys(groups).forEach(function (g) {
          var n = d.entries.filter(groups[g]).length;
          tabs.appendChild(h('button', { class: 'tab', role: 'tab', 'aria-selected': g === tab ? 'true' : 'false', onclick: function () { tab = g; draw(); } }, g, h('span', { class: 'count', text: n })));
        });
        var rows = d.entries.filter(groups[tab]);
        body.appendChild(table(['Experiment', 'Category', 'Verdict', { t: 'tok/s (ref → new)', n: 1 }, { t: 'Change', n: 1 }, 'Output', 'Details'], rows.map(function (e) {
          var m = e.metrics || {};
          var tags = h('div', { class: 'row' }, e.lossy ? lossyTag() : null, e.everyday ? h('span', { class: 'tag tag-usable', text: 'everyday · by owner' }) : e.usable ? h('span', { class: 'tag tag-usable', text: 'usable · by owner' }) : null);
          var det = h('details', { class: 'x' }, h('summary', { text: 'Why and result' }),
            h('dl', { class: 'kv', style: 'font-size:13px' }, [['Change', e.change], ['Why', e.hypothesis], ['Result', e.conclusion || (e.effects || []).join('; ')], ['Tradeoffs', e.tradeoffs], ['Reference', e.ref], ['Runs', (e.runs || []).join(', ')]]
              .filter(function (x) { return x[1]; }).map(function (x) { return [h('dt', { text: x[0] }), h('dd', { text: x[1] })]; })),
            (e.sources || []).map(function (s) { return h('p', { class: 'hint' }, h('a', { href: s, target: '_blank', rel: 'noopener', text: s })); }));
          var acts = (e.verdict === 'not run' && e.plan) ? h('div', { class: 'row' },
            h('button', { type: 'button', class: 'btn btn-sm', onclick: function () { runOrQueue('planned', { id: e.id }, e.title, false); }, text: 'Run now' }),
            h('button', { type: 'button', class: 'btn btn-sm', onclick: function () { runOrQueue('planned', { id: e.id }, e.title, true); }, text: 'Queue' })) : null;
          return h('tr', { class: e.lossy ? 'lossy' : null }, td(h('div', { class: 'stack', style: 'gap:2px;min-width:220px' }, h('strong', { text: e.title }), h('span', { class: 'hint mono', text: e.id }), tags, acts)),
            td(e.category), td(verdict(e.verdict)), td(m.measured ? f2(m.ref_tok_s) + ' → ' + f2(m.tok_s) : '—', 'n'),
            td(m.speed_change_pct == null ? '—' : (m.speed_change_pct > 0 ? '+' : '') + Math.round(m.speed_change_pct) + '%', 'n'), td(m.measured ? m.output : '—'), td(det, 'wrap'));
        })));
      }
      put(main, header('Experiments', 'The experiment registry (experiments/glm-experiments.json). Verdicts are computed from published runs; changes under ~10% are noise.'), tabs, body);
      draw();
    });
  }

  function screenModels(main) {
    return api('/api/models').then(function (d) {
      var n = d.suite.benches.length;
      var cards = d.models.map(function (m) {
        var st = m.installed ? chip('st-done', 'Installed') : m.download ? chip('st-running', 'Downloading ' + pct(m.download.done, m.download.total) + '%') : chip('st-missing', 'Not installed');
        var b = m.best || {};
        return card([
          h('div', { class: 'row between' }, h('strong', { text: m.name }), st),
          h('span', { class: 'hint', text: [m.family, m.params, m.format, m.size_gb + ' GB', m.mtp ? 'MTP head' : null].filter(Boolean).join(' · ') }),
          h('span', { class: 'hint', text: 'Engine: ' + m.engine }),
          m.download ? h('div', { class: 'stack', style: 'gap:4px' }, meter(m.download.done, m.download.total), h('span', { class: 'hint num', text: f2(m.download.done, 1) + ' of ' + m.download.total + ' GB' })) : null,
          h('div', { class: 'kv2', style: 'border-top:1px solid var(--line);padding-top:8px' },
            [['best exact', b.best_exact, false], ['everyday', b.everyday, true], ['best usable lossy', b.best_usable_lossy, true]].map(function (x) {
              return h('div', {}, h('span', { class: 'tag ' + (x[2] ? 'tag-lossy' : 'tag-exact'), text: x[0] }), h('div', { class: x[1] ? 'num' : 'muted', style: 'font-size:' + (x[1] ? '18px' : '13px') + ';margin-top:4px', text: x[1] ? f2(x[1].tok_s) + ' tok/s' : 'not run' }));
            })),
          m.aa ? h('span', { class: 'hint', text: 'Published Artificial Analysis Intelligence Index: ' + m.aa.score + ' (' + m.aa.model + ', full model as served by its makers; reported, not measured here)' }) : null,
          h('span', { class: 'hint', text: 'Bench coverage: ' + m.covered + ' of ' + n + (m.bench_names.length ? ' · quality bench ' + m.bench_names.join(', ') : ' · quality: not benched') }),
          !m.installed ? h('dl', { class: 'kv', style: 'font-size:13px' }, [['Source', m.source], ['Download', m.download_gb ? '~' + m.download_gb + ' GB' : null], ['Prepare with', m.prep], ['Unlocks', (m.unlocks || []).join(', ')]]
            .filter(function (x) { return x[1]; }).map(function (x) { return [h('dt', { text: x[0] }), h('dd', { class: x[0] === 'Prepare with' ? 'mono' : null, text: x[1] })]; })) : null,
          m.owner_model ? h('span', { class: 'hint', text: "The owner's model folder: never modified by the lab." }) : null
        ]);
      });
      put(main, header('Models', 'Every model the lab can run, installed or not (models/catalog.json). Downloads need your OK; run the prep command in a terminal.'),
        h('div', { class: 'grid3' }, cards));
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
          td(j.started), td(chip(cls, j.status + (j.exit != null && j.status !== 'done' ? ' (' + j.exit + ')' : ''))), td(det, 'wrap'));
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

  function screenInstall(main) {
    return Promise.all([api('/api/models'), api('/api/now'), api('/api/storage')]).then(function (res) {
      var ms = res[0].models, now = res[1], store = res[2], free = now.machine.disk_free_gb;
      function remove(m) {
        confirmDialog({ eyebrow: 'Confirmation · remove', title: 'Move ' + m.name + ' to the Trash?', danger: true, confirm: 'Move ' + f2(m.gb, 1) + ' GB to the Trash',
          sub: 'Its folders move to the macOS Trash. Nothing is deleted: you can restore them until you empty the Trash, which frees the space.',
          rows: m.folders.map(function (f) { return ['Folder', f.path + ' · ' + f2(f.gb, 1) + ' GB', true]; }).concat([['Results and logs', 'kept (they are in the lab repo, not here)']]),
          note: 'Experiments that need this model become blocked until it is installed again.' })
          .then(function (ok) {
            if (ok) post('/api/remove', { model: m.id }).then(function (r) { toast('Moved to the Trash: ' + r.moved.map(function (x) { return x.src; }).join(', ')); route(); }, function (e) { toast(e.message, true); });
          });
      }
      var storeRows = store.models.map(function (m) {
        var state = m.owner_model ? h('span', { class: 'hint', text: 'your model · never removed by the app' })
          : m.in_use ? h('span', { class: 'hint', text: 'in use (downloading or running): stop it first' })
          : m.removable ? h('button', { type: 'button', class: 'btn btn-sm btn-danger', onclick: function () { remove(m); }, text: 'Remove…' }) : h('span', { class: 'hint', text: '—' });
        return h('tr', {}, td(h('div', { class: 'stack', style: 'gap:2px' }, h('strong', { text: m.name }),
          m.folders.map(function (f) { return h('span', { class: 'hint mono', text: f.path + ' · ' + f2(f.gb, 1) + ' GB' + (f.in_use ? ' · in use' : '') }); }))),
          td(chip(m.installed ? 'st-done' : 'st-running', m.installed ? 'Installed' : 'Partial / downloading')), td(f2(m.gb, 1) + ' GB', 'n'), td(state));
      });
      var downloaded = section('Downloaded models · ' + store.models.length, h('span', { class: 'hint', text: 'Sizes are measured on disk now' }), h('div', { class: 'stack' },
        table(['Model and folders', 'Status', { t: 'On disk', n: 1 }, 'Remove'], storeRows),
        store.other.length ? h('p', { class: 'hint', text: 'Other folders in ~/colibri-models, not in the lab catalog (not managed here): ' + store.other.map(function (o) { return o.path + ' (' + f2(o.gb, 1) + ' GB)'; }).join(', ') + '.' }) : null));
      setGpu(now);
      var dlRunning = now.jobs.filter(function (j) { return j.kind === 'Download'; });
      var gpuBusy = now.jobs.some(function (j) { return j.gpu; });
      function download(m) {
        var after = free - (m.download_gb || 0);
        confirmDialog({ eyebrow: 'Confirmation · download', title: m.name, confirm: 'Download ~' + m.download_gb + ' GB',
          rows: [['Source', m.source, true], ['Download size', '~' + m.download_gb + ' GB'], ['Kept on disk', '~' + m.size_gb + ' GB'],
                 ['Free disk after', '~' + after + ' GB'], ['Saved to', '~/' + (m.download_path || m.path), true], ['Runs', m.prep, true], ['Unlocks', (m.unlocks || []).join(', ')]],
          warn: after < 30 || gpuBusy,
          note: after < 30 ? 'This would leave less than 30 GB free.' : gpuBusy ? 'A GPU job is running: the download will skew its timings (quality results are unaffected).' : 'Resumable: if it stops, start it again here.' })
          .then(function (ok) { if (ok) post('/api/download', { model: m.id }).then(function (r) { toast('Started: ' + r.started.title + ' (PID ' + r.started.pid + ')'); route(); }, function (e) { toast(e.message, true); }); });
      }
      var rows = ms.map(function (m) {
        var st = m.installed ? chip('st-done', 'Installed') : m.download ? chip('st-running', pct(m.download.done, m.download.total) + '% downloaded') : chip('st-missing', 'Not installed');
        var act = m.installed ? h('span', { class: 'hint', text: m.owner_model ? 'your model (never changed)' : 'ready' })
          : !m.prep ? h('span', { class: 'hint', text: 'no prep step' })
          : dlRunning.length ? h('span', { class: 'hint', text: 'wait for the running download' })
          : h('button', { type: 'button', class: 'btn btn-primary btn-sm', onclick: function () { download(m); }, text: (m.download ? 'Resume download (~' : 'Download (~') + m.download_gb + ' GB)…' });
        return h('tr', {}, td(h('div', { class: 'stack', style: 'gap:2px' }, h('strong', { text: m.name }), h('span', { class: 'hint', text: m.format }))), td(st),
          td(m.download_gb ? '~' + m.download_gb + ' GB' : '—', 'n'), td(m.size_gb + ' GB', 'n'), td((m.unlocks || []).join(', ') || '—', 'wrap'), td(act));
      });
      var sel = ms.filter(function (m) { return !m.installed && m.download_gb; }).reduce(function (a, m) { return a + m.download_gb - (m.download ? m.download.done : 0); }, 0);
      put(main, header('Install', 'Models and engines the lab can add. Every download needs a confirmation showing source, size and disk left.'),
        card([h('div', { class: 'row between' }, h('span', { class: 'num' }, h('strong', { text: free + ' GB' }), ' free · ', h('strong', { text: Math.round(free - sel) + ' GB' }), ' if every remaining download finished'), h('span', { class: 'hint', text: 'Warn below 30 GB' })),
          h('div', { class: 'bar', style: 'height:14px', 'aria-hidden': 'true' }, h('span', { style: 'width:' + Math.max(0, 100 - pct(free, 2000)) + '%;background:var(--fg-2)' }), h('span', { class: 'hatch', style: 'width:' + pct(sel, 2000) + '%' })),
          dlRunning.length ? h('p', { class: 'hint', text: 'Downloading now: ' + dlRunning.map(function (j) { return j.title + ' (PID ' + j.pid + ')'; }).join(', ') + '. Stop it from Now.' }) : null]),
        downloaded,
        section('Catalog · available to install', null, table(['Model', 'Status', { t: 'Download', n: 1 }, { t: 'Kept', n: 1 }, 'Unlocks', 'Action'], rows)));
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

  // ---------- router ----------
  var ROUTES = { now: screenNow, queue: screenQueue, install: screenInstall, settings: screenSettings, benches: screenBenches, runs: screenRuns,
                 experiments: screenExperiments, models: screenModels, leaderboard: screenLeaderboard, research: screenResearch };
  function route() {
    clearInterval(timer);
    var hash = (location.hash || '#now').slice(1), parts = hash.split('/'), name = parts[0];
    var main = document.getElementById('main');
    var fn = name === 'bench' ? function (m) { return screenBench(m, parts[1]); } : ROUTES[name] || screenNow;
    renderNav(name === 'bench' ? 'benches' : (ROUTES[name] ? name : 'now'));
    function load(keepScroll) {
      var y = window.scrollY, fresh = h('main', { id: 'main', tabindex: '-1' });
      return fn(fresh).then(function () {
        var cur = document.getElementById('main'); cur.replaceWith(fresh);
        if (keepScroll) window.scrollTo(0, y);
      }).catch(function (e) { main.textContent = ''; put(main, errorBox(e)); });
    }
    load(false);
    if (fn === screenNow || fn === screenQueue) timer = setInterval(function () { if (!document.querySelector('.scrim') && !document.querySelector('details.x[open]') && !(document.activeElement && /INPUT|SELECT/.test(document.activeElement.tagName))) load(true); }, fn === screenNow ? 5000 : 10000);
    else api('/api/now').then(setGpu).catch(function () {});
  }
  window.addEventListener('hashchange', route);
  route();
})();
