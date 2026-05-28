"""
Clasifica las preguntas con especialidad_principal='mixto' por keywords.

Cada pregunta es texto (enunciado + opciones + justificación). Se cuenta
cuántas keywords de cada especialidad aparecen y se asigna a la de mayor
puntaje. Si no hay un ganador claro, queda como 'mixto'.
"""
import json
import os
import re
import unicodedata
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANCO = os.path.join(ROOT, "data/banco_inicial.json")


def norm(s: str) -> str:
    s = s.lower()
    s = "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )
    return s


# Keywords por especialidad. Términos suficientemente específicos para
# evitar colisiones obvias. Cada match suma 1 al puntaje.
KEYWORDS = {
    "cardio": [
        "infarto", "iam", "isquemia miocard", "angina", "coronario",
        "fibrilacion auricular", "flutter", "taquicardia ventricular",
        "extrasist", "soplo", "estenosis aortica", "insuficiencia mitral",
        "insuficiencia cardiaca", "edema pulmonar agudo", "epa",
        "hipertension arterial", "presion arterial", "antihipertens",
        "tep ", "tromboembolismo pulmon", "trombosis venosa",
        "marcapaso", "bloqueo av", "bloqueo auriculoven", "ekg",
        "electrocardiograma", "troponina", "ortopnea", "disnea paroxistica",
        "sindrome coronario", "betabloqueo", "valvulopati",
        "endocarditis", "miocarditis", "pericarditis",
    ],
    "dermato": [
        "psoriasis", "dermatitis", "eccema", "eczema", "acne", "rosacea",
        "pitiriasis", "tina", "tinea", "dermatofito", "candidiasis cutanea",
        "verruga", "herpes simplex", "herpes zoster", "varicela",
        "melanoma", "carcinoma basocelular", "espinocelular",
        "queratosis", "nevus", "nevo", "vitiligo", "alopecia",
        "urticaria", "pemfigo", "penfigo", "penfigoide", "rosaceo",
        "impetigo", "celulitis cutanea", "erisipela",
        "exantema", "rash", "vesicula", "bula", "ampolla",
        "molusco contagioso", "escabiosis", "sarna",
    ],
    "endocrino": [
        "diabetes mellitus", "dm2", "dm1", "diabetes", "glicemia",
        "hemoglobina glico", "hba1c", "metformina", "insulina",
        "hipotiroidismo", "hipertiroidismo", "tsh", "t4 libre", "t3 ",
        "hashimoto", "graves", "tiroiditis", "nodulo tiroideo",
        "cushing", "addison", "feocromocitoma", "aldosteronismo",
        "hiperprolactinemia", "prolactina", "acromegalia", "hipofisis",
        "cetoacidosis", "cad ", "hiperosmolar",
        "osteoporosis", "raquitismo", "hipercalcemia", "hipocalcemia",
        "obesidad", "dislipidemia", "hipercolesterolemia",
        "menopausia", "andropausia",
    ],
    "infecto": [
        "antibiotic", "amoxicilina", "ampicilina", "penicilina",
        "ceftriaxona", "cefazolina", "cloxacilina", "vancomicina",
        "azitromicina", "clindamicina", "ciprofloxacino", "metronidazol",
        "vih", "sida", "tuberculosis", "tbc",
        "sifilis", "vdrl", "treponema", "gonorrea",
        "malaria", "dengue", "zika", "chikungun",
        "hepatitis a", "hepatitis b", "hepatitis c",
        "neumococo", "meningococ", "hemofilus", "estreptococ",
        "estafilococ", "salmonella", "shigella", "escherichia",
        "pseudomona", "clostridium", "candida", "criptococ",
        "toxoplasm", "citomegalovirus", "cmv", "ebv",
        "influenza", "rotavirus", "covid", "coronavirus",
        "antiretroviral", "tar ", "carga viral", "cd4",
    ],
    "neurologia": [
        "accidente vascular encefal", "ave isquem", "ave hemorrag", "ataque cerebrov",
        "convulsion", "epilepsia", "estado epileptic",
        "cefalea", "migrana", "jaqueca",
        "alzheimer", "parkinson", "demencia",
        "esclerosis multiple", "miastenia", "guillain barre", "guillain-barre",
        "neuropati", "polineuropati", "neuralgia",
        "vertigo", "neuronitis", "menier",
        "meningitis", "encefalitis",
        "hemiparesia", "hemiplejia", "hemipleg",
        "afasia", "disartria", "diplopia",
        "reflejo osteotendinos", "babinski",
    ],
    "psiquiatria": [
        "depresion", "depresivo", "ansiedad", "trastorno ansioso",
        "panico", "fobia", "agorafobia",
        "bipolar", "mania", "hipomania",
        "esquizofren", "psicotic", "delirio", "alucinacion",
        "trastorno obsesivo", "toc ", "estres postraumatic",
        "anorex", "bulim", "trastorno alimentar",
        "alcohol", "abstinencia", "delirium tremens",
        "antidepresivo", "fluoxetina", "sertralina", "paroxetina", "citalopram",
        "litio", "valproico", "carbamazepina",
        "antipsicotic", "haloperidol", "risperidona", "olanzapina", "quetiapina",
        "benzodiazepin", "lorazepam", "diazepam", "clonazepam", "alprazolam",
        "personalidad limitrofe", "narcisista", "antisocial",
        "autismo", "tea ", "deficit atencional", "tdah",
    ],
    "gineco": [
        "menstruacion", "menarquia", "menopausia",
        "ovario poliquistic", "sop ", "endometriosis",
        "anticoncept", "diu ", "lng ", "etonogestrel",
        "papanicolaou", "pap ", "cancer cervicouterino", "ccu ",
        "cancer mama", "cancer de mama", "mamografia",
        "miom", "hiperplasia endometr", "polip endometr",
        "vulvov", "candidiasis vagin", "vaginosis", "gardnerella",
        "tricom", "salpingitis", "pip ",
        "leucorrea", "hipogastri", "amenorrea",
    ],
    "obstetricia": [
        "embarazo", "embarazada", "gestaci",
        "preclampsia", "preeclampsia", "eclampsia", "hellp",
        "parto", "cesarea", "puerperio",
        "rotura prematura", "rpm ",
        "trabajo de parto prematuro", "tppt",
        "monitoreo fetal", "lcf ", "fcf ",
        "amenorrea", "fecha de ultima regla", "fur ", "edad gestacional",
        "ecografia obstetric", "translucencia nucal",
        "rh ", "isoinmunizacion", "globulina rh",
        "diabetes gestacional", "ttog",
        "placenta previa", "desprendimiento placent",
        "metrorragia", "hemorragia postparto",
        "lactancia", "calostro",
    ],
    "pediatria": [
        "lactante", "recien nacido", "neonato", "neonatal",
        "prematuro", "rciu ", "post termino",
        "vacuna", "pni ", "inmunizac",
        "convulsion febril", "fiebre sin foco",
        "bronquiolitis", "laringitis", "epiglotitis", "crup",
        "exantema viral", "sarampion", "rubeola", "varicela", "kawasaki",
        "diarrea aguda", "rotavirus pediatr",
        "displasia de cadera", "pie bot", "escoliosis", "pertes",
        "raquitismo", "pdm ", "desarrollo psicomotor",
        "lactancia materna", "ablactacion",
        "talla baja", "obesidad infantil",
        "ttn ", "membrana hialina", "apgar",
    ],
    "cirugia": [
        "apendicitis", "colecistitis", "colelitiasis", "colangitis",
        "pancreatitis aguda", "ulcera peptica", "ulcera gastrica", "ulcera duodenal",
        "hernia inguinal", "hernia umbilical", "hernia hiatal",
        "obstruccion intestin", "abdomen agudo", "peritonitis",
        "diverticulitis", "diverticul",
        "hemorragia digestiva", "melena", "hematemesis", "hematoquecia",
        "endoscopia", "colonoscopia",
        "cancer gastric", "cancer colorrect", "cancer de colon",
        "pneumotor", "neumotorax", "hemotorax", "tubo pleural",
        "anestesia", "preoperatorio", "postoperatorio",
        "abdomen quirurg",
    ],
    "uro": [
        "litiasis renal", "litiasis urin", "calculo renal",
        "infeccion urinaria", "itu ", "pielonefritis", "cistitis",
        "prostatit", "hiperplasia prostatic", "hbp ", "adenoma prost",
        "cancer prostat", "antigeno prostatic", "psa ",
        "incontinencia urinari", "vejiga hiperactiv",
        "hematuria", "proteinuria",
        "varicocele", "hidrocele", "torsion testicul",
        "cancer testicul", "cancer vesic",
        "uretra", "urolog",
    ],
    "trauma": [
        "fractura", "luxacion", "esguince",
        "yeso", "osteosintesis", "reduccion cerrada",
        "menisco", "ligamento cruzado", "lcr ", "lcp ",
        "manguito rotador", "hombro", "epicondilitis", "epitrocleitis",
        "lumbago", "ciatica", "lumbociatica", "hernia nucleo pulposo",
        "tendinitis", "bursitis",
        "fractura expuesta", "gustilo",
        "politraumat", "trauma",
    ],
    "otorrino": [
        "otitis media", "otitis externa", "mastoidit",
        "rinitis alergic", "sinusitis", "rinosinusit",
        "amigdalitis", "faringitis", "laringitis",
        "epistaxis", "tabique nasal",
        "hipoacusia", "audiometr", "tinitus", "acufen",
        "vertigo postur", "vppb",
        "cuerpo extrano nasal", "cuerpo extrano oido",
        "paralisis facial", "bell",
    ],
    "oftalmo": [
        "glaucoma", "presion intraocular",
        "catarata", "facoemulsific",
        "retinopati diabetic", "retinopati hiperten",
        "degeneracion macul", "dmae",
        "conjuntivitis", "queratitis", "uveitis", "uveiti",
        "ojo rojo", "fondo de ojo",
        "estrabismo", "ambliopia",
        "miopia", "hipermetropia", "astigmatismo", "presbicia",
        "lente de contacto",
        "desprendimiento de retina", "neuritis optic",
    ],
    "hemato": [
        "anemia ferrop", "anemia perni", "anemia hemolit", "anemia megaloblas",
        "leucemia", "linfoma", "mieloma multiple",
        "trombocitopen", "purpura trombocit", "pti ",
        "trombofil", "trombocitosis",
        "policitemia", "eritrocitos",
        "neutropenia", "agranulocit",
        "ferritina", "transferrina", "hierro plasm",
        "coombs", "reticulocit",
        "esplenomegal", "hodgkin", "no hodgkin",
        "hemofilia", "von willebrand",
    ],
    "medicina_interna": [
        "epoc", "asma bronquial", "enfermedad pulmonar obstructiva",
        "tabaquismo", "espirometria", "neumonia adquirida",
        "derrame pleural", "tep ", "embolia pulmonar",
        "fibrosis pulmonar",
        "reflujo gastroes", "erge ", "esofagitis",
        "intestino irritable", "sii ",
        "enfermedad inflamatoria intestinal", "cron", "colitis ulcer",
        "cirrosis", "hepatitis cronic", "esteatohepat",
    ],
    "nefro": [
        "insuficiencia renal", "falla renal", "enfermedad renal cronic", "erc ",
        "glomerulonefritis", "sindrome nefrotic", "sindrome nefritic",
        "creatinina", "uremia", "dialisis", "hemodialisi", "peritoneal",
        "trasplante renal",
        "acidosis tubular", "tubular renal",
        "nefropatia diabet", "microalbuminuri",
    ],
    "salud_publica": [
        "incidencia", "prevalencia", "letalidad", "mortalidad",
        "sensibilidad", "especificidad", "valor predictivo",
        "ensayo clinic", "casos y controles", "cohortes", "estudio transversal",
        "tasa de natalidad", "tasa de mortalidad",
        "atencion primaria", "consultorio", "cesfam",
        "ges ", "auge ", "fonasa", "isapre",
        "etica medica", "consentimiento informado",
        "licencia medica", "mala praxis", "negligencia",
        "bradford hill", "sesgo",
    ],
    "geriatria": [
        "adulto mayor", "delirium", "demencia", "polifarmacia",
        "caida del adulto", "fragilidad",
        "incontinencia geriatric",
    ],
    "urgencias": [
        "paro cardiorespiratorio", "rcp ", "reanimacion cardiopulmon",
        "abc de la urgenc", "shock", "choque",
        "intoxicacion", "envenenamiento",
    ],
}

