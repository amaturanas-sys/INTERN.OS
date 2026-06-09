// Biblioteca — Catálogo CIMIO 2026 (Consultor Inmediato Medicina Interna Offline).
// Carga data/biblioteca.json bajo demanda, lista por unidades, búsqueda en
// título + cuerpo. Mantiene la paleta InternOS (sin colores propios de CIMIO).
import { el, mount } from "../ui/dom.js";
import { navegar } from "../ui/router.js";
import { icono } from "../ui/iconos.js";

let _data = null;

async function cargar() {
  if (_data) return _data;
  const res = await fetch("data/biblioteca.json", { cache: "force-cache" });
  if (!res.ok) throw new Error("No se pudo cargar la biblioteca");
  _data = await res.json();
  return _data;
}

// Normaliza texto para búsqueda: NFD + quita diacríticos (rango U+0300-U+036F).
function norm(s) {
  return (s || "").toString().normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
}

// Búsqueda full-text: matchea sobre título y cuerpo (sin HTML); devuelve ranking.
function buscar(entradas, query) {
  const q = norm(query.trim());
  if (!q) return [];
  const tokens = q.split(/\s+/).filter(Boolean);
  const tmp = document.createElement("div");
  return entradas.map((e) => {
    tmp.innerHTML = e.html;
    const texto = norm(tmp.textContent || "");
    const titNorm = norm(e.titulo);
    const unidadNorm = norm(e.unidad);
    let score = 0;
    for (const t of tokens) {
      if (titNorm.includes(t)) score += 10;
      if (unidadNorm.includes(t)) score += 3;
      const safe = t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      const matches = (texto.match(new RegExp(safe, "g")) || []).length;
      score += matches;
    }
    return { entrada: e, score };
  }).filter((r) => r.score > 0).sort((a, b) => b.score - a.score);
}

// === Landing: índice por unidades + barra de búsqueda ===
export async function vistaBiblioteca() {
  const data = await cargar();
  const unidadesMap = new Map();
  for (const e of data.entradas) {
    if (!unidadesMap.has(e.unidad)) unidadesMap.set(e.unidad, []);
    unidadesMap.get(e.unidad).push(e);
  }

  const buscador = el("input", {
    type: "search",
    class: "biblio__buscador",
    placeholder: `Buscar en ${data.entradas.length} patologías…`,
    autocomplete: "off",
  });
  const resultados = el("div", { class: "biblio__resultados", hidden: true });
  const indice = el("div", { class: "biblio__indice" });

  // Render del índice por unidad (acordeón nativo <details>)
  for (const [unidad, items] of unidadesMap) {
    if (unidad === "¡BIENVENIDO!") continue;
    const lista = el("div", { class: "biblio__lista" },
      items.map((it) => el("button", {
        class: "biblio__item",
        type: "button",
        onClick: () => navegar(`biblioteca/${encodeURIComponent(it.id)}`),
      }, [
        el("span", { class: "biblio__item-titulo", text: it.titulo }),
        icono("chevron_derecha", { tamano: 14, clase: "biblio__item-flecha" }),
      ])),
    );
    indice.appendChild(el("details", { class: "biblio__unidad", open: "" }, [
      el("summary", { class: "biblio__unidad-titulo" }, [
        el("span", { text: unidad }),
        el("span", { class: "biblio__unidad-conteo", text: `${items.length}` }),
      ]),
      lista,
    ]));
  }

  let timer = null;
  buscador.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      const q = buscador.value.trim();
      if (!q) {
        resultados.hidden = true;
        indice.hidden = false;
        resultados.innerHTML = "";
        return;
      }
      const hits = buscar(data.entradas, q).slice(0, 30);
      indice.hidden = true;
      resultados.hidden = false;
      resultados.innerHTML = "";
      if (!hits.length) {
        resultados.appendChild(el("p", { class: "muted",
          text: `Sin coincidencias para "${q}". Prueba otros términos.` }));
        return;
      }
      resultados.appendChild(el("p", { class: "muted",
        text: `${hits.length} resultado${hits.length === 1 ? "" : "s"} para "${q}"` }));
      for (const { entrada } of hits) {
        resultados.appendChild(el("button", {
          class: "biblio__item biblio__item--resultado",
          type: "button",
          onClick: () => navegar(`biblioteca/${encodeURIComponent(entrada.id)}`),
        }, [
          el("div", { class: "biblio__item-cuerpo" }, [
            el("span", { class: "biblio__item-titulo", text: entrada.titulo }),
            el("span", { class: "biblio__item-unidad muted", text: entrada.unidad }),
          ]),
          icono("chevron_derecha", { tamano: 14, clase: "biblio__item-flecha" }),
        ]));
      }
    }, 120);
  });

  mount(el("div", { class: "biblio" }, [
    el("div", { class: "biblio__cab" }, [
      el("h2", { text: "Biblioteca" }),
      el("p", { class: "muted", text:
        `${data.entradas.length} patologías de Medicina Interna y especialidades · ` +
        `fuente: ${data.meta.fuente || "CIMIO 2026"}` }),
    ]),
    el("div", { class: "biblio__buscar" }, [
      icono("buscar", { tamano: 16, clase: "biblio__buscar-icono" }),
      buscador,
    ]),
    resultados,
    indice,
  ]));
}

// === Vista de entrada individual ===
export async function vistaBibliotecaEntrada({ id }) {
  const data = await cargar();
  const entrada = data.entradas.find((e) => e.id === id);
  if (!entrada) {
    mount(el("div", { class: "card" }, [
      el("h2", { text: "Entrada no encontrada" }),
      el("p", { class: "muted", text: `No hay una patología con ID "${id}".` }),
      el("button", { class: "btn btn--primary",
        onClick: () => navegar("biblioteca") }, "Volver a la biblioteca"),
    ]));
    return;
  }

  // Navegación entre entradas de la misma unidad
  const mismaUnidad = data.entradas.filter((e) => e.unidad === entrada.unidad);
  const idx = mismaUnidad.findIndex((e) => e.id === entrada.id);
  const prev = mismaUnidad[idx - 1];
  const next = mismaUnidad[idx + 1];

  function navBar() {
    return el("div", { class: "biblio__nav" }, [
      el("button", {
        class: "btn btn--ghost btn--sm",
        onClick: () => navegar("biblioteca"),
      }, [icono("chevron_izquierda", { tamano: 14 }), "Índice"]),
      prev ? el("button", {
        class: "btn btn--ghost btn--sm",
        onClick: () => navegar(`biblioteca/${encodeURIComponent(prev.id)}`),
        title: prev.titulo,
      }, "← Anterior") : null,
      next ? el("button", {
        class: "btn btn--ghost btn--sm",
        onClick: () => navegar(`biblioteca/${encodeURIComponent(next.id)}`),
        title: next.titulo,
      }, "Siguiente →") : null,
    ]);
  }

  mount(el("article", { class: "biblio biblio--entrada" }, [
    navBar(),
    el("div", { class: "biblio__entrada-cab" }, [
      el("span", { class: "biblio__entrada-unidad", text: entrada.unidad }),
      el("h2", { text: entrada.titulo }),
    ]),
    el("div", { class: "biblio__entrada-cuerpo", html: entrada.html }),
    el("div", { class: "biblio__entrada-pie muted" }, [
      el("p", { text:
        "Información con fines educativos. Verifica siempre contra guías clínicas " +
        "oficiales actualizadas antes de aplicar en contexto asistencial." }),
    ]),
    navBar(),
  ]));
}
