"""
Repara el bug del parser: la justificación quedó pegada al final de la última
opción, y el campo `justificacion` arranca truncado a media frase.

MODO SIMULACIÓN por defecto. Con --aplicar escribe el banco.

Estrategia del corte: el texto real de la opción debería medir parecido a las
otras opciones de la misma pregunta. Se evalúan los cortes candidatos (espacio
seguido de mayúscula) y se elige el que deja la opción más cerca de la mediana
de las demás. Así no se corta en siglas internas ("Vitamina D", "GnRH", "TAC").
"""
import json, re, sys, statistics, random
from pathlib import Path

ROOT = Path('/home/user/INTERN.OS')
APLICAR = '--aplicar' in sys.argv

INICIO_JUSTIF = re.compile(r' (?=[A-ZÁÉÍÓÚÑ¿\[])')

# Palabras con las que suele arrancar una justificación. Un corte justo antes
# de una de estas es mucho más probable que uno antes de una sigla interna
# de la opción ("... o ARA2", "análogo GnRH", "pedir TAC").
ARRANQUE_FRASE = {
    'el','la','los','las','un','una','es','son','esta','este','estas','estos',
    'se','en','por','para','con','sin','tiene','tienen','hay','no','si','lo',
    'como','cuando','donde','actualmente','ante','todo','toda','todos','todas',
    'dado','debido','frente','ambos','ambas','cabe','corresponde','recordar',
    'primero','segundo','tanto','aunque','pero','sin embargo','a','al','del','de',
}
# Una "palabra" toda en mayúsculas de 2+ caracteres es casi siempre una sigla
# clínica dentro del texto de la opción, no el inicio de la justificación.
SIGLA = re.compile(r'^[A-ZÁÉÍÓÚÑ0-9]{2,}$')

def afectada(p):
    ops = p.get('opciones') or []
    if len(ops) < 3: return False
    L = [len(o.get('texto','')) for o in ops]
    j = (p.get('justificacion') or '').strip()
    return L[-1] > max(L[:-1]) * 2.2 and L[-1] > 90 and j[:1].islower()

def reparar(p):
    """Devuelve (texto_opcion, fragmento_justificacion) o None si no se puede."""
    ops = p['opciones']
    texto = ops[-1]['texto']
    otras = [len(o['texto']) for o in ops[:-1]]
    objetivo = statistics.median(otras)

    mejor, mejor_score = None, None
    for m in INICIO_JUSTIF.finditer(texto):
        corte = m.start()
        izq, der = texto[:corte].strip(), texto[corte:].strip()
        if len(der) < 40:            # el resto debe ser una justificación real
            continue
        if len(izq) < 3:             # la opción no puede quedar vacía
            continue
        score = abs(len(izq) - objetivo)
        # Penaliza cortes que dejan la opción mucho más larga que las otras
        if len(izq) > max(otras) * 1.6:
            score += 100
        primera = der.split()[0].strip('.,;:()[]') if der.split() else ''
        # Premia fuerte los cortes justo antes de un arranque de frase típico
        if primera.lower() in ARRANQUE_FRASE:
            score -= 60
        # Castiga fuerte cortar antes de una sigla: casi siempre va dentro de
        # la opción ("Digitálicos, furosemia y aspirina Los IECA o ARA2, ...")
        if SIGLA.match(primera):
            score += 150
        if mejor_score is None or score < mejor_score:
            mejor, mejor_score = (izq, der), score
    return mejor

COLGANDO = re.compile(r'\b(el|la|los|las|un|una|de|del|en|con|por|para|y|o|a|al|sin|que)$', re.I)

def corte_dudoso(izq, der, otras):
    """Criterios para NO tocar automáticamente una pregunta."""
    motivos = []
    if not der[:1].isupper() and der[:1] not in '¿[':
        motivos.append('la justificación no empieza en mayúscula')
    if COLGANDO.search(izq.strip()):
        motivos.append('la opción queda terminada en artículo o conjunción')
    # Si la opción sigue midiendo mucho más que la más larga de las otras,
    # probablemente quedó texto de la justificación adentro.
    if len(izq) > max(otras) * 1.8 and len(izq) > 60:
        motivos.append('la opción sigue desproporcionada')
    return motivos

def main():
    path = ROOT / 'data' / 'banco_inicial.json'
    data = json.load(open(path))
    banco = data['preguntas']

    af = [p for p in banco if afectada(p)]
    reparadas, sin_corte, dudosas = 0, [], []
    muestras = []
    for p in af:
        r = reparar(p)
        if not r:
            sin_corte.append(p['id_unico']); continue
        opcion, frag = r
        motivos = corte_dudoso(opcion, frag, [len(o['texto']) for o in p['opciones'][:-1]])
        if motivos:
            dudosas.append((p['id_unico'], opcion[:70], motivos))
            continue
        antes = {'opcion': p['opciones'][-1]['texto'], 'justif': p['justificacion']}
        if APLICAR:
            p['opciones'][-1]['texto'] = opcion
            p['justificacion'] = (frag + ' ' + p['justificacion'].strip()).strip()
        if len(muestras) < 6:
            muestras.append((p['id_unico'], antes, opcion, frag, p['justificacion'] if APLICAR else frag + ' ' + p['justificacion'].strip()))
        reparadas += 1

    print(f"Afectadas detectadas    : {len(af)}")
    print(f"Reparadas automáticamente: {reparadas}")
    print(f"Sin corte confiable      : {len(sin_corte)}  {sin_corte[:5]}")
    print(f"Dudosas (NO se tocan)    : {len(dudosas)}")
    if dudosas:
        print("\n  Requieren revisión manual en el editor de la app:")
        for pid, izq, motivos in dudosas:
            print(f"    {pid:<16} {'; '.join(motivos)}")
            print(f"    {'':<16} quedaría: \"{izq}\"")
    print()
    print("═" * 78)
    print("MUESTRA (revisar antes de aplicar)")
    print("═" * 78)
    for pid, antes, opcion, frag, justif_final in muestras:
        print(f"\n── {pid}")
        print(f"  ANTES  opción e) : {antes['opcion'][:150]}")
        print(f"  ANTES  justif    : {antes['justif'][:100]}")
        print(f"  ─────")
        print(f"  DESPUÉS opción e): {opcion}")
        print(f"  DESPUÉS justif   : {justif_final[:150]}")

    if APLICAR:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
        print(f"\n✓ APLICADO. {reparadas} preguntas reparadas en {path}")
    else:
        print(f"\n(simulación — nada se escribió. Usar --aplicar para confirmar)")

main()
