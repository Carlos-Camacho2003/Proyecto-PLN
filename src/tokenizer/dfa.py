"""
Motor de Autómata Finito Determinista (DFA) — construido desde cero.

Un DFA es la 5-tupla formal  M = (Q, Σ, δ, q0, F):

    Q   conjunto de estados
    Σ   alfabeto (símbolos de entrada)
    δ   función de transición  δ: Q × Σ → Q
    q0  estado inicial
    F   conjunto de estados de aceptación

Esta clase es genérica: no sabe nada de texto ni de tokens. El tokenizador
(tokenizer.py) la usa pasándole como "símbolos" las *clases de carácter*
(letra, dígito, signo, ...), que es la forma habitual de aplicar un autómata
a un alfabeto grande como el del español.

Además del reconocimiento clásico (`acepta`), se incluye `match_mas_largo`,
que implementa la estrategia *maximal munch* (el prefijo aceptado más largo),
imprescindible para tokenizar.
"""

from __future__ import annotations


class DFA:
    """Autómata Finito Determinista genérico."""

    def __init__(self, estados, alfabeto, transiciones, inicial, aceptacion):
        """
        Parámetros
        ----------
        estados : iterable de estados (cualquier valor hashable).
        alfabeto : iterable de símbolos de entrada.
        transiciones : dict {(estado, simbolo): estado_destino}  (la función δ).
        inicial : estado inicial q0.
        aceptacion : puede ser
            - un dict {estado: etiqueta}  -> útil para devolver el *tipo* de token, o
            - un conjunto/lista de estados -> la etiqueta será el propio estado.
        """
        self.Q = set(estados)
        self.Sigma = set(alfabeto)
        self.delta = dict(transiciones)
        self.q0 = inicial

        if isinstance(aceptacion, dict):
            self.F = dict(aceptacion)
        else:
            self.F = {estado: estado for estado in aceptacion}

        self._validar()

    # ------------------------------------------------------------------ #
    # Validación de la definición formal
    # ------------------------------------------------------------------ #
    def _validar(self):
        if self.q0 not in self.Q:
            raise ValueError(f"El estado inicial {self.q0!r} no está en Q.")
        for estado in self.F:
            if estado not in self.Q:
                raise ValueError(f"Estado de aceptación {estado!r} no está en Q.")
        for (estado, simbolo), destino in self.delta.items():
            if estado not in self.Q:
                raise ValueError(f"Transición desde estado desconocido {estado!r}.")
            if destino not in self.Q:
                raise ValueError(f"Transición hacia estado desconocido {destino!r}.")
            if simbolo not in self.Sigma:
                raise ValueError(f"Símbolo {simbolo!r} no está en el alfabeto Σ.")

    # ------------------------------------------------------------------ #
    # Operación básica: δ(estado, símbolo)
    # ------------------------------------------------------------------ #
    def transicion(self, estado, simbolo):
        """Devuelve δ(estado, símbolo) o None si no hay transición definida."""
        return self.delta.get((estado, simbolo))

    # ------------------------------------------------------------------ #
    # Reconocimiento clásico: ¿la cadena completa es aceptada?
    # ------------------------------------------------------------------ #
    def acepta(self, simbolos) -> bool:
        """True si el autómata termina en un estado de aceptación tras leer
        toda la secuencia de símbolos."""
        estado = self.q0
        for simbolo in simbolos:
            estado = self.delta.get((estado, simbolo))
            if estado is None:
                return False
        return estado in self.F

    def recorrido(self, simbolos):
        """Devuelve la lista de estados visitados (útil para depurar/visualizar).
        Si encuentra una transición indefinida, corta el recorrido ahí."""
        estado = self.q0
        camino = [estado]
        for simbolo in simbolos:
            estado = self.delta.get((estado, simbolo))
            if estado is None:
                break
            camino.append(estado)
        return camino

    # ------------------------------------------------------------------ #
    # Maximal munch: prefijo aceptado más largo (para tokenizar)
    # ------------------------------------------------------------------ #
    def match_mas_largo(self, simbolos, inicio=0):
        """
        Lee `simbolos` desde la posición `inicio` y devuelve la tupla
        (longitud, etiqueta) correspondiente al prefijo ACEPTADO más largo.

        Si no se acepta ningún prefijo, devuelve (0, None).
        """
        estado = self.q0
        mejor_longitud = 0
        mejor_etiqueta = None

        i = inicio
        while i < len(simbolos):
            estado = self.delta.get((estado, simbolos[i]))
            if estado is None:
                break
            i += 1
            if estado in self.F:          # registramos el último estado de aceptación
                mejor_longitud = i - inicio
                mejor_etiqueta = self.F[estado]

        return mejor_longitud, mejor_etiqueta

    # ------------------------------------------------------------------ #
    def __repr__(self):
        return (f"DFA(|Q|={len(self.Q)}, |Σ|={len(self.Sigma)}, "
                f"|δ|={len(self.delta)}, q0={self.q0!r}, |F|={len(self.F)})")
