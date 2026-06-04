"""
DCG + Unificación de rimas — Fase 5.

Cierra el agujero que deja la CFG de la Fase 3.

El problema
-----------
La CFG (Fase 3) razona sobre el patrón SIMBÓLICO de rima: ve la cadena
['A','A','A','A'] y dice "esto es un cuarteto monorrimo AAAA". Pero las
etiquetas A, B, ... son solo símbolos: la CFG nunca comprueba que las
palabras finales de los versos rimen DE VERDAD entre sí.

    Patrón AAAA propuesto por la CFG:
        andar / hogar / cantar / soñar   → las 4 terminan en 'ar' → OK
        andar / hogar / amor   / pared   → NO riman               → debería fallar

La Fase 5 añade esa verificación usando UNIFICACIÓN, el mismo mecanismo
de la clase 7 (DCG). Allí se verificaba concordancia de género/número
("la libro" fallaba). Aquí verificamos concordancia de TERMINACIÓN RÍMICA.

La idea de la DCG
-----------------
Cada etiqueta de rima A, B, C... es una VARIABLE LÓGICA. A medida que
recorremos los versos:

    - La primera vez que vemos la etiqueta 'A', la LIGAMOS a la terminación
      real del verso (p. ej. 'A' = 'ar').
    - Cada vez que 'A' reaparece, su terminación debe UNIFICAR con la que
      ya tiene ligada. Si no unifica, el esquema es inconsistente.

Esto es justo lo que en la clase 7 hacía:
    {gen: X} unificado con {gen: masc}  → X queda ligada a masc.
Aquí:
    A = (libre)  unificado con 'ar'     → A queda ligada a 'ar'.
    A = 'ar'     unificado con 'or'      → conflicto → None → rechaza.

Reutiliza el extractor de la Fase 3 (`terminacion_consonante` /
`terminacion_asonante`) para obtener la terminación real de cada palabra.
"""

from __future__ import annotations

from src.rima import terminacion_consonante, terminacion_asonante, palabra_final


# --------------------------------------------------------------------------- #
# 1. Unificación de una variable de rima con una terminación
# --------------------------------------------------------------------------- #
def unificar_rima(ligaduras, etiqueta, terminacion):
    """
    Intenta unificar la VARIABLE de rima `etiqueta` (p. ej. 'A') con la
    `terminacion` real observada (p. ej. 'ar'), dado el diccionario de
    `ligaduras` acumuladas hasta ahora.

    Es el equivalente al `unificar(dag1, dag2)` de la clase 7, pero sobre
    una sola variable:

        - Si la etiqueta NO está ligada todavía → se liga a la terminación
          (como agregar un rasgo nuevo).
        - Si YA está ligada al MISMO valor → no hay conflicto, continúa.
        - Si está ligada a un valor DISTINTO → conflicto, retorna None.

    Retorna el nuevo diccionario de ligaduras, o None si hay conflicto.
    No modifica el diccionario original (trabaja sobre una copia).
    """
    nuevas = dict(ligaduras)

    if etiqueta not in nuevas:
        # Variable libre: la ligamos por primera vez.
        nuevas[etiqueta] = terminacion
        return nuevas

    # Variable ya ligada: debe coincidir.
    if nuevas[etiqueta] == terminacion:
        return nuevas

    # Conflicto: la misma etiqueta exige dos terminaciones distintas.
    return None


# --------------------------------------------------------------------------- #
# 2. Verificación de un esquema completo contra los versos reales
# --------------------------------------------------------------------------- #
def verificar_esquema(etiquetas, versos, modo="consonante", detalle=False):
    """
    Verifica que el esquema simbólico `etiquetas` (p. ej. ['A','A','A','A'])
    sea consistente con las rimas REALES de `versos`.

    Parámetros
    ----------
    etiquetas : lista de etiquetas de rima, una por verso (de la Fase 3).
    versos    : lista de versos; cada verso es una lista de palabras.
    modo      : 'consonante' o 'asonante'.
    detalle   : si True, devuelve también la traza de la verificación.

    Funcionamiento
    --------------
    Recorre verso por verso. Para cada uno:
        1. Extrae la terminación real de su última palabra.
        2. Intenta unificar la etiqueta de ese verso con esa terminación.
        3. Si la unificación falla → el esquema es INCONSISTENTE.

    Además exige que DOS etiquetas DISTINTAS tengan terminaciones distintas
    (si 'A' y 'B' acabaran ligadas a 'ar', el esquema diría que riman cosas
    que en realidad son la misma rima → se reporta como inconsistencia).

    Retorna
    -------
    Si detalle=False: True/False (¿el esquema es consistente?).
    Si detalle=True : un dict con 'valido', 'ligaduras', 'traza' y 'motivo'.
    """
    extraer = terminacion_consonante if modo == "consonante" else terminacion_asonante

    ligaduras = {}     # etiqueta -> terminación real
    traza     = []     # registro paso a paso para la demo

    for etiqueta, palabras in zip(etiquetas, versos):
        ultima = palabra_final(palabras)
        term   = extraer(ultima)

        resultado = unificar_rima(ligaduras, etiqueta, term)

        if resultado is None:
            # Conflicto: esta etiqueta ya estaba ligada a otra terminación.
            traza.append(
                f"✗ '{ultima}' (-{term}) debía rimar como [{etiqueta}]"
                f" = -{ligaduras[etiqueta]}  → NO unifica"
            )
            if detalle:
                return {
                    "valido": False,
                    "ligaduras": ligaduras,
                    "traza": traza,
                    "motivo": (f"El verso que termina en '{ultima}' no rima con "
                               f"los anteriores marcados [{etiqueta}]."),
                }
            return False

        ligaduras = resultado
        traza.append(f"✓ '{ultima}' (-{term})  ligado a  [{etiqueta}]")

    # Chequeo extra: dos etiquetas distintas no pueden tener la misma rima.
    invertido = {}
    for etiqueta, term in ligaduras.items():
        if term in invertido and invertido[term] != etiqueta:
            motivo = (f"Las rimas [{invertido[term]}] y [{etiqueta}] son distintas "
                      f"en el esquema pero ambas terminan en '-{term}'.")
            traza.append("✗ " + motivo)
            if detalle:
                return {"valido": False, "ligaduras": ligaduras,
                        "traza": traza, "motivo": motivo}
            return False
        invertido[term] = etiqueta

    if detalle:
        return {"valido": True, "ligaduras": ligaduras,
                "traza": traza, "motivo": "Todas las rimas son consistentes."}
    return True


# --------------------------------------------------------------------------- #
# 3. Filtrado de árboles: descarta los que la DCG considera inconsistentes
# --------------------------------------------------------------------------- #
def filtrar_arboles_validos(arboles, versos, modo="consonante"):
    """
    Dada la lista de árboles que produjo la CFG (Fase 3), conserva solo
    aquellos cuyo esquema de rima es CONSISTENTE con los versos reales.

    Para leer el esquema de cada árbol se usan sus hojas (las etiquetas de
    rima en orden), que es justo lo que `Nodo.hojas()` devuelve.

    Retorna la lista de árboles que sobreviven a la verificación DCG.
    """
    validos = []
    for arbol in arboles:
        etiquetas = arbol.hojas()
        if verificar_esquema(etiquetas, versos, modo):
            validos.append(arbol)
    return validos
