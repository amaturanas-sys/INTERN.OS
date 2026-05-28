// Ajustes: estado de datos, exportar/restaurar banco, reinicio y estado offline.
import { el, mount, toast, modal } from "./dom.js";
import { navegar } from "./router.js";
import { getAll, bulkPut, clearStore, count, setConfig, getConfig } from "../db/db.js";

export async function vistaAjustes() {
  const [nPreg, nCasos, nDefs] = await Promise.all([
    count("preguntas"), count("casos_clinicos"), count("definiciones"),
  ]);
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
    el("h3", { text: "Respaldo" }),
    el("div", { class: "runner__acciones" }, [
      el("button", { class: "btn btn--primary", onClick: exportar }, "Exportar banco (JSON)"),
      el("label", { class: "btn btn--ghost" }, [
        "Restaurar banco", el("input", { type: "file", accept: ".json", style: "display:none", onChange: restaurar }),
      ]),
    ]),
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
    try {
      const dump = JSON.parse(await f.text());
      if (dump.preguntas) await bulkPut("preguntas", dump.preguntas);
      if (dump.casos_clinicos) await bulkPut("casos_clinicos", dump.casos_clinicos);
      if (dump.definiciones) await bulkPut("definiciones", dump.definiciones);
      if (dump.progreso_usuario) await bulkPut("progreso_usuario", dump.progreso_usuario);
      if (dump.repaso) await bulkPut("repaso", dump.repaso);
      toast("Banco restaurado.", "ok");
      navegar("ajustes");
    } catch (err) { toast("Archivo inválido: " + err.message, "error"); }
  }

  function borrarTodo() {
    modal("Borrar todos los datos",
      el("p", { text: "Se eliminarán preguntas, casos, definiciones y progreso de este dispositivo. El banco inicial se volverá a cargar. ¿Continuar?" }),
      [
        { label: "Cancelar", clase: "btn--ghost" },
        { label: "Borrar", clase: "btn--danger", onClick: async () => {
          for (const s of ["preguntas", "casos_clinicos", "definiciones", "progreso_usuario", "repaso"]) await clearStore(s);
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
