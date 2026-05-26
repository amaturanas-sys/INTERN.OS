// Parser de la convención .md definida en la sección 10.1 de la arquitectura.
// Front-matter YAML + cuerpo estructurado. Varios ítems por archivo, cada uno
// con su propio front-matter. La marca (x) indica la alternativa correcta.

function parseFrontMatter(lines) {
  // YAML plano clave: valor (sin anidamiento).
  const fm = {};
  for (const raw of lines) {
    const line = raw.trim();
    if (!line) continue;
    const idx = line.indexOf(":");
    if (idx === -1) continue;
    const key = line.slice(0, idx).trim();
    let val = line.slice(idx + 1).trim();
    val = val.replace(/^["']|["']$/g, "");
    fm[key] = val;
  }
  return fm;
}

// Divide el archivo en bloques [frontmatter, body] usando líneas "---".
function splitItems(text) {
  const lines = text.replace(/\r\n/g, "\n").split("\n");
  const delim = [];
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].trim() === "---") delim.push(i);
  }
  const items = [];
  // Los "---" alternan abrir/cerrar. Cada ítem usa un par (open, close).
  for (let k = 0; k + 1 < delim.length; k += 2) {
    const open = delim[k];
    const close = delim[k + 1];
    const fmLines = lines.slice(open + 1, close);
    const bodyEnd = k + 2 < delim.length ? delim[k + 2] : lines.length;
    const bodyLines = lines.slice(close + 1, bodyEnd);
    items.push({ fm: parseFrontMatter(fmLines), body: bodyLines });
  }
  return items;
}

