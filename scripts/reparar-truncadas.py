"""
Segunda pasada sobre las justificaciones truncadas (empiezan en minúscula).

reparar-banco.py detectaba el bug del parser por el LARGO de la última opción
(>2,2x la más larga del resto y >90 caracteres). Ese umbral dejó pasar ~170
casos con el inicio de la justificación pegado a la opción e: cuando el texto
pegado es corto o las otras opciones son largas no se alcanza el umbral.
Ejemplo: R00805, opción e de 200 caracteres contra 127 de la más larga (1,6x).

La señal fiable es la justificación truncada. Tres situaciones:

  1) INICIO PEGADO A LA OPCIÓN e: se corta con el mismo criterio que
     reparar-banco.py, pero sin exigir 40 caracteres mínimos al trozo pegado
     (R00725: "10 / 30 La letalidad son las").
  2) CORTE DENTRO DE LA OPCIÓN: la opción termina a media frase ("…y
     controlar") y la justificación empieza con el resto de la opción
     ("ambulatoriamente."). Se devuelve ese fragmento a la opción. Solo si el
     fragmento es de 1-3 palabras, termina en punto y lo sigue una frase en
     mayúscula.
  3) INICIO PERDIDO: el texto no está en ninguna parte. No se inventa: se
     marca con "[…] " al comienzo.

Después, sobre TODAS las justificaciones, se corrige la ROTACIÓN: el PDF se
extrajo como INICIO | FINAL | MEDIO, así que la justificación termina a media
frase ("…acortamiento del") y su continuación quedó más arriba ("QT,
constipación, debilidad y poliuria."). Se busca el FINAL —la primera frase que
empieza como continuación: al comienzo del texto, o tras un punto pero en
minúscula o con paréntesis— y se mueve detrás del MEDIO. Si no se encuentra,
el final se perdió en la fuente y se marca con " […]".

Uso: python3 scripts/reparar-truncadas.py [--aplicar]
"""
import importlib.util, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APLICAR = '--aplicar' in sys.argv
spec = importlib.util.spec_from_file_location('rb', ROOT / 'scripts' / 'reparar-banco.py')
rb = importlib.util.module_from_spec(spec); spec.loader.exec_module(rb)

