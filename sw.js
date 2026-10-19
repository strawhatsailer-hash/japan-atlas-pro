// Recovery release: retire the service worker completely to isolate blank-screen navigation.
// The app is a static HTML planner and must remain usable without a fetch-intercepting worker.
self.addEventListener('install', event => {
  event.waitUntil(self.skipWaiting());
});
self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    try {
      const keys = await caches.keys();
      await Promise.all(keys.filter(key => key.startsWith('japan-atlas-shell-')).map(key => caches.delete(key)));
    } catch (_) {}
    try { await self.registration.unregister(); } catch (_) {}
    // Intentionally do not claim clients: subsequent navigations should go directly to GitHub Pages.
  })());
});
// No fetch handler: all page and asset requests go directly to the network.
