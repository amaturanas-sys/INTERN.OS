// Punto de entrada: inicializa IndexedDB + seed, registra rutas y arranca el router.
import { ruta, iniciarRouter, navegar, alCambiar } from "./ui/router.js";
import { seedIfNeeded } from "./db/seed.js";
import { toast } from "./ui/dom.js";

import { vistaHome } from "./ui/home.js";
import { vistaQuizFiltros } from "./modos/quiz-temas.js";
import { vistaCasosLista, vistaCaso } from "./modos/casos-clinicos.js";
import { vistaDefiniciones } from "./modos/definiciones.js";
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
ruta("importar", vistaImportar);
ruta("progreso", vistaProgreso);
ruta("ajustes", vistaAjustes);
ruta("editar/:tipo/:id", ({ tipo, id }) => abrirEditor(tipo, id));

// Resalta el item de navegación activo.
alCambiar((segmentos) => {
  const base = segmentos[0] || "home";
  document.querySelectorAll("[data-nav]").forEach((b) => {
    b.classList.toggle("activo", b.dataset.nav === base || (base === "home" && b.dataset.nav === ""));
  });
});

async function arranque() {
  const splash = document.getElementById("splash");
  const setMsg = (m) => { const s = document.getElementById("splash-msg"); if (s) s.textContent = m; };
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
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("./service-worker.js").catch((e) => console.warn("SW:", e));
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
