// Lista de preguntas marcadas para revisar. Acceso a edición + práctica rápida.
import { el, mount, badge, toast } from "../ui/dom.js";
import { getAll, put } from "../db/db.js";
import { navegar } from "../ui/router.js";
import { runMcq } from "../ui/mcq.js";
import { registrarRespuesta, registrarSesion } from "../db/stats.js";
import { requiereImagenFaltante } from "../ui/imagen.js";

export async function vistaMarcadas() {
  const todas = await getAll("preguntas");
  const marcadas = todas.filter((q) => q.marcada_revision);

  if (!marcadas.length) {
    mount(el("div", { class: "card" }, [
      el("h2", { text: "Preguntas marcadas" }),
      el("p", { class: "muted", text: "No tienes preguntas marcadas para revisar. Mientras haces el quiz puedes marcar con 🚩 las que quieras volver a ver." }),
      el("button", { class: "btn btn--primary", onClick: () => navegar("") }, "Volver"),
    ]));
    return;
  }

  function ficha(q) {
    return el("li", { class: "marcadas__item" }, [
      el("div", { class: "marcadas__cuerpo" }, [
        el("div", { class: "chips" }, [
          q.especialidad_principal ? badge(q.especialidad_principal) : null,
          q.tema_validado ? badge(q.tema_validado) : null,
          q.dificultad_estimada ? badge(q.dificultad_estimada) : null,
        ]),
        el("p", { class: "marcadas__enunciado", text: q.enunciado }),
      ]),
      el("div", { class: "marcadas__acc" }, [
        el("button", { class: "btn btn--ghost btn--sm",
          onClick: () => navegar(`editar/pregunta/${encodeURIComponent(q.id_unico)}`) },
          "✎ Editar"),
        el("button", { class: "btn btn--ghost btn--sm",
          onClick: async () => {
            q.marcada_revision = false;
            await put("preguntas", q);
            toast("Desmarcada.", "ok");
            navegar("marcadas");
          } }, "Desmarcar"),
      ]),
    ]);
  }

  mount(el("div", { class: "card" }, [
    el("h2", { text: `Preguntas marcadas (${marcadas.length})` }),
    el("p", { class: "muted", text: "Cola personal de revisión. Edita con bibliografía o practícalas de corrido." }),
    el("div", { class: "runner__acciones" }, [
      el("button", { class: "btn btn--primary", onClick: () => practicar(marcadas) }, "Practicar todas las marcadas"),
      el("button", { class: "btn btn--ghost", onClick: () => navegar("") }, "Volver"),
    ]),
    el("ul", { class: "marcadas" }, marcadas.map(ficha)),
  ]));
}

async function practicar(marcadas) {
  const lista = marcadas.filter((q) => q.utilizable !== false && !requiereImagenFaltante(q));
  if (!lista.length) { toast("No hay marcadas utilizables.", "error"); return; }
  const items = lista.map((q) => ({
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
  }));
  runMcq({
    titulo: "Marcadas para revisar",
    subtitulo: `${items.length} preguntas en tu cola`,
    items,
    onAnswer: (item, correcta) => registrarRespuesta({
      store: "preguntas", item: item._raw, correcta,
      tema: item._raw.tema_validado, ref: { tipo: "pregunta", id: item.id },
    }),
    onFinish: (r) => registrarSesion({ modo: "marcadas", ...r }),
  });
}
