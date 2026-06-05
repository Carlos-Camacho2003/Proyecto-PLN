"""
Detector de ambigüedad léxica — Fase 6.

Recibe los versos ya tokenizados (de la Fase 1) y reporta cada palabra
polisémica de jerga colombiana que encuentre, junto con todas sus
acepciones posibles.

Esto es el equivalente, en el dominio del rap, del desambiguador léxico
de la clase 9: allí detectaba palabras como `pelo` o `nota` que tienen
varias categorías gramaticales. Aquí detectamos jerga polisémica como
`vuelta`, `parcero`, `llave`, donde el problema no es la categoría sino
el SIGNIFICADO (acepción).

Ejemplos
--------
    Verso: "esa vuelta la arreglo yo"
    -> 'vuelta' tiene 2 acepciones:
       [1] asunto / encargo (paisa)
       [2] venganza / represalia (urbano)

    Verso: "mi parcero me dio la mano"
    -> 'parcero' tiene 2 acepciones:
       [1] amigo cercano (paisa)
       [2] apelativo genérico (nacional)
"""

from __future__ import annotations

from .jerga import consultar, es_polisemica, cargar_jerga


# --------------------------------------------------------------------------- #
# 1. Detectar palabras polisémicas en un verso
# --------------------------------------------------------------------------- #
def detectar_palabras_ambiguas(palabras_verso, jerga=None) -> list:
    """
    Recorre las palabras de UN verso y devuelve una lista de tuplas:
        [(posicion, palabra, [acepciones]), ...]

    Solo reporta palabras polisémicas (con MÁS DE una acepción en el JSON).
    `posicion` es el índice 0-based de la palabra dentro del verso.
    """
    if jerga is None:
        jerga = cargar_jerga()

    detectadas = []
    for i, palabra in enumerate(palabras_verso):
        if es_polisemica(palabra, jerga):
            detectadas.append((i, palabra, consultar(palabra, jerga)))
    return detectadas


# --------------------------------------------------------------------------- #
# 2. Analizar toda una letra (lista de versos)
# --------------------------------------------------------------------------- #
def analizar_ambiguedad_lexica(versos, jerga=None) -> list:
    """
    Recorre todos los versos y devuelve un informe con TODAS las palabras
    ambiguas encontradas. Formato:

        [
          {
            "verso_num": 2,
            "verso_texto": "esa vuelta la arreglo yo",
            "palabra": "vuelta",
            "posicion": 1,
            "acepciones": [ {...}, {...} ]
          },
          ...
        ]
    """
    if jerga is None:
        jerga = cargar_jerga()

    informe = []
    for n, palabras in enumerate(versos, start=1):
        ambiguas = detectar_palabras_ambiguas(palabras, jerga)
        for pos, palabra, acepciones in ambiguas:
            informe.append({
                "verso_num":   n,
                "verso_texto": " ".join(palabras),
                "palabra":     palabra,
                "posicion":    pos,
                "acepciones":  acepciones,
            })
    return informe


# --------------------------------------------------------------------------- #
# 3. Extracción de contexto: las palabras vecinas como pista de acepción
# --------------------------------------------------------------------------- #
def contexto_palabra(palabras_verso, posicion: int, ventana: int = 2) -> str:
    """
    Devuelve un fragmento de texto alrededor de `posicion` (±`ventana`
    palabras), con la palabra ambigua marcada con corchetes.

    Ejemplo:
        palabras = ["esa", "vuelta", "la", "arreglo", "yo"]
        posicion = 1, ventana = 2
        -> "esa [vuelta] la arreglo"
    """
    inicio = max(0, posicion - ventana)
    fin    = min(len(palabras_verso), posicion + ventana + 1)
    fragmento = []
    for i in range(inicio, fin):
        if i == posicion:
            fragmento.append(f"[{palabras_verso[i]}]")
        else:
            fragmento.append(palabras_verso[i])
    return " ".join(fragmento)
