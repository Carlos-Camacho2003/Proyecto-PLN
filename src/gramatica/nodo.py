"""
Clase Nodo — bloque base del árbol de derivación (Fase 3).

Un árbol de derivación representa la estructura métrica de una estrofa
según la CFG. Cada nodo tiene:

    etiqueta : nombre del símbolo no-terminal (Estrofa, Cuarteto, Pareado, ...)
               o el símbolo de rima terminal (A, B, C, ...).
    hijos    : lista de subnodos o terminales (cadenas).

Basado en la clase 6,
adaptada al dominio del proyecto: aquí los terminales no son palabras
sino etiquetas simbólicas de rima ('A', 'B', ...).
"""

from __future__ import annotations


class Nodo:
    """Nodo del árbol de derivación."""

    def __init__(self, etiqueta, hijos=None):
        self.etiqueta = etiqueta
        self.hijos    = hijos if hijos else []

    # ------------------------------------------------------------------ #
    # Representación textual con sangría — sin necesidad de matplotlib.
    # ------------------------------------------------------------------ #
    def mostrar(self, nivel: int = 0) -> str:
        sangria = "  " * nivel
        salida  = f"{sangria}{self.etiqueta}\n"
        for hijo in self.hijos:
            if isinstance(hijo, Nodo):
                salida += hijo.mostrar(nivel + 1)
            else:
                salida += f"{'  ' * (nivel + 1)}{hijo}\n"
        return salida

    # ------------------------------------------------------------------ #
    # Recorre las hojas del árbol de izquierda a derecha.
    # Sirve para reconstruir la secuencia de rimas original ('AABB', etc.)
    # y verificar que el árbol corresponde a la entrada.
    # ------------------------------------------------------------------ #
    def hojas(self):
        resultado = []
        for hijo in self.hijos:
            if isinstance(hijo, Nodo):
                resultado.extend(hijo.hojas())
            else:
                resultado.append(hijo)
        return resultado

    def __repr__(self):
        return self.mostrar()
