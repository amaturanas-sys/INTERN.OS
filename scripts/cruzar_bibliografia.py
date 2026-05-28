"""
Adjunta bibliografía sugerida a cada pregunta del banco.

Estrategia ligera y determinista:
  1. Para cada transcripción (317 archivos .txt), extrae:
     - título, URL, especialidad (del directorio)
     - tokens clave del título + primeros 500 chars del contenido
  2. Para cada pregunta del banco:
     - Restringe candidatos a transcripciones de la misma especialidad
       (mapeo flexible: 'cardio'<->'cardiologia', 'gineco'<->'ginecologia', etc.)
     - Calcula score = nº de tokens compartidos entre la pregunta
       (enunciado + opción correcta) y los tokens del título/contenido
     - Adjunta hasta 3 referencias top con score >= 2
"""
import json
import os
import re
import glob
import unicodedata
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIBL = os.path.join(ROOT, "scripts/banco_fuente/_bibliografia")
INDEX = os.path.join(BIBL, "indice.json")
BANCO = os.path.join(ROOT, "data/banco_inicial.json")


# Mapeo entre especialidades del banco (app) y nombres de carpetas
# de bibliografía. Una especialidad del banco puede mapear a varias
# carpetas (ej. medicina_interna no tiene carpeta dedicada).
SPEC_TO_BIBL = {
    "cardio": ["cardiologia"],
    "dermato": ["dermatologia"],
    "endocrino": ["endocrinologia"],
    "infecto": [],  # no hay carpeta de infectología aún (en otorrino y ped hay temas)
    "neurologia": ["neurologia"],
    "psiquiatria": ["psiquiatria"],
    "gineco": ["ginecologia"],
    "obstetricia": ["obstetricia"],
    "pediatria": ["pediatria"],
    "cirugia": [],  # bibliografía de cirugía aún no integrada
    "uro": [],
    "trauma": ["traumatologia"],
    "otorrino": ["otorrinolaringologia"],
    "oftalmo": ["oftalmologia"],
    "hemato": ["hematologia"],
    "medicina_interna": ["gastroenterologia"],
    "nefro": ["nefrologia"],
    "salud_publica": ["salud_publica"],
    "geriatria": ["geriatria"],
    "urgencias": [],
    "mixto": [],  # se busca en todas
    "ambigua": [],
}


STOPWORDS = set(
    """
    a al algun alguna algunas algunos ante antes aqui aquello aquellos asi
    aun aunque cada como con cuando cuanto da de del desde donde dos durante
    el ella ellas ellos en entre era eran eras eres es esa esas ese esos esta
    estaba estaban estado estamos estan estar este esto estos estoy ex
    excepto fue fueron ha habia habian han has hasta hay hizo hubo igual
    incluyendo la las le les lo los mas menos mi mientras mis mucha muchas
    mucho muchos muy nada ni no nos nosotros nuestra nuestras nuestro nuestros
    o otra otras otro otros para pero poca poco pocos por porque pues que
    quien quienes se segun ser si sin sino sobre solo son su sus tal tambien
    tan tanto te tenia tenian tener tenga tengo ti tiene tienen toda todas
    todo todos tras tu tu un una unas uno unos vez ya yo
    """.split()
)


def norm_tokens(text: str) -> Counter:
    s = text.lower()
    s = "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    toks = [t for t in s.split() if len(t) >= 4 and t not in STOPWORDS]
    return Counter(toks)


def cargar_bibliografia():
    """Devuelve {especialidad_carpeta: [{titulo,url,tokens}, ...]}"""
    bibl = {}
    for unidad_dir in sorted(d for d in os.listdir(BIBL) if os.path.isdir(os.path.join(BIBL, d))):
        items = []
        for txt in sorted(glob.glob(os.path.join(BIBL, unidad_dir, "*.txt"))):
            with open(txt, encoding="utf-8") as f:
                content = f.read()
            # Extraer título y URL
            titulo = ""
            url = ""
            for line in content.split("\n")[:5]:
                if line.lower().startswith("título:") or line.lower().startswith("titulo:"):
                    titulo = line.split(":", 1)[1].strip()
                elif line.lower().startswith("url:"):
                    url = line.split(":", 1)[1].strip()
            # Tokens del título y primeros 4000 chars (cubre intro temática)
            blob = titulo + " " + content[:4000]
            items.append({
                "archivo": os.path.basename(txt),
                "titulo": titulo,
                "url": url,
                "tokens": norm_tokens(blob),
            })
        bibl[unidad_dir] = items
    return bibl


def main():
    bibl = cargar_bibliografia()
    print(f"Cargada bibliografía: {sum(len(v) for v in bibl.values())} transcripciones en {len(bibl)} unidades")

    d = json.load(open(BANCO, encoding="utf-8"))
    pregs = d["preguntas"]

    sin_ref = 0
    con_ref = 0
    refs_total = 0
    sin_ref_por_spec = Counter()

    for p in pregs:
        spec = p["especialidad_principal"]
        carpetas = SPEC_TO_BIBL.get(spec, [])
        # Si no hay carpetas para la especialidad, buscar en todas
        if not carpetas and spec in ("mixto", "ambigua", "urgencias", "infecto", "cirugia", "uro"):
            carpetas = list(bibl.keys())

        candidatos = []
        for c in carpetas:
            candidatos.extend(bibl.get(c, []))

        if not candidatos:
            sin_ref += 1
            sin_ref_por_spec[spec] += 1
            continue

        # Tokens de la pregunta: enunciado + opción correcta + justificación
        cor = next((o["texto"] for o in p["opciones"] if o.get("correcta")), "")
        q_text = (
            p["enunciado"] + " " + cor + " " + (p.get("justificacion") or "")
        )
        q_toks = norm_tokens(q_text)

        # Score: suma de min(count_q, count_t) por token compartido
        scored = []
        for t in candidatos:
            score = sum(min(q_toks[k], t["tokens"][k]) for k in q_toks if k in t["tokens"])
            if score >= 2:
                scored.append((score, t))
        scored.sort(key=lambda x: -x[0])

        if scored:
            top = scored[:3]
            p["bibliografia_sugerida"] = [
                {
                    "titulo": t["titulo"],
                    "url": t["url"],
                    "archivo": t["archivo"],
                    "score": s,
                }
                for s, t in top
            ]
            con_ref += 1
            refs_total += len(top)
        else:
            sin_ref += 1
            sin_ref_por_spec[spec] += 1

    # Bump version
    prev = d["meta"].get("version", "reconstruccion_v4")
    match = re.search(r"v(\d+)$", prev)
    next_v = int(match.group(1)) + 1 if match else 5
    d["meta"]["version"] = f"reconstruccion_v{next_v}"
    d["meta"]["bibliografia_cruzada"] = {
        "preguntas_con_referencia": con_ref,
        "preguntas_sin_referencia": sin_ref,
        "promedio_refs_por_pregunta": round(refs_total / max(con_ref, 1), 2),
        "sin_referencia_por_especialidad": dict(sin_ref_por_spec.most_common()),
    }

    with open(BANCO, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

    print(f"Con referencia: {con_ref} | Sin referencia: {sin_ref}")
    print(f"Promedio refs/pregunta: {refs_total / max(con_ref, 1):.2f}")
    print("Sin referencia por especialidad:", dict(sin_ref_por_spec.most_common()))


if __name__ == "__main__":
    main()
