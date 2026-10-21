/* GLM lab service worker: makes the app installable and opens its shell even when the
   local server is down (the page then says so). Data (/api/*) is never cached: the lab
   is live state, so a stale answer would be worse than none. */
var SHELL = 'glm-lab-shell-v5';
var FILES = ['/', '/app.js', '/qrcode.js', '/lab.css', '/manifest.webmanifest', '/icon-192.png', '/icon-512.png'];

self.addEventListener('install', function (e) {
  e.waitUntil(caches.open(SHELL).then(function (c) { return c.addAll(FILES); }).then(function () { return self.skipWaiting(); }));
});
self.addEventListener('activate', function (e) {
  e.waitUntil(caches.keys().then(function (keys) {
    return Promise.all(keys.filter(function (k) { return k !== SHELL; }).map(function (k) { return caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }));
});
self.addEventListener('fetch', function (e) {
  var url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.origin !== location.origin || url.pathname.indexOf('/api/') === 0) return;
  // network first, so the app always runs the latest code; the cached copy only when the server is down
  e.respondWith(fetch(e.request).then(function (r) {
    if (r.ok) { var copy = r.clone(); caches.open(SHELL).then(function (c) { c.put(e.request, copy); }); }
    return r;
  }).catch(function () {
    return caches.match(e.request, { ignoreSearch: true }).then(function (m) { return m || caches.match('/'); });
  }));
});
