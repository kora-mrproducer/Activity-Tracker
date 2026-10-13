// Cache only bundled assets. Live pages and CSRF tokens always come from the server.
const CACHE_NAME = 'activity-tracker-assets-v1.1';
const ASSETS = ['/static/css/tailwind-built.css', '/static/js/common.js', '/static/js/dashboard.js', '/static/icon-192.png', '/static/icon-512.png'];
self.addEventListener('install', event => {
    event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', event => {
    event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key.startsWith('activity-tracker-') && key !== CACHE_NAME).map(key => caches.delete(key)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', event => {
    const url = new URL(event.request.url);
    if (event.request.method !== 'GET' || url.origin !== self.location.origin || !url.pathname.startsWith('/static/')) return;
    event.respondWith(caches.match(event.request).then(cached => cached || fetch(event.request)));
});
