"""
Genera contenido inicial sustancial para Casos clínicos y Definiciones.

Cubre los grandes temas EUNACOM: cardio, respi, infecto, pediatria, gineco,
obstetricia, neuro, endocrino, urgencias, psiquiatría, cirugía.

Estructura JSON idéntica a la que ya consumía la app (campos del schema
de IndexedDB). El resumen final de cada caso refuerza la decisión clínica
clave para que el modo "Casos clínicos" sea formativo, no solo evaluativo.
"""
import json
import os
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HIST = lambda fuente="Guía MINSAL + Dr. Guevara", nota="Versión inicial": [{
    "version": 1,
    "fecha": date.today().isoformat(),
    "fuente": fuente,
    "nota": nota,
    "snapshot": None,
}]

IMG_VACIA = {"presente": False, "requerida": False, "data": None, "descripcion": None}


def op(letra, texto, correcta=False, feedback=None):
    d = {"letra": letra, "texto": texto, "correcta": correcta}
    if feedback:
        d["feedback"] = feedback
    return d


def etapa(orden, tipo, enunciado, opciones):
    return {"orden": orden, "tipo": tipo, "enunciado": enunciado, "opciones": opciones}


def caso(cid, titulo, especialidad, tema, dif, etapas, resumen):
    return {
        "id": cid,
        "titulo": titulo,
        "especialidad": especialidad,
        "tema": tema,
        "dificultad": dif,
        "imagen": IMG_VACIA,
        "etapas": etapas,
        "resumen_final": resumen,
        "version_actual": 1,
        "historial_ediciones": HIST(),
    }


