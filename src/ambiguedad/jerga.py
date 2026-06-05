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
Cada palabra mapea a un objeto con una lista de `acepciones`. Cada acepción
tiene: id, significado, ejemplo, region, registro. Por ejemplo:

    "vuelta": {
        "acepciones": [
            {"id": 1, "significado": "encargo / asunto",  "region": "paisa", ...},
            {"id": 2, "significado": "venganza",          "region": "urbano", ...}
        ]
    }
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


def cargar_jerga(ruta: str = None) -> dict:
    """
    Lee el JSON de jerga y devuelve un diccionario:
        { palabra: { "acepciones": [ {...}, {...} ] }, ... }

    Las entradas que empiezan con '_' (como '_comentario') se descartan.
    Se cachea entre llamadas para no leer el archivo cada vez.
    """
    global _CACHE

    if ruta is None and _CACHE is not None:
        return _CACHE

    archivo = ruta or _RUTA_JSON
    with open(archivo, "r", encoding="utf-8") as f:
        datos = json.load(f)

    # Filtra metadatos (claves que empiezan con '_').
    jerga = {k: v for k, v in datos.items() if not k.startswith("_")}

    if ruta is None:
        _CACHE = jerga
    return jerga


def consultar(palabra: str, jerga: dict = None) -> list:
    """
    Devuelve la lista de acepciones de `palabra`.

    Si la palabra no está en el diccionario, retorna [].
    La búsqueda es case-insensitive.
    """
    if jerga is None:
        jerga = cargar_jerga()

    entrada = jerga.get(palabra.lower())
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