def partir_corto(p):
    """Como rb.partir(), pero admite trozos pegados cortos (>= 12 caracteres)."""
    ops = p['opciones']; texto = ops[-1]['texto']
    otras = [len(o['texto']) for o in ops[:-1]]
    objetivo = sorted(otras)[len(otras) // 2]
    mejor, mejor_score = None, None
    for m in rb.INICIO.finditer(texto):
        izq, der = texto[:m.start()].strip(), texto[m.start():].strip()
        if len(der) < 12 or len(izq) < 2: continue
        score = abs(len(izq) - objetivo)
        prim = der.split()[0].strip('.,;:()[]') if der.split() else ''
        if prim.lower() in rb.ARRANQUE: score -= 60
        if rb.SIGLA.match(prim): score += 150
        if mejor_score is None or score < mejor_score:
            mejor, mejor_score = (izq, der), score
    return mejor

FRAG_OPCION = re.compile(r'^(?P<frag>(?:\S+\s+){0,2}\S+?)\.\s+(?P<resto>[A-ZÁÉÍÓÚÑ¿\[][\s\S]*)$')
COLGANDO = re.compile(r'\b(y|o|e|de|del|con|por|para|en|a|al|la|el|los|las|controlar|realizar|indicar|solicitar|según)$', re.I)

FIN_FRASE = re.compile(r'[.!?)\]"»:%]\s*$')
# Límite de frase seguido de algo que NO puede abrir frase: ahí empieza el FINAL.
CONTINUACION = re.compile(r'(?<=[.!?])\s+(?=[a-záéíóúñ(])')
# Puntos que no cierran frase: abreviaturas, iniciales ("T. de angustia",
# "C. Lewy") y numerales de lista ("4. últimamente", "6. Rotura").
ABREVIATURA = re.compile(r'(\b(?i:ej|etc|aprox|vs|p|dr|dra|sr|sra|mg|ml|cc|min|hrs?|seg|cm|kg|no|nº|art)|\b[A-ZÁÉÍÓÚÑ]|\b\d+)\.$')
# "[…]" que dejó reordenar-justificaciones.py delante de un trozo en minúscula:
# no era texto perdido sino el FINAL de una rotación.
HUECO_FINAL = re.compile(r'\[…\]\s+(?=[a-záéíóúñ(])')
LIMITE = re.compile(r'(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ¿\[-])')

def colgando(j):
    return bool(j.strip()) and not FIN_FRASE.search(j.strip())

# FINAL que empieza con sigla en mayúscula: no se distingue de una frase nueva.
FINAL_MANUAL = {'GUEV-CAR-0013': 'QT, constipación, debilidad y poliuria.'}
# Cálculos cuyo resultado se perdió, rehechos a partir de la fórmula del texto.
COMPLETAR = {
    'R00330': '10,5.',   # 10,5 + 0,8 × (4 − 4)
    'R00339': '14,2.',   # 13,4 + 0,8 × (4 − 3)
}

def rotar(j, pid=''):
    """Devuelve (texto reordenado, 'rotada') o (texto con ' […]', 'final_perdido')."""
    j = j.strip()
    inicios = []
    if j[:1].islower() or j[:1] == '(' or j.startswith('[…] '):
        inicios.append(4 if j.startswith('[…] ') else 0)
    for m in CONTINUACION.finditer(j):
        # Tras un numeral sí puede empezar el FINAL ("…siguiente: 1. termine el
        # embarazo."); tras una abreviatura o inicial, no.
        if not ABREVIATURA.search(j[:m.start()]) or re.search(r'\b\d+\.$', j[:m.start()]):
            inicios.append(m.end())
    inicios += [m.end() for m in HUECO_FINAL.finditer(j)]
    inicios = sorted(set(inicios))
    for ini in inicios:
        # El FINAL termina en el siguiente límite de frase; lo que sigue es el MEDIO.
        fin = next((m for m in LIMITE.finditer(j, ini) if not ABREVIATURA.search(j[:m.start()])), None)
        if not fin: continue
        final, medio = j[ini:fin.start()].strip(), j[fin.end():].strip()
        if not medio or colgando(final): continue
        antes = re.sub(r'\s*\[…\]$', '', j[:ini].strip())
        return ' '.join(x for x in (antes, medio, final) if x), 'rotada'
    if pid in FINAL_MANUAL and FINAL_MANUAL[pid] in j:
        final = FINAL_MANUAL[pid]
        return ' '.join(j.replace(final, '', 1).split()) + ' ' + final, 'rotada'
    if pid in COMPLETAR:
        return j + ' ' + COMPLETAR[pid], 'completada'
    # No es texto perdido: termina en una URL de referencia, en una tabla
    # ("Ovario – Compromiso peritoneal") o es una frase corta sin punto.
    if re.search(r'https?://\S+$', j) or ' – ' in j[-80:]:
        return j, 'sin_cambio'
    if len(j) < 80:
        return j + '.', 'completada'
    return j + ' […]', 'final_perdido'

# Casos revisados a mano: el corte automático no es confiable. Para cada uno,
# el texto final de la última opción; lo que sobra de "opción + justificación"
# queda como justificación.
OPCION_FINAL = {
    # La correcta quedó truncada ("…hemograma,") y su resto abría la justificación.
    'R00858': 'Solicitar punción lumbar, hemograma, hemocultivos, radiografía de tórax, '
              'sedimento de orina y urocultivo e iniciar antibióticos endovenosos de inmediato',
    'GUEV-HEM-0051': 'Solicitar exámenes generales, parámetros inflamatorios y sedimento de orina, '
                     'luego decidir conducta según resultados',
    'R02106': 'El 95% de las personas que usan anticonceptivos orales, tienen 1,5 veces más riesgo '
              'de desarrollar cáncer',
    'GUEV-NEU-0109': 'En los cordones posteriores de la médula',   # " - Los" pegado
    'GUEV-INF-0021': 'No debe iniciar terapia por ahora',
    'R01423': 'Delirium',                      # el corte automático elige "…ISRS clásico."
    'GUEV-DER-0138': 'Test pack para Estreptococo grupo A',   # "grupo" | "A Es una…"
}
MAYUSCULA_INICIAL = {'GUEV-OBS-0124'}   # la frase se entiende completa

def corregir_a_mano(data):
    idx = {p['id_unico']: p for p in data['preguntas']}
    for pid, opcion in OPCION_FINAL.items():
        p = idx[pid]; ult = p['opciones'][-1]
        todo = ' '.join((ult['texto'] + ' ' + p['justificacion']).split())
        assert todo.startswith(opcion), f"{pid}: no calza"
        resto = todo[len(opcion):].strip().lstrip('-').strip()
        ult['texto'] = opcion
        p['justificacion'] = resto[:1].upper() + resto[1:]
    for pid in MAYUSCULA_INICIAL:
        j = idx[pid]['justificacion']; idx[pid]['justificacion'] = j[:1].upper() + j[1:]
    return list(OPCION_FINAL) + list(MAYUSCULA_INICIAL)

def main():
    path = ROOT / 'data' / 'banco_inicial.json'
    data = json.load(open(path))
    a_mano = corregir_a_mano(data)
    print(f"corregidas a mano: {len(a_mano)} ({', '.join(a_mano)})")
    cat = {1: [], 2: [], 3: [], 'dudosa': []}
    for p in data['preguntas']:
        if not rb.justif_truncada(p) or len(p.get('opciones') or []) < 3: continue
        ult = p['opciones'][-1]; j = p['justificacion'].strip()
        # 2) corte dentro de la opción
        m = FRAG_OPCION.match(j)
        if m and COLGANDO.search(ult['texto'].strip()):
            cat[2].append((p['id_unico'], f"«…{ult['texto'][-30:]}» + «{m['frag']}»"))
            if APLICAR:
                ult['texto'] = ult['texto'].rstrip() + ' ' + m['frag']
                p['justificacion'] = m['resto'].strip()
            continue
        # 1) inicio pegado a la opción e
        r = partir_corto(p)
        if r:
            izq, der = r
            motivos = rb.dudoso(izq, der, [len(o['texto']) for o in p['opciones'][:-1]])
            if not motivos:
                cat[1].append((p['id_unico'], f"e) «{izq[:45]}»"))
                if APLICAR:
                    ult['texto'] = izq
                    # Rotar antes de anteponer el inicio: si no, el FINAL queda a
                    # continuación de un inicio que puede no terminar en punto.
                    p['justificacion'] = der + ' ' + (rotar(j, p['id_unico'])[0] if colgando(j) else j)
                continue
            cat['dudosa'].append((p['id_unico'], f"«{izq[:50]}» — {'; '.join(motivos)}"))
            continue
        # 3) inicio perdido (salvo que esté rotada: entonces es el FINAL y se
        #    resuelve abajo)
        if colgando(j): continue
        cat[3].append((p['id_unico'], f"«{j[:55]}…»"))
        if APLICAR:
            p['justificacion'] = '[…] ' + j

    rot = {'rotada': [], 'final_perdido': [], 'completada': [], 'sin_cambio': []}
    for p in data['preguntas']:
        j = p.get('justificacion') or ''
        if not colgando(j): continue
        nueva, tipo = rotar(j, p['id_unico'])
        rot[tipo].append((p['id_unico'], nueva))
        if APLICAR: p['justificacion'] = nueva

    nombres = {1: 'inicio pegado a la opción e (cortado)', 2: 'corte dentro de la opción (fragmento devuelto)',
               3: 'inicio perdido en la fuente (marcado […])', 'dudosa': 'dudosas (no se tocan)'}
    for k in (1, 2, 3, 'dudosa'):
        print(f"{nombres[k]}: {len(cat[k])}")
        for pid, desc in (cat[k] if k != 1 else cat[k][:4]):
            print(f"    {pid:<15} {desc}")
    print(f"rotación INICIO|FINAL|MEDIO corregida: {len(rot['rotada'])}")
    print(f"final perdido en la fuente (marcado […]): {len(rot['final_perdido'])}")
    print(f"final completado (cálculo o punto final): {len(rot['completada'])}")
    print(f"sin cambio (URL o tabla al final): {len(rot['sin_cambio'])}")
    if '-v' in sys.argv:
        for tipo in rot:
            for pid, t in rot[tipo]: print(f"    {tipo[:5]} {pid:<15} …{t[-110:]!r}")
    if APLICAR:
        json.dump(data, open(path, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
        print('✓ aplicado')
    else:
        print('(simulación — usar --aplicar)')

if __name__ == '__main__':
    main()
