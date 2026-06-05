"""Fase 7 — PCFG: desambiguación probabilística de la estructura métrica."""

from .gramatica_probabilistica import (
    gramatica_pcfg,
    validar_pcfg,
    probabilidad_regla,
    descripcion_formal_pcfg,
)
from .calculadora import (
    probabilidad_arbol,
    reglas_usadas,
    desglose_probabilidad,
)
from .desambiguador import (
    rankear_arboles,
    mejor_arbol,
    reporte_ranking,
    reporte_desglose_ganador,
)

__all__ = [
    # gramática
    "gramatica_pcfg", "validar_pcfg",
    "probabilidad_regla", "descripcion_formal_pcfg",
    # calculadora
    "probabilidad_arbol", "reglas_usadas", "desglose_probabilidad",
    # desambiguador
    "rankear_arboles", "mejor_arbol",
    "reporte_ranking", "reporte_desglose_ganador",
]
