"""
Reconstruye el banco unificado desde scripts/banco_fuente/_banco_recuperado/*.json

Etapas:
  1. Carga los JSON recuperados (2610 preguntas).
  2. Repara ligaduras perdidas (NUL -> fi/fl/ff).
  3. Reconstruye la justificación completa para preguntas con "bleed"
     (texto de opción correcta arrastró el inicio de la explicación)
     y recorta la opción a su forma corta (heurístico + flag de confianza).
  4. Deduplica por enunciado normalizado, prefiriendo:
        - Copia desde archivo de especialidad clara > repasos/novedades.
        - Copia sin bleed > con bleed.
        - Copia más completa.
  5. Asigna especialidad_principal con el catálogo de la app.
     Preserva `origen_set` (simulacro EUNACOM o módulo) para futuro modo de simulacros.
  6. Emite reporte y, si --emit, genera data/banco_inicial.json.

Uso:
    python3 scripts/reconstruir_banco.py            # solo reporte
    python3 scripts/reconstruir_banco.py --emit     # escribe data/banco_inicial.json
"""
import json
import glob
import os
import re
import sys
import unicodedata
import statistics
from collections import Counter, defaultdict
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "scripts/banco_fuente/_banco_recuperado")
OUT = os.path.join(ROOT, "data/banco_inicial.json")
REPORT = os.path.join(ROOT, "scripts/banco_fuente/_banco_recuperado/_reporte_reconstruccion.json")

# ---------- 1. ligaduras ----------
# Por defecto, NUL -> "fi" (caso más frecuente en español médico).
# Excepciones donde es "fl" o "ff" según contexto.
FL_PATTERNS = [
    (re.compile(r"\b\x00utter\b", re.IGNORECASE), "flutter"),
    (re.compile(r"\b\x00ujo\b", re.IGNORECASE), "flujo"),
    (re.compile(r"\b\x00ujos\b", re.IGNORECASE), "flujos"),
    (re.compile(r"\b\x00uido\b", re.IGNORECASE), "fluido"),
    (re.compile(r"\b\x00uidos\b", re.IGNORECASE), "fluidos"),
    (re.compile(r"\b\x00uir\b", re.IGNORECASE), "fluir"),
    (re.compile(r"\b\x00ora\b", re.IGNORECASE), "flora"),
    (re.compile(r"\b\x00ema\b", re.IGNORECASE), "flema"),
    (re.compile(r"\b\x00ebitis\b", re.IGNORECASE), "flebitis"),
    (re.compile(r"\b\x00ebografía\b", re.IGNORECASE), "flebografía"),
    (re.compile(r"\b\x00exi", re.IGNORECASE), "flexi"),   # flexión, flexible
    (re.compile(r"\b\x00exo", re.IGNORECASE), "flexo"),
    (re.compile(r"\b\x00exor", re.IGNORECASE), "flexor"),
    (re.compile(r"\binf\x00am", re.IGNORECASE), "inflam"),
    (re.compile(r"\bre\x00ej", re.IGNORECASE), "reflej"),
    (re.compile(r"\bre\x00uj", re.IGNORECASE), "refluj"),
    (re.compile(r"\bin\x00uenza\b", re.IGNORECASE), "influenza"),
    (re.compile(r"\bcon\x00icto", re.IGNORECASE), "conflicto"),
]
# Algunas "ff" comunes en castellano son raras; lo dejamos en fi por defecto.

def fix_ligatures(s: str) -> str:
    if not s or "\x00" not in s:
        return s
    for rx, rep in FL_PATTERNS:
        s = rx.sub(rep, s)
    # default
    s = s.replace("\x00", "fi")
    return s


# ---------- 2. mapeo de especialidad ----------
# El banco en vivo usa estas claves en `especialidad_principal`. Mapeamos
# los nombres de archivo del banco recuperado.
ESPEC_ALIAS = {
    "cardio": "cardio",
    "dermato": "dermato",
    "endocrino": "endocrino",
    "infecto": "infecto",
    "ginecologia": "gineco",
    "obstetricia": "obstetricia",
    "neuro": "neurologia",
    "oftalmo": "oftalmo",
    "otorrino": "otorrino",
    "pediatria": "pediatria",
    "psiquiatria": "psiquiatria",
    "trauma": "trauma",
    "uro": "uro",
    "cx_y_anestesia": "cirugia",
    "salud_publica": "salud_publica",
}
# Archivos temáticos dentro de repasos/novedades que dan pista de especialidad.
ARCHIVO_HINT = {
    "endocrino_infecto.txt": ("endocrino", "infecto"),
    "dermato_uro.txt": ("dermato", "uro"),
    "neuro_cardio_y_respi.txt": ("neurologia", "cardio"),
    "otorrino_oftalmo.txt": ("otorrino", "oftalmo"),
    "psiquiatria_y_salud_publica.txt": ("psiquiatria", "salud_publica"),
    "traumato_y_cirugia.txt": ("trauma", "cirugia"),
    "hemato_nefro_reuma.txt": ("hemato", "nefro"),
    "diabetes_y_gastroenterologia.txt": ("endocrino", "medicina_interna"),
}