// Extrae secciones del cuerpo por encabezados (# o ##). Devuelve {tituloLower: [lineas]}.
function parseSections(bodyLines) {
  const secciones = {};
  let actual = "_preludio";
  secciones[actual] = [];
  for (const line of bodyLines) {
    const m = line.match(/^#{1,3}\s+(.*)$/);
    if (m) {
      actual = m[1].trim().toLowerCase();
      secciones[actual] = [];
    } else {
      secciones[actual].push(line);
    }
  }
  return secciones;
}

function findSection(secciones, ...nombres) {
  for (const n of nombres) {
    const key = Object.keys(secciones).find((k) => k.startsWith(n));
    if (key) return secciones[key];
  }
  return null;
}

function parseOpciones(lines) {
  const opciones = [];
  let letra = 97; // 'a'
  for (const raw of lines) {
    const line = raw.trim();
    const m = line.match(/^-\s*\((x|\s*)\)\s*(.+)$/i);
    if (!m) continue;
    const correcta = m[1].trim().toLowerCase() === "x";
    let texto = m[2].trim();
    let feedback = null;
    const pipe = texto.indexOf("|");
    if (pipe !== -1) {
      feedback = texto.slice(pipe + 1).trim();
      texto = texto.slice(0, pipe).trim();
    }
    opciones.push({
      letra: String.fromCharCode(letra++),
      texto,
      correcta,
      ...(feedback !== null ? { feedback } : {}),
    });
  }
  return opciones;
}

function joinText(lines) {
  return (lines || []).join("\n").trim();
}

const sello = () => Date.now().toString(36);
const imagenVacia = () => ({ presente: false, requerida: false, data: null, descripcion: null });
const histInicial = (fuente) => [{
  version: 1, fecha: new Date().toISOString().slice(0, 10),
  fuente: fuente || "Importado desde .md", nota: "Importación inicial", snapshot: null,
}];

function buildMcq(fm, secciones, n) {
  const enun = findSection(secciones, "pregunta", "enunciado");
  const ops = findSection(secciones, "opciones", "alternativas");
  const just = findSection(secciones, "justificación", "justificacion", "explicación", "explicacion");
  return {
    id_unico: fm.id || `IMP-MCQ-${sello()}-${n}`,
    enunciado: joinText(enun) || joinText(secciones._preludio),
    opciones: parseOpciones(ops || []),
    justificacion: joinText(just),
    especialidad_principal: fm.especialidad || "general",
    tema_validado: fm.tema || "",
    subtema: fm.subtema || "",
    sistema_behrens: fm.sistema_behrens || fm.sistema || "",
    dificultad_estimada: fm.dificultad || "intermedia",
    contexto: fm.contexto || "",
    habilidad_evaluada: fm.habilidad || "",
    frecuencia_eunacom: fm.frecuencia || "",
    ges_relacionado: fm.ges || "",
    tiene_imagen_referenciada: false,
    estado_imagen: "no_aplica",
    utilizable: true,
    imagen: imagenVacia(),
    version_actual: 1,
    historial_ediciones: histInicial(fm.fuente),
    estadisticas_usuario: { veces_respondida: 0, veces_correcta: 0, ultima_vez: null },
  };
}

function buildDefinicion(fm, secciones, n) {
  const enun = findSection(secciones, "pregunta");
  const ops = findSection(secciones, "opciones", "alternativas");
  const exp = findSection(secciones, "explicación", "explicacion", "justificación", "justificacion");
  return {
    id: fm.id || `IMP-DEF-${sello()}-${n}`,
    tipo: fm.subtipo || fm.tipo_def || "concepto",
    concepto: fm.concepto || "",
    pregunta: joinText(enun),
    opciones: parseOpciones(ops || []),
    explicacion: joinText(exp),
    especialidad: fm.especialidad || "general",
    imagen: imagenVacia(),
    version_actual: 1,
    historial_ediciones: [],
  };
}

function buildCaso(fm, secciones, bodyLines, n) {
  // Las etapas se reconstruyen leyendo el cuerpo en orden.
  const etapas = [];
  let resumen = "";
  let etapaActual = null;
  let subseccion = null; // "opciones" | "enunciado"
  let orden = 0;

  for (const line of bodyLines) {
    const h2 = line.match(/^##\s+(.*)$/);
    const h3 = line.match(/^###\s+(.*)$/);
    if (h2) {
      const titulo = h2[1].trim();
      const mEtapa = titulo.match(/^etapa\s*:?\s*(.*)$/i);
      if (mEtapa) {
        if (etapaActual) etapas.push(etapaActual);
        orden += 1;
        etapaActual = { orden, tipo: (mEtapa[1] || "etapa").trim().toLowerCase(), enunciado: [], opciones: [] };
        subseccion = "enunciado";
      } else if (/^resumen/i.test(titulo)) {
        if (etapaActual) { etapas.push(etapaActual); etapaActual = null; }
        subseccion = "resumen";
      }
      continue;
    }
    if (h3) {
      if (/opciones|alternativas/i.test(h3[1])) subseccion = "opciones";
      continue;
    }
    if (subseccion === "enunciado" && etapaActual) etapaActual.enunciado.push(line);
    else if (subseccion === "opciones" && etapaActual) etapaActual.opciones.push(line);
    else if (subseccion === "resumen") resumen += line + "\n";
  }
  if (etapaActual) etapas.push(etapaActual);

  const etapasFinal = etapas.map((e) => ({
    orden: e.orden,
    tipo: e.tipo,
    enunciado: joinText(e.enunciado),
    opciones: parseOpciones(e.opciones),
  }));

  return {
    id: fm.id || `IMP-CASO-${sello()}-${n}`,
    titulo: fm.titulo || "Caso importado",
    especialidad: fm.especialidad || "general",
    tema: fm.tema || "",
    dificultad: fm.dificultad || "intermedia",
    imagen: imagenVacia(),
    etapas: etapasFinal,
    resumen_final: resumen.trim(),
    version_actual: 1,
    historial_ediciones: [],
  };
}

// API principal: devuelve { preguntas:[], casos:[], definiciones:[], errores:[] }
export function parseMarkdown(text) {
  const items = splitItems(text);
  const out = { preguntas: [], casos: [], definiciones: [], errores: [] };
  if (items.length === 0) {
    out.errores.push("No se encontró ningún front-matter (bloques delimitados por ---).");
    return out;
  }
  items.forEach((it, i) => {
    const tipo = (it.fm.tipo || "").toLowerCase();
    const secciones = parseSections(it.body);
    try {
      if (tipo === "mcq") {
        const q = buildMcq(it.fm, secciones, i);
        if (!q.opciones.length) out.errores.push(`Ítem ${i + 1} (mcq): sin opciones válidas.`);
        else out.preguntas.push(q);
      } else if (tipo === "definicion" || tipo === "definición") {
        const d = buildDefinicion(it.fm, secciones, i);
        if (!d.opciones.length) out.errores.push(`Ítem ${i + 1} (definicion): sin opciones válidas.`);
        else out.definiciones.push(d);
      } else if (tipo === "caso") {
        const c = buildCaso(it.fm, secciones, it.body, i);
        if (!c.etapas.length) out.errores.push(`Ítem ${i + 1} (caso): sin etapas.`);
        else out.casos.push(c);
      } else {
        out.errores.push(`Ítem ${i + 1}: tipo desconocido o ausente ("${tipo}").`);
      }
    } catch (err) {
      out.errores.push(`Ítem ${i + 1}: error al parsear (${err.message}).`);
    }
  });
  return out;
}
