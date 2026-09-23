"""
Indexa cada pregunta del banco al código oficial del Perfil EUNACOM 2026.

Agrega tres campos:
  codigo_perfil            "X.YY.S.NNN" si hay match específico,
                           "X.YY.0.000" si solo se pudo determinar la especialidad
  codigo_perfil_titulo     título del ítem del Perfil (trazabilidad)
  codigo_perfil_confianza  tema_directo | fuzzy_alto | fuzzy_medio |
                           especialidad | ambigua

Hay que volver a correrlo cada vez que cambie el banco (deduplicación,
reparaciones, importaciones), porque los ids y los textos cambian.

OJO con tema_validado: la auditoría de septiembre 2026 encontró que es poco
confiable en varios temas (Valvulopatias 3% coherente, Acne 12%, Arritmias
24%). Por eso el mapeo directo solo se aplica a los temas verificados y el
resto cae al fuzzy sobre el enunciado, que es más fiable.
"""
import json, re, math, unicodedata, sys
from collections import defaultdict, Counter
from pathlib import Path

ROOT = Path('/home/user/INTERN.OS')

with open(ROOT / 'data' / 'banco_inicial.json') as f:
    data = json.load(f)
banco = data['preguntas']
with open(ROOT / 'data' / 'referencias' / 'perfil_eunacom_2026.json') as f:
    PERFIL = json.load(f)['items']
PERFIL_CODES = {it['codigo']: it for it in PERFIL}

