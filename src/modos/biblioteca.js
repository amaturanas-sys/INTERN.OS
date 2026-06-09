// Biblioteca CIMIO 2026 — catálogo + edición local con imágenes y bibliografía.
//
// Modelo:
// - data/biblioteca.json: contenido base (read-only, sembrado en el repo).
// - IndexedDB store "biblioteca_ediciones" {id, html, bibliografia, imagenes,
//   fecha_edicion, fecha_actualizacion}: overrides locales por entrada.
// - IndexedDB store "biblioteca_imagenes" {id, blob, mime, titulo, descripcion,
//   fecha}: imágenes indexadas, referenciadas por <img data-img-id="X">.
//
// El render mezcla baseline + edición; el último fecha_actualizacion gana.

import { el, mount } from "../ui/dom.js";
import { navegar } from "../ui/router.js";
import { icono } from "../ui/iconos.js";
import { get, getAll, put, del } from "../db/db.js";

let _data = null;

async function cargarBase() {
  if (_data) return _data;
  const res = await fetch("data/biblioteca.json", { cache: "force-cache" });
  if (!res.ok) throw new Error("No se pudo cargar la biblioteca");
  _data = await res.json();
  return _data;
}

// Combina entrada base con su edición local (si existe).
async function resolverEntrada(id) {
  const data = await cargarBase();
  const base = data.entradas.find((e) => e.id === id);
  if (!base) return null;
  const override = await get("biblioteca_ediciones", id);
  if (!override) return { ...base, _editado: false };
  return {
    ...base,
    html: override.html ?? base.html,
    bibliografia: override.bibliografia ?? base.bibliografia ?? [],
    imagenes: override.imagenes ?? [],
    fecha_actualizacion: override.fecha_edicion || base.fecha_actualizacion,
    _editado: true,
  };
}

function norm(s) {
  return (s || "").toString().normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
}

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
      score += (texto.match(new RegExp(safe, "g")) || []).length;
    }
    return { entrada: e, score };
  }).filter((r) => r.score > 0).sort((a, b) => b.score - a.score);
}

