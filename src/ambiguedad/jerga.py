"""
Diccionario de jerga colombiana polisémica — Fase 6.

Carga `data/jerga_colombiana.json` y ofrece dos operaciones simples:

    - `cargar_jerga()`        : lee el archivo y devuelve el diccionario.
    - `consultar(palabra)`    : devuelve todas las acepciones de una palabra
                                o lista vacía si no es ambigua.
    - `es_polisemica(palabra)`: True si tiene más de una acepción.

El JSON es la fuente de verdad: para añadir más jerga (chimba, parcero,
vacano, etc.) basta editar el archivo, no el código.

Formato del JSON
----------------
Cada palabra mapea a un objeto con una lista de `acepciones` y, opcionalmente,
una lista de `variantes` (plurales, género, grafías alternativas) que se
reconocen como la misma palabra. Cada acepción tiene: id, significado, ejemplo,
region, registro. Por ejemplo:

    "vuelta": {
        "variantes": ["vueltas"],
        "acepciones": [
            {"id": 1, "significado": "encargo / asunto",  "region": "paisa", ...},
            {"id": 2, "significado": "venganza",          "region": "urbano", ...}
        ]
    }

Reconocimiento robusto
----------------------
`consultar` es insensible a mayúsculas y resuelve las formas declaradas en
`variantes` a su palabra canónica (p. ej. 'Parceros' → 'parcero'). Se usan
variantes EXPLÍCITAS en vez de stemming automático para no producir falsos
positivos (p. ej. el verbo 'notas' no debe confundirse con el sustantivo
'nota').
"""

from __future__ import annotations

import json
import os


# Ruta absoluta al JSON: sube tres niveles desde src/ambiguedad/ hasta la raíz
# del proyecto, luego baja a data/.
_RUTA_JSON = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "jerga_colombiana.json",
)

# Caché global: el JSON se lee una sola vez y se guarda en memoria.
_CACHE = None
# Caché del índice de variantes → palabra canónica (para la jerga por defecto).
_INDICE_CACHE = None


def cargar_jerga(ruta: str = None) -> dict:
    """
    Lee el JSON de jerga y devuelve un diccionario:
        { palabra: { "acepciones": [ {...}, {...} ] }, ... }

    Las entradas que empiezan con '_' (como '_comentario') se descartan.
    Se cachea entre llamadas para no leer el archivo cada vez.
    """
    global _CACHE, _INDICE_CACHE

    if ruta is None and _CACHE is not None:
        return _CACHE

    archivo = ruta or _RUTA_JSON
    with open(archivo, "r", encoding="utf-8") as f:
        datos = json.load(f)

    # Filtra metadatos (claves que empiezan con '_').
    jerga = {k: v for k, v in datos.items() if not k.startswith("_")}

    if ruta is None:
        _CACHE = jerga
        _INDICE_CACHE = None      # se reconstruye al primer uso
    return jerga


def _normalizar(palabra: str) -> str:
    return palabra.strip().lower()


def _construir_indice(jerga: dict) -> dict:
    """Mapa {variante: palabra_canonica} a partir del campo opcional 'variantes'."""
    indice = {}
    for canonica, entrada in jerga.items():
        for var in entrada.get("variantes", []):
            indice[_normalizar(var)] = canonica
    return indice


def indice_variantes(jerga: dict = None) -> dict:
    """Devuelve el índice {variante: canónica}. Cachea el de la jerga por
    defecto; para una jerga ad-hoc (tests) lo construye al vuelo."""
    global _INDICE_CACHE
    if jerga is None:
        jerga = cargar_jerga()
    if jerga is _CACHE:
        if _INDICE_CACHE is None:
            _INDICE_CACHE = _construir_indice(jerga)
        return _INDICE_CACHE
    return _construir_indice(jerga)


def consultar(palabra: str, jerga: dict = None) -> list:
    """
    Devuelve la lista de acepciones de `palabra` (o [] si no es jerga).

    El reconocimiento es insensible a mayúsculas y admite las formas declaradas
    en el campo 'variantes' de cada entrada (plurales, género, grafías
    alternativas). Ejemplo: 'Parceros' → acepciones de 'parcero'.
    """
    if jerga is None:
        jerga = cargar_jerga()

    p = _normalizar(palabra)

    entrada = jerga.get(p)
    if entrada is None:                              # ¿es una variante declarada?
        canonica = indice_variantes(jerga).get(p)
        if canonica is not None:
            entrada = jerga.get(canonica)

    if entrada is None:
        return []
    return entrada.get("acepciones", [])


def es_polisemica(palabra: str, jerga: dict = None) -> bool:
    """True si la palabra tiene MÁS DE UNA acepción registrada."""
    return len(consultar(palabra, jerga)) > 1


def palabras_registradas(jerga: dict = None) -> set:
    """Conjunto de todas las palabras de jerga conocidas (útil para tests)."""
    if jerga is None:
        jerga = cargar_jerga()
    return set(jerga.keys())
