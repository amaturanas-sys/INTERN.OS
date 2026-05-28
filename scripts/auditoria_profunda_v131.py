#!/usr/bin/env python3
"""Auditoría profunda v1.3.1 — Fix 4 bugs de datos:
1. Schema mismatch: 20 nuevas defs sin pregunta/opciones (DEF-NOM, DEF-GUIA).
   Las convierto a MCQ + conservo contenido en `explicacion`.
2. Bleeds remanentes: 339 opciones >200 chars con markers de justificación.
   Split: opción se trunca al marker, resto se mueve a justificacion.
3. Letras duplicadas: 1 pregunta (R01708). Elimino segunda ocurrencia.
4. Sin opción correcta: 17 preguntas. 9 con artefactos PDF irrecuperables
   + 8 limpias pero sin marca. Todas marcadas `inactivo: true` para
   filtrarlas de rotación activa.
"""
import json, re
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).parent.parent
BANCO = ROOT / "data" / "banco_inicial.json"
DEFS  = ROOT / "data" / "definiciones_iniciales.json"

# ============================================================
# 1) MCQs PARA LAS 20 DEFINICIONES NUEVAS
# ============================================================
# Schema target: {id, tipo, concepto, pregunta, opciones, explicacion,
#                 especialidad, version_actual, historial_ediciones, ...}
# Conservamos la definición original en `explicacion` (largo).
# El campo `concepto` es el término. `categoria` se mapea a `especialidad`.

CAT_TO_ESP = {
    "ginecología/endocrino": "gineco", "medicina interna/endocrino": "medicina_interna",
    "gastroenterología": "gastroenterologia",  "cardiología/urgencias": "cardio",
    "nefrología": "nefro",       "endocrino": "endocrino",
    "infectología": "infecto",   "gastroenterología/hepatología": "gastroenterologia",
    "neurología/psiquiatría": "neurologia",
    "pulmonar": "respiratorio",  "cardiología": "cardio",
    "cardiología/hematología": "cardio",       "urgencias/UCI": "urgencias",
    "cardiología/pulmonar": "cardio",
}

