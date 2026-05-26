// Vista de progreso / estadísticas globales (store 5.4) + estado del repaso.
import { el, mount, badge } from "./dom.js";
import { navegar } from "./router.js";
import { leerProgreso } from "../db/stats.js";
import { estadisticasRepaso } from "../repaso/sm2.js";

export async function vistaProgreso() {
  const g = await leerProgreso();
  const rep = await estadisticasRepaso();
  const pct = g.total_respondidas ? Math.round((g.total_correctas / g.total_respondidas) * 100) : 0;

  const temas = Object.entries(g.por_tema || {})
    .map(([t, v]) => ({ t, ...v, pct: v.respondidas ? Math.round((v.correctas / v.respondidas) * 100) : 0 }))
    .sort((a, b) => a.pct - b.pct);

  mount(el("div", { class: "card" }, [
    el("h2", { text: "Mi progreso" }),
    el("div", { class: "stats-grid" }, [
      stat("Respondidas", g.total_respondidas),
      stat("Acierto global", `${pct}%`),
      stat("Racha", `${g.racha_dias} día(s)`),
      stat("Repaso pendiente", rep.pendientes),
    ]),
    el("h3", { text: "Temas más débiles" }),
    temas.length ? el("div", { class: "barras" }, temas.slice(0, 12).map((x) =>
      el("div", { class: "barra" }, [
        el("div", { class: "barra__label" }, [el("span", { text: x.t }), el("span", { class: "muted", text: `${x.pct}% (${x.respondidas})` })]),
        el("div", { class: "barra__track" }, [el("div", { class: `barra__fill ${x.pct < 60 ? "barra__fill--bajo" : ""}`, style: `width:${x.pct}%` })]),
      ]))) : el("p", { class: "muted", text: "Aún no hay datos. Responde algunas preguntas." }),
    el("h3", { text: "Sesiones recientes" }),
    g.sesiones && g.sesiones.length ? el("ul", { class: "importar__lista" }, g.sesiones.slice(0, 10).map((s) =>
      el("li", {}, [badge(s.modo), el("span", { text: `${s.aciertos}/${s.total} · ${s.pct}% · ${new Date(s.fecha).toLocaleDateString()}` })])))
      : el("p", { class: "muted", text: "Sin sesiones registradas." }),
    el("button", { class: "btn btn--ghost", onClick: () => navegar("") }, "Volver"),
  ]));
}

function stat(label, valor) {
  return el("div", { class: "stat" }, [el("div", { class: "stat__val", text: String(valor) }), el("div", { class: "stat__lbl", text: label })]);
}
