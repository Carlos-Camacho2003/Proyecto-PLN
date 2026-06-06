"""
Parser tipo Chart (algoritmo de Earley) — construido desde cero.

Analiza una secuencia de etiquetas de rima (['A','A','B','B'],
['A','B','A','B'], ...) contra la CFG definida en `gramatica.py` y construye
su(s) árbol(es) de derivación. Es el núcleo del análisis estructural.

¿Por qué Earley y no recursivo descendente?
-------------------------------------------
- Es un parser de tipo **Chart**: tabula análisis parciales por posición, así
  que nunca rehace el mismo subanálisis (a diferencia del recursivo descendente
  con retroceso).
- Maneja la **ambigüedad de forma nativa**: si una entrada tiene varias
  derivaciones (cuarteto AABB vs. dos pareados AA-AA), el chart las contiene
  todas y `analizar_todos` las reconstruye.
- Acepta gramáticas arbitrarias sin restricciones de recursión por la izquierda.

El algoritmo en una frase
-------------------------
Para cada posición i de la entrada se mantiene un conjunto de "items"
(producciones a medio reconocer). Tres operaciones los hacen crecer:

    PREDICT   : ante  A → α•Bβ  se agregan las producciones de B en la posición i.
    SCAN      : ante  A → α•aβ  si el token i es 'a', se avanza el punto a i+1.
    COMPLETE  : ante  B → γ•    (B terminado en i, iniciado en j) se avanzan en j
                todos los items que esperaban una B.

Un item se representa como la tupla   (lhs, rhs, punto, origen).
"""

from __future__ import annotations

from .nodo import Nodo


# --------------------------------------------------------------------------- #
# 1. Construcción del chart (reconocedor de Earley)
# --------------------------------------------------------------------------- #
def construir_chart(tokens, gramatica, simbolo_inicial="Estrofa"):
    """
    Ejecuta el algoritmo de Earley sobre `tokens` y devuelve el chart:
    una lista de `len(tokens) + 1` conjuntos de items.

    Cada item es la tupla (lhs, rhs, punto, origen):
        lhs    : no-terminal del lado izquierdo.
        rhs    : tupla con el lado derecho de la producción.
        punto  : cuántos símbolos de `rhs` ya se reconocieron.
        origen : posición de la entrada donde empezó este item.
    """
    n = len(tokens)
    chart = [[] for _ in range(n + 1)]
    vistos = [set() for _ in range(n + 1)]

    def agregar(i, item):
        """Inserta un item en el conjunto i evitando duplicados."""
        if item not in vistos[i]:
            vistos[i].add(item)
            chart[i].append(item)

    # Sembrado: todas las producciones del símbolo inicial, en la posición 0.
    for produccion in gramatica.get(simbolo_inicial, []):
        agregar(0, (simbolo_inicial, tuple(produccion), 0, 0))

    # Recorremos cada posición; el conjunto puede crecer mientras lo recorremos.
    for i in range(n + 1):
        k = 0
        while k < len(chart[i]):
            lhs, rhs, punto, origen = chart[i][k]
            k += 1

            if punto < len(rhs):
                simbolo = rhs[punto]
                if simbolo in gramatica:
                    # PREDICT: el siguiente símbolo es no-terminal.
                    for produccion in gramatica[simbolo]:
                        agregar(i, (simbolo, tuple(produccion), 0, i))
                else:
                    # SCAN: el siguiente símbolo es terminal (etiqueta de rima).
                    if i < n and tokens[i] == simbolo:
                        agregar(i + 1, (lhs, rhs, punto + 1, origen))
            else:
                # COMPLETE: `lhs` quedó reconocido en [origen, i].
                # Avanzamos en `origen` todo item que esperaba un `lhs`.
                for (p_lhs, p_rhs, p_punto, p_org) in list(chart[origen]):
                    if p_punto < len(p_rhs) and p_rhs[p_punto] == lhs:
                        agregar(i, (p_lhs, p_rhs, p_punto + 1, p_org))

    return chart


# --------------------------------------------------------------------------- #
# 2. Reconstrucción del bosque de derivaciones a partir del chart
# --------------------------------------------------------------------------- #
def _completados_por_span(chart):
    """
    Indexa los items completados del chart por (lhs, inicio, fin) → lista de rhs.

    Un item (lhs, rhs, len(rhs), origen) en el conjunto `fin` significa que
    `lhs` se reconoció abarcando la entrada [origen, fin] usando `rhs`.
    """
    completados = {}
    for fin, items in enumerate(chart):
        for (lhs, rhs, punto, origen) in items:
            if punto == len(rhs):                       # item terminado
                completados.setdefault((lhs, origen, fin), []).append(rhs)
    return completados


