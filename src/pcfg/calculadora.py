"""
Calculadora de probabilidades de árboles — Fase 7.

Dado un árbol de derivación producido por el parser de la Fase 4, calcula
su probabilidad como producto de las probabilidades de TODAS las reglas
que se usaron para construirlo.

Fórmula (de la clase 10)
-----------------------
    P(T) = ∏ P(regla)  para cada regla que aparece en el árbol T

Por ejemplo, para un árbol que reconoce ['A','A','B','B'] como Cuarteto:

    Estrofa  → Cuarteto                  P = 0.50
    Cuarteto → A A B B                   P = 0.35
    ──────────────────────────────────────────────
    P(árbol) = 0.50 × 0.35 = 0.175

Y para el mismo input como DosPareados:

    Estrofa     → DosPareados            P = 0.20
    DosPareados → Pareado Pareado        P = 1.00
    Pareado     → A A                    P = 0.20
    Pareado     → B B                    P = 0.20
    ──────────────────────────────────────────────────
    P(árbol) = 0.20 × 1.00 × 0.20 × 0.20 = 0.008

Conclusión: el cuarteto AABB es ~22 veces más probable que dos pareados.
"""

from __future__ import annotations

from src.gramatica import Nodo
from .gramatica_probabilistica import probabilidad_regla, gramatica_pcfg


def probabilidad_arbol(arbol: Nodo, gram=None) -> float:
    """
    Calcula P(arbol) = producto de P(reglas) usadas en su construcción.

    Recorre el árbol en profundidad. Para cada nodo interno (no-terminal):
        1. Reconstruye la regla aplicada: lhs = etiqueta, rhs = etiquetas de hijos.
        2. Consulta su probabilidad en la PCFG.
        3. Multiplica recursivamente por las probabilidades de los subárboles.

    Las hojas (terminales como 'A', 'B', ...) no aportan factor.
    """
    if gram is None:
        gram = gramatica_pcfg

    if not isinstance(arbol, Nodo):
        return 1.0

    rhs = []
    for hijo in arbol.hijos:
        if isinstance(hijo, Nodo):
            rhs.append(hijo.etiqueta)
        else:
            rhs.append(hijo)

    p_regla = probabilidad_regla(arbol.etiqueta, rhs, gram)

    p_total = p_regla
    for hijo in arbol.hijos:
        p_total *= probabilidad_arbol(hijo, gram)

    return p_total


def reglas_usadas(arbol: Nodo) -> list:
    """
    Devuelve la lista de tuplas (lhs, rhs) de TODAS las reglas aplicadas
    en el árbol, en orden de recorrido en profundidad.
    """
    if not isinstance(arbol, Nodo):
        return []

    rhs = []
    for hijo in arbol.hijos:
        if isinstance(hijo, Nodo):
            rhs.append(hijo.etiqueta)
        else:
            rhs.append(hijo)

    reglas = [(arbol.etiqueta, rhs)]
    for hijo in arbol.hijos:
        reglas.extend(reglas_usadas(hijo))
    return reglas


def desglose_probabilidad(arbol: Nodo, gram=None) -> dict:
    """
    Devuelve un dict con el cálculo paso a paso de P(árbol):

        {
          "reglas": [ ("Estrofa", ["Cuarteto"]),
                      ("Cuarteto", ["A","A","B","B"]) ],
          "probs":  [ 0.50, 0.35 ],
          "total":  0.175
        }
    """
    if gram is None:
        gram = gramatica_pcfg

    reglas = reglas_usadas(arbol)
    probs  = [probabilidad_regla(lhs, rhs, gram) for lhs, rhs in reglas]

    total = 1.0
    for p in probs:
        total *= p

    return {"reglas": reglas, "probs": probs, "total": total}
