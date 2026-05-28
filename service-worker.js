// Service Worker: cachea toda la app para uso 100% offline.
// CACHE incluye el SHA del commit (estampado por el workflow de deploy)
// para que cada release invalide automáticamente la caché previa.
const CACHE = "eunacom-__GIT_SHA__";

const ASSETS = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./styles/app.css",
  "./assets/icon-192.png",
  "./assets/icon-512.png",
  "./assets/icon-maskable-512.png",
  "./assets/favicon-64.png",
  "./assets/icon.svg",
  "./data/banco_inicial.json",
  "./data/casos_iniciales.json",
  "./data/definiciones_iniciales.json",
  "./data/version.json",
  "./src/app.js",
  "./src/ui/dom.js",
  "./src/ui/router.js",
  "./src/ui/mcq.js",
  "./src/ui/imagen.js",
  "./src/ui/home.js",
  "./src/ui/progreso.js",
  "./src/ui/ajustes.js",
  "./src/db/db.js",
  "./src/db/seed.js",
  "./src/db/stats.js",
  "./src/repaso/sm2.js",
  "./src/importar/md-parser.js",
  "./src/importar/importar.js",
  "./src/editor/editor.js",
  "./src/modos/quiz-temas.js",
  "./src/modos/casos-clinicos.js",
  "./src/modos/definiciones.js",
  "./src/modos/marcadas.js",
  "./src/modos/listado-preguntas.js",
  "./src/version.js",
];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

// Cache-first: todo está precacheado; si falta, va a la red y guarda copia.
self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  e.respondWith(
    caches.match(req).then((hit) => {
      if (hit) return hit;
      return fetch(req).then((res) => {
        if (res && res.status === 200 && req.url.startsWith(self.location.origin)) {
          const copia = res.clone();
          caches.open(CACHE).then((c) => c.put(req, copia));
        }
        return res;
      }).catch(() => caches.match("./index.html"));
    })
  );
});
