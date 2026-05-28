// Punto de entrada: inicializa IndexedDB + seed, registra rutas y arranca el router.
import { ruta, iniciarRouter, navegar, alCambiar } from "./ui/router.js";
import { seedIfNeeded } from "./db/seed.js";
import { toast } from "./ui/dom.js";

import { vistaHome } from "./ui/home.js";
import { leerVersion } from "./version.js";
import { vistaQuizFiltros } from "./modos/quiz-temas.js";
import { vistaCasosLista, vistaCaso } from "./modos/casos-clinicos.js";
import { vistaDefiniciones } from "./modos/definiciones.js";
import { vistaMarcadas } from "./modos/marcadas.js";
import { vistaListadoPreguntas } from "./modos/listado-preguntas.js";
import { vistaImportar } from "./importar/importar.js";
import { vistaProgreso } from "./ui/progreso.js";
import { vistaAjustes } from "./ui/ajustes.js";
import { abrirEditor } from "./editor/editor.js";

// --- Rutas ---
ruta("", vistaHome);
ruta("quiz", vistaQuizFiltros);
ruta("casos", vistaCasosLista);
ruta("caso/:id", vistaCaso);
ruta("definiciones", vistaDefiniciones);
ruta("marcadas", vistaMarcadas);
ruta("preguntas", vistaListadoPreguntas);
ruta("importar", vistaImportar);
ruta("progreso", vistaProgreso);
ruta("ajustes", vistaAjustes);
ruta("editar/:tipo/:id", ({ tipo, id }) => abrirEditor(tipo, id));

// Resalta el item de navegación activo. Algunas rutas hijas
// se mapean a una pestaña del navbar para coherencia visual.
const NAV_ALIAS = {
  caso: "casos",
  preguntas: "quiz",   // listado para editar pertenece al universo de quiz
  marcadas: "quiz",
  editar: "quiz",
  importar: "quiz",
};
alCambiar((segmentos) => {
  const raw = segmentos[0] || "";
  const base = NAV_ALIAS[raw] || raw || "home";
  document.querySelectorAll("[data-nav]").forEach((b) => {
    const target = b.dataset.nav || "home";
    b.classList.toggle("activo", target === base || (base === "home" && target === ""));
  });
});

async function arranque() {
  const splash = document.getElementById("splash");
  const setMsg = (m) => { const s = document.getElementById("splash-msg"); if (s) s.textContent = m; };
  // Versión visible en <title> y splash desde el primer instante.
  const v = await leerVersion();
  document.title = `InternOS v${v.version} — EUNACOM`;
  const splashSub = document.getElementById("splash-version");
  if (splashSub) splashSub.textContent = `v${v.version}${v.commit !== "local" ? " · " + v.commit : ""}`;
  try {
    const r = await seedIfNeeded(setMsg);
    if (r.sembrado) toast(`Banco inicial cargado (${r.preguntas} preguntas).`, "ok");
  } catch (e) {
    console.error(e);
    setMsg("Error al cargar el banco inicial: " + e.message);
    return;
  }
  if (splash) splash.remove();
  iniciarRouter();
}

// Navegación inferior.
document.querySelectorAll("[data-nav]").forEach((b) => {
  b.addEventListener("click", () => navegar(b.dataset.nav));
});

// Service worker (offline).
// Cuando aparece una versión nueva del SW (cache name distinto por SHA),
// fuerza el reload del cliente para que use los nuevos JS/CSS.
if ("serviceWorker" in navigator) {
  let recargando = false;
  navigator.serviceWorker.addEventListener("controllerchange", () => {
    if (recargando) return;
    recargando = true;
    location.reload();
  });
  window.addEventListener("load", async () => {
    try {
      const reg = await navigator.serviceWorker.register("./service-worker.js");
      reg.addEventListener("updatefound", () => {
        const sw = reg.installing;
        if (!sw) return;
        sw.addEventListener("statechange", () => {
          if (sw.state === "installed" && navigator.serviceWorker.controller) {
            // Hay un SW nuevo listo; el controllerchange disparará el reload.
            sw.postMessage({ type: "SKIP_WAITING" });
          }
        });
      });
    } catch (e) { console.warn("SW:", e); }
  });
}

// Prompt de instalación (PWA).
let deferredPrompt = null;
window.addEventListener("beforeinstallprompt", (e) => {
  e.preventDefault();
  deferredPrompt = e;
  const btn = document.getElementById("btn-instalar");
  if (btn) {
    btn.hidden = false;
    btn.addEventListener("click", async () => {
      btn.hidden = true;
      deferredPrompt.prompt();
      await deferredPrompt.userChoice;
      deferredPrompt = null;
    }, { once: true });
  }
});

arranque();
