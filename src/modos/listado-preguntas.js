// Listado de preguntas con búsqueda y filtro por especialidad,
// pensado para curar el banco (clic -> editor con trazabilidad).
import { el, mount, badge } from "../ui/dom.js";
import { getAll } from "../db/db.js";
import { navegar } from "../ui/router.js";

const PAGE = 30;

function normalizar(s) {
  return (s || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "");
}

export async function vistaListadoPreguntas() {
  const todas = await getAll("preguntas");
  let pagina = 0;
  let textoBuscado = "";
  let especFiltro = "";
  let estadoFiltro = "";

  const especialidades = [...new Set(todas.map((q) => q.especialidad_principal).filter(Boolean))].sort();

  const buscarInp = el("input", { type: "search", placeholder: "Buscar enunciado, opción, especialidad…", class: "buscar-pregs__inp" });
  const especSel = el("select", {}, [
    el("option", { value: "" }, "Todas las especialidades"),
    ...especialidades.map((s) => el("option", { value: s }, s)),
  ]);
  const estadoSel = el("select", {}, [
    el("option", { value: "" }, "Estado: cualquiera"),
    el("option", { value: "editadas" }, "Solo editadas"),
    el("option", { value: "no-editadas" }, "No editadas"),
    el("option", { value: "marcadas" }, "Marcadas para revisar"),
    el("option", { value: "no-utilizables" }, "No utilizables"),
  ]);
  const resultadosBox = el("ul", { class: "buscar-pregs__lista" });
  const conteoLbl = el("p", { class: "muted" });
  const paginadorBox = el("div", { class: "runner__acciones" });

  function aplicar() {
    const q = normalizar(textoBuscado).trim();
    const filtradas = todas.filter((p) => {
      if (especFiltro && p.especialidad_principal !== especFiltro) return false;
      if (estadoFiltro === "editadas" && !(p.version_actual > 1)) return false;
      if (estadoFiltro === "no-editadas" && p.version_actual > 1) return false;
      if (estadoFiltro === "marcadas" && !p.marcada_revision) return false;
      if (estadoFiltro === "no-utilizables" && p.utilizable !== false) return false;
      if (q) {
        const blob = normalizar(
          p.enunciado + " " +
          (p.opciones || []).map((o) => o.texto).join(" ") + " " +
          (p.especialidad_principal || "") + " " +
          (p.tema_validado || "")
        );
        if (!blob.includes(q)) return false;
      }
      return true;
    });
    pintar(filtradas);
  }

  function pintar(filtradas) {
    resultadosBox.innerHTML = "";
    paginadorBox.innerHTML = "";
    conteoLbl.textContent = `${filtradas.length} pregunta(s) — página ${pagina + 1} de ${Math.max(1, Math.ceil(filtradas.length / PAGE))}`;
    const slice = filtradas.slice(pagina * PAGE, (pagina + 1) * PAGE);
    slice.forEach((p) => {
      const li = el("li", { class: "buscar-pregs__item" }, [
        el("button", {
          class: "buscar-pregs__btn",
          onClick: () => navegar(`editar/pregunta/${encodeURIComponent(p.id_unico)}`),
        }, [
          el("div", { class: "chips" }, [
            p.especialidad_principal ? badge(p.especialidad_principal) : null,
            p.tema_validado ? badge(p.tema_validado) : null,
            p.version_actual > 1 ? badge(`v${p.version_actual}`, "badge--edit") : null,
            p.marcada_revision ? badge("🚩 marcada") : null,
            p.utilizable === false ? badge("no usable") : null,
          ]),
          el("p", { class: "buscar-pregs__enun", text: p.enunciado }),
        ]),
      ]);
      resultadosBox.appendChild(li);
    });
    const totalP = Math.max(1, Math.ceil(filtradas.length / PAGE));
    if (totalP > 1) {
      paginadorBox.append(
        el("button", {
          class: "btn btn--ghost btn--sm",
          disabled: pagina === 0 ? "disabled" : null,
          onClick: () => { pagina = Math.max(0, pagina - 1); pintar(filtradas); },
        }, "← Anterior"),
        el("button", {
          class: "btn btn--ghost btn--sm",
          disabled: pagina >= totalP - 1 ? "disabled" : null,
          onClick: () => { pagina = Math.min(totalP - 1, pagina + 1); pintar(filtradas); },
        }, "Siguiente →"),
      );
    }
  }

  let typingTimer;
  buscarInp.addEventListener("input", () => {
    clearTimeout(typingTimer);
    typingTimer = setTimeout(() => { textoBuscado = buscarInp.value; pagina = 0; aplicar(); }, 200);
  });
  especSel.addEventListener("change", () => { especFiltro = especSel.value; pagina = 0; aplicar(); });
  estadoSel.addEventListener("change", () => { estadoFiltro = estadoSel.value; pagina = 0; aplicar(); });

  mount(el("div", { class: "card buscar-pregs" }, [
    el("h2", { text: "Editar preguntas" }),
    el("p", { class: "muted", text: "Busca y haz clic para abrir el editor con trazabilidad (fuente obligatoria) y la bibliografía sugerida." }),
    el("div", { class: "buscar-pregs__controles" }, [
      buscarInp, especSel, estadoSel,
    ]),
    conteoLbl,
    resultadosBox,
    paginadorBox,
    el("button", { class: "btn btn--ghost", onClick: () => navegar("") }, "Volver"),
  ]));

  aplicar();
}
