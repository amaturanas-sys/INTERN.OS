// Sistema de íconos SVG inline. Estilo Lucide: 24x24 viewBox, stroke-width 1.75,
// líneas redondeadas, currentColor. Sin dependencias externas — todo el SVG
// se sirve como string para ser inyectado vía innerHTML del span contenedor.
// Uso: `icono("home", { tamano: 18, clase: "extra" })`.

const PATHS = {
  // --- Navegación / modos ---
  home: '<path d="M3 12l9-9 9 9"/><path d="M5 10v10a1 1 0 0 0 1 1h3v-6h6v6h3a1 1 0 0 0 1-1V10"/>',
  quiz: '<path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"/>' +
        '<rect x="9" y="3" width="6" height="4" rx="1"/>' +
        '<path d="M9 12h6M9 16h4"/>',
  casos: '<path d="M11 2v2M11 4a3 3 0 0 0-3 3v3a4 4 0 0 0 8 0V7a3 3 0 0 0-3-3"/>' +
         '<path d="M12 14v3a5 5 0 0 1-10 0v-2"/>' +
         '<circle cx="19" cy="13" r="3"/>' +
         '<path d="M16 13a3 3 0 0 1-4 0"/>',
  definiciones: '<path d="M9 18h6M10 22h4"/>' +
                '<path d="M12 2a7 7 0 0 0-4 12.7c.6.6 1 1.3 1 2.1v.2c0 .6.4 1 1 1h4c.6 0 1-.4 1-1v-.2c0-.8.4-1.5 1-2.1A7 7 0 0 0 12 2z"/>',
  progreso: '<path d="M3 3v18h18"/>' +
            '<rect x="7" y="13" width="3" height="5" rx="0.5"/>' +
            '<rect x="12" y="9" width="3" height="9" rx="0.5"/>' +
            '<rect x="17" y="5" width="3" height="13" rx="0.5"/>',
  ajustes: '<line x1="4" y1="6" x2="14" y2="6"/><line x1="18" y1="6" x2="20" y2="6"/>' +
           '<circle cx="16" cy="6" r="2"/>' +
           '<line x1="4" y1="12" x2="6" y2="12"/><line x1="10" y1="12" x2="20" y2="12"/>' +
           '<circle cx="8" cy="12" r="2"/>' +
           '<line x1="4" y1="18" x2="14" y2="18"/><line x1="18" y1="18" x2="20" y2="18"/>' +
           '<circle cx="16" cy="18" r="2"/>',
  importar: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>' +
            '<path d="M7 10l5-5 5 5"/><line x1="12" y1="5" x2="12" y2="15"/>',
  // --- Acciones / estado ---
  editar: '<path d="M17 3a2.83 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"/>',
  marcar: '<path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z"/>',
  marcar_lleno: '<path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z" fill="currentColor"/>',
  veloz: '<polygon points="13 2 3 14 11 14 11 22 21 10 13 10 13 2"/>',
  check: '<polyline points="20 6 9 17 4 12"/>',
  x: '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>',
  plus: '<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>',
  // --- Flechas / decoradores ---
  chevron_derecha: '<polyline points="9 6 15 12 9 18"/>',
  chevron_izquierda: '<polyline points="15 6 9 12 15 18"/>',
  flecha_derecha: '<line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>',
  // --- Biblioteca / búsqueda ---
  buscar: '<circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.5" y2="16.5"/>',
  biblioteca: '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>' +
              '<path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>',
};

export function icono(nombre, opts = {}) {
  const tamano = opts.tamano || 18;
  const cls = ["icono", opts.clase].filter(Boolean).join(" ");
  const path = PATHS[nombre] || PATHS.x;
  const span = document.createElement("span");
  span.className = cls;
  span.setAttribute("aria-hidden", "true");
  span.style.display = "inline-flex";
  span.style.alignItems = "center";
  span.style.justifyContent = "center";
  span.style.flexShrink = "0";
  span.innerHTML =
    `<svg width="${tamano}" height="${tamano}" viewBox="0 0 24 24" ` +
    `fill="none" stroke="currentColor" stroke-width="1.75" ` +
    `stroke-linecap="round" stroke-linejoin="round">${path}</svg>`;
  return span;
}

// Devuelve string HTML del SVG (para usar inline en index.html o donde se
// requiera texto plano sin nodo wrapper).
export function iconoHTML(nombre, tamano = 18) {
  const path = PATHS[nombre] || PATHS.x;
  return `<svg class="icono" width="${tamano}" height="${tamano}" viewBox="0 0 24 24" ` +
    `aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.75" ` +
    `stroke-linecap="round" stroke-linejoin="round">${path}</svg>`;
}
