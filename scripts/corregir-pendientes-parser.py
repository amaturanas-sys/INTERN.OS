"""
Corrección manual, pregunta por pregunta, de los casos que el script
automático (reparar-banco.py) dejó intactos por no tener un corte confiable.

Cada entrada de CORTES es el texto con el que DEBE quedar la última opción; lo
que sobra de ese texto es el inicio de la justificación y se antepone a ella.
El script verifica que la opción actual empiece exactamente así antes de tocar.

Uso: python3 scripts/corregir-pendientes-parser.py [--aplicar]
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APLICAR = '--aplicar' in sys.argv

CORTES = {
    'GUEV-INF-0017': 'Amoxicilina + ácido clavulánico',
    'GUEV-HEM-0004': 'Sospechar un trauma renal grave y solicitar TAC de abdomen y pelvis con contraste endovenoso',
    'GUEV-CAR-0095': 'Disección aórtica tipo A',
    'GUEV-MED-0003': 'Central Nacional de Abastecimiento',
    'GUEV-PED-0007': 'Conjuntivitis neonatal por Chlamydia',
    'R00832':        'Indicar paracetamol oral y controlar ambulatoriamente',
    'GUEV-MED-0010': 'No es posible determinar el diagnóstico nutricional con esa información',
    'GUEV-DER-0129': 'Asociación de anemia ferropénica y anemia por déficit de vitamina B12',
    'GUEV-OFT-0051': 'Conjuntivistis neonatal por Chlamydia trachomatis',
    'GUEV-PSQ-0034': 'Complejas, con componentes visuales y auditivos personificados y no personificados',
    'R01808':        'Estreptococo A',
    'GUEV-URO-0055': 'Solicitar alfafetoproteína y HCG y decidir conducta según resultados',
}
# Erratas puntuales en el texto que queda (opción o inicio de justificación).
ERRATAS = {
    'GUEV-OFT-0051': [('Conjuntivistis', 'Conjuntivitis')],
    'GUEV-INF-0017': [('SI bien solo', 'Si bien solo')],
    'R00984':        [('anti- transglutaminasa', 'anti-transglutaminasa')],
}

def main():
    path = ROOT / 'data' / 'banco_inicial.json'
    data = json.load(open(path))
    idx = {p['id_unico']: p for p in data['preguntas']}
    log = []

    # 1) Cortes de la última opción
    for pid, opcion in CORTES.items():
        p = idx[pid]; ult = p['opciones'][-1]
        assert ult['texto'].startswith(opcion), f"{pid}: la opción no empieza como se esperaba"
        inicio = ult['texto'][len(opcion):].strip()
        ult['texto'] = opcion
        p['justificacion'] = (inicio + ' ' + (p.get('justificacion') or '').strip()).strip()
        log.append(f"{pid:<15} opción e → «{opcion[:60]}»")

    # 2) R01012: la opción d se tragó la opción e completa y el inicio de la
    #    justificación ("… (DMRE) e) Retinoblastoma La pérdida lenta …").
    p = idx['R01012']
    d = p['opciones'][3]
    m = re.match(r'^(?P<d>.+?\(DMRE\))\s*e\)\s*(?P<e>Retinoblastoma)\s*(?P<resto>[\s\S]*)$', d['texto'])
    assert m and len(p['opciones']) == 4, "R01012: estructura inesperada"
    d['texto'] = m['d']
    p['opciones'].append({'letra': 'e', 'texto': m['e'], 'correcta': False})
    p['justificacion'] = (m['resto'].strip() + ' ' + p['justificacion'].strip()).strip()
    log.append("R01012          opción d separada: d) DMRE · e) Retinoblastoma (vuelve a tener 5 alternativas)")

    # 3) GUEV-OFT-0011: copia degradada de R01012 (perdió los valores de agudeza
    #    visual del enunciado). Se elimina; meta.reemplazos la mapea a R01012.
    data['preguntas'] = [q for q in data['preguntas'] if q['id_unico'] != 'GUEV-OFT-0011']
    assert data['meta'].get('reemplazos', {}).get('GUEV-OFT-0011') == 'R01012'
    log.append("GUEV-OFT-0011   eliminada: duplicado degradado de R01012 (mapeada en meta.reemplazos)")

    # 4) R00984: su opción e estaba bien (solo larga). Nunca tuvo alternativa
    #    marcada como correcta y por eso estaba desactivada, pero la propia
    #    justificación —ahora reordenada— explica la E: ante celíaco que no
    #    responde, lo primero es revisar adherencia y pedir anti-TGT.
    p = idx['R00984']
    assert not any(o.get('correcta') for o in p['opciones'])
    p['opciones'][4]['correcta'] = True
    if p.get('utilizable') is False:
        p['utilizable'] = True
    log.append("R00984          alternativa E marcada correcta según su justificación; reactivada")

    # 5) Etiqueta "[Opción X]" al comienzo (quedó en correcciones manuales de v1.9.1)
    for q in data['preguntas']:
        j = q.get('justificacion') or ''
        if j.startswith('[Opción '):
            q['justificacion'] = re.sub(r'^\[Opción [A-E]\]\s*', '', j)
            log.append(f"{q['id_unico']:<15} etiqueta '[Opción X]' inicial eliminada")

    # 6) Erratas
    for pid, pares in ERRATAS.items():
        p = idx[pid]
        for a, b in pares:
            for campo in ('justificacion',):
                if a in (p.get(campo) or ''): p[campo] = p[campo].replace(a, b)
            for o in p['opciones']:
                if a in o['texto']: o['texto'] = o['texto'].replace(a, b)

    data['meta']['total'] = len(data['preguntas'])
    print('\n'.join(log))
    print(f"\npreguntas: {len(data['preguntas'])}")
    if APLICAR:
        json.dump(data, open(path, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
        print('✓ aplicado')
    else:
        print('(simulación — usar --aplicar)')

if __name__ == '__main__':
    main()
