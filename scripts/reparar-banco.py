"""
Reparación integral del banco. El ORDEN importa y se aprendió probando:

  1. LIGADURAS    — primero. Si no, las copias con "refiejos" y "reflejos" no
                    se ven iguales y la deduplicación las deja pasar a ambas.
  2. DEDUPLICAR   — antes de reparar, para no arreglar tres veces la misma
                    pregunta y que el dedup descarte dos de esos arreglos.
  3. PARSER       — reparar el corte solo en los supervivientes.

MODO SIMULACIÓN por defecto. Con --aplicar escribe data/banco_inicial.json.
"""
import json, re, sys, statistics, unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path('/home/user/INTERN.OS')
APLICAR = '--aplicar' in sys.argv

# ═══════════════════════════════════════════════════════════════════
#  Resolución manual de las contradicciones REALES entre duplicados.
#  Clave: id que SOBREVIVE. Valor: por qué.
#  (Los demás grupos "contradictorios" resultaron ser la misma respuesta
#   con el texto corrupto, y se resuelven solos con el criterio general.)
# ═══════════════════════════════════════════════════════════════════
GANADOR_CONTRADICCION = {
    'R00947': 'Angina inestable: la conducta detallada (ECG + O2 + aspirina + '
              'nitroglicerina + troponinas) enseña más que "manejar como SCA".',
    'R01572': 'Sarna en embarazo: permetrina 5% es el estándar actual '
              '(categoría B). La vaselina azufrada es la alternativa antigua.',
    'R01443': 'NAC grave en mayor de 80 con confusión (CURB-65 alto): requiere '
              'ceftriaxona MÁS un cubrimiento de atípicos. Ceftriaxona sola es '
              'insuficiente.',
    'R00891': 'Exámenes del primer trimestre: el registro basal no estresante '
              'es de tercer trimestre, así que es la excepción correcta.',
    'R01914': 'Criterios de Wilson y Jungner: la existencia de tratamiento '
              'eficaz es el criterio clásico que justifica un tamizaje.',
}

# ═══════════════════════════════════════════════════════════════════
#  1. Utilidades
# ═══════════════════════════════════════════════════════════════════
def norm(s):
    s = unicodedata.normalize('NFD', str(s or ''))
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9 ]', ' ', s.lower())).strip()

def justif_truncada(p):
    j = (p.get('justificacion') or '').strip()
    return bool(j) and j[:1].islower()

def tiene_bug_parser(p):
    ops = p.get('opciones') or []
    if len(ops) < 3: return False
    L = [len(o.get('texto','')) for o in ops]
    return L[-1] > max(L[:-1]) * 2.2 and L[-1] > 90 and justif_truncada(p)

# ═══════════════════════════════════════════════════════════════════
#  2. Deduplicación
# ═══════════════════════════════════════════════════════════════════
def puntaje_copia(p):
    """Mayor es mejor. Decide qué copia del grupo sobrevive."""
    s = 0
    if p['id_unico'] in GANADOR_CONTRADICCION: s += 1000   # decisión médica explícita
    if not justif_truncada(p):                s += 100    # justificación completa
    if not tiene_bug_parser(p):               s += 50     # opciones limpias
    if p.get('utilizable') is not False:      s += 20     # utilizable
    if p['id_unico'].startswith('GUEV-'):     s += 10     # trazabilidad de especialidad
    s += min(len(p.get('justificacion') or '') / 100, 10) # justificación más rica
    if p.get('tema_validado'):                s += 2
    return s