# (id_def, pregunta, [opciones (letra,texto,correcta)], breve nota adicional)
QUIZ_NOM = {
    "DEF-NOM-001": ("¿Cuántos criterios de Rotterdam se requieren para el diagnóstico de "
                    "síndrome de ovario poliendocrino metabólico (SOPEM)?",
                    [("a", "1 de 3", False),
                     ("b", "2 de 3 + exclusión de otras causas", True),
                     ("c", "3 de 3 obligatorios", False),
                     ("d", "Solo morfología ecográfica", False),
                     ("e", "Solo hiperandrogenismo bioquímico", False)]),
    "DEF-NOM-002": ("Para el diagnóstico de síndrome de disfunción metabólica (antes "
                    "síndrome metabólico) según la definición operacional vigente (IDF/ATP-III), "
                    "se requieren ≥3 de los siguientes EXCEPTO:",
                    [("a", "Perímetro abdominal aumentado por etnia", False),
                     ("b", "TG ≥150 mg/dL", False),
                     ("c", "HDL bajo (<40 H, <50 M)", False),
                     ("d", "Microalbuminuria ≥30 mg/g", True),
                     ("e", "PA ≥130/85 o tratamiento", False)]),
    "DEF-NOM-003": ("¿Cuál criterio cardiometabólico es suficiente, junto con esteatosis, "
                    "para diagnosticar MASLD (antes NAFLD)?",
                    [("a", "Solo glicemia ≥126 mg/dL", False),
                     ("b", "Cualquier criterio cardiometabólico (IMC ≥25, glicemia alterada, "
                            "HTA, dislipidemia, perímetro abdominal aumentado)", True),
                     ("c", "Biopsia con esteatosis >30%", False),
                     ("d", "Resistencia insulínica medida con HOMA-IR", False),
                     ("e", "Consumo alcohólico significativo", False)]),
    "DEF-NOM-004": ("Una mujer 65 años llega a urgencia con PA 195/115 sin síntomas, sin "
                    "daño de órgano blanco. Según la AHA 2025, ¿cuál es la conducta correcta "
                    "para esta presión arterial marcadamente elevada asintomática (AMBP)?",
                    [("a", "Nifedipino sublingual inmediato", False),
                     ("b", "Reposo 30 min, optimizar régimen oral, seguimiento 24–72 h", True),
                     ("c", "Ingreso a UCI con nitroprusiato IV", False),
                     ("d", "Alta sin tratamiento", False),
                     ("e", "Captopril 50 mg sublingual", False)]),
    "DEF-NOM-005": ("Según KDIGO, ¿cuál NO es criterio diagnóstico de lesión renal aguda (LRA)?",
                    [("a", "Aumento de creatinina ≥0,3 mg/dL en 48 h", False),
                     ("b", "Aumento de creatinina ≥1,5× basal en 7 días", False),
                     ("c", "Diuresis <0,5 mL/kg/h por ≥6 h", False),
                     ("d", "TFG <60 mL/min mantenida por 3 meses", True),
                     ("e", "Requerimiento de terapia renal de reemplazo", False)]),
    "DEF-NOM-006": ("¿Cuál es la prueba diagnóstica de mayor precisión actualmente para "
                    "diferenciar deficiencia de arginina-vasopresina (AVP-D, antes diabetes "
                    "insípida central) de polidipsia primaria?",
                    [("a", "Test de privación de agua clásico", False),
                     ("b", "Copeptina estimulada con suero hipertónico o arginina", True),
                     ("c", "Osmolaridad urinaria basal", False),
                     ("d", "Resonancia magnética hipofisaria", False),
                     ("e", "AVP plasmática directa", False)]),
    "DEF-NOM-007": ("Respecto a mpox (antes viruela del mono), señale lo CORRECTO:",
                    [("a", "Profilaxis con vacuna JYNNEOS (MVA-BN), 2 dosis SC c/28 días", True),
                     ("b", "Tratamiento de primera línea: aciclovir IV", False),
                     ("c", "Solo se transmite por mordedura de animales", False),
                     ("d", "Clado II es el más virulento", False),
                     ("e", "El brote 2022 fue por clado I", False)]),
    "DEF-NOM-008": ("Tratamiento de primera línea de colangitis biliar primaria (CBP, antes "
                    "cirrosis biliar primaria) en una mujer 50 años con FA 3× elevada y AMA "
                    "positivos:",
                    [("a", "Corticoides IV", False),
                     ("b", "Ácido ursodeoxicólico 13–15 mg/kg/d", True),
                     ("c", "Inmunoglobulinas IV", False),
                     ("d", "Trasplante hepático inmediato", False),
                     ("e", "Plasmaféresis", False)]),
    "DEF-NOM-009": ("Según DSM-5, ¿en cuántos dominios cognitivos al menos debe haber "
                    "deterioro significativo para diagnosticar trastorno neurocognitivo "
                    "mayor (antes demencia)?",
                    [("a", "1 dominio", True),
                     ("b", "2 dominios", False),
                     ("c", "3 dominios", False),
                     ("d", "4 dominios", False),
                     ("e", "Todos los dominios", False)]),
    "DEF-NOM-010": ("Respecto al trastorno de síntomas neurológicos funcionales (TSNF, antes "
                    "trastorno conversivo) en DSM-5, ¿qué cambió respecto a DSM-IV?",
                    [("a", "Se requiere demostrar un estresor psicológico previo", False),
                     ("b", "Ya NO se requiere probar conflicto psicológico; basta con signos "
                            "positivos de incompatibilidad", True),
                     ("c", "Solo se diagnostica en mujeres", False),
                     ("d", "Es un trastorno de personalidad", False),
                     ("e", "Se trata solo con psicoanálisis", False)]),
}

