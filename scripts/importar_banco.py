#!/usr/bin/env python3
"""Normaliza el banco real (arrays *_clean.json) al schema de la app y genera
data/banco_inicial.json.

- Lee scripts/banco_fuente/*.json que sean ARRAYS de preguntas.
- Ignora scripts/banco_fuente/_meta/ (índices, videos, etc.).
- Deduplica por id_unico (gana la primera aparición, orden alfabético de archivo).
- Importa el texto TAL CUAL (no corrige la extracción).

Reejecutable: agrega nuevos *_clean.json a scripts/banco_fuente/ y vuelve a correr.
"""
import json, glob, os, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT, "scripts", "banco_fuente")
OUT = os.path.join(ROOT, "data", "banco_inicial.json")
HOY = datetime.date.today().isoformat()


def normalizar(q, n):
    ops = [
        {"letra": o.get("letra", ""), "texto": o.get("texto", ""), "correcta": bool(o.get("correcta"))}
        for o in q.get("opciones", [])
    ]
    return {
        "id_unico": q.get("id_unico") or f"IMP-{n}",
        "enunciado": q.get("enunciado", ""),
        "opciones": ops,
        "justificacion": q.get("justificacion", "") or "",
        "especialidad_principal": q.get("especialidad_principal", "general"),
        "tema_validado": q.get("tema", "") or "",
        "subtema": q.get("subtema", "") or "",
        "sistema_behrens": q.get("sistema_behrens", "") or "",
        "dificultad_estimada": q.get("dificultad_estimada", "intermedia") or "intermedia",
        "contexto": q.get("contexto", "") or "",
        "habilidad_evaluada": q.get("habilidad_evaluada", "") or "",
        "frecuencia_eunacom": q.get("frecuencia_eunacom", "") or "",
        "ges_relacionado": q.get("ges_relacionado", "") or "",
        # La marca de imagen del origen es poco fiable; no bloqueamos la pregunta.
        "tiene_imagen_referenciada": bool(q.get("tiene_imagen_referenciada")),
        "estado_imagen": "no_aplica",
        "utilizable": True,
        "imagen": {"presente": False, "requerida": False, "data": None, "descripcion": None},
        "version_actual": 1,
        "historial_ediciones": [{
            "version": 1, "fecha": HOY,
            "fuente": q.get("origen") or "Banco Guevara (importado)",
            "nota": "Importación inicial (texto sin editar)", "snapshot": None,
        }],
        "estadisticas_usuario": {"veces_respondida": 0, "veces_correcta": 0, "ultima_vez": None},
        "subespecialidades": q.get("subespecialidades", []) or [],
        "origen": q.get("origen", "") or "",
    }


def main():
    archivos = sorted(glob.glob(os.path.join(SRC_DIR, "*.json")))
    preguntas, vistos = [], set()
    omitidos, por_esp = [], {}
    n = 0
    for f in archivos:
        try:
            data = json.load(open(f, encoding="utf-8"))
        except Exception as e:
            print(f"  ! No se pudo leer {os.path.basename(f)}: {e}")
            continue
        if not isinstance(data, list):
            omitidos.append(os.path.basename(f))
            continue
        for q in data:
            n += 1
            item = normalizar(q, n)
            if not item["opciones"]:
                continue
            if item["id_unico"] in vistos:
                continue
            vistos.add(item["id_unico"])
            por_esp[item["especialidad_principal"]] = por_esp.get(item["especialidad_principal"], 0) + 1
            preguntas.append(item)

    banco = {
        "meta": {
            "descripcion": "Banco real (repasos Dr. Guevara) importado al schema de la app. Texto sin editar.",
            "version_schema": "2026.1",
            "fecha_generacion": HOY,
            "total": len(preguntas),
            "por_especialidad": dict(sorted(por_esp.items())),
        },
        "preguntas": preguntas,
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(banco, fh, ensure_ascii=False, indent=2)

    print(f"Preguntas: {len(preguntas)}")
    print(f"Por especialidad: {banco['meta']['por_especialidad']}")
    if omitidos:
        print(f"Omitidos (no son array de preguntas): {omitidos}")
    print(f"Escrito: {OUT}")


if __name__ == "__main__":
    main()