SIMULACROS = {
    "eunacom_2013.txt": "EUNACOM 2013",
    "eunacom_2016.txt": "EUNACOM 2016",
    "eunacom_2018.txt": "EUNACOM 2018",
    "enacom_2017.txt": "EUNACOM 2017",
    "prueba_final_modulo_2.txt": "Repaso Módulo 2",
    "prueba_final_modulo_3_-_1.txt": "Repaso Módulo 3 (1)",
    "prueba_final_modulo_3_-_2.txt": "Repaso Módulo 3 (2)",
    "prueba_final_modulo_3_-_3.txt": "Repaso Módulo 3 (3)",
    "repaso_modulo_1_prueba_70_preg_n2.txt": "Repaso Módulo 1",
}


# ---------- 3. bleed: reconstruir justificación y recortar opción ----------
STARTER_RX = re.compile(
    r"(?<=[a-záéíóúñ\)\.,;:])\s+([A-ZÁÉÍÓÚ][a-záéíóúñ])"
)

def split_bleed(correct_text: str, siblings: list[str]) -> tuple[str, str, float]:
    """Devuelve (opcion_real, parte_bleed, confianza_0_1)."""
    txt = correct_text.strip()
    if not txt:
        return "", "", 1.0
    sib_lens = [len(s) for s in siblings if s and s.strip()]
    base = statistics.median(sib_lens) if sib_lens else 40
    limit = max(int(base * 1.8), 40)

    # 1er intento: cortar en primer "sentence-starter" >= 8 chars y <= limite*2
    m = STARTER_RX.search(txt)
    if m:
        cut = m.start() + 1  # antes del espacio
        if 8 <= cut <= limit * 2.4:
            opt = txt[:cut].rstrip()
            rest = txt[cut:].lstrip()
            # confianza alta si cae cerca de la mediana hermana
            conf = 0.9 if abs(len(opt) - base) <= base * 0.7 else 0.6
            return opt, rest, conf

    # Fallback: cortar por longitud en frontera de palabra
    cut = txt.rfind(" ", 0, limit)
    if cut < 10:
        cut = limit
    return txt[:cut].rstrip(), txt[cut:].lstrip(), 0.4


def rebuild_question(p: dict, source_file: str) -> dict:
    """Aplica ligature-fix, bleed-repair y mapea al esquema interno."""
    # Ligaduras en todos los campos textuales
    enun = fix_ligatures((p.get("enunciado") or "").strip())
    just = fix_ligatures((p.get("justificacion") or "").strip())
    opciones = []
    correct_idx = None
    for i, o in enumerate(p.get("opciones") or []):
        opciones.append({
            "letra": (o.get("letra") or chr(97 + i)).lower(),
            "texto": fix_ligatures((o.get("texto") or "").strip()),
            "correcta": bool(o.get("correcta")),
        })
        if o.get("correcta"):
            correct_idx = i

    bleed_flag = False
    bleed_conf = 1.0
    if correct_idx is not None:
        cor = opciones[correct_idx]
        siblings = [o["texto"] for j, o in enumerate(opciones) if j != correct_idx]
        if len(cor["texto"]) > 80 and len(cor["texto"]) > max(
            (len(s) for s in siblings), default=0
        ) * 2:
            opt_short, bleed_part, bleed_conf = split_bleed(cor["texto"], siblings)
            opciones[correct_idx]["texto"] = opt_short
            # justificación completa = bleed + " " + justif_original
            just = (bleed_part + " " + just).strip()
            bleed_flag = True

    archivo_origen = (p.get("archivo_origen") or "").lower()
    return {
        "_src_file": source_file,
        "_archivo_origen": archivo_origen,
        "_numero": p.get("numero"),
        "enunciado": enun,
        "opciones": opciones,
        "justificacion": just,
        "_bleed_reparado": bleed_flag,
        "_bleed_confianza": round(bleed_conf, 2),
    }


# ---------- 4. normalización para dedup ----------
def norm_enun(s: str) -> str:
    s = (s or "").lower().strip()
    s = "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