QUIZ_GUIA = {
    "DEF-GUIA-001": ("Según GINA 2026, en Track 1 (preferido), ¿cuál es el medicamento de "
                     "RESCATE preferido en TODOS los escalones del adulto?",
                     [("a", "Salbutamol a demanda en monoterapia", False),
                      ("b", "Budesónida-formoterol (ICS-formoterol) a demanda", True),
                      ("c", "Bromuro de ipratropio", False),
                      ("d", "Salmeterol-fluticasona", False),
                      ("e", "Beclometasona en monoterapia", False)]),
    "DEF-GUIA-002": ("Según GOLD 2026 (EPOC), ¿cuál es el umbral de eosinófilos en sangre "
                     "que apoya añadir ICS al broncodilatador dual (triple terapia) en grupo E?",
                     [("a", "≥50 céls/µL", False),
                      ("b", "≥100 céls/µL", False),
                      ("c", "≥300 céls/µL", True),
                      ("d", "≥500 céls/µL", False),
                      ("e", "Independiente del recuento", False)]),
    "DEF-GUIA-003": ("¿Cuál es el cambio principal en el score de riesgo embólico de FA según "
                     "ESC 2024?",
                     [("a", "Se eliminó el sexo (CHA₂DS₂-VA en vez de VASc)", True),
                      ("b", "Se duplicó el peso de la edad", False),
                      ("c", "Se reemplazó por HAS-BLED", False),
                      ("d", "Se agregó el IMC", False),
                      ("e", "Se eliminó la diabetes", False)]),
    "DEF-GUIA-004": ("¿Cuál es la duración de la TRIPLE terapia (AAS + clopidogrel + DOAC) "
                     "tras SCA/ICP en paciente con FA, según ESC 2024?",
                     [("a", "Hasta 1 semana post-ICP", True),
                      ("b", "1 mes", False),
                      ("c", "3 meses", False),
                      ("d", "6 meses", False),
                      ("e", "12 meses", False)]),
    "DEF-GUIA-005": ("Según SSC 2026, ¿qué herramienta de tamizaje de sepsis se PREFIERE "
                     "sobre qSOFA en pacientes hospitalizados?",
                     [("a", "qSOFA por su simplicidad", False),
                      ("b", "NEWS2 o MEWS", True),
                      ("c", "SOFA en todo paciente febril", False),
                      ("d", "Solo lactato sérico", False),
                      ("e", "Solo PCR", False)]),
    "DEF-GUIA-006": ("Paciente con TEP categoría intermedio-alto (disfunción VD + biomarcadores "
                     "positivos), sin shock. Según AHA/ACC 2026 y ensayos PEERLESS/HI-PEITHO, "
                     "¿cuál es la conducta más apropiada en un centro con PERT?",
                     [("a", "Trombolisis sistémica de inmediato", False),
                      ("b", "Anticoagulación sola y observación pasiva", False),
                      ("c", "Activar PERT y evaluar trombectomía mecánica o CDT-US", True),
                      ("d", "Filtro de vena cava única medida", False),
                      ("e", "Aspirina 300 mg como antitrombótico", False)]),
    "DEF-GUIA-007": ("¿Cuál es el cambio de paradigma central de AACE 2026 en DM2?",
                     [("a", "Iniciar siempre con insulina basal", False),
                      ("b", "Comorbidities-centric ANTES que glucose-centric", True),
                      ("c", "Volver a sulfonilureas como 1ª línea", False),
                      ("d", "Suspender metformina rutinariamente", False),
                      ("e", "Iniciar todos con bomba de insulina", False)]),
    "DEF-GUIA-008": ("Paciente diabético insulinizado encontrado inconsciente en su casa, sin "
                     "acceso IV. Según ADA 2026, ¿cuál es la conducta inicial?",
                     [("a", "Glucosa IV 50 g de inmediato", False),
                      ("b", "Glucagón 1 mg IM/SC o intranasal 3 mg (Baqsimi)", True),
                      ("c", "Esperar paramédicos sin tratamiento", False),
                      ("d", "Adrenalina IM", False),
                      ("e", "Insulina regular adicional", False)]),
    "DEF-GUIA-009": ("¿Qué examen incorpora AHA/ACC 2026 como cribado UNA VEZ EN LA VIDA en "
                     "TODO adulto, por primera vez en una guía estadounidense?",
                     [("a", "ApoA-I", False),
                      ("b", "Lp(a) (lipoproteína a)", True),
                      ("c", "Homocisteína", False),
                      ("d", "Coronariografía", False),
                      ("e", "Score de calcio coronario obligatorio", False)]),
    "DEF-GUIA-010": ("Según ACG 2024, ¿cuál es la primera línea para erradicación de H. pylori "
                     "en regiones con resistencia a claritromicina >15%?",
                     [("a", "Triple terapia con claritromicina × 7 días", False),
                      ("b", "Cuádruple con bismuto × 14 d O vonoprazan dual × 14 d", True),
                      ("c", "Monoterapia con amoxicilina", False),
                      ("d", "Levofloxacina × 7 días", False),
                      ("e", "Solo PPI a dosis altas", False)]),
}

