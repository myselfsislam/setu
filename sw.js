/* Setu service worker: works offline, keeps the app fast. Bump VERSION on every release. */
const VERSION = 'setu-v35-2026-10-01-inacct';
const SHELL = ['./', './index.html', './manifest.webmanifest', './fonts/figtree.woff2', './fonts/bricolage.woff2', './icons/setu-192.png', './icons/setu-512.png', './icons/apple-touch-icon.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(VERSION).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== VERSION).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const req = e.request, url = new URL(req.url);
  if (req.method !== 'GET') return;
  // Live data (exchange rates, fund prices): always from the network, never cached here.
  if (/frankfurter|mfapi|gdeltproject|gov\.uk/.test(url.hostname)) return;
  // Headlines file: network first, cached copy when offline.
  if (url.pathname.endsWith('/news.json')) {
    e.respondWith(fetch(req, { cache: 'no-store' }).then(r => { if (r.ok) { const copy = r.clone(); caches.open(VERSION).then(c => c.put(url.pathname, copy)); } return r; }).catch(() => caches.match(url.pathname)));
    return;
  }
  // The app page: network first so updates arrive, cached copy when offline.
  if (req.mode === 'navigate') {
    // Each page is cached under its own address (app and guides), so the app is never replaced by a guide.
    const isApp = /\/(index\.html)?$/.test(url.pathname);
    const key = isApp ? './index.html' : url.pathname;
    e.respondWith(fetch(req).then(r => { if (r.ok) { const copy = r.clone(); caches.open(VERSION).then(c => c.put(key, copy)); } return r; })
      .catch(() => caches.match(key).then(hit => hit || caches.match('./index.html'))));
    return;
  }
  // Fonts, icons and other files: cached copy first, refreshed in the background.
  e.respondWith(caches.match(req).then(hit => {
    const net = fetch(req).then(r => { if (r && (r.ok || r.type === 'opaque')) { const copy = r.clone(); caches.open(VERSION).then(c => c.put(req, copy)); } return r; }).catch(() => hit);
    return hit || net;
  }));
});