def deduplicar(banco):
    grupos = defaultdict(list)
    for p in banco:
        grupos[norm(p['enunciado'])].append(p)
    supervivientes, descartados, decisiones = [], 0, []
    for clave, copias in grupos.items():
        if len(copias) == 1 or not clave:
            supervivientes.extend(copias); continue
        copias_ord = sorted(copias, key=puntaje_copia, reverse=True)
        gana = copias_ord[0]
        # Arrastrar al superviviente los campos de usuario que tengan las otras
        for otra in copias_ord[1:]:
            if otra.get('marcada_revision') and not gana.get('marcada_revision'):
                gana['marcada_revision'] = True
        supervivientes.append(gana)
        descartados += len(copias) - 1
        if gana['id_unico'] in GANADOR_CONTRADICCION:
            decisiones.append((gana['id_unico'],
                               [c['id_unico'] for c in copias_ord[1:]],
                               GANADOR_CONTRADICCION[gana['id_unico']]))
    return supervivientes, descartados, decisiones

# ═══════════════════════════════════════════════════════════════════
#  3. Reparación del corte del parser
# ═══════════════════════════════════════════════════════════════════
INICIO = re.compile(r' (?=[A-ZÁÉÍÓÚÑ¿\[])')
ARRANQUE = {'el','la','los','las','un','una','es','son','esta','este','estas',
 'estos','se','en','por','para','con','sin','tiene','tienen','hay','no','si',
 'lo','como','cuando','donde','actualmente','ante','todo','toda','todos',
 'todas','dado','debido','frente','ambos','ambas','cabe','corresponde',
 'recordar','primero','segundo','tanto','aunque','pero','a','al','del','de'}
SIGLA = re.compile(r'^[A-ZÁÉÍÓÚÑ0-9]{2,}$')
COLGANDO = re.compile(r'\b(el|la|los|las|un|una|de|del|en|con|por|para|y|o|a|al|sin|que)$', re.I)

def partir(p):
    ops = p['opciones']; texto = ops[-1]['texto']
    otras = [len(o['texto']) for o in ops[:-1]]
    objetivo = statistics.median(otras)
    mejor, mejor_score = None, None
    for m in INICIO.finditer(texto):
        izq, der = texto[:m.start()].strip(), texto[m.start():].strip()
        if len(der) < 40 or len(izq) < 3: continue
        score = abs(len(izq) - objetivo)
        if len(izq) > max(otras) * 1.6: score += 100
        prim = der.split()[0].strip('.,;:()[]') if der.split() else ''
        if prim.lower() in ARRANQUE: score -= 60
        if SIGLA.match(prim): score += 150
        if mejor_score is None or score < mejor_score:
            mejor, mejor_score = (izq, der), score
    return mejor

def dudoso(izq, der, otras):
    m = []
    if not der[:1].isupper() and der[:1] not in '¿[': m.append('justificación no empieza en mayúscula')
    if COLGANDO.search(izq.strip()): m.append('opción termina en artículo o conjunción')
    if len(izq) > max(otras) * 1.8 and len(izq) > 60: m.append('opción sigue desproporcionada')
    return m

def reparar_parser(banco):
    reparadas, pendientes = 0, []
    for p in banco:
        if not tiene_bug_parser(p): continue
        r = partir(p)
        if not r:
            pendientes.append((p['id_unico'], 'sin corte confiable')); continue
        izq, der = r
        motivos = dudoso(izq, der, [len(o['texto']) for o in p['opciones'][:-1]])
        if motivos:
            pendientes.append((p['id_unico'], '; '.join(motivos))); continue
        p['opciones'][-1]['texto'] = izq
        p['justificacion'] = (der + ' ' + (p.get('justificacion') or '').strip()).strip()
        reparadas += 1
    return reparadas, pendientes

