// Utilidades para imágenes de apoyo (decisión 10.5). Se guardan como data URL.

export function archivoADataURL(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

import { el } from "./dom.js";

// Devuelve un nodo con la imagen de apoyo, o null si no hay.
export function vistaImagen(imagen) {
  if (!imagen || !imagen.presente || !imagen.data) return null;
  const fig = el("figure", { class: "imagen-apoyo" }, [
    el("img", {
      src: imagen.data,
      alt: imagen.descripcion || "Imagen de apoyo",
      loading: "lazy",
      decoding: "async",
      // Si el dataURL es inválido / quedó truncado, ocultamos el figure
      // entero en lugar de mostrar el icono roto del navegador.
      onError: (e) => { if (e.target.parentElement) e.target.parentElement.style.display = "none"; },
    }),
    imagen.descripcion ? el("figcaption", { text: imagen.descripcion }) : null,
  ]);
  return fig;
}

// ¿El ítem queda fuera del quiz por requerir imagen y no tenerla?
export function requiereImagenFaltante(item) {
  const img = item.imagen;
  return !!(img && img.requerida && !(img.presente && img.data));
}
