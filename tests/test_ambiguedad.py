"""
Pruebas del manejo de ambigüedad (estructural + léxica).

Cubre:
    - jerga.py            : cargar_jerga, consultar, es_polisemica, palabras_registradas
    - detector_lexico.py  : detectar_palabras_ambiguas, analizar_ambiguedad_lexica,
                            contexto_palabra
    - reporte.py          : reportar_ambiguedad_estructural, reportar_ambiguedad_lexica,
                            reporte_completo

Los tests de reporte estructural usan un Nodo falso (stub) para no depender del
parser de la gramática. Los tests léxicos usan un JSON mínimo temporal y, al
final, el JSON real de data/.

Correr desde la raíz del proyecto:
    python tests/test_ambiguedad.py
"""

from __future__ import annotations

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.ambiguedad.jerga import (
    cargar_jerga, consultar, es_polisemica, palabras_registradas, indice_variantes,
)
from src.ambiguedad.detector_lexico import (
    detectar_palabras_ambiguas, analizar_ambiguedad_lexica, contexto_palabra,
)
from src.ambiguedad.reporte import (
    reportar_ambiguedad_estructural, reportar_ambiguedad_lexica, reporte_completo,
)


_RESULTADOS = {"ok": 0, "fail": 0}


def check(condicion, descripcion):
    if condicion:
        _RESULTADOS["ok"] += 1
        print("  [OK] " + descripcion)
    else:
        _RESULTADOS["fail"] += 1
        print("  [FALLO] " + descripcion)


# --------------------------------------------------------------------------- #
# Utilidades: JSON de jerga en archivos temporales
# --------------------------------------------------------------------------- #

_TEMPORALES = []


def _escribir_json_temporal(datos):
    """Escribe `datos` en un JSON temporal y devuelve su ruta (se borra al final)."""
    fd, ruta = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False)
    _TEMPORALES.append(ruta)
    return ruta


def _crear_jerga_mini():
    """JSON mínimo con 3 palabras: 2 polisémicas, 1 con una sola acepción."""
    datos = {
        "vuelta": {
            "acepciones": [
                {"id": 1, "significado": "asunto / encargo", "region": "paisa",
                 "registro": "coloquial", "ejemplo": "tengo una vuelta"},
                {"id": 2, "significado": "venganza / represalia", "region": "urbano",
                 "registro": "informal", "ejemplo": "esa vuelta la cobro"},
            ]
        },
        "parcero": {
            "acepciones": [
                {"id": 1, "significado": "amigo cercano", "region": "paisa",
                 "registro": "coloquial", "ejemplo": "mi parcero"},
                {"id": 2, "significado": "apelativo genérico", "region": "nacional",
                 "registro": "informal", "ejemplo": "qué más, parcero"},
            ]
        },
        "barrio": {
            "acepciones": [
                {"id": 1, "significado": "zona residencial", "region": "nacional",
                 "registro": "estándar", "ejemplo": "vivo en el barrio"},
            ]
        },
    }
    return _escribir_json_temporal(datos)


def _limpiar_temporales():
    for ruta in _TEMPORALES:
        try:
            os.remove(ruta)
        except OSError:
            pass


class _NodoStub:
    """Stub mínimo de Nodo para probar reportar_ambiguedad_estructural sin parser."""
    def __init__(self, etiqueta, hijos=None):
        self.etiqueta = etiqueta
        self.hijos = hijos or []

    def mostrar(self):
        return f"({self.etiqueta})"

    def hojas(self):
        resultado = []
        for hijo in self.hijos:
            if isinstance(hijo, _NodoStub):
                resultado.extend(hijo.hojas())
            else:
                resultado.append(hijo)
        return resultado


# ════════════════════════════════════════════════════════════════════════════ #
# 1. jerga.py
# ════════════════════════════════════════════════════════════════════════════ #

