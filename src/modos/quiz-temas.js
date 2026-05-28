// Modo 1 — Quiz por temas (MCQ clásico). Sección 3, Modo 1.
import { el, mount, badge } from "../ui/dom.js";
import { getAll } from "../db/db.js";
import { runMcq } from "../ui/mcq.js";
import { navegar } from "../ui/router.js";
import { requiereImagenFaltante } from "../ui/imagen.js";
import { registrarRespuesta, registrarSesion } from "../db/stats.js";
import { pendientesHoy } from "../repaso/sm2.js";

function valoresUnicos(items, campo) {
  return [...new Set(items.map((i) => i[campo]).filter(Boolean))].sort();
}

function selectFiltro(label, valores) {
  const sel = el("select", {}, [
    el("option", { value: "" }, `Todas (${label})`),
    ...valores.map((v) => el("option", { value: v }, v)),
  ]);
  return el("label", { class: "filtro" }, [el("span", { text: label }), sel]);
}

export async function vistaQuizFiltros() {
  const todas = await getAll("preguntas");

  const fEsp = selectFiltro("Especialidad", valoresUnicos(todas, "especialidad_principal"));
  const fTema = selectFiltro("Tema", valoresUnicos(todas, "tema_validado"));
  const fSist = selectFiltro("Sistema (Behrens)", valoresUnicos(todas, "sistema_behrens"));
  const fDif = selectFiltro("Dificultad", valoresUnicos(todas, "dificultad_estimada"));
  const fFrec = selectFiltro("Frecuencia EUNACOM", valoresUnicos(todas, "frecuencia_eunacom"));

  const cantidad = el("select", {}, [10, 20, 30, 50, 100].map((n) =>
    el("option", { value: n, ...(n === 20 ? { selected: "selected" } : {}) }, `${n} preguntas`)));

  const modoRepaso = el("input", { type: "checkbox" });

  const requierenImg = todas.filter(requiereImagenFaltante).length;
  const disponibles = todas.filter((q) => q.utilizable !== false && !requiereImagenFaltante(q)).length;

  const view = el("div", { class: "card" }, [
    el("h2", { text: "Modo 1 · Quiz por temas" }),
    el("p", { class: "muted", text: `${disponibles} preguntas disponibles · banco de ${todas.length}.` }),
    requierenImg ? el("p", { class: "aviso" },
      [badge("requiere imagen", "badge--img"), ` ${requierenImg} pregunta(s) están fuera del quiz hasta adjuntarles imagen (Modo editor).`]) : null,
    el("div", { class: "filtros" }, [fEsp, fTema, fSist, fDif, fFrec,
      el("label", { class: "filtro" }, [el("span", { text: "Cantidad" }), cantidad]),
    ]),
    el("label", { class: "form__check" }, [modoRepaso,
      el("span", { text: "Modo repaso (solo lo que toca repasar hoy según SM-2)" })]),
    el("div", { class: "runner__acciones" }, [
      el("button", { class: "btn btn--primary", onClick: iniciar }, "Comenzar quiz"),
      el("button", { class: "btn btn--ghost", onClick: () => navegar("") }, "Volver"),
    ]),
  ]);
  mount(view);

  function valor(nodo) { return nodo.querySelector("select").value; }

  async function iniciar() {
    let lista = todas.filter((q) => q.utilizable !== false && !requiereImagenFaltante(q));
    const esp = valor(fEsp), tema = valor(fTema), sist = valor(fSist), dif = valor(fDif), frec = valor(fFrec);
    if (esp) lista = lista.filter((q) => q.especialidad_principal === esp);
    if (tema) lista = lista.filter((q) => q.tema_validado === tema);
    if (sist) lista = lista.filter((q) => q.sistema_behrens === sist);
    if (dif) lista = lista.filter((q) => q.dificultad_estimada === dif);
    if (frec) lista = lista.filter((q) => q.frecuencia_eunacom === frec);

    if (modoRepaso.checked) {
      const pend = new Set((await pendientesHoy("pregunta")).map((c) => c.id));
      lista = lista.filter((q) => pend.has(q.id_unico));
    }

    lista = mezclar(lista).slice(0, parseInt(cantidad.value, 10));
    const items = lista.map((q) => normalizar(q));

    runMcq({
      titulo: "Quiz por temas",
      subtitulo: modoRepaso.checked ? "Modo repaso (SM-2)" : "Práctica libre",
      items,
      onAnswer: (item, correcta) =>
        registrarRespuesta({ store: "preguntas", item: item._raw, correcta,
          tema: item._raw.tema_validado, ref: { tipo: "pregunta", id: item.id } }),
      onFinish: (r) => registrarSesion({ modo: "quiz", ...r }),
    });
  }
}

function normalizar(q) {
  return {
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
  };
}

function mezclar(a) {
  const arr = a.slice();
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}
