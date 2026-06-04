"""Extracción de rima — convierte versos en la secuencia simbólica de rimas."""

from .extractor_rima import (
    terminacion_consonante,
    terminacion_asonante,
    palabra_final,
    secuencia_rimas,
    describir_esquema,
)

__all__ = [
    "terminacion_consonante",
    "terminacion_asonante",
    "palabra_final",
    "secuencia_rimas",
    "describir_esquema",
]
