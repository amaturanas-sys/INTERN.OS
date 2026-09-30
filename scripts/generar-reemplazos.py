"""
Genera meta.reemplazos en data/banco_inicial.json: {id_eliminado: id_superviviente}.

Lo necesita seed.js para las instalaciones que YA tienen el banco anterior en
IndexedDB. La siembra solo agrega y actualiza; sin este mapa, las 1.540 copias
duplicadas eliminadas en v1.11.0 seguirían en el dispositivo del usuario, con
el bug del parser incluido. Con el mapa, seed.js traspasa marcas, estadísticas,
ediciones y tarjetas de repaso a la copia superviviente y borra la vieja.

Solo se borran los ids de este mapa: nunca "todo lo que no esté en el banco",
porque el importador .md acepta ids arbitrarios y eso borraría preguntas
importadas por el usuario.

Uso: python3 scripts/generar-reemplazos.py <commit-del-banco-anterior> [--aplicar]
"""
import json, re, subprocess, sys, unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
commit = sys.argv[1]
viejo = json.loads(subprocess.check_output(['git', 'show', f'{commit}:data/banco_inicial.json'], cwd=ROOT))['preguntas']
data = json.load(open(ROOT / 'data' / 'banco_inicial.json'))
actuales = {p['id_unico'] for p in data['preguntas']}

LIG = [('refiej','reflej'),('infiuenza','influenza'),('infiama','inflama'),('hiperfiexi','hiperflexi'),
       ('fiujo','flujo'),('fiuido','fluido'),('fiexi','flexi'),('refiuj','refluj'),('confiict','conflict'),
       ('fiatulen','flatulen'),('fiujometr','flujometr'),('fiema','flema'),('fiuctu','fluctu')]
def norm(s):
    s = unicodedata.normalize('NFD', str(s or '')).lower()
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    for a, b in LIG: s = s.replace(a, b)
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9 ]', ' ', s)).strip()

grupos = defaultdict(list)
for p in viejo: grupos[norm(p['enunciado'])].append(p['id_unico'])

reemplazos, huerfanos = {}, []
for ids in grupos.values():
    sup = [i for i in ids if i in actuales]
    if len(sup) != 1:
        huerfanos += [i for i in ids if i not in actuales]
        continue
    for i in ids:
        if i != sup[0]: reemplazos[i] = sup[0]

# Duplicados "degradados" que el dedup exacto no podía ver (texto distinto):
MANUALES = {'GUEV-OFT-0011': 'R01012'}   # mismo caso de catarata, sin los valores de agudeza visual
reemplazos.update(MANUALES)

eliminados = {p['id_unico'] for p in viejo} - actuales
print(f'banco anterior: {len(viejo)} | actual: {len(actuales)} | eliminados en el dedup: {len(eliminados)}')
print(f'reemplazos: {len(reemplazos)}  (incluye {len(MANUALES)} manual)')
print(f'eliminados sin superviviente: {len(eliminados - set(reemplazos))} {sorted(eliminados - set(reemplazos))[:5]}')
if '--aplicar' in sys.argv:
    data['meta']['reemplazos'] = dict(sorted(reemplazos.items()))
    json.dump(data, open(ROOT / 'data' / 'banco_inicial.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('✓ meta.reemplazos escrito')
