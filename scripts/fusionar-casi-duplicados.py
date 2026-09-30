"""
Fusiona preguntas duplicadas que difieren SOLO en valores numéricos, cuando la
diferencia se debe a que una copia PERDIÓ números en la extracción del PDF.

La deduplicación de v1.11.0 comparaba el enunciado exacto (normalizado), así
que no vio estos pares: la copia GUEV-… suele haber perdido los valores
("t°: 35,0 °C" → "t°: °C", "suero fisiológico al 0,9%" → "al %"). En una
pregunta clínica los números son la pregunta, así que la copia degradada es
engañosa o directamente incontestable.

Para cada grupo de enunciados que coinciden al quitarles los números:

  - Mismos números en el mismo orden → duplicado exacto con otro formato.
  - Los números de una copia son una SUBSECUENCIA de los de otra → la copia
    corta perdió valores. Sobrevive la completa.
  - Números distintos (no es subsecuencia) → pueden ser dos casos clínicos
    distintos con la misma viñeta. NO se fusionan.
  - Si las alternativas correctas no coinciden (ignorando números) → NO se
    fusionan y se listan para revisión.

Cada fusión se agrega a meta.reemplazos para que seed.js traspase marcas,
estadísticas y repaso a la superviviente en las instalaciones existentes.

Uso: python3 scripts/fusionar-casi-duplicados.py [--aplicar]
"""
import json, re, sys, unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APLICAR = '--aplicar' in sys.argv
NUM = re.compile(r'\d+(?:[.,]\d+)?')

def base(s):
    s = unicodedata.normalize('NFD', s or ''); s = ''.join(c for c in s if unicodedata.category(c) != 'Mn').lower()
    s = NUM.sub('', s)
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z ]', ' ', s)).strip()

def texto_total(p):
    return p['enunciado'] + ' ' + ' '.join(o.get('texto', '') for o in p['opciones'])

def numeros(p):
    # Solo el enunciado: la opción e de una copia sin reparar arrastra texto de
    # la justificación con sus propios números y falsea la comparación.
    return [n.replace(',', '.') for n in NUM.findall(p['enunciado'])]

def numeros_sin_uno(p):
    # La extracción del PDF inserta un "1" suelto donde había una nota al pie
    # ("frecuencia 1 cardíaca", "a realizar 1 es"). Si cuenta como número, la
    # copia corrupta "gana" por tener más valores y se elimina la limpia
    # (47 casos). Para comparar se ignora; para elegir, gana la que tiene menos.
    return [n for n in numeros(p) if n != '1']

def coincide(corto, largo):
    # "12" coincide con "12.5": la extracción suele perder el decimal.
    return corto == largo or (('.' not in corto) and largo.split('.')[0] == corto)

def es_subsecuencia(corta, larga):
    i = 0
    for x in corta:
        while i < len(larga) and not coincide(x, larga[i]): i += 1
        if i == len(larga): return False
        i += 1
    return True

# ── Decisiones manuales tras revisar los pares ambiguos uno por uno ──
# Copias degradadas que el criterio automático no reconoce: en vez de perder el
# número, la extracción insertó un "1" suelto o cambió "5,3/5,0" por "520".
# Mismas alternativas y misma respuesta. Clave: copia que se elimina.
FUSIONAR_MANUAL = {
    'GUEV-CAR-0183': 'R02038', 'GUEV-CIR-0062': 'R00152', 'GUEV-MED-0039': 'R00337',
    'GUEV-MED-0040': 'R01461', 'GUEV-PED-0035': 'R00883', 'GUEV-INF-0150': 'R00980',
    'GUEV-PED-0398': 'R02054', 'GUEV-NEF-0012': 'R01244', 'GUEV-DER-0134': 'R01247',
    'GUEV-GIN-0081': 'R01252',
    # La correcta "difiere" solo porque la copia GUEV arrastra el inicio de la
    # justificación en la alternativa; es la misma respuesta.
    'GUEV-END-0006': 'R00298',
}
# Casos clínicos DISTINTOS con la misma viñeta: el número cambia la pregunta.
MANTENER = {
    frozenset({'GUEV-INF-0125', 'GUEV-INF-0133'}),  # CD4 200 vs 400 hace 2 años
    frozenset({'GUEV-OBS-0022', 'GUEV-OBS-0050'}),  # glicemia basal 105 vs 100 (límite diagnóstico)
    frozenset({'GUEV-OBS-0035', 'GUEV-OBS-0067'}),  # 7 cm (fase activa, sin tocolisis) vs 1 cm
}
# Arreglos de texto en la superviviente con lo que conserva la otra copia.
CORRECCIONES = {
    'R00883':        [('está en percentil para su edad', 'está en percentil 8 para su edad')],
}