def _construir_arboles(simbolo, i, j, tokens, gramatica, completados, memo):
    """
    Devuelve TODOS los árboles del `simbolo` que abarcan exactamente [i, j).

    - Terminal: hoja válida solo si consume justo el token en la posición i.
    - No-terminal: por cada producción reconocida en ese span, se exploran
      todas las particiones de sus sub-símbolos (de ahí la ambigüedad).
    """
    if simbolo not in gramatica:
        # Terminal: debe coincidir con un único token.
        if j == i + 1 and tokens[i] == simbolo:
            return [tokens[i]]
        return []

    clave = (simbolo, i, j)
    if clave in memo:
        return memo[clave]
    memo[clave] = []                                    # corta recursión cíclica

    arboles = []
    for rhs in completados.get(clave, []):
        for hijos in _particionar(rhs, 0, i, j, tokens,
                                   gramatica, completados, memo):
            arboles.append(Nodo(simbolo, hijos))

    memo[clave] = arboles
    return arboles


def _particionar(rhs, idx, i, j, tokens, gramatica, completados, memo):
    """
    Genera todas las formas de repartir el span [i, j) entre los símbolos
    rhs[idx:], devolviendo listas de árboles hijos.
    """
    # Caso base: ya colocamos todos los símbolos; válido si cubrimos [i, j).
    if idx == len(rhs):
        return [[]] if i == j else []

    simbolo = rhs[idx]
    es_ultimo = (idx == len(rhs) - 1)
    resultados = []

    # Posibles posiciones de corte para este símbolo: span [i, k).
    if simbolo not in gramatica:
        cortes = [i + 1] if (i < j and tokens[i] == simbolo) else []
    else:
        cortes = [k for k in range(i, j + 1)
                  if (simbolo, i, k) in completados]

    for k in cortes:
        if es_ultimo and k != j:
            continue                                    # el último debe cerrar en j
        if k > j:
            continue
        subarboles = _construir_arboles(simbolo, i, k, tokens,
                                        gramatica, completados, memo)
        if not subarboles:
            continue
        for resto in _particionar(rhs, idx + 1, k, j, tokens,
                                   gramatica, completados, memo):
            for sub in subarboles:
                resultados.append([sub] + resto)

    return resultados


# --------------------------------------------------------------------------- #
# 3. Funciones de alto nivel — las que usan main.py y los tests
# --------------------------------------------------------------------------- #
def analizar_todos(tokens, gramatica, simbolo_inicial="Estrofa"):
    """
    Devuelve TODOS los árboles de derivación que reconocen la entrada completa.

    Si la lista tiene más de un árbol → la entrada es estructuralmente ambigua.
    """
    tokens = list(tokens)
    chart = construir_chart(tokens, gramatica, simbolo_inicial)
    completados = _completados_por_span(chart)
    return _construir_arboles(simbolo_inicial, 0, len(tokens),
                              tokens, gramatica, completados, memo={})


def analizar(tokens, gramatica, simbolo_inicial="Estrofa"):
    """Devuelve el PRIMER árbol válido, o None si la entrada no se reconoce."""
    arboles = analizar_todos(tokens, gramatica, simbolo_inicial)
    return arboles[0] if arboles else None


def analizar_con_fallback(tokens, gram_clasica, gram_con_libre):
    """
    Estrategia de dos pasos:

    1. Intenta con la gramática CLÁSICA (cuarteto, terceto, pareado, dos
       pareados). Si reconoce → devuelve todos los árboles clásicos; si hay
       más de uno → ambigüedad estructural real.
    2. Si la clásica no reconoce nada, recurre a la gramática con EstrofaLibre
       para capturar fragmentos sin patrón rítmico.

    Retorna (lista_de_arboles, modo) con modo ∈ {'clasica', 'libre', 'rechazada'}.
    """
    clasicos = analizar_todos(tokens, gram_clasica)
    if clasicos:
        return clasicos, "clasica"

    libres = analizar_todos(tokens, gram_con_libre)
    if libres:
        return libres, "libre"

    return [], "rechazada"


# --------------------------------------------------------------------------- #
# 4. Identificador legible del esquema reconocido
# --------------------------------------------------------------------------- #
def nombre_esquema(arbol) -> str:
    """
    Devuelve un nombre amigable para el esquema detectado, leyendo la raíz
    del árbol de derivación.

    Ejemplos: 'Cuarteto AABB', 'Pareado AA', 'Terceto AAA', 'Estrofa libre (ABC)'.
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
