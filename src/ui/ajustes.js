// Ajustes: estado de datos, exportar/restaurar banco, reinicio y estado offline.
import { el, mount, toast, modal } from "./dom.js";
import { navegar } from "./router.js";
import { getAll, bulkPut, clearStore, count, setConfig, getConfig } from "../db/db.js";

// Convierte Blob a dataURL base64 (para serializar imágenes en JSON).
function blobToDataURL(blob) {
  return new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => resolve(r.result);
    r.onerror = () => reject(r.error);
    r.readAsDataURL(blob);
  });
}

// Reconstruye un Blob desde dataURL base64.
async function dataURLToBlob(dataURL) {
  const res = await fetch(dataURL);
  return res.blob();
}

// Tamaño total ocupado por las imágenes de la biblioteca (bytes).
async function tamanoImagenesBytes() {
  const imgs = await getAll("biblioteca_imagenes").catch(() => []);
  return imgs.reduce((s, r) => s + ((r.blob && r.blob.size) || 0), 0);
}

export async function vistaAjustes() {
  const [nPreg, nCasos, nDefs] = await Promise.all([
    count("preguntas"), count("casos_clinicos"), count("definiciones"),
  ]);
  const nEdiciones = await count("biblioteca_ediciones").catch(() => 0);
  const nImagenes = await count("biblioteca_imagenes").catch(() => 0);
  const bytesImagenes = await tamanoImagenesBytes();
  const fechaSeed = await getConfig("seed_fecha", "—");
  const objetivo = await getConfig("objetivo_diario", 30);
  const offline = navigator.onLine ? "Conectado" : "Sin conexión (funciona igual)";

  let estimacion = "n/d";
  if (navigator.storage && navigator.storage.estimate) {
    const e = await navigator.storage.estimate();
    estimacion = `${(e.usage / 1048576).toFixed(1)} MB usados de ${(e.quota / 1048576).toFixed(0)} MB`;
  }

  mount(el("div", { class: "card" }, [
    el("h2", { text: "Ajustes" }),
    el("dl", { class: "datos" }, [
      fila("Preguntas", nPreg), fila("Casos", nCasos), fila("Definiciones", nDefs),
      fila("Biblioteca · ediciones locales", nEdiciones),
      fila("Biblioteca · imágenes indexadas", `${nImagenes} (${(bytesImagenes / 1048576).toFixed(1)} MB)`),
      fila("Banco cargado", fechaSeed === "—" ? "—" : new Date(fechaSeed).toLocaleString()),
      fila("Almacenamiento", estimacion), fila("Estado", offline),
    ]),
    el("h3", { text: "Objetivo diario" }),
    el("div", { class: "form" }, [
      el("label", { class: "form__row" }, [
        el("span", { class: "form__label", text: "Preguntas por día" }),
        (() => {
          const inp = el("input", { type: "number", min: "5", max: "200", step: "5", value: String(objetivo) });
          inp.addEventListener("change", async () => {
            const v = Math.max(5, Math.min(200, parseInt(inp.value, 10) || 30));
            await setConfig("objetivo_diario", v);
            toast(`Objetivo: ${v} preguntas/día`, "ok");
          });
          return inp;
        })(),
      ]),
    ]),
    el("h3", { text: "Respaldo del banco" }),
    el("div", { class: "runner__acciones" }, [
      el("button", { class: "btn btn--primary", onClick: exportar }, "Exportar banco (JSON)"),
      el("label", { class: "btn btn--ghost" }, [
        "Restaurar banco", el("input", { type: "file", accept: ".json", style: "display:none", onChange: restaurar }),
      ]),
    ]),
    el("p", { class: "muted", text:
      "Incluye preguntas, casos, definiciones, progreso y repaso (SM-2)." }),

    el("h3", { text: "Respaldo de la biblioteca" }),
    el("div", { class: "runner__acciones" }, [
      el("button", { class: "btn btn--primary", onClick: exportarBiblioteca },
        "Exportar biblioteca (JSON)"),
      el("label", { class: "btn btn--ghost" }, [
        "Restaurar biblioteca",
        el("input", { type: "file", accept: ".json", style: "display:none", onChange: restaurarBiblioteca }),
      ]),
    ]),
    el("p", { class: "muted", text:
      `Incluye tus ediciones locales (${nEdiciones}) e imágenes indexadas (${nImagenes}, ${(bytesImagenes / 1048576).toFixed(1)} MB en base64). Usa este respaldo para mover tu biblioteca a otro dispositivo.` }),

    el("h3", { text: "Mantenimiento" }),
    el("div", { class: "runner__acciones" }, [
      el("button", { class: "btn btn--danger", onClick: borrarTodo }, "Borrar todos los datos"),
      el("button", { class: "btn btn--ghost", onClick: () => navegar("") }, "Volver"),
    ]),
    el("p", { class: "muted", text: "Persistencia: los datos viven en IndexedDB del dispositivo. Exporta periódicamente para respaldar tus correcciones." }),
  ]));

  async function exportar() {
    const dump = {
      exportado: new Date().toISOString(),
      preguntas: await getAll("preguntas"),
      casos_clinicos: await getAll("casos_clinicos"),
      definiciones: await getAll("definiciones"),
      progreso_usuario: await getAll("progreso_usuario"),
      repaso: await getAll("repaso"),
    };
    const blob = new Blob([JSON.stringify(dump, null, 2)], { type: "application/json" });
    const a = el("a", { href: URL.createObjectURL(blob), download: `eunacom_backup_${Date.now()}.json` });
    document.body.appendChild(a); a.click(); a.remove();
    toast("Banco exportado.", "ok");
  }

  async function restaurar(e) {
    const f = e.target.files[0];
    if (!f) return;
    let parsed;
    try { parsed = JSON.parse(await f.text()); }
    catch (err) { toast("Archivo inválido: " + (err.message || "no es JSON"), "error"); return; }

    const pasos = [
      ["preguntas",        parsed.preguntas],
      ["casos_clinicos",   parsed.casos_clinicos],
      ["definiciones",     parsed.definiciones],
      ["progreso_usuario", parsed.progreso_usuario],
      ["repaso",           parsed.repaso],
    ].filter(([, arr]) => Array.isArray(arr) && arr.length);
    if (!pasos.length) { toast("El archivo no contiene datos restaurables.", "error"); return; }

    for (let i = 0; i < pasos.length; i++) {
      const [store, arr] = pasos[i];
      toast(`Restaurando ${store}… (${i + 1}/${pasos.length})`, "info");
      try { await bulkPut(store, arr); }
      catch (err) {
        toast(`Falló al restaurar ${store}: ${err && err.message || "error"}`, "error");
        return;
      }
    }
    toast(`Restauración completa: ${pasos.length} stores.`, "ok");
    navegar("ajustes");
  }

  async function exportarBiblioteca() {
    toast("Empaquetando biblioteca…", "info");
    const ediciones = await getAll("biblioteca_ediciones").catch(() => []);
    const imagenes = await getAll("biblioteca_imagenes").catch(() => []);
    // Convertir blobs a dataURL en paralelo (limitado para no explotar memoria)
    const imagenesSer = [];
    for (const img of imagenes) {
      let dataURL = null;
      if (img.blob) {
        try { dataURL = await blobToDataURL(img.blob); }
        catch (_) { continue; }
      }
      imagenesSer.push({
        id: img.id,
        mime: img.mime || (img.blob && img.blob.type) || "image/png",
        titulo: img.titulo || "",
        descripcion: img.descripcion || "",
        fecha: img.fecha || null,
        dataURL,
      });
    }
    const dump = {
      tipo: "internos-biblioteca",
      version: 1,
      exportado: new Date().toISOString(),
      ediciones,
      imagenes: imagenesSer,
    };
    const blob = new Blob([JSON.stringify(dump)], { type: "application/json" });
    const a = el("a", {
      href: URL.createObjectURL(blob),
      download: `internos_biblioteca_${Date.now()}.json`,
    });
    document.body.appendChild(a); a.click(); a.remove();
    toast(`Biblioteca exportada (${ediciones.length} ediciones, ${imagenesSer.length} imágenes).`, "ok");
  }

  async function restaurarBiblioteca(e) {
    const f = e.target.files[0];
    if (!f) return;
    let parsed;
    try { parsed = JSON.parse(await f.text()); }
    catch (err) { toast("Archivo inválido: " + (err.message || "no es JSON"), "error"); return; }
    if (parsed.tipo !== "internos-biblioteca") {
      toast("El archivo no es un respaldo de biblioteca de InternOS.", "error");
      return;
    }
    const ediciones = Array.isArray(parsed.ediciones) ? parsed.ediciones : [];
    const imagenes = Array.isArray(parsed.imagenes) ? parsed.imagenes : [];
    if (!ediciones.length && !imagenes.length) {
      toast("El archivo no contiene ediciones ni imágenes.", "error");
      return;
    }
    toast(`Restaurando ${ediciones.length} ediciones e ${imagenes.length} imágenes…`, "info");
    try {
      if (ediciones.length) await bulkPut("biblioteca_ediciones", ediciones);
      // Imágenes: reconstruir Blob desde dataURL una por una
      const imgsRestauradas = [];
      for (const img of imagenes) {
        if (!img.dataURL) continue;
        try {
          const blob = await dataURLToBlob(img.dataURL);
          imgsRestauradas.push({
            id: img.id,
            blob,
            mime: img.mime,
            titulo: img.titulo,
            descripcion: img.descripcion,
            fecha: img.fecha,
          });
        } catch (_) { /* salta imagen corrupta */ }
      }
      if (imgsRestauradas.length) await bulkPut("biblioteca_imagenes", imgsRestauradas);
      toast(`Biblioteca restaurada: ${ediciones.length} ediciones, ${imgsRestauradas.length} imágenes.`, "ok");
      navegar("ajustes");
    } catch (err) {
      toast(`Falló al restaurar biblioteca: ${err && err.message || "error"}`, "error");
    }
  }

  function borrarTodo() {
    modal("Borrar todos los datos",
      el("p", { text:
        "Se eliminarán preguntas, casos, definiciones, progreso, ediciones de biblioteca e imágenes indexadas de este dispositivo. El banco inicial se volverá a cargar. ¿Continuar?" }),
      [
        { label: "Cancelar", clase: "btn--ghost" },
        { label: "Borrar", clase: "btn--danger", onClick: async () => {
          for (const s of [
            "preguntas", "casos_clinicos", "definiciones", "progreso_usuario", "repaso",
            "biblioteca_ediciones", "biblioteca_imagenes",
          ]) {
            try { await clearStore(s); } catch (_) { /* store puede no existir en DB antigua */ }
          }
          // Limpiar marcadores de seed para forzar re-sembrado en el próximo arranque.
          await setConfig("seed_done", false);
          await setConfig("seed_banco_version", null);
          toast("Datos borrados. Recargando…", "ok");
          setTimeout(() => location.reload(), 800);
        } },
      ]);
  }
}

function fila(k, v) { return el("div", { class: "datos__fila" }, [el("dt", { text: k }), el("dd", { text: String(v) })]); }