# La superviviente se elige por los números del enunciado, pero a veces la copia
# eliminada tenía la justificación completa. Superviviente → copia de la que se
# toma la justificación.
JUSTIFICACION_DE = {
    'R02038': 'GUEV-CAR-0094', 'R02037': 'GUEV-CAR-0092', 'R02026': 'GUEV-NEU-0130',
    'GUEV-DER-0068': 'R00240',   # la superviviente empieza a media frase
}
# GUEV-PED-0035 trae el razonamiento de la pregunta (retraso constitucional)
# que a R00883 le falta, pero rotado en trozos: se agrega al final.
AGREGAR_A_JUSTIFICACION = {
    'R00883': ' Sin embargo, la pregunta orienta a un retraso constitucional del crecimiento (RCC), '
              'ya que sus padres son bastante altos, lo que no se condice con la talla en percentil 8 '
              'y además tiene una edad ósea menor, con un delta de 2 años, que es diagnóstico de RCC, '
              'el que tiene talla final normal.',
}

def correcta(p):
    o = next((o for o in p['opciones'] if o.get('correcta')), None)
    return base(o['texto'])[:60] if o else None

def main():
    path = ROOT / 'data' / 'banco_inicial.json'
    data = json.load(open(path))
    if set(FUSIONAR_MANUAL) <= set(data['meta'].get('reemplazos', {})):
        print('ya aplicado: las fusiones manuales están en meta.reemplazos'); return
    grupos = defaultdict(list)
    for p in data['preguntas']:
        grupos[base(p['enunciado'])].append(p)

    cat = {'manual': [], 'distintas_revisadas': [], 'formato': [], 'perdio_numeros': [], 'valores_distintos': [], 'respuesta_distinta': []}
    eliminar = {}
    for g in (v for v in grupos.values() if len(v) > 1):
        # Superviviente candidata: la que conserva más números; empate → id R0 (suele ser la completa).
        g = sorted(g, key=lambda p: (len(numeros_sin_uno(p)), -numeros(p).count('1'),
                                     p['id_unico'].startswith('R')), reverse=True)
        sup = g[0]
        for otra in g[1:]:
            ids = f"{sup['id_unico']} ← {otra['id_unico']}"
            if frozenset({sup['id_unico'], otra['id_unico']}) in MANTENER:
                cat['distintas_revisadas'].append(ids); continue
            if FUSIONAR_MANUAL.get(otra['id_unico']) == sup['id_unico']:
                cat['manual'].append(ids); eliminar[otra['id_unico']] = sup['id_unico']; continue
            if correcta(sup) != correcta(otra):
                cat['respuesta_distinta'].append(ids); continue
            ns, no = numeros_sin_uno(sup), numeros_sin_uno(otra)
            if ns == no:
                cat['formato'].append(ids); eliminar[otra['id_unico']] = sup['id_unico']
            elif es_subsecuencia(no, ns):
                cat['perdio_numeros'].append(f"{ids}  ({len(ns)} vs {len(no)} números)")
                eliminar[otra['id_unico']] = sup['id_unico']
            else:
                cat['valores_distintos'].append(f"{ids}  {ns[:6]} vs {no[:6]}")

    for k, v in cat.items():
        print(f"{k}: {len(v)}")
        muestra = v if k in ('valores_distintos', 'respuesta_distinta', 'distintas_revisadas') else v[:4]
        for x in muestra: print(f"    {x}")
    print(f"\nse eliminan {len(eliminar)} copias degradadas")
    faltan = set(FUSIONAR_MANUAL) - set(eliminar)
    assert not faltan, f"fusiones manuales que no calzaron con ningún grupo: {faltan}"

    idx = {p['id_unico']: p for p in data['preguntas']}
    for pid, pares in CORRECCIONES.items():
        for a, b in pares:
            assert a in idx[pid]['enunciado'], f"{pid}: no se encontró «{a}»"
            idx[pid]['enunciado'] = idx[pid]['enunciado'].replace(a, b)
    for sup, otra in JUSTIFICACION_DE.items():
        assert eliminar.get(otra) == sup, f"{otra} no se fusiona en {sup}"
        idx[sup]['justificacion'] = idx[otra]['justificacion']
    for pid, extra in AGREGAR_A_JUSTIFICACION.items():
        idx[pid]['justificacion'] = idx[pid]['justificacion'].rstrip() + extra

    if APLICAR:
        antes = len(data['preguntas'])
        data['preguntas'] = [p for p in data['preguntas'] if p['id_unico'] not in eliminar]
        # Encadenar: si A ya apuntaba a B y ahora B se elimina hacia C, A → C.
        rem = data['meta'].setdefault('reemplazos', {})
        rem.update(eliminar)
        for k in list(rem):
            v = rem[k]; vistos = set()
            while v in rem and v not in vistos:
                vistos.add(v); v = rem[v]
            rem[k] = v
        data['meta']['reemplazos'] = dict(sorted(rem.items()))
        data['meta']['total'] = len(data['preguntas'])
        json.dump(data, open(path, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
        print(f"✓ aplicado: {antes} → {len(data['preguntas'])} preguntas; reemplazos: {len(rem)}")
    else:
        print('(simulación — usar --aplicar)')

if __name__ == '__main__':
    main()