META_RICA = (
    "tema_validado",
    "subtema",
    "sistema_behrens",
    "dificultad_estimada",
    "contexto",
    "habilidad_evaluada",
    "frecuencia_eunacom",
    "ges_relacionado",
    "tiene_imagen_referenciada",
    "estado_imagen",
    "imagen",
    "id_unico",
)


def cargar_banco_actual(path: str) -> list:
    """Lee data/banco_inicial.json y reconstruye cada pregunta con el mismo
    pipeline (ligaduras + bleed). Adjunta `_meta_rica` con campos de la app."""
    if not os.path.exists(path):
        return []
    try:
        d = json.load(open(path, encoding="utf-8"))
    except Exception:
        return []
    pregs = d.get("preguntas") or []
    out = []
    for p in pregs:
        # adaptar al formato esperado por rebuild_question
        src_p = {
            "enunciado": p.get("enunciado", ""),
            "justificacion": p.get("justificacion", ""),
            "opciones": [
                {
                    "letra": (o.get("letra") or "").lower(),
                    "texto": o.get("texto", ""),
                    "correcta": bool(o.get("correcta")),
                }
                for o in (p.get("opciones") or [])
            ],
            "numero": None,
            "archivo_origen": p.get("id_unico", ""),
        }
        q = rebuild_question(src_p, "_banco_actual")
        q["_meta_rica"] = {k: p.get(k) for k in META_RICA if k in p}
        q["_meta_rica"]["especialidad_principal"] = p.get(
            "especialidad_principal", ""
        )
        out.append(q)
    return out


