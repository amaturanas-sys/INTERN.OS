"""
Tres preguntas en que el parseo original dejó solo una o dos alternativas: el
resto ("b. … c. … d. … e. …") quedó al comienzo de la
justificación. Se reconstruyen las cinco a partir de ese texto; nada se
inventa salvo la marca de la correcta en R01681, que su justificación indica
explícitamente ("La eritromicina … es el tratamiento de elección de la sífilis
en alérgicos … en el embarazo").

Además: GUEV-CIR-0029 es copia de R00119 que perdió la palabra "INCORRECTA"
del enunciado (estaba en negrita en el PDF). Sin ella la pregunta se responde
al revés, así que se elimina y se mapea en meta.reemplazos.

Uso: python3 scripts/reparar-opciones-en-justificacion.py [--aplicar]
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APLICAR = '--aplicar' in sys.argv

# id → (texto con que empieza la justificación real, letra correcta)
CASOS = {
    'GUEV-PED-0017': ('Si bien, hay algunas diferencias', 'a'),
    'R00936':        ('Tiene una corioamnionitis clínica clásica', 'a'),
    'R01681':        ('Todo VDRL positivo en el embarazo', 'd'),
}
SEP = re.compile(r'\s+([b-e])\.\s+')

def main():
    path = ROOT / 'data' / 'banco_inicial.json'
    data = json.load(open(path))
    idx = {p['id_unico']: p for p in data['preguntas']}

    for pid, (inicio_j, correcta) in CASOS.items():
        p = idx[pid]
        if len(p['opciones']) == 5:
            print(f"{pid}: ya reparada"); continue
        # Las alternativas ya separadas se mantienen; la última sigue en el texto.
        fijas, ult = p['opciones'][:-1], p['opciones'][-1]
        todo = ult['texto'].rstrip() + ' ' + p['justificacion'].strip()
        corte = todo.index(inicio_j)
        alternativas, justificacion = todo[:corte].strip(), todo[corte:].strip()
        trozos = SEP.split(alternativas)          # [texto_ult, 'c', texto_c, …]
        letras = [o['letra'] for o in fijas] + [ult['letra']] + trozos[1::2]
        assert letras == list('abcde'), f"{pid}: {letras}"
        textos = [o['texto'] for o in fijas] + [trozos[0]] + trozos[2::2]
        p['opciones'] = [{'letra': l, 'texto': t.strip().rstrip('.'), 'correcta': l == correcta}
                         for l, t in zip(letras, textos)]
        p['justificacion'] = justificacion
        p['utilizable'] = True
        print(f"{pid}: 5 alternativas reconstruidas, correcta {correcta.upper()}")
        for o in p['opciones']: print(f"    {o['letra']}{'*' if o['correcta'] else ' '} {o['texto'][:90]}")

    if 'GUEV-CIR-0029' in idx:
        assert 'INCORRECTA' in idx['R00119']['enunciado']
        data['preguntas'] = [q for q in data['preguntas'] if q['id_unico'] != 'GUEV-CIR-0029']
        data['meta']['reemplazos']['GUEV-CIR-0029'] = 'R00119'
        data['meta']['reemplazos'] = dict(sorted(data['meta']['reemplazos'].items()))
        data['meta']['total'] = data['meta']['preguntas_total'] = len(data['preguntas'])
        print("GUEV-CIR-0029: eliminada (copia de R00119 sin «INCORRECTA»)")

    if APLICAR:
        json.dump(data, open(path, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
        print('✓ aplicado')
    else:
        print('(simulación — usar --aplicar)')

if __name__ == '__main__':
    main()
