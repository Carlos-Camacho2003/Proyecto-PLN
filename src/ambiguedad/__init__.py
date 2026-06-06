"""Fase 6 — Manejo de ambigüedad estructural y léxica."""

from .jerga import (
    cargar_jerga,
    consultar,
    es_polisemica,
    palabras_registradas,
)
from .detector_lexico import (
    detectar_palabras_ambiguas,
    analizar_ambiguedad_lexica,
    contexto_palabra,
)
from .reporte import (
    reportar_ambiguedad_estructural,
    reportar_ambiguedad_lexica,
    reporte_completo,
)

__all__ = [
    # jerga
    "cargar_jerga", "consultar", "es_polisemica", "palabras_registradas",
    # detector léxico
    "detectar_palabras_ambiguas", "analizar_ambiguedad_lexica", "contexto_palabra",
    # reporte
    "reportar_ambiguedad_estructural", "reportar_ambiguedad_lexica", "reporte_completo",
]
