const CACHE_NAME = 'japan-atlas-shell-v34-fast-cache';
const APP_SHELL = ['./','./index.html','./manifest.webmanifest','./icon.svg','./published-itinerary.json','./assets/css/atlas-premium.css','./assets/css/atlas-studio.css','./assets/js/atlas-motion.js'];

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
    // Return the last complete planner immediately while checking for a newer copy.
    const update = fetch(req).then(res => {
      if (res && res.ok) {
        const copy = res.clone();
        caches.open(CACHE_NAME).then(cache => cache.put('./index.html', copy));
      }
      return res;
    });
    event.waitUntil(update.catch(() => {}));
    event.respondWith(
      caches.match('./index.html').then(cached => cached || update)
        .catch(() => update)
    );
    return;
  }

  // Cache-first for same-origin assets and data; update cached copies in the background.
  event.respondWith(
    caches.match(req).then(cached => {
      const update = fetch(req).then(res => {
        if (res && res.ok) {
          const copy = res.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(req, copy));
        }
        return res;
      });
      if (cached) {
        event.waitUntil(update.catch(() => {}));
        return cached;
      }
      return update.catch(() => caches.match('./index.html'));
    })
  );
});
