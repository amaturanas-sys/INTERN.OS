#!/usr/bin/env python3
"""Optimización v1.3.2 del banco JSON:
- Elimina campos huérfanos no usados por la app (_origenes, _bleed_*).
- Elimina valores por defecto vacíos (estadisticas_usuario: {}, historial_ediciones: [],
  imagen: null, etc.) — el seed/editor los re-crea cuando hace falta.
- Minifica (sin indent) — los JSON quedan reproducibles vía este script.
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
BANCO = ROOT / "data" / "banco_inicial.json"
META  = ROOT / "data" / "banco_meta.json"

DROP_INTERNAL = (
    "_origenes", "_bleed_reparado", "_bleed_confianza",
    "_clasificacion_auto",  # residuo del clasificador, no usado en runtime
)

def es_vacio(v):
    return v is None or v == "" or v == [] or v == {}

def main():
    b = json.load(open(BANCO))
    antes = BANCO.stat().st_size
    for q in b["preguntas"]:
        for f in DROP_INTERNAL:
            q.pop(f, None)
        # Defaults vacíos (no afecta lectura, el código usa `||` o `?.`)
        for f in ("historial_ediciones", "estadisticas_usuario", "imagen",
                  "bibliografia_sugerida", "subtema", "contexto",
                  "ges_relacionado"):
            if f in q and es_vacio(q[f]):
                q.pop(f)
        # bibliografia_sugerida: el campo `score` solo se usa offline para
        # ordenar candidatos. En runtime la UI lee titulo/url/archivo. Lo
        # eliminamos para reducir el JSON. ~70 KB ahorrados.
        for ref in (q.get("bibliografia_sugerida") or []):
            ref.pop("score", None)
        # razon_inactivo vacío
        if q.get("razon_inactivo") == []:
            q.pop("razon_inactivo")
    # Preservar la version ya seteada (cruzar_bibliografia.py o bumps manuales);
    # solo asignar default si no existe.
    if not b["meta"].get("version"):
        b["meta"]["version"] = "reconstruccion_v10_optimizado"
    # Minificar
    json.dump(b, open(BANCO, "w"), ensure_ascii=False, separators=(",", ":"))
    despues = BANCO.stat().st_size
    print(f"Antes: {antes/1024:.0f} KB")
    print(f"Después: {despues/1024:.0f} KB")
    print(f"Ahorro: {(antes-despues)/1024:.0f} KB ({100*(antes-despues)/antes:.1f}%)")

    # Sidecar `banco_meta.json` (~200 B) — el seed lo lee primero para evitar
    # descargar el banco completo cuando ya está sembrado con la misma versión.
    # total real (no el campo viejo de meta), y fecha de generación si existe.
    meta = {
        "version": b["meta"]["version"],
        "total": len(b.get("preguntas", [])),
        "actualizado": b["meta"].get("generado") or b["meta"].get("fecha_generacion"),
    }
    json.dump(meta, open(META, "w"), ensure_ascii=False, separators=(",", ":"))
    print(f"Sidecar banco_meta.json: {META.stat().st_size} bytes")

if __name__ == "__main__":
    main()
