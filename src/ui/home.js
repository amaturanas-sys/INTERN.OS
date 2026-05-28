// Landing: identidad InternOS + estadísticas, sesión veloz, modos, curación, herramientas.
import { el, mount, hoyISO } from "./dom.js";
import { navegar } from "./router.js";
import { count, getConfig, getAll } from "../db/db.js";
import { estadisticasRepaso, sesionDelDia } from "../repaso/sm2.js";
import { leerProgreso, registrarRespuesta, registrarSesion } from "../db/stats.js";
import { runMcq } from "./mcq.js";
import { requiereImagenFaltante } from "./imagen.js";
import { leerVersion, etiquetaCorta } from "../version.js";

export async function vistaHome() {
  const [nPreg, nCasos, nDefs, rep, g, objetivo, ver, todasPreg] = await Promise.all([
    count("preguntas"), count("casos_clinicos"), count("definiciones"),
    estadisticasRepaso(), leerProgreso(), getConfig("objetivo_diario", 30),
    leerVersion(), getAll("preguntas"),
  ]);
  const marcadas = todasPreg.filter((q) => q.marcada_revision).length;
  const editadas = todasPreg.filter((q) => (q.version_actual || 1) > 1).length;

  const pct = g.total_respondidas ? Math.round((g.total_correctas / g.total_respondidas) * 100) : 0;
  const hoyKey = hoyISO();
  const respondidasHoy = (g.por_dia && g.por_dia[hoyKey]) ? g.por_dia[hoyKey].respondidas : 0;
  const objetivoPct = Math.min(100, Math.round((respondidasHoy / objetivo) * 100));

  mount(el("div", { class: "home" }, [
    // ---- Hero con logo + versión ----
    el("div", { class: "home__hero" }, [
      el("div", { class: "home__hero-titulo" }, [
        el("img", { src: "assets/icon.svg", alt: "InternOS", class: "home__logo" }),
        el("span", { class: "home__version", title: ver.fecha_build || "", text: etiquetaCorta(ver) }),
      ]),
      el("p", { class: "muted", text: "Estudio EUNACOM offline · material del Dr. Guevara" }),
    ]),

    // ---- Estadísticas rápidas ----
    el("div", { class: "home__stats" }, [
      stat("Respondidas", g.total_respondidas || 0),
      stat("Acierto", `${pct}%`),
      stat("Racha", `🔥 ${g.racha_dias || 0}`),
      stat("Repaso", rep.pendientes || 0, "para hoy"),
      stat("Marcadas", marcadas, "por revisar"),
      stat("Editadas", editadas, "con fuente"),
    ]),

    // ---- Sesión veloz ----
    el("div", { class: "card sesion-dia" }, [
      el("div", { class: "sesion-dia__cab" }, [
        el("h2", { text: "Sesión veloz" }),
        el("span", { class: "muted", text: `${respondidasHoy} / ${objetivo} hoy` }),
      ]),
      el("div", { class: "progress" }, [
        el("div", {
          class: `progress__fill ${objetivoPct >= 100 ? "progress__fill--ok" : ""}`,
          style: `width:${objetivoPct}%`,
        }),
      ]),
      el("div", { class: "runner__acciones" }, [
        el("button", { class: "btn btn--primary",
          onClick: () => iniciarSesionDelDia(20)
        }, "⚡ 20 preguntas rápidas"),
        el("button", { class: "btn btn--ghost",
          onClick: () => iniciarSesionDelDia(Math.max(5, objetivo - respondidasHoy))
        }, respondidasHoy >= objetivo ? "+1 más" : `Completar día (${Math.max(0, objetivo - respondidasHoy)})`),
      ]),
      heatmap(g.por_dia, objetivo),
    ]),

    // ---- Modos de estudio ----
    el("h3", { class: "home__sub", text: "Modos" }),
    el("div", { class: "modos" }, [
      tarjeta("📝", "Quiz por temas", "Filtra por especialidad, tema, dificultad.", "quiz", `${nPreg} preguntas`),
      tarjeta("🩺", "Casos clínicos", "Casos paso a paso, lineales con feedback.", "casos", `${nCasos} casos`),
      tarjeta("💡", "Definiciones", "Conceptos, fármacos y herramientas.", "definiciones", `${nDefs} definiciones`),
    ]),

    // ---- Curación activa ----
    el("h3", { class: "home__sub", text: "Curación" }),
    el("div", { class: "modos" }, [
      tarjeta("✎", "Editar preguntas", "Buscar, corregir y enriquecer con bibliografía.", "preguntas", `${nPreg} en el banco`),
      marcadas > 0
        ? tarjeta("🚩", "Marcadas", "Cola personal para revisar y corregir.", "marcadas", `${marcadas} pendientes`)
        : tarjeta("🚩", "Marcadas", "Aparecerán aquí al usar 🚩 durante un quiz.", "marcadas", "vacía"),
      tarjeta("📂", "Importar .md / .txt", "Añade preguntas, casos o definiciones por archivo.", "importar"),
    ]),

    // ---- Herramientas ----
    el("h3", { class: "home__sub", text: "Herramientas" }),
    el("div", { class: "modos" }, [
      tarjeta("📊", "Mi progreso", "Estadísticas, temas débiles y sesiones recientes.", "progreso"),
      tarjeta("⚙️", "Ajustes", "Objetivo diario, exportar / restaurar, offline.", "ajustes"),
    ]),
  ]));
}

