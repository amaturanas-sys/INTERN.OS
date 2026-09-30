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
      if (p.startsWith(":")) {
        // decodeURIComponent lanza URIError ante secuencias inválidas
        // (%E0%A4%A). Tratamos URLs malformadas como crudas para evitar crash.
        try { params[p.slice(1)] = decodeURIComponent(segmentos[i] || ""); }
        catch (_) { params[p.slice(1)] = segmentos[i] || ""; }
      } else if (p !== segmentos[i]) { ok = false; break; }
    }
    if (ok) return { handler: r.handler, params };
  }
  return null;
}

let onChange = () => {};
export function alCambiar(fn) { onChange = fn; }

// Si llega un hashchange mientras una vista todavía se está construyendo (p.
// ej. vistaQuizFiltros hace un getAll de miles de preguntas), antes se
// descartaba con un `return` y se perdía para siempre: la URL ya decía
// #/progreso pero la pantalla seguía en el quiz. Ahora se anota como
// pendiente y se vuelve a renderizar al terminar, leyendo el hash más
// reciente. Varios cambios seguidos se colapsan en un solo render final.
let renderEnCurso = false;
let renderPendiente = false;

// Construido con nodos y textContent, no con innerHTML: el mensaje del error
// puede llegar a contener texto de la URL.
function pintarErrorDeVista(v, e) {
  const detalle = ((e && e.message) || "Error desconocido").toString().slice(0, 240);
  const boton = (texto, clase, accion) => {
    const b = document.createElement("button");
    b.className = `btn ${clase}`;
    b.textContent = texto;
    b.addEventListener("click", accion);
    return b;
  };
  const card = document.createElement("div");
  card.className = "card";
  const h = document.createElement("h2");
  h.textContent = "Algo falló al cargar la vista";
  const p = document.createElement("p");
  p.className = "muted";
  p.textContent = detalle;
  const acciones = document.createElement("div");
  acciones.className = "runner__acciones";
  acciones.append(
    boton("Volver al inicio", "btn--primary", () => { location.hash = "#/"; }),
    boton("Recargar", "btn--ghost", () => location.reload()),
  );
  card.append(h, p, acciones);
  v.replaceChildren(card);
}

async function render() {
  if (renderEnCurso) { renderPendiente = true; return; }
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
        if (v) pintarErrorDeVista(v, e);
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
    if (renderPendiente) {
      renderPendiente = false;
      render();
    }
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
