// Importación de material .md (sección 6 + 10.1). Selector de archivos,
// previsualización y carga a IndexedDB. Soporta mcq, caso y definicion.
import { el, clear, mount, toast, badge } from "../ui/dom.js";
import { navegar } from "../ui/router.js";
import { bulkPut } from "../db/db.js";
import { parseMarkdown } from "./md-parser.js";

const EJEMPLO = `---
tipo: mcq
especialidad: cardio
tema: HTA
dificultad: intermedia
---
# Pregunta
Hombre de 65 años, diabético, PA 160/95...

## Opciones
- (x) Iniciar IECA
- ( ) Iniciar betabloqueador
- ( ) Observar

## Justificación
En diabéticos, los IECA son primera línea porque...`;

export async function vistaImportar() {
  let parsed = null;

  const file = el("input", { type: "file", accept: ".md,text/markdown,text/plain", multiple: "multiple" });
  const previa = el("div", { class: "importar__previa" });
  const btnConfirmar = el("button", { class: "btn btn--primary", disabled: "disabled", onClick: confirmar }, "Incorporar a la app");

  file.addEventListener("change", async () => {
    const archivos = Array.from(file.files);
    if (!archivos.length) return;
    const acc = { preguntas: [], casos: [], definiciones: [], errores: [] };
    for (const f of archivos) {
      const texto = await f.text();
      const r = parseMarkdown(texto);
      acc.preguntas.push(...r.preguntas);
      acc.casos.push(...r.casos);
      acc.definiciones.push(...r.definiciones);
      acc.errores.push(...r.errores.map((e) => `${f.name}: ${e}`));
    }
    parsed = acc;
    mostrarPrevia(acc);
  });

  function mostrarPrevia(r) {
    clear(previa);
    const total = r.preguntas.length + r.casos.length + r.definiciones.length;
    previa.append(el("div", { class: "chips" }, [
      badge(`${r.preguntas.length} preguntas`, "badge--img"),
      badge(`${r.casos.length} casos`),
      badge(`${r.definiciones.length} definiciones`),
    ]));

    const items = [
      ...r.preguntas.map((q) => ({ t: "MCQ", txt: q.enunciado })),
      ...r.casos.map((c) => ({ t: "Caso", txt: `${c.titulo} (${c.etapas.length} etapas)` })),
      ...r.definiciones.map((d) => ({ t: "Def", txt: d.pregunta })),
    ];
    previa.appendChild(el("ul", { class: "importar__lista" }, items.slice(0, 30).map((x) =>
      el("li", {}, [badge(x.t), el("span", { text: (x.txt || "").slice(0, 90) })]))));

    if (r.errores.length) {
      previa.appendChild(el("div", { class: "aviso aviso--error" }, [
        el("strong", { text: `${r.errores.length} aviso(s):` }),
        el("ul", {}, r.errores.slice(0, 10).map((e) => el("li", { text: e }))),
      ]));
    }
    btnConfirmar.disabled = total === 0;
  }

  async function confirmar() {
    if (!parsed) return;
    if (parsed.preguntas.length) await bulkPut("preguntas", parsed.preguntas);
    if (parsed.casos.length) await bulkPut("casos_clinicos", parsed.casos);
    if (parsed.definiciones.length) await bulkPut("definiciones", parsed.definiciones);
    const total = parsed.preguntas.length + parsed.casos.length + parsed.definiciones.length;
    toast(`${total} ítem(s) incorporados.`, "ok");
    navegar("");
  }

  mount(el("div", { class: "card" }, [
    el("h2", { text: "Importar material (.md / .txt)" }),
    el("p", { class: "muted", text: "Selecciona uno o varios archivos .md o .txt con el formato de front-matter. Se previsualiza antes de incorporar." }),
    el("label", { class: "form__row" }, [el("span", { class: "form__label", text: "Archivos .md / .txt" }), file]),
    previa,
    el("details", { class: "ayuda" }, [
      el("summary", { text: "Ver formato esperado (convención .md)" }),
      el("pre", { class: "snapshot", text: EJEMPLO }),
      el("p", { class: "muted", text: "tipo admite: mcq, caso, definicion. Para definicion añade 'concepto:' y 'subtipo:'. Para caso usa secciones '## Etapa: <tipo>', '### Opciones' y '## Resumen'. La marca (x) indica la correcta; tras '|' puedes añadir feedback." }),
    ]),
    el("div", { class: "runner__acciones" }, [btnConfirmar,
      el("button", { class: "btn btn--ghost", onClick: () => navegar("") }, "Volver")]),
  ]));
}
