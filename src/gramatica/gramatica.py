"""
Gramática de Contexto Libre (CFG) — Fase 3.

Esta es la **gramática central del proyecto**, definida como una 4-tupla
formal G = (V, T, P, S) donde:

    V = símbolos no-terminales (Estrofa, Cuarteto, Pareado, Terceto, Verso)
    T = símbolos terminales    (etiquetas simbólicas de rima: A, B, C, D, E)
    P = conjunto de producciones (el diccionario `gramatica`)
    S = símbolo inicial         ('Estrofa')

La gramática NO recibe palabras: recibe la **secuencia simbólica de rimas**
que produce `extractor_rima.secuencia_rimas`. Por ejemplo, los cuatro
versos del enunciado del proyecto:

    "Llevo el barrio en la sangre, lo respiro al andar"  → A
    "cada esquina me canta, cada calle es mi hogar"      → A
    "se quema mi corazón cuando me dices que no"         → B
    "no encuentro paz ni razón, todo es un eco veloz"    → B

se transforman en la cadena ['A','A','B','B'], y la CFG la analiza.

Esquemas métricos cubiertos
---------------------------
- Pareado          AA, BB, ...
- Terceto monorrimo / encadenado     AAA, ABA
- Cuarteto         AABB, ABAB, ABBA, AAAA
- Quintilla        ABABB, etc. (extensible)
- Estrofa libre    secuencia de versos sin restricción rítmica

La gramática es **deliberadamente ambigua** en casos como ['A','A','B','B']:
puede analizarse como un cuarteto AABB o como dos pareados (AA)(BB).
Esa ambigüedad es uno de los puntos centrales del proyecto y se manejará
en la Fase 5 con la PCFG.
"""

from __future__ import annotations


# --------------------------------------------------------------------------- #
# Producciones P de la gramática
# --------------------------------------------------------------------------- #
# Cada clave es un no-terminal de V.
# Cada lista interna es una producción (lado derecho de la regla).
# Los símbolos de una letra mayúscula al final del alfabeto (A..E) son
# los terminales de T — las etiquetas de rima que entrega el extractor.
#
# La gramática es DELIBERADAMENTE AMBIGUA en algunos casos: por ejemplo,
# ['A','A','B','B'] puede derivarse como `Cuarteto → A A B B` o como
# `DosPareados → Pareado Pareado`. 
# --------------------------------------------------------------- #
gramatica = {

    # --------------------------------------------------------------- #
    # Símbolo inicial S = Estrofa.
    # El orden importa: las formas clásicas se prueban primero.
    # `EstrofaLibre` se deja FUERA de las producciones de Estrofa, en
    # una gramática extendida (ver `gramatica_con_libre` más abajo) que
    # se usa solo como fallback cuando ninguna forma clásica encaja.
    # --------------------------------------------------------------- #
    'Estrofa': [
        ['Cuarteto'],
        ['DosPareados'],   # <-- la "otra lectura" que compite con el cuarteto
        ['Pareado'],
        ['Terceto'],
    ],

    # --------------------------------------------------------------- #
    # CUARTETOS — cuatro versos con un esquema fijo de rima.
    #   AABB : dos pareados pegados (ambiguo con DosPareados)
    #   ABAB : rima cruzada
    #   ABBA : rima abrazada
    #   AAAA : monorrimo (ambiguo con dos pareados AA + AA)
    # --------------------------------------------------------------- #
    'Cuarteto': [
        ['A', 'A', 'B', 'B'],
        ['A', 'B', 'A', 'B'],
        ['A', 'B', 'B', 'A'],
        ['A', 'A', 'A', 'A'],
    ],

    # --------------------------------------------------------------- #
    # DOS PAREADOS — alternativa al cuarteto.
    # Cuando entran 4 versos con esquema xxyy o xxxx, el parser también
    # los puede analizar como dos pareados pegados. Esa es la AMBIGÜEDAD
    # estructural central del proyecto.
    # --------------------------------------------------------------- #
    'DosPareados': [
        ['Pareado', 'Pareado'],
    ],

    # --------------------------------------------------------------- #
    # TERCETOS — tres versos.
    # --------------------------------------------------------------- #
    'Terceto': [
        ['A', 'A', 'A'],
        ['A', 'B', 'A'],
    ],

    # --------------------------------------------------------------- #
    # PAREADO — dos versos que riman entre sí.
    # Se expande en todas las letras posibles para que el parser
    # reconozca pareados B-B, C-C, ... y no solo A-A.
    # --------------------------------------------------------------- #
    'Pareado': [
        ['A', 'A'],
        ['B', 'B'],
        ['C', 'C'],
        ['D', 'D'],
        ['E', 'E'],
    ],
}


# --------------------------------------------------------------------------- #
# Gramática extendida con `EstrofaLibre` — solo se usa como FALLBACK
# cuando la gramática clásica de arriba no reconoce el fragmento.
# Modela versos sin patrón rítmico claro (común en trap y reggaetón).
# --------------------------------------------------------------------------- #
gramatica_con_libre = {
    **gramatica,
    'Estrofa': gramatica['Estrofa'] + [['EstrofaLibre']],
    'EstrofaLibre': [
        ['Verso', 'EstrofaLibre'],
        ['Verso'],
    ],
    'Verso': [[letra] for letra in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'],
}


# --------------------------------------------------------------------------- #
# Conjuntos formales de la 4-tupla — útiles.
# y para mostrar G = (V, T, P, S)
# --------------------------------------------------------------------------- #
NO_TERMINALES   = set(gramatica.keys())                                 # V
TERMINALES      = {'A', 'B', 'C', 'D', 'E'}                             # T
SIMBOLO_INICIAL = 'Estrofa'                                             # S


def descripcion_formal(gram=None) -> str:
    """Devuelve la 4-tupla formal
     (entregable 5.2). Por defecto usa la gramática clásica."""
    if gram is None:
        gram = gramatica
    no_term = set(gram.keys())
    term    = set()
    for prods in gram.values():
        for rhs in prods:
            for s in rhs:
                if s not in gram:
                    term.add(s)

    salida  = "G = (V, T, P, S)\n\n"
    salida += f"  V = {{ {', '.join(sorted(no_term))} }}\n"
    salida += f"  T = {{ {', '.join(sorted(term))} }}\n"
    salida += f"  S = {SIMBOLO_INICIAL}\n\n"
    salida += "  P:\n"
    for lhs, producciones in gram.items():
        for rhs in producciones:
            salida += f"    {lhs:14s} → {' '.join(rhs)}\n"
    return salida
