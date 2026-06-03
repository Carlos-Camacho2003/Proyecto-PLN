"""
Parser recursivo descendente — Fase 3.

Construye el árbol de derivación de una secuencia de etiquetas de rima
(['A','A','B','B'], ['A','B','A','B'], ...) según la CFG definida en
`gramatica.py`.

Hay DOS funciones de análisis:

  * `parse(...)`        retorna el PRIMER árbol válido que encuentra.
                        Sirve para análisis rápido y para mostrar una
                        derivación canónica.

  * `parse_todos(...)`  retorna TODOS los árboles válidos.
                        Es la pieza clave para la **detección de
                        ambigüedad estructural**: cuando la lista tiene
                        más de un árbol, el sistema avisa que el
                        fragmento puede leerse de varias maneras
                        (por ejemplo cuarteto AABB vs. dos pareados AA-AA).

 adaptada al dominio del proyecto:

    - Si el símbolo NO está en la gramática, es un terminal: se compara
      directamente con el token actual (la etiqueta de rima).
    - Si el símbolo SÍ está en la gramática, se prueba cada producción
      hasta encontrar una que reconozca el resto de la entrada.
"""

from __future__ import annotations

from .nodo import Nodo


# --------------------------------------------------------------------------- #
# parse — devuelve el PRIMER árbol válido 
# --------------------------------------------------------------------------- #
def parse(simbolo, tokens, pos, gramatica):
    """
    Análisis recursivo descendente.

    simbolo    : símbolo actual a analizar (no-terminal o terminal).
    tokens     : lista de etiquetas de rima ['A','A','B','B'].
    pos        : posición actual dentro de `tokens`.
    gramatica  : el diccionario de producciones.

    Retorna (nodo, nueva_pos) si tuvo éxito, o (None, pos) si falló.
    """
    # Caso terminal: el símbolo no aparece como clave en la gramática.
    # Comparamos con el token actual.
    if simbolo not in gramatica:
        if pos < len(tokens) and tokens[pos] == simbolo:
            return tokens[pos], pos + 1
        return None, pos

    # Caso no-terminal: probamos cada producción en orden.
    for produccion in gramatica[simbolo]:
        nodo_actual = Nodo(simbolo)
        pos_actual  = pos
        exito       = True

        # Intentamos reconocer cada sub-símbolo de la producción.
        for subsimbolo in produccion:
            hijo, pos_actual = parse(subsimbolo, tokens,
                                     pos_actual, gramatica)
            if hijo is None:
                exito = False
                break
            nodo_actual.hijos.append(hijo)

        # Si toda la producción cuadró, devolvemos este nodo.
        if exito:
            return nodo_actual, pos_actual

    # Ninguna producción funcionó.
    return None, pos


# --------------------------------------------------------------------------- #
# parse_todos — devuelve TODOS los árboles válidos esto para ambigüedad)
# --------------------------------------------------------------------------- #
def parse_todos(simbolo, tokens, pos, gramatica):
    """
    Versión exhaustiva: en lugar de retornar el primer árbol, retorna
    TODOS los análisis posibles del símbolo desde la posición `pos`.

    Retorna una lista de tuplas (nodo, nueva_pos). Si la lista tiene más
    de un elemento, hay ambigüedad estructural.

    Es exactamente el `parse_todos` que aparece en las diapositivas de
    la clase 6, adaptado a este dominio.
    """
    # Caso terminal — igual que en parse.
    if simbolo not in gramatica:
        if pos < len(tokens) and tokens[pos] == simbolo:
            return [(tokens[pos], pos + 1)]
        return []

    resultados = []

    # Caso no-terminal: para cada producción, exploramos TODAS las
    # combinaciones posibles de derivaciones de sus sub-símbolos.
    for produccion in gramatica[simbolo]:
        # `candidatos` es la lista de (hijos_parciales, posicion) que
        # vamos acumulando a medida que avanzamos por la producción.
        candidatos = [([], pos)]

        for subsimbolo in produccion:
            nuevos = []
            for hijos, p in candidatos:
                # Cada subanálisis puede dar varios resultados:
                # los acumulamos todos sin descartar ninguno.
                for hijo, p2 in parse_todos(subsimbolo, tokens, p, gramatica):
                    nuevos.append((hijos + [hijo], p2))
            candidatos = nuevos
            if not candidatos:
                break

        # Cada candidato exitoso produce un nuevo nodo.
        for hijos, p_final in candidatos:
            resultados.append((Nodo(simbolo, hijos), p_final))

    return resultados


# --------------------------------------------------------------------------- #
# Funciones de alto nivel — son las que usará main.py
# --------------------------------------------------------------------------- #
def analizar(tokens, gramatica, simbolo_inicial: str = "Estrofa"):
    """
    Analiza una secuencia completa de etiquetas de rima.

    Retorna el árbol si toda la entrada fue reconocida, o None.
    """
    arbol, pos_final = parse(simbolo_inicial, tokens, 0, gramatica)
    if arbol is not None and pos_final == len(tokens):
        return arbol
    return None


def analizar_todos(tokens, gramatica, simbolo_inicial: str = "Estrofa"):
    """
    Versión que retorna TODOS los análisis posibles.
    Solo conserva los que consumen la entrada completa.

    Si retorna más de un árbol → la entrada es estructuralmente ambigua.
    """
    candidatos = parse_todos(simbolo_inicial, tokens, 0, gramatica)
    return [arbol for arbol, pos in candidatos if pos == len(tokens)]


def analizar_con_fallback(tokens, gram_clasica, gram_con_libre):
    """
    Estrategia de dos pasos:

    1. Intenta primero con la gramática CLÁSICA (cuarteto, terceto, pareado,
       dos pareados). Si reconoce el fragmento → devuelve todos los árboles
       clásicos. Si hay más de uno → ambigüedad estructural real.

    2. Si la clásica no reconoce nada, recurre a la gramática con
       EstrofaLibre. Esto captura fragmentos sin patrón rítmico.

    Retorna: (lista_de_arboles, modo)
        modo ∈ {'clasica', 'libre', 'rechazada'}
    """
    clasicos = analizar_todos(tokens, gram_clasica)
    if clasicos:
        return clasicos, 'clasica'

    libres = analizar_todos(tokens, gram_con_libre)
    if libres:
        return libres, 'libre'

    return [], 'rechazada'


# --------------------------------------------------------------------------- #
# Identificador legible del esquema reconocido
# --------------------------------------------------------------------------- #
def nombre_esquema(arbol) -> str:
    """
    Devuelve un nombre amigable para el esquema detectado, leyendo la
    raíz del árbol. Útil para reportar al usuario.

    Ejemplos:
        'Cuarteto AABB'
        'Cuarteto ABAB'
        'Pareado'
        'Terceto AAA'
        'Estrofa libre'
    """
    if arbol is None:
        return "(no reconocida)"

    raiz = arbol.etiqueta
    hojas = arbol.hojas()

    if raiz == "Estrofa" and arbol.hijos and isinstance(arbol.hijos[0], Nodo):
        # Bajamos al primer hijo para identificar la forma concreta.
        return nombre_esquema(arbol.hijos[0])

    if raiz == "Cuarteto":
        return f"Cuarteto {''.join(hojas)}"
    if raiz == "Terceto":
        return f"Terceto {''.join(hojas)}"
    if raiz == "Pareado":
        return f"Pareado {''.join(hojas)}"
    if raiz == "DosPareados":
        return f"Dos pareados ({''.join(hojas)})"
    if raiz == "EstrofaLibre":
        return f"Estrofa libre ({''.join(hojas)})"

    return raiz
