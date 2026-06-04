"""Gramática (CFG) + parser de esquemas métricos — núcleo del sistema."""

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
    construir_chart,
    analizar, analizar_todos, analizar_con_fallback,
    nombre_esquema,
)

__all__ = [
    "Nodo",
    "gramatica", "gramatica_con_libre",
    "NO_TERMINALES", "TERMINALES", "SIMBOLO_INICIAL", "descripcion_formal",
    "construir_chart",
    "analizar", "analizar_todos", "analizar_con_fallback",
    "nombre_esquema",
]