// === Landing ===
export async function vistaBiblioteca() {
  const data = await cargarBase();
  const ediciones = await getAll("biblioteca_ediciones");
  const editadosIds = new Set(ediciones.map((e) => e.id));

  const unidadesMap = new Map();
  for (const e of data.entradas) {
    if (!unidadesMap.has(e.unidad)) unidadesMap.set(e.unidad, []);
    unidadesMap.get(e.unidad).push(e);
  }
  // Ordenar unidades según meta.unidades
  const ordenUnidades = data.meta.unidades || [...unidadesMap.keys()];

  const buscador = el("input", {
    type: "search", class: "biblio__buscador",
    placeholder: `Buscar en ${data.entradas.length} patologías…`,
    autocomplete: "off",
  });
  const resultados = el("div", { class: "biblio__resultados", hidden: true });
  const indice = el("div", { class: "biblio__indice" });

  for (const unidad of ordenUnidades) {
    const items = unidadesMap.get(unidad);
    if (!items || !items.length) continue;
    const lista = el("div", { class: "biblio__lista" },
      items.map((it) => el("button", {
        class: "biblio__item", type: "button",
        onClick: () => navegar(`biblioteca/${encodeURIComponent(it.id)}`),
      }, [
        el("span", { class: "biblio__item-titulo", text: it.titulo }),
        editadosIds.has(it.id)
          ? el("span", { class: "biblio__badge", text: "editado", title: "Tiene edición local" })
          : null,
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
        resultados.hidden = true; indice.hidden = false; resultados.innerHTML = ""; return;
      }
      const hits = buscar(data.entradas, q).slice(0, 30);
      indice.hidden = true; resultados.hidden = false; resultados.innerHTML = "";
      if (!hits.length) {
        resultados.appendChild(el("p", { class: "muted", text: `Sin coincidencias para "${q}".` }));
        return;
      }
      resultados.appendChild(el("p", { class: "muted",
        text: `${hits.length} resultado${hits.length === 1 ? "" : "s"} para "${q}"` }));
      for (const { entrada } of hits) {
        resultados.appendChild(el("button", {
          class: "biblio__item biblio__item--resultado", type: "button",
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
        `${data.entradas.length} patologías · fuente: ${data.meta.fuente || "CIMIO 2026"}` }),
      editadosIds.size > 0
        ? el("p", { class: "muted", text: `${editadosIds.size} entradas con edición local` })
        : null,
    ]),
    el("div", { class: "biblio__buscar" }, [
      icono("buscar", { tamano: 16, clase: "biblio__buscar-icono" }),
      buscador,
    ]),
    resultados,
    indice,
  ]));
}

// === Render del HTML con resolución de imágenes inyectadas (data-img-id) ===
async function renderContenido(html, imagenes) {
  const wrap = el("div", { class: "biblio__entrada-cuerpo", html });
  // Reemplazar <img data-img-id="X"> por blobs desde IndexedDB
  const imgs = wrap.querySelectorAll("img[data-img-id]");
  for (const img of imgs) {
    const imgId = img.getAttribute("data-img-id");
    const row = await get("biblioteca_imagenes", imgId);
    if (row && row.blob) {
      img.src = URL.createObjectURL(row.blob);
      if (row.titulo && !img.alt) img.alt = row.titulo;
    } else {
      img.alt = "(imagen no disponible)";
      img.style.display = "none";
    }
  }
  return wrap;
}

// === Vista de entrada individual ===
export async function vistaBibliotecaEntrada({ id }) {
  const entrada = await resolverEntrada(id);
  if (!entrada) {
    mount(el("div", { class: "card" }, [
      el("h2", { text: "Entrada no encontrada" }),
      el("p", { class: "muted", text: `No hay una patología con ID "${id}".` }),
      el("button", { class: "btn btn--primary", onClick: () => navegar("biblioteca") }, "Volver"),
    ]));
    return;
  }

  const data = await cargarBase();
  const mismaUnidad = data.entradas.filter((e) => e.unidad === entrada.unidad);
  const idx = mismaUnidad.findIndex((e) => e.id === entrada.id);
  const prev = mismaUnidad[idx - 1];
  const next = mismaUnidad[idx + 1];

  function navBar() {
    return el("div", { class: "biblio__nav" }, [
      el("button", { class: "btn btn--ghost btn--sm",
        onClick: () => navegar("biblioteca") },
        [icono("chevron_izquierda", { tamano: 14 }), "Índice"]),
      el("button", { class: "btn btn--primary btn--sm",
        onClick: () => navegar(`biblioteca/${encodeURIComponent(id)}/editar`) },
        [icono("editar", { tamano: 14 }), "Editar"]),
      prev ? el("button", { class: "btn btn--ghost btn--sm",
        onClick: () => navegar(`biblioteca/${encodeURIComponent(prev.id)}`),
        title: prev.titulo }, "← Anterior") : null,
      next ? el("button", { class: "btn btn--ghost btn--sm",
        onClick: () => navegar(`biblioteca/${encodeURIComponent(next.id)}`),
        title: next.titulo }, "Siguiente →") : null,
    ]);
  }

  const cuerpo = await renderContenido(entrada.html, entrada.imagenes);

  // Bibliografía
  const refs = Array.isArray(entrada.bibliografia) ? entrada.bibliografia : [];
  const biblio = refs.length ? el("div", { class: "biblio__refs" }, [
    el("h3", { text: "Bibliografía y referencias" }),
    el("ol", { class: "biblio__refs-lista" }, refs.map((r) =>
      el("li", { class: "biblio__ref-item" }, [
        r.url
          ? el("a", { href: r.url, target: "_blank", rel: "noopener" }, [
              el("span", { text: r.titulo || r.url }),
            ])
          : el("span", { text: r.titulo || r.cita || "(referencia sin título)" }),
        r.detalle ? el("span", { class: "muted", text: ` — ${r.detalle}` }) : null,
      ])
    )),
  ]) : null;

  const fechaTxt = entrada.fecha_actualizacion
    ? `Última actualización: ${entrada.fecha_actualizacion}${entrada._editado ? " (edición local)" : ""}`
    : "";

  mount(el("article", { class: "biblio biblio--entrada" }, [
    navBar(),
    el("div", { class: "biblio__entrada-cab" }, [
      el("span", { class: "biblio__entrada-unidad", text: entrada.unidad }),
      el("h2", { text: entrada.titulo }),
      fechaTxt ? el("p", { class: "muted biblio__fecha", text: fechaTxt }) : null,
    ]),
    cuerpo,
    biblio,
    el("div", { class: "biblio__entrada-pie muted" }, [
      el("p", { text:
        "Información con fines educativos. Verifica siempre contra guías clínicas oficiales actualizadas antes de aplicar en contexto asistencial." }),
    ]),
    navBar(),
  ]));
}

// === Editor de entrada ===
export async function vistaBibliotecaEditor({ id }) {
  const entrada = await resolverEntrada(id);
  if (!entrada) {
    mount(el("div", { class: "card" }, [
      el("h2", { text: "Entrada no encontrada" }),
      el("button", { class: "btn btn--primary", onClick: () => navegar("biblioteca") }, "Volver"),
    ]));
    return;
  }

  // Estado editable
  let htmlActual = entrada.html;
  let refsActual = JSON.parse(JSON.stringify(entrada.bibliografia || []));
  let imgsActual = JSON.parse(JSON.stringify(entrada.imagenes || []));

  // -- HTML editor (textarea simple) --
  const textarea = el("textarea", {
    class: "biblio__editor-html", rows: 24, spellcheck: "true",
  });
  textarea.value = htmlActual;
  textarea.addEventListener("input", () => { htmlActual = textarea.value; });

  // -- Bibliografía --
  const refsLista = el("div", { class: "biblio__refs-editor" });
  function renderRefs() {
    refsLista.innerHTML = "";
    refsActual.forEach((r, i) => {
      const row = el("div", { class: "biblio__ref-row" }, [
        el("input", { type: "text", placeholder: "Título o cita", value: r.titulo || "",
          onInput: (e) => refsActual[i].titulo = e.target.value }),
        el("input", { type: "url", placeholder: "URL (opcional)", value: r.url || "",
          onInput: (e) => refsActual[i].url = e.target.value }),
        el("input", { type: "text", placeholder: "Detalle (autor, año, etc.)", value: r.detalle || "",
          onInput: (e) => refsActual[i].detalle = e.target.value }),
        el("button", { class: "btn btn--ghost btn--sm", type: "button",
          onClick: () => { refsActual.splice(i, 1); renderRefs(); } }, "✕"),
      ]);
      refsLista.appendChild(row);
    });
    if (!refsActual.length) {
      refsLista.appendChild(el("p", { class: "muted", text: "(Sin referencias todavía)" }));
    }
  }
  renderRefs();

  const btnAgregarRef = el("button", {
    class: "btn btn--ghost btn--sm", type: "button",
    onClick: () => { refsActual.push({ titulo: "", url: "", detalle: "" }); renderRefs(); },
  }, "+ Añadir referencia");

  // -- Imágenes --
  const imgsLista = el("div", { class: "biblio__imgs-editor" });

  async function renderImgs() {
    imgsLista.innerHTML = "";
    if (!imgsActual.length) {
      imgsLista.appendChild(el("p", { class: "muted",
        text: "(Sin imágenes indexadas todavía. Sube una abajo.)" }));
      return;
    }
    for (let i = 0; i < imgsActual.length; i++) {
      const ref = imgsActual[i];
      const row = await get("biblioteca_imagenes", ref.id);
      const previa = row && row.blob ? URL.createObjectURL(row.blob) : null;
      const card = el("div", { class: "biblio__img-row" }, [
        previa ? el("img", { src: previa, class: "biblio__img-thumb", alt: ref.titulo || "" }) : null,
        el("div", { class: "biblio__img-meta" }, [
          el("input", { type: "text", placeholder: "Título / leyenda", value: ref.titulo || "",
            onInput: (e) => imgsActual[i].titulo = e.target.value }),
          el("p", { class: "muted biblio__img-id-tag",
            text: `Insertar en HTML: <img data-img-id="${ref.id}" alt="...">` }),
          el("button", { class: "btn btn--ghost btn--sm", type: "button",
            onClick: () => {
              const tag = `<img data-img-id="${ref.id}" alt="${(ref.titulo || "").replace(/"/g, "")}" />`;
              const pos = textarea.selectionStart || textarea.value.length;
              textarea.value = textarea.value.slice(0, pos) + "\n" + tag + "\n" + textarea.value.slice(pos);
              htmlActual = textarea.value;
            } }, "Insertar en cuerpo"),
        ]),
        el("button", { class: "btn btn--ghost btn--sm", type: "button",
          onClick: async () => {
            await del("biblioteca_imagenes", ref.id);
            imgsActual.splice(i, 1);
            renderImgs();
          } }, "Eliminar"),
      ]);
      imgsLista.appendChild(card);
    }
  }
  renderImgs();

  const fileInput = el("input", { type: "file", accept: "image/*", multiple: false, hidden: true });
  fileInput.addEventListener("change", async (ev) => {
    const file = ev.target.files[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) {
      alert("La imagen excede 5 MB. Comprímela antes de subir.");
      return;
    }
    const imgId = `img_${id}_${Date.now()}`;
    await put("biblioteca_imagenes", {
      id: imgId, blob: file, mime: file.type,
      titulo: "", descripcion: "",
      fecha: new Date().toISOString().slice(0, 10),
    });
    imgsActual.push({ id: imgId, titulo: file.name.replace(/\.[^.]+$/, "") });
    renderImgs();
    fileInput.value = "";
  });
  const btnSubir = el("button", {
    class: "btn btn--ghost btn--sm", type: "button",
    onClick: () => fileInput.click(),
  }, [icono("importar", { tamano: 14 }), "Subir imagen"]);

  // -- Guardar / Restaurar baseline --
  async function guardar() {
    const hoy = new Date().toISOString().slice(0, 10);
    await put("biblioteca_ediciones", {
      id, html: htmlActual,
      bibliografia: refsActual.filter((r) => r.titulo || r.url),
      imagenes: imgsActual,
      fecha_edicion: hoy,
    });
    navegar(`biblioteca/${encodeURIComponent(id)}`);
  }

  async function restaurar() {
    if (!confirm("¿Restaurar al contenido original? Tu edición local se perderá. Las imágenes seguirán almacenadas pero ya no estarán vinculadas a esta entrada.")) return;
    await del("biblioteca_ediciones", id);
    navegar(`biblioteca/${encodeURIComponent(id)}`);
  }

  mount(el("div", { class: "biblio biblio--editor" }, [
    el("div", { class: "biblio__nav" }, [
      el("button", { class: "btn btn--ghost btn--sm",
        onClick: () => navegar(`biblioteca/${encodeURIComponent(id)}`) },
        [icono("chevron_izquierda", { tamano: 14 }), "Cancelar"]),
      el("button", { class: "btn btn--primary btn--sm",
        onClick: guardar }, [icono("check", { tamano: 14 }), "Guardar cambios"]),
      entrada._editado
        ? el("button", { class: "btn btn--ghost btn--sm",
            onClick: restaurar }, "Restaurar original")
        : null,
    ]),
    el("div", { class: "biblio__entrada-cab" }, [
      el("span", { class: "biblio__entrada-unidad", text: entrada.unidad }),
      el("h2", { text: `Editando: ${entrada.titulo}` }),
      el("p", { class: "muted biblio__fecha",
        text: `Última actualización: ${entrada.fecha_actualizacion}${entrada._editado ? " (edición local)" : " (versión original)"}` }),
    ]),
    el("section", { class: "biblio__editor-sec" }, [
      el("h3", { text: "Contenido (HTML)" }),
      el("p", { class: "muted", text:
        "Puedes usar etiquetas HTML estándar: <h3>, <p>, <ul>/<li>, <strong>, <em>, <table>, <span class=\"highlight\">…</span>. " +
        "Las imágenes se insertan con <img data-img-id=\"...\">." }),
      textarea,
    ]),
    el("section", { class: "biblio__editor-sec" }, [
      el("h3", { text: "Imágenes indexadas" }),
      el("p", { class: "muted",
        text: "Las imágenes se guardan localmente en tu dispositivo. Usa el botón \"Insertar en cuerpo\" para colocarlas en el texto." }),
      imgsLista, btnSubir, fileInput,
    ]),
    el("section", { class: "biblio__editor-sec" }, [
      el("h3", { text: "Bibliografía y referencias" }),
      refsLista, btnAgregarRef,
    ]),
    el("p", { class: "muted",
      text: "Las ediciones se guardan localmente en este dispositivo. Puedes exportarlas desde Ajustes (futuro)." }),
  ]));
}
