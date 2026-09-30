// Utilidades para imágenes de apoyo (decisión 10.5).
import { el } from "./dom.js";

// Tope después de reducir. Lo que lo supere se rechaza con un mensaje claro.
export const TOPE_IMAGEN_BYTES = 1.5 * 1024 * 1024;

/**
 * Reduce una imagen antes de guardarla.
 *
 * Una foto de la cámara de la tablet (4000×3000, 6-8 MB) se guardaba entera:
 * en el editor, como ~11 MB de base64 DENTRO del registro de la pregunta, que
 * además queda residente en RAM por la caché de getAll("preguntas"). Con
 * pocas fotos el WebView de Android se quedaba sin memoria o reventaba la
 * cuota de IndexedDB. Para estudiar, 1600 px de lado mayor sobra.
 *
 * - Si ya es chica (≤ ladoMax y ≤ 400 KB) se devuelve tal cual.
 * - PNG/GIF/WebP pueden tener transparencia (esquemas, diagramas): se
 *   re-codifican a WebP, que la conserva. El resto, a JPEG sobre fondo blanco.
 * - Si el navegador no puede decodificarla (p. ej. SVG, HEIC) y es chica, se
 *   deja como está; si es grande, se rechaza.
 */
export async function reducirImagen(file, { ladoMax = 1600, calidad = 0.85 } = {}) {
  if (!file || !/^image\//.test(file.type || "")) {
    throw new Error("El archivo no es una imagen.");
  }
  let bmp;
  try {
    bmp = await createImageBitmap(file, { imageOrientation: "from-image" });
  } catch (_) {
    if (file.size <= TOPE_IMAGEN_BYTES) return file;
    throw new Error("No se pudo procesar la imagen y es demasiado grande para guardarla tal cual.");
  }
  const escala = Math.min(1, ladoMax / Math.max(bmp.width, bmp.height));
  if (escala === 1 && file.size <= 400 * 1024) { bmp.close && bmp.close(); return file; }

  const w = Math.max(1, Math.round(bmp.width * escala));
  const h = Math.max(1, Math.round(bmp.height * escala));
  const canvas = document.createElement("canvas");
  canvas.width = w; canvas.height = h;
  const ctx = canvas.getContext("2d");
  const conTransparencia = /png|gif|webp/.test(file.type);
  if (!conTransparencia) { ctx.fillStyle = "#fff"; ctx.fillRect(0, 0, w, h); }
  ctx.drawImage(bmp, 0, 0, w, h);
  bmp.close && bmp.close();

  const aBlob = (tipo) => new Promise((r) => canvas.toBlob(r, tipo, calidad));
  let salida = await aBlob(conTransparencia ? "image/webp" : "image/jpeg");
  // Si el navegador no sabe codificar WebP, toBlob devuelve PNG o null.
  if (!salida || (conTransparencia && salida.type !== "image/webp" && salida.size > file.size)) {
    salida = await aBlob("image/png");
  }
  // Nunca devolver algo más pesado que el original.
  return salida && salida.size < file.size ? salida : file;
}

export function archivoADataURL(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}


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