# =============================================================================
#  CASOS CLÍNICOS
# =============================================================================
CASOS = [
    # ------------------------------------------------------------------ Cardio
    caso(
        "CASO-CARDIO-001", "Dolor torácico en adulto mayor", "cardio", "IAM", "intermedia",
        [
            etapa(1, "anamnesis",
                  "Hombre de 65 años, hipertenso y diabético, llega a urgencias por dolor torácico opresivo de 30 minutos.",
                  [
                      op("a", "Caracterizar el dolor: irradiación, factores que lo modifican y síntomas asociados", True),
                      op("b", "Preguntar por antecedentes de cirugías abdominales"),
                      op("c", "Indagar hábitos alimentarios del último mes"),
                  ]),
            etapa(2, "examen_complementario",
                  "El dolor irradia al brazo izquierdo con diaforesis. ¿Cuál es el examen inicial prioritario?",
                  [
                      op("a", "Electrocardiograma de 12 derivaciones en menos de 10 minutos", True),
                      op("b", "Radiografía de tórax antes que cualquier otra cosa"),
                      op("c", "Ecocardiograma de estrés"),
                  ]),
            etapa(3, "diagnostico",
                  "El ECG muestra supradesnivel del ST en II, III y aVF. ¿Cuál es el diagnóstico?",
                  [
                      op("a", "IAM con SDST de cara inferior", True),
                      op("b", "Angina estable"),
                      op("c", "Pericarditis"),
                  ]),
            etapa(4, "manejo",
                  "Está a 30 minutos de un centro con hemodinamia (angioplastia disponible <90 min). ¿Cuál es la conducta?",
                  [
                      op("a", "Angioplastia primaria + doble antiagregación y anticoagulación", True),
                      op("b", "Solo observación con enzimas seriadas"),
                      op("c", "Trombólisis aunque haya angioplastia disponible a tiempo"),
                  ]),
        ],
        "IAM con SDST de cara inferior. Manejo: ECG <10 min, angioplastia primaria en <90 min cuando esté disponible, doble antiagregación (AAS+ticagrelor/clopidogrel) y anticoagulación. La trombólisis se reserva si no hay angioplastia oportuna."
    ),

    caso(
        "CASO-CARDIO-002", "Disnea progresiva y edema", "cardio", "IC", "intermedia",
        [
            etapa(1, "anamnesis",
                  "Mujer de 72 años con disnea de esfuerzo progresiva, ortopnea y edema vespertino de tobillos. ¿Qué dato dirige el diagnóstico?",
                  [
                      op("a", "Ortopnea y disnea paroxística nocturna", True),
                      op("b", "Edema de tobillos aislado"),
                      op("c", "Dolor abdominal posprandial"),
                  ]),
            etapa(2, "examen_complementario",
                  "¿Cuál es el examen de elección para confirmar y medir la fracción de eyección?",
                  [
                      op("a", "Ecocardiograma transtorácico", True),
                      op("b", "Holter de 24 horas"),
                      op("c", "Test de esfuerzo convencional"),
                  ]),
            etapa(3, "manejo",
                  "FE 30% (IC con FE reducida, NYHA II-III). ¿Qué combinación modifica mortalidad?",
                  [
                      op("a", "IECA/ARNI + betabloqueador + antagonista mineralocorticoide + iSGLT2", True),
                      op("b", "Solo furosemida en dosis altas"),
                      op("c", "Antiarrítmicos clase I de mantención"),
                  ]),
        ],
        "IC-FEr (FE 30%). Los cuatro pilares que modifican la mortalidad: IECA/ARA-II o sacubitrilo-valsartán, betabloqueador (carvedilol, bisoprolol, metoprolol succinato), antagonista mineralocorticoide y iSGLT2. La furosemida mejora síntomas pero no mortalidad."
    ),

    caso(
        "CASO-CARDIO-003", "Palpitaciones e irregularidad del pulso", "cardio", "FA", "intermedia",
        [
            etapa(1, "anamnesis",
                  "Hombre de 78 años con palpitaciones desde hace 2 días, pulso irregular y RC también irregular. ¿Dato más relevante?",
                  [
                      op("a", "Hace cuánto comenzaron exactamente las palpitaciones y antecedentes de embolia previa", True),
                      op("b", "Tipo de alimentación reciente"),
                      op("c", "Cuántas horas duerme habitualmente"),
                  ]),
            etapa(2, "diagnostico",
                  "ECG: ritmo irregular sin ondas P. FC 130. ¿Diagnóstico?",
                  [
                      op("a", "Fibrilación auricular con respuesta ventricular rápida", True),
                      op("b", "Flutter auricular 2:1"),
                      op("c", "Taquicardia sinusal"),
                  ]),
            etapa(3, "manejo",
                  "PA 130/80, sin dolor torácico, sin signos de bajo gasto. ¿Conducta inicial?",
                  [
                      op("a", "Control de frecuencia con betabloqueador + evaluar anticoagulación según CHA₂DS₂-VASc", True),
                      op("b", "Cardioversión eléctrica inmediata sin más estudio"),
                      op("c", "Solo AAS"),
                  ]),
        ],
        "FA con RVR estable: priorizar control de frecuencia (beta o calcioantagonista no dihidropiridínico) y estratificar riesgo embólico con CHA₂DS₂-VASc. ≥2 en hombres / ≥3 en mujeres → anticoagulación. AAS no es suficiente."
    ),

    # --------------------------------------------------------------- Medicina interna
    caso(
        "CASO-MI-001", "Disnea súbita en mujer puérpera", "medicina_interna", "TEP", "avanzada",
        [
            etapa(1, "anamnesis",
                  "Mujer 32 años, 8 días postcesárea, debuta con disnea súbita y dolor pleurítico derecho. FC 118, FR 28, SatO₂ 89%.",
                  [
                      op("a", "Calcular probabilidad pretest de TEP (Wells/Ginebra)", True),
                      op("b", "Tratar como ansiedad puerperal"),
                      op("c", "Solicitar PAP urgente"),
                  ]),
            etapa(2, "examen_complementario",
                  "Wells >4 (alta probabilidad). ¿Examen de elección?",
                  [
                      op("a", "Angio-TC de tórax (si función renal lo permite)", True),
                      op("b", "Dímero D como única prueba — descarta TEP si negativo"),
                      op("c", "Radiografía simple de tórax para confirmar"),
                  ]),
            etapa(3, "manejo",
                  "Angio-TC confirma TEP submasivo, paciente estable.",
                  [
                      op("a", "Anticoagulación con heparina de bajo peso molecular", True),
                      op("b", "Trombólisis sistémica inmediata"),
                      op("c", "Solo observación 24 h"),
                  ]),
        ],
        "TEP en puerperio (período de alto riesgo). Con Wells alto, ir directo a angio-TC; el dímero D solo descarta cuando el pretest es bajo/intermedio. Anticoagulación estándar con HBPM; trombólisis solo si TEP masivo con inestabilidad hemodinámica."
    ),

    caso(
        "CASO-MI-002", "Tos productiva y fiebre en EPOC", "medicina_interna", "EPOC_exacerbacion", "intermedia",
        [
            etapa(1, "anamnesis",
                  "Varón 70 años, fumador 50 paquetes-año, EPOC GOLD III. 3 días con aumento de tos, expectoración purulenta y disnea mayor a la habitual.",
                  [
                      op("a", "Estamos ante una exacerbación tipo Anthonisen — evaluar criterios de gravedad", True),
                      op("b", "Es una neumonía adquirida en la comunidad obligadamente"),
                      op("c", "Esperar 7 días antes de actuar"),
                  ]),
            etapa(2, "examen_complementario",
                  "FR 26, SatO₂ 87% aire ambiental, sibilancias difusas, sin condensación a la auscultación. ¿Examen prioritario?",
                  [
                      op("a", "Gasometría arterial + radiografía de tórax", True),
                      op("b", "Espirometría de urgencia"),
                      op("c", "TAC de tórax de inmediato"),
                  ]),
            etapa(3, "manejo",
                  "GSA: pH 7.32, pCO₂ 58, HCO₃ 30. Acidosis respiratoria.",
                  [
                      op("a", "Broncodilatador inhalado + corticoide sistémico + antibiótico + VMNI (BiPAP)", True),
                      op("b", "Solo oxígeno a alto flujo sin VMNI"),
                      op("c", "Intubación inmediata"),
                  ]),
        ],
        "Exacerbación de EPOC con acidosis respiratoria. VMNI (BiPAP) es de primera línea cuando hay acidosis hipercápnica sin falla franca. Corticoide sistémico 5 días + antibiótico (presencia de los 3 criterios de Anthonisen: ↑disnea, ↑volumen y ↑purulencia)."
    ),

    caso(
        "CASO-MI-003", "Neumonía adquirida en la comunidad", "medicina_interna", "NAC", "basica",
        [
            etapa(1, "anamnesis",
                  "Mujer 58 años, fiebre 39°C, tos productiva con expectoración herrumbrosa y dolor pleurítico izquierdo de 3 días.",
                  [
                      op("a", "Aplicar score CURB-65 / CRB-65 para estratificar gravedad", True),
                      op("b", "Iniciar antibióticos sin más estudio"),
                      op("c", "Solicitar broncoscopia"),
                  ]),
            etapa(2, "examen_complementario",
                  "CRB-65 = 1 (FR 31). Radiografía con condensación en LII. ¿Conducta?",
                  [
                      op("a", "Hospitalizar para tratamiento parenteral", True),
                      op("b", "Tratamiento ambulatorio con amoxicilina vía oral"),
                      op("c", "Solicitar TAC torácica antes de tratar"),
                  ]),
            etapa(3, "manejo",
                  "¿Esquema antibiótico empírico inicial?",
                  [
                      op("a", "Ceftriaxona + azitromicina", True),
                      op("b", "Cloxacilina monoterapia"),
                      op("c", "Vancomicina + meropenem"),
                  ]),
        ],
        "NAC con criterio de hospitalización (CRB-65 ≥1 y/o requiere O₂). Esquema empírico: betalactámico (ceftriaxona) + macrólido (azitromicina) para cubrir neumococo + atípicos. La duración promedio es 5-7 días."
    ),

    # ------------------------------------------------------------------ Urgencias
    caso(
        "CASO-URG-001", "Politraumatizado por accidente vehicular", "urgencias", "ATLS", "avanzada",
        [
            etapa(1, "manejo",
                  "Hombre 28 años, conductor sin cinturón, ingresa con Glasgow 13. ¿Cuál es la prioridad inmediata?",
                  [
                      op("a", "ABCDE — Vía aérea con control cervical", True),
                      op("b", "TAC corporal total de entrada"),
                      op("c", "Esperar al especialista antes de actuar"),
                  ]),
            etapa(2, "examen_complementario",
                  "PA 90/60, FC 122, palidez. Abdomen distendido y doloroso difuso.",
                  [
                      op("a", "FAST ecográfico al lado del paciente + transfusión + cirugía si inestable", True),
                      op("b", "Lavado peritoneal diagnóstico hoy día es la primera opción"),
                      op("c", "TAC abdominal antes de cualquier maniobra"),
                  ]),
            etapa(3, "manejo",
                  "FAST positivo en pelvis y Morrison. Sigue inestable pese a fluidos.",
                  [
                      op("a", "Laparotomía exploradora de urgencia", True),
                      op("b", "Observación 6 h con monitoreo"),
                      op("c", "Angiotomografía electiva"),
                  ]),
        ],
        "Politraumatizado: ABCDE con control cervical. FAST guía decisión en paciente inestable. Si FAST positivo + inestabilidad hemodinámica → laparotomía sin TAC previo. TAC solo si está estable."
    ),

    caso(
        "CASO-URG-002", "Shock séptico de origen abdominal", "urgencias", "sepsis", "avanzada",
        [
            etapa(1, "examen_complementario",
                  "Mujer 65 años con fiebre 39°C, PA 80/40, FC 130, lactato 4 mmol/L tras dolor abdominal. ¿Diagnóstico clínico?",
                  [
                      op("a", "Shock séptico (sepsis con vasopresores y lactato > 2)", True),
                      op("b", "Shock cardiogénico"),
                      op("c", "Shock hipovolémico aislado"),
                  ]),
            etapa(2, "manejo",
                  "¿Bundle de la 1ª hora de la sepsis?",
                  [
                      op("a", "Hemocultivos + ATB empírico + cristaloides 30 mL/kg + lactato + vasopresores si PA persiste baja", True),
                      op("b", "Solo cristaloides hasta resolver hipotensión"),
                      op("c", "Esperar hemocultivos antes de iniciar ATB"),
                  ]),
            etapa(3, "diagnostico",
                  "TAC abdominal: absceso diverticular complicado. ¿Conducta?",
                  [
                      op("a", "Antibiótico de amplio espectro + drenaje (percutáneo o quirúrgico)", True),
                      op("b", "Solo antibiótico"),
                      op("c", "Solo drenaje sin antibiótico"),
                  ]),
        ],
        "Sepsis abdominal con shock. La 'hora dorada': hemocultivos, ATB empírico precoz, cristaloides 30 mL/kg, lactato seriado y vasopresores (noradrenalina) si la PA no responde. Control de foco (drenaje) es indispensable cuando hay colección."
    ),

    # ------------------------------------------------------------------ Pediatría
    caso(
        "CASO-PED-001", "Lactante con dificultad respiratoria", "pediatria", "bronquiolitis", "basica",
        [
            etapa(1, "anamnesis",
                  "Lactante de 5 meses con coriza hace 3 días, ahora con tos en accesos, sibilancias y rechazo alimentario.",
                  [
                      op("a", "Evaluar dificultad respiratoria con Score de Tal/Bierman", True),
                      op("b", "Solicitar TAC torácica de entrada"),
                      op("c", "Iniciar antibiótico empírico"),
                  ]),
            etapa(2, "diagnostico",
                  "Sibilancias difusas, retracciones subcostales, SatO₂ 92%. Tal 6/12.",
                  [
                      op("a", "Bronquiolitis aguda probable VRS", True),
                      op("b", "Neumonía bacteriana"),
                      op("c", "Asma bronquial"),
                  ]),
            etapa(3, "manejo",
                  "¿Manejo inicial recomendado?",
                  [
                      op("a", "Oxigenoterapia si SatO₂ <92%, kinesioterapia y aporte hidratación + observación", True),
                      op("b", "Salbutamol nebulizado de rutina"),
                      op("c", "Corticoide sistémico"),
                  ]),
        ],
        "Bronquiolitis: cuadro autolimitado por VRS. El manejo es de soporte (oxígeno si SatO₂ <92%, hidratación, kinesioterapia). Broncodilatadores y corticoides NO han demostrado beneficio en bronquiolitis típica."
    ),

    caso(
        "CASO-PED-002", "Convulsión febril en preescolar", "pediatria", "convulsion_febril", "basica",
        [
            etapa(1, "anamnesis",
                  "Niño de 2 años, fiebre 39.5°C, convulsión tónico-clónica generalizada de 3 minutos. Al llegar postictal somnoliento.",
                  [
                      op("a", "Identificar si reúne criterios de convulsión febril simple (edad, duración, tipo, sin foco)", True),
                      op("b", "Solicitar EEG y RMN de cerebro de urgencia"),
                      op("c", "Iniciar fenitoína de mantención"),
                  ]),
            etapa(2, "diagnostico",
                  "Convulsión <15 min, generalizada, sin foco neurológico ni signos meníngeos.",
                  [
                      op("a", "Convulsión febril simple", True),
                      op("b", "Estatus convulsivo febril"),
                      op("c", "Meningoencefalitis seguro"),
                  ]),
            etapa(3, "manejo",
                  "¿Conducta?",
                  [
                      op("a", "Estudio etiológico de la fiebre + educación familiar; no requiere anticonvulsivante crónico", True),
                      op("b", "Iniciar ácido valproico de mantención"),
                      op("c", "Punción lumbar de rutina en todo caso"),
                  ]),
        ],
        "Convulsión febril simple: 6 m – 5 años, <15 min, generalizada, sin foco. Buen pronóstico. Tratar la causa de la fiebre, educar a la familia. PL solo si hay signos meníngeos o sospecha de SNC. No requiere anticonvulsivantes crónicos."
    ),

    caso(
        "CASO-PED-003", "Diarrea aguda con deshidratación", "pediatria", "diarrea_aguda", "basica",
        [
            etapa(1, "anamnesis",
                  "Lactante de 9 meses con diarrea acuosa 8 veces/día, vómitos y rechazo alimentario hace 24 h.",
                  [
                      op("a", "Evaluar grado de deshidratación clínica (signos: pliegue, fontanela, llene capilar, mucosas)", True),
                      op("b", "Solicitar coprocultivo antes de cualquier cosa"),
                      op("c", "Iniciar antibióticos empíricos"),
                  ]),
            etapa(2, "diagnostico",
                  "Pliegue (+), mucosas secas, ojos hundidos, FC 160, llene 3 seg, irritable. Pérdida estimada 6-9%.",
                  [
                      op("a", "Deshidratación moderada", True),
                      op("b", "Deshidratación leve"),
                      op("c", "Deshidratación severa con shock"),
                  ]),
            etapa(3, "manejo",
                  "¿Tratamiento de elección?",
                  [
                      op("a", "Sales de rehidratación oral (SRO) 75 mL/kg en 4 horas, supervisado", True),
                      op("b", "Suero fisiológico EV inmediato 20 mL/kg"),
                      op("c", "Antidiarreicos como loperamida"),
                  ]),
        ],
        "Deshidratación moderada por diarrea aguda en lactante. SRO según OMS (Plan B) es el tratamiento de elección. Suero EV solo en deshidratación severa, shock, vómitos incoercibles o íleo. Loperamida está contraindicada en niños."
    ),

    # ------------------------------------------------------------------ Obstetricia
    caso(
        "CASO-OBS-001", "Cefalea y edema en embarazo de 34 semanas", "obstetricia", "preeclampsia", "intermedia",
        [
            etapa(1, "anamnesis",
                  "Primigesta de 28 años, 34 semanas. Cefalea pulsátil, edema facial y de manos hace 3 días.",
                  [
                      op("a", "Tomar PA en ambos brazos y solicitar proteinuria", True),
                      op("b", "Solo tranquilizar — es propio del 3er trimestre"),
                      op("c", "Indicar paracetamol y reevaluar en 7 días"),
                  ]),
            etapa(2, "diagnostico",
                  "PA 160/110, proteinuria 3+, plaquetas 95.000, AST 130. ROT exaltados.",
                  [
                      op("a", "Preeclampsia severa con síndrome HELLP incipiente", True),
                      op("b", "HTA crónica"),
                      op("c", "Hígado graso del embarazo"),
                  ]),
            etapa(3, "manejo",
                  "¿Conducta inmediata?",
                  [
                      op("a", "Hospitalizar, sulfato de magnesio + antihipertensivo + interrupción del embarazo", True),
                      op("b", "Reposo en casa y control en 48 h"),
                      op("c", "Antihipertensivo y continuar hasta término"),
                  ]),
        ],
        "Preeclampsia severa con HELLP. Tres pilares: profilaxis de eclampsia con sulfato de magnesio, control de PA (labetalol/hidralazina/nifedipino), interrupción del embarazo (a las 34 sem si severa). Profilaxis con corticoides para maduración pulmonar."
    ),

    caso(
        "CASO-OBS-002", "Hemorragia postparto", "obstetricia", "HPP", "avanzada",
        [
            etapa(1, "examen_complementario",
                  "Puérpera inmediata, parto vaginal hace 30 min, sangrado >1000 mL persistente. PA 95/55, FC 115, útero palpable sobre el ombligo, blando.",
                  [
                      op("a", "Diagnóstico clínico: HPP por atonía uterina", True),
                      op("b", "Retención de restos placentarios sin más datos"),
                      op("c", "Coagulación intravascular diseminada primaria"),
                  ]),
            etapa(2, "manejo",
                  "¿Conducta inicial?",
                  [
                      op("a", "Masaje uterino bimanual + oxitocina + 2 vías venosas + cristaloides + grupar/cruzar sangre", True),
                      op("b", "Solo observar y reevaluar en 30 min"),
                      op("c", "Histerectomía de entrada"),
                  ]),
            etapa(3, "manejo",
                  "Persiste sangrado tras oxitocina y misoprostol. ¿Siguiente paso?",
                  [
                      op("a", "Pabellón: revisión, taponamiento con balón intrauterino, ligaduras vasculares; histerectomía si fracasa", True),
                      op("b", "Esperar al pabellón otras 2 horas"),
                      op("c", "Solo más fluidos y continuar oxitocina"),
                  ]),
        ],
        "HPP por atonía (causa más frecuente). Manejo escalonado de las 4 T: Tono (uterotónicos: oxitocina → metilergometrina → misoprostol → carboprost), Trauma, Tejido, Trombina. Si fracasa: balón intrauterino, ligaduras o histerectomía."
    ),

    # ------------------------------------------------------------------ Ginecología
    caso(
        "CASO-GIN-001", "Dolor pélvico con leucorrea", "gineco", "EPI", "intermedia",
        [
            etapa(1, "anamnesis",
                  "Mujer 24 años, sexualmente activa, dolor pélvico bajo hace 5 días, leucorrea fétida y fiebre 38.5°C.",
                  [
                      op("a", "Sospechar EPI; examinar movilidad cervical y palpación anexial", True),
                      op("b", "Solo solicitar PAP"),
                      op("c", "Iniciar tratamiento antifúngico"),
                  ]),
            etapa(2, "examen_complementario",
                  "Dolor a movilización cervical (+), masa anexial dolorosa derecha en ecografía sugerente de absceso tubo-ovárico.",
                  [
                      op("a", "EPI complicada con absceso", True),
                      op("b", "Embarazo ectópico"),
                      op("c", "Cistitis aguda"),
                  ]),
            etapa(3, "manejo",
                  "¿Conducta?",
                  [
                      op("a", "Hospitalizar, ATB de amplio espectro EV (ceftriaxona + doxiciclina + metronidazol) ± drenaje", True),
                      op("b", "Ambulatorio con azitromicina sola"),
                      op("c", "Solo observación"),
                  ]),
        ],
        "Enfermedad pélvica inflamatoria complicada (absceso tubo-ovárico). Hospitalizar y cobertura para N. gonorrhoeae, C. trachomatis y anaerobios. Drenaje si absceso >7 cm o falla a 72 h de antibiótico. Estudio de pareja y ETS asociadas."
    ),

    # ------------------------------------------------------------------ Infectología
    caso(
        "CASO-INF-001", "Cefalea, fiebre y rigidez de nuca", "infecto", "meningitis", "avanzada",
        [
            etapa(1, "anamnesis",
                  "Adulto joven, cefalea intensa, fiebre, fotofobia y rigidez de nuca hace 12 h.",
                  [
                      op("a", "Sospecha de meningitis aguda; signos meníngeos y evaluar contraindicación de PL", True),
                      op("b", "Tomar paracetamol y reevaluar mañana"),
                      op("c", "Iniciar antiviral empírico solo"),
                  ]),
            etapa(2, "examen_complementario",
                  "Sin focalidad neurológica ni edema de papila. ¿Examen prioritario?",
                  [
                      op("a", "Punción lumbar con cultivo + gram + bioquímica del LCR", True),
                      op("b", "RMN de entrada antes que cualquier cosa"),
                      op("c", "Hemocultivos como único estudio"),
                  ]),
            etapa(3, "manejo",
                  "LCR turbio, predominio PMN, glucosa baja. ¿Manejo inicial?",
                  [
                      op("a", "Ceftriaxona + vancomicina + dexametasona, idealmente antes del 1er ATB", True),
                      op("b", "Solo aciclovir EV"),
                      op("c", "Esperar cultivo antes de iniciar tratamiento"),
                  ]),
        ],
        "Meningitis bacteriana aguda. Sin contraindicación → PL antes de imagen. Iniciar ATB empírico precoz (ceftriaxona + vancomicina) tras hemocultivos. Dexametasona disminuye secuelas neurológicas, idealmente antes o junto con el ATB. Avisar SEREMI: enfermedad de notificación obligatoria."
    ),

    # ------------------------------------------------------------------ Endocrino
    caso(
        "CASO-END-001", "Cetoacidosis diabética", "endocrino", "CAD", "avanzada",
        [
            etapa(1, "examen_complementario",
                  "Adolescente con DM1 conocida, 24 h con poliuria, vómitos y dolor abdominal. Aliento cetósico. Glicemia 480 mg/dL.",
                  [
                      op("a", "Solicitar GSA, electrolitos plasmáticos, cuerpos cetónicos en orina/sangre", True),
                      op("b", "Solo dar insulina rápida vía oral"),
                      op("c", "Esperar control glicémico ambulatorio"),
                  ]),
            etapa(2, "diagnostico",
                  "pH 7.18, HCO₃ 10, anión gap 22, cetonuria 3+, K 5.5.",
                  [
                      op("a", "Cetoacidosis diabética", True),
                      op("b", "Estado hiperglicémico hiperosmolar"),
                      op("c", "Acidosis láctica primaria"),
                  ]),
            etapa(3, "manejo",
                  "¿Pilares del tratamiento?",
                  [
                      op("a", "Suero fisiológico + insulina EV en infusión + reposición de potasio si <5.5 + buscar gatillante", True),
                      op("b", "Bicarbonato EV de rutina"),
                      op("c", "Glucosa EV antes que insulina"),
                  ]),
        ],
        "CAD: hidratación con SF, insulina EV en bomba a 0.1 U/kg/h, reposición de K (siempre antes de bajar de 5.5), corregir el déficit gradual, buscar el gatillante (infección, omisión de insulina). Bicarbonato solo si pH <6.9. Cambiar a glucosa al 5% cuando la glicemia llegue a 200-250 para evitar hipoglicemia."
    ),

    # ------------------------------------------------------------------ Neurología
    caso(
        "CASO-NEU-001", "Hemiparesia súbita", "neurologia", "ACV_isquemico", "avanzada",
        [
            etapa(1, "anamnesis",
                  "Hombre 68 años con instauración súbita hace 90 min de hemiparesia derecha y afasia. PA 170/100.",
                  [
                      op("a", "Activar código ACV — TAC sin contraste inmediato", True),
                      op("b", "Diferir TAC hasta confirmar PA controlada"),
                      op("c", "Esperar 6 h para repetir examen"),
                  ]),
            etapa(2, "examen_complementario",
                  "TAC sin contraste sin sangrado ni signos precoces extensos. NIHSS 14. Tiempo de inicio claro <4.5 h. Sin contraindicaciones.",
                  [
                      op("a", "Trombólisis EV con alteplasa + evaluación para trombectomía mecánica", True),
                      op("b", "Solo aspirina y observar"),
                      op("c", "Anticoagulación con heparina de inmediato"),
                  ]),
            etapa(3, "manejo",
                  "Tras trombólisis exitosa, ¿conducta a 24 h?",
                  [
                      op("a", "Iniciar AAS, estudio etiológico (ecocardio, doppler carótidas, Holter), rehabilitación precoz", True),
                      op("b", "Anticoagular sin estudio previo"),
                      op("c", "Continuar trombolítico 24 h más"),
                  ]),
        ],
        "ACV isquémico agudo. Ventana de trombólisis: <4.5 h tras TAC sin sangrado. Trombectomía mecánica si hay oclusión proximal hasta 6 h (extendida a 24 h en casos seleccionados). Anticoagulación se difiere por riesgo de transformación hemorrágica."
    ),

    # ------------------------------------------------------------------ Cirugía
    caso(
        "CASO-CIR-001", "Dolor abdominal en FID", "cirugia", "apendicitis", "basica",
        [
            etapa(1, "anamnesis",
                  "Hombre 22 años con dolor periumbilical migrado a FID hace 12 h, anorexia y fiebre 37.8°C.",
                  [
                      op("a", "Aplicar Alvarado / pediatric appendicitis score", True),
                      op("b", "TAC de inmediato sin más datos"),
                      op("c", "Antibiótico empírico ambulatorio"),
                  ]),
            etapa(2, "examen_complementario",
                  "Blumberg (+), McBurney positivo, leucocitos 14.000, neutrofilia. Alvarado 8.",
                  [
                      op("a", "Apendicitis aguda probable — apendicectomía", True),
                      op("b", "Antibióticos solo y observación"),
                      op("c", "Más estudio ambulatorio"),
                  ]),
            etapa(3, "manejo",
                  "¿Tratamiento?",
                  [
                      op("a", "Apendicectomía laparoscópica + ATB profiláctico perioperatorio", True),
                      op("b", "Cirugía abierta de entrada"),
                      op("c", "Tratamiento antibiótico exclusivo de ambulatorio"),
                  ]),
        ],
        "Apendicitis aguda (Alvarado 8). Apendicectomía laparoscópica es el estándar; abierta solo si no está disponible o perforada con peritonitis difusa. ATB profiláctico única dosis. Estrategia 'antibiótico solo' está en estudio y no es estándar en Chile."
    ),

    # ------------------------------------------------------------------ Psiquiatría
    caso(
        "CASO-PSQ-001", "Intento autolítico", "psiquiatria", "suicidio", "intermedia",
        [
            etapa(1, "anamnesis",
                  "Mujer 19 años traída a urgencias tras ingerir 30 comprimidos de paracetamol hace 1 hora.",
                  [
                      op("a", "Estabilizar + evaluar dosis ingerida + N-acetilcisteína según nomograma de Rumack-Matthew", True),
                      op("b", "Lavado gástrico sin más estudio"),
                      op("c", "Alta tras 2 h sin síntomas"),
                  ]),
            etapa(2, "manejo",
                  "Concentración de paracetamol confirma toxicidad.",
                  [
                      op("a", "N-acetilcisteína EV según protocolo (150 mg/kg → 50 → 100)", True),
                      op("b", "Solo carbón activado"),
                      op("c", "Hemodiálisis de entrada"),
                  ]),
            etapa(3, "manejo",
                  "Tras estabilización médica, ¿qué evaluación es prioritaria?",
                  [
                      op("a", "Evaluación de riesgo suicida actual + acompañamiento + hospitalización en salud mental", True),
                      op("b", "Alta tras compromiso verbal"),
                      op("c", "Solo control ambulatorio en 1 mes"),
                  ]),
        ],
        "Intento autolítico con paracetamol. Tratamiento específico con N-acetilcisteína (efectivo en las primeras 8 h, considerar hasta 24 h). Evaluación de riesgo suicida persistente, antecedentes, plan, accesibilidad. Hospitalización en salud mental si el riesgo es alto."
    ),
]


