// Helpers mínimos de DOM y UI (sin framework).

// Atajo común: fecha YYYY-MM-DD local (se usa en stats, editor, home, sm2).
export const hoyISO = () => new Date().toISOString().slice(0, 10);

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
  const overlay = el("div", { class: "modal-overlay" });
  const cerrar = () => overlay.remove();
  overlay.addEventListener("click", (e) => { if (e.target === overlay) cerrar(); });

  const botones = acciones.map((a) =>
    el("button", {
      class: `btn ${a.clase || "btn--ghost"}`,
      onClick: () => { if (!a.onClick || a.onClick() !== false) cerrar(); },
    }, a.label)
  );

  const box = el("div", { class: "modal" }, [
    el("div", { class: "modal__head" }, [
      el("h3", { text: titulo }),
      el("button", { class: "modal__x", onClick: cerrar, "aria-label": "Cerrar" }, "✕"),
    ]),
    el("div", { class: "modal__body" }, [contenido]),
    el("div", { class: "modal__foot" }, botones),
  ]);
  overlay.appendChild(box);
  document.body.appendChild(overlay);
  return { cerrar, overlay };
}

export function badge(texto, clase = "") {
  return el("span", { class: `badge ${clase}` }, texto);
}
