const CACHE_NAME = 'japan-atlas-shell-v30-cinematic-home';
const APP_SHELL = ['./','./index.html','./manifest.webmanifest','./icon.svg','./published-itinerary.json','./assets/css/atlas-premium.css'];
self.addEventListener('install',event=>{event.waitUntil(caches.open(CACHE_NAME).then(cache=>cache.addAll(APP_SHELL)).then(()=>self.skipWaiting()))});
self.addEventListener('activate',event=>{event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(key=>key.startsWith('japan-atlas-shell-')&&key!==CACHE_NAME).map(key=>caches.delete(key)))).then(()=>self.clients.claim()))});
self.addEventListener('fetch',event=>{const req=event.request;if(req.method!=='GET'||new URL(req.url).origin!==self.location.origin)return;event.respondWith(fetch(req).then(res=>{if(res&&res.ok){const copy=res.clone();caches.open(CACHE_NAME).then(cache=>cache.put(req,copy))}return res}).catch(()=>caches.match(req).then(cached=>cached||caches.match('./index.html'))))});
