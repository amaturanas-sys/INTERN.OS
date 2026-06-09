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
//
// Endurecimiento (v1.7.2):
// - Todo HTML que se inyecta vía innerHTML pasa por sanitizarHTML().
// - Blob URLs se trackean por vista y se liberan en el evento "vista:cambia".
// - El buscador no parsea HTML (strip por regex + memoiza texto plano).

import { el, mount } from "../ui/dom.js";
import { navegar } from "../ui/router.js";
import { icono } from "../ui/iconos.js";
import { get, getAll, put, del } from "../db/db.js";

let _data = null;

// ===========================================================
// Sanitizador HTML (allow-list de tags y atributos)
// ===========================================================
const TAGS_PERMITIDOS = new Set([
  "p", "br", "hr", "div", "span", "section",
  "h2", "h3", "h4", "h5", "h6",
  "ul", "ol", "li", "dl", "dt", "dd",
  "strong", "b", "em", "i", "u", "s", "code", "pre", "kbd",
  "a", "img",
  "table", "thead", "tbody", "tr", "td", "th", "caption",
  "blockquote", "sup", "sub",
]);
const ATTRS_PERMITIDOS_GLOBAL = new Set(["class", "title", "lang", "dir"]);
const ATTRS_POR_TAG = {
  a: new Set(["href", "target", "rel"]),
  img: new Set(["src", "alt", "data-img-id", "width", "height"]),
  td: new Set(["colspan", "rowspan"]),
  th: new Set(["colspan", "rowspan", "scope"]),
};
const CLASES_PERMITIDAS = new Set([
  "section-subsection", "highlight", "image-caption", "medical-image",
]);

function escapeAttr(v) {
  return String(v).replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}
function urlSegura(url) {
  if (typeof url !== "string") return null;
  const trim = url.trim();
  if (!trim) return null;
  // Protocolos permitidos
  if (/^(https?:|mailto:|tel:|#|\/|\.|data:image\/(png|jpe?g|gif|webp);base64,)/i.test(trim)) {
    return trim;
  }
  return null;
}

// Sanitiza un HTML arbitrario. Usa el DOMParser del navegador para tokenizar
// y reconstruye sólo lo que está en la allow-list. Evita XSS sin librerías.
export function sanitizarHTML(htmlSucio) {
  if (typeof htmlSucio !== "string" || !htmlSucio) return "";
  const doc = new DOMParser().parseFromString(`<div>${htmlSucio}</div>`, "text/html");
  const raiz = doc.body.firstChild;
  if (!raiz) return "";
  return Array.from(raiz.childNodes).map(serializarNodo).join("");
}

function serializarNodo(node) {
  if (node.nodeType === 3) {
    // Texto: escapar
    return escapeAttr(node.nodeValue);
  }
  if (node.nodeType !== 1) return "";
  const tag = node.tagName.toLowerCase();
  if (!TAGS_PERMITIDOS.has(tag)) {
    // tag no permitido: descartar tag pero conservar contenido (excepto script/style)
    if (tag === "script" || tag === "style" || tag === "iframe" || tag === "object" || tag === "embed") {
      return "";
    }
    return Array.from(node.childNodes).map(serializarNodo).join("");
  }
  // Atributos permitidos
  const attrs = [];
  for (const attr of Array.from(node.attributes)) {
    const name = attr.name.toLowerCase();
    if (name.startsWith("on")) continue; // bloquear handlers
    if (name === "style") continue;       // bloquear estilos inline
    const tagAttrs = ATTRS_POR_TAG[tag];
    if (!ATTRS_PERMITIDOS_GLOBAL.has(name) && !(tagAttrs && tagAttrs.has(name))) continue;
    let val = attr.value;
    if (name === "href" || name === "src") {
      val = urlSegura(val);
      if (val == null) continue;
    }
    if (name === "class") {
      // Filtrar clases por allow-list
      const clases = val.split(/\s+/).filter((c) => CLASES_PERMITIDAS.has(c));
      if (!clases.length) continue;
      val = clases.join(" ");
    }
    attrs.push(`${name}="${escapeAttr(val)}"`);
  }
  // Tags void
  const VOID = new Set(["br", "hr", "img"]);
  const attrStr = attrs.length ? " " + attrs.join(" ") : "";
  if (VOID.has(tag)) return `<${tag}${attrStr}>`;
  const inner = Array.from(node.childNodes).map(serializarNodo).join("");
  return `<${tag}${attrStr}>${inner}</${tag}>`;
}

// ===========================================================
// Carga de datos
// ===========================================================
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
  // U+0300-U+036F = combining diacritical marks
  return (s || "").toString().normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
}

