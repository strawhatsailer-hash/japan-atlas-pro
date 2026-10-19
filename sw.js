const CACHE_NAME = 'japan-atlas-shell-v35-recovery';
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
    // Always prefer the newest HTML; fall back to the last cached shell if offline.
    event.respondWith(
      fetch(req).then(res => {
        if (res && res.ok) {
          const copy = res.clone();
          event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.put('./index.html', copy)));
        }
        return res;
      }).catch(() => caches.match('./index.html').then(cached => cached || Response.error()))
    );
    return;
  }

  // Cache-first for static same-origin assets; fetch on misses and cache successful responses.
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
