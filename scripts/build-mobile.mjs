// Empaqueta el PWA en `dist/` para que Capacitor lo embeba dentro de la APK.
// Copia solo lo que necesita el runtime web, sella las plantillas de versión
// (igual que el workflow deploy-pages) y deja todo listo para `cap sync`.

import { promises as fs } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const ROOT = path.resolve(path.dirname(__filename), "..");
const DIST = path.join(ROOT, "dist");

// Archivos/directorios a incluir (relativos a ROOT)
const INCLUDES = [
  "index.html",
  "manifest.webmanifest",
  "service-worker.js",
  "assets",
  "data",
  "src",
  "styles",
];

async function rimraf(p) {
  await fs.rm(p, { recursive: true, force: true });
}

async function copyTree(src, dst) {
  const st = await fs.stat(src);
  if (st.isDirectory()) {
    await fs.mkdir(dst, { recursive: true });
    for (const entry of await fs.readdir(src)) {
      await copyTree(path.join(src, entry), path.join(dst, entry));
    }
  } else {
    await fs.mkdir(path.dirname(dst), { recursive: true });
    await fs.copyFile(src, dst);
  }
}

async function leerVersion() {
  const v = await fs.readFile(path.join(ROOT, "VERSION"), "utf8");
  return v.trim();
}

async function sellarPlaceholders(version) {
  const sha = `native-${Date.now().toString(36)}`;
  const fecha = new Date().toISOString();

  // data/version.json
  const versionJsonPath = path.join(DIST, "data", "version.json");
  let versionJson = await fs.readFile(versionJsonPath, "utf8");
  versionJson = versionJson
    .replaceAll("__APP_VERSION__", version)
    .replaceAll("__GIT_SHA__", sha)
    .replaceAll("__BUILD_DATE__", fecha);
  await fs.writeFile(versionJsonPath, versionJson);

  // service-worker.js (cache name único por build)
  const swPath = path.join(DIST, "service-worker.js");
  let sw = await fs.readFile(swPath, "utf8");
  sw = sw.replaceAll("__GIT_SHA__", sha);
  await fs.writeFile(swPath, sw);
}

async function main() {
  console.log(`[build-mobile] limpiando ${DIST}`);
  await rimraf(DIST);
  await fs.mkdir(DIST, { recursive: true });

  for (const item of INCLUDES) {
    const src = path.join(ROOT, item);
    try {
      await fs.access(src);
    } catch {
      console.warn(`[build-mobile] (omitiendo, no existe) ${item}`);
      continue;
    }
    const dst = path.join(DIST, item);
    await copyTree(src, dst);
    console.log(`[build-mobile] copiado ${item}`);
  }

  const version = await leerVersion();
  await sellarPlaceholders(version);
  console.log(`[build-mobile] versión sellada: ${version}`);

  // Resumen tamaños
  console.log(`[build-mobile] OK → ${DIST}`);
}

main().catch((e) => {
  console.error("[build-mobile] ERROR:", e);
  process.exit(1);
});
