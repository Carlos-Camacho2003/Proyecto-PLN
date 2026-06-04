"""
Gramática CFG + Parser — acceso directo desde src.gramatica.

Re-exporta los componentes de src.cfg para que el pipeline y los tests
puedan importarlos con la ruta plana que usa el compañero (Fase 5).
"""

from src.cfg.gramatica import (
    gramatica,
    gramatica_con_libre,
    NO_TERMINALES,
    TERMINALES,
    SIMBOLO_INICIAL,
    descripcion_formal,
)
from src.cfg.parser import (
    parse,
    parse_todos,
    analizar,
    analizar_todos,
    analizar_con_fallback,
    nombre_esquema,
)

__all__ = [
    "gramatica", "gramatica_con_libre",
    "NO_TERMINALES", "TERMINALES", "SIMBOLO_INICIAL", "descripcion_formal",
    "parse", "parse_todos",
    "analizar", "analizar_todos", "analizar_con_fallback",
    "nombre_esquema",
]