MAP_ESP = {
    'cardio': (1,'01'), 'endocrino': (1,'03'), 'infecto': (1,'04'),
    'neurologia': (1,'10'), 'hemato': (1,'08'), 'nefro': (1,'09'),
    'geriatria': (1,'07'), 'pediatria': (2,'01'),
    'obstetricia': (3,'01'), 'gineco': (3,'01'),
    'cirugia': (4,'01'), 'trauma': (4,'02'), 'uro': (4,'03'),
    'psiquiatria': (5,'01'),
    'dermato': (6,'01'), 'oftalmo': (6,'02'), 'otorrino': (6,'03'),
    'salud_publica': (7,'01'),
}
MAP_MI_TEMA = {
    'Diabetes_MI': (1,'02'), 'EPOC': (1,'05'), 'Asma_MI': (1,'05'),
    'ITU_MI': (1,'09'), 'Hipotiroidismo_MI': (1,'03'), 'HTA_MI': (1,'01'),
    'Anemia_MI': (1,'08'), 'Sd_constitucional': (1,'08'),
    'Manejo_dolor_cronico': (1,'07'),
}
KEYWORDS_AREA = [
 (r'\b(neumon[ií]a|asma|EPOC|bronquiol|TBC|tuberculos|hemoptisis|derrame pleural|sibilancia)\b',(1,'05')),
 (r'\b(infart|angina|miocardio|valvulopat|arritmi|insuficiencia card|hipertensi[oó]n arterial|HTA\b|soplo|cardiopat)\b',(1,'01')),
 (r'\b(diabetes|glicemi|cetoacid|hiperosmol|hipoglicemi|insulin|metformina|HbA1c)\b',(1,'02')),
 (r'\b(tiroide|hipotiroid|hipertiroid|cushing|adrenal|prolactin|hipof[ií]s|osteoporos)\b',(1,'03')),
 (r'\b(meningitis|encefalitis|VIH|SIDA|sepsis|s[ée]ptic|fiebre tifoide|infeccion\b)\b',(1,'04')),
 (r'\b(gastritis|[uú]lcera g[áa]stric|colelit|colecistitis|hepatitis|cirrosis|pancreatitis|diarrea|colon irrit)\b',(1,'06')),
 (r'\b(adulto mayor|geri[áa]tr|polifarmacia|s[ií]ndrome confusional)\b',(1,'07')),
 (r'\b(anemia|leucemia|linfoma|trombocit|hemoglobin|hemorragi|coagul)\b',(1,'08')),
 (r'\b(creatinin|nefr[oí]tic|nefr[oó]tico|glomerul|h[ée]mat[uú]r|prote[ií]nuri|di[áa]lisis)\b',(1,'09')),
 (r'\b(cefalea|migra[ñn]a|epileps|convuls|ACV\b|ictus|hemorragia subaracnoidea|demencia|Parkinson|esclerosis m[uú]ltiple|vertigo|par[áa]lisis facial)\b',(1,'10')),
 (r'\b(artritis|artralgi|reumat|LES\b|lupus|esclerodermi)\b',(1,'11')),
 (r'\b(pediatr|ni[ñn]o de \d+|reci[ée]n nacido|RN |lactante|preescolar|vacunas? PNI|inmunizaci|displasia|cardiopat[íi]a cong)\b',(2,'01')),
 (r'\b(embaraz|gestaci[oó]n|preeclamps|HELLP|parto|metrorragi|c[eé]rvico-uterin|placenta|RPM|aborto|puerperio)\b',(3,'01')),
 (r'\b(menstr|anticoncep|ginecol|ovario|trompas|endometr|miomas?|menopaus|climater|vulvovagin)\b',(3,'01')),
 (r'\b(quemadura|apendic|hernia inguinal|peritonitis|obstrucci[oó]n intestinal|laparotom|cirug[ií]a|colecist)\b',(4,'01')),
 (r'\b(fractura|esguince|luxaci[oó]n|trauma musc|trauma toracico|polifractura|inmoviliz)\b',(4,'02')),
 (r'\b(pr[oó]stata|HBP|urol|escrotal|testicul|c[áa]ncer renal|c[áa]ncer vesical|c[áa]lculo renal)\b',(4,'03')),
 (r'\b(esquizofreni|psicos|depresi[oó]n|bipolar|p[áa]nico|ansiedad|TOC\b|psiqui[áa]tric|antidepres|antipsic|delirium)\b',(5,'01')),
 (r'\b(acn[eé]|psorias|dermatit|melanoma|c[áa]ncer de piel|tinea|escabios|pediculos|urticari|liquen plan|eritema nod|loxosceles)\b',(6,'01')),
 (r'\b(ojo rojo|conjuntivit|glaucoma|catarat|retinopat|estrabismo|ambliop|pter[ií]gi[oó]n|miop[ií]a|astigmat|hipermetrop)\b',(6,'02')),
 (r'\b(otitis|hipoacusi|tinnitus|vertigo|disfon[íi]a|sinusit|rinit|epistax|amigdal)\b',(6,'03')),
 (r'\b(salud p[uú]blica|epidemio|sensibilidad|especificidad|tamizaje|screening|vigilancia|brote|incidencia|prevalencia|sesgo|estudio de cohort|caso-control|determin|GES|AUGE|notificaci[oó]n obligat)\b',(7,'01')),
]
# Solo los temas cuya etiqueta se verificó coherente con el texto (>85%).
# Los demás (Valvulopatias, Acne, Arritmias, Epilepsia…) caen al fuzzy.
MAP_TEMA_DIRECTO_RAW = {
    'Ca_prostata':'4.03.1.022', 'Diabetes_MI':'1.02.1.005', 'Cefalea':'1.10.1.012',
    'Ojo_rojo':'6.02.1.005', 'VIH':'1.04.1.014', 'VIH_diagnostico':'1.04.1.014',
    'TBC':'1.04.1.028', 'Hipertiroidismo':'1.03.1.003', 'Hipotiroidismo':'1.03.1.002',
    'Demencia':'1.10.1.005', 'Parkinson':'1.10.1.006', 'Esclerosis':'1.10.1.008',
    'Glaucoma':'6.02.1.013', 'Cataratas':'6.02.1.003', 'Epistaxis':'6.03.1.012',
    'Melanoma':'6.01.1.017', 'Psoriasis':'6.01.1.024', 'Dermatitis_atopica':'6.01.1.004',
}
MAP_TEMA_DIRECTO = {t:c for t,c in MAP_TEMA_DIRECTO_RAW.items() if c in PERFIL_CODES}

