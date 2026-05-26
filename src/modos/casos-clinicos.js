// Modo 2 — Casos clínicos lineales con feedback. Sección 3, Modo 2 + esquema 5.2.
// Lineal: si se equivoca, muestra el error pero el caso CONTINÚA (no se ramifica).
import { el, clear, mount, badge } from "../ui/dom.js";
import { getAll, get } from "../db/db.js";
import { vistaImagen } from "../ui/imagen.js";
import { navegar } from "../ui/router.js";
import { registrarRespuesta, registrarSesion } from "../db/stats.js";

export async function vistaCasosLista() {
  const casos = await getAll("casos_clinicos");
  const cards = casos.map((c) => el("div", { class: "lista__item",
    onClick: () => navegar(`caso/${encodeURIComponent(c.id)}`) }, [
    el("div", {}, [
      el("h3", { text: c.titulo }),
      el("p", { class: "muted", text: `${c.especialidad} · ${c.tema} · ${c.etapas.length} etapas` }),
    ]),
    c.version_actual > 1 ? badge(`editado · v${c.version_actual}`, "badge--edit") : null,
    el("span", { class: "lista__flecha", text: "›" }),
  ]));

  mount(el("div", { class: "card" }, [
    el("h2", { text: "Modo 2 · Casos clínicos" }),
    el("p", { class: "muted", text: "Casos paso a paso. Lineal con feedback: aunque te equivoques, el caso continúa." }),
    casos.length ? el("div", { class: "lista" }, cards)
      : el("p", { class: "muted", text: "No hay casos cargados." }),
    el("button", { class: "btn btn--ghost", onClick: () => navegar("") }, "Volver"),
  ]));
}

export async function vistaCaso({ id }) {
  const caso = await get("casos_clinicos", id);
  if (!caso) { navegar("casos"); return; }

  const etapas = caso.etapas.slice().sort((a, b) => a.orden - b.orden);
  let idx = 0;
  const decisiones = [];
  const cont = el("div", { class: "card runner" });

  function pintarEtapa() {
    const etapa = etapas[idx];
    clear(cont);
    let respondida = false;

    cont.append(
      el("div", { class: "runner__head" }, [
        el("div", {}, [el("h2", { text: caso.titulo }), el("p", { class: "muted", text: `Etapa ${idx + 1} de ${etapas.length} · ${etapa.tipo}` })]),
        el("button", { class: "btn btn--ghost btn--sm",
          onClick: () => navegar(`editar/caso/${encodeURIComponent(caso.id)}`) }, "✎ Editar"),
      ]),
      el("div", { class: "progress" }, [el("div", { class: "progress__fill", style: `width:${(idx / etapas.length) * 100}%` })]),
      el("div", { class: "enunciado" }, [el("p", { class: "enunciado__texto", text: etapa.enunciado }), vistaImagen(etapa.imagen)]),
    );

    const feedback = el("div", { class: "feedback" });
    const opcionesBox = el("div", { class: "opciones" });
    etapa.opciones.forEach((op) => {
      const btn = el("button", { class: "opcion" }, [
        el("span", { class: "opcion__letra", text: op.letra.toUpperCase() }),
        el("span", { class: "opcion__texto", text: op.texto }),
      ]);
      btn.addEventListener("click", () => {
        if (respondida) return;
        respondida = true;
        const correcta = !!op.correcta;
        decisiones.push({ etapa: etapa.orden, tipo: etapa.tipo, correcta, elegida: op.texto });

        Array.from(opcionesBox.children).forEach((b, i) => {
          b.classList.add("opcion--bloqueada");
          if (etapa.opciones[i].correcta) b.classList.add("opcion--correcta");
        });
        if (!correcta) btn.classList.add("opcion--incorrecta");

        feedback.className = `feedback feedback--visible feedback--${correcta ? "ok" : "mal"}`;
        clear(feedback);
        feedback.append(
          el("p", { class: "feedback__titulo", text: correcta ? "✔ Correcto" : "✗ Incorrecto — pero el caso continúa" }),
          op.feedback ? el("p", { text: op.feedback }) : null,
          el("button", { class: "btn btn--primary",
            onClick: () => { if (idx === etapas.length - 1) finalizar(); else { idx++; pintarEtapa(); } } },
            idx === etapas.length - 1 ? "Ver resumen del caso" : "Continuar →"),
        );
      });
      opcionesBox.appendChild(btn);
    });

    cont.append(opcionesBox, feedback);
  }

  function finalizar() {
    const aciertos = decisiones.filter((d) => d.correcta).length;
    const pct = Math.round((aciertos / decisiones.length) * 100);
    clear(cont);
    cont.append(
      el("h2", { text: "Resumen del caso" }),
      el("div", { class: "resultado" }, [
        el("div", { class: "resultado__pct", text: `${pct}%` }),
        el("p", { text: `${aciertos} de ${decisiones.length} decisiones correctas.` }),
      ]),
      el("ol", { class: "decisiones" }, decisiones.map((d) =>
        el("li", { class: d.correcta ? "ok" : "mal" }, [
          el("span", { class: "decisiones__tipo", text: d.tipo }),
          el("span", { text: d.elegida }),
          badge(d.correcta ? "✔" : "✗", d.correcta ? "badge--ok" : "badge--mal"),
        ]))),
      el("div", { class: "resumen-final" }, [el("h3", { text: "Evaluación global" }), el("p", { text: caso.resumen_final })]),
      el("div", { class: "runner__acciones" }, [
        el("button", { class: "btn btn--primary", onClick: () => navegar("casos") }, "Otros casos"),
        el("button", { class: "btn btn--ghost", onClick: () => navegar("") }, "Inicio"),
      ]),
    );

    registrarRespuesta({ store: "casos_clinicos", item: null, correcta: pct >= 60,
      tema: caso.tema, ref: { tipo: "caso", id: caso.id } });
    registrarSesion({ modo: "caso", id: caso.id, total: decisiones.length, aciertos, pct });
  }

  mount(cont);
  pintarEtapa();
}
