// Router por hash. Las rutas registran funciones que reciben los parámetros.
const rutas = [];

export function ruta(patron, handler) {
  // patron: "" | "quiz" | "caso/:id".
  // filter(Boolean) hace que `ruta("")` quede como `partes=[]` y matchee
  // los segmentos vacíos del hash raíz (#, #/, vacío).
  const partes = patron.split("/").filter(Boolean);
  rutas.push({ partes, handler });
}

function parseHash() {
  const h = location.hash.replace(/^#\/?/, "");
  const [ruta] = h.split("?");
  return ruta.split("/").filter(Boolean);
}

function match(segmentos) {
  for (const r of rutas) {
    if (r.partes.length !== segmentos.length && !r.partes.some((p) => p === "*")) {
      continue;
    }
    const params = {};
    let ok = true;
    for (let i = 0; i < r.partes.length; i++) {
      const p = r.partes[i];
      if (p === "*") break;
      if (p.startsWith(":")) params[p.slice(1)] = decodeURIComponent(segmentos[i] || "");
      else if (p !== segmentos[i]) { ok = false; break; }
    }
    if (ok) return { handler: r.handler, params };
  }
  return null;
}

let onChange = () => {};
export function alCambiar(fn) { onChange = fn; }

let renderEnCurso = false;
async function render() {
  if (renderEnCurso) return;       // anti-loop
  renderEnCurso = true;
  try {
    const segmentos = parseHash();
    const m = match(segmentos);
    onChange(segmentos);
    if (m) {
      try { await m.handler(m.params); }
      catch (e) {
        console.error("[router]", e);
        const v = document.getElementById("vista");
        if (v) v.innerHTML = `<div class="card"><h2>Error al cargar la vista</h2><p>${e.message}</p><pre style="overflow:auto;max-width:100%">${(e.stack||"").split("\n").slice(0,5).join("\n")}</pre></div>`;
      }
    } else {
      // Ninguna ruta matcheó: redirige a inicio sin recursión.
      if (segmentos.length) {
        location.hash = "#/";
      } else {
        const v = document.getElementById("vista");
        if (v) v.innerHTML = `<div class="card"><h2>404</h2><p>No hay una vista registrada para la raíz. Recarga la página.</p></div>`;
      }
    }
  } finally {
    renderEnCurso = false;
  }
}

export function navegar(patron) {
  const dest = "#/" + patron;
  if (location.hash === dest) {
    // Mismo hash: re-renderizar la vista actual.
    render();
  } else {
    location.hash = dest;
  }
}

export function iniciarRouter() {
  window.addEventListener("hashchange", render);
  render();
}
