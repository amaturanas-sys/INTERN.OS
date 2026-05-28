// Carga inicial del banco precargado en IndexedDB (solo la primera vez).
import { bulkPut, count, getConfig, setConfig } from "./db.js";

const FUENTES = {
  meta: "./data/banco_meta.json",
  preguntas: "./data/banco_inicial.json",
  casos: "./data/casos_iniciales.json",
  definiciones: "./data/definiciones_iniciales.json",
};

async function fetchJson(url) {
  // Sin `no-cache` — el service-worker.js usa network-first para data/*.json
  // y entrega lo último, con fallback offline a la caché.
  const res = await fetch(url);
  if (!res.ok) throw new Error(`No se pudo cargar ${url}: ${res.status}`);
  return res.json();
}

export async function seedIfNeeded(onProgress = () => {}) {
  // 1) Lee SOLO el sidecar (~200 bytes) para decidir si re-sembrar.
  //    Evita descargar el banco completo (~7,8 MB) en cada arranque ya sembrado.
  onProgress("Verificando versión del banco…");
  let versionBanco = "v0";
  try {
    const meta = await fetchJson(FUENTES.meta);
    versionBanco = (meta && meta.version) || "v0";
  } catch (_) {
    // Fallback: si no hay sidecar (deploy antiguo), leemos el banco completo.
  }
  const versionSembrada = await getConfig("seed_banco_version", null);
  const nPreguntas = await count("preguntas");
  if (versionSembrada === versionBanco && nPreguntas > 0) {
    return { sembrado: false, version: versionBanco };
  }

  // 2) Re-seed completo en paralelo.
  onProgress("Cargando contenido inicial…");
  const [banco, casos, defs] = await Promise.all([
    fetchJson(FUENTES.preguntas),
    fetchJson(FUENTES.casos),
    fetchJson(FUENTES.definiciones),
  ]);
  // Por si el sidecar no estaba disponible, sincroniza con el banco real.
  versionBanco = (banco.meta && banco.meta.version) || versionBanco;

  onProgress("Indexando preguntas…");
  await bulkPut("preguntas", banco.preguntas || []);
  onProgress("Indexando casos clínicos…");
  await bulkPut("casos_clinicos", casos.casos || []);
  onProgress("Indexando definiciones…");
  await bulkPut("definiciones", defs.definiciones || []);

  await setConfig("seed_done", true);
  await setConfig("seed_banco_version", versionBanco);
  await setConfig("seed_fecha", new Date().toISOString());
  return {
    sembrado: true,
    version: versionBanco,
    preguntas: (banco.preguntas || []).length,
    casos: (casos.casos || []).length,
    definiciones: (defs.definiciones || []).length,
  };
}
