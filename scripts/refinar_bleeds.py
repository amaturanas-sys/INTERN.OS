"""
Refina los bleeds de baja confianza marcados en data/banco_inicial.json.

Estrategia: para cada pregunta con _bleed_confianza < 0.7, busca conectores
explicativos claros ("Es un/a", "Tiene un/a", "Se sospecha", "Corresponde a",
"El paciente", ". El", ". La", etc.) DENTRO del texto de la opción correcta.
Si encuentra uno, separa la opción en ese punto y mueve el resto a la
justificación. Si no, deja la opción tal cual (era falso positivo) y limpia
el flag de revisión.
"""
import json
import re
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANCO = os.path.join(ROOT, "data/banco_inicial.json")

# Conectores explicativos en orden de especificidad. El grupo a separar debe
# estar en MAYÚSCULA inicial y aparecer después de al menos 8 chars de opción.
CONECTORES = [
    r"\s(?=Es\s+(?:un|una|el|la|esta|este|esto|ésta|éste|aquí|frecuente|característico|importante)\b)",
    r"\s(?=Tiene\s+(?:un|una|el|la)\b)",
    r"\s(?=Se\s+(?:sospecha|so?pecha|trata|observa|ve\s|confirma|debe|considera|recomienda|presenta|asocia|maneja|caracteriza)\b)",
    r"\s(?=Corresponde\s+a\b)",
    r"\s(?=Recordar\s+que\b)",
    r"\s(?=El\s+(?:paciente|cuadro|tratamiento|diagnóstico|examen|manejo|riesgo|signo|electrocardiograma|EKG|test))",
    r"\s(?=La\s+(?:paciente|clínica|sospecha|conducta|causa|presencia|inmensa|primera|fibrilación|principal|mayoría|enfermedad))",
    r"\s(?=Los\s+(?:síntomas|exámenes|hallazgos|pacientes|criterios))",
    r"\s(?=Las\s+(?:guías|opciones|preguntas))",
    r"\s(?=Sin\s+embargo\b)",
    r"\s(?=Sobre\s+la\b)",
    r"\s(?=Ante\s+(?:la|el)\b)",
    r"\s(?=Dado\s+que\b)",
    r"\s(?=Esta\s+(?:pregunta|paciente|enfermedad|patología)\b)",
    # Después de punto siempre es nueva oración explicativa
    r"(?<=\.)\s(?=[A-ZÁÉÍÓÚ])",
]

CONECTORES_RX = [re.compile(p) for p in CONECTORES]


def refinar_bleed(opcion_texto: str, justif: str):
    """Devuelve (nueva_opcion, nueva_justif, fue_modificada)."""
    txt = opcion_texto.strip()
    # Solo intentar si la opción es razonablemente larga
    if len(txt) < 25:
        return txt, justif, False
    best_cut = None
    for rx in CONECTORES_RX:
        m = rx.search(txt, pos=2)
        if m:
            cut = m.start()
            if best_cut is None or cut < best_cut:
                best_cut = cut
    if best_cut is None:
        return txt, justif, False
    nueva_opcion = txt[:best_cut].rstrip(" ,;.")
    bleed = txt[best_cut:].lstrip()
    nueva_justif = (bleed + " " + (justif or "")).strip()
    return nueva_opcion, nueva_justif, True


def main():
    d = json.load(open(BANCO, encoding="utf-8"))
    pregs = d["preguntas"]
    revisados = 0
    modificados = 0
    falsos_positivos = 0
    for p in pregs:
        # Escaneo amplio: cualquier opción correcta cuyo texto contenga un
        # conector explicativo claro es candidata, sin importar el flag.
        revisados += 1
        cor_idx = next(
            (i for i, o in enumerate(p["opciones"]) if o.get("correcta")), None
        )
        if cor_idx is None:
            continue
        cor = p["opciones"][cor_idx]
        # Solo aplicar refinamiento si la opción aún es sospechosamente larga
        # (>= 30 chars) y contiene algún conector explicativo.
        if len(cor["texto"]) < 30:
            continue
        nueva, justif, fue = refinar_bleed(cor["texto"], p.get("justificacion", ""))
        if fue and nueva != cor["texto"]:
            p["opciones"][cor_idx]["texto"] = nueva
            p["justificacion"] = justif
            p["_bleed_confianza"] = 0.95
            modificados += 1
        elif p.get("_bleed_confianza", 1.0) < 0.7:
            # Era baja confianza y no encontramos conector: falso positivo.
            p["_bleed_reparado"] = False
            p["_bleed_confianza"] = 1.0
            falsos_positivos += 1
    # Bump version cada vez que el script corre y deja cambios
    if modificados or falsos_positivos:
        prev = d["meta"].get("version", "reconstruccion_v1")
        match = re.search(r"v(\d+)$", prev)
        next_v = int(match.group(1)) + 1 if match else 2
        d["meta"]["version"] = f"reconstruccion_v{next_v}"
    d["meta"]["refinamiento_bleeds_ultimo"] = {
        "revisados": revisados,
        "modificados": modificados,
        "falsos_positivos_limpiados": falsos_positivos,
    }
    with open(BANCO, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(
        f"Revisados {revisados} | Modificados {modificados} | "
        f"Falsos positivos limpiados {falsos_positivos}"
    )


if __name__ == "__main__":
    main()