# ═══════════════════════════════════════════════════════════════════
#  4. Ligaduras fl→fi corrompidas al extraer el PDF original
# ═══════════════════════════════════════════════════════════════════
LIGADURAS = [
    (r'\brefiej', 'reflej'), (r'\bRefiej', 'Reflej'),
    (r'\binfiuenza', 'influenza'), (r'\bInfiuenza', 'Influenza'),
    (r'\binfiama', 'inflama'), (r'\bInfiama', 'Inflama'),
    (r'\bhiperfiexi', 'hiperflexi'), (r'\bHiperfiexi', 'Hiperflexi'),
    (r'\bfiujo', 'flujo'), (r'\bFiujo', 'Flujo'),
    (r'\bfiuido', 'fluido'), (r'\bFiuido', 'Fluido'),
    (r'\bfiexi', 'flexi'), (r'\bFiexi', 'Flexi'),
    (r'\bfiexib', 'flexib'), (r'\brefiuj', 'refluj'), (r'\bRefiuj', 'Refluj'),
    (r'\bconfiict', 'conflict'), (r'\bfiatulen', 'flatulen'),
    (r'\bfiujometr', 'flujometr'), (r'\bfiema\b', 'flema'),
    (r'\bfiogosis', 'flogosis'), (r'\bfiebotom', 'flebotom'),
    (r'\bdesfiec', 'desflec'), (r'\bfiuctu', 'fluctu'), (r'\bFiuctu', 'Fluctu'),
]
CAMPOS_TEXTO = ['enunciado', 'justificacion']

def arreglar_ligaduras(banco):
    tocadas, reemplazos = set(), 0
    for p in banco:
        for c in CAMPOS_TEXTO:
            if not p.get(c): continue
            orig = p[c]
            for pat, rep in LIGADURAS:
                p[c] = re.sub(pat, rep, p[c])
            if p[c] != orig: tocadas.add(p['id_unico']); reemplazos += 1
        for o in p.get('opciones') or []:
            if not o.get('texto'): continue
            orig = o['texto']
            for pat, rep in LIGADURAS:
                o['texto'] = re.sub(pat, rep, o['texto'])
            if o['texto'] != orig: tocadas.add(p['id_unico']); reemplazos += 1
    return len(tocadas), reemplazos

# ═══════════════════════════════════════════════════════════════════
def main():
    path = ROOT / 'data' / 'banco_inicial.json'
    data = json.load(open(path))
    banco = data['preguntas']
    n0 = len(banco)
    bug0 = sum(1 for p in banco if tiene_bug_parser(p))

    print("═" * 74)
    print(f"ESTADO INICIAL: {n0} preguntas, {bug0} con el bug del parser")
    print("═" * 74)

    print("\n[1/3] CORRIGIENDO LIGADURAS fl→fi…")
    tocadas, reemplazos = arreglar_ligaduras(banco)
    print(f"      preguntas corregidas: {tocadas}  ({reemplazos} campos)")
    print("      (va primero: si no, 'refiejos' y 'reflejos' no se ven iguales")
    print("       y la deduplicación deja pasar las dos copias)")

    print("\n[2/3] DEDUPLICANDO…")
    banco, descartados, decisiones = deduplicar(banco)
    print(f"      {n0} → {len(banco)} preguntas  (−{descartados})")
    if decisiones:
        print(f"\n      Contradicciones resueltas con criterio médico ({len(decisiones)}):")
        for gana, perdedores, razon in decisiones:
            print(f"        ✓ {gana}  (descarta {', '.join(perdedores)})")
            print(f"          {razon}")

    print("\n[3/3] REPARANDO EL CORTE DEL PARSER…")
    reparadas, pendientes = reparar_parser(banco)
    print(f"      reparadas automáticamente : {reparadas}")
    print(f"      pendientes de revisión    : {len(pendientes)}")
    for pid, motivo in pendientes:
        print(f"        · {pid:<16} {motivo}")

    bug1 = sum(1 for p in banco if tiene_bug_parser(p))
    print("\n" + "═" * 74)
    print(f"RESULTADO: {n0} → {len(banco)} preguntas")
    print(f"           bug del parser: {bug0} → {bug1}")
    print("═" * 74)

    if APLICAR:
        data['preguntas'] = banco
        if 'meta' in data and isinstance(data['meta'], dict):
            data['meta']['total'] = len(banco)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
        print(f"\n✓ APLICADO en {path}")
    else:
        print("\n(simulación — nada se escribió. Usar --aplicar)")

main()
