const CACHE_NAME = 'japan-atlas-shell-v36-nav-timeout';
const APP_SHELL = ['./','./index.html','./manifest.webmanifest','./icon.svg','./published-itinerary.json','./assets/css/atlas-premium.css','./assets/css/atlas-studio.css?v=5','./assets/js/atlas-motion.js'];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys
        .filter(key => key.startsWith('japan-atlas-shell-') && key !== CACHE_NAME)
        .map(key => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  const isNavigation = req.mode === 'navigate' || url.pathname.endsWith('/index.html') || url.pathname.endsWith('/');
  if (isNavigation) {
    // Never let a slow/stalled network request leave the browser on a blank navigation.
    event.respondWith((async () => {
      const cached = await caches.match('./index.html');
      const network = fetch(req).then(async res => {
        if (res && res.ok) {
          const copy = res.clone();
          await caches.open(CACHE_NAME).then(cache => cache.put('./index.html', copy));
        }
        return res;
      });
      let timeout;
      const deadline = new Promise(resolve => { timeout = setTimeout(() => resolve(null), 2500); });
      const result = await Promise.race([network, deadline]).catch(() => null);
      clearTimeout(timeout);
      if (result && result.ok) return result;
      if (cached) return cached;
      try {
        const late = await network;
        if (late && late.ok) return late;
      } catch (_) {}
      return new Response('<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1"><title>Japan Atlas</title><main style="font:16px system-ui;padding:24px;color:#18343b"><h1>Japan Atlas</h1><p>The planner could not connect just now. Check your connection and reload.</p><button onclick="location.reload()">Reload planner</button></main>', {headers:{'Content-Type':'text/html; charset=utf-8'}});
    })());
    return;
  }

  event.respondWith(
    caches.match(req).then(cached => {
      if (cached) return cached;
      return fetch(req).then(res => {
        if (res && res.ok) {
          const copy = res.clone();
          event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.put(req, copy)));
        }
        return res;
      }).catch(() => caches.match('./index.html').then(cached => cached || Response.error()));
    })
  );
});
