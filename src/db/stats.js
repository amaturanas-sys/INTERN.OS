// Persistencia de estadísticas de uso y progreso global (store 5.4).
import { get, put } from "./db.js";
import { registrarRepaso, calidadDesdeResultado } from "../repaso/sm2.js";

const hoy = () => new Date().toISOString().slice(0, 10);

async function progresoGlobal() {
  let g = await get("progreso_usuario", "global");
  if (!g) {
    g = {
      id: "global", total_respondidas: 0, total_correctas: 0,
      racha_dias: 0, ultimo_dia: null, por_tema: {}, sesiones: [],
    };
  }
  return g;
}

export async function registrarRespuesta({ store, item, correcta, tema, ref }) {
  // 1) estadísticas en el propio ítem (si las tiene)
  if (item && item.estadisticas_usuario) {
    item.estadisticas_usuario.veces_respondida += 1;
    if (correcta) item.estadisticas_usuario.veces_correcta += 1;
    item.estadisticas_usuario.ultima_vez = new Date().toISOString();
    await put(store, item);
  }
  // 2) SM-2
  if (ref) await registrarRepaso(ref.tipo, ref.id, calidadDesdeResultado(correcta));
  // 3) progreso global
  const g = await progresoGlobal();
  g.total_respondidas += 1;
  if (correcta) g.total_correctas += 1;
  const t = tema || "sin_tema";
  g.por_tema[t] = g.por_tema[t] || { respondidas: 0, correctas: 0 };
  g.por_tema[t].respondidas += 1;
  if (correcta) g.por_tema[t].correctas += 1;
  // racha
  const d = hoy();
  if (g.ultimo_dia !== d) {
    const ayer = new Date(Date.now() - 86400000).toISOString().slice(0, 10);
    g.racha_dias = g.ultimo_dia === ayer ? g.racha_dias + 1 : 1;
    g.ultimo_dia = d;
  }
  await put("progreso_usuario", g);
}

export async function registrarSesion(resumen) {
  const g = await progresoGlobal();
  g.sesiones.unshift({ fecha: new Date().toISOString(), ...resumen });
  g.sesiones = g.sesiones.slice(0, 50);
  await put("progreso_usuario", g);
}

export async function leerProgreso() {
  return progresoGlobal();
}
