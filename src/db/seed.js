// Carga inicial del banco precargado en IndexedDB (solo la primera vez).
import { bulkPut, count, getConfig, setConfig } from "./db.js";

const FUENTES = {
  preguntas: "./data/banco_inicial.json",
  casos: "./data/casos_iniciales.json",
  definiciones: "./data/definiciones_iniciales.json",
};

async function fetchJson(url) {
  const res = await fetch(url, { cache: "no-cache" });
  if (!res.ok) throw new Error(`No se pudo cargar ${url}: ${res.status}`);
  return res.json();
}

export async function seedIfNeeded(onProgress = () => {}) {
  onProgress("Cargando banco de preguntas…");
  const banco = await fetchJson(FUENTES.preguntas);
  const versionBanco = (banco.meta && banco.meta.version) || "v0";
  const versionSembrada = await getConfig("seed_banco_version", null);
  const nPreguntas = await count("preguntas");
  // Re-sembrar si: nunca se sembró, el store quedó vacío, o cambió la versión.
  if (versionSembrada === versionBanco && nPreguntas > 0) {
    return { sembrado: false };
  }
  await bulkPut("preguntas", banco.preguntas || []);

  onProgress("Cargando casos clínicos…");
  const casos = await fetchJson(FUENTES.casos);
  await bulkPut("casos_clinicos", casos.casos || []);

  onProgress("Cargando definiciones…");
  const defs = await fetchJson(FUENTES.definiciones);
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
