const CACHE = 'worship-v11';

// Only precache CSS (rarely changes); HTML and JS use network-first
const PRECACHE = [
  '/css/style.css',
  '/manifest.json',
  '/manifest-leader.json',
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(PRECACHE)));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
      .then(() => self.clients.matchAll({ type: 'window', includeUncontrolled: true }))
      .then(clients => {
        // Force all open pages to reload so they get fresh HTML/JS from network
        clients.forEach(client => {
          client.navigate(client.url).catch(() => {});
        });
      })
  );
});

self.addEventListener('fetch', e => {
  const { request } = e;
  const url = new URL(request.url);

  // API: always network, never cache
  if (url.pathname.startsWith('/api/')) {
    e.respondWith(
      fetch(request).catch(() =>
        new Response(JSON.stringify([]), { headers: { 'Content-Type': 'application/json' } })
      )
    );
    return;
  }

  // HTML pages and JS files: network-first (always get latest; cache only as offline fallback)
  if (request.destination === 'document' || url.pathname.endsWith('.js')) {
    e.respondWith(
      fetch(request)
        .then(res => {
          const clone = res.clone();
          caches.open(CACHE).then(c => c.put(request, clone));
          return res;
        })
        .catch(() => caches.match(request))
    );
    return;
  }

  // CSS / images / other static assets: cache-first
  e.respondWith(
    caches.match(request).then(cached =>
      cached ||
      fetch(request).then(res => {
        const clone = res.clone();
        caches.open(CACHE).then(c => c.put(request, clone));
        return res;
      })
    )
  );
});