# Pre-normalizar keywords
KW_NORM = {
    spec: [norm(k) for k in kws] for spec, kws in KEYWORDS.items()
}


def clasificar(texto: str):
    t = norm(texto)
    scores = Counter()
    for spec, kws in KW_NORM.items():
        for k in kws:
            # Buscar como substring; los espacios al final fuerzan límite de palabra básico
            if k in t:
                scores[spec] += 1
    if not scores:
        return None, {}
    # Si hay ganador claro (al menos 2 matches O diferencia >=2 con el 2do)
    top = scores.most_common(3)
    if top[0][1] >= 3:
        return top[0][0], dict(top)
    if top[0][1] >= 2 and (len(top) == 1 or top[0][1] - top[1][1] >= 1):
        return top[0][0], dict(top)
    if top[0][1] == 1 and len(top) == 1:
        return top[0][0], dict(top)
    return None, dict(top)


def main():
    d = json.load(open(BANCO, encoding="utf-8"))
    pregs = d["preguntas"]
    mixto_antes = sum(1 for p in pregs if p["especialidad_principal"] == "mixto")
    asignadas = Counter()
    sin_asignar = 0
    for p in pregs:
        if p["especialidad_principal"] != "mixto":
            continue
        texto = (
            p["enunciado"]
            + " "
            + " ".join(o["texto"] for o in p["opciones"])
            + " "
            + (p.get("justificacion") or "")
        )
        spec, scores = clasificar(texto)
        if spec:
            p["especialidad_principal"] = spec
            p["_clasificacion_auto"] = scores
            asignadas[spec] += 1
        else:
            sin_asignar += 1

    # Bump version
    prev = d["meta"].get("version", "reconstruccion_v3")
    match = re.search(r"v(\d+)$", prev)
    next_v = int(match.group(1)) + 1 if match else 4
    d["meta"]["version"] = f"reconstruccion_v{next_v}"
    d["meta"]["clasificacion_mixto"] = {
        "mixto_inicial": mixto_antes,
        "asignadas": sum(asignadas.values()),
        "siguen_mixto": sin_asignar,
        "por_especialidad": dict(asignadas.most_common()),
    }
    with open(BANCO, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(
        f"Mixto inicial: {mixto_antes} | Asignadas: {sum(asignadas.values())} | "
        f"Siguen mixto: {sin_asignar}"
    )
    print("Por especialidad:", dict(asignadas.most_common()))


if __name__ == "__main__":
    main()