STOP = set('''de la el los las en con sin para por sobre o e a y u un una unos unas del al
ante bajo desde hasta hacia segun sino su sus mi mis tu tus que cual cuales cuando donde
como mas menos muy paciente pacientes consulta presenta tiene historia evolucion
diagnostico tratamiento manejo enfermedad enfermedades'''.split())

def norm(s):
    s = unicodedata.normalize('NFD', str(s or ''))
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-zA-Z0-9 ]', ' ', s).lower()

def toks(s, minlen=4):
    return [t for t in norm(s).split() if len(t) >= minlen and t not in STOP]

PERFIL_TOKENS = {it['codigo']: set(toks(it['titulo'])) for it in PERFIL}
DF = Counter()
for ts in PERFIL_TOKENS.values():
    for t in ts: DF[t] += 1
N = len(PERFIL)
idf = lambda t: math.log(N / (1 + DF[t]))
PERFIL_IDF = {c: {t: idf(t) for t in ts} for c, ts in PERFIL_TOKENS.items()}
ITEMS = defaultdict(list)
for it in PERFIL: ITEMS[(it['area'], it['especialidad_codigo'])].append(it)
URGENCIA = re.compile(r'\b(agudo|aguda|urgenc|emergenc|shock|crisis|s[uú]bit|inminente|PCR\b|paro cardio|intubaci|inestab|fulminante)\b', re.I)

def inferir(enunciado):
    for pat, ae in KEYWORDS_AREA:
        if re.search(pat, enunciado or '', re.I): return ae
    return None

def match(p):
    esp = p.get('especialidad_principal','')
    tema = p.get('tema_validado','') or ''
    enun = p.get('enunciado','') or ''
    if tema in MAP_TEMA_DIRECTO:
        c = MAP_TEMA_DIRECTO[tema]
        return c, PERFIL_CODES[c]['titulo'], 'tema_directo'
    ae = MAP_ESP.get(esp)
    if ae is None and esp == 'medicina_interna':
        ae = MAP_MI_TEMA.get(tema) or inferir(enun)
    elif ae is None and esp in ('mixto','urgencias','ambigua'):
        ae = inferir(enun)
    if not ae:
        return None, 'Sin especialidad determinable', 'ambigua'
    area, ec = ae
    cands = ITEMS.get((area, ec), [])
    tq = set(toks(enun + ' ' + tema))
    if not cands or not tq:
        return f'{area}.{ec}.0.000', f'Especialidad {area}.{ec}', 'especialidad'
    urg = bool(URGENCIA.search(enun))
    mejor, best, disc = None, 0, False
    for it in cands:
        tt = PERFIL_TOKENS[it['codigo']]
        if not tt: continue
        d = PERFIL_IDF[it['codigo']]
        inter = tt & tq
        if not inter: continue
        tot = sum(d.values())
        sc = (sum(d[t] for t in inter) / tot) if tot else 0
        if urg and it['seccion'] == 2: sc *= 1.20
        if urg and it['seccion'] == 1: sc *= 0.90
        if sc > best:
            best, mejor = sc, it
            disc = max((d[t] for t in inter), default=0) >= (tot/len(tt)) * 0.7
    if mejor and best >= 0.6 and disc: return mejor['codigo'], mejor['titulo'], 'fuzzy_alto'
    if mejor and best >= 0.4 and disc: return mejor['codigo'], mejor['titulo'], 'fuzzy_medio'
    return f'{area}.{ec}.0.000', f'Especialidad {area}.{ec}', 'especialidad'

conf = Counter()
for p in banco:
    c, t, k = match(p)
    p['codigo_perfil'] = c; p['codigo_perfil_titulo'] = t; p['codigo_perfil_confianza'] = k
    conf[k] += 1

print(f'Preguntas indexadas: {len(banco)}')
for k, v in conf.most_common():
    print(f'  {k:<16}{v:>5}  ({100*v/len(banco):.1f}%)')

if '--aplicar' in sys.argv:
    with open(ROOT/'data'/'banco_inicial.json','w',encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',',':'))
    print('\n✓ aplicado')
else:
    print('\n(simulación — usar --aplicar)')
