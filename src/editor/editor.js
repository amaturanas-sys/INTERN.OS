// Editor con trazabilidad (sección 4 + decisión 10.5).
// Edita preguntas, definiciones y casos; obliga a registrar la fuente del cambio,
// conserva el historial de versiones y permite adjuntar imágenes de apoyo.
import { el, clear, mount, toast, badge, modal, hoyISO } from "../ui/dom.js";
import { navegar } from "../ui/router.js";
import { get, put } from "../db/db.js";
import { archivoADataURL } from "../ui/imagen.js";

const STORE = { pregunta: "preguntas", definicion: "definiciones", caso: "casos_clinicos" };

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
  const imgClonada = clon(item.imagen);
  const estado = {
    imagen: imgClonada && typeof imgClonada === "object"
      ? { presente: !!imgClonada.presente, requerida: !!imgClonada.requerida, data: imgClonada.data || null, descripcion: imgClonada.descripcion || null }
      : { presente: false, requerida: false, data: null, descripcion: null }
  };

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
    bibliografiaSugeridaUI(item, fuente),
    el("label", { class: "form__row" }, [el("span", { class: "form__label", text: "Fuente *" }), fuente]),
    el("label", { class: "form__row" }, [el("span", { class: "form__label", text: "Nota" }), nota]),
  ]);

  // Snapshot del estado inicial para detectar cambios sin guardar.
  const baseline = JSON.stringify(snapshotEditable(tipo, item));
  function huboCambios() {
    // Comparamos el snapshot original con el estado actual leído del form.
    const actual = snapshotEditable(tipo, {
      ...item,
      enunciado: refs.enunciado?.value ?? item.enunciado,
      justificacion: refs.justificacion?.value ?? item.justificacion,
      concepto: refs.concepto?.value ?? item.concepto,
      pregunta: refs.pregunta?.value ?? item.pregunta,
      explicacion: refs.explicacion?.value ?? item.explicacion,
      titulo: refs.titulo?.value ?? item.titulo,
      resumen_final: refs.resumen?.value ?? item.resumen_final,
      opciones: refs._ops ? leerOpciones(refs) : item.opciones,
    });
    return JSON.stringify(actual) !== baseline ||
      fuente.value.trim() !== "" || nota.value.trim() !== "";
  }
  const cancelar = () => {
    if (huboCambios() && !confirm("Tienes cambios sin guardar. ¿Salir igualmente?")) return;
    navegar(volver(tipo));
  };

  const acciones = el("div", { class: "runner__acciones" }, [
    el("button", { class: "btn btn--primary", onClick: guardar }, "Guardar versión"),
    el("button", { class: "btn btn--ghost", onClick: cancelar }, "Cancelar"),
    item.historial_ediciones && item.historial_ediciones.length
      ? el("button", { class: "btn btn--ghost", onClick: verHistorial }, `Ver historial (${item.historial_ediciones.length})`) : null,
  ]);

  form.append(titulo, campos, bloqueRequiere(estado, tipo), bloqueMarcada(tipo, item), traza, acciones);
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

    // Validaciones por tipo — evita guardar ítems inválidos.
    if (tipo === "pregunta" || tipo === "definicion") {
      const enunciadoIn = tipo === "pregunta" ? refs.enunciado : refs.pregunta;
      const ops = leerOpciones(refs);
      if (!enunciadoIn.value.trim()) {
        toast(tipo === "pregunta" ? "Enunciado vacío." : "Pregunta vacía.", "error");
        enunciadoIn.focus(); return;
      }
      if (ops.filter((o) => (o.texto || "").trim()).length < 2) {
        toast("Se necesitan al menos 2 alternativas con texto.", "error"); return;
      }
      if (!ops.some((o) => o.correcta)) {
        toast("Marca una alternativa como correcta.", "error"); return;
      }
    }

    const pre = snapshotEditable(tipo, item);

    if (tipo === "pregunta") {
      item.enunciado = refs.enunciado.value.trim();
      item.opciones = leerOpciones(refs);
      item.justificacion = refs.justificacion.value.trim();
      // Cualquier edición reactiva una inactiva (la app la vuelve a usar
      // si ya tiene opción correcta).
      if (item.inactivo && item.opciones.some((o) => o.correcta)) {
        delete item.inactivo;
        delete item.razon_inactivo;
      }
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
      version: nuevaVersion, fecha: hoyISO(), fuente: fuente.value.trim(),
      nota: nota.value.trim() || null, snapshot: snapshotEditable(tipo, item),
    });

    try {
      await put(STORE[tipo], item);
      toast(`Guardado como versión ${nuevaVersion}.`, "ok");
      navegar(volver(tipo));
    } catch (e) {
      toast("No se pudo guardar: " + (e && e.message || "error"), "error");
    }
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
  const ops = Array.isArray(opciones) && opciones.length
    ? opciones
    : ["a", "b", "c", "d", "e"].map((l) => ({ letra: l, texto: "", correcta: false }));
  ops.forEach((op) => {
    const letra = (op.letra || "a").toLowerCase();
    const radio = el("input", { type: "radio", name: "correcta", ...(op.correcta ? { checked: "checked" } : {}) });
    const texto = el("input", { type: "text", value: op.texto || "", class: "op-texto" });
    refs._ops.push({ radio, texto, letra });
    lista.appendChild(el("div", { class: "op-edit" }, [
      radio, el("span", { class: "op-edit__letra", text: letra.toUpperCase() }), texto,
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

function bibliografiaSugeridaUI(item, fuenteInput) {
  const refs = Array.isArray(item.bibliografia_sugerida) ? item.bibliografia_sugerida : [];
  if (!refs.length) return null;
  return el("div", { class: "biblio-sug" }, [
    el("p", { class: "form__label", text: "Bibliografía sugerida (Dr. Guevara)" }),
    el("ul", { class: "biblio-sug__lista" }, refs.slice(0, 3).map((r) =>
      el("li", { class: "biblio-sug__item" }, [
        r.url
          ? el("a", { href: r.url, target: "_blank", rel: "noopener noreferrer",
              class: "biblio-sug__link", text: r.titulo || r.archivo || r.url })
          : el("span", { text: r.titulo || r.archivo || "—" }),
        el("button", {
          class: "btn btn--ghost btn--sm",
          onClick: () => {
            const txt = r.titulo
              ? `Clase Dr. Guevara — ${r.titulo}${r.url ? " (" + r.url + ")" : ""}`
              : (r.url || r.archivo || "");
            fuenteInput.value = txt;
            fuenteInput.dispatchEvent(new Event("input"));
            fuenteInput.focus();
          },
        }, "Usar esta fuente"),
      ])
    )),
  ]);
}

function bloqueMarcada(tipo, item) {
  if (tipo !== "pregunta") return null;
  const chk = el("input", { type: "checkbox", ...(item.marcada_revision ? { checked: "checked" } : {}) });
  chk.addEventListener("change", () => { item.marcada_revision = chk.checked; });
  return el("label", { class: "form__row form__check" }, [
    chk, el("span", { text: "Marcar para revisar (queda en la cola 'Preguntas marcadas')." }),
  ]);
}

function bloqueRequiere(estado, tipo) {
  if (tipo !== "pregunta") return null;
  const chk = el("input", { type: "checkbox", ...(estado.imagen.requerida ? { checked: "checked" } : {}) });
  chk.addEventListener("change", () => { estado.imagen.requerida = chk.checked; });
  return el("label", { class: "form__row form__check" }, [
    chk, el("span", { text: "Esta pregunta REQUIERE imagen para responderse (queda fuera de los quizzes hasta adjuntarla)." }),
  ]);
}
