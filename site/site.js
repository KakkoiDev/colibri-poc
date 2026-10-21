/* Colibri lab public site: shared behaviour for every page.
   Theme switch (Auto / Light / Dark, remembered per browser), copy-link buttons and a tiny DOM helper.
   Each page applies the saved theme before first paint with an inline script right after <body>. */
(function () {
  'use strict';
  var KEY = 'theme';

  function h(tag, attrs) {
    var e = document.createElement(tag);
    for (var k in attrs || {}) {
      var v = attrs[k];
      if (v == null || v === false) continue;
      if (k === 'text') e.textContent = v;
      else if (k === 'style' && typeof v === 'object') Object.assign(e.style, v);
      else if (k.slice(0, 2) === 'on') e.addEventListener(k.slice(2).toLowerCase(), v);
      else e.setAttribute(k, v === true ? '' : v);
    }
    for (var i = 2; i < arguments.length; i++) add(e, arguments[i]);
    return e;
  }
  function add(e, c) {
    if (c == null || c === false) return;
    if (Array.isArray(c)) { c.forEach(function (x) { add(e, x); }); return; }
    e.appendChild(typeof c === 'string' || typeof c === 'number' ? document.createTextNode(String(c)) : c);
  }

  function theme() { try { var t = localStorage.getItem(KEY); return t === 'light' || t === 'dark' ? t : 'auto'; } catch (e) { return 'auto'; } }
  function setTheme(t) {
    document.body.setAttribute('data-theme', t);
    if (t === 'auto') document.documentElement.removeAttribute('data-theme'); else document.documentElement.setAttribute('data-theme', t);   /* the Report's own colours key on <html> */
    try { t === 'auto' ? localStorage.removeItem(KEY) : localStorage.setItem(KEY, t); } catch (e) { /* private mode: not remembered */ }
    document.querySelectorAll('.theme button').forEach(function (b) { b.setAttribute('aria-pressed', String(b.dataset.t === t)); });
  }

  var LINK = 'M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1';
  function linkIcon() {
    var ns = 'http://www.w3.org/2000/svg', s = document.createElementNS(ns, 'svg'), p = document.createElementNS(ns, 'path');
    s.setAttribute('viewBox', '0 0 24 24'); s.setAttribute('aria-hidden', 'true'); p.setAttribute('d', LINK); s.appendChild(p);
    return s;
  }
  var live;
  function announce(msg) {
    if (!live) { live = h('p', { class: 'sr', 'aria-live': 'polite' }); document.body.appendChild(live); }
    live.textContent = msg;
  }
  /* A "Copy link" button. `url` is a string or a function returning one (relative to this page). */
  function copyButton(aria, url) {
    var label = h('span', { text: 'Copy link' });
    var b = h('button', { type: 'button', class: 'copy', 'aria-label': aria }, linkIcon(), label);
    b.addEventListener('click', function () {
      var href = new URL(typeof url === 'function' ? url() : url, location.href).href;
      var done = function () { label.textContent = 'Link copied'; b.classList.add('done'); announce('Link copied: ' + href);
        setTimeout(function () { label.textContent = 'Copy link'; b.classList.remove('done'); }, 2500); };
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(href).then(done, function () { announce(href); });
      else announce(href);
    });
    return b;
  }

  function getJSON(path) {
    return fetch(path, { cache: 'no-cache' }).then(function (r) { if (!r.ok) throw new Error(path + ': ' + r.status); return r.json(); });
  }

  document.addEventListener('DOMContentLoaded', function () {
    var t = theme();
    document.querySelectorAll('.theme button').forEach(function (b) {
      b.setAttribute('aria-pressed', String(b.dataset.t === t));
      b.addEventListener('click', function () { setTheme(b.dataset.t); });
    });
    document.querySelectorAll('[data-copy]').forEach(function (el) {
      el.replaceWith(copyButton(el.getAttribute('aria-label') || 'Copy link', el.getAttribute('data-copy')));
    });
  });

  /* Replace an element's children with any mix of nodes, strings, arrays and nulls (nulls are skipped). */
  function fill(e) { e.textContent = ''; for (var i = 1; i < arguments.length; i++) add(e, arguments[i]); return e; }
  function put(e) { for (var i = 1; i < arguments.length; i++) add(e, arguments[i]); return e; }

  window.Site = { h: h, fill: fill, put: put, copyButton: copyButton, getJSON: getJSON, announce: announce };
})();