def convertir_def_a_mcq(d, banco_quiz):
    """Convierte una definición tipo termino+definicion a schema MCQ."""
    if d["id"] not in banco_quiz:
        return None
    pregunta_texto, opciones_raw = banco_quiz[d["id"]]
    opciones = [
        {"letra": l, "texto": t, "correcta": c} for (l, t, c) in opciones_raw
    ]
    nuevo = {
        "id": d["id"],
        "tipo": "concepto",  # tratamos como concepto para que aparezca en filtro
        "concepto": d.get("termino", ""),
        "pregunta": pregunta_texto,
        "opciones": opciones,
        "explicacion": d.get("definicion", ""),  # contenido extenso
        "especialidad": CAT_TO_ESP.get(d.get("categoria", ""), "general"),
        "imagen": None,
        "version_actual": 1,
        "historial_ediciones": [],
        # Metadata extra preservada
        "fuente_guia": d.get("fuente", ""),
        "vigencia": d.get("vigencia", ""),
        "categoria_original": d.get("categoria", ""),
    }
    return nuevo


# ============================================================
# 2) DETECTOR DE BLEEDS Y SPLIT
# ============================================================
PATRONES_BLEED = [
    r" Tiene un[ao]? ", r" Tiene una clínica", r" Se trata de ", r" Se sospecha ",
    r" Las otras opciones", r" La A \(", r" La B \(", r" La C \(", r" La D \(",
    r" La E \(", r" La opción ", r" Dado que ", r" Por lo (cual|que|tanto)",
    r" Si hubies[ae] ", r" La respuesta correcta", r" El paciente (presenta|tiene|cursa) ",
    r" Esto se debe ", r" Recordar que", r" Cabe destacar", r" En cambio ",
    r" Es un[ao]? ", r" Lleva ", r" Por tanto ", r" En este caso ",
    r" La causa ", r" Que esté ", r" Adicionalmente ", r" Además, ",
    r" Por otra parte ", r" Inicialmente ",
]
# Fallback: punto + espacio + Mayúscula (límite de oración dentro de una opción).
SENT_BOUNDARY = re.compile(r"(?<=[a-záéíóúñ])\. (?=[A-ZÁÉÍÓÚÑ][a-záéíóúñ])")

def encontrar_split(t):
    """Devuelve la posición del primer marker de bleed, o -1.
    Si la opción es >300 chars y no hay marker, usa fallback de límite de oración.
    """
    if len(t) <= 200:
        return -1
    mejor = len(t)
    for p in PATRONES_BLEED:
        m = re.search(p, t)
        if m and m.start() < mejor and m.start() >= 5:
            mejor = m.start()
    if mejor < len(t):
        return mejor
    # Fallback: si la opción es muy larga, dividir en el 1er límite de oración
    if len(t) > 300:
        m = SENT_BOUNDARY.search(t, 30)  # busca tras los primeros 30 chars
        if m:
            return m.start() + 1  # mantener el punto
    return -1


