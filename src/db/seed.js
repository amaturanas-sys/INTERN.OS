// Carga inicial del banco precargado en IndexedDB (solo la primera vez).
import { bulkPut, count, getAll, getConfig, setConfig } from "./db.js";

// Campos que pertenecen al USUARIO, no al banco. Viven dentro del mismo
// registro que el contenido, así que un bulkPut a secas los borraría.
const CAMPOS_USUARIO = [
  "marcada_revision",
  "estadisticas_usuario",
  "historial_ediciones",
  "version_actual",
];

// Campos de CONTENIDO que el editor puede haber corregido. Solo se conservan
// cuando el registro existente está marcado como editado (version_actual > 1).
const CAMPOS_EDITABLES = [
  "enunciado", "opciones", "justificacion", "bibliografia_sugerida",
  "titulo", "etapas", "resumen_final", "concepto", "pregunta", "explicacion",
  "imagen",
];

/**
 * Funde los registros entrantes del banco con lo que ya hay en IndexedDB,
 * preservando el trabajo del usuario:
 *  - marcas, estadísticas e historial se arrastran siempre;
 *  - si el registro fue editado (version_actual > 1), su contenido gana sobre
 *    el del banco: de lo contrario cada release borraría las correcciones.
 */
function fundirConUsuario(entrantes, existentes, keyPath) {
  const previos = new Map(existentes.map((r) => [r[keyPath], r]));
  let preservados = 0, edicionesIntactas = 0;
  const salida = entrantes.map((nuevo) => {
    const viejo = previos.get(nuevo[keyPath]);
    if (!viejo) return nuevo;
    const fundido = { ...nuevo };
    for (const c of CAMPOS_USUARIO) {
      if (viejo[c] !== undefined) { fundido[c] = viejo[c]; preservados++; }
    }
    if ((viejo.version_actual || 1) > 1) {
      for (const c of CAMPOS_EDITABLES) {
        if (viejo[c] !== undefined) fundido[c] = viejo[c];
      }
      edicionesIntactas++;
    }
    return fundido;
  });
  return { salida, preservados, edicionesIntactas };
}

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
  let banco, casos, defs;
  try {
    [banco, casos, defs] = await Promise.all([
      fetchJson(FUENTES.preguntas),
      fetchJson(FUENTES.casos),
      fetchJson(FUENTES.definiciones),
    ]);
  } catch (e) {
    // Sin red y con la base ya poblada: seguir con lo que hay en IndexedDB.
    // Antes esto lanzaba y dejaba la app colgada en el splash después de cada
    // deploy, aunque las preguntas estuvieran intactas en disco.
    if (nPreguntas > 0) {
      console.warn("[seed] no se pudo descargar el banco; se usa el local:", e.message);
      return { sembrado: false, version: versionSembrada || versionBanco, offline: true };
    }
    throw e;
  }
  // Por si el sidecar no estaba disponible, sincroniza con el banco real.
  versionBanco = (banco.meta && banco.meta.version) || versionBanco;

  // Fusión con lo existente para no pisar marcas, estadísticas ni ediciones.
  onProgress("Indexando preguntas…");
  const [prevPreg, prevCasos, prevDefs] = await Promise.all([
    getAll("preguntas").catch(() => []),
    getAll("casos_clinicos").catch(() => []),
    getAll("definiciones").catch(() => []),
  ]);
  const fPreg = fundirConUsuario(banco.preguntas || [], prevPreg, "id_unico");
  await bulkPut("preguntas", fPreg.salida);
  onProgress("Indexando casos clínicos…");
  const fCasos = fundirConUsuario(casos.casos || [], prevCasos, "id");
  await bulkPut("casos_clinicos", fCasos.salida);
  onProgress("Indexando definiciones…");
  const fDefs = fundirConUsuario(defs.definiciones || [], prevDefs, "id");
  await bulkPut("definiciones", fDefs.salida);
  const edicionesIntactas = fPreg.edicionesIntactas + fCasos.edicionesIntactas + fDefs.edicionesIntactas;
  if (edicionesIntactas) {
    console.info(`[seed] ${edicionesIntactas} ítems editados por el usuario preservados.`);
  }

  await setConfig("seed_done", true);
  await setConfig("seed_banco_version", versionBanco);
  await setConfig("seed_fecha", new Date().toISOString());
  return {
    sembrado: true,
    version: versionBanco,
    preguntas: (banco.preguntas || []).length,
    casos: (casos.casos || []).length,
    definiciones: (defs.definiciones || []).length,
    edicionesPreservadas: edicionesIntactas,
  };
}
