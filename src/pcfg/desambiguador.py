"""
Desambiguador probabilístico — Fase 7.

Resuelve la ambigüedad estructural usando las probabilidades de la PCFG.

Cuando la Fase 4 entrega múltiples árboles válidos para la misma estrofa
(ej. cuarteto AABB vs dos pareados AA-BB), este módulo:

    1. Calcula P(árbol) para cada uno.
    2. Los ordena de mayor a menor probabilidad.
    3. Reporta el árbol GANADOR y un ranking con todas las alternativas.

Esto convierte a la Fase 6 ("aquí tienes 2 lecturas, decide tú") en una
respuesta concluyente: "la lectura más probable es X, con estas alternativas".
"""

from __future__ import annotations

from src.gramatica import Nodo, nombre_esquema
from .gramatica_probabilistica import gramatica_pcfg
from .calculadora import probabilidad_arbol, desglose_probabilidad


def rankear_arboles(arboles, gram=None) -> list:
    """
    Toma la lista de árboles de la Fase 4 y los devuelve ordenados
    de mayor a menor probabilidad como lista de tuplas (arbol, probabilidad).
    """
    if gram is None:
        gram = gramatica_pcfg

    if not arboles:
        return []

    con_prob = [(a, probabilidad_arbol(a, gram)) for a in arboles]
    con_prob.sort(key=lambda par: par[1], reverse=True)
    return con_prob


def mejor_arbol(arboles, gram=None):
    """Devuelve el árbol de mayor probabilidad, o None si la lista está vacía."""
    ranking = rankear_arboles(arboles, gram)
    return ranking[0][0] if ranking else None


def reporte_ranking(arboles, gram=None) -> str:
    """
    Genera un texto con el ranking ordenado por probabilidad, marcando el
    ganador y mostrando todas las alternativas con su porcentaje normalizado.
    """
    if gram is None:
        gram = gramatica_pcfg

    ranking = rankear_arboles(arboles, gram)

    if not ranking:
        return " (no hay árboles para evaluar con la PCFG)"

    if len(ranking) == 1:
        arbol, prob = ranking[0]
        return (f" Única lectura posible: {nombre_esquema(arbol)}\n"
                f"   P(árbol) = {prob:.6f}")

    lineas = [f" Ranking probabilístico — {len(ranking)} lecturas:"]
    suma = sum(p for _, p in ranking) or 1.0

    for i, (arbol, prob) in enumerate(ranking, start=1):
        porc = (prob / suma) * 100
        marca = "✓" if i == 1 else " "
        lineas.append(
            f"   {marca} #{i}  {nombre_esquema(arbol):30s}"
            f"  P = {prob:.6f}   ({porc:5.1f}% normalizado)"
        )

    lineas.append("")
    lineas.append(f" → Lectura elegida: {nombre_esquema(ranking[0][0])}")
    return "\n".join(lineas)


def reporte_desglose_ganador(arboles, gram=None) -> str:
    """
    Muestra paso a paso cómo se calculó la probabilidad del árbol elegido:
    cada regla aplicada y su probabilidad parcial.
    """
    if gram is None:
        gram = gramatica_pcfg

    ganador = mejor_arbol(arboles, gram)
    if ganador is None:
        return " (sin ganador: no hay árboles)"

    info = desglose_probabilidad(ganador, gram)
    lineas = [f" Desglose de P(árbol ganador) = {info['total']:.6f}:"]
    lineas.append("")
    for (lhs, rhs), prob in zip(info["reglas"], info["probs"]):
        regla_txt = f"{lhs} → {' '.join(rhs)}"
        lineas.append(f"   P({regla_txt:35s}) = {prob:.4f}")
    lineas.append("")
    lineas.append(f"   Producto total = {info['total']:.6f}")
    return "\n".join(lineas)
