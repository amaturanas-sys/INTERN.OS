// Pantalla de inicio (dashboard) con acceso a los tres modos y utilidades.
import { el, mount } from "./dom.js";
import { navegar } from "./router.js";
import { count, getConfig, getAll } from "../db/db.js";
import { estadisticasRepaso, sesionDelDia } from "../repaso/sm2.js";
import { leerProgreso, registrarRespuesta, registrarSesion } from "../db/stats.js";
import { runMcq } from "./mcq.js";
import { requiereImagenFaltante } from "./imagen.js";

const hoy = () => new Date().toISOString().slice(0, 10);

export async function vistaHome() {
  const [nPreg, nCasos, nDefs, rep, g, objetivo] = await Promise.all([
    count("preguntas"), count("casos_clinicos"), count("definiciones"),
    estadisticasRepaso(), leerProgreso(), getConfig("objetivo_diario", 30),
  ]);
  const pct = g.total_respondidas ? Math.round((g.total_correctas / g.total_respondidas) * 100) : 0;
  const hoyKey = hoy();
  const respondidasHoy = (g.por_dia && g.por_dia[hoyKey]) ? g.por_dia[hoyKey].respondidas : 0;
  const objetivoPct = Math.min(100, Math.round((respondidasHoy / objetivo) * 100));
  const marcadas = await contarMarcadas();

  function tarjeta(icono, titulo, desc, ruta, meta) {
    return el("button", { class: "modo-card", onClick: () => navegar(ruta) }, [
      el("div", { class: "modo-card__icono", text: icono }),
      el("div", { class: "modo-card__cuerpo" }, [
        el("h3", { text: titulo }),
        el("p", { class: "muted", text: desc }),
        meta ? el("span", { class: "modo-card__meta", text: meta }) : null,
      ]),
      el("span", { class: "lista__flecha", text: "›" }),
    ]);
  }

  mount(el("div", { class: "home" }, [
    el("div", { class: "home__hero" }, [
      el("h1", { text: "EUNACOM" }),
      el("p", { class: "muted", text: "Estudio offline · material del Dr. Guevara" }),
      el("div", { class: "home__resumen" }, [
        el("span", {}, `${pct}% acierto`),
        el("span", {}, `🔥 ${g.racha_dias || 0} día(s) de racha`),
        rep.pendientes ? el("span", { class: "pill" }, `${rep.pendientes} para repasar`) : null,
      ]),
    ]),

    // -------- Sesión del día --------
    el("div", { class: "card sesion-dia" }, [
      el("div", { class: "sesion-dia__cab" }, [
        el("h2", { text: "Hoy" }),
        el("span", { class: "muted", text: `${respondidasHoy} / ${objetivo} preguntas` }),
      ]),
      el("div", { class: "progress" }, [
        el("div", {
          class: `progress__fill ${objetivoPct >= 100 ? "progress__fill--ok" : ""}`,
          style: `width:${objetivoPct}%`,
        }),
      ]),
      el("div", { class: "runner__acciones" }, [
        el("button", { class: "btn btn--primary",
          onClick: () => iniciarSesionDelDia(Math.max(10, Math.min(30, objetivo - respondidasHoy)))
        }, respondidasHoy >= objetivo ? "¡Meta lograda! Una más" : "Comenzar sesión del día"),
      ]),
      heatmap(g.por_dia, objetivo),
    ]),

    el("div", { class: "modos" }, [
      tarjeta("📝", "Quiz por temas", "MCQ clásico con filtros y feedback inmediato.", "quiz", `${nPreg} preguntas`),
      tarjeta("🩺", "Casos clínicos", "Casos paso a paso, lineales con feedback.", "casos", `${nCasos} casos`),
      tarjeta("💡", "Definiciones", "Conceptos, fármacos y herramientas en MCQ.", "definiciones", `${nDefs} definiciones`),
    ]),
    el("h3", { class: "home__sub", text: "Herramientas" }),
    el("div", { class: "modos" }, [
      marcadas > 0
        ? tarjeta("🚩", "Preguntas marcadas", "Cola de preguntas para revisar y corregir.", "marcadas", `${marcadas} en la cola`)
        : null,
      tarjeta("📂", "Importar material", "Carga preguntas/casos/definiciones desde .md.", "importar"),
      tarjeta("📊", "Mi progreso", "Estadísticas, temas débiles y repaso.", "progreso"),
      tarjeta("⚙️", "Ajustes", "Datos, almacenamiento y estado offline.", "ajustes"),
    ]),
  ]));
}

async function iniciarSesionDelDia(target) {
  const lista = (await sesionDelDia(target)).filter((q) => !requiereImagenFaltante(q));
  if (!lista.length) {
    mount(el("div", { class: "card" }, [
      el("h2", { text: "Sesión del día" }),
      el("p", { class: "muted", text: "No quedan preguntas disponibles hoy." }),
      el("button", { class: "btn btn--primary", onClick: () => navegar("") }, "Volver"),
    ]));
    return;
  }
  const items = lista.map((q) => ({
    id: q.id_unico,
    enunciado: q.enunciado,
    opciones: q.opciones,
    explicacion: q.justificacion,
    bibliografia: Array.isArray(q.bibliografia_sugerida) ? q.bibliografia_sugerida : [],
    imagen: q.imagen,
    editado: q.version_actual > 1,
    version: q.version_actual,
    subtitulo: [q.especialidad_principal, q.tema_validado, q.dificultad_estimada].filter(Boolean),
    onEdit: () => navegar(`editar/pregunta/${encodeURIComponent(q.id_unico)}`),
    onMarcar: true,
    onMarcarStore: "preguntas",
    _raw: q,
  }));
  runMcq({
    titulo: "Sesión del día",
    subtitulo: `${items.length} preguntas mezclando repaso + falladas + nuevas`,
    items,
    onAnswer: (item, correcta) => registrarRespuesta({
      store: "preguntas", item: item._raw, correcta,
      tema: item._raw.tema_validado, ref: { tipo: "pregunta", id: item.id },
    }),
    onFinish: (r) => registrarSesion({ modo: "diaria", ...r }),
  });
}

async function contarMarcadas() {
  const all = await getAll("preguntas");
  return all.filter((q) => q.marcada_revision).length;
}

function heatmap(porDia, objetivo) {
  porDia = porDia || {};
  const dias = [];
  for (let i = 29; i >= 0; i--) {
    const d = new Date(Date.now() - i * 86400000).toISOString().slice(0, 10);
    dias.push({ d, n: (porDia[d] && porDia[d].respondidas) || 0 });
  }
  return el("div", { class: "heatmap" },
    dias.map((x) => {
      const intensidad =
        x.n === 0 ? "0" :
        x.n < objetivo / 3 ? "1" :
        x.n < (2 * objetivo) / 3 ? "2" :
        x.n < objetivo ? "3" : "4";
      return el("span", {
        class: `heatmap__c heatmap__c--${intensidad}`,
        title: `${x.d} · ${x.n} respondidas`,
      });
    }));
}
