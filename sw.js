// Service worker : l'application s'ouvre même sans réseau (les données, elles, viennent de la base).
const VERSION = "conserva-v1";
const SHELL = ["./", "index.html", "config.js", "manifest.webmanifest", "assets/tabler.min.css", "assets/app.css",
  "assets/tabler.min.js", "assets/supabase.min.js", "assets/app.js", "icons/icon-192.png", "icons/icon-512.png"];
self.addEventListener("install", e => { e.waitUntil(caches.open(VERSION).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())); });
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== VERSION).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const u = new URL(e.request.url);
  if (e.request.method !== "GET" || u.origin !== location.origin) return; // Supabase et polices : jamais mis en cache ici
  // Réseau d'abord (pour recevoir les mises à jour), cache en secours hors ligne.
  e.respondWith(fetch(e.request).then(r => { const c = r.clone(); caches.open(VERSION).then(x => x.put(e.request, c)); return r; })
    .catch(() => caches.match(e.request).then(r => r || caches.match("index.html"))));
});
