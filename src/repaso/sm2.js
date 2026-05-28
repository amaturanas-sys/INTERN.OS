// Algoritmo de repaso espaciado tipo SM-2 (SuperMemo 2).
// Capa opcional sobre los tres modos. Cada ítem se referencia con ref = "tipo:id".
import { get, put, getAll } from "../db/db.js";

const HOY = () => new Date().toISOString().slice(0, 10);

function addDays(isoDate, days) {
  const d = new Date(isoDate + "T00:00:00");
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
}

export function ref(tipo, id) {
  return `${tipo}:${id}`;
}

// quality: 0..5. Convertimos "correcta/incorrecta" a calidad:
//  - correcta => 5, incorrecta => 2 (por debajo de 3 reinicia repeticiones).
export function calidadDesdeResultado(correcta) {
  return correcta ? 5 : 2;
}

export async function registrarRepaso(tipo, id, quality) {
  const r = ref(tipo, id);
  let card = await get("repaso", r);
  if (!card) {
    card = { ref: r, tipo, id, ef: 2.5, intervalo: 0, repeticiones: 0, proxima_revision: HOY(), ultima: null };
  }

  if (quality < 3) {
    card.repeticiones = 0;
    card.intervalo = 1;
  } else {
    card.repeticiones += 1;
    if (card.repeticiones === 1) card.intervalo = 1;
    else if (card.repeticiones === 2) card.intervalo = 6;
    else card.intervalo = Math.round(card.intervalo * card.ef);
  }

  // Ajuste del factor de facilidad (EF), mínimo 1.3.
  card.ef = Math.max(1.3, card.ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)));
  card.ultima = HOY();
  card.proxima_revision = addDays(HOY(), card.intervalo);

  await put("repaso", card);
  return card;
}

// Devuelve los refs que tocan repasar hoy o antes, filtrables por tipo.
export async function pendientesHoy(tipo = null) {
  const all = await getAll("repaso");
  const hoy = HOY();
  return all.filter((c) => c.proxima_revision <= hoy && (tipo ? c.tipo === tipo : true));
}

export async function estadisticasRepaso() {
  const all = await getAll("repaso");
  const hoy = HOY();
  return {
    total: all.length,
    pendientes: all.filter((c) => c.proxima_revision <= hoy).length,
    aprendidas: all.filter((c) => c.repeticiones >= 3).length,
  };
}

// Arma una "sesión del día" mezclando, en orden de prioridad:
//   1) repaso pendiente SM-2 hoy (hasta la mitad del target)
//   2) preguntas que han fallado más que acertado (curado)
//   3) preguntas nunca respondidas (descubrimiento)
// Devuelve la lista de objetos de preguntas (ya hidratados, no refs).
export async function sesionDelDia(target = 20) {
  const todasPreg = (await getAll("preguntas")).filter(
    (q) => q && q.id_unico && q.utilizable !== false && q.inactivo !== true &&
           Array.isArray(q.opciones) && q.opciones.length > 0 &&
           q.opciones.some((o) => o.correcta)
  );
  const porId = new Map(todasPreg.map((q) => [q.id_unico, q]));
  const cards = await getAll("repaso");
  const hoy = HOY();

  // 1) Repaso pendiente (solo preguntas, ignorar casos/defs)
  const pendIds = cards
    .filter((c) => c.tipo === "pregunta" && c.proxima_revision <= hoy)
    .sort((a, b) => (a.proxima_revision < b.proxima_revision ? -1 : 1))
    .map((c) => c.id);

  // 2) Falladas históricas (respondidas > correctas)
  const falladas = todasPreg
    .filter((q) => {
      const e = q.estadisticas_usuario || {};
      return (e.veces_respondida || 0) > 0 &&
        (e.veces_correcta || 0) < (e.veces_respondida || 0);
    })
    .sort((a, b) => {
      const ea = a.estadisticas_usuario || {};
      const eb = b.estadisticas_usuario || {};
      const ra = (ea.veces_correcta || 0) / (ea.veces_respondida || 1);
      const rb = (eb.veces_correcta || 0) / (eb.veces_respondida || 1);
      return ra - rb; // peor primero
    })
    .map((q) => q.id_unico);

  // 3) Nuevas (nunca respondidas)
  const nuevas = todasPreg
    .filter((q) => !(q.estadisticas_usuario && q.estadisticas_usuario.veces_respondida))
    .map((q) => q.id_unico);
  // mezcla las nuevas
  for (let i = nuevas.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [nuevas[i], nuevas[j]] = [nuevas[j], nuevas[i]];
  }

  const seleccion = new Set();
  const tomarHasta = (lista, max) => {
    for (const id of lista) {
      if (seleccion.size >= target) return;
      if (seleccion.size - antesDeBloque >= max) return;
      if (porId.has(id) && !seleccion.has(id)) seleccion.add(id);
    }
  };
  let antesDeBloque = 0;
  tomarHasta(pendIds, Math.ceil(target * 0.5));
  antesDeBloque = seleccion.size;
  tomarHasta(falladas, Math.ceil(target * 0.3));
  antesDeBloque = seleccion.size;
  tomarHasta(nuevas, target); // completar con nuevas
  // si aún falta y no quedan nuevas, completar con resto (re-repasos blandos)
  antesDeBloque = 0;
  if (seleccion.size < target) {
    const resto = todasPreg.map((q) => q.id_unico).sort(() => Math.random() - 0.5);
    tomarHasta(resto, target);
  }

  return [...seleccion].map((id) => porId.get(id));
}
