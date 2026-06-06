"""Fase 2 — Silabeo del español y conteo métrico (sinalefa + acento final)."""

from .silabeador import (
    silabas,
    contar_silabas,
    tonicidad,
    contar_silabas_verso,
)

__all__ = ["silabas", "contar_silabas", "tonicidad", "contar_silabas_verso"]
