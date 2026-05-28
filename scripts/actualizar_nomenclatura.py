#!/usr/bin/env python3
"""Migración v1.2.1 — actualización de nomenclatura clínica.

Reemplaza términos en enunciado/opciones/feedback y prepende
nota de nomenclatura + criterios actualizados en justificacion.
No altera ids ni opciones correctas.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
BANCO = ROOT / "data" / "banco_inicial.json"
CASOS = ROOT / "data" / "casos_iniciales.json"
DEFS  = ROOT / "data" / "definiciones_iniciales.json"

# (pattern, replacement, nombre_corto, nota_nomenclatura, fuente)
# Las patterns son regex case-insensitive. El replacement preserva
# capitalización aproximada con función.
RENAMES = [
    {
        "key": "sopem",
        "patterns": [
            (r"s[ií]ndrome de ovario poliqu[ií]stico", "síndrome de ovario poliendocrino metabólico (SOPEM, antes SOP)"),
            (r"ovario poliqu[ií]stico", "ovario poliendocrino metabólico"),
        ],
        "sigla": r"\bSOP\b",
        "sigla_repl": "SOPEM",
        "contexto_sigla": r"ovario|androgen|hirsut|menstrual|amenorrea|oligomenorrea|insulin|metform",
        "nota": ("Nomenclatura actualizada: el síndrome de ovario poliquístico (SOP) ha sido "
                 "redenominado «síndrome de ovario poliendocrino metabólico» (SOPEM) por el "
                 "consenso internacional 2023, reflejando el componente metabólico (resistencia "
                 "insulínica, riesgo cardiovascular). Criterios de Rotterdam vigentes: 2 de 3 — "
                 "oligo/anovulación, hiperandrogenismo clínico o bioquímico, morfología ovárica "
                 "poliquística (≥20 folículos por ovario y/o volumen >10 mL) — más exclusión de "
                 "otras causas. Manejo: estilo de vida y metformina como pilares."),
    },
    {
        "key": "sdm",
        "patterns": [
            (r"s[ií]ndrome metab[óo]lico", "síndrome de disfunción metabólica (antes síndrome metabólico)"),
        ],
        "sigla": None,
        "nota": ("Nomenclatura actualizada: el síndrome metabólico se denomina ahora "
                 "«síndrome de disfunción metabólica», resaltando el continuo fisiopatológico "
                 "más que el agrupamiento de criterios. Definición operacional (ATP-III/IDF "
                 "vigente): ≥3 de — circunferencia abdominal aumentada por etnia, TG ≥150, "
                 "HDL bajo, PA ≥130/85 o tratamiento, glicemia ≥100 o DM."),
    },
    {
        "key": "masld",
        "patterns": [
            (r"esteatosis hep[áa]tica no alcoh[óo]lica", "enfermedad hepática esteatósica asociada a disfunción metabólica (MASLD, antes NAFLD/EHNA)"),
            (r"h[ií]gado graso no alcoh[óo]lico", "enfermedad hepática esteatósica asociada a disfunción metabólica (MASLD)"),
            (r"\bNAFLD\b", "MASLD"),
            (r"\bNASH\b", "MASH"),
            (r"\bEHNA\b", "MASLD"),
        ],
        "sigla": None,
        "nota": ("Nomenclatura actualizada (consenso multinacional AASLD-EASL-ALEH 2023): "
                 "NAFLD → MASLD (Metabolic dysfunction-Associated Steatotic Liver Disease) y "
                 "NASH → MASH. Diagnóstico: esteatosis hepática + ≥1 criterio cardiometabólico "
                 "(IMC ≥25, perímetro abdominal aumentado, alteración glicémica, HTA, dislipidemia). "
                 "Manejo: pérdida de peso 7-10%, control metabólico; resmetirom aprobado en MASH "
                 "con fibrosis F2-F3."),
    },
    {
        "key": "ambp",
        "patterns": [
            (r"urgencia hipertensiva", "presión arterial marcadamente elevada asintomática (AMBP, antes urgencia hipertensiva)"),
            (r"crisis hipertensiva", "crisis hipertensiva (emergencia o presión marcadamente elevada asintomática)"),
        ],
        "sigla": None,
        "nota": ("Nomenclatura actualizada (AHA 2025): el término «urgencia hipertensiva» se "
                 "reemplaza por «presión arterial marcadamente elevada asintomática» (AMBP, "
                 "asymptomatic markedly elevated BP) cuando hay PA ≥180/120 sin daño agudo de "
                 "órgano blanco, porque «urgencia» implicaba erróneamente reducción inmediata. "
                 "Manejo: reposo, reevaluar 30 min, optimizar régimen ambulatorio; descenso de "
                 "PA en horas-días, no minutos. Emergencia hipertensiva (con daño agudo de "
                 "órgano: encefalopatía, IAM, edema pulmonar, eclampsia, disección): UCI + "
                 "endovenoso, descenso 20-25% en la primera hora."),
    },
    {
        "key": "lra",
        "patterns": [
            (r"insuficiencia renal aguda", "lesión renal aguda (LRA, antes IRA)"),
            (r"falla renal aguda", "lesión renal aguda (LRA)"),
        ],
        "sigla": r"\bIRA\b",
        "sigla_repl": "LRA",
        "contexto_sigla": r"creatinin|BUN|nitrogen|ri[ñn][óo]n|renal|oliguria|anuria|prerrenal|NTA|necrosis tubular|KDIGO|diuresis|nefron",
        "nota": ("Nomenclatura actualizada (KDIGO): el término «insuficiencia renal aguda» (IRA) "
                 "se reemplazó por «lesión renal aguda» (LRA, AKI). Criterios diagnósticos: "
                 "↑creatinina ≥0,3 mg/dL en 48 h, o ≥1,5× basal en 7 días, o diuresis "
                 "<0,5 mL/kg/h por ≥6 h. Estadios I-III según delta de creatinina y oliguria. "
                 "Causas: prerrenal (hipovolemia, IC, shock — más frecuente), renal (NTA isquémica "
                 "o por nefrotóxicos, GN, NIA), postrenal (obstrucción)."),
    },
    {
        "key": "avpd",
        "patterns": [
            (r"diabetes ins[ií]pida central", "deficiencia de arginina-vasopresina (AVP-D, antes diabetes insípida central)"),
            (r"diabetes ins[ií]pida nefrog[ée]nica", "resistencia a arginina-vasopresina (AVP-R, antes diabetes insípida nefrogénica)"),
            (r"diabetes ins[ií]pida", "deficiencia/resistencia de arginina-vasopresina (AVP-D/AVP-R, antes diabetes insípida)"),
        ],
        "sigla": None,
        "nota": ("Nomenclatura actualizada (consenso 2022-2023): «diabetes insípida central» → "
                 "deficiencia de arginina-vasopresina (AVP-D); «diabetes insípida nefrogénica» → "
                 "resistencia a arginina-vasopresina (AVP-R). El cambio evita confusión con "
                 "diabetes mellitus (causa de errores de medicación graves). Clínica: poliuria "
                 "hipotónica + polidipsia. Diagnóstico: test de privación de agua; copeptina basal "
                 "y estimulada con hipertónica/arginina diferencia AVP-D de polidipsia primaria. "
                 "Tratamiento AVP-D: desmopresina. AVP-R: tiazidas + AINEs + dieta hiposódica."),
    },
    {
        "key": "mpox",
        "patterns": [
            (r"viruela del mono", "mpox (antes viruela del mono)"),
            (r"monkeypox", "mpox"),
        ],
        "sigla": None,
        "nota": ("Nomenclatura actualizada (OMS 2022): «monkeypox/viruela del mono» → «mpox», "
                 "para evitar estigmatización geográfica/étnica. Agente: orthopoxvirus, clados I "
                 "(África central, más virulento) y II (África occidental, brote global 2022). "
                 "Clínica: pródromo (fiebre, adenopatías) + exantema vesiculo-pustular sincrónico, "
                 "frecuentemente con lesiones anogenitales en el brote actual. Vacuna: JYNNEOS "
                 "(MVA-BN). Antiviral: tecovirimat en casos graves o inmunocomprometidos."),
    },
    {
        "key": "cbp",
        "patterns": [
            (r"cirrosis biliar primaria", "colangitis biliar primaria (CBP, antes cirrosis biliar primaria)"),
        ],
        "sigla": None,
        "nota": ("Nomenclatura actualizada (consenso internacional 2014): «cirrosis biliar "
                 "primaria» → «colangitis biliar primaria» (mantiene la sigla CBP). El cambio "
                 "refleja que la cirrosis es una complicación tardía, no la enfermedad. "
                 "Diagnóstico: 2 de 3 — colestasis bioquímica (FA elevada >1,5x), AMA positivos "
                 "(≥1:40) o anti-sp100/gp210, biopsia compatible (no obligatoria si serología "
                 "típica). Tratamiento de primera línea: ácido ursodeoxicólico 13-15 mg/kg/d. "
                 "Segunda línea (no respondedores): ácido obeticólico, fibratos."),
    },
    {
        "key": "tsnf",
        "patterns": [
            (r"trastorno conversivo", "trastorno de síntomas neurológicos funcionales (TSNF, antes trastorno conversivo)"),
            (r"trastorno de conversi[óo]n", "trastorno de síntomas neurológicos funcionales (TSNF)"),
            (r"reacci[óo]n conversiva", "manifestación de trastorno de síntomas neurológicos funcionales (TSNF)"),
        ],
        "sigla": None,
        "nota": ("Nomenclatura actualizada (DSM-5/ICD-11): «trastorno conversivo» → «trastorno "
                 "de síntomas neurológicos funcionales» (TSNF/FND). Criterios DSM-5: ≥1 síntoma "
                 "motor o sensitivo alterado + signos clínicos de incompatibilidad con enfermedad "
                 "neurológica reconocida (signo de Hoover, distractibilidad del temblor, etc.) — "
                 "NO se requiere probar conflicto psicológico. Manejo: comunicación diagnóstica "
                 "positiva, fisioterapia/TO especializada, TCC."),
    },
]

# Demencia: NO renombrar, solo agregar nota DSM-5
DEMENCIA_NOTA = ("Nomenclatura DSM-5: la «demencia» se denomina ahora «trastorno neurocognitivo "
                 "mayor» (TNC mayor) con especificación de subtipo (Alzheimer, vascular, cuerpos "
                 "de Lewy, frontotemporal, etc.). Criterios: deterioro cognitivo significativo "
                 "desde un nivel previo en ≥1 dominio (atención compleja, función ejecutiva, "
                 "aprendizaje/memoria, lenguaje, perceptivo-motor o cognición social) + "
                 "interferencia con la autonomía + no por delirium ni otro trastorno mental.")

DEMENCIA_PAT = re.compile(r"\bdemencia\b", re.IGNORECASE)


def aplicar_reemplazos(texto, rename, contexto_full):
    """Aplica replacements preservando capitalización inicial cuando es trivial."""
    if not texto:
        return texto, 0
    n = 0
    for pat, repl in rename["patterns"]:
        nuevo, k = re.subn(pat, repl, texto, flags=re.IGNORECASE)
        if k:
            # Restaurar capitalización si el match empezaba con mayúscula
            for m in re.finditer(pat, texto, re.IGNORECASE):
                if m.group()[0].isupper():
                    nuevo = nuevo.replace(repl, repl[0].upper() + repl[1:], 1)
                    break
            texto = nuevo
            n += k
    # Sigla con contexto
    if rename.get("sigla") and rename.get("contexto_sigla"):
        if re.search(rename["contexto_sigla"], contexto_full, re.IGNORECASE):
            nuevo, k = re.subn(rename["sigla"], rename["sigla_repl"], texto)
            if k:
                texto = nuevo
                n += k
    return texto, n


def procesar_pregunta(q, stats):
    """Devuelve la pregunta modificada y True si cambió."""
    contexto = " ".join([
        q.get("enunciado", "") or "",
        q.get("justificacion", "") or "",
        q.get("tema_validado", "") or "",
        " ".join((op.get("texto", "") or "") for op in (q.get("opciones") or [])),
    ])
    notas_a_agregar = []
    cambios = False

    for rename in RENAMES:
        cambios_local = 0
        # Enunciado
        nuevo, k = aplicar_reemplazos(q.get("enunciado", ""), rename, contexto)
        if k:
            q["enunciado"] = nuevo
            cambios_local += k
        # Opciones
        for op in (q.get("opciones") or []):
            for campo in ("texto", "feedback"):
                if op.get(campo):
                    nuevo, k = aplicar_reemplazos(op[campo], rename, contexto)
                    if k:
                        op[campo] = nuevo
                        cambios_local += k
        # tema_validado
        nuevo, k = aplicar_reemplazos(q.get("tema_validado", ""), rename, contexto)
        if k:
            q["tema_validado"] = nuevo
            cambios_local += k
        # justificacion (también reemplaza)
        nuevo, k = aplicar_reemplazos(q.get("justificacion", ""), rename, contexto)
        if k:
            q["justificacion"] = nuevo
            cambios_local += k

        # Detección por contexto sin replacement (para agregar nota)
        match_general = False
        for pat, _ in rename["patterns"]:
            if re.search(pat, contexto, re.IGNORECASE):
                match_general = True
                break
        if rename.get("sigla") and rename.get("contexto_sigla"):
            if re.search(rename["sigla"], contexto) and re.search(rename["contexto_sigla"], contexto, re.IGNORECASE):
                match_general = True

        if match_general:
            notas_a_agregar.append(rename["nota"])
            stats[rename["key"]] += 1
            cambios = True
        elif cambios_local:
            stats[rename["key"]] += 1
            cambios = True

    # Demencia: nota DSM-5 si menciona demencia
    if DEMENCIA_PAT.search(contexto):
        notas_a_agregar.append(DEMENCIA_NOTA)
        stats["demencia"] += 1
        cambios = True

    if notas_a_agregar:
        prefijo = "  ".join("[Nota de nomenclatura] " + n for n in notas_a_agregar)
        just_actual = q.get("justificacion", "") or ""
        if not just_actual.startswith("[Nota de nomenclatura]"):
            q["justificacion"] = prefijo + "\n\n" + just_actual

    return q, cambios


def procesar_caso(caso, stats):
    """Procesa un caso clínico igual que las preguntas."""
    contexto_partes = [caso.get("titulo", ""), caso.get("resumen_final", ""), caso.get("tema", "")]
    for et in caso.get("etapas", []) or []:
        contexto_partes.append(et.get("enunciado", "") or "")
        for op in et.get("opciones", []) or []:
            contexto_partes.append((op.get("texto", "") or "") + " " + (op.get("feedback", "") or ""))
    contexto = " ".join(contexto_partes)
    cambios = False
    notas = []

    for rename in RENAMES:
        for campo in ("titulo", "resumen_final"):
            if caso.get(campo):
                nuevo, k = aplicar_reemplazos(caso[campo], rename, contexto)
                if k:
                    caso[campo] = nuevo
                    cambios = True
        for et in caso.get("etapas", []) or []:
            if et.get("enunciado"):
                nuevo, k = aplicar_reemplazos(et["enunciado"], rename, contexto)
                if k:
                    et["enunciado"] = nuevo
                    cambios = True
            for op in et.get("opciones", []) or []:
                for campo in ("texto", "feedback"):
                    if op.get(campo):
                        nuevo, k = aplicar_reemplazos(op[campo], rename, contexto)
                        if k:
                            op[campo] = nuevo
                            cambios = True
        # Detectar para nota
        match_general = False
        for pat, _ in rename["patterns"]:
            if re.search(pat, contexto, re.IGNORECASE):
                match_general = True
                break
        if match_general:
            notas.append(rename["nota"])
            stats[rename["key"]] += 1
            cambios = True

    if DEMENCIA_PAT.search(contexto):
        notas.append(DEMENCIA_NOTA)
        stats["demencia"] += 1
        cambios = True

    if notas and caso.get("resumen_final"):
        prefijo = "  ".join("[Nota de nomenclatura] " + n for n in notas)
        if not caso["resumen_final"].startswith("[Nota de nomenclatura]"):
            caso["resumen_final"] = prefijo + "\n\n" + caso["resumen_final"]

    return cambios


def main():
    banco = json.load(open(BANCO))
    casos = json.load(open(CASOS))
    defs  = json.load(open(DEFS))

    stats = {r["key"]: 0 for r in RENAMES}
    stats["demencia"] = 0

    cambios_preg = 0
    for q in banco.get("preguntas", []):
        _, cambio = procesar_pregunta(q, stats)
        if cambio:
            cambios_preg += 1

    cambios_caso = 0
    for c in casos.get("casos", []):
        if procesar_caso(c, stats):
            cambios_caso += 1

    # === Definiciones nuevas (10) ===
    nuevas_defs = [
        {
            "id": "DEF-NOM-001",
            "termino": "Síndrome de ovario poliendocrino metabólico (SOPEM)",
            "tipo": "concepto",
            "categoria": "ginecología/endocrino",
            "definicion": ("Nueva denominación del antiguo síndrome de ovario poliquístico (SOP), "
                           "introducida por el consenso internacional 2023 para resaltar el componente "
                           "metabólico (resistencia insulínica, dislipidemia, riesgo cardiovascular). "
                           "Criterios de Rotterdam vigentes (2 de 3 + exclusión de otras causas): "
                           "oligo/anovulación, hiperandrogenismo clínico o bioquímico, morfología "
                           "ovárica poliquística (≥20 folículos por ovario y/o volumen >10 mL en "
                           "ecografía transvaginal de alta resolución). "
                           "Manejo: estilo de vida, metformina, anticonceptivos combinados; "
                           "letrozol/clomifeno si busca embarazo."),
            "fuente": "International evidence-based guideline for assessment and management of PCOS, 2023.",
        },
        {
            "id": "DEF-NOM-002",
            "termino": "Síndrome de disfunción metabólica",
            "tipo": "concepto",
            "categoria": "medicina interna/endocrino",
            "definicion": ("Nueva denominación del síndrome metabólico, reflejando el continuo "
                           "fisiopatológico de resistencia insulínica e inflamación de bajo grado más "
                           "que un agrupamiento estático de criterios. Definición operacional "
                           "(ATP-III modificada / IDF, vigente): ≥3 de — perímetro abdominal aumentado "
                           "según etnia, TG ≥150 mg/dL, HDL bajo (<40 H, <50 M), PA ≥130/85 o "
                           "tratamiento antihipertensivo, glicemia en ayunas ≥100 mg/dL o DM. "
                           "Riesgo CV y de DM2 elevado; manejo: dieta mediterránea, ejercicio, "
                           "pérdida de peso, tratar componentes específicos."),
            "fuente": "ATP-III; IDF consensus; AHA/ACC scientific statement.",
        },
        {
            "id": "DEF-NOM-003",
            "termino": "Enfermedad hepática esteatósica asociada a disfunción metabólica (MASLD)",
            "tipo": "concepto",
            "categoria": "gastroenterología",
            "definicion": ("Reemplazo de NAFLD (esteatosis hepática no alcohólica). Si hay "
                           "inflamación y daño hepatocitario: MASH (antes NASH). Diagnóstico: "
                           "esteatosis hepática por imagen/biopsia + ≥1 criterio cardiometabólico "
                           "(IMC ≥25 o perímetro abdominal aumentado, glicemia ≥100/HbA1c ≥5,7% o "
                           "DM, PA ≥130/85 o tratamiento, TG ≥150, HDL bajo). Si hay consumo "
                           "alcohólico moderado: MetALD. "
                           "Manejo: pérdida de peso 7-10% (resuelve MASH en muchos), control "
                           "cardiometabólico, semaglutida (off-label), resmetirom aprobado en "
                           "MASH F2-F3."),
            "fuente": "AASLD-EASL-ALEH multisociety Delphi consensus, Hepatology 2023.",
        },
        {
            "id": "DEF-NOM-004",
            "termino": "Presión arterial marcadamente elevada asintomática (AMBP)",
            "tipo": "concepto",
            "categoria": "cardiología/urgencias",
            "definicion": ("Reemplaza el término «urgencia hipertensiva» (AHA 2025). Se define como "
                           "PA ≥180/120 mmHg SIN daño agudo de órgano blanco. El cambio nominal "
                           "evita la sugerencia equívoca de tratamiento inmediato endovenoso. "
                           "Manejo: reposo 30 min, descartar síntomas de daño orgánico (cefalea "
                           "intensa, dolor torácico, déficit neurológico, disnea), reiniciar u "
                           "optimizar régimen antihipertensivo oral, seguimiento en 24-72 h. "
                           "Reducción de PA gradual (horas-días). NO usar nifedipino sublingual. "
                           "Distinguir de EMERGENCIA hipertensiva: PA elevada + daño agudo "
                           "(encefalopatía, IAM, edema pulmonar agudo, disección aórtica, "
                           "eclampsia, ACV) → UCI, antihipertensivos IV, descenso 20-25% en 1 h."),
            "fuente": "AHA/ACC Scientific Statement on Hypertensive Crises, 2025.",
        },
        {
            "id": "DEF-NOM-005",
            "termino": "Lesión renal aguda (LRA / AKI)",
            "tipo": "concepto",
            "categoria": "nefrología",
            "definicion": ("Reemplazo de «insuficiencia renal aguda» (KDIGO). Criterios: "
                           "↑creatinina sérica ≥0,3 mg/dL en 48 h, O ↑a ≥1,5× basal en 7 días, "
                           "O diuresis <0,5 mL/kg/h durante ≥6 h. Estadios: "
                           "I (1,5-1,9× o ↑0,3); II (2,0-2,9×); III (≥3× o creat ≥4 o terapia "
                           "renal de reemplazo o, en <18 años, eGFR <35). "
                           "Causas: prerrenal (50%, hipovolemia, IC, shock, AINEs/IECA en flujo "
                           "marginal), renal/intrínseca (NTA por isquemia o nefrotóxicos — "
                           "aminoglucósidos, contraste, vancomicina, cisplatino; GN; NIA), "
                           "postrenal (obstrucción bilateral o de monorreno). "
                           "Manejo: corregir causa, optimizar volemia, evitar nefrotóxicos, "
                           "ajuste de fármacos por TFG; TRR si refractario."),
            "fuente": "KDIGO Clinical Practice Guideline for AKI.",
        },
        {
            "id": "DEF-NOM-006",
            "termino": "Deficiencia de arginina-vasopresina (AVP-D)",
            "tipo": "concepto",
            "categoria": "endocrino",
            "definicion": ("Nueva denominación de «diabetes insípida central» (consenso 2022-2023, "
                           "respaldado por The Lancet, AACE, ENEA, etc.). Su contraparte renal "
                           "(antes «diabetes insípida nefrogénica») se denomina ahora «resistencia "
                           "a arginina-vasopresina» (AVP-R). El cambio evita confusión letal con "
                           "diabetes mellitus en órdenes médicas. "
                           "Clínica: poliuria hipotónica (>3 L/d, densidad <1010), polidipsia, "
                           "nicturia. "
                           "Diagnóstico: test de privación de agua; copeptina basal >21,4 pmol/L → "
                           "AVP-R; estimulación con suero hipertónico o arginina mide copeptina "
                           "para diferenciar AVP-D de polidipsia primaria (mejor precisión que el "
                           "test clásico). "
                           "Tratamiento: AVP-D → desmopresina (oral, intranasal o SC). AVP-R → "
                           "tiazidas, dieta hiposódica, AINEs, amilorida (si litio)."),
            "fuente": "Christ-Crain et al., Lancet 2022; AACE/AAP statements 2023.",
        },
        {
            "id": "DEF-NOM-007",
            "termino": "Mpox (antes monkeypox / viruela del mono)",
            "tipo": "concepto",
            "categoria": "infectología",
            "definicion": ("Renombrado por la OMS en 2022 para reducir estigmatización geográfica. "
                           "Agente: virus Orthopoxvirus (familia Poxviridae). Clados I "
                           "(antes Congo Basin, mortalidad ~3-10%) y II (antes West African, "
                           "<1%); brote multinacional 2022 fue clado IIb. "
                           "Transmisión: contacto piel/mucosas, gotitas, fómites; brote actual "
                           "predominantemente por contacto sexual (HSH). "
                           "Clínica: pródromo (fiebre, mialgias, linfadenopatía característica) "
                           "→ exantema vesículo-pustular sincrónico (mismo estadio), centrífugo o "
                           "anogenital; proctitis dolorosa frecuente en brote actual. "
                           "Diagnóstico: PCR de hisopado de lesión. "
                           "Tratamiento: soporte; tecovirimat (TPOXX) en graves o "
                           "inmunocomprometidos. Profilaxis pre y post-exposición: JYNNEOS (MVA-BN), "
                           "2 dosis SC separadas por 28 días."),
            "fuente": "OMS technical brief 2022-2024; CDC guidance.",
        },
        {
            "id": "DEF-NOM-008",
            "termino": "Colangitis biliar primaria (CBP)",
            "tipo": "concepto",
            "categoria": "gastroenterología/hepatología",
            "definicion": ("Reemplaza «cirrosis biliar primaria» (conserva sigla CBP). Cambio "
                           "nominal porque la cirrosis es una complicación tardía, no la "
                           "enfermedad. Es una colangiopatía autoinmune crónica que afecta "
                           "predominantemente a mujeres de 40-60 años, con destrucción "
                           "progresiva de conductillos biliares intrahepáticos. "
                           "Clínica: fatiga, prurito, ictericia tardía, xantomas; asociaciones — "
                           "síndrome de Sjögren, tiroiditis. "
                           "Diagnóstico (2 de 3): FA ≥1,5× normal por ≥6 meses; AMA "
                           "(antimitocondriales) ≥1:40 — específicos en >95% — o anti-sp100/gp210; "
                           "biopsia con colangitis linfocítica granulomatosa no-supurativa "
                           "(no obligatoria si serología típica). "
                           "Tratamiento: ácido ursodeoxicólico 13-15 mg/kg/d primera línea; "
                           "ácido obeticólico o bezafibrato si no responde."),
            "fuente": "EASL CPG 2017; AASLD practice guidance 2018; nomenclatura 2014 (Beuers et al.).",
        },
        {
            "id": "DEF-NOM-009",
            "termino": "Trastorno neurocognitivo mayor (TNC mayor, DSM-5)",
            "tipo": "concepto",
            "categoria": "neurología/psiquiatría",
            "definicion": ("Denominación DSM-5 que reemplaza «demencia». Subtipos: enfermedad de "
                           "Alzheimer, vascular, cuerpos de Lewy, frontotemporal, enfermedad de "
                           "Parkinson, HIV, trauma, sustancias/medicamentos, etiología múltiple. "
                           "Criterios: (a) evidencia de deterioro cognitivo significativo desde un "
                           "nivel previo de funcionamiento en ≥1 dominio cognitivo — atención "
                           "compleja, función ejecutiva, aprendizaje y memoria, lenguaje, "
                           "perceptivo-motor, cognición social — basado en preocupación del "
                           "individuo/cuidador/clínico y evaluación neuropsicológica objetiva; "
                           "(b) interfiere con la autonomía en actividades de la vida diaria; "
                           "(c) no ocurre exclusivamente en contexto de delirium; (d) no se "
                           "explica mejor por otro trastorno mental. "
                           "Variante leve = «trastorno neurocognitivo leve» (no interfiere con "
                           "autonomía). "
                           "Cribado: MMSE, MoCA, ACE-III. Estudio etiológico: TC/RM, B12, TSH, "
                           "VDRL/VIH si riesgo; LCR (biomarcadores Aβ/tau) o PET-amiloide en "
                           "casos seleccionados."),
            "fuente": "DSM-5 / DSM-5-TR; consenso APA.",
        },
        {
            "id": "DEF-NOM-010",
            "termino": "Trastorno de síntomas neurológicos funcionales (TSNF / FND)",
            "tipo": "concepto",
            "categoria": "neurología/psiquiatría",
            "definicion": ("Denominación DSM-5 e ICD-11 que reemplaza «trastorno conversivo». "
                           "Criterios DSM-5: (a) ≥1 síntoma de alteración de la función motora "
                           "voluntaria o sensitiva; (b) hallazgos clínicos que demuestran "
                           "incompatibilidad entre el síntoma y enfermedades neurológicas o "
                           "médicas reconocidas — signos positivos como signo de Hoover (debilidad "
                           "de extensión de cadera que mejora con flexión contralateral), "
                           "distractibilidad del temblor, prueba de la fuerza variable, "
                           "movimientos en zigzag al caminar, etc.; (c) el síntoma no se explica "
                           "mejor por otro trastorno; (d) causa malestar/disfunción clínicamente "
                           "significativa. NO se requiere probar estresor o conflicto "
                           "psicológico (cambio respecto a DSM-IV). "
                           "Manejo: comunicación diagnóstica positiva («tienes una alteración "
                           "real en el procesamiento, no estás fingiendo, es tratable»), "
                           "fisioterapia y terapia ocupacional especializadas en FND, TCC para "
                           "comorbilidades."),
            "fuente": "DSM-5; ICD-11; Stone J. et al., functional neurological disorder guidance.",
        },
    ]

    # Anexar al store de definiciones (sin duplicar por id)
    ids_existentes = {d.get("id") for d in defs.get("definiciones", [])}
    agregadas = 0
    for nd in nuevas_defs:
        if nd["id"] not in ids_existentes:
            defs["definiciones"].append(nd)
            agregadas += 1
    defs["meta"]["total"] = len(defs["definiciones"])
    defs["meta"]["descripcion"] = ("Definiciones de fármacos, conceptos y herramientas diagnósticas "
                                   "más preguntadas, con actualizaciones de nomenclatura 2022-2025.")
    defs["meta"]["version"] = "v2-nomenclatura"

    # Bump banco meta version
    banco["meta"]["version"] = "reconstruccion_v8_nomenclatura"
    banco["meta"]["actualizacion_nomenclatura"] = {
        "fecha": "2026-05-28",
        "preguntas_actualizadas": cambios_preg,
        "casos_actualizados": cambios_caso,
        "renames": {k: v for k, v in stats.items()},
        "fuente": ("Consensos 2014-2025 — KDIGO, AASLD-EASL-ALEH, AHA, OMS, DSM-5, "
                   "Rotterdam/PCOS guideline, AVP nomenclature consensus."),
    }
    casos["meta"]["version"] = "v2-nomenclatura"

    json.dump(banco, open(BANCO, "w"), ensure_ascii=False, indent=2)
    json.dump(casos, open(CASOS, "w"), ensure_ascii=False, indent=2)
    json.dump(defs,  open(DEFS,  "w"), ensure_ascii=False, indent=2)

    print(f"Preguntas afectadas:  {cambios_preg}")
    print(f"Casos afectados:      {cambios_caso}")
    print(f"Definiciones nuevas:  {agregadas} (total: {defs['meta']['total']})")
    print("Por rename:")
    for k, v in stats.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