# =============================================================================
#  DEFINICIONES (concepto / fármaco / herramienta)
# =============================================================================

def define(did, tipo, concepto, esp, pregunta, opciones, explicacion):
    return {
        "id": did,
        "tipo": tipo,
        "concepto": concepto,
        "pregunta": pregunta,
        "opciones": opciones,
        "explicacion": explicacion,
        "especialidad": esp,
        "imagen": IMG_VACIA,
        "version_actual": 1,
        "historial_ediciones": HIST(),
    }


DEFS = [
    # --------- Fármacos
    define("DEF-FARM-001", "farmaco", "Furosemida", "cardio",
           "¿Cuál es el mecanismo de acción de la furosemida?",
           [
               op("a", "Inhibe el cotransportador Na-K-2Cl en la rama ascendente del asa de Henle", True),
               op("b", "Inhibe el cotransportador Na-Cl en el túbulo contorneado distal"),
               op("c", "Antagoniza el receptor de aldosterona en el túbulo colector"),
               op("d", "Inhibe la anhidrasa carbónica en el túbulo proximal"),
           ],
           "Furosemida: diurético de asa, inhibe Na-K-2Cl en rama ascendente gruesa del asa de Henle. Indicado en IC congestiva, edema pulmonar, hipertensión refractaria. Efectos adversos: hipokalemia, hipovolemia, ototoxicidad, hiperuricemia."),

    define("DEF-FARM-002", "farmaco", "Espironolactona", "cardio",
           "¿Cuál es la indicación principal de la espironolactona en IC con FE reducida?",
           [
               op("a", "Reducción de mortalidad en IC NYHA II-IV con FE <35%", True),
               op("b", "Solo control de edema refractario"),
               op("c", "Tratamiento del hiperaldosteronismo aislado"),
               op("d", "Prevención de litiasis renal"),
           ],
           "Espironolactona: antagonista del receptor mineralocorticoide. Reduce mortalidad en IC-FEr (RALES). Monitoreo de K y creatinina. Efecto adverso: ginecomastia (menor con eplerenona)."),

    define("DEF-FARM-003", "farmaco", "Enalapril (IECA)", "cardio",
           "¿Cuál es el efecto adverso más característico de los IECA?",
           [
               op("a", "Tos seca persistente por acumulación de bradiquinina", True),
               op("b", "Hipertensión rebote"),
               op("c", "Bradicardia severa"),
               op("d", "Hepatitis tóxica"),
           ],
           "IECA: inhiben la ECA, reducen angiotensina II. Indicación: HTA, IC, nefroprotección en DM. Efectos adversos: tos seca (10-20% por bradiquinina), angioedema, hiperkalemia, IRA en estenosis bilateral. Contraindicado en embarazo."),

    define("DEF-FARM-004", "farmaco", "Metformina", "endocrino",
           "¿Cuál es la primera línea de tratamiento farmacológico en DM2?",
           [
               op("a", "Metformina, salvo contraindicación", True),
               op("b", "Insulina basal de entrada"),
               op("c", "Sulfonilurea desde el inicio"),
               op("d", "iSGLT2 monoterapia"),
           ],
           "Metformina: biguanida, reduce gluconeogénesis hepática y mejora sensibilidad a la insulina. Primera línea en DM2. Contraindicada en TFG <30. Efecto adverso: intolerancia GI, acidosis láctica (rara). Suspender 48 h antes de contraste yodado."),

    define("DEF-FARM-005", "farmaco", "Salbutamol", "medicina_interna",
           "¿Cuál es el mecanismo del salbutamol?",
           [
               op("a", "Agonista β₂-adrenérgico → broncodilatación", True),
               op("b", "Antagonista muscarínico"),
               op("c", "Corticoide inhalado"),
               op("d", "Antileucotrieno"),
           ],
           "Salbutamol: agonista β₂ de corta acción (SABA). Broncodilatación rápida. Indicación: crisis asmática, broncoespasmo. Efectos adversos: tremor, taquicardia, hipokalemia con dosis altas."),

    define("DEF-FARM-006", "farmaco", "AAS (ácido acetilsalicílico)", "cardio",
           "¿Cuál es la dosis de AAS en el manejo agudo del IAM?",
           [
               op("a", "300 mg masticable de carga", True),
               op("b", "100 mg vía oral"),
               op("c", "500 mg vía intramuscular"),
               op("d", "Solo si hay confirmación enzimática"),
           ],
           "AAS en SCA: 162-325 mg masticable lo antes posible (irreversible inhibición de COX-1 y producción de tromboxano A2). Mantención 75-100 mg/día indefinido tras IAM."),

    define("DEF-FARM-007", "farmaco", "Heparina de bajo peso molecular", "medicina_interna",
           "¿Cuál es el monitoreo recomendado en una paciente embarazada con HBPM?",
           [
               op("a", "Anti-factor Xa", True),
               op("b", "TTPa"),
               op("c", "INR"),
               op("d", "No requiere monitoreo nunca"),
           ],
           "HBPM (enoxaparina, dalteparina): inhibe principalmente factor Xa. No prolonga TTPa de forma confiable. En embarazo, obesidad mórbida o IR se usa anti-Xa para titular dosis. Antídoto parcial: protamina."),

    define("DEF-FARM-008", "farmaco", "Ceftriaxona", "infecto",
           "¿Cuál es la cobertura empírica de ceftriaxona en meningitis bacteriana del adulto?",
           [
               op("a", "Neisseria meningitidis, S. pneumoniae y H. influenzae", True),
               op("b", "Solo gramnegativos entéricos"),
               op("c", "Solo S. aureus meticilino-resistente"),
               op("d", "Anaerobios exclusivamente"),
           ],
           "Ceftriaxona: cefalosporina de 3ª generación. Cobertura amplia para gramnegativos y la mayoría de gérmenes meníngeos típicos. En adulto se asocia vancomicina por resistencia del neumococo. En neonatos NO se usa por desplazamiento de bilirrubina."),

    define("DEF-FARM-009", "farmaco", "Morfina", "urgencias",
           "¿Cuál es el efecto adverso más relevante a vigilar en una dosis aguda de morfina EV?",
           [
               op("a", "Depresión respiratoria", True),
               op("b", "Hipertensión severa"),
               op("c", "Crisis convulsiva"),
               op("d", "Hipertermia maligna"),
           ],
           "Morfina: agonista μ. Analgesia potente. Riesgos: depresión respiratoria, hipotensión, prurito, constipación, retención urinaria. Antídoto: naloxona (vida media corta, dosis repetidas si es necesario)."),

    define("DEF-FARM-010", "farmaco", "Sulfato de magnesio", "obstetricia",
           "¿Cuál es la indicación del sulfato de magnesio en obstetricia?",
           [
               op("a", "Profilaxis y manejo de eclampsia en preeclampsia severa", True),
               op("b", "Inducción del parto"),
               op("c", "Tratamiento de la diabetes gestacional"),
               op("d", "Profilaxis de hemorragia postparto"),
           ],
           "Sulfato de magnesio: anticonvulsivante de elección en eclampsia y profilaxis en preeclampsia severa. Dosis: 4-6 g EV en 20 min + 1-2 g/h. Vigilar reflejos osteotendinosos, FR y diuresis. Antídoto: gluconato de calcio."),

    # --------- Conceptos
    define("DEF-CONC-001", "concepto", "Pulso paradójico", "cardio",
           "¿Cuál es la definición clásica de pulso paradójico?",
           [
               op("a", "Disminución >10 mmHg de la PAS en inspiración", True),
               op("b", "Pulso irregular sin onda P"),
               op("c", "Pulso fuerte en parálisis cardíaca"),
               op("d", "Equivalente al signo de Beck"),
           ],
           "Pulso paradójico: caída inspiratoria de la PAS >10 mmHg. Clásico en taponamiento cardíaco; también en asma severa, EPOC exacerbado, pericarditis constrictiva. Refleja interacción ventricular y disminución del volumen sistólico izquierdo en inspiración."),

    define("DEF-CONC-002", "concepto", "Clasificación de Killip", "cardio",
           "¿Para qué se utiliza la clasificación de Killip-Kimball?",
           [
               op("a", "Estratificar pronóstico del IAM según hallazgos de IC", True),
               op("b", "Clasificar gravedad de FA"),
               op("c", "Evaluar profundidad de la trombosis"),
               op("d", "Clasificar hipertensión pulmonar"),
           ],
           "Killip-Kimball (1967): estratificación pronóstica del IAM. I sin signos de IC, II crépitos basales y/o R3, III edema pulmonar agudo, IV shock cardiogénico. A mayor clase, mayor mortalidad."),

    define("DEF-CONC-003", "concepto", "Triada de Beck", "cardio",
           "¿Qué incluye la triada de Beck (taponamiento cardíaco)?",
           [
               op("a", "Hipotensión, ingurgitación yugular, ruidos cardíacos apagados", True),
               op("b", "Disnea, dolor torácico, ortopnea"),
               op("c", "Cianosis, taquicardia, sudoración"),
               op("d", "Edema, oliguria, hipertensión"),
           ],
           "Triada de Beck: tres signos clásicos del taponamiento cardíaco — hipotensión, ingurgitación yugular y ruidos cardíacos apagados. Diagnóstico clínico apoyado por ecocardiograma. Tratamiento: pericardiocentesis."),

    define("DEF-CONC-004", "concepto", "Sepsis (Sepsis-3)", "urgencias",
           "Según la definición Sepsis-3, ¿qué define a la sepsis?",
           [
               op("a", "Disfunción orgánica potencialmente mortal por respuesta desregulada a infección (SOFA ≥2)", True),
               op("b", "Solo presencia de hemocultivos positivos"),
               op("c", "SIRS con foco infeccioso conocido"),
               op("d", "Fiebre >38°C con neutrofilia"),
           ],
           "Sepsis-3 (2016): infección + ↑SOFA ≥2 puntos. Shock séptico: sepsis + necesidad de vasopresores para PAM ≥65 + lactato >2 a pesar de resucitación. SIRS quedó deprecado para definir sepsis."),

    define("DEF-CONC-005", "concepto", "Score de Wells (TEP)", "medicina_interna",
           "¿Qué hace operativamente el score de Wells para TEP?",
           [
               op("a", "Estratifica probabilidad pretest de TEP para decidir entre dímero D o angio-TC", True),
               op("b", "Confirma TEP por sí solo"),
               op("c", "Mide la severidad hemodinámica"),
               op("d", "Reemplaza al angio-TC"),
           ],
           "Wells para TEP: estima probabilidad pretest. Probabilidad baja → dímero D; si normal, descarta. Alta probabilidad → angio-TC directo. Categorías: ≤4 'TEP poco probable', >4 'TEP probable'."),

    define("DEF-CONC-006", "concepto", "Criterios de Ranson", "cirugia",
           "¿Para qué sirven los criterios de Ranson?",
           [
               op("a", "Estratificar severidad de la pancreatitis aguda", True),
               op("b", "Clasificar la severidad de la colecistitis"),
               op("c", "Predecir riesgo de cáncer pancreático"),
               op("d", "Evaluar respuesta al tratamiento de PA"),
           ],
           "Ranson (1974): 5 criterios al ingreso + 6 a las 48 h. ≥3 indica pancreatitis severa con mayor mortalidad. APACHE-II y BISAP son más usados actualmente pero Ranson sigue siendo evaluado en EUNACOM."),

    define("DEF-CONC-007", "concepto", "Escala de Glasgow", "neurologia",
           "¿Cuál es el rango y los componentes de la escala de Glasgow?",
           [
               op("a", "3-15 puntos: apertura ocular (1-4), verbal (1-5), motora (1-6)", True),
               op("b", "0-20 puntos: motor, sensitivo, autonómico"),
               op("c", "1-10 puntos: respuesta al dolor, pupilas, FC"),
               op("d", "5-20 puntos: lenguaje, marcha, equilibrio"),
           ],
           "Glasgow: estandariza nivel de conciencia. 13-15 leve, 9-12 moderado, ≤8 grave (vía aérea segura indicada). Útil en TCE y otras causas de compromiso de conciencia. Considerar sedación y limitaciones."),

    define("DEF-CONC-008", "concepto", "NIHSS", "neurologia",
           "¿Qué evalúa el NIHSS en ACV?",
           [
               op("a", "Severidad del déficit neurológico (0-42 puntos)", True),
               op("b", "Riesgo de transformación hemorrágica"),
               op("c", "Pronóstico funcional a largo plazo aislado"),
               op("d", "Indicación absoluta de trombectomía"),
           ],
           "NIHSS (National Institutes of Health Stroke Scale): 15 ítems, 0-42 puntos. Estratifica déficit en ACV agudo. Útil para decisiones de trombólisis y trombectomía (>6 sugiere oclusión proximal). Permite seguimiento."),

    define("DEF-CONC-009", "concepto", "Criterios de Light", "medicina_interna",
           "¿Cuál es el criterio de Light que define exudado pleural?",
           [
               op("a", "Proteínas líquido/suero >0.5 ó LDH líquido/suero >0.6 ó LDH líquido > 2/3 del límite superior sérico", True),
               op("b", "Glucosa <60 mg/dL exclusivamente"),
               op("c", "Linfocitosis >50%"),
               op("d", "Conteo celular >1000"),
           ],
           "Criterios de Light (1972): diferencian exudado (≥1 criterio) de trasudado (ninguno). Alta sensibilidad para exudado. Exudado: infecciones, neoplasias, TEP, conectivopatías. Trasudado: IC, cirrosis, síndrome nefrótico."),

    define("DEF-CONC-010", "concepto", "FAST", "urgencias",
           "¿Qué evalúa el FAST en trauma?",
           [
               op("a", "Líquido libre en 4 ventanas: pericárdica, hepatorrenal, esplenorrenal, pelvis", True),
               op("b", "Fractura de costillas y vértebras"),
               op("c", "Solo el corazón en pacientes inestables"),
               op("d", "Solo el espacio pleural"),
           ],
           "FAST (Focused Assessment with Sonography for Trauma): identifica hemoperitoneo y hemopericardio al lado del paciente, en pocos minutos. Si FAST positivo en politrauma inestable → laparotomía sin TAC. eFAST agrega ventanas pleurales (neumotórax, hemotórax)."),

    # --------- Herramientas diagnósticas
    define("DEF-HERR-001", "herramienta", "BNP / NT-proBNP", "cardio",
           "¿Cuál es la utilidad del BNP en disnea aguda?",
           [
               op("a", "Diferenciar disnea de causa cardíaca (alto) vs pulmonar (bajo)", True),
               op("b", "Diagnostica TEP"),
               op("c", "Mide directamente la fracción de eyección"),
               op("d", "Sustituye al ecocardiograma"),
           ],
           "BNP/NT-proBNP: secretados por miocardio en estrés parietal. Útiles para descartar IC en disnea aguda (BNP <100 ó NT-proBNP <300 hace IC improbable). Niveles altos también en TEP, IRA y edad avanzada (precaución)."),

    define("DEF-HERR-002", "herramienta", "Troponinas cardíacas", "cardio",
           "¿Cuál es el rol de las troponinas en el SCA?",
           [
               op("a", "Marcadores específicos de injuria miocárdica para diagnóstico y pronóstico", True),
               op("b", "Solo se elevan en IAM con SDST"),
               op("c", "Diagnostican estenosis coronaria estable"),
               op("d", "Equivalen a un cateterismo"),
           ],
           "Troponinas T/I: gold standard para diagnóstico de injuria miocárdica. Elevación + cambios clínicos/EKG → SCA. Considerar troponina alta sensibilidad seriada (0 h y 1-3 h). Elevación también en miocarditis, TEP, IC severa, sepsis."),

    define("DEF-HERR-003", "herramienta", "Electrocardiograma de 12 derivaciones", "cardio",
           "¿Cuál es la utilidad principal del ECG inicial en dolor torácico?",
           [
               op("a", "Identificar SDST/IDST y arritmias en <10 minutos del ingreso", True),
               op("b", "Confirmar oclusión coronaria por sí solo"),
               op("c", "Reemplazar a las troponinas"),
               op("d", "Estimar la FE"),
           ],
           "ECG en dolor torácico: clave para clasificar SCA-SDST vs SCA-NSDST y detectar arritmias. ECG normal NO descarta IAM. Repetir si persiste sospecha o cambios clínicos. Comparar con ECG previos."),

    define("DEF-HERR-004", "herramienta", "Hemoglobina glicosilada", "endocrino",
           "¿Cuál es el corte diagnóstico de DM con HbA1c?",
           [
               op("a", "≥6.5% confirmada en dos ocasiones (o con clínica)", True),
               op("b", "≥5.0%"),
               op("c", "≥7.0%"),
               op("d", "≥8.5%"),
           ],
           "HbA1c: refleja glicemia promedio de los últimos 2-3 meses. Diagnóstico de DM ≥6.5%. Prediabetes 5.7-6.4%. Falsamente baja en anemia, hemólisis, embarazo. Falsamente alta en alcoholismo, IRC."),

    define("DEF-HERR-005", "herramienta", "Gasometría arterial", "medicina_interna",
           "¿Qué evalúa la gasometría arterial?",
           [
               op("a", "Oxigenación, ventilación y equilibrio ácido-base", True),
               op("b", "Solo la oxigenación"),
               op("c", "Solo el pH"),
               op("d", "Equivale al hemograma"),
           ],
           "GSA: pH, pCO₂, pO₂, HCO₃, exceso de base, lactato. Permite diagnóstico de insuficiencia respiratoria (pO₂ <60), hipercapnia, alteraciones del equilibrio ácido-base. PaO₂/FiO₂ orienta a SDRA. Hipoxemia se evalúa con A-a gradient."),

    define("DEF-HERR-006", "herramienta", "Lactato sérico", "urgencias",
           "¿Qué refleja el lactato elevado en un paciente crítico?",
           [
               op("a", "Hipoperfusión tisular y mal pronóstico — especialmente >4 mmol/L", True),
               op("b", "Solo deshidratación"),
               op("c", "Función renal"),
               op("d", "Estado nutricional"),
           ],
           "Lactato: marcador de hipoperfusión tisular y metabolismo anaerobio. >2 mmol/L sugestivo, >4 mmol/L se asocia a alta mortalidad en sepsis. Útil para definir resucitación y monitorización seriada."),

    define("DEF-HERR-007", "herramienta", "Dímero D", "medicina_interna",
           "¿Cuál es el valor predictivo del dímero D en TEP?",
           [
               op("a", "Alto valor predictivo NEGATIVO — descarta TEP en probabilidad baja-intermedia", True),
               op("b", "Alta especificidad — confirma TEP"),
               op("c", "Diagnóstico definitivo si está alto"),
               op("d", "Equivale al angio-TC"),
           ],
           "Dímero D: producto de degradación de fibrina. Alta sensibilidad pero baja especificidad. Útil para descartar TEP cuando Wells/Geneva es bajo/intermedio. Falsamente elevado en embarazo, post-cirugía, cáncer, edad avanzada."),

    define("DEF-HERR-008", "herramienta", "PCR (proteína C reactiva)", "infecto",
           "¿Qué información aporta la PCR en infección?",
           [
               op("a", "Marcador inespecífico de inflamación, útil para seguimiento", True),
               op("b", "Diagnóstico específico de bacteriemia"),
               op("c", "Indica resistencia antibiótica"),
               op("d", "Sustituye al hemocultivo"),
           ],
           "PCR: reactante de fase aguda. Inespecífica (infección, autoinmune, neoplasia). Útil para seguimiento de respuesta a tratamiento. Procalcitonina es más específica para infección bacteriana grave."),

    define("DEF-HERR-009", "herramienta", "Tomografía con vs. sin contraste", "urgencias",
           "¿Cuándo NO usar contraste yodado en TAC?",
           [
               op("a", "Sospecha de sangrado agudo del SNC; alergia severa al yodo; ERC sin protección renal", True),
               op("b", "Siempre que se busque trauma"),
               op("c", "En todo abdomen agudo sin excepción"),
               op("d", "Nunca: el contraste no agrega información"),
           ],
           "TAC sin contraste: sangrado SNC (HSA, hemorragia intracraneal), litiasis renal, planificación de TAC con contraste. Contraste yodado: caracteriza tumores, vasos (angio-TC), procesos inflamatorios. Precauciones: ERC (TFG <30), alergias, hipertiroidismo."),

    define("DEF-HERR-010", "herramienta", "Ecocardiograma transtorácico", "cardio",
           "¿Cuál es la primera utilidad del ecocardiograma en disnea aguda con sospecha de IC?",
           [
               op("a", "Medir fracción de eyección y evaluar disfunción diastólica y valvulopatías", True),
               op("b", "Diagnostica TEP definitivamente"),
               op("c", "Mide la PA central"),
               op("d", "Sustituye al cateterismo"),
           ],
           "Ecocardiograma TT: examen no invasivo de elección en IC. Fracción de eyección, función diastólica, valvulopatías, derrame pericárdico, hipertensión pulmonar. Diferencia IC-FEr (≤40%) de IC-FEp (≥50%)."),
]


