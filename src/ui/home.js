// Pantalla de inicio (dashboard) con acceso a los tres modos y utilidades.
import { el, mount } from "./dom.js";
import { navegar } from "./router.js";
import { count } from "../db/db.js";
import { estadisticasRepaso } from "../repaso/sm2.js";
import { leerProgreso } from "../db/stats.js";

export async function vistaHome() {
  const [nPreg, nCasos, nDefs, rep, g] = await Promise.all([
    count("preguntas"), count("casos_clinicos"), count("definiciones"),
    estadisticasRepaso(), leerProgreso(),
  ]);
  const pct = g.total_respondidas ? Math.round((g.total_correctas / g.total_respondidas) * 100) : 0;

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
        el("span", {}, `${g.racha_dias || 0} día(s) de racha`),
        rep.pendientes ? el("span", { class: "pill" }, `${rep.pendientes} para repasar`) : null,
      ]),
    ]),
    el("div", { class: "modos" }, [
      tarjeta("📝", "Quiz por temas", "MCQ clásico con filtros y feedback inmediato.", "quiz", `${nPreg} preguntas`),
      tarjeta("🩺", "Casos clínicos", "Casos paso a paso, lineales con feedback.", "casos", `${nCasos} casos`),
      tarjeta("💡", "Definiciones", "Conceptos, fármacos y herramientas en MCQ.", "definiciones", `${nDefs} definiciones`),
    ]),
    el("h3", { class: "home__sub", text: "Herramientas" }),
    el("div", { class: "modos" }, [
      tarjeta("📂", "Importar material", "Carga preguntas/casos/definiciones desde .md.", "importar"),
      tarjeta("📊", "Mi progreso", "Estadísticas, temas débiles y repaso.", "progreso"),
      tarjeta("⚙️", "Ajustes", "Datos, almacenamiento y estado offline.", "ajustes"),
    ]),
  ]));
}
