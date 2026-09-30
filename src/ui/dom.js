// Helpers mínimos de DOM y UI (sin framework).

// Fechas YYYY-MM-DD en hora LOCAL (se usan en stats, editor, home, sm2).
//
// Antes se usaba toISOString().slice(0,10), que devuelve la fecha UTC. En
// Chile (UTC-3/-4) el "día" rodaba a las 21:00: estudiar a las 20:00 y a las
// 21:30 de la misma noche sumaba +1 a la racha, y el heatmap y el repaso
// SM-2 quedaban corridos un día por la noche. Tampoco se resta 86400000 ms
// para "ayer": en los días de cambio de horario el día dura 23 o 25 horas.
export function fechaLocalISO(d = new Date()) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const dia = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${dia}`;
}
export const hoyISO = () => fechaLocalISO();
// Suma (o resta, con n negativo) días de calendario a una fecha YYYY-MM-DD.
export function sumarDiasISO(iso, n) {
  const [y, m, d] = iso.split("-").map(Number);
  return fechaLocalISO(new Date(y, m - 1, d + n));
}
export const diasAtrasISO = (n) => sumarDiasISO(hoyISO(), -n);

// Shuffle Fisher-Yates (usado por quiz-temas y definiciones).
export function mezclar(a) {
  const arr = a.slice();
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

export function el(tag, props = {}, children = []) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (k === "class") node.className = v;
    else if (k === "html") node.innerHTML = v;
    else if (k === "text") node.textContent = v;
    else if (k === "dataset") Object.assign(node.dataset, v);
    else if (k.startsWith("on") && typeof v === "function") {
      node.addEventListener(k.slice(2).toLowerCase(), v);
    } else if (v !== null && v !== undefined && v !== false) {
      node.setAttribute(k, v);
    }
  }
  const kids = Array.isArray(children) ? children : [children];
  for (const c of kids) {
    if (c == null || c === false) continue;
    node.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
  }
  return node;
}

export function clear(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
  return node;
}

export function mount(view) {
  const root = document.getElementById("vista");
  clear(root);
  // Emite una señal para que los runners (mcq, casos) limpien listeners
  // globales (keydown, etc.) al re-entrar al mismo hash o cambiar de vista.
  // Sin esto, navegar a #/quiz dos veces seguidas dejaba el listener viejo
  // activo y un tap registraba como dos.
  document.dispatchEvent(new CustomEvent("vista:cambia"));
  root.appendChild(view);
  root.scrollTop = 0;
  window.scrollTo(0, 0);
}

let toastTimer = null;
export function toast(mensaje, tipo = "info") {
  let t = document.getElementById("toast");
  if (!t) {
    // role + aria-live para que lectores de pantalla anuncien el toast.
    t = el("div", { id: "toast", role: "status", "aria-live": "polite", "aria-atomic": "true" });
    document.body.appendChild(t);
  }
  t.className = `toast toast--${tipo} toast--visible`;
  t.textContent = mensaje;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { t.className = "toast"; }, 3200);
}

export function modal(titulo, contenido, acciones = []) {
  // Restaurar foco al elemento que abrió el modal al cerrarse.
  const foco_previo = document.activeElement;
  const overlay = el("div", { class: "modal-overlay" });
  const cerrar = () => {
    overlay.remove();
    document.removeEventListener("keydown", onKey);
    // El elemento que abrió el modal puede haber desaparecido (p. ej. la
    // acción del modal re-renderizó la vista). Enfocar un nodo fuera del
    // documento no hace nada y el foco quedaba perdido en <body>.
    if (foco_previo && foco_previo.focus && document.contains(foco_previo)) foco_previo.focus();
  };
  overlay.addEventListener("click", (e) => { if (e.target === overlay) cerrar(); });

  const botones = acciones.map((a) =>
    el("button", {
      class: `btn ${a.clase || "btn--ghost"}`,
      onClick: () => { if (!a.onClick || a.onClick() !== false) cerrar(); },
    }, a.label)
  );

  const tituloId = "modal-titulo-" + Math.random().toString(36).slice(2, 8);
  const box = el("div", {
    class: "modal", role: "dialog", "aria-modal": "true", "aria-labelledby": tituloId,
  }, [
    el("div", { class: "modal__head" }, [
      el("h3", { id: tituloId, text: titulo }),
      (() => {
        // SVG inline para la X (evita ciclo con iconos.js).
        const x = document.createElement("button");
        x.className = "modal__x";
        x.setAttribute("aria-label", "Cerrar");
        x.innerHTML = '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" ' +
          'fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">' +
          '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';
        x.addEventListener("click", cerrar);
        return x;
      })(),
    ]),
    el("div", { class: "modal__body" }, [contenido]),
    el("div", { class: "modal__foot" }, botones),
  ]);
  overlay.appendChild(box);

  // Focus trap: Tab/Shift+Tab queda dentro del modal; Escape cierra.
  function focusables() {
    return box.querySelectorAll("button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])");
  }
  function onKey(e) {
    if (e.key === "Escape") { e.preventDefault(); cerrar(); return; }
    if (e.key !== "Tab") return;
    const f = Array.from(focusables()).filter((n) => !n.disabled);
    if (!f.length) return;
    const primero = f[0], ultimo = f[f.length - 1];
    if (e.shiftKey && document.activeElement === primero) { e.preventDefault(); ultimo.focus(); }
    else if (!e.shiftKey && document.activeElement === ultimo) { e.preventDefault(); primero.focus(); }
  }
  document.addEventListener("keydown", onKey);
  document.body.appendChild(overlay);
  // Focus inicial al primer botón (típicamente "Cerrar" o la primera acción).
  setTimeout(() => { const f = focusables()[0]; if (f) f.focus(); }, 0);
  return { cerrar, overlay };
}

export function badge(texto, clase = "") {
  return el("span", { class: `badge ${clase}` }, texto);
}