def main(emit: bool = False):
    files = sorted(
        f
        for f in glob.glob(os.path.join(SRC, "*.json"))
        if "INDEX" not in f and not os.path.basename(f).startswith("_")
    )

    # 1) Banco recuperado
    raw = []
    nul_count = 0
    for f in files:
        spec_file = os.path.basename(f).replace(".json", "")
        for p in json.load(open(f, encoding="utf-8")):
            blob = (p.get("enunciado") or "") + (p.get("justificacion") or "") + "".join(
                (o.get("texto") or "") for o in (p.get("opciones") or [])
            )
            had_nul = "\x00" in blob
            q = rebuild_question(p, spec_file)
            q["_had_nul"] = had_nul
            raw.append(q)
            if had_nul:
                nul_count += 1

    # 2) Banco actual (en vivo) — también reparar bleeds
    actuales = cargar_banco_actual(OUT)
    bleeds_act = sum(1 for q in actuales if q["_bleed_reparado"])
    raw_total_brutas = len(raw) + len(actuales)

    # 3) Fusionar recuperado + actual, dedup por enunciado normalizado
    groups = defaultdict(list)
    for q in raw + actuales:
        groups[norm_enun(q["enunciado"])].append(q)

    def score(q):
        # Mayor score = preferida
        src = q["_src_file"]
        ao = q["_archivo_origen"]
        s = 0
        if src == "_banco_actual":
            s += 6  # ya en vivo, prioritario
        elif src in ESPEC_ALIAS:
            s += 5
        elif src == "repasos" and ao in ARCHIVO_HINT:
            s += 2
        elif src == "repasos":
            s += 0
        elif src == "novedades":
            s -= 1
        if not q["_bleed_reparado"]:
            s += 1
        s += q["_bleed_confianza"]
        s += min(len(q["justificacion"]) / 500, 2)
        return s

    unique = []
    fused_from_both = 0
    only_recuperado = 0
    only_actual = 0
    for k, group in groups.items():
        if not k:
            continue
        group.sort(key=score, reverse=True)
        best = group[0]
        srcs = {g["_src_file"] for g in group}
        if "_banco_actual" in srcs and len(srcs) > 1:
            fused_from_both += 1
            # Adjuntar metadata rica desde la copia del banco actual
            for g in group:
                if g["_src_file"] == "_banco_actual":
                    best["_meta_rica"] = g.get("_meta_rica", {})
                    break
        elif srcs == {"_banco_actual"}:
            only_actual += 1
        else:
            only_recuperado += 1

        # Orígenes (excluir el banco actual del listado de "fuentes")
        origenes = []
        for g in group:
            if g["_src_file"] == "_banco_actual":
                continue
            ao = g["_archivo_origen"]
            sim = SIMULACROS.get(ao)
            if sim:
                origenes.append({"tipo": "simulacro", "set": sim, "numero": g["_numero"]})
            else:
                origenes.append({
                    "tipo": "fuente",
                    "archivo": ao,
                    "src": g["_src_file"],
                    "numero": g["_numero"],
                })
        best["_origenes"] = origenes
        unique.append(best)

    # Asignar especialidad_principal
    def asignar_espec(q):
        # 1) Si tiene meta rica del banco actual, conservar su especialidad
        mr = q.get("_meta_rica") or {}
        if mr.get("especialidad_principal"):
            return mr["especialidad_principal"]
        src = q["_src_file"]
        ao = q["_archivo_origen"]
        if src in ESPEC_ALIAS:
            return ESPEC_ALIAS[src]
        if src == "repasos" and ao in ARCHIVO_HINT:
            return ARCHIVO_HINT[ao][0]
        return "mixto"

    for q in unique:
        q["especialidad_principal"] = asignar_espec(q)

    # Reporte
    bleed_repaired = sum(1 for q in unique if q["_bleed_reparado"])
    bleed_low_conf = sum(
        1 for q in unique if q["_bleed_reparado"] and q["_bleed_confianza"] < 0.7
    )
    by_spec = Counter(q["especialidad_principal"] for q in unique)
    by_origen_simulacro = Counter()
    for q in unique:
        for o in q["_origenes"]:
            if o["tipo"] == "simulacro":
                by_origen_simulacro[o["set"]] += 1

    report = {
        "generado": datetime.now().isoformat(timespec="seconds"),
        "fuentes": {
            "banco_recuperado_brutas": len(raw),
            "banco_actual_en_vivo": len(actuales),
            "total_brutas": raw_total_brutas,
        },
        "fusion": {
            "preguntas_unicas_final": len(unique),
            "duplicados_eliminados": raw_total_brutas - len(unique),
            "solo_en_banco_actual": only_actual,
            "solo_en_recuperado": only_recuperado,
            "en_ambos_fusionadas": fused_from_both,
        },
        "reparaciones": {
            "ligaduras_NUL_detectadas_en_recuperado": nul_count,
            "bleeds_reparados_recuperado": sum(
                1 for q in raw if q["_bleed_reparado"]
            ),
            "bleeds_reparados_actual": bleeds_act,
            "bleeds_reparados_total_post_dedup": bleed_repaired,
            "bleeds_baja_confianza_para_revision": bleed_low_conf,
        },
        "distribucion_por_especialidad": dict(by_spec.most_common()),
        "simulacros_preservados": dict(by_origen_simulacro.most_common()),
    }

    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(json.dumps(report, ensure_ascii=False, indent=2))

    if emit:
        # Generar banco_inicial.json con el esquema de la app
        meta_actual = {}
        if os.path.exists(OUT):
            try:
                meta_actual = json.load(open(OUT)).get("meta", {})
            except Exception:
                pass
        out = {
            "meta": {
                **meta_actual,
                "version": "reconstruccion_v1",
                "generado": report["generado"],
                "preguntas_total": len(unique),
            },
            "preguntas": [],
        }
        for i, q in enumerate(unique, 1):
            mr = q.get("_meta_rica") or {}
            # Si la pregunta venía del banco actual, conservar su id_unico
            id_unico = mr.get("id_unico") or f"R{i:05d}"
            out["preguntas"].append({
                "id_unico": id_unico,
                "enunciado": q["enunciado"],
                "opciones": q["opciones"],
                "justificacion": q["justificacion"],
                "especialidad_principal": q["especialidad_principal"],
                "tema_validado": mr.get("tema_validado", ""),
                "subtema": mr.get("subtema", ""),
                "sistema_behrens": mr.get("sistema_behrens", ""),
                "dificultad_estimada": mr.get("dificultad_estimada", ""),
                "contexto": mr.get("contexto", ""),
                "habilidad_evaluada": mr.get("habilidad_evaluada", ""),
                "frecuencia_eunacom": mr.get("frecuencia_eunacom", ""),
                "ges_relacionado": mr.get("ges_relacionado", False),
                "tiene_imagen_referenciada": mr.get(
                    "tiene_imagen_referenciada", False
                ),
                "estado_imagen": mr.get("estado_imagen", ""),
                "utilizable": True,
                "imagen": mr.get(
                    "imagen",
                    {
                        "presente": False,
                        "requerida": False,
                        "data": None,
                        "descripcion": "",
                    },
                ),
                "version_actual": 2,
                "historial_ediciones": [],
                "estadisticas_usuario": {},
                "_origenes": q["_origenes"],
                "_bleed_reparado": q["_bleed_reparado"],
                "_bleed_confianza": q["_bleed_confianza"],
            })
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print(f"\nEscrito {OUT} con {len(unique)} preguntas")


if __name__ == "__main__":
    main(emit="--emit" in sys.argv)
