const CACHE = 'antonio-junior-hub-mobile-v5-photo-v5'
const APP_SHELL = ['./', './index.html', './manifest.webmanifest', './antonio-junior-photo-icon-512-v5.png', './antonio-junior-photo-icon-64-v5.png', './antonio-junior-photo-icon-180-v5.png', './antonio-junior-photo-icon-192-v5.png', './antonio-junior-photo-icon-512-v5.png', './antonio-junior.webp']
self.addEventListener('install', event => {
  self.skipWaiting()
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(APP_SHELL).catch(() => undefined)))
})
self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key !== CACHE).map(key => caches.delete(key)))).then(() => self.clients.claim()))
})
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return
  const url = new URL(event.request.url)
  if (url.origin !== self.location.origin) return
  event.respondWith(fetch(event.request).then(response => {
    const copy = response.clone()
    caches.open(CACHE).then(cache => cache.put(event.request, copy)).catch(() => undefined)
    return response
  }).catch(() => caches.match(event.request).then(cached => cached || caches.match('./index.html'))))
})