def test_jerga(jerga_mini):
    print("\n[jerga.py — carga y consulta]")

    j = cargar_jerga(jerga_mini)
    check(isinstance(j, dict), "cargar_jerga devuelve un dict")
    check("vuelta" in j and "parcero" in j, "contiene las palabras conocidas")

    # Filtra claves privadas (las que empiezan por '_').
    ruta_priv = _escribir_json_temporal(
        {"_comentario": "ignorar", "vuelta": {"acepciones": [{"id": 1}]}}
    )
    jp = cargar_jerga(ruta_priv)
    check("_comentario" not in jp and "vuelta" in jp, "filtra claves privadas ('_...')")

    # consultar
    check(len(consultar("vuelta", j)) == 2, "consultar('vuelta') → 2 acepciones")
    check(len(consultar("barrio", j)) == 1, "consultar('barrio') → 1 acepción")
    check(consultar("palabra_inexistente", j) == [], "consultar(ausente) → []")
    check(len(consultar("VUELTA", j)) == 2 and len(consultar("Parcero", j)) == 2,
          "consultar es insensible a mayúsculas")

    # es_polisemica
    check(es_polisemica("vuelta", j) is True, "es_polisemica('vuelta') → True")
    check(es_polisemica("barrio", j) is False, "es_polisemica('barrio') → False")
    check(es_polisemica("inexistente", j) is False, "es_polisemica(ausente) → False")

    # palabras_registradas
    reg = palabras_registradas(j)
    check(isinstance(reg, set), "palabras_registradas devuelve un set")
    check({"vuelta", "parcero", "barrio"} <= reg, "el set contiene todas las palabras")


# ════════════════════════════════════════════════════════════════════════════ #
# 2. detector_lexico.py
# ════════════════════════════════════════════════════════════════════════════ #

def test_detector_lexico(jerga_mini):
    print("\n[detector_lexico.py — detección y contexto]")
    j = cargar_jerga(jerga_mini)

    resultado = detectar_palabras_ambiguas(["esa", "vuelta", "es", "mía"], j)
    ok = (len(resultado) == 1 and resultado[0][1] == "vuelta"
          and resultado[0][0] == 1 and len(resultado[0][2]) == 2)
    check(ok, "detecta 'vuelta' polisémica con su posición y acepciones")

    check(detectar_palabras_ambiguas(["vivo", "en", "el", "barrio"], j) == [],
          "ignora la palabra monosémica 'barrio'")
    check(detectar_palabras_ambiguas(["llevo", "el", "rap", "conmigo"], j) == [],
          "verso sin jerga → []")
    check(len(detectar_palabras_ambiguas(["mi", "parcero", "hace", "la", "vuelta"], j)) == 2,
          "detecta dos polisémicas en el mismo verso")

    # analizar_ambiguedad_lexica
    versos = [["esa", "vuelta", "la", "cobro"], ["mi", "parcero", "me", "ayuda"]]
    informe = analizar_ambiguedad_lexica(versos, j)
    ok = (len(informe) == 2
          and informe[0]["palabra"] == "vuelta" and informe[0]["verso_num"] == 1
          and informe[1]["palabra"] == "parcero" and informe[1]["verso_num"] == 2)
    check(ok, "analizar_ambiguedad_lexica reporta palabra y verso_num correctos")
    check(analizar_ambiguedad_lexica([["llevo", "el", "barrio"]], j) == [],
          "sin jerga polisémica → informe vacío")
    check(analizar_ambiguedad_lexica([["sin", "jerga"], ["con", "vuelta"]], j)[0]["verso_num"] == 2,
          "verso_num apunta al verso correcto")

    # contexto_palabra
    ctx = contexto_palabra(["esa", "vuelta", "la", "arreglo", "yo"], 1, ventana=2)
    check("[vuelta]" in ctx and "esa" in ctx and "la" in ctx, "contexto centra y marca [palabra]")
    check(contexto_palabra(["vuelta", "al", "barrio"], 0, ventana=2).startswith("[vuelta]"),
          "contexto en la primera palabra")
    check(contexto_palabra(["lo", "hago", "por", "parcero"], 3, ventana=2).endswith("[parcero]"),
          "contexto en la última palabra")
    ctx1 = contexto_palabra(["a", "b", "c", "d", "e"], 2, ventana=1)
    check("b" in ctx1 and "[c]" in ctx1 and "d" in ctx1 and "a" not in ctx1 and "e" not in ctx1,
          "ventana=1 toma solo el vecino inmediato")


# ════════════════════════════════════════════════════════════════════════════ #
# 3. reporte.py
# ════════════════════════════════════════════════════════════════════════════ #

