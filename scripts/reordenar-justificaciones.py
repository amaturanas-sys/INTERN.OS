"""
Reordena las justificaciones que el parseo original dejó en tres trozos.

Estructura encontrada en el banco original (antes de v1.11.0):

    opción e      = "<texto de la opción> <INICIO de la justificación>"
    justificacion = "<FINAL>\n\n[Opción E] <MEDIO>"

El orden correcto es INICIO + MEDIO + FINAL. Ejemplo, GUEV-CAR-0027:
    MEDIO termina en  "…se debe estudiar con ecocardiografía y"
    FINAL empieza en  "luego debe resolverse quirúrgicamente…"

La etiqueta "[Opción X]" es un resto de un parseo anterior: nunca coincide con
la alternativa correcta (0 de 443), y un estudiante la puede leer como "la
respuesta es la E". Se elimina.

Dos situaciones en el banco actual:
  A) La reparación de v1.11.0 no tocó la pregunta:  "<FINAL>\n\n[Opción E] <MEDIO>"
  B) v1.11.0 antepuso el INICIO (sacado de la opción e) y quedó en mal orden:
     "<INICIO> <FINAL>\n\n[Opción E] <MEDIO>".  Para separar INICIO de FINAL se
     usa la justificación ORIGINAL guardada en git (FINAL es exactamente su
     primer trozo, con la corrección de ligaduras fl→fi aplicada).

Si MEDIO termina en punto y FINAL empieza en minúscula, entre ambos se perdió
texto en la fuente: se marca con "[…]" en vez de inventarlo.

Uso: python3 scripts/reordenar-justificaciones.py <commit-banco-original> [--aplicar]
"""
import json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
commit = sys.argv[1]
APLICAR = '--aplicar' in sys.argv
orig = {p['id_unico']: p for p in json.loads(subprocess.check_output(
    ['git', 'show', f'{commit}:data/banco_inicial.json'], cwd=ROOT))['preguntas']}
data = json.load(open(ROOT / 'data' / 'banco_inicial.json'))

LIG = [(r'\brefiej','reflej'),(r'\bRefiej','Reflej'),(r'\binfiuenza','influenza'),(r'\bInfiuenza','Influenza'),
 (r'\binfiama','inflama'),(r'\bInfiama','Inflama'),(r'\bhiperfiexi','hiperflexi'),(r'\bHiperfiexi','Hiperflexi'),
 (r'\bfiujo','flujo'),(r'\bFiujo','Flujo'),(r'\bfiuido','fluido'),(r'\bFiuido','Fluido'),(r'\bfiexi','flexi'),
 (r'\bFiexi','Flexi'),(r'\bfiexib','flexib'),(r'\brefiuj','refluj'),(r'\bRefiuj','Refluj'),(r'\bconfiict','conflict'),
 (r'\bfiatulen','flatulen'),(r'\bfiujometr','flujometr'),(r'\bfiema\b','flema'),(r'\bfiogosis','flogosis'),
 (r'\bfiebotom','flebotom'),(r'\bdesfiec','desflec'),(r'\bfiuctu','fluctu'),(r'\bFiuctu','Fluctu')]
def lig(s):
    for a, b in LIG: s = re.sub(a, b, s)
    return s

BLOQUE = re.compile(r'^(?P<pre>[\s\S]*?)\s*\n\n\[Opción [A-E]\]\s*(?P<mid>[\s\S]*)$')
FIN_FRASE = re.compile(r'[.!?)"»:]\s*$')

cont = {'A_sin_inicio': 0, 'B_con_inicio': 0, 'con_hueco': 0, 'sin_final': 0}
revisar, muestras = [], []
for p in data['preguntas']:
    j = p.get('justificacion') or ''
    m = BLOQUE.match(j)
    if not m: continue
    pre, mid = m['pre'].strip(), m['mid'].strip()
    o = orig.get(p['id_unico'])
    ofinal = lig(o['justificacion'].split('\n\n[Opción')[0].strip()) if o else None

    if not pre:
        inicio, final = '', ''; cont['sin_final'] += 1
    elif ofinal and pre == ofinal:
        inicio, final = '', ofinal; cont['A_sin_inicio'] += 1
    elif ofinal and pre.endswith(ofinal):
        inicio, final = pre[:-len(ofinal)].strip(), ofinal; cont['B_con_inicio'] += 1
    else:
        revisar.append((p['id_unico'], 'no se pudo ubicar el trozo final original')); continue

    if final and FIN_FRASE.search(mid) and final[:1].islower():
        union = ' […] '; cont['con_hueco'] += 1
    else:
        union = ' '
    nueva = ' '.join(x for x in [inicio, mid] if x)
    if final: nueva = nueva + union + final
    if len(muestras) < 4 and inicio:
        muestras.append((p['id_unico'], j, nueva))
    if APLICAR: p['justificacion'] = nueva

total = sum(v for k, v in cont.items() if k != 'con_hueco')
print(f"Justificaciones con bloque [Opción X] reordenadas: {total}")
print(f"  A) sin inicio antepuesto            : {cont['A_sin_inicio']}")
print(f"  B) con inicio antepuesto en v1.11.0 : {cont['B_con_inicio']}")
print(f"  solo bloque (sin trozo final)       : {cont['sin_final']}")
print(f"  con texto perdido en la fuente, marcado '[…]': {cont['con_hueco']}")
print(f"  sin resolver (revisión manual)      : {len(revisar)} {revisar[:5]}")
for pid, antes, despues in muestras[:2]:
    print('─' * 90); print(pid)
    print('  ANTES  :', antes[:260].replace('\n', ' ⏎ '))
    print('  DESPUÉS:', despues[:260])
if APLICAR:
    json.dump(data, open(ROOT / 'data' / 'banco_inicial.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('\n✓ aplicado')
else:
    print('\n(simulación — usar --aplicar)')
