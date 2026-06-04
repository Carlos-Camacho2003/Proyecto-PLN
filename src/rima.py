"""
Extractor de rima — acceso directo desde src.rima.

Re-exporta los componentes de src.cfg.extractor_rima para que el pipeline
y los tests puedan importarlos con la ruta plana que usa el compañero (Fase 5).
"""

from src.cfg.extractor_rima import (
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
