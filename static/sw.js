// Service Worker for Activity Tracker PWA
// Provides offline caching and install-to-homescreen functionality

const CACHE_NAME = 'activity-tracker-v1.0.0';
const RUNTIME_CACHE = 'activity-tracker-runtime-v1';

// Assets to cache immediately on install
const PRECACHE_ASSETS = [
  '/',
  '/static/css/tailwind-built.css',
  '/static/fontawesome/css/all.min.css',
  '/static/fonts/outfit-local.css',
  '/static/fonts/outfit-400.ttf',
  '/static/fonts/outfit-500.ttf',
  '/static/fonts/outfit-600.ttf',
  '/static/fonts/outfit-700.ttf',
  '/static/js/common.js',
  '/static/js/dashboard.js',
  '/static/js/chart.min.js',
  '/static/icon-192.png',
  '/static/icon-512.png',
  '/static/manifest.json'
];

// Install event: cache core assets
self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[SW] Precaching static assets');
        return cache.addAll(PRECACHE_ASSETS);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event: clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating service worker...');
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((name) => name !== CACHE_NAME && name !== RUNTIME_CACHE)
            .map((name) => {
              console.log('[SW] Deleting old cache:', name);
              return caches.delete(name);
            })
        );
      })
      .then(() => self.clients.claim())
  );
});

// Fetch event: network-first for API/data, cache-first for assets
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Skip chrome-extension and other non-http(s) requests
  if (!url.protocol.startsWith('http')) {
    return;
  }

  // Strategy: Cache-first for static assets
  if (
    url.pathname.startsWith('/static/') ||
    url.pathname === '/favicon.ico' ||
    url.pathname.endsWith('.png') ||
    url.pathname.endsWith('.jpg') ||
    url.pathname.endsWith('.css') ||
    url.pathname.endsWith('.js') ||
    url.pathname.endsWith('.woff2') ||
    url.pathname.endsWith('.ttf')
  ) {
    event.respondWith(
      caches.match(request)
        .then((cachedResponse) => {
          if (cachedResponse) {
            return cachedResponse;
          }
          return fetch(request).then((networkResponse) => {
            // Cache successful responses
            if (networkResponse && networkResponse.status === 200) {
              const responseClone = networkResponse.clone();
              caches.open(CACHE_NAME).then((cache) => {
                cache.put(request, responseClone);
              });
            }
            return networkResponse;
          });
        })
    );
    return;
  }

  // Strategy: Network-first for HTML pages and API routes (with cache fallback)
  event.respondWith(
    fetch(request)
      .then((networkResponse) => {
        // Cache successful HTML responses for offline fallback
        if (networkResponse && networkResponse.status === 200 && 
            request.headers.get('accept')?.includes('text/html')) {
          const responseClone = networkResponse.clone();
          caches.open(RUNTIME_CACHE).then((cache) => {
            cache.put(request, responseClone);
          });
        }
        return networkResponse;
      })
      .catch(() => {
        // Offline: try cache
        return caches.match(request).then((cachedResponse) => {
          if (cachedResponse) {
            return cachedResponse;
          }
          // Offline fallback for HTML pages
          if (request.headers.get('accept')?.includes('text/html')) {
            return caches.match('/');
          }
          // No cache available
          return new Response('Offline - content not cached', {
            status: 503,
            statusText: 'Service Unavailable',
            headers: new Headers({
              'Content-Type': 'text/plain'
            })
          });
        });
      })
  );
});

// Background sync for future enhancement (optional)
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync triggered:', event.tag);
  // Could be used for syncing offline updates when connection restored
});

// Push notifications support (optional for future)
self.addEventListener('push', (event) => {
  console.log('[SW] Push notification received');
  const options = {
    body: event.data ? event.data.text() : 'New activity update',
    icon: '/static/icon-192.png',
    badge: '/static/icon-192.png',
    vibrate: [200, 100, 200]
  };
  event.waitUntil(
    self.registration.showNotification('Activity Tracker', options)
  );
});
