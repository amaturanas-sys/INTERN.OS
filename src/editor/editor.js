// Editor con trazabilidad (sección 4 + decisión 10.5).
// Edita preguntas, definiciones y casos; obliga a registrar la fuente del cambio,
// conserva el historial de versiones y permite adjuntar imágenes de apoyo.
import { el, clear, mount, toast, badge, modal } from "../ui/dom.js";
import { navegar } from "../ui/router.js";
import { get, put } from "../db/db.js";
import { archivoADataURL } from "../ui/imagen.js";

const STORE = { pregunta: "preguntas", definicion: "definiciones", caso: "casos_clinicos" };
const hoy = () => new Date().toISOString().slice(0, 10);

function snapshotEditable(tipo, item) {
  if (tipo === "pregunta") {
    return { enunciado: item.enunciado, opciones: clon(item.opciones), justificacion: item.justificacion, imagen: clon(item.imagen) };
  }
  if (tipo === "definicion") {
    return { concepto: item.concepto, pregunta: item.pregunta, opciones: clon(item.opciones), explicacion: item.explicacion, imagen: clon(item.imagen) };
  }
  return { titulo: item.titulo, resumen_final: item.resumen_final, etapas: clon(item.etapas), imagen: clon(item.imagen) };
}
const clon = (x) => JSON.parse(JSON.stringify(x ?? null));

export async function abrirEditor(tipo, id) {
  const store = STORE[tipo];
  const item = await get(store, id);
  if (!item) { toast("Ítem no encontrado", "error"); navegar(""); return; }

  const form = el("div", { class: "card editor" });
  const estado = { imagen: clon(item.imagen) || { presente: false, requerida: false, data: null, descripcion: null } };

  const titulo = el("div", { class: "editor__head" }, [
    el("div", {}, [
      el("h2", { text: "Editor con trazabilidad" }),
      el("p", { class: "muted", text: `${tipo} · ${id}` }),
    ]),
    item.version_actual > 1 ? badge(`editado · v${item.version_actual}`, "badge--edit") : null,
  ]);

  const campos = el("div", { class: "form" });
  const refs = {};

  function input(label, valor, opts = {}) {
    const id2 = "f_" + Math.random().toString(36).slice(2);
    const control = opts.area
      ? el("textarea", { id: id2, rows: opts.rows || 3 }, valor || "")
      : el("input", { id: id2, type: "text", value: valor || "" });
    campos.appendChild(el("label", { class: "form__row", for: id2 }, [
      el("span", { class: "form__label", text: label }), control,
    ]));
    return control;
  }

  // ---- Campos según tipo ----
  if (tipo === "pregunta") {
    refs.enunciado = input("Enunciado", item.enunciado, { area: true, rows: 4 });
    campos.appendChild(opcionesEditor(item.opciones, refs));
    refs.justificacion = input("Justificación", item.justificacion, { area: true, rows: 4 });
  } else if (tipo === "definicion") {
    refs.concepto = input("Concepto", item.concepto);
    refs.pregunta = input("Pregunta", item.pregunta, { area: true, rows: 3 });
    campos.appendChild(opcionesEditor(item.opciones, refs));
    refs.explicacion = input("Explicación", item.explicacion, { area: true, rows: 4 });
  } else {
    refs.titulo = input("Título", item.titulo);
    refs.resumen = input("Resumen final", item.resumen_final, { area: true, rows: 4 });
    campos.appendChild(el("p", { class: "muted",
      text: "Edición de etapas: para reestructurar etapas completas, reimporta el caso vía .md." }));
  }

  // ---- Imagen de apoyo ----
  campos.appendChild(bloqueImagen(estado));

  // ---- Trazabilidad obligatoria ----
  const fuente = el("input", { type: "text", placeholder: "Ej: GES HTA 2024, UpToDate 2025 (obligatorio)" });
  const nota = el("textarea", { rows: 2, placeholder: "Motivo del cambio (opcional)" });
  const traza = el("div", { class: "form trazabilidad" }, [
    el("h3", { text: "Trazabilidad del cambio" }),
    el("label", { class: "form__row" }, [el("span", { class: "form__label", text: "Fuente *" }), fuente]),
    el("label", { class: "form__row" }, [el("span", { class: "form__label", text: "Nota" }), nota]),
  ]);

  const acciones = el("div", { class: "runner__acciones" }, [
    el("button", { class: "btn btn--primary", onClick: guardar }, "Guardar versión"),
    el("button", { class: "btn btn--ghost", onClick: () => navegar(volver(tipo)) }, "Cancelar"),
    item.historial_ediciones && item.historial_ediciones.length
      ? el("button", { class: "btn btn--ghost", onClick: verHistorial }, `Ver historial (${item.historial_ediciones.length})`) : null,
  ]);

  form.append(titulo, campos, bloqueRequiere(estado, tipo), traza, acciones);
  mount(form);

  function verHistorial() {
    const lista = el("div", { class: "historial" }, item.historial_ediciones.map((h) =>
      el("div", { class: "historial__item" }, [
        el("div", { class: "historial__cab" }, [
          badge(`v${h.version}`), el("span", { text: h.fecha }),
        ]),
        el("p", { html: `<strong>Fuente:</strong> ${h.fuente || "—"}` }),
        h.nota ? el("p", { html: `<strong>Nota:</strong> ${h.nota}` }) : null,
        h.snapshot ? el("button", { class: "btn btn--ghost btn--sm",
          onClick: () => verSnapshot(h) }, "Ver contenido de esta versión") : null,
      ])
    ));
    modal("Historial de versiones", lista, [{ label: "Cerrar", clase: "btn--primary" }]);
  }

  function verSnapshot(h) {
    const pre = el("pre", { class: "snapshot", text: JSON.stringify(h.snapshot, null, 2) });
    modal(`Versión ${h.version} — ${h.fecha}`, pre, [{ label: "Cerrar", clase: "btn--primary" }]);
  }

  async function guardar() {
    if (!fuente.value.trim()) { toast("La fuente es obligatoria para guardar.", "error"); fuente.focus(); return; }

    const pre = snapshotEditable(tipo, item);

    if (tipo === "pregunta") {
      item.enunciado = refs.enunciado.value.trim();
      item.opciones = leerOpciones(refs);
      item.justificacion = refs.justificacion.value.trim();
    } else if (tipo === "definicion") {
      item.concepto = refs.concepto.value.trim();
      item.pregunta = refs.pregunta.value.trim();
      item.opciones = leerOpciones(refs);
      item.explicacion = refs.explicacion.value.trim();
    } else {
      item.titulo = refs.titulo.value.trim();
      item.resumen_final = refs.resumen.value.trim();
    }
    item.imagen = estado.imagen;
    if (tipo === "pregunta") {
      item.tiene_imagen_referenciada = !!estado.imagen.requerida || item.tiene_imagen_referenciada;
      const faltaImagen = estado.imagen.requerida && !(estado.imagen.presente && estado.imagen.data);
      item.utilizable = !faltaImagen;
      item.estado_imagen = estado.imagen.requerida ? (faltaImagen ? "faltante" : "adjunta") : "no_aplica";
    }

    if (!Array.isArray(item.historial_ediciones)) item.historial_ediciones = [];
    const last = item.historial_ediciones[item.historial_ediciones.length - 1];
    if (last && !last.snapshot) last.snapshot = pre;
    const nuevaVersion = (item.version_actual || 1) + 1;
    item.version_actual = nuevaVersion;
    item.historial_ediciones.push({
      version: nuevaVersion, fecha: hoy(), fuente: fuente.value.trim(),
      nota: nota.value.trim() || null, snapshot: snapshotEditable(tipo, item),
    });

    await put(STORE[tipo], item);
    toast(`Guardado como versión ${nuevaVersion}.`, "ok");
    navegar(volver(tipo));
  }
}