// Cache de texto plano por entrada (memoizado en módulo).
// Se invalida en guardar()/restaurar() para evitar resultados de búsqueda obsoletos.
const _textoPlanoCache = new Map();
function textoPlanoEntrada(e) {
  // Si la entrada fue editada localmente, el html del baseline puede estar
  // desactualizado; clavemos en cache por (id + length) para detectar cambios.
  const cacheKey = `${e.id}:${(e.html || "").length}`;
  if (_textoPlanoCache.has(cacheKey)) return _textoPlanoCache.get(cacheKey);
  const t = norm((e.html || "").replace(/<[^>]+>/g, " "));
  _textoPlanoCache.set(cacheKey, t);
  return t;
}
function invalidarCacheTexto(id) {
  // Borrar todas las entradas del cache cuya key empiece con "id:"
  for (const k of _textoPlanoCache.keys()) {
    if (k.startsWith(id + ":")) _textoPlanoCache.delete(k);
  }
}

function buscar(entradas, query) {
  const q = norm(query.trim());
  if (!q) return [];
  const tokens = q.split(/\s+/).filter(Boolean);
  return entradas.map((e) => {
    const texto = textoPlanoEntrada(e);
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

// ===========================================================
// Gestión de blob URLs por vista (anti-leak)
// ===========================================================
let _blobUrlsVista = [];
function trackBlobURL(blob) {
  const url = URL.createObjectURL(blob);
  _blobUrlsVista.push(url);
  return url;
}
function liberarBlobsVista() {
  for (const u of _blobUrlsVista) URL.revokeObjectURL(u);
  _blobUrlsVista = [];
}
// Cuando la vista cambia, liberar todas las URLs
document.addEventListener("vista:cambia", liberarBlobsVista);

// ===========================================================
// Landing
// ===========================================================
export async function vistaBiblioteca() {
  const data = await cargarBase();
  const ediciones = await getAll("biblioteca_ediciones");
  const editadosIds = new Set(ediciones.map((e) => e.id));

  const unidadesMap = new Map();
  for (const e of data.entradas) {
    if (!unidadesMap.has(e.unidad)) unidadesMap.set(e.unidad, []);
    unidadesMap.get(e.unidad).push(e);
  }
  const ordenUnidades = (data.meta && data.meta.unidades) || [...unidadesMap.keys()];

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
        it.placeholder
          ? el("span", { class: "biblio__badge biblio__badge--wip",
              text: "WIP", title: "Contenido placeholder — pendiente de redacción" })
          : null,
        editadosIds.has(it.id)
          ? el("span", { class: "biblio__badge", text: "editado",
              title: "Tiene edición local" })
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

  // Conteos para el header
  const totalReal = data.entradas.filter((e) => !e.placeholder).length;
  const totalPlaceholder = data.entradas.length - totalReal;

  mount(el("div", { class: "biblio" }, [
    el("div", { class: "biblio__cab" }, [
      el("h2", { text: "Biblioteca" }),
      el("p", { class: "muted", text:
        `${data.entradas.length} patologías · ${totalReal} con contenido redactado` +
        (totalPlaceholder ? ` · ${totalPlaceholder} en preparación (WIP)` : "") }),
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

// ===========================================================
// Render del HTML con imágenes inyectadas (data-img-id)
// ===========================================================
async function renderContenido(html) {
  const safe = sanitizarHTML(html);
  const wrap = el("div", { class: "biblio__entrada-cuerpo", html: safe });
  // Resolver <img data-img-id="X"> en paralelo
  const imgs = Array.from(wrap.querySelectorAll("img[data-img-id]"));
  await Promise.all(imgs.map(async (img) => {
    const imgId = img.getAttribute("data-img-id");
    const row = await get("biblioteca_imagenes", imgId);
    if (row && row.blob) {
      img.src = trackBlobURL(row.blob);
      if (row.titulo && !img.alt) img.alt = row.titulo;
    } else {
      img.alt = "(imagen no disponible)";
      img.style.display = "none";
    }
  }));
  return wrap;
}

// ===========================================================
// Vista de entrada individual
// ===========================================================
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

  const cuerpo = await renderContenido(entrada.html);

  // Bibliografía
  const refs = Array.isArray(entrada.bibliografia) ? entrada.bibliografia : [];
  const biblio = refs.length ? el("div", { class: "biblio__refs" }, [
    el("h3", { text: "Bibliografía y referencias" }),
    el("ol", { class: "biblio__refs-lista" }, refs.map((r) =>
      el("li", { class: "biblio__ref-item" }, [
        r.url
          ? el("a", { href: urlSegura(r.url) || "#",
              target: "_blank", rel: "noopener noreferrer" },
              [el("span", { text: r.titulo || r.url })])
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
      entrada.placeholder
        ? el("span", { class: "biblio__badge biblio__badge--wip",
            text: "Contenido WIP", title: "Pendiente de redacción" })
        : null,
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

// ===========================================================
// Editor de entrada (WYSIWYG + HTML crudo)
// ===========================================================
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
  let modoHtml = false;

  // Tracking de imágenes subidas EN ESTA SESIÓN (para GC al cancelar)
  const imgsSubidasSesion = new Set();
  // Tracking de imágenes preexistentes (para no borrar accidentalmente)
  const imgsPreexistentes = new Set(imgsActual.map((i) => i.id));

  // Lock para serializar uploads concurrentes
  let uploadLock = Promise.resolve();

  // -- Editor WYSIWYG --
  const wysiwyg = el("div", {
    class: "biblio__wysiwyg",
    contenteditable: "true", spellcheck: "true",
  });
  wysiwyg.innerHTML = sanitizarHTML(htmlActual);
  wysiwyg.addEventListener("input", () => { htmlActual = wysiwyg.innerHTML; });
  // Bloquear pegado enriquecido sin sanitizar
  wysiwyg.addEventListener("paste", (e) => {
    e.preventDefault();
    const html = (e.clipboardData || window.clipboardData).getData("text/html");
    const txt = (e.clipboardData || window.clipboardData).getData("text/plain");
    if (html) {
      const safe = sanitizarHTML(html);
      document.execCommand("insertHTML", false, safe);
    } else if (txt) {
      document.execCommand("insertText", false, txt);
    }
    htmlActual = wysiwyg.innerHTML;
  });

  // Resolver imágenes en el WYSIWYG con tracking de blob URLs
  async function resolverImagenesEnEditor() {
    const imgs = Array.from(wysiwyg.querySelectorAll('img[data-img-id]'));
    await Promise.all(imgs.map(async (img) => {
      // Revocar URL previa si existía
      if (img.src && img.src.startsWith("blob:")) URL.revokeObjectURL(img.src);
      const row = await get("biblioteca_imagenes", img.getAttribute("data-img-id"));
      if (row && row.blob) img.src = trackBlobURL(row.blob);
    }));
  }
  resolverImagenesEnEditor();

  // -- Textarea (HTML crudo) --
  const textarea = el("textarea", {
    class: "biblio__editor-html", rows: 22, spellcheck: "true",
  });
  textarea.value = htmlActual;
  textarea.addEventListener("input", () => { htmlActual = textarea.value; });

  // -- Toolbar --
  function exec(cmd, val) {
    wysiwyg.focus();
    document.execCommand(cmd, false, val);
    htmlActual = wysiwyg.innerHTML;
  }
  function wrapHighlight() {
    wysiwyg.focus();
    const sel = window.getSelection();
    if (!sel.rangeCount || sel.isCollapsed) return;
    const range = sel.getRangeAt(0);
    const span = document.createElement("span");
    span.className = "highlight";
    span.appendChild(range.extractContents());
    range.insertNode(span);
    sel.removeAllRanges();
    htmlActual = wysiwyg.innerHTML;
  }
  function insertarEnlace() {
    const url = prompt("URL del enlace (https://… o mailto:…):");
    if (!url) return;
    if (!urlSegura(url)) {
      alert("URL no permitida (solo http/https/mailto/tel/relativas).");
      return;
    }
    exec("createLink", url);
  }
  function insertarTabla() {
    let filas = parseInt(prompt("Filas (incluyendo cabecera, máx 50):", "3"), 10);
    let cols = parseInt(prompt("Columnas (máx 20):", "3"), 10);
    if (!filas || !cols) return;
    filas = Math.max(1, Math.min(50, filas));
    cols = Math.max(1, Math.min(20, cols));
    let html = "<table><thead><tr>";
    for (let c = 0; c < cols; c++) html += "<th>—</th>";
    html += "</tr></thead><tbody>";
    for (let r = 1; r < filas; r++) {
      html += "<tr>";
      for (let c = 0; c < cols; c++) html += "<td>—</td>";
      html += "</tr>";
    }
    html += "</tbody></table><p></p>";
    exec("insertHTML", html);
  }
  function toolBtn(label, cmd, title, val) {
    return el("button", {
      class: "biblio__toolbar-btn", type: "button", title,
      onClick: () => exec(cmd, val),
    }, label);
  }
  function toolBtnCustom(label, fn, title) {
    return el("button", {
      class: "biblio__toolbar-btn", type: "button", title, onClick: fn,
    }, label);
  }
  const toolbar = el("div", { class: "biblio__toolbar" }, [
    toolBtn("B",       "bold",                 "Negrita"),
    toolBtn("I",       "italic",               "Cursiva"),
    toolBtn("H3",      "formatBlock",          "Encabezado",       "h3"),
    toolBtn("P",       "formatBlock",          "Párrafo",          "p"),
    toolBtn("• Lista", "insertUnorderedList",  "Lista con viñetas"),
    toolBtn("1. Lista","insertOrderedList",    "Lista numerada"),
    toolBtnCustom("Resaltado", wrapHighlight,  "Resaltar selección"),
    toolBtnCustom("Enlace",    insertarEnlace, "Insertar enlace"),
    toolBtnCustom("Tabla",     insertarTabla,  "Insertar tabla"),
    toolBtn("⤺", "undo", "Deshacer"),
    toolBtn("⤻", "redo", "Rehacer"),
  ]);

  // -- Toggle WYSIWYG ↔ HTML --
  const editorMount = el("div", { class: "biblio__editor-mount" });
  function renderEditor() {
    editorMount.innerHTML = "";
    if (modoHtml) {
      textarea.value = htmlActual;
      editorMount.appendChild(textarea);
    } else {
      editorMount.appendChild(toolbar);
      // Revocar URLs previas del wysiwyg antes de re-renderizar
      for (const img of wysiwyg.querySelectorAll('img[src^="blob:"]')) {
        URL.revokeObjectURL(img.src);
      }
      wysiwyg.innerHTML = sanitizarHTML(htmlActual);
      editorMount.appendChild(wysiwyg);
      resolverImagenesEnEditor();
    }
  }
  const btnToggleModo = el("button", {
    class: "btn btn--ghost btn--sm", type: "button",
    title: "Alternar entre editor visual y HTML crudo",
    onClick: () => {
      if (modoHtml) {
        // HTML → WYSIWYG: capturar último valor del textarea
        htmlActual = textarea.value;
        modoHtml = false;
        btnToggleModo.textContent = "Ver HTML";
      } else {
        // WYSIWYG → HTML: capturar innerHTML actual
        htmlActual = wysiwyg.innerHTML;
        modoHtml = true;
        btnToggleModo.textContent = "Vista visual";
      }
      renderEditor();
    },
  }, "Ver HTML");

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
  const storageTag = el("span", { class: "biblio__storage-tag" });

  async function actualizarTag() {
    const todas = await getAll("biblioteca_imagenes").catch(() => []);
    const bytesTot = todas.reduce((s, r) => s + ((r.blob && r.blob.size) || 0), 0);
    const mb = bytesTot / 1048576;
    let mbCuota = null;
    if (navigator.storage && navigator.storage.estimate) {
      try {
        const est = await navigator.storage.estimate();
        mbCuota = est.quota ? (est.quota / 1048576) : null;
      } catch (_) { /* nada */ }
    }
    storageTag.textContent = mbCuota
      ? `Imágenes locales: ${todas.length} · ${mb.toFixed(1)} MB (de ~${Math.round(mbCuota)} MB de cuota)`
      : `Imágenes locales: ${todas.length} · ${mb.toFixed(1)} MB`;
  }
  actualizarTag();

  async function renderImgs() {
    // Revocar miniaturas previas antes de re-render
    for (const img of imgsLista.querySelectorAll('img[src^="blob:"]')) {
      URL.revokeObjectURL(img.src);
    }
    imgsLista.innerHTML = "";
    if (!imgsActual.length) {
      imgsLista.appendChild(el("p", { class: "muted",
        text: "(Sin imágenes indexadas todavía. Sube una abajo.)" }));
      actualizarTag();
      return;
    }
    await Promise.all(imgsActual.map(async (ref, i) => {
      const row = await get("biblioteca_imagenes", ref.id);
      const previa = row && row.blob ? trackBlobURL(row.blob) : null;
      const card = el("div", { class: "biblio__img-row" }, [
        previa ? el("img", { src: previa, class: "biblio__img-thumb", alt: ref.titulo || "" }) : null,
        el("div", { class: "biblio__img-meta" }, [
          el("input", { type: "text", placeholder: "Título / leyenda", value: ref.titulo || "",
            onInput: (e) => imgsActual[i].titulo = e.target.value }),
          el("p", { class: "muted biblio__img-id-tag",
            text: `Insertar en HTML: <img data-img-id="${ref.id}" alt="...">` }),
          el("button", { class: "btn btn--ghost btn--sm", type: "button",
            onClick: () => {
              const altLimpio = escapeAttr(ref.titulo || "");
              const tag = `<img data-img-id="${ref.id}" alt="${altLimpio}" />`;
              if (modoHtml) {
                const pos = textarea.selectionStart || textarea.value.length;
                textarea.value = textarea.value.slice(0, pos) + "\n" + tag + "\n" + textarea.value.slice(pos);
                htmlActual = textarea.value;
              } else {
                wysiwyg.focus();
                document.execCommand("insertHTML", false, tag);
                htmlActual = wysiwyg.innerHTML;
                resolverImagenesEnEditor();
              }
            } }, "Insertar en cuerpo"),
        ]),
        el("button", { class: "btn btn--ghost btn--sm", type: "button",
          onClick: async () => {
            // Eliminar también los <img> que la referencian
            // En WYSIWYG
            const refId = ref.id;
            wysiwyg.querySelectorAll(`img[data-img-id="${refId}"]`).forEach((n) => n.remove());
            // En textarea: regex
            textarea.value = textarea.value.replace(
              new RegExp(`<img[^>]*data-img-id=["']${refId.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}["'][^>]*/?>`, "g"),
              ""
            );
            htmlActual = modoHtml ? textarea.value : wysiwyg.innerHTML;
            await del("biblioteca_imagenes", refId);
            imgsActual.splice(i, 1);
            renderImgs();
          } }, "Eliminar"),
      ]);
      imgsLista.appendChild(card);
    }));
    actualizarTag();
  }
  renderImgs();

  const fileInput = el("input", { type: "file", accept: "image/*", hidden: true });
  fileInput.addEventListener("change", (ev) => {
    const file = ev.target.files[0];
    if (!file) return;
    fileInput.value = "";  // reset inmediato para permitir mismo archivo otra vez
    // Encolar en el lock para serializar
    uploadLock = uploadLock.then(async () => {
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
      imgsSubidasSesion.add(imgId);
      imgsActual.push({ id: imgId, titulo: file.name.replace(/\.[^.]+$/, "") });
      await renderImgs();
    }).catch((e) => { console.error("[biblioteca] upload:", e); });
  });
  const btnSubir = el("button", {
    class: "btn btn--ghost btn--sm", type: "button",
    onClick: () => fileInput.click(),
  }, [icono("importar", { tamano: 14 }), "Subir imagen"]);

  // -- Guardar / Cancelar / Restaurar baseline --
  async function guardar() {
    // Asegurar que htmlActual refleje el modo activo
    htmlActual = modoHtml ? textarea.value : wysiwyg.innerHTML;
    // Sanitizar antes de persistir (defensa en profundidad)
    const htmlLimpio = sanitizarHTML(htmlActual);
    const hoy = new Date().toISOString().slice(0, 10);
    await put("biblioteca_ediciones", {
      id, html: htmlLimpio,
      bibliografia: refsActual.filter((r) => r.titulo || r.url),
      imagenes: imgsActual,
      fecha_edicion: hoy,
    });
    // Invalida la cache de texto plano para que la próxima búsqueda
    // refleje el contenido editado.
    invalidarCacheTexto(id);
    navegar(`biblioteca/${encodeURIComponent(id)}`);
  }

  async function cancelar() {
    // GC: borrar imágenes subidas en esta sesión que NO existían antes y NO se guardaron
    const idsActuales = new Set(imgsActual.map((i) => i.id));
    for (const subidaId of imgsSubidasSesion) {
      if (!imgsPreexistentes.has(subidaId)) {
        // Era nueva en esta sesión. Si está en imgsActual la guardaría; pero como cancelamos, borrar siempre.
        try { await del("biblioteca_imagenes", subidaId); } catch (_) { /* ignorar */ }
      }
    }
    navegar(`biblioteca/${encodeURIComponent(id)}`);
  }

  async function restaurar() {
    if (!confirm("¿Restaurar al contenido original? Tu edición local se perderá.")) return;
    await del("biblioteca_ediciones", id);
    invalidarCacheTexto(id);
    navegar(`biblioteca/${encodeURIComponent(id)}`);
  }

  renderEditor();

  mount(el("div", { class: "biblio biblio--editor" }, [
    el("div", { class: "biblio__nav" }, [
      el("button", { class: "btn btn--ghost btn--sm",
        onClick: cancelar },
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
      el("div", { class: "biblio__editor-cab" }, [
        el("h3", { text: "Contenido" }),
        btnToggleModo,
      ]),
      el("p", { class: "muted", text:
        "Usa la barra para formatear (B, I, encabezado H3, listas, resaltado, enlace, tabla). " +
        "Para insertar imágenes, súbelas más abajo y pincha \"Insertar en cuerpo\". " +
        "Con \"Ver HTML\" puedes editar el código directamente si necesitas un control fino." }),
      editorMount,
    ]),
    el("section", { class: "biblio__editor-sec" }, [
      el("div", { class: "biblio__editor-cab" }, [
        el("h3", { text: "Imágenes indexadas" }),
        storageTag,
      ]),
      el("p", { class: "muted",
        text: "Las imágenes se guardan localmente en tu dispositivo. Tamaño máximo por imagen: 5 MB. Si cancelas la edición, las imágenes recién subidas se descartan." }),
      imgsLista, btnSubir, fileInput,
    ]),
    el("section", { class: "biblio__editor-sec" }, [
      el("h3", { text: "Bibliografía y referencias" }),
      refsLista, btnAgregarRef,
    ]),
    el("p", { class: "muted",
      text: "Las ediciones se guardan localmente en este dispositivo. Puedes exportarlas e importarlas desde Ajustes." }),
  ]));
}
