// Service Worker: cachea toda la app para uso 100% offline.
// CACHE incluye el SHA del commit (estampado por el workflow de deploy)
// para que cada release invalide automáticamente la caché previa.
const CACHE = "eunacom-__GIT_SHA__";

// Precache CORE: shell de la app + sidecar de metadata.
// El banco completo (~8 MB) se cachea bajo demanda en el primer fetch — así
// el `install` del SW es rápido y robusto en conexiones lentas/iOS.
const ASSETS = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./styles/app.css",
  "./assets/wordmark.png",
  "./assets/statue-bg.png",
  "./assets/icon-192.png",
  "./assets/icon-512.png",
  "./assets/icon-maskable-512.png",
  "./assets/favicon-64.png",
  "./data/banco_meta.json",
  "./data/casos_iniciales.json",
  "./data/definiciones_iniciales.json",
  "./data/biblioteca.json",
  "./data/version.json",
  "./src/app.js",
  "./src/ui/dom.js",
  "./src/ui/router.js",
  "./src/ui/mcq.js",
  "./src/ui/imagen.js",
  "./src/ui/iconos.js",
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
  "./src/modos/biblioteca.js",
  "./src/modos/marcadas.js",
  "./src/modos/listado-preguntas.js",
  "./src/version.js",
];

// Tolerante a fallos: si un asset individual no se puede cachear, el SW
// igual se instala. Antes, `addAll` rechazaba atómicamente al primer 404.
self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE).then((c) =>
      Promise.all(ASSETS.map((a) =>
        c.add(a).catch((err) => console.warn("[sw] skip asset", a, err.message))
      ))
    ).then(() => self.skipWaiting())
  );
});

self.addEventListener("message", (e) => {
  if (e.data && e.data.type === "SKIP_WAITING") self.skipWaiting();
});

// Al activar una versión nueva se purgan las cachés viejas, PERO antes se
// rescatan los data/*.json que estaban ahí. banco_inicial.json (8 MB) no está
// en ASSETS —se cachea bajo demanda— así que una purga a secas lo borraba, y
// quien abriera la app sin red después de un deploy no podía re-sembrar y
// quedaba colgado en el splash con las preguntas intactas en IndexedDB.
self.addEventListener("activate", (e) => {
  e.waitUntil((async () => {
    const nueva = await caches.open(CACHE);
    const keys = await caches.keys();
    const viejas = keys.filter((k) => k !== CACHE);
    for (const k of viejas) {
      const vieja = await caches.open(k);
      for (const req of await vieja.keys()) {
        // Solo los JSON de datos, y solo si la caché nueva aún no los tiene.
        if (!/\/data\/.*\.json$/.test(new URL(req.url).pathname)) continue;
        if (await nueva.match(req)) continue;
        const res = await vieja.match(req);
        if (res) await nueva.put(req, res.clone());
      }
      await caches.delete(k);
    }
    await self.clients.claim();
  })());
});

// Estrategia:
//   - data/*.json → network-first (con fallback a caché). Permite re-seed de
//     contenido actualizado aún si el CACHE name no rotó (dev local, edición de
//     contenido vía workflow distinto, etc.).
//   - resto → cache-first (assets estáticos versionados por SHA).
function esDataJson(url) {
  try {
    const u = new URL(url, self.location.origin);
    return u.pathname.endsWith(".json") && u.pathname.includes("/data/");
  } catch (_) { return false; }
}

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  if (esDataJson(req.url)) {
    e.respondWith(
      fetch(req).then((res) => {
        if (res && res.status === 200 && req.url.startsWith(self.location.origin)) {
          const copia = res.clone();
          caches.open(CACHE).then((c) => c.put(req, copia));
        }
        return res;
      }).catch(() => caches.match(req))
    );
    return;
  }
  // Cache-first para el resto (assets versionados por SHA).
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
