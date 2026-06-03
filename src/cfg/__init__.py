"""Fase 3 — CFG + Parser recursivo descendente para esquemas métricos."""

from .nodo            import Nodo
from .gramatica       import (
    gramatica,
    gramatica_con_libre,
    NO_TERMINALES,
    TERMINALES,
    SIMBOLO_INICIAL,
    descripcion_formal,
)
from .parser          import (
    parse, parse_todos,
    analizar, analizar_todos, analizar_con_fallback,
    nombre_esquema,
)
from .extractor_rima  import (
    terminacion_consonante,
    terminacion_asonante,
    palabra_final,
    secuencia_rimas,
    describir_esquema,
)

__all__ = [
    "Nodo",
    "gramatica", "gramatica_con_libre",
    "NO_TERMINALES", "TERMINALES", "SIMBOLO_INICIAL", "descripcion_formal",
    "parse", "parse_todos",
    "analizar", "analizar_todos", "analizar_con_fallback",
    "nombre_esquema",
    "terminacion_consonante", "terminacion_asonante", "palabra_final",
    "secuencia_rimas", "describir_esquema",
]
