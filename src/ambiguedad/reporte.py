"""
Reporte unificado de ambigüedad — Fase 6.

Genera el informe final del análisis con AMBOS tipos de ambigüedad:

    1. Estructural: cuando la CFG (Fase 4) produce más de un árbol válido
       para la misma estrofa (cuarteto AABB vs dos pareados, etc.).
       Esa información llega ya calculada desde `analizar_con_fallback`.

    2. Léxica: cuando el detector de jerga encuentra palabras polisémicas
       (vuelta, parcero, llave, ...) en los versos.

El módulo SOLO formatea texto legible. La lógica de análisis vive en las
fases 4 (estructural) y en `detector_lexico.py` (léxica).
"""

from __future__ import annotations

from src.gramatica import nombre_esquema
from .detector_lexico import analizar_ambiguedad_lexica, contexto_palabra


# --------------------------------------------------------------------------- #
# 1. Reporte de ambigüedad ESTRUCTURAL
# --------------------------------------------------------------------------- #
def reportar_ambiguedad_estructural(arboles, modo: str) -> str:
    """
    Toma la lista de árboles que devolvió `analizar_con_fallback` y produce
    un texto que muestra las lecturas alternativas.

    Si hay UN solo árbol → no hay ambigüedad estructural.
    Si hay VARIOS → se reportan todos con su nombre de esquema y su árbol.
    """
    if not arboles:
        return " (no se pudo reconocer ninguna estructura)"

    if len(arboles) == 1:
        return (f" Sin ambigüedad estructural.\n"
                f" Estructura única: {nombre_esquema(arboles[0])}")

    lineas = [f" AMBIGÜEDAD ESTRUCTURAL — {len(arboles)} lecturas posibles:"]
    for i, arbol in enumerate(arboles, start=1):
        lineas.append("")
        lineas.append(f"   ─ Lectura {i}: {nombre_esquema(arbol)}")
        for sub in arbol.mostrar().split("\n"):
            if sub.strip():
                lineas.append(f"      {sub}")
    return "\n".join(lineas)


# --------------------------------------------------------------------------- #
# 2. Reporte de ambigüedad LÉXICA
# --------------------------------------------------------------------------- #
def reportar_ambiguedad_lexica(versos_palabras, jerga=None) -> str:
    """
    Detecta toda la jerga polisémica en `versos_palabras` y produce el
    reporte legible con las acepciones de cada palabra encontrada.
    """
    informe = analizar_ambiguedad_lexica(versos_palabras, jerga)

    if not informe:
        return " No se detectó jerga polisémica en los versos."

    lineas = [f" AMBIGÜEDAD LÉXICA — {len(informe)} palabra(s) polisémica(s):"]
    for entrada in informe:
        n         = entrada["verso_num"]
        palabra   = entrada["palabra"]
        posicion  = entrada["posicion"]
        contexto  = contexto_palabra(
            entrada["verso_texto"].split(), posicion, ventana=2,
        )
        lineas.append("")
        lineas.append(f"   ★ '{palabra}'  (verso {n})")
        lineas.append(f"     contexto: ... {contexto} ...")
        lineas.append(f"     {len(entrada['acepciones'])} lecturas posibles:")
        for acep in entrada["acepciones"]:
            lineas.append(
                f"       [{acep['id']}] {acep['significado']:40s}"
                f"  ({acep['region']})"
            )
            if "ejemplo" in acep:
                lineas.append(f"           ej.: \"{acep['ejemplo']}\"")
    return "\n".join(lineas)


# --------------------------------------------------------------------------- #
# 3. Reporte unificado (las dos partes juntas)
# --------------------------------------------------------------------------- #
def reporte_completo(arboles, modo: str, versos_palabras, jerga=None) -> str:
    """
    Combina ambos reportes en un único texto. Es la función que llamará
    `main.py` desde la fase 6 del pipeline.
    """
    secciones = [
        " ── Ambigüedad estructural (Fase 4) ──",
        reportar_ambiguedad_estructural(arboles, modo),
        "",
        " ── Ambigüedad léxica (jerga colombiana) ──",
        reportar_ambiguedad_lexica(versos_palabras, jerga),
    ]
    return "\n".join(secciones)