# =============================================================================
# Escritura
# =============================================================================
casos_out = {
    "meta": {
        "version": "v1",
        "descripcion": "Set inicial de casos clínicos paso a paso para los temas más preguntados en EUNACOM.",
        "total": len(CASOS),
    },
    "casos": CASOS,
}
defs_out = {
    "meta": {
        "version": "v1",
        "descripcion": "Definiciones de fármacos, conceptos y herramientas diagnósticas más preguntadas.",
        "total": len(DEFS),
    },
    "definiciones": DEFS,
}

with open(os.path.join(ROOT, "data/casos_iniciales.json"), "w", encoding="utf-8") as f:
    json.dump(casos_out, f, ensure_ascii=False, indent=2)
with open(os.path.join(ROOT, "data/definiciones_iniciales.json"), "w", encoding="utf-8") as f:
    json.dump(defs_out, f, ensure_ascii=False, indent=2)

print(f"Casos: {len(CASOS)}")
print(f"Definiciones: {len(DEFS)}")
print(f"  fármacos: {sum(1 for d in DEFS if d['tipo']=='farmaco')}")
print(f"  conceptos: {sum(1 for d in DEFS if d['tipo']=='concepto')}")
print(f"  herramientas: {sum(1 for d in DEFS if d['tipo']=='herramienta')}")
