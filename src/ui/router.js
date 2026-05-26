// Router por hash. Las rutas registran funciones que reciben los parámetros.
const rutas = [];

export function ruta(patron, handler) {
  // patron: "quiz" o "caso/:id". Se convierte a regex.
  const partes = patron.split("/");
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
      if (r.partes.length !== segmentos.length) continue;
    }
    const params = {};
    let ok = true;
    for (let i = 0; i < r.partes.length; i++) {
      const p = r.partes[i];
      if (p.startsWith(":")) params[p.slice(1)] = decodeURIComponent(segmentos[i] || "");
      else if (p === "*") { break; }
      else if (p !== segmentos[i]) { ok = false; break; }
    }
    if (ok) return { handler: r.handler, params };
  }
  return null;
}

let onChange = () => {};
export function alCambiar(fn) { onChange = fn; }

async function render() {
  const segmentos = parseHash();
  const m = match(segmentos);
  onChange(segmentos);
  if (m) {
    try { await m.handler(m.params); }
    catch (e) { console.error(e); document.getElementById("vista").innerHTML =
      `<div class="card"><h2>Error</h2><p>${e.message}</p></div>`; }
  } else {
    navegar(segmentos.length ? "" : "");
  }
}

export function navegar(patron) {
  if (location.hash === "#/" + patron) render();
  else location.hash = "#/" + patron;
}

export function iniciarRouter() {
  window.addEventListener("hashchange", render);
  render();
}
