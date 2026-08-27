const CACHE = 'antonio-junior-hub-mobile-v5-photo-v4';
const SHELL = ['./', './index.html', './manifest.webmanifest', './antonio-junior-photo-banner-v3.webp', './antonio-junior-photo-icon-64-v4.png', './antonio-junior-photo-icon-180-v4.png', './antonio-junior-photo-icon-192-v4.png', './antonio-junior-photo-icon-512-v4.png', './antonio-junior.webp'];
self.addEventListener('install', event => { event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(SHELL)).then(() => self.skipWaiting())); });
self.addEventListener('activate', event => { event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key !== CACHE).map(key => caches.delete(key)))).then(() => self.clients.claim())); });
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  event.respondWith(fetch(event.request).then(response => {
    if (response.ok && new URL(event.request.url).origin === self.location.origin) {
      const copy = response.clone();
      caches.open(CACHE).then(cache => cache.put(event.request, copy));
    }
    return response;
  }).catch(() => caches.match(event.request).then(cached => cached || caches.match('./index.html'))));
});
