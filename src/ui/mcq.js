// Runner genérico de sesiones MCQ. Lo usan el Modo 1 (quiz) y el Modo 3 (definiciones).
import { el, clear, mount, badge } from "./dom.js";
import { vistaImagen } from "./imagen.js";
import { navegar } from "./router.js";

// items: [{ id, tipo, enunciado, opciones:[{letra,texto,correcta}], explicacion, imagen,
//           subtitulo, onEdit }]
// hooks: onAnswer(item, correcta), onFinish(resultado)
export function runMcq({ items, titulo, subtitulo, onAnswer, onFinish }) {
  if (!items.length) {
    mount(el("div", { class: "card" }, [
      el("h2", { text: titulo }),
      el("p", { class: "muted", text: "No hay ítems disponibles con estos criterios." }),
      el("button", { class: "btn btn--primary", onClick: () => navegar("") }, "Volver al inicio"),
    ]));
    return;
  }

  let i = 0;
  let aciertos = 0;
  const respuestas = [];
  const cont = el("div", { class: "card runner" });

  function pintar() {
    const item = items[i];
    clear(cont);
    let respondida = false;

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

    item.opciones.forEach((op) => {
      const btn = el("button", { class: "opcion" }, [
        el("span", { class: "opcion__letra", text: op.letra.toUpperCase() }),
        el("span", { class: "opcion__texto", text: op.texto }),
      ]);
      btn.addEventListener("click", () => {
        if (respondida) return;
        respondida = true;
        const correcta = !!op.correcta;
        if (correcta) aciertos++;
        respuestas.push({ id: item.id, correcta });

        Array.from(opcionesBox.children).forEach((b, idx) => {
          b.classList.add("opcion--bloqueada");
          if (item.opciones[idx].correcta) b.classList.add("opcion--correcta");
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
        feedback.appendChild(siguienteBtn());

        if (onAnswer) Promise.resolve(onAnswer(item, correcta)).catch(console.error);
      });
      opcionesBox.appendChild(btn);
    });

    const acciones = el("div", { class: "runner__acciones" }, [
      item.onEdit ? el("button", { class: "btn btn--ghost btn--sm",
        onClick: () => item.onEdit() }, "✎ Editar/corregir") : null,
      el("button", { class: "btn btn--ghost btn--sm", onClick: () => salir() }, "Salir"),
    ]);

    cont.append(cabecera, barra, enunciado, opcionesBox, feedback, acciones);
  }

  function siguienteBtn() {
    const ultima = i === items.length - 1;
    return el("button", { class: "btn btn--primary",
      onClick: () => { if (ultima) finalizar(); else { i++; pintar(); } } },
      ultima ? "Ver resultados" : "Siguiente →");
  }

  function salir() {
    if (respuestas.length === 0) { navegar(""); return; }
    finalizar();
  }

  function finalizar() {
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
      ]),
    );
    if (onFinish) Promise.resolve(onFinish({ total, aciertos, pct, respuestas })).catch(console.error);
  }

  mount(cont);
  pintar();
}
