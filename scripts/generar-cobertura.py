"""
Genera data/referencias/cobertura_banco_2026.json: cuántas preguntas del banco
cubren cada ítem del Perfil EUNACOM 2026, y el resumen por especialidad.

Correr DESPUÉS de scripts/indexar-perfil.py --aplicar, cada vez que cambie el
banco. Uso: python3 scripts/generar-cobertura.py
"""
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
with open(ROOT / 'data' / 'banco_inicial.json') as f:
    banco = json.load(f)['preguntas']
with open(ROOT / 'data' / 'referencias' / 'perfil_eunacom_2026.json') as f:
    perfil = json.load(f)['items']

cuentas = Counter(p['codigo_perfil'] for p in banco if p.get('codigo_perfil'))
PERFIL_BY = {it['codigo']: it for it in perfil}

# Construir reporte por código del Perfil
reporte_items = []
for it in perfil:
    n = cuentas.get(it['codigo'], 0)
    reporte_items.append({
        'codigo': it['codigo'],
        'area': it['area'],
        'especialidad_codigo': it['especialidad_codigo'],
        'especialidad_nombre': it['especialidad_nombre'],
        'seccion': it['seccion'],
        'titulo': it['titulo'],
        'preguntas_banco': n,
    })

# Por especialidad
esp_stats = defaultdict(lambda: {'items_total': 0, 'items_cubiertos': 0,
                                  'preguntas': 0, 'codigos_solo_area': 0})
for it in reporte_items:
    k = (it['area'], it['especialidad_codigo'])
    esp_stats[k]['items_total'] += 1
    if it['preguntas_banco'] > 0:
        esp_stats[k]['items_cubiertos'] += 1
    esp_stats[k]['preguntas'] += it['preguntas_banco']
    esp_stats[k]['especialidad_nombre'] = it['especialidad_nombre']
# Sumar preguntas con codigo_perfil de tipo "X.YY.0.000" (solo área)
for p in banco:
    c = p.get('codigo_perfil', '')
    if isinstance(c, str) and c.endswith('.0.000'):
        a, e = c.split('.')[:2]
        esp_stats[(int(a), e)]['codigos_solo_area'] += 1
        esp_stats[(int(a), e)]['preguntas'] += 1

resumen_esp = []
for (a, e), s in sorted(esp_stats.items()):
    resumen_esp.append({
        'codigo_area_esp': f'{a}.{e}',
        'especialidad_nombre': s.get('especialidad_nombre','?'),
        'items_perfil': s['items_total'],
        'items_cubiertos': s['items_cubiertos'],
        'cobertura_pct': round(100*s['items_cubiertos']/s['items_total'], 1) if s['items_total'] else 0,
        'preguntas_banco': s['preguntas'],
        'preguntas_sin_item_especifico': s['codigos_solo_area'],
    })

ambiguas = sum(1 for p in banco if p.get('codigo_perfil_confianza') == 'ambigua')

reporte = {
    'meta': {
        'fuente_perfil': 'Perfil EUNACOM 2026 (ASOFAMECh)',
        'total_preguntas_banco': len(banco),
        'preguntas_ambiguas_sin_area': ambiguas,
        'items_perfil_total': len(perfil),
        'items_perfil_cubiertos_con_pregunta': sum(1 for it in reporte_items if it['preguntas_banco']>0),
        'version_banco': json.load(open(ROOT / 'data' / 'banco_inicial.json'))['meta'].get('version'),
    },
    'resumen_por_especialidad': resumen_esp,
    'items': reporte_items,
}
out = ROOT / 'data' / 'referencias' / 'cobertura_banco_2026.json'
with open(out, 'w', encoding='utf-8') as f:
    json.dump(reporte, f, ensure_ascii=False, indent=2)
print(f'✓ Reporte guardado: {out}')
print(f'\nResumen por especialidad:')
print(f'{"Esp":8s} {"Nombre":28s} {"Items":>7s} {"Cubier":>7s} {"%":>5s} {"Pregs":>7s}')
for r in resumen_esp:
    print(f'{r["codigo_area_esp"]:8s} {r["especialidad_nombre"][:28]:28s} '
          f'{r["items_perfil"]:7d} {r["items_cubiertos"]:7d} '
          f'{r["cobertura_pct"]:5.1f} {r["preguntas_banco"]:7d}')
