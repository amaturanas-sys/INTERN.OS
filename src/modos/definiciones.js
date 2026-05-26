// Modo 3 — Definiciones (conceptos, fármacos, herramientas). Sección 3, Modo 3.
import { el, mount } from "../ui/dom.js";
import { getAll } from "../db/db.js";
import { runMcq } from "../ui/mcq.js";
import { navegar } from "../ui/router.js";
import { registrarRespuesta, registrarSesion } from "../db/stats.js";
import { pendientesHoy } from "../repaso/sm2.js";

const ETIQUETA = { farmaco: "Fármacos", concepto: "Conceptos", herramienta: "Herramientas diagnósticas" };

export async function vistaDefiniciones() {
  const todas = await getAll("definiciones");
  const tipos = [...new Set(todas.map((d) => d.tipo))];

  const fTipo = el("select", {}, [
    el("option", { value: "" }, "Todos los subtipos"),
    ...tipos.map((t) => el("option", { value: t }, ETIQUETA[t] || t)),
  ]);
  const fEsp = el("select", {}, [
    el("option", { value: "" }, "Todas las especialidades"),
    ...[...new Set(todas.map((d) => d.especialidad).filter(Boolean))].map((e) => el("option", { value: e }, e)),
  ]);
  const modoRepaso = el("input", { type: "checkbox" });

  mount(el("div", { class: "card" }, [
    el("h2", { text: "Modo 3 · Definiciones" }),
    el("p", { class: "muted", text: `${todas.length} definiciones en formato MCQ.` }),
    el("div", { class: "filtros" }, [
      el("label", { class: "filtro" }, [el("span", { text: "Subtipo" }), fTipo]),
      el("label", { class: "filtro" }, [el("span", { text: "Especialidad" }), fEsp]),
    ]),
    el("label", { class: "form__check" }, [modoRepaso,
      el("span", { text: "Modo repaso (SM-2)" })]),
    el("div", { class: "runner__acciones" }, [
      el("button", { class: "btn btn--primary", onClick: iniciar }, "Comenzar"),
      el("button", { class: "btn btn--ghost", onClick: () => navegar("") }, "Volver"),
    ]),
  ]));

  async function iniciar() {
    let lista = todas.slice();
    if (fTipo.value) lista = lista.filter((d) => d.tipo === fTipo.value);
    if (fEsp.value) lista = lista.filter((d) => d.especialidad === fEsp.value);
    if (modoRepaso.checked) {
      const pend = new Set((await pendientesHoy("definicion")).map((c) => c.id));
      lista = lista.filter((d) => pend.has(d.id));
    }
    lista = mezclar(lista);
    const items = lista.map((d) => ({
      id: d.id,
      enunciado: d.pregunta,
      opciones: d.opciones,
      explicacion: d.explicacion,
      imagen: d.imagen,
      editado: d.version_actual > 1,
      version: d.version_actual,
      subtitulo: [ETIQUETA[d.tipo] || d.tipo, d.concepto].filter(Boolean),
      onEdit: () => navegar(`editar/definicion/${encodeURIComponent(d.id)}`),
      _raw: d,
    }));
    runMcq({
      titulo: "Definiciones", subtitulo: modoRepaso.checked ? "Modo repaso" : "Práctica libre", items,
      onAnswer: (item, correcta) =>
        registrarRespuesta({ store: "definiciones", item: item._raw, correcta,
          tema: item._raw.concepto, ref: { tipo: "definicion", id: item.id } }),
      onFinish: (r) => registrarSesion({ modo: "definiciones", ...r }),
    });
  }
}

function mezclar(a) {
  const arr = a.slice();
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}
