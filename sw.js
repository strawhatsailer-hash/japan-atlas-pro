// Previous shell cache retired by this release: japan-atlas-shell-v18-release2-dashboard-branding
// Previous shell cache retired by this release: japan-atlas-shell-v19-cohesive-redesign
const CACHE_NAME = 'japan-atlas-shell-v19-cohesive-redesign';
const APP_SHELL = ['./', './index.html', './manifest.webmanifest', './icon.svg', './places.json'];
self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(APP_SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key.startsWith('japan-atlas-shell-') && key !== CACHE_NAME).map(key => caches.delete(key)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return; // External maps and navigation remain online-only.
  const isPhotoAsset = url.pathname.includes('/assets/photos/');
  const isShell = ['index.html','manifest.webmanifest','icon.svg','places.json'].some(x => url.pathname.endsWith('/'+x)) || url.pathname.endsWith('/');
  if (!isPhotoAsset && !isShell) return;
  event.respondWith(caches.match(request).then(cached => {
    if (cached) {
      // Serve cached shell/photo immediately, and refresh successful network responses in the background.
      if (isShell || isPhotoAsset) fetch(request).then(response => {
        if (response && response.ok) caches.open(CACHE_NAME).then(cache => cache.put(request, response.clone()));
      }).catch(() => {});
      return cached;
    }
    return fetch(request).then(response => {
      if (response && response.ok) caches.open(CACHE_NAME).then(cache => cache.put(request, response.clone()));
      return response;
    }).catch(() => isShell ? caches.match('./index.html') : Response.error());
  }));
});
