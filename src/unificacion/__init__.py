"""Fase 5 — DCG + unificación: verifica que las rimas reales sean consistentes."""

from .dcg_rima import (
    unificar_rima,
    verificar_esquema,
    esquemas_candidatos,
    filtrar_hipotesis,
    filtrar_arboles_validos,
)

__all__ = [
    "unificar_rima",
    "verificar_esquema",
    "esquemas_candidatos",
    "filtrar_hipotesis",
    "filtrar_arboles_validos",
]
