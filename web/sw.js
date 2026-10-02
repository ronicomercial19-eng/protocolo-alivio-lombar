const CACHE_NAME = 'alivio-lombar-v1';
const ASSETS = [
  '/',
  '/index.html',
  '/style.css',
  '/brand.css',
  '/app.js',
  '/auth.js',
  '/protocol.js',
  '/care.js',
  '/staff.js',
  '/manifest.json'
];

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS)));
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => response || fetch(event.request))
  );
});