function stat(label, valor, sub) {
  return el("div", { class: "home__stat" }, [
    el("div", { class: "home__stat-val", text: String(valor) }),
    el("div", { class: "home__stat-lbl", text: label }),
    sub ? el("div", { class: "home__stat-sub", text: sub }) : null,
  ]);
}

function tarjeta(icono, titulo, desc, ruta, meta) {
  return el("button", { class: "modo-card", onClick: () => navegar(ruta) }, [
    el("div", { class: "modo-card__icono", text: icono }),
    el("div", { class: "modo-card__cuerpo" }, [
      el("h3", { text: titulo }),
      el("p", { class: "muted", text: desc }),
      meta ? el("span", { class: "modo-card__meta", text: meta }) : null,
    ]),
    el("span", { class: "lista__flecha", text: "›" }),
  ]);
}

async function iniciarSesionDelDia(target) {
  const lista = (await sesionDelDia(target)).filter((q) => !requiereImagenFaltante(q));
  if (!lista.length) {
    mount(el("div", { class: "card" }, [
      el("h2", { text: "Sesión veloz" }),
      el("p", { class: "muted", text: "No quedan preguntas disponibles." }),
      el("button", { class: "btn btn--primary", onClick: () => navegar("") }, "Volver"),
    ]));
    return;
  }
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
    titulo: "Sesión veloz",
    subtitulo: `${items.length} preguntas: repaso + falladas + nuevas`,
    items,
    onAnswer: (item, correcta) => registrarRespuesta({
      store: "preguntas", item: item._raw, correcta,
      tema: item._raw.tema_validado, ref: { tipo: "pregunta", id: item.id },
    }),
    onFinish: (r) => registrarSesion({ modo: "diaria", ...r }),
  });
}

function heatmap(porDia, objetivo) {
  porDia = porDia || {};
  const dias = [];
  for (let i = 29; i >= 0; i--) {
    const d = new Date(Date.now() - i * 86400000).toISOString().slice(0, 10);
    dias.push({ d, n: (porDia[d] && porDia[d].respondidas) || 0 });
  }
  return el("div", { class: "heatmap" },
    dias.map((x) => {
      const intensidad =
        x.n === 0 ? "0" :
        x.n < objetivo / 3 ? "1" :
        x.n < (2 * objetivo) / 3 ? "2" :
        x.n < objetivo ? "3" : "4";
      return el("span", {
        class: `heatmap__c heatmap__c--${intensidad}`,
        title: `${x.d} · ${x.n} respondidas`,
      });
    }));
}
