#!/usr/bin/env python3
"""Genera 10 definiciones de guías clínicas 2024-2026 + casos asociados.

Sintetiza contenido desde fuente primaria de 10 actualizaciones clave
y lo anexa a definiciones_iniciales.json y casos_iniciales.json.
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
CASOS = ROOT / "data" / "casos_iniciales.json"
DEFS  = ROOT / "data" / "definiciones_iniciales.json"

# ============================================================
# DEFINICIONES DE GUÍAS (10)
# ============================================================
DEFS_GUIAS = [
    {
        "id": "DEF-GUIA-001",
        "termino": "GINA 2026 — Manejo del asma",
        "tipo": "guia",
        "categoria": "pulmonar",
        "definicion": (
            "GINA 2026 (Global Initiative for Asthma) — actualización mayo 2026.\n\n"
            "CAMBIOS CLAVE 2026:\n"
            "• SABA en monoterapia ELIMINADO en todos los escalones (toda exposición a "
            "SABA debe acompañarse de ICS).\n"
            "• AIR con ICS-SABA formalmente incorporado al Step 1 del Track 2 (estudio "
            "BATURA: redujo exacerbaciones graves ~50% vs SABA solo).\n"
            "• Saturación O₂ objetivo 93–95% (no >95%) en adultos, adolescentes y niños 6–11.\n"
            "• Nuevos biológicos: depemokimab (anti-IL-5 ultra-prolongado, SC c/26 semanas, "
            "≥12 años con asma eosinofílica grave) y omalizumab-igec (biosimilar anti-IgE).\n"
            "• 4 flowcharts nuevos de exacerbación (atención primaria y urgencias).\n\n"
            "TRACK 1 — PREFERIDO (ICS-formoterol como rescate, AIR/MART):\n"
            "• Steps 1–2: budesónida-formoterol 200/6 (o 160/4,5) a demanda.\n"
            "• Step 3: budesónida-formoterol 200/6, 1 inh c/12h + a demanda (MART dosis baja).\n"
            "• Step 4: budesónida-formoterol 200/6, 2 inh c/12h + a demanda (MART dosis media).\n"
            "• Step 5: añadir LAMA (tiotropio 5 µg/d) + derivar a fenotipado + biológico.\n\n"
            "TRACK 2 — ALTERNATIVO (rescate con SABA o ICS-SABA):\n"
            "• Step 1 (NUEVO): ICS-SABA a demanda (budesónida-albuterol 80/180, 1–2 inh).\n"
            "• Step 2: ICS dosis baja diaria + rescate.\n"
            "• Step 3: ICS-LABA dosis baja + rescate.\n"
            "• Step 4: ICS-LABA dosis media + rescate ± LAMA.\n"
            "• Step 5: ICS-LABA dosis alta + LAMA + biológico.\n\n"
            "EXACERBACIÓN AGUDA (adultos/adolescentes):\n"
            "• Salbutamol 4–10 puffs con aerocámara c/20 min × 1 h.\n"
            "• Oxígeno controlado, meta SpO₂ 93–95%.\n"
            "• Ipratropio 4–8 puffs (o 0,5 mg nebulizado) c/20 min × 3 en moderada-grave.\n"
            "• Prednisona 40–50 mg VO × 5–7 días (adultos) o 1–2 mg/kg/d × 3–5 d (niños).\n"
            "• Sulfato de Mg 2 g IV en 20 min en grave refractaria.\n"
            "• NO antibióticos rutinarios.\n\n"
            "BIOLÓGICOS PARA ASMA SEVERA — qué fenotipo a cuál:\n"
            "• Omalizumab: alérgica + IgE 30–1500 UI/mL, ≥6 años.\n"
            "• Mepolizumab: eosinofílica (eos ≥150 si OCS-dep o ≥300 último año), ≥6 a; 100 mg SC c/4 sem.\n"
            "• Benralizumab: eosinofílica; 30 mg SC c/4 sem × 3 luego c/8 sem.\n"
            "• Dupilumab: T2-alta (eos ≥150 y/o FeNO ≥25), especial si dermatitis atópica o "
            "poliposis nasal; 200–300 mg SC c/2 sem.\n"
            "• Tezepelumab: asma grave con o sin fenotipo T2 (única opción T2-baja); "
            "210 mg SC c/4 sem, ≥12 a.\n"
            "• Depemokimab (NUEVO 2026): eosinofílica grave, ≥12 a; SC c/26 semanas."
        ),
        "fuente": "GINA 2026 Strategy Report — ginasthma.org/2026-gina-strategy-report/",
        "vigencia": "2026",
    },
    {
        "id": "DEF-GUIA-002",
        "termino": "GOLD 2026 — Manejo de EPOC",
        "tipo": "guia",
        "categoria": "pulmonar",
        "definicion": (
            "GOLD 2026 (Global Initiative for COPD) — vigente desde diciembre 2025.\n\n"
            "CAMBIOS CLAVE 2026:\n"
            "• Grupo E ahora incluye pacientes con ≥1 exacerbación moderada O grave/año "
            "(antes ≥2 moderadas o ≥1 grave).\n"
            "• Adopción de criterios de Roma para clasificar severidad de exacerbaciones.\n"
            "• Vacuna PCV21 incorporada junto a PCV20.\n"
            "• Nuevo capítulo de tecnologías (telemedicina, IA, dispositivos portátiles).\n"
            "• Advertencia explícita: NO escalar farmacoterapia tras LABA+LAMA si persiste "
            "disnea sin antes revisar técnica inhalatoria, rehabilitación y comorbilidades.\n\n"
            "DIAGNÓSTICO: FEV1/FVC <0,70 POST-broncodilatador + síntomas + factor de "
            "riesgo. Severidad GOLD 1–4 por FEV1 post-BD: ≥80, 50–79, 30–49, <30.\n\n"
            "GRUPOS ABE (eliminado C y D):\n"
            "• A: 0 exacerbaciones último año + mMRC 0–1 (CAT <10).\n"
            "• B: 0 exacerbaciones + mMRC ≥2 (CAT ≥10).\n"
            "• E: ≥1 exacerbación moderada o ≥1 grave (hospitalización), independiente de síntomas.\n\n"
            "TRATAMIENTO INICIAL:\n"
            "• A: un broncodilatador (LAMA o LABA).\n"
            "• B: LABA + LAMA en inhalador único.\n"
            "• E: LABA + LAMA; añadir ICS (triple terapia) si eosinófilos sangre ≥300 céls/µL "
            "(fenotipo eosinofílico).\n"
            "• ICS NO recomendado si eos <100 o antecedente de neumonías a repetición o "
            "micobacterias.\n"
            "• Biológicos (dupilumab, mepolizumab) si exacerbaciones persisten en triple terapia "
            "con eos ≥300.\n\n"
            "EXACERBACIÓN (criterios de Roma): empeoramiento agudo ≤14 días.\n"
            "• Leve: aumentar SABA/SAMA.\n"
            "• Moderada/grave: SABA + ipratropio + prednisona 40 mg/d × 5 días + O₂ "
            "controlado (SpO₂ 88–92%) + VNI si pH <7,35 y PaCO₂ >45.\n"
            "• Antibióticos × 5 días si: 3 criterios de Anthonisen, 2 con purulencia, o "
            "ventilación mecánica. Opciones: amoxi-clav, macrólido, doxiciclina; "
            "fluoroquinolona si riesgo Pseudomonas.\n\n"
            "VACUNAS 2026:\n"
            "• Influenza anual.\n"
            "• Neumococo: PCV20 o PCV21 dosis única (alternativa PCV13/15 + PPSV23).\n"
            "• COVID-19 según esquema local.\n"
            "• VSR ≥50 años con enfermedad pulmonar crónica.\n"
            "• Herpes zóster (Shingrix 2 dosis), Tdap.\n\n"
            "CESACIÓN TABÁQUICA (estándar referenciado):\n"
            "• Vareniclina (más eficaz): 0,5 → 1 mg c/12h × 12 sem.\n"
            "• Bupropión SR: 150 mg/d × 3 d → 150 mg c/12h × 7–12 sem.\n"
            "• TRN: parche + chicle/comprimido de rescate.\n"
            "• Citisina como alternativa emergente."
        ),
        "fuente": "GOLD 2026 Report — goldcopd.org/2026-gold-report-and-pocket-guide/",
        "vigencia": "2026",
    },
    {
        "id": "DEF-GUIA-003",
        "termino": "ESC 2024 — Fibrilación auricular y esquema AF-CARE",
        "tipo": "guia",
        "categoria": "cardiología",
        "definicion": (
            "ESC/EACTS 2024 Guidelines on Atrial Fibrillation — vigente.\n\n"
            "CAMBIOS CLAVE vs ESC 2020:\n"
            "• Nuevo esquema AF-CARE reemplaza al «ABC pathway».\n"
            "• CHA₂DS₂-VASc → CHA₂DS₂-VA (eliminado sexo como criterio independiente).\n"
            "• Ablación con catéter Clase I como PRIMERA LÍNEA en FA paroxística (antes IIa).\n"
            "• Cierre de orejuela (LAAC) sube a Clase IIa en contraindicación a OAC.\n"
            "• Anticoagulación de FA subclínica (AHRE/SCAF) recomendación IIb-B en alto "
            "riesgo embólico + bajo riesgo hemorrágico (tras NOAH-AFNET 6 y ARTESiA).\n"
            "• Reducción ≥10% de peso explícita como meta en obesos con FA.\n\n"
            "ESQUEMA AF-CARE (cada letra es un pilar):\n"
            "• [C] Comorbidity & risk factor management — HTA, IC, DM, obesidad ≥10%, "
            "apnea del sueño, alcohol, actividad física.\n"
            "• [A] Avoid stroke and thromboembolism — anticoagulación según CHA₂DS₂-VA.\n"
            "• [R] Reduce symptoms — control de frecuencia/ritmo, ablación temprana.\n"
            "• [E] Evaluation and dynamic reassessment — reevaluar fenotipo periódicamente.\n\n"
            "ANTICOAGULACIÓN — Umbrales CHA₂DS₂-VA:\n"
            "• 0 → no anticoagular.\n"
            "• 1 → considerar OAC (IIa).\n"
            "• ≥2 → OAC recomendado (I).\n\n"
            "DOACs preferidos sobre warfarina, EXCEPTO en válvula mecánica o estenosis "
            "mitral moderada-severa (warfarina INR 2-3).\n\n"
            "DOSIS DOACs (FANV):\n"
            "• Apixabán 5 mg c/12h; 2,5 c/12h si ≥2 de: ≥80 a, ≤60 kg, Cr ≥1,5 mg/dL.\n"
            "• Rivaroxabán 20 mg/d; 15 mg/d si ClCr 15–49.\n"
            "• Edoxabán 60 mg/d; 30 mg/d si ClCr 15–50, ≤60 kg o inhibidor P-gp.\n"
            "• Dabigatrán 150 mg c/12h; 110 mg c/12h si ≥80 a, HAS-BLED ≥3, ClCr 30–50.\n\n"
            "REVERSIÓN:\n"
            "• Idarucizumab 5 g IV → dabigatrán.\n"
            "• Andexanet alfa → apix/rivaroxabán en sangrado mayor "
            "(ANNEXA-I 2024: mejor hemostasia pero ↑eventos trombóticos 10,3% vs 5,6%).\n"
            "• CCP 4F (50 UI/kg) → alternativa o edoxabán (sin antídoto específico).\n\n"
            "CONTROL DE RITMO vs FRECUENCIA:\n"
            "• Frecuencia: meta laxa <110 lpm; estricta <80 si síntomas. Primera línea betabloqueante.\n"
            "• Ritmo: si sintomático o IC. ABLACIÓN Clase I en FA paroxística y FA + IC con FEVI "
            "reducida (CASTLE-AF).\n\n"
            "FA SUBCLÍNICA (SCAF/AHRE detectada por dispositivos):\n"
            "• Anticoagular IIb-B si alto riesgo embólico + bajo riesgo hemorrágico.\n"
            "• Episodios <6 min no requieren OAC.\n\n"
            "TRIPLE/DUAL TERAPIA EN SCA + FA:\n"
            "• Triple (AAS + clopidogrel + DOAC): HASTA 1 SEMANA post-ICP.\n"
            "• Dual (DOAC + clopidogrel): hasta 12 meses.\n"
            "• Después: DOAC solo."
        ),
        "fuente": "Van Gelder IC, et al. Eur Heart J 2024;45:3314–3414.",
        "vigencia": "2024",
    },
    {
        "id": "DEF-GUIA-004",
        "termino": "Anticoagulación 2024-2026 — DOACs, reversión y manejo del sangrado",
        "tipo": "guia",
        "categoria": "cardiología/hematología",
        "definicion": (
            "NOTA: no existe guía ESC 2026 específica sobre anticoagulación (ESC Congress "
            "2026: Múnich, ago 2026). Síntesis basada en ESC AF 2024, ESC PE 2019, ESC "
            "Valvular 2021/2025, CHEST 2024 antitrombóticos y AHA/ACC PE 2026.\n\n"
            "DOSIS DE TRATAMIENTO DOACs PARA TVP/TEP:\n"
            "• Apixabán: 10 mg c/12h × 7 días → 5 mg c/12h. Extendido (>6 m): 2,5 mg c/12h.\n"
            "• Rivaroxabán: 15 mg c/12h × 21 días → 20 mg/d con comida. Extendido: 10 mg/d.\n"
            "• Edoxabán: tras ≥5 d HBPM, 60 mg/d (30 mg si criterios de reducción).\n"
            "• Dabigatrán: tras ≥5 d HBPM, 150 mg c/12h.\n\n"
            "AJUSTE POR FUNCIÓN RENAL:\n"
            "• Apixabán: menos dependiente de TFG; usable hasta ClCr 15.\n"
            "• Rivaroxabán: reducir si ClCr 15–49; evitar <15.\n"
            "• Edoxabán: evitar <15 y >95 mL/min.\n"
            "• Dabigatrán: evitar <30 mL/min (alta eliminación renal).\n"
            "• Si TFG <15: NO DOAC; usar warfarina o HBPM ajustada.\n\n"
            "REVERSIÓN DE SANGRADO MAYOR:\n"
            "• Dabigatrán → idarucizumab 5 g IV (2 viales de 2,5 g).\n"
            "• Apixabán/Rivaroxabán → andexanet alfa (bolo + infusión 2 h) en HIC y otros "
            "sangrados con riesgo vital. ANNEXA-I 2024: ↑eventos trombóticos: monitorizar.\n"
            "• Cualquier DOAC sin antídoto → CCP 4F (50 UI/kg) + soporte.\n"
            "• Edoxabán → sin antídoto específico; CCP 4F.\n"
            "• Carbón activado si ingesta <2–4 h.\n"
            "• Diálisis útil para dabigatrán (no para los anti-Xa).\n\n"
            "WARFARINA — INR OBJETIVO:\n"
            "• FANV: 2,0–3,0; TTR objetivo >70%.\n"
            "• Válvula aórtica mecánica: 2,5–3,0.\n"
            "• Válvula mitral mecánica: 3,0–3,5.\n"
            "• SAF: 2,0–3,0 (alto riesgo: 3,0–3,5).\n"
            "• Reversión electiva: suspender 5 d.\n"
            "• Sangrado mayor: CCP 4F + vitamina K 10 mg IV (no plasma fresco como primera línea).\n\n"
            "CONTRAINDICACIONES DOACs:\n"
            "• Válvula mecánica (RE-ALIGN: ↑eventos con dabigatrán).\n"
            "• Estenosis mitral reumática moderada-severa.\n"
            "• SAF triple positivo (TRAPS: rivaroxabán inferior a warfarina).\n"
            "• Embarazo y lactancia.\n\n"
            "TRIPLE/DUAL TERAPIA SCA + FA: ver ESC 2024 AF — 1 semana triple + 11 meses dual."
        ),
        "fuente": "ESC AF 2024; CHEST 2024 antithrombotic; AHA/ACC PE 2026.",
        "vigencia": "2024–2026",
    },
    {
        "id": "DEF-GUIA-005",
        "termino": "Surviving Sepsis Campaign 2026 — Bundle hora-1 y SOFA/NEWS2",
        "tipo": "guia",
        "categoria": "urgencias/UCI",
        "definicion": (
            "Surviving Sepsis Campaign 2026 — abril 2026 en Critical Care Medicine. 129 "
            "statements, 46 nuevos vs SSC 2021.\n\n"
            "DEFINICIONES (Sepsis-3 vigente, NO existe Sepsis-4):\n"
            "• Sepsis: disfunción orgánica potencialmente mortal por respuesta desregulada "
            "del huésped a infección (↑SOFA ≥2 puntos).\n"
            "• Shock séptico: sepsis + vasopresores para MAP ≥65 + lactato >2 mmol/L pese a "
            "resucitación adecuada.\n\n"
            "TAMIZAJE — CAMBIO MAYOR:\n"
            "• qSOFA DEGRADADO: no usar como herramienta única (sensibilidad ~23%).\n"
            "• Preferir NEWS2 (sens ~73%) o MEWS o SIRS en hospitalizados.\n"
            "• SOFA: sigue siendo estándar para definir disfunción orgánica.\n\n"
            "BUNDLE HORA-1:\n"
            "• Lactato: medir; si >2 mmol/L resucitar y repetir seriadamente (umbral bajado "
            "de 4 a 2 mmol/L).\n"
            "• Hemocultivos antes de antibióticos (sin retrasarlos en shock).\n"
            "• Antibióticos:\n"
            "  – Shock séptico o sepsis probable: ≤1 hora.\n"
            "  – Sepsis posible sin shock: hasta 3 horas tras evaluación (permite diferir si "
            "baja probabilidad — favorece stewardship).\n"
            "• Fluidos: 30 mL/kg cristaloides en 3 h (recomendación DÉBIL, individualizar; "
            "CLOVERS y CLASSIC no mostraron beneficio de estrategia liberal vs restrictiva).\n"
            "• Cristaloides balanceados (Plasma-Lyte, Ringer lactato) sobre SF 0,9%.\n"
            "• Vasopresores: noradrenalina primera línea; iniciar precoz junto a fluidos "
            "si shock inestable, no esperar a completar 30 mL/kg.\n"
            "• MAP objetivo ≥65 mmHg (en AM considerar objetivo menor).\n"
            "• Vasopresina o adrenalina como segunda línea.\n\n"
            "ANTIBIOTICOTERAPIA EMPÍRICA POR FOCO:\n"
            "• Abdominal: pip-tazo o carbapenémico (anaerobios + BGN).\n"
            "• Urinario: ceftriaxona; cefepime/pip-tazo si riesgo MDR. NO anaerobios.\n"
            "• NAC severa: ceftriaxona + macrólido; vancomicina + pip-tazo si riesgo SAMR/Pseudomonas.\n"
            "• Piel/partes blandas: vancomicina + pip-tazo (SAMR + BGN); clindamicina si fascitis.\n"
            "• Foco desconocido: pip-tazo o meropenem ± vancomicina.\n"
            "• Antifúngicos solo si factores de riesgo (inmunosupresión, ATB prolongado, "
            "hospitalización prolongada, foco abdominal).\n\n"
            "CORTICOIDES:\n"
            "• Hidrocortisona IV 200 mg/d (50 mg c/6h o infusión continua) en shock séptico "
            "con vasopresores en escalada (típicamente noradrenalina ≥0,25 µg/kg/min por ≥4 h).\n\n"
            "CAMBIOS RECIENTES — qué NO hacer:\n"
            "• NO ácido ascórbico/HAT therapy (VITAMINS, LOVIT negativos).\n"
            "• Hemoperfusión con polimixina B: sugerida en contra (TIGRIS 2026 con señal en "
            "shock endotóxico — área en evolución).\n"
            "• Estrategia restrictiva NO superior a liberal: individualizar."
        ),
        "fuente": "Prescott HC, et al. Crit Care Med 2026;54(4); también Intensive Care Med 2026.",
        "vigencia": "2026",
    },
    {
        "id": "DEF-GUIA-006",
        "termino": "TEP 2026 — Guía AHA/ACC/ACCP/ACEP/CHEST y CDT",
        "tipo": "guia",
        "categoria": "cardiología/pulmonar",
        "definicion": (
            "2026 AHA/ACC/ACCP/ACEP/CHEST/SCAI/SHM/SIR/SVM/SVN Guideline for Acute PE — "
            "primera guía conjunta multisocietaria para TEP agudo (feb 2026).\n\n"
            "ESTRATIFICACIÓN DE RIESGO (categorías ESC):\n"
            "• Alto riesgo: shock/hipotensión sostenida (PAS <90 o caída ≥40 por >15 min).\n"
            "• Intermedio-alto: disfunción VD (TC o eco) + biomarcadores positivos (troponina, BNP).\n"
            "• Intermedio-bajo: solo uno de los anteriores.\n"
            "• Bajo riesgo: sPESI 0, sin disfunción VD, biomarcadores normales.\n\n"
            "DIAGNÓSTICO:\n"
            "• Probabilidad pre-test: Wells o Geneva revisado (PE likely/unlikely).\n"
            "• Dímero D ajustado por edad (>50 a): umbral = edad × 10 µg/L (no <500 fijo).\n"
            "• Algoritmo YEARS: 3 ítems (signos TVP, hemoptisis, TEP como dx más probable). "
            "0 ítems → DD <1000 excluye; ≥1 ítem → DD <500 excluye.\n"
            "• AngioTC pulmonar = gold standard.\n"
            "• V/Q en embarazo, ERC, alergia contraste.\n"
            "• Ecocardio bedside: signos sobrecarga VD (dilatación VD, hipocinesia, "
            "McConnell, septum en D, TAPSE <16 mm, 60/60). Indispensable en inestabilidad.\n\n"
            "TRATAMIENTO POR CATEGORÍA:\n"
            "• ALTO RIESGO (shock): TROMBOLISIS SISTÉMICA — alteplasa 100 mg IV en 2 h "
            "(o 0,6 mg/kg en 15 min si paro). Si contraindicada/falla → trombectomía "
            "mecánica o CDT. Soporte (noradrenalina, ECMO V-A si refractario).\n"
            "• INTERMEDIO-ALTO: anticoagulación + monitorización estrecha.\n"
            "  – HI-PEITHO (NEJM 2026): CDT con ultrasonido (EKOS) redujo 61% endpoint "
            "compuesto (muerte/descompensación/recurrencia a 7 d) vs anticoag sola.\n"
            "  – PEERLESS 2024: trombectomía mecánica (FlowTriever) superior a CDT (win "
            "ratio 5,01).\n"
            "• INTERMEDIO-BAJO / BAJO: DOAC primera línea.\n"
            "• BAJO RIESGO (sPESI 0, HESTIA negativo): manejo ambulatorio con DOAC.\n\n"
            "ANTICOAGULACIÓN:\n"
            "• Apixabán 10 mg c/12h × 7 d → 5 mg c/12h; extendida 2,5 mg c/12h tras 6 m.\n"
            "• Rivaroxabán 15 mg c/12h × 21 d → 20 mg/d; extendida 10 mg/d.\n"
            "• Cáncer activo: DOAC o HBPM mientras enfermedad activa.\n\n"
            "DURACIÓN:\n"
            "• Provocado por factor mayor transitorio (cirugía, trauma): 3 meses.\n"
            "• Factor menor transitorio (viaje, estrógenos, embarazo): 3–6 meses.\n"
            "• No provocado o factor persistente (cáncer, trombofilia, recurrente): "
            "INDEFINIDA (apixabán 2,5 c/12h o rivaroxabán 10 mg/d).\n"
            "• Herramientas: HERDOO2, DASH, Vienna.\n\n"
            "TROMBECTOMÍA MECÁNICA (FlowTriever, Inari):\n"
            "• Indicada en alto riesgo con contraindicación a trombolisis, falla de "
            "trombolisis, o intermedio-alto con deterioro.\n"
            "• FLASH registry: MAE 1,8%, mortalidad 30 d 0,8%.\n"
            "• Decisiones idealmente vía PERT (Pulmonary Embolism Response Team)."
        ),
        "fuente": "2026 AHA/ACC PE Guideline; ESC PE 2019; HI-PEITHO NEJM 2026.",
        "vigencia": "2026",
    },
    {
        "id": "DEF-GUIA-007",
        "termino": "AACE 2026 — Algoritmo de DM2 comorbidities-centric",
        "tipo": "guia",
        "categoria": "endocrino",
        "definicion": (
            "AACE Consensus Statement: Algorithm for Management of Adults With Type 2 "
            "Diabetes — 2026 Update. Endocrine Practice, marzo 2026.\n\n"
            "CAMBIO DE PARADIGMA:\n"
            "Las comorbilidades CV/renales/hepáticas se evalúan ANTES que la HbA1c. La "
            "elección de fármaco depende primero de qué órgano hay que proteger.\n\n"
            "OBJETIVOS GLICÉMICOS (individualizados):\n"
            "• General: HbA1c ≤6,5% si alcanzable de forma segura.\n"
            "• Joven, sin complicaciones, DM corta evolución: ≤6,5%.\n"
            "• Comorbilidad, alto riesgo hipoglicemia, larga duración, deterioro cognitivo: "
            "meta menos estricta (>6,5%).\n"
            "• Adulto mayor frágil / expectativa vida limitada: 7–8%.\n"
            "• Glicemia ayuno: <110 mg/dL sin hipoglicemia.\n\n"
            "ALGORITMO DE INICIO (glucose-centric, una vez evaluado comorbidities):\n"
            "• HbA1c <7,5% → monoterapia (preferir GLP-1 RA o SGLT2i si hay indicación "
            "cardio-reno; metformina si sin comorbilidad mayor).\n"
            "• HbA1c 7,5–9% → dual desde el inicio.\n"
            "• HbA1c >9% sin síntomas → triple.\n"
            "• HbA1c >10%, glicemia >300 o síntomas catabólicos → INSULINA ± otros.\n\n"
            "GLP-1 RA con beneficio CV probado:\n"
            "• Semaglutida (1ª línea ASCVD; reduce ACV).\n"
            "• Dulaglutida (reduce ACV).\n"
            "• Liraglutida.\n"
            "• Tirzepatida (GIP/GLP-1 dual): opción racional T2D + obesidad + AOS.\n"
            "• Retatrutida (triple GLP-1/GIP/glucagón): fase 2, no recomendado aún (~17% "
            "pérdida peso a 36 sem en T2D).\n\n"
            "SGLT2i primera línea en:\n"
            "• Insuficiencia cardiaca (HFrEF y HFpEF).\n"
            "• ERC (independiente de HbA1c, eGFR ≥20).\n"
            "• Empagliflozina, dapagliflozina, canagliflozina.\n\n"
            "AJUSTE POR COMORBILIDAD:\n"
            "• Obesidad → GLP-1 RA o tirzepatida.\n"
            "• IC → SGLT2i.\n"
            "• ERC → SGLT2i; añadir GLP-1 RA si albuminuria persiste.\n"
            "• ASCVD → GLP-1 RA con beneficio CV probado o SGLT2i.\n"
            "• MASLD/MASH → GLP-1 RA, pioglitazona.\n"
            "• AOS → tirzepatida.\n\n"
            "OTROS FÁRMACOS:\n"
            "• Metformina: válida primera línea SIN comorbilidad mayor; ya no obligatoria si "
            "hay indicación cardio-reno.\n"
            "• Sulfonilureas: LIMITAR/DISCONTINUAR — sin beneficio CV/renal, riesgo hipoglicemia, ↑peso.\n"
            "• DPP-4i: rol limitado, peso-neutro; NO combinar con GLP-1 RA.\n"
            "• Pioglitazona: útil si resistencia insulínica, prediabetes, antecedente TIA/ACV.\n\n"
            "INSULINA:\n"
            "• Basal análoga (glargina, degludec) preferida sobre NPH.\n"
            "• Titular cada 2–5 días a ayuno <110 mg/dL.\n"
            "• Evitar sobrebasalización: si postprandial alto, añadir GLP-1 RA o prandial (lispro, aspart, glulisina).\n\n"
            "CGM (monitoreo continuo): fuertemente recomendado en MDI o alto riesgo "
            "hipoglicemia. Métricas: TIR, TBR, variabilidad, GMI."
        ),
        "fuente": "AACE Consensus Statement 2026 — Endocrine Practice, marzo 2026.",
        "vigencia": "2026",
    },
    {
        "id": "DEF-GUIA-008",
        "termino": "ADA 2026 — Hipoglicemia",
        "tipo": "guia",
        "categoria": "endocrino",
        "definicion": (
            "ADA Standards of Care in Diabetes 2026, Capítulo 6 — Glycemic Goals, "
            "Hypoglycemia, and Hyperglycemic Crises. Diabetes Care 2026;49(Suppl 1):S132-S149.\n\n"
            "CLASIFICACIÓN ADA/EASD (vigente):\n"
            "• Nivel 1 (alerta/leve): glicemia <70 mg/dL (3,9 mmol/L) y ≥54.\n"
            "• Nivel 2 (clínicamente significativa): glicemia <54 mg/dL (3,0); umbral de "
            "síntomas neuroglucopénicos.\n"
            "• Nivel 3 (severa): alteración del estado mental/físico que requiere asistencia "
            "de otra persona (no se define por valor de glicemia).\n\n"
            "RECONOCIMIENTO:\n"
            "• Adrenérgicos/autonómicos (~60–70 mg/dL): temblor, palpitaciones, sudoración, "
            "ansiedad, hambre, palidez.\n"
            "• Neuroglucopénicos (<54): confusión, dificultad para concentrarse, visión "
            "borrosa, lenguaje farfullante, convulsiones, coma.\n"
            "• Hypoglycemia unawareness: episodio nivel 2 sin síntomas — restaurar "
            "percepción evitando hipoglicemia 2–3 semanas y relajando metas.\n\n"
            "TRATAMIENTO AGUDO:\n"
            "• CONSCIENTE — Regla de 15: 15 g HC rápida (preferir glucosa oral; jugo, "
            "azúcar) → recontrolar a los 15 min → repetir hasta >70 mg/dL → comida o snack.\n"
            "• INCONSCIENTE EXTRAHOSPITALARIO — Glucagón:\n"
            "  – IM o SC 1 mg adultos / niños >25 kg (0,5 mg si <25 kg).\n"
            "  – Intranasal (Baqsimi) 3 mg, 1 actuación en una fosa, NO requiere inhalación.\n"
            "  – SC listo (Gvoke) 1 mg.\n"
            "  – Respuesta esperada ~15 min; repetir si no responde.\n"
            "• HOSPITAL con acceso IV: dextrosa 25 g IV (50 mL D50% o 100 mL D25%) → "
            "infusión D5–D10% hasta euglicemia estable.\n\n"
            "PREVENCIÓN (nuevo 2026):\n"
            "• Rec. 5.47: cribado anual de miedo a hipoglicemia.\n"
            "• Rec. 6.17: incluir glucosa oral en botiquines de trabajo/escuelas.\n"
            "• CGM con alertas predictivas ampliado a todo usuario de insulina.\n"
            "• Sistemas híbridos automáticos (AID).\n"
            "• Educación estructurada (DAFNE, BGAT), identificación médica visible.\n"
            "• Glucagón prescrito a TODO paciente con riesgo de nivel 2–3.\n\n"
            "HIPOGLICEMIA INDUCIDA — fármacos clave:\n"
            "• Insulina (principal causa).\n"
            "• Sulfonilureas: glibenclamida mayor riesgo (vida media larga + metabolitos "
            "activos); EVITAR en AM/ERC (Beers). Glimepirida menor riesgo, preferida si SU "
            "necesaria. Glinidas (repaglinida) menor riesgo.\n"
            "• Alcohol (inhibe gluconeogénesis hepática).\n"
            "• Comorbilidad: sepsis, IRC, IH, deficiencia cortisol, hipotiroidismo severo, "
            "desnutrición.\n\n"
            "EN NO DIABÉTICOS — Tríada de Whipple (Endocrine Society):\n"
            "(1) síntomas compatibles + (2) glicemia <55 mg/dL documentada + (3) resolución "
            "con glucosa. Solo evaluar si se cumple.\n"
            "• Hiperinsulinismo endógeno (insulinoma): insulina ≥3 µU/mL, péptido C ≥0,6 "
            "ng/mL, proinsulina ≥5 pmol/L con glicemia <55; test de ayuno 72 h; "
            "localización por TC/RM, EUS, PET-68Ga-exendina.\n"
            "• Hipoglicemia reactiva postprandial: post-bariátrica (dumping tardío), "
            "idiopática; manejo dietético (HC complejos, comidas fraccionadas)."
        ),
        "fuente": "ADA Diabetes Care 2026;49(Suppl 1):S132-S149.",
        "vigencia": "2026",
    },
    {
        "id": "DEF-GUIA-009",
        "termino": "AHA/ACC 2026 — Dislipidemia, Lp(a) y PREVENT",
        "tipo": "guia",
        "categoria": "cardiología",
        "definicion": (
            "2026 ACC/AHA/AACVPR/ABC/ACPM/ADA/AGS/APhA/ASPC/NLA/PCNA Guideline on the "
            "Management of Dyslipidemia (Circulation, marzo 2026). Reemplaza la guía 2018 "
            "de Blood Cholesterol. Cambio de nombre clave: «dislipidemia» (incluye LDL-C, "
            "TG y Lp(a)).\n\n"
            "CRIBADO:\n"
            "• Niños 9–11 años: panel lipídico universal. Desde los 2 años si historia "
            "familiar de ASCVD prematura, hipercolesterolemia severa o HF.\n"
            "• Adultos: panel cada 5 años (mínimo) desde los 19 años.\n"
            "• Lp(a) UNA VEZ EN LA VIDA en todos los adultos (Clase I, primera vez en guía "
            "estadounidense). Umbral significativo: ≥125 nmol/L (~50 mg/dL).\n"
            "• ApoB útil cuando TG >200, DM, o LDL-C logrado <70.\n\n"
            "ESTRATIFICACIÓN DE RIESGO:\n"
            "• PREVENT (AHA 2023) ENDORSADA — incluye eGFR, omite raza, BMI solo para IC. "
            "Calcula riesgo a 10 y 30 años.\n"
            "• Pooled Cohort Equations: DEPRECATED.\n"
            "• Categorías PREVENT: bajo <3%, borderline 3–<5%, intermedio 5–<10%, alto ≥10%; "
            "muy alto = ASCVD establecida con eventos recurrentes o múltiples condiciones "
            "de alto riesgo.\n\n"
            "METAS LDL-C (la guía RESTAURA metas numéricas):\n"
            "• Bajo/borderline: estilo de vida; estatina si otros factores.\n"
            "• Intermedio (PREVENT 5–<10%): LDL-C <100 mg/dL, no-HDL-C <130.\n"
            "• Alto riesgo (ASCVD establecida, ≥10%): LDL-C <70 mg/dL o reducción ≥50%.\n"
            "• Muy alto riesgo (ASCVD recurrente, DM con múltiples factores): LDL-C <55.\n\n"
            "ESTATINAS:\n"
            "• Alta intensidad: atorvastatina 40–80, rosuvastatina 20–40 → ASCVD clínica, "
            "muy alto/alto riesgo, LDL ≥190, DM con factores, SCA al ingreso.\n"
            "• Moderada: atorva 10–20, rosuva 5–10, simva 20–40 → intermedio, CKD ≥3 "
            "(atorvastatina preferida; rosuva ≤10).\n\n"
            "ESCALADA (Clase I):\n"
            "1. Estatina alta intensidad → si LDL no llega a meta:\n"
            "2. + Ezetimiba 10 mg/d → si no:\n"
            "3. + iPCSK9 (alirocumab, evolocumab) si LDL ≥70 (muy alto riesgo) o ≥100 (alto).\n"
            "4. Inclisiran 284 mg SC dosis 0, mes 3, luego cada 6 meses — alternativa a iPCSK9.\n"
            "5. Ácido bempedoico en intolerancia a estatinas (CLEAR Outcomes: ↓MACE 13%).\n\n"
            "Lp(a) ELEVADA — Manejo actual:\n"
            "• Intensificar control de otros factores (LDL más agresivo, PA, no fumar).\n"
            "• Sin terapia Lp(a)-específica aprobada aún.\n"
            "• En pipeline: pelacarsen (HORIZON, 2026), olpasiran (OCEAN(a), 2027), "
            "lepodisiran, muvalaplin (oral).\n\n"
            "TG ALTOS:\n"
            "• 150–499 mg/dL + ASCVD/DM con factor adicional, post-meta LDL: ICOSAPENT "
            "ETHYL 4 g/d (REDUCE-IT: ↓25% MACE). Único TG-lowering con outcomes.\n"
            "• Fenofibrato y niacina: NO recomendados como add-on rutinario.\n"
            "• ≥500: prioridad prevenir pancreatitis (fenofibrato, ω-3, dieta).\n"
            "• HDL bajo aislado: NO target farmacológico."
        ),
        "fuente": "Circulation 2026 — DOI 10.1161/CIR.0000000000001423.",
        "vigencia": "2026",
    },
    {
        "id": "DEF-GUIA-010",
        "termino": "ACG 2024-2026 — H. pylori, HDA, pancreatitis, EII y encefalopatía hepática",
        "tipo": "guia",
        "categoria": "gastroenterología",
        "definicion": (
            "Síntesis de guías ACG vigentes 2021–2026 más relevantes para EUNACOM.\n\n"
            "H. PYLORI (ACG 2024 — Chey et al., Am J Gastroenterol sept 2024):\n"
            "• Se ELIMINA triple terapia con claritromicina como 1ª línea (resistencia >15%).\n"
            "• Primera línea: CUÁDRUPLE CON BISMUTO × 14 días (PPI + bismuto + tetraciclina "
            "+ metronidazol) O VONOPRAZAN DUAL (vonoprazan 20 mg c/12h + amoxicilina 1 g c/8h × 14 d).\n"
            "• Alternativa: rifabutina triple.\n"
            "• Confirmar erradicación con test de aliento o antígeno fecal ≥4 sem post-tratamiento.\n\n"
            "HDA NO VARICEAL (ACG 2021, vigente):\n"
            "• Transfundir GR si Hb <7 g/dL.\n"
            "• Glasgow-Blatchford 0–1 → alta desde urgencias.\n"
            "• Eritromicina IV pre-endoscopía (procinético).\n"
            "• Endoscopía dentro de 24 h.\n"
            "• Forrest Ia/Ib/IIa/IIb → terapia endoscópica DUAL (inyección + térmica o clips).\n"
            "• PPI IV bolo + infusión continua 72 h post-hemostasia.\n\n"
            "HDA VARICEAL (AASLD 2024 — referencia):\n"
            "• Profilaxis primaria (várices alto riesgo): carvedilol (preferido) o ligadura.\n"
            "• Sangrado agudo: TERLIPRESINA o octreotida + ligadura endoscópica + CEFTRIAXONA "
            "1 g/d × 7 días.\n"
            "• Prevención secundaria: BB no selectivo + ligadura.\n\n"
            "PANCREATITIS AGUDA (ACG 2024):\n"
            "• Diagnóstico: 2 de 3 (dolor típico, lipasa/amilasa >3× normal, imagen).\n"
            "• RINGER LACTATO preferido sobre SF.\n"
            "• Resucitación MODERADA (no agresiva), reevaluar a 6 h, meta: ↓BUN.\n"
            "• NO TC rutinaria al ingreso — solo si diagnóstico incierto o no mejora a 48–72 h.\n"
            "• Nutrición enteral <48 h.\n"
            "• Antibióticos solo en NECROSIS INFECTADA confirmada.\n"
            "• Colangitis con PA biliar → CPRE <24 h.\n"
            "• PA biliar leve → COLECISTECTOMÍA en la misma hospitalización.\n\n"
            "ERGE (ACG 2022):\n"
            "• Síntomas clásicos sin alarma → prueba empírica con PPI antes de comidas × 8 semanas.\n"
            "• Endoscopía si disfagia, pérdida de peso, sangrado o riesgo de Barrett.\n"
            "• pH-metría/impedancia si PPI falla.\n"
            "• PPI a dosis mínima efectiva por seguridad a largo plazo.\n\n"
            "EII — CROHN y CU (ACG 2025):\n"
            "• Nuevos biológicos aprobados: risankizumab, mirikizumab, guselkumab "
            "(anti-IL-23) y upadacitinib (JAK).\n"
            "• YA NO se requiere falla a terapia convencional antes de biológicos.\n"
            "• Infliximab IV + tiopurina superior a monoterapia.\n"
            "• CU severa aguda: infliximab; si albúmina <2,5 → intensificar dosis.\n"
            "• Vedolizumab y infliximab subcutáneos disponibles.\n\n"
            "CONSTIPACIÓN CRÓNICA (AGA-ACG 2023):\n"
            "• 1ª línea: PEG (polietilenglicol) + fibra.\n"
            "• Si falla: secretagogos — linaclotida, plecanatida, lubiprostona, prucaloprida "
            "(agonista 5-HT4). Bisacodilo/senósidos como estimulantes. Tenapanor para IBS-C.\n\n"
            "ENCEFALOPATÍA HEPÁTICA (ACG 2026 — primera guía ACG dedicada):\n"
            "• Manifiesta: LACTULOSA titulada a 2–3 deposiciones blandas/día (1ª línea, "
            "prevención de recurrencia).\n"
            "• Añadir RIFAXIMINA 550 mg c/12h en EH aguda y profilaxis secundaria ambulatoria.\n"
            "• PEG alta dosis como alternativa a lactulosa.\n"
            "• Suplementar zinc si déficit.\n\n"
            "ASCITIS (AASLD 2021):\n"
            "• Restricción de sodio <2 g/d.\n"
            "• Espironolactona ± furosemida 100:40 mg.\n"
            "• Paracentesis con ALBÚMINA IV si extracción >5 L (8 g/L extraído)."
        ),
        "fuente": "ACG/AASLD guidelines 2021–2026 — journals.lww.com/ajg",
        "vigencia": "2021–2026",
    },
]

# ============================================================
# CASOS CLÍNICOS APLICANDO LAS GUÍAS (7)
# ============================================================
def op(letra, texto, correcta=False, feedback=None):
    o = {"letra": letra, "texto": texto, "correcta": correcta}
    if feedback:
        o["feedback"] = feedback
    return o

def etapa(orden, tipo, enunciado, opciones):
    return {"orden": orden, "tipo": tipo, "enunciado": enunciado, "opciones": opciones}

CASOS_NUEVOS = [
    {
        "id": "CASO-GUIA-001-ASMA",
        "titulo": "Asma con exacerbación moderada — GINA 2026",
        "especialidad": "pulmonar",
        "tema": "asma",
        "nivel": "intermedio",
        "guia_fuente": "GINA 2026",
        "version_actual": 1,
        "etapas": [
            etapa(1, "anamnesis",
                "Mujer 28 años, asma persistente conocida hace 5 años. Refiere disnea progresiva "
                "y sibilancias desde hace 48 h tras IVRS. Solo ha usado salbutamol a demanda "
                "(8 puffs en las últimas 24 h). Sin ICS de mantención. En consulta: FR 26, FC 110, "
                "SpO₂ 92% aire ambiental, sibilancias difusas con espiración prolongada. ¿Cuál es "
                "el manejo INICIAL correcto?",
                [
                    op("a", "Salbutamol 4–10 puffs con aerocámara c/20 min × 1 h + O₂ controlado para SpO₂ 93–95% + prednisona 40 mg VO", correcta=True,
                       feedback="Correcto. GINA 2026 mantiene SABA con aerocámara, O₂ a SpO₂ 93–95% (no >95%), corticoides sistémicos en exacerbación moderada."),
                    op("b", "Iniciar ICS-formoterol a demanda y enviar a casa",
                       feedback="Es exacerbación con SpO₂ 92% y FR 26 — requiere tratamiento agudo en box antes."),
                    op("c", "Salbutamol nebulizado continuo + adrenalina IM 0,3 mg",
                       feedback="Adrenalina IM es para anafilaxia, no para exacerbación asmática."),
                    op("d", "Aminofilina IV en infusión",
                       feedback="GINA 2026 reafirma: NO usar aminofilina rutinaria en exacerbación."),
                    op("e", "Antibiótico empírico (amoxicilina-clavulánico)",
                       feedback="No hay indicación de antibiótico — IVRS es la causa, no requiere ATB salvo infección documentada."),
                ]),
            etapa(2, "diagnostico",
                "A las 2 h responde parcialmente: SpO₂ 94%, FR 22, FC 100, sibilancias menos "
                "intensas. Decide ingresar para observación. Al revisar su tratamiento de "
                "mantención antes del alta, ¿cuál es el esquema PREFERIDO según GINA 2026 para "
                "una paciente con asma persistente y exacerbación reciente?",
                [
                    op("a", "Salbutamol a demanda como único tratamiento",
                       feedback="ELIMINADO de GINA 2026 — SABA monoterapia es contraindicado."),
                    op("b", "Budesónida-formoterol 200/6, 1 inhalación c/12h + a demanda (MART, Track 1 Step 3)", correcta=True,
                       feedback="Correcto. Track 1 con ICS-formoterol como mantención + rescate (MART/AIR) es preferido por GINA 2026."),
                    op("c", "Salmeterol-fluticasona dos veces al día + salbutamol como rescate",
                       feedback="Esquema de Track 2; GINA 2026 prefiere Track 1 con ICS-formoterol como rescate."),
                    op("d", "Tiotropio inhalado como monoterapia",
                       feedback="LAMA monoterapia no es estándar en asma persistente."),
                    op("e", "Omalizumab inicial",
                       feedback="Biológico se reserva para asma severa no controlada en Steps 4–5 con fenotipado."),
                ]),
            etapa(3, "manejo",
                "La paciente pregunta sobre vacunas y prevención. ¿Cuál de las siguientes "
                "recomendaciones es INCORRECTA según las guías vigentes 2026?",
                [
                    op("a", "Vacuna anti-influenza anual",
                       feedback="Es correcta."),
                    op("b", "Educación sobre técnica inhalatoria y plan de acción escrito",
                       feedback="Es correcta."),
                    op("c", "Vacuna PCV20 o PCV21 (neumococo)",
                       feedback="Es correcta — GOLD/GINA 2026 incorporan PCV20/PCV21."),
                    op("d", "Antibiótico profiláctico mensual con azitromicina",
                       correcta=True,
                       feedback="INCORRECTA. Azitromicina profiláctica no es estándar en asma sin bronquiectasias o asma neutrofílica refractaria."),
                    op("e", "Vacuna anti-VSR si comorbilidad pulmonar crónica",
                       feedback="Es correcta para enfermedad pulmonar crónica ≥50 años."),
                ]),
        ],
        "resumen_final": (
            "Caso clave de manejo agudo y crónico de asma según GINA 2026:\n"
            "• Exacerbación moderada: SABA con aerocámara + O₂ titulado a SpO₂ 93–95% + "
            "prednisona 40 mg VO × 5 días.\n"
            "• NO SABA monoterapia de mantención (eliminado).\n"
            "• Track 1 (preferido): ICS-formoterol como mantención y rescate (AIR/MART).\n"
            "• Vacunas: influenza, neumococo (PCV20/PCV21), VSR, COVID, herpes zóster."
        ),
    },
    {
        "id": "CASO-GUIA-002-FA",
        "titulo": "FA de novo con HTA y DM — ESC 2024",
        "especialidad": "cardiología",
        "tema": "fibrilacion_auricular",
        "nivel": "intermedio",
        "guia_fuente": "ESC AF 2024",
        "version_actual": 1,
        "etapas": [
            etapa(1, "anamnesis",
                "Hombre 68 años con HTA + DM2 + obesidad (IMC 32). Consulta por palpitaciones "
                "de 3 días. PA 145/85, FC irregular 110, sin disnea ni signos de IC. ECG "
                "muestra fibrilación auricular sin onda P, RR irregular. Aplicando el esquema "
                "AF-CARE y el nuevo score CHA₂DS₂-VA, ¿cuál es la conducta correcta?",
                [
                    op("a", "CHA₂DS₂-VA = 3 (HTA 1 + DM 1 + edad 65-74 1) → iniciar DOAC", correcta=True,
                       feedback="Correcto. CHA₂DS₂-VA 3 indica OAC (≥2). DOAC preferido sobre warfarina en FA no valvular."),
                    op("b", "CHA₂DS₂-VASc = 4 → iniciar AAS",
                       feedback="ESC 2024: el sexo ya no se cuenta (CHA₂DS₂-VA), y AAS NO está indicado para prevenir ACV en FA — solo OAC."),
                    op("c", "No anticoagular hasta confirmar FA persistente >30 segundos",
                       feedback="Con FA documentada en ECG de 12 derivaciones no se requiere monitorización adicional para indicar OAC."),
                    op("d", "Iniciar AAS + clopidogrel como alternativa a OAC",
                       feedback="La doble antiagregación NO sustituye OAC para profilaxis de ACV en FA."),
                    op("e", "Cardioversión eléctrica inmediata sin anticoagulación previa",
                       feedback="Sin urgencia hemodinámica, cardioversión inmediata sin OAC ≥3 sem o ecotransesofágico negativo es riesgosa."),
                ]),
            etapa(2, "manejo",
                "Inicia apixabán. El paciente tiene 68 años, peso 78 kg, creatinina 1,0 mg/dL. "
                "¿Qué dosis le indica?",
                [
                    op("a", "Apixabán 5 mg c/12h", correcta=True,
                       feedback="Correcto. Para reducir a 2,5 mg c/12h necesita ≥2 de: edad ≥80, peso ≤60 kg, Cr ≥1,5 mg/dL. No cumple ninguno."),
                    op("b", "Apixabán 2,5 mg c/12h",
                       feedback="Subdosis. NO reducir fuera de criterios — evitar infradosificación."),
                    op("c", "Apixabán 10 mg c/12h",
                       feedback="Es la dosis de fase aguda de TVP/TEP, no de FA."),
                    op("d", "Apixabán 5 mg/día",
                       feedback="Apixabán siempre se dosifica c/12h en FA, no una vez al día."),
                    op("e", "Apixabán 7,5 mg c/12h",
                       feedback="No existe esa presentación."),
                ]),
            etapa(3, "diagnostico",
                "Al aplicar AF-CARE más allá de la anticoagulación, ¿cuál de los siguientes "
                "componentes es el MÁS importante para este paciente con obesidad e HTA?",
                [
                    op("a", "Reducción de peso explícita ≥10% como meta", correcta=True,
                       feedback="Correcto. ESC 2024 establece pérdida ≥10% como meta explícita en obesos con FA (pilar C: comorbilidades)."),
                    op("b", "Ablación con catéter inmediata como única opción",
                       feedback="Ablación es Clase I en FA paroxística para reducir síntomas/recurrencia, pero AF-CARE prioriza control de comorbilidades primero."),
                    op("c", "Iniciar amiodarona como control de ritmo",
                       feedback="Si requiere control de ritmo, amiodarona NO es 1ª línea por toxicidad."),
                    op("d", "Cierre de orejuela percutáneo",
                       feedback="Cierre de orejuela es IIa solo si contraindicación a OAC, no como prevención primaria."),
                    op("e", "AAS adicional a apixabán",
                       feedback="Aumenta riesgo de sangrado sin beneficio antitrombótico."),
                ]),
        ],
        "resumen_final": (
            "FA según ESC 2024 — esquema AF-CARE:\n"
            "• [C] Comorbilidades primero: pérdida ≥10% peso, control PA, DM, apnea, alcohol.\n"
            "• [A] Anticoagulación según CHA₂DS₂-VA (sin sexo): ≥2 indica OAC.\n"
            "• [R] Reducir síntomas: control frecuencia (BB) o ritmo (ablación Clase I en FA paroxística).\n"
            "• [E] Reevaluación dinámica.\n\n"
            "DOAC preferido. NO reducir dosis fuera de criterios. AAS no sustituye OAC."
        ),
    },
    {
        "id": "CASO-GUIA-003-TEP",
        "titulo": "TEP intermedio-alto en paciente postquirúrgico — AHA 2026",
        "especialidad": "cardiología",
        "tema": "tep",
        "nivel": "avanzado",
        "guia_fuente": "AHA/ACC PE 2026",
        "version_actual": 1,
        "etapas": [
            etapa(1, "anamnesis",
                "Mujer 62 años, 7º día postoperatorio de prótesis de cadera. Presenta disnea "
                "súbita y dolor torácico. PA 100/60, FC 115, FR 26, SpO₂ 90% aire ambiental. "
                "Wells: 7,5 puntos (TEP probable). AngioTC confirma TEP segmentario bilateral. "
                "Ecocardio bedside: dilatación de VD con TAPSE 14 mm. Troponina I 0,08 ng/mL "
                "(elevada). NT-proBNP 950 pg/mL. ¿En qué categoría de riesgo la clasifica?",
                [
                    op("a", "Alto riesgo (shock)",
                       feedback="No hay shock — PA 100/60 sostenida no cumple criterio (<90 sostenida >15 min)."),
                    op("b", "Intermedio-alto (disfunción VD + biomarcadores positivos)", correcta=True,
                       feedback="Correcto. AHA/ACC 2026 — intermedio-alto = disfunción VD + biomarcadores positivos sin shock."),
                    op("c", "Intermedio-bajo",
                       feedback="Intermedio-bajo sería solo uno de los dos (VD O biomarcadores), no ambos."),
                    op("d", "Bajo riesgo",
                       feedback="Bajo riesgo requiere sPESI 0, sin disfunción VD ni biomarcadores."),
                    op("e", "No clasificable sin centellograma V/Q",
                       feedback="AngioTC es gold standard; la clasificación se hace con clínica + VD + biomarcadores."),
                ]),
            etapa(2, "manejo",
                "Tratamiento inicial. Considerando la categoría intermedio-alto y los ensayos "
                "PEERLESS / HI-PEITHO (2024-2026), ¿cuál es la conducta MÁS apropiada en un "
                "centro con PERT disponible?",
                [
                    op("a", "Anticoagulación con heparina + monitorización estrecha",
                       feedback="Es lo mínimo aceptable; sin embargo HI-PEITHO 2026 mostró superioridad de CDT facilitado por US en este perfil."),
                    op("b", "Trombolisis sistémica con alteplasa 100 mg en 2 h",
                       feedback="Trombolisis sistémica es para alto riesgo (shock); en intermedio-alto el riesgo de sangrado supera el beneficio."),
                    op("c", "Activar PERT y evaluar trombectomía mecánica (FlowTriever) o CDT facilitado por ultrasonido (EKOS)", correcta=True,
                       feedback="Correcto. PEERLESS 2024 (FlowTriever > CDT en intermedio-riesgo) y HI-PEITHO 2026 (CDT-US ↓61% endpoint compuesto vs anticoag). Decisión PERT."),
                    op("d", "Filtro de vena cava como única medida",
                       feedback="Filtro IVC se reserva para contraindicación absoluta a anticoagulación; nunca como única medida."),
                    op("e", "ECMO V-A",
                       feedback="ECMO V-A solo en alto riesgo refractario tras trombolisis o como puente a trombectomía."),
                ]),
            etapa(3, "diagnostico",
                "Se realiza trombectomía mecánica exitosa. La paciente se estabiliza y se inicia "
                "apixabán. Como fue un TEP provocado por cirugía mayor reciente, ¿cuál es la "
                "duración correcta de anticoagulación?",
                [
                    op("a", "3 meses", correcta=True,
                       feedback="Correcto. Factor mayor transitorio (cirugía) → 3 meses de anticoagulación es estándar."),
                    op("b", "6 meses fijos siempre",
                       feedback="6 meses se usa en provocados por factor menor; cirugía mayor es factor mayor."),
                    op("c", "Anticoagulación indefinida obligatoria",
                       feedback="Indefinida es para TEP no provocado o factor persistente (cáncer, trombofilia, recurrente)."),
                    op("d", "Suspender al alta hospitalaria",
                       feedback="Incorrecto — duración mínima 3 meses."),
                    op("e", "Cambiar a warfarina por 1 año",
                       feedback="DOAC se mantiene; warfarina no es preferida sin indicación específica."),
                ]),
        ],
        "resumen_final": (
            "TEP según AHA/ACC 2026:\n"
            "• Estratificación: alto (shock), intermedio-alto (VD+biomarcadores+), "
            "intermedio-bajo (uno), bajo (sPESI 0).\n"
            "• Alto: trombolisis sistémica (alteplasa 100 mg/2 h).\n"
            "• Intermedio-alto: anticoagulación + considerar CDT-US (HI-PEITHO 2026) o "
            "trombectomía mecánica (PEERLESS 2024) vía PERT.\n"
            "• Intermedio-bajo / bajo: DOAC primera línea; bajo con sPESI 0 → ambulatorio.\n"
            "• Duración: 3 m si factor mayor transitorio; INDEFINIDA si no provocado o "
            "persistente."
        ),
    },
    {
        "id": "CASO-GUIA-004-SEPSIS",
        "titulo": "Shock séptico de origen abdominal — SSC 2026",
        "especialidad": "urgencias",
        "tema": "sepsis",
        "nivel": "avanzado",
        "guia_fuente": "Surviving Sepsis 2026",
        "version_actual": 1,
        "etapas": [
            etapa(1, "anamnesis",
                "Hombre 58 años con DM2 mal controlada. Consulta por dolor abdominal difuso, "
                "fiebre 39 °C, vómitos. PA 88/52, FC 124, FR 28, SpO₂ 94%. Glasgow 14. "
                "Abdomen distendido con dolor difuso. Lactato 3,4 mmol/L, leucocitos "
                "18.000/mm³ con desviación izquierda, creatinina 1,9 mg/dL (basal 0,9). "
                "Aplicando SSC 2026, ¿cuál herramienta de tamizaje es la PREFERIDA en este "
                "paciente hospitalizado?",
                [
                    op("a", "qSOFA por su simplicidad",
                       feedback="SSC 2026 DEGRADA qSOFA por baja sensibilidad (~23%) — no usar como única herramienta."),
                    op("b", "NEWS2 sobre qSOFA", correcta=True,
                       feedback="Correcto. SSC 2026 prefiere NEWS2 (sens ~73%), MEWS o SIRS sobre qSOFA en hospitalizados."),
                    op("c", "SIRS exclusivamente",
                       feedback="SIRS aceptable pero NEWS2 es preferida."),
                    op("d", "Solo lactato como tamizaje",
                       feedback="Lactato es marcador de resucitación, no herramienta de tamizaje aislada."),
                    op("e", "Solo PCR sérica",
                       feedback="PCR es marcador inflamatorio, no validado para tamizaje de sepsis."),
                ]),
            etapa(2, "manejo",
                "Diagnóstico: shock séptico de probable origen abdominal. ¿Cuál de las "
                "siguientes conductas iniciales NO se ajusta a SSC 2026?",
                [
                    op("a", "Hemocultivos antes de antibióticos, sin retrasar éstos por la toma",
                       feedback="Correcta."),
                    op("b", "Cristaloides balanceados (Ringer lactato o Plasma-Lyte) sobre SF",
                       feedback="Correcta."),
                    op("c", "Esperar a completar 30 mL/kg antes de iniciar noradrenalina",
                       correcta=True,
                       feedback="INCORRECTA. SSC 2026 acepta vasopresores PRECOCES junto a fluidos si shock inestable; no esperar a completar el bolo."),
                    op("d", "Piperacilina-tazobactam IV antes de 1 hora",
                       feedback="Correcta — pip-tazo cubre foco abdominal (anaerobios + BGN), y antibiótico ≤1 h en shock."),
                    op("e", "Reevaluar lactato seriadamente",
                       feedback="Correcta — umbral 2 mmol/L para resucitar y reevaluar dinámicamente."),
                ]),
            etapa(3, "diagnostico",
                "A las 6 h: persiste hipotenso, requiere noradrenalina 0,30 µg/kg/min para "
                "MAP 65, lactato 3,1, ya recibió 30 mL/kg de Ringer. ¿Qué intervención adicional "
                "se justifica?",
                [
                    op("a", "Vitamina C IV en megadosis + hidrocortisona + tiamina",
                       feedback="VITAMINS y LOVIT fueron NEGATIVOS — SSC 2026 NO recomienda vitamina C."),
                    op("b", "Hidrocortisona IV 200 mg/d (50 mg c/6 h) por vasopresores en escalada", correcta=True,
                       feedback="Correcto. Hidrocortisona en shock séptico con noradrenalina ≥0,25 µg/kg/min por ≥4 h."),
                    op("c", "Iniciar inmunoglobulinas IV",
                       feedback="No es estándar en sepsis no específica."),
                    op("d", "Hemoperfusión con polimixina B de rutina",
                       feedback="SSC 2026 sugiere EN CONTRA (TIGRIS con señal solo en shock endotóxico — área en evolución)."),
                    op("e", "Cambiar Ringer lactato por gelatinas o coloides",
                       feedback="No se recomiendan coloides; mantener cristaloides balanceados."),
                ]),
        ],
        "resumen_final": (
            "Shock séptico según SSC 2026:\n"
            "• Tamizaje: NEWS2 (preferido) sobre qSOFA (degradado).\n"
            "• Bundle hora-1: lactato + hemocultivos + ATB amplio espectro ≤1 h en shock "
            "+ cristaloides balanceados (30 mL/kg condicional, individualizar).\n"
            "• Vasopresores PRECOCES junto a fluidos (noradrenalina 1ª línea), MAP ≥65.\n"
            "• Hidrocortisona 200 mg/d si vasopresores en escalada.\n"
            "• NO vit C, NO HAT therapy, NO polimixina B de rutina."
        ),
    },
    {
        "id": "CASO-GUIA-005-DM2",
        "titulo": "DM2 con ASCVD y obesidad — AACE 2026",
        "especialidad": "endocrino",
        "tema": "diabetes",
        "nivel": "intermedio",
        "guia_fuente": "AACE 2026",
        "version_actual": 1,
        "etapas": [
            etapa(1, "anamnesis",
                "Hombre 54 años con DM2 (HbA1c 8,2%), IAM hace 2 años (ASCVD establecida), "
                "IMC 34, eGFR 75. Toma metformina 850 mg c/12h y atorvastatina 40 mg. PA "
                "controlada. AACE 2026 prioriza qué pilar terapéutico antes de la HbA1c?",
                [
                    op("a", "Comorbilidades (CV/renal/hepáticas) — evaluar protección CV-renal primero", correcta=True,
                       feedback="Correcto. AACE 2026 introduce el «comorbidities-/complications-centric» ANTES que el glucose-centric."),
                    op("b", "Glicemia ayuno como única guía",
                       feedback="No — ya no es así en AACE 2026."),
                    op("c", "Iniciar insulina basal de inmediato por HbA1c >8%",
                       feedback="Insulina se inicia con HbA1c >10%, síntomas catabólicos o glicemia >300."),
                    op("d", "Suspender metformina antes de añadir nada",
                       feedback="Metformina sigue válida; no se suspende rutinariamente."),
                    op("e", "Aumentar metformina a 1000 mg c/8h",
                       feedback="No es la conducta principal; la prioridad es protección CV/renal."),
                ]),
            etapa(2, "manejo",
                "Decide intensificar terapia. Considerando que es ASCVD establecida + obesidad, "
                "¿cuál es la elección PREFERIDA según AACE 2026?",
                [
                    op("a", "Glibenclamida 5 mg/día",
                       feedback="AACE 2026 LIMITA sulfonilureas — sin beneficio CV/renal, riesgo hipoglicemia, ↑peso."),
                    op("b", "Sitagliptina 100 mg/día",
                       feedback="DPP-4i: rol limitado, peso-neutro, sin beneficio CV — no preferido en ASCVD."),
                    op("c", "Semaglutida SC semanal (GLP-1 RA con beneficio CV probado)", correcta=True,
                       feedback="Correcto. AACE 2026 prefiere GLP-1 RA con beneficio CV probado (semaglutida, dulaglutida, liraglutida) en ASCVD + obesidad."),
                    op("d", "Pioglitazona 30 mg/día",
                       feedback="Útil si resistencia insulínica/MASH; pero no es la 1ª línea con ASCVD."),
                    op("e", "Insulina glargina nocturna",
                       feedback="Indicada con HbA1c >10% o glicemia >300; no es la preferida ahora."),
                ]),
            etapa(3, "diagnostico",
                "A los 6 meses: HbA1c 6,8%, IMC 31. Pierde 7% del peso. Desarrolla microalbuminuria "
                "60 mg/g (nueva). eGFR 70. ¿Qué intervención agrega?",
                [
                    op("a", "Empagliflozina 10 mg/d (SGLT2i)", correcta=True,
                       feedback="Correcto. ERC con albuminuria → SGLT2i 1ª línea por protección renal (eGFR ≥20 permite uso)."),
                    op("b", "Suspender semaglutida y volver a metformina sola",
                       feedback="Funciona bien; no suspender."),
                    op("c", "Glibenclamida añadida",
                       feedback="Sulfonilureas no agregan beneficio CV/renal y aumentan riesgo de hipoglicemia."),
                    op("d", "Insulina NPH nocturna",
                       feedback="HbA1c 6,8% no requiere insulina."),
                    op("e", "DPP-4i",
                       feedback="No combinar DPP-4 con GLP-1 y no ofrece protección renal."),
                ]),
        ],
        "resumen_final": (
            "DM2 según AACE 2026 — comorbidities-centric:\n"
            "• Evaluar IC, ERC, ASCVD, MASLD, obesidad ANTES de glicemia.\n"
            "• ASCVD → GLP-1 RA con beneficio CV probado (semaglutida, dulaglutida, liraglutida).\n"
            "• ERC → SGLT2i (1ª línea, independiente de HbA1c).\n"
            "• Obesidad → GLP-1 RA o tirzepatida (GIP/GLP-1).\n"
            "• Sulfonilureas: LIMITAR/discontinuar. Metformina válida sin comorbilidad mayor.\n"
            "• HbA1c <7,5%: monoterapia. 7,5–9%: dual. >9%: triple. >10% o síntomas: INSULINA."
        ),
    },
    {
        "id": "CASO-GUIA-006-DISLIPIDEMIA",
        "titulo": "Dislipidemia con Lp(a) elevada — AHA 2026",
        "especialidad": "cardiología",
        "tema": "dislipidemia",
        "nivel": "intermedio",
        "guia_fuente": "AHA/ACC 2026",
        "version_actual": 1,
        "etapas": [
            etapa(1, "anamnesis",
                "Mujer 48 años, sin eventos CV, padre con IAM a los 50. Sin DM. PA 130/80. "
                "IMC 26. LDL-C 160 mg/dL, HDL 50, TG 130. PREVENT a 10 años: 8% (intermedio). "
                "¿Qué examen ADICIONAL solicita por primera vez según AHA 2026?",
                [
                    op("a", "Lp(a) sérica UNA VEZ EN LA VIDA", correcta=True,
                       feedback="Correcto. AHA 2026 incorpora Lp(a) como cribado de por vida en TODOS los adultos (Clase I), primera vez en guía estadounidense."),
                    op("b", "Apo A-I",
                       feedback="No estándar en cribado."),
                    op("c", "Homocisteína",
                       feedback="No es marcador establecido para guiar manejo."),
                    op("d", "Cribado de Lp(a) cada 5 años",
                       feedback="Lp(a) es genéticamente determinada — UNA SOLA VEZ basta."),
                    op("e", "Solo perfil lipídico estándar repetido",
                       feedback="AHA 2026 añade Lp(a) como nuevo Clase I."),
                ]),
            etapa(2, "manejo",
                "Lp(a) resulta 180 nmol/L (significativamente elevada, umbral >125). Riesgo "
                "intermedio (PREVENT 8%) + Lp(a) alta + historia familiar. ¿Cuál es el manejo "
                "inicial?",
                [
                    op("a", "Estatina alta intensidad (atorvastatina 40-80 o rosuvastatina 20-40)", correcta=True,
                       feedback="Correcto. AHA 2026 sube la indicación: Lp(a) elevada + riesgo intermedio justifica estatina alta intensidad para LDL <70 si posible."),
                    op("b", "Solo dieta y ejercicio sin estatina",
                       feedback="Insuficiente con Lp(a) elevada + riesgo intermedio."),
                    op("c", "iPCSK9 como monoterapia",
                       feedback="iPCSK9 es add-on a estatina + ezetimiba, no monoterapia."),
                    op("d", "Pelacarsen (ASO anti-Lp(a))",
                       feedback="Pelacarsen está en fase 3 (HORIZON, 2026); aún no aprobado."),
                    op("e", "Niacina + fenofibrato",
                       feedback="AHA 2026: NO recomendados como add-on rutinario a estatina."),
                ]),
            etapa(3, "diagnostico",
                "A los 3 meses con rosuvastatina 20 mg: LDL-C 95 mg/dL. La paciente no tolera "
                "subir dosis por mialgias. ¿Cuál es el siguiente paso según AHA 2026 (Clase I)?",
                [
                    op("a", "Añadir ezetimiba 10 mg/d", correcta=True,
                       feedback="Correcto. Ezetimiba es Clase I como PRIMER add-on no-estatina cuando LDL no llega a meta."),
                    op("b", "Cambiar a inclisiran de entrada",
                       feedback="Inclisiran tras estatina + ezetimiba; orden establecido por AHA 2026."),
                    op("c", "Suspender estatina y manejar con dieta",
                       feedback="Mialgias suelen ser manejables; estatina de baja dosis o alternativa antes de suspender."),
                    op("d", "Fenofibrato + niacina",
                       feedback="No recomendado como add-on a estatina."),
                    op("e", "iPCSK9 directo sin pasar por ezetimiba",
                       feedback="El orden es: estatina + ezetimiba → iPCSK9 o inclisiran si LDL persiste alto."),
                ]),
        ],
        "resumen_final": (
            "Dislipidemia según AHA/ACC 2026:\n"
            "• Cribado: PREVENT (NO Pooled Cohort); Lp(a) UNA VEZ EN LA VIDA en todo adulto.\n"
            "• Metas LDL-C: intermedio <100; alto <70 o ↓≥50%; muy alto <55.\n"
            "• Estatina alta intensidad: ASCVD, LDL ≥190, DM con factores, muy alto/alto riesgo.\n"
            "• Escalada Clase I: estatina → + ezetimiba → + iPCSK9 (alirocumab, evolocumab) o "
            "inclisiran (c/6 meses).\n"
            "• Ácido bempedoico en intolerancia (CLEAR Outcomes ↓MACE 13%).\n"
            "• TG 150-499 con ASCVD/DM: icosapent ethyl 4 g/d (REDUCE-IT)."
        ),
    },
    {
        "id": "CASO-GUIA-007-HPYLORI",
        "titulo": "H. pylori — ACG 2024 (sin claritromicina como 1ª línea)",
        "especialidad": "gastroenterología",
        "tema": "h_pylori",
        "nivel": "intermedio",
        "guia_fuente": "ACG 2024",
        "version_actual": 1,
        "etapas": [
            etapa(1, "anamnesis",
                "Mujer 45 años con dispepsia y úlcera duodenal en endoscopía. Test de aliento "
                "para H. pylori positivo. Vive en Chile (área de alta resistencia a "
                "claritromicina). Sin alergias. ¿Cuál es el tratamiento de PRIMERA LÍNEA "
                "según ACG 2024?",
                [
                    op("a", "Triple terapia con claritromicina + amoxicilina + PPI × 14 días",
                       feedback="ACG 2024 ELIMINA esta como 1ª línea por resistencia >15% a claritromicina en muchas regiones."),
                    op("b", "Cuádruple con bismuto × 14 días (PPI + bismuto + tetraciclina + metronidazol)", correcta=True,
                       feedback="Correcto. ACG 2024: primera línea es cuádruple con bismuto optimizada × 14 d o vonoprazan dual."),
                    op("c", "Levofloxacina + amoxicilina × 7 días",
                       feedback="Levo se reserva para fallo de 1ª línea o rifabutina triple."),
                    op("d", "PPI solo × 14 días",
                       feedback="PPI solo NO erradica H. pylori."),
                    op("e", "Metronidazol solo",
                       feedback="Monoterapia no erradica."),
                ]),
            etapa(2, "diagnostico",
                "¿Cuándo y cómo confirma erradicación?",
                [
                    op("a", "Test de aliento o antígeno fecal ≥4 semanas post-tratamiento", correcta=True,
                       feedback="Correcto. ACG 2024 — test ≥4 semanas tras finalizar antibióticos (y suspender PPI ≥2 sem)."),
                    op("b", "Serología IgG anti-H. pylori inmediatamente",
                       feedback="Serología persiste positiva por años — NO útil para confirmar erradicación."),
                    op("c", "Endoscopía obligatoria a los 6 meses",
                       feedback="Solo si úlcera gástrica o complicación, no rutinaria."),
                    op("d", "No requiere confirmación si los síntomas mejoran",
                       feedback="Síntomas no son fiables para confirmar erradicación."),
                    op("e", "Test de aliento al día siguiente del último antibiótico",
                       feedback="Falsos negativos por PPI o antibiótico reciente."),
                ]),
            etapa(3, "manejo",
                "El test de aliento 6 semanas después es POSITIVO (no se erradicó). ¿Qué "
                "alternativa de 2ª línea recomienda según ACG 2024?",
                [
                    op("a", "Rifabutina triple (PPI + amoxicilina + rifabutina) × 14 días", correcta=True,
                       feedback="Correcto. Rifabutina triple es alternativa de rescate (también vonoprazan dual si no se usó antes)."),
                    op("b", "Repetir la misma cuádruple con bismuto",
                       feedback="No se repite el mismo esquema fallido."),
                    op("c", "Volver a claritromicina",
                       feedback="Tras fallar primera línea sin claritromicina, NO usarla."),
                    op("d", "Suspender tratamiento porque dos intentos son suficientes",
                       feedback="Si persiste sintomática o úlcera complicada, se intentan esquemas de rescate."),
                    op("e", "Bismuto + omeprazol como única medida",
                       feedback="Bismuto solo no erradica H. pylori."),
                ]),
        ],
        "resumen_final": (
            "H. pylori según ACG 2024:\n"
            "• Primera línea: CUÁDRUPLE CON BISMUTO × 14 días (PPI + bismuto + tetraciclina "
            "+ metronidazol) o VONOPRAZAN DUAL (vonoprazan 20 mg c/12h + amoxicilina 1 g c/8h × 14 d).\n"
            "• ELIMINADA la triple con claritromicina como 1ª línea por resistencia >15%.\n"
            "• Confirmación: test de aliento o antígeno fecal ≥4 sem post-tratamiento "
            "(suspender PPI ≥2 sem).\n"
            "• Rescate (2ª línea): rifabutina triple o vonoprazan dual (si no usado), levofloxacina."
        ),
    },
]


def main():
    casos = json.load(open(CASOS))
    defs  = json.load(open(DEFS))

    # Anexar defs nuevas
    ids_def = {d.get("id") for d in defs.get("definiciones", [])}
    nuevos_def = 0
    for nd in DEFS_GUIAS:
        if nd["id"] not in ids_def:
            defs["definiciones"].append(nd)
            nuevos_def += 1
    defs["meta"]["total"] = len(defs["definiciones"])
    defs["meta"]["version"] = "v3-guias"
    defs["meta"]["descripcion"] = (
        "Definiciones de fármacos, conceptos, herramientas y guías clínicas "
        "actualizadas (2014-2026). Incluye consensos de nomenclatura y guías "
        "primarias (GINA, GOLD, ESC, SSC, ADA, AACE, AHA, ACG)."
    )

    # Anexar casos nuevos
    ids_caso = {c.get("id") for c in casos.get("casos", [])}
    nuevos_caso = 0
    for nc in CASOS_NUEVOS:
        if nc["id"] not in ids_caso:
            casos["casos"].append(nc)
            nuevos_caso += 1
    casos["meta"]["total"] = len(casos["casos"])
    casos["meta"]["version"] = "v3-guias"
    casos["meta"]["descripcion"] = (
        "Casos clínicos paso a paso para temas más preguntados en EUNACOM, "
        "incluyendo escenarios alineados con guías actualizadas 2024-2026."
    )

    json.dump(defs,  open(DEFS,  "w"), ensure_ascii=False, indent=2)
    json.dump(casos, open(CASOS, "w"), ensure_ascii=False, indent=2)

    print(f"Definiciones nuevas: {nuevos_def} (total {defs['meta']['total']})")
    print(f"Casos nuevos: {nuevos_caso} (total {casos['meta']['total']})")


if __name__ == "__main__":
    main()
