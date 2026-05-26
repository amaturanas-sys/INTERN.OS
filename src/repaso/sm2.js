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