function volver(tipo) {
  return tipo === "definicion" ? "definiciones" : tipo === "caso" ? "casos" : "quiz";
}

function opcionesEditor(opciones, refs) {
  refs._ops = [];
  const box = el("div", { class: "form__row" }, [
    el("span", { class: "form__label", text: "Alternativas (marca la correcta)" }),
  ]);
  const lista = el("div", { class: "opciones-editor" });
  opciones.forEach((op) => {
    const radio = el("input", { type: "radio", name: "correcta", ...(op.correcta ? { checked: "checked" } : {}) });
    const texto = el("input", { type: "text", value: op.texto, class: "op-texto" });
    refs._ops.push({ radio, texto, letra: op.letra });
    lista.appendChild(el("div", { class: "op-edit" }, [
      radio, el("span", { class: "op-edit__letra", text: op.letra.toUpperCase() }), texto,
    ]));
  });
  box.appendChild(lista);
  return box;
}

function leerOpciones(refs) {
  return refs._ops.map((o, idx) => ({
    letra: o.letra,
    texto: o.texto.value.trim(),
    correcta: o.radio.checked,
  }));
}

function bloqueImagen(estado) {
  const wrap = el("div", { class: "form imagen-editor" });
  const previa = el("div", { class: "imagen-editor__previa" });

  function repintarPrevia() {
    clear(previa);
    if (estado.imagen.presente && estado.imagen.data) {
      previa.append(
        el("img", { src: estado.imagen.data, alt: "previa" }),
        el("button", { class: "btn btn--ghost btn--sm", onClick: () => {
          estado.imagen.presente = false; estado.imagen.data = null; repintarPrevia();
        } }, "Quitar imagen"),
      );
    } else {
      previa.append(el("p", { class: "muted", text: "Sin imagen adjunta." }));
    }
  }

  const file = el("input", { type: "file", accept: "image/*" });
  file.addEventListener("change", async () => {
    const f = file.files[0];
    if (!f) return;
    estado.imagen.data = await archivoADataURL(f);
    estado.imagen.presente = true;
    repintarPrevia();
    toast("Imagen adjuntada.", "ok");
  });

  const desc = el("input", { type: "text", value: estado.imagen.descripcion || "", placeholder: "Descripción / texto alternativo" });
  desc.addEventListener("input", () => { estado.imagen.descripcion = desc.value; });

  wrap.append(
    el("h3", { text: "Imagen de apoyo (opcional)" }),
    previa,
    el("label", { class: "form__row" }, [el("span", { class: "form__label", text: "Adjuntar imagen" }), file]),
    el("label", { class: "form__row" }, [el("span", { class: "form__label", text: "Descripción" }), desc]),
  );
  repintarPrevia();
  return wrap;
}

function bloqueRequiere(estado, tipo) {
  if (tipo !== "pregunta") return null;
  const chk = el("input", { type: "checkbox", ...(estado.imagen.requerida ? { checked: "checked" } : {}) });
  chk.addEventListener("change", () => { estado.imagen.requerida = chk.checked; });
  return el("label", { class: "form__row form__check" }, [
    chk, el("span", { text: "Esta pregunta REQUIERE imagen para responderse (queda fuera de los quizzes hasta adjuntarla)." }),
  ]);
}