def test_reporte(jerga_mini):
    print("\n[reporte.py — ambigüedad estructural y léxica]")
    j = cargar_jerga(jerga_mini)

    # Estructural
    check("no se pudo" in reportar_ambiguedad_estructural([], "clasica").lower(),
          "sin árboles → mensaje 'no se pudo'")
    r1 = reportar_ambiguedad_estructural([_NodoStub("Cuarteto", ["A", "A", "B", "B"])], "clasica")
    check("sin ambigüedad" in r1.lower() or "única" in r1.lower(),
          "un solo árbol → 'sin ambigüedad'/'única'")
    r2 = reportar_ambiguedad_estructural(
        [_NodoStub("Cuarteto", ["A", "A", "A", "A"]),
         _NodoStub("DosPareados", ["A", "A", "B", "B"])], "clasica")
    check("2" in r2 and "Lectura 1" in r2 and "Lectura 2" in r2,
          "dos árboles → reporta las 2 lecturas")

    # Léxica
    check("no se detectó" in reportar_ambiguedad_lexica([["llevo", "el", "rap"]], j).lower(),
          "verso sin jerga → 'no se detectó'")
    rl = reportar_ambiguedad_lexica([["esa", "vuelta", "la", "cobro", "yo"]], j)
    check("vuelta" in rl and "2 lecturas" in rl, "muestra 'vuelta' con sus 2 lecturas")
    check("paisa" in reportar_ambiguedad_lexica([["esa", "vuelta"]], j)
          or "urbano" in reportar_ambiguedad_lexica([["esa", "vuelta"]], j),
          "el reporte incluye la región de la acepción")

    # reporte_completo
    rc = reporte_completo([_NodoStub("Cuarteto", ["A", "A", "B", "B"])],
                          "clasica", [["esa", "vuelta", "la", "cobro"]], j)
    check("estructural" in rc.lower() and ("léxica" in rc.lower() or "lexica" in rc.lower()),
          "reporte_completo contiene ambas secciones")


# ════════════════════════════════════════════════════════════════════════════ #
# 4. Integración con el JSON real de data/
# ════════════════════════════════════════════════════════════════════════════ #

def test_robustez():
    print("\n[Robustez: variantes declaradas, sin stemming ciego]")
    jerga = {
        "parcero": {
            "variantes": ["parceros", "parcera"],
            "acepciones": [
                {"id": 1, "significado": "amigo",     "region": "paisa"},
                {"id": 2, "significado": "apelativo", "region": "nacional"},
            ],
        },
        "vacano": {
            "variantes": ["bacano", "vacana"],
            "acepciones": [
                {"id": 1, "significado": "chévere",     "region": "nacional"},
                {"id": 2, "significado": "de calidad",  "region": "nacional"},
            ],
        },
    }
    check(es_polisemica("parceros", jerga), "plural 'parceros' resuelve a 'parcero'")
    check(es_polisemica("Parcera", jerga), "género + mayúscula 'Parcera' resuelve")
    check(es_polisemica("bacano", jerga), "grafía alterna 'bacano' resuelve a 'vacano'")
    check(consultar("parceros", jerga) == consultar("parcero", jerga),
          "la variante devuelve las mismas acepciones que la canónica")
    check(not es_polisemica("parceritos", jerga),
          "una forma NO declarada no se inventa (sin stemming ciego)")
    check(indice_variantes(jerga).get("bacano") == "vacano",
          "el índice mapea variante → canónica")


def test_json_real():
    print("\n[Integración con data/jerga_colombiana.json]")
    j = cargar_jerga()
    check(isinstance(j, dict) and len(j) > 0, "el JSON real existe y carga con entradas")
    check(es_polisemica("vuelta", j), "'vuelta' es polisémica en el JSON real")
    check(es_polisemica("parcero", j), "'parcero' es polisémico en el JSON real")

    # Robustez contra el JSON real (palabras nuevas + variantes + falso positivo).
    check(es_polisemica("vaina", j), "palabra nueva 'vaina' es polisémica en el JSON real")
    check(es_polisemica("verraco", j), "palabra nueva 'verraco' es polisémica")
    check(es_polisemica("parceros", j), "plural 'parceros' reconocido contra el JSON real")
    check(not es_polisemica("notas", j), "el verbo 'notas' NO se confunde con 'nota'")

    completo = True
    for palabra, entrada in j.items():
        for acep in entrada.get("acepciones", []):
            if not ("id" in acep and "significado" in acep and "region" in acep):
                completo = False
    check(completo, "toda acepción tiene 'id', 'significado' y 'region'")


def main():
    print("=" * 64)
    print(" PRUEBAS - Manejo de ambigüedad (estructural + léxica)")
    print("=" * 64)
    jerga_mini = _crear_jerga_mini()
    try:
        test_jerga(jerga_mini)
        test_detector_lexico(jerga_mini)
        test_reporte(jerga_mini)
        test_robustez()
        test_json_real()
    finally:
        _limpiar_temporales()

    print("\n" + "=" * 64)
    total = _RESULTADOS["ok"] + _RESULTADOS["fail"]
    print(" RESULTADO: %d/%d pruebas OK, %d fallidas"
          % (_RESULTADOS["ok"], total, _RESULTADOS["fail"]))
    print("=" * 64)
    sys.exit(1 if _RESULTADOS["fail"] else 0)


if __name__ == "__main__":
    main()