def main():
    banco = json.load(open(BANCO))
    defs  = json.load(open(DEFS))

    # ================= FIX 1: DEFINICIONES =================
    convertidas = 0
    BANCO_QUIZ = {**QUIZ_NOM, **QUIZ_GUIA}
    nuevas_defs = []
    for d in defs["definiciones"]:
        if d["id"].startswith(("DEF-NOM-", "DEF-GUIA-")) and "termino" in d and "pregunta" not in d:
            nuevo = convertir_def_a_mcq(d, BANCO_QUIZ)
            if nuevo:
                nuevas_defs.append(nuevo)
                convertidas += 1
            else:
                nuevas_defs.append(d)  # sin quiz definido, dejar como está
        else:
            nuevas_defs.append(d)
    defs["definiciones"] = nuevas_defs
    defs["meta"]["version"] = "v4-mcq-aligned"
    defs["meta"]["descripcion"] = (
        "Definiciones de fármacos, conceptos, herramientas y guías clínicas en formato MCQ. "
        "Las definiciones tipo guía conservan el contenido extenso en `explicacion` "
        "y un MCQ clave para repaso activo."
    )

    # ================= FIX 2: LIMPIAR ARTEFACTOS PDF MOODLE =================
    # "Sin contestar", "Puntúa como" son chrome de la interfaz Moodle que
    # se pegó en el cuerpo durante la extracción. Se eliminan + colapso de espacios.
    ART_PATS = [
        re.compile(r"\bSin contestar\b"),
        re.compile(r"\bPuntúa como\s*[\d,\.]*"),  # captura "Puntúa como 1,00"
        re.compile(r"\bMarcar pregunta\b"),
        re.compile(r"\bQuitar marca\b"),
        re.compile(r"\bRespuesta no obtenida\b"),
        re.compile(r"\bSeleccione una:\b"),
        re.compile(r"\bSeleccione una o más:\b"),
    ]
    # Scores Moodle huérfanos: "1,00", "0,50", "0,33", "0,66" etc.
    # Restringido a 0,XX y 1,00 (rango típico Moodle).
    # Sin lookahead estricto: el match siempre está rodeado de espacios.
    SCORE_HUERFANO = re.compile(r" (?:[01]),(?:00|25|33|50|66|75|80) ")
    SPACES = re.compile(r"[ \t]{2,}")

    def limpiar(t):
        if not t:
            return t
        for p in ART_PATS:
            t = p.sub(" ", t)
        t = SCORE_HUERFANO.sub(" ", t)
        t = SPACES.sub(" ", t).strip()
        return t

    artefactos_limpiados = 0
    for q in banco["preguntas"]:
        for campo in ("enunciado", "justificacion"):
            if q.get(campo):
                nuevo = limpiar(q[campo])
                if nuevo != q[campo]:
                    artefactos_limpiados += 1
                    q[campo] = nuevo
        for op in q.get("opciones", []) or []:
            for campo in ("texto", "feedback"):
                if op.get(campo):
                    nuevo = limpiar(op[campo])
                    if nuevo != op[campo]:
                        op[campo] = nuevo

    # ================= FIX 3: BLEEDS EN BANCO =================
    bleeds_split = 0
    chars_movidos = 0
    for q in banco["preguntas"]:
        cambios_just = []
        for op in q.get("opciones", []):
            t = op.get("texto", "") or ""
            pos = encontrar_split(t)
            if pos > 0:
                opcion_real = t[:pos].strip()
                bleed = t[pos:].strip()
                op["texto"] = opcion_real
                cambios_just.append(f"[Opción {op.get('letra','?').upper()}] {bleed}")
                bleeds_split += 1
                chars_movidos += len(bleed)
        if cambios_just:
            extra = "\n\n" + "\n".join(cambios_just)
            existing = q.get("justificacion", "") or ""
            primero = cambios_just[0][:80]
            if primero not in existing:
                q["justificacion"] = existing + extra

    # ================= FIX 4: LETRAS DUPLICADAS =================
    letras_dup_fixed = 0
    for q in banco["preguntas"]:
        ops = q.get("opciones", []) or []
        vistos = set()
        nuevas = []
        for op in ops:
            l = (op.get("letra") or "").lower()
            if l in vistos:
                letras_dup_fixed += 1
                continue  # descartar duplicada (segunda ocurrencia)
            vistos.add(l)
            nuevas.append(op)
        if len(nuevas) != len(ops):
            q["opciones"] = nuevas

    # ================= FIX 5: INACTIVAR SIN OPCIÓN CORRECTA =================
    # Solo las 17 que carecen de cualquier opción marcada como correcta.
    inactivas = 0
    for q in banco["preguntas"]:
        if not any(op.get("correcta") for op in q.get("opciones", [])):
            q["inactivo"] = True
            q["razon_inactivo"] = ["sin_correcta_marcada"]
            inactivas += 1

    # ================= META =================
    banco["meta"]["version"] = "reconstruccion_v9_auditoria_profunda"
    banco["meta"]["auditoria_v1_3_1"] = {
        "artefactos_pdf_limpiados": artefactos_limpiados,
        "bleeds_split": bleeds_split,
        "chars_movidos_a_justificacion": chars_movidos,
        "letras_duplicadas_corregidas": letras_dup_fixed,
        "preguntas_inactivadas": inactivas,
    }

    json.dump(banco, open(BANCO, "w"), ensure_ascii=False, indent=2)
    json.dump(defs,  open(DEFS,  "w"), ensure_ascii=False, indent=2)

    print(f"Definiciones convertidas a MCQ: {convertidas}")
    print(f"Preguntas con artefactos Moodle limpiados: {artefactos_limpiados}")
    print(f"Bleeds split: {bleeds_split} ({chars_movidos} chars movidos)")
    print(f"Letras duplicadas corregidas: {letras_dup_fixed}")
    print(f"Preguntas inactivadas (sin correcta): {inactivas}")


if __name__ == "__main__":
    main()
