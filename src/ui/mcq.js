// Runner genérico de sesiones MCQ. Lo usan el Modo 1 (quiz) y el Modo 3 (definiciones).
import { el, clear, mount, badge, toast } from "./dom.js";
import { vistaImagen } from "./imagen.js";
import { navegar } from "./router.js";

async function marcarParaRevisar(item, btn) {
  try {
    const { put } = await import("../db/db.js");
    if (!item._raw) return;
    item._raw.marcada_revision = !item._raw.marcada_revision;
    item.onMarcarStore = item.onMarcarStore || "preguntas";
    await put(item.onMarcarStore, item._raw);
    toast(item._raw.marcada_revision ? "Marcada para revisar." : "Desmarcada.", "ok");
    if (btn) btn.textContent = item._raw.marcada_revision ? "🚩 Marcada (deshacer)" : "🚩 Marcar para revisar";
  } catch (e) {
    toast("No se pudo marcar: " + e.message, "error");
  }
}

// items: [{ id, tipo, enunciado, opciones:[{letra,texto,correcta}], explicacion, imagen,
//           subtitulo, onEdit }]
// hooks: onAnswer(item, correcta), onFinish(resultado)
export function runMcq({ items, titulo, subtitulo, onAnswer, onFinish }) {
  if (!items || !items.length) {
    mount(el("div", { class: "card" }, [
      el("h2", { text: titulo }),
      el("p", { class: "muted", text: "No hay ítems disponibles con estos criterios." }),
      el("button", { class: "btn btn--primary", onClick: () => navegar("") }, "Volver al inicio"),
    ]));
    return;
  }

  let i = 0;
  let aciertos = 0;
  let terminada = false;
  const respuestas = [];
  const cont = el("div", { class: "card runner" });
  // Estado del ítem actual visible al handler de teclado.
  let opcionesBtns = [];
  let respondida = false;
  let onSiguiente = null;

  function pintar() {
    const item = items[i];
    clear(cont);
    respondida = false;
    onSiguiente = null;

    // Guard: ítem sin opciones (datos rotos) — saltar mostrando aviso.
    if (!item || !Array.isArray(item.opciones) || item.opciones.length === 0) {
      cont.append(
        el("h2", { text: titulo }),
        el("p", { class: "muted", text: `Ítem ${i + 1} sin opciones, se omite.` }),
        el("div", { class: "runner__acciones" }, [
          el("button", { class: "btn btn--primary",
            onClick: () => { if (i >= items.length - 1) finalizar(); else { i++; pintar(); } } },
            "Siguiente →"),
        ]),
      );
      return;
    }

    const cabecera = el("div", { class: "runner__head" }, [
      el("div", {}, [
        el("h2", { text: titulo }),
        subtitulo ? el("p", { class: "muted", text: subtitulo }) : null,
      ]),
      el("div", { class: "runner__progress" }, [
        el("span", { text: `${i + 1} / ${items.length}` }),
        el("span", { class: "muted", text: `Aciertos: ${aciertos}` }),
      ]),
    ]);

    const barra = el("div", { class: "progress" }, [
      el("div", { class: "progress__fill", style: `width:${(i / items.length) * 100}%` }),
    ]);

    const editado = item.editado
      ? badge(`editado · v${item.version}`, "badge--edit") : null;

    const enunciado = el("div", { class: "enunciado" }, [
      item.subtitulo ? el("div", { class: "chips" }, item.subtitulo.map((c) => badge(c))) : null,
      el("p", { class: "enunciado__texto", text: item.enunciado }),
      editado,
      vistaImagen(item.imagen),
    ]);

    const feedback = el("div", { class: "feedback" });
    const opcionesBox = el("div", { class: "opciones" });
    opcionesBtns = [];

    item.opciones.forEach((op, idx) => {
      const btn = el("button", { class: "opcion" }, [
        el("span", { class: "opcion__letra", text: (op.letra || "").toUpperCase() }),
        el("span", { class: "opcion__texto", text: op.texto || "" }),
      ]);
      btn.addEventListener("click", () => responder(op, btn, idx));
      opcionesBox.appendChild(btn);
      opcionesBtns.push(btn);
    });

    function responder(op, btn, idx) {
      if (respondida) return;
      respondida = true;
      const correcta = !!op.correcta;
      if (correcta) aciertos++;
      respuestas.push({ id: item.id, correcta });

      Array.from(opcionesBox.children).forEach((b, k) => {
        b.classList.add("opcion--bloqueada");
        if (item.opciones[k] && item.opciones[k].correcta) b.classList.add("opcion--correcta");
      });
      if (!correcta) btn.classList.add("opcion--incorrecta");

      feedback.className = `feedback feedback--visible feedback--${correcta ? "ok" : "mal"}`;
      clear(feedback);
      feedback.appendChild(el("p", { class: "feedback__titulo",
        text: correcta ? "✔ Correcto" : "✗ Incorrecto" }));
      if (op.feedback) feedback.appendChild(el("p", { text: op.feedback }));
      if (item.explicacion) {
        feedback.appendChild(el("p", { class: "feedback__exp", text: item.explicacion }));
      }
      if (Array.isArray(item.bibliografia) && item.bibliografia.length) {
        const refsBox = el("div", { class: "feedback__refs" }, [
          el("p", { class: "feedback__refs-titulo", text: "Clases relacionadas" }),
        ]);
        item.bibliografia.slice(0, 3).forEach((r) => {
          if (!r.url) return;
          const a = el("a", {
            href: r.url, target: "_blank", rel: "noopener noreferrer", class: "feedback__ref",
          }, [
            el("span", { class: "feedback__ref-icon", text: "▶" }),
            el("span", { class: "feedback__ref-titulo", text: r.titulo || r.archivo || r.url }),
          ]);
          refsBox.appendChild(a);
        });
        feedback.appendChild(refsBox);
      }
      const sigBtn = siguienteBtn();
      onSiguiente = () => sigBtn.click();
      feedback.appendChild(sigBtn);

      if (onAnswer) Promise.resolve(onAnswer(item, correcta)).catch(console.error);
    }

    const acciones = el("div", { class: "runner__acciones" }, [
      item.onEdit ? el("button", { class: "btn btn--ghost btn--sm",
        onClick: () => item.onEdit() }, "✎ Editar/corregir") : null,
      item.onMarcar ? el("button", { class: "btn btn--ghost btn--sm",
        onClick: (ev) => marcarParaRevisar(item, ev.currentTarget) },
        item._raw && item._raw.marcada_revision ? "🚩 Marcada (deshacer)" : "🚩 Marcar para revisar") : null,
      el("button", { class: "btn btn--ghost btn--sm", onClick: () => salir() }, "Salir"),
    ]);

    cont.append(cabecera, barra, enunciado, opcionesBox, feedback, acciones);
  }

  // Atajos de teclado: 1-9 / a-e seleccionan opción; Enter o Espacio → siguiente.
  function manejarTecla(e) {
    if (terminada) return;
    const t = e.target;
    // No interceptar cuando hay un input/textarea/select enfocado
    if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.tagName === "SELECT")) return;
    const k = e.key.toLowerCase();
    if (!respondida && opcionesBtns.length) {
      let idx = -1;
      if (k >= "1" && k <= "9") idx = parseInt(k, 10) - 1;
      else if (k >= "a" && k <= "i") idx = k.charCodeAt(0) - 97;
      if (idx >= 0 && idx < opcionesBtns.length) {
        e.preventDefault();
        opcionesBtns[idx].click();
        return;
      }
    }
    if ((k === "enter" || k === " ") && respondida && onSiguiente) {
      e.preventDefault();
      onSiguiente();
    }
  }
  window.addEventListener("keydown", manejarTecla);
  // Si el usuario navega sin pasar por "Salir" / "Ver resultados"
  // (ej. usando el navbar inferior), limpiamos el listener global.
  function limpiezaPorRuta() {
    window.removeEventListener("keydown", manejarTecla);
    window.removeEventListener("hashchange", limpiezaPorRuta);
    terminada = true;
  }
  window.addEventListener("hashchange", limpiezaPorRuta);

  function siguienteBtn() {
    const ultima = i === items.length - 1;
    return el("button", { class: "btn btn--primary",
      onClick: () => { if (ultima) finalizar(); else { i++; pintar(); } } },
      ultima ? "Ver resultados" : "Siguiente →");
  }

  function salir() {
    if (respuestas.length === 0) {
      window.removeEventListener("keydown", manejarTecla);
      navegar(""); return;
    }
    finalizar();
  }

  function finalizar() {
    if (terminada) return;
    terminada = true;
    window.removeEventListener("keydown", manejarTecla);
    const total = respuestas.length;
    const pct = total ? Math.round((aciertos / total) * 100) : 0;
    clear(cont);
    cont.append(
      el("h2", { text: "Resultado de la sesión" }),
      el("div", { class: "resultado" }, [
        el("div", { class: "resultado__pct", text: `${pct}%` }),
        el("p", { text: `${aciertos} de ${total} correctas.` }),
      ]),
      el("div", { class: "runner__acciones" }, [
        el("button", { class: "btn btn--primary", onClick: () => navegar("") }, "Inicio"),
        el("button", { class: "btn btn--ghost", onClick: () => history.back() }, "Otra sesión"),
      ]),
    );
    if (onFinish) Promise.resolve(onFinish({ total, aciertos, pct, respuestas })).catch(console.error);
  }

  mount(cont);
  pintar();
}
