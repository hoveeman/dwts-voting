/**
 * DWTS Season 35 Ballroom Companion - Service Worker
 * Strategy:
 *  - Network-first for dynamic live show data (HTML, JSON manifests)
 *  - Cache-first for heavy static assets (photos, icons, fonts)
 *  - Offline fallback when network is unavailable
 */

const CACHE_VERSION = 'dwts-s35-v1.0.1';
const STATIC_CACHE = `dwts-static-${CACHE_VERSION}`;
const IMAGE_CACHE = `dwts-images-${CACHE_VERSION}`;

// Pre-cached App Shell resources
const PRECACHE_ASSETS = [
  '/',
  '/index.html',
  '/manifest.webmanifest',
  '/version.json',
  '/dancers.json',
  '/spotify_tracks.json',
  '/spotify_playlists.json',
  '/assets/favicon.svg',
  '/assets/icon-192.png',
  '/assets/icon-512.png',
  '/assets/icon-maskable-192.png',
  '/assets/icon-maskable-512.png',
  '/assets/apple-touch-icon.png',
  '/assets/dwts-hosts.jpg'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => {
      return cache.addAll(PRECACHE_ASSETS).catch((err) => {
        console.warn('[SW] Pre-cache partial warning:', err);
      });
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== STATIC_CACHE && key !== IMAGE_CACHE) {
            console.log('[SW] Purging outdated cache:', key);
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  const url = new URL(req.url);

  // Only handle GET requests
  if (req.method !== 'GET') return;

  // External APIs (e.g. Kalshi prediction market, Spotify API) -> Network with graceful fallback
  if (url.origin !== self.location.origin) {
    if (url.hostname.includes('fonts.googleapis.com') || url.hostname.includes('fonts.gstatic.com')) {
      // Cache Google Fonts
      event.respondWith(
        caches.match(req).then((cached) => {
          if (cached) return cached;
          return fetch(req).then((res) => {
            const clone = res.clone();
            caches.open(STATIC_CACHE).then((cache) => cache.put(req, clone));
            return res;
          });
        })
      );
    }
    return;
  }

  // Heavy static images in /assets/ -> Cache-First
  if (url.pathname.startsWith('/assets/')) {
    event.respondWith(
      caches.open(IMAGE_CACHE).then(async (cache) => {
        const cached = await cache.match(req);
        if (cached) return cached;

        try {
          const networkRes = await fetch(req);
          if (networkRes.status === 200) {
            cache.put(req, networkRes.clone());
          }
          return networkRes;
        } catch (err) {
          // If offline and image missing, fallback gracefully
          return cached || Response.error();
        }
      })
    );
    return;
  }

  // HTML documents & JSON manifests (index.html, version.json, dancers.json)
  // Network-First: Always try to get real-time show updates, fallback to cache if offline
  event.respondWith(
    fetch(req)
      .then((networkRes) => {
        if (networkRes.status === 200) {
          const clone = networkRes.clone();
          caches.open(STATIC_CACHE).then((cache) => cache.put(req, clone));
        }
        return networkRes;
      })
      .catch(async () => {
        const cached = await caches.match(req);
        if (cached) return cached;

        // Fallback for navigation requests to root
        if (req.mode === 'navigate') {
          return caches.match('/');
        }
        return Response.error();
      })
  );
});

// Support manual skipWaiting from client update toast
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
