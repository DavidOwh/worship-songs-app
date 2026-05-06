const CACHE = 'worship-v3';
const ASSETS = [
  '/',
  '/leader',
  '/admin',
  '/css/style.css',
  '/js/app.js',
  '/js/leader.js',
  '/js/admin.js',
  '/manifest.json'
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  const { request } = e;
  // Always fetch API calls fresh; cache everything else
  if (request.url.includes('/api/')) {
    e.respondWith(
      fetch(request).catch(() => new Response(JSON.stringify([]), { headers: { 'Content-Type': 'application/json' } }))
    );
    return;
  }
  e.respondWith(
    caches.match(request).then(cached => cached || fetch(request).then(res => {
      const clone = res.clone();
      caches.open(CACHE).then(c => c.put(request, clone));
      return res;
    }))
  );
});
