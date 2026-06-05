"""
Gramática de Contexto Libre Probabilística (PCFG) — Fase 7.

Es la MISMA gramática de la Fase 4, pero ahora cada producción tiene una
PROBABILIDAD asociada. Esto permite, ante varias derivaciones válidas,
elegir la más plausible.

Formalmente, una PCFG es una 5-tupla:

    G_p = (V, T, P, S, ρ)

donde (V, T, P, S) es la CFG de la Fase 4 y ρ: P → [0,1] asigna a cada
producción su probabilidad. Requisito: la suma de probabilidades de las
producciones que comparten el mismo lado izquierdo es 1.

Cómo se estiman las probabilidades
----------------------------------
En un proyecto real se contarían las apariciones de cada regla en un corpus
anotado (treebank), siguiendo la fórmula de la clase 10:

    P(A → α) = veces(A → α) / veces(A)

Aquí las hemos estimado a mano observando qué formas métricas son típicas
en rap colombiano:

    - El cuarteto cruzado ABAB es el esquema más común en rap clásico.
    - AABB también es muy frecuente, sobre todo en estribillos.
    - AAAA es raro fuera del freestyle improvisado.
    - DosPareados es válido pero menos esperable como lectura primaria.
"""

from __future__ import annotations


# --------------------------------------------------------------------------- #
# Producciones P y la función de probabilidad ρ
# --------------------------------------------------------------------------- #
# Cada entrada del diccionario representa el lado izquierdo de una regla.
# El valor es una lista de tuplas (produccion, probabilidad).
# Las probabilidades de cada no-terminal deben sumar 1.
# --------------------------------------------------------------------------- #
gramatica_pcfg = {

    'Estrofa': [
        (['Cuarteto'],     0.50),
        (['DosPareados'],  0.20),
        (['Pareado'],      0.20),
        (['Terceto'],      0.10),
    ],

    'Cuarteto': [
        (['A', 'B', 'A', 'B'],  0.40),   # cruzado: rey del rap clásico colombiano
        (['A', 'A', 'B', 'B'],  0.35),   # pareado pegado, común en estribillos
        (['A', 'B', 'B', 'A'],  0.15),   # abrazado: menos común
        (['A', 'A', 'A', 'A'],  0.10),   # monorrimo: raro fuera de freestyle
    ],

    'DosPareados': [
        (['Pareado', 'Pareado'],  1.00),
    ],

    'Terceto': [
        (['A', 'A', 'A'],  0.50),
        (['A', 'B', 'A'],  0.50),
    ],

    'Pareado': [
        (['A', 'A'],  0.20),
        (['B', 'B'],  0.20),
        (['C', 'C'],  0.20),
        (['D', 'D'],  0.20),
        (['E', 'E'],  0.20),
    ],
}


# --------------------------------------------------------------------------- #
# Validación: las probabilidades de cada no-terminal deben sumar 1.0
# --------------------------------------------------------------------------- #
TOLERANCIA = 1e-6


def validar_pcfg(gram=None) -> bool:
    """
    Verifica que la PCFG sea formalmente válida:
    para cada no-terminal, las probabilidades de sus producciones suman 1.

    Lanza ValueError si algún no-terminal no cumple.
    """
    if gram is None:
        gram = gramatica_pcfg

    for lhs, producciones in gram.items():
        total = sum(prob for _, prob in producciones)
        if abs(total - 1.0) > TOLERANCIA:
            raise ValueError(
                f"PCFG mal formada: las probabilidades de '{lhs}' suman {total:.6f}, "
                f"no 1.0. Producciones: {producciones}"
            )
    return True


def probabilidad_regla(lhs: str, rhs: list, gram=None) -> float:
    """
    Devuelve P(lhs → rhs). Si la regla no existe, devuelve 0.0.

    Ejemplo:
        probabilidad_regla('Cuarteto', ['A', 'B', 'A', 'B'])  -> 0.40
        probabilidad_regla('Cuarteto', ['X', 'Y'])            -> 0.0
    """
    if gram is None:
        gram = gramatica_pcfg

    rhs_tuple = tuple(rhs)
    for produccion, prob in gram.get(lhs, []):
        if tuple(produccion) == rhs_tuple:
            return prob
    return 0.0


def descripcion_formal_pcfg(gram=None) -> str:
    """Devuelve la PCFG formal como texto con cada producción y su probabilidad."""
    if gram is None:
        gram = gramatica_pcfg

    no_term = set(gram.keys())
    term    = set()
    for prods in gram.values():
        for rhs, _ in prods:
            for s in rhs:
                if s not in gram:
                    term.add(s)

    salida  = "G_p = (V, T, P, S, ρ)\n\n"
    salida += f"  V = {{ {', '.join(sorted(no_term))} }}\n"
    salida += f"  T = {{ {', '.join(sorted(term))} }}\n"
    salida += f"  S = Estrofa\n\n"
    salida += "  P  (con ρ entre corchetes):\n"
    for lhs, producciones in gram.items():
        for rhs, prob in producciones:
            salida += f"    {lhs:14s} → {' '.join(rhs):20s}  [{prob:.2f}]\n"
    return salida


# Validar al cargar el módulo: si las probabilidades están mal, falla rápido.
validar_pcfg()
