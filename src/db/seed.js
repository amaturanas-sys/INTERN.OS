// Carga inicial del banco precargado en IndexedDB (solo la primera vez).
import { bulkPut, count, escribirAtomico, getAll, getConfig, setConfig } from "./db.js";

// Campos que pertenecen al USUARIO, no al banco. Viven dentro del mismo
// registro que el contenido, así que un bulkPut a secas los borraría.
const CAMPOS_USUARIO = [
  "marcada_revision",
  "estadisticas_usuario",
];

// Editado por el usuario = su historial tiene una entrada de versión 2 o más:
// el editor SIEMPRE agrega una al guardar. Los datos publicados traen a lo
// sumo la entrada "Versión inicial" (versión 1).
// No sirve mirar version_actual: el banco de preguntas se publicó con
// version_actual = 2 en TODOS los registros, y con ese criterio cada re-siembra
// conservaba el texto viejo de las 4 017 preguntas: ninguna reparación del
// banco llegaba a las instalaciones existentes.
function editadoPorUsuario(r) {
  return Array.isArray(r.historial_ediciones) &&
    r.historial_ediciones.some((h) => h && (h.version || 0) > 1);
}

// Campos de CONTENIDO que el editor puede haber corregido. Solo se conservan
// cuando el registro existente fue editado por el usuario (junto con su
// historial_ediciones y version_actual).
const CAMPOS_EDITABLES = [
  "enunciado", "opciones", "justificacion", "bibliografia_sugerida",
  "titulo", "etapas", "resumen_final", "concepto", "pregunta", "explicacion",
  "imagen",
];

/**
 * Funde los registros entrantes del banco con lo que ya hay en IndexedDB,
 * preservando el trabajo del usuario:
 *  - marcas, estadísticas e historial se arrastran siempre;
 *  - si el registro fue editado por el usuario, su contenido gana sobre el
 *    del banco: de lo contrario cada release borraría las correcciones.
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
    if (editadoPorUsuario(viejo)) {
      for (const c of ["historial_ediciones", "version_actual", ...CAMPOS_EDITABLES]) {
        if (viejo[c] !== undefined) fundido[c] = viejo[c];
      }
      edicionesIntactas++;
    }
    return fundido;
  });
  return { salida, preservados, edicionesIntactas };
}

/**
 * Aplica meta.reemplazos del banco: { id_eliminado: id_superviviente }.
 *
 * El banco elimina duplicados y copias degradadas, pero bulkPut solo agrega o
 * actualiza: sin esto, las instalaciones existentes conservaban para siempre
 * las 1 777 preguntas eliminadas (con el texto sin reparar) junto a las nuevas.
 *
 * Por cada pregunta eliminada que exista en el dispositivo:
 *  - marca de revisión y estadísticas pasan a la superviviente (se suman);
 *  - su tarjeta de repaso SM-2 pasa a la superviviente si esta no tenía una;
 *  - se borra la pregunta y su tarjeta.
 * Si el usuario la EDITÓ no se toca: su trabajo gana.
 *
 * Modifica `fundidas` (el array que se va a guardar) en su lugar y devuelve
 * qué tarjetas escribir y qué borrar; el llamador lo guarda TODO en una sola
 * transacción (si se cortara a medias, un segundo arranque sumaría dos veces).
 */
async function aplicarReemplazos(reemplazos, previas, fundidas) {
  const resultado = { eliminadas: 0, conservadasPorEdicion: 0, tarjetasMovidas: 0,
                      escrituras: {}, borrados: {} };
  if (!reemplazos) return resultado;
  const porId = new Map(fundidas.map((p) => [p.id_unico, p]));
  const tarjetas = new Map((await getAll("repaso").catch(() => [])).map((c) => [c.ref, c]));
  const borrarPreguntas = [], borrarTarjetas = [], tarjetasNuevas = [];

  for (const vieja of previas) {
    const idNuevo = reemplazos[vieja.id_unico];
    if (!idNuevo || porId.has(vieja.id_unico)) continue;
    if (editadoPorUsuario(vieja)) { resultado.conservadasPorEdicion++; continue; }
    const sup = porId.get(idNuevo);
    if (sup) {
      if (vieja.marcada_revision) sup.marcada_revision = true;
      const a = vieja.estadisticas_usuario, b = sup.estadisticas_usuario;
      if (a) {
        sup.estadisticas_usuario = {
          ...(b || {}),
          veces_respondida: (a.veces_respondida || 0) + ((b && b.veces_respondida) || 0),
          veces_correcta: (a.veces_correcta || 0) + ((b && b.veces_correcta) || 0),
          ultima_vez: [a.ultima_vez, b && b.ultima_vez].filter(Boolean).sort().pop() || null,
        };
      }
      const refVieja = `pregunta:${vieja.id_unico}`, refNueva = `pregunta:${idNuevo}`;
      const tarjeta = tarjetas.get(refVieja);
      if (tarjeta && !tarjetas.has(refNueva)) {
        const movida = { ...tarjeta, ref: refNueva, id: idNuevo };
        tarjetas.set(refNueva, movida);
        tarjetasNuevas.push(movida);
        resultado.tarjetasMovidas++;
      }
    }
    borrarPreguntas.push(vieja.id_unico);
    if (tarjetas.has(`pregunta:${vieja.id_unico}`)) borrarTarjetas.push(`pregunta:${vieja.id_unico}`);
  }

  resultado.eliminadas = borrarPreguntas.length;
  resultado.escrituras = { repaso: tarjetasNuevas };
  resultado.borrados = { repaso: borrarTarjetas, preguntas: borrarPreguntas };
  return resultado;
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
  // Primero traspasar el estado de las eliminadas a las supervivientes (muta
  // fPreg.salida), después guardar. Si se guardara antes, el traspaso se perdería.
  const reemp = await aplicarReemplazos(banco.meta && banco.meta.reemplazos, prevPreg, fPreg.salida);
  await escribirAtomico({ preguntas: fPreg.salida, ...reemp.escrituras }, reemp.borrados);
  if (reemp.eliminadas || reemp.conservadasPorEdicion) {
    console.info(`[seed] reemplazos: ${reemp.eliminadas} preguntas eliminadas, ` +
      `${reemp.tarjetasMovidas} tarjetas de repaso traspasadas, ` +
      `${reemp.conservadasPorEdicion} conservadas por estar editadas.`);
  }
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
    reemplazadas: reemp.eliminadas,
  };
}
