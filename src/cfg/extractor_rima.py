"""
Extractor de rima — Fase 3.

Convierte una lista de versos (en forma de palabras) en la **secuencia
simbólica de rimas** que alimenta al parser CFG.

Idea
----
La CFG no analiza palabras, analiza esquemas de rima. Para alimentarla,
cada verso se reduce a una etiqueta simbólica:

    "Llevo el barrio en la sangre, lo respiro al andar"  → "ar"  → A
    "cada esquina me canta, cada calle es mi hogar"      → "ar"  → A
    "se quema mi corazón"                                → "on"  → B
    "no te encuentro en la razón"                        → "on"  → B

Resultado para esos cuatro versos: ['A', 'A', 'B', 'B'].
Esa secuencia es la entrada del parser.

Pasos
-----
1. Tomar la última palabra del verso.
2. Extraer su terminación rímica desde la vocal tónica (no toda la palabra).
   Para esto reutilizamos el silabeador de la Fase 2.
3. Asignar a esa terminación una etiqueta simbólica A, B, C... según
   el orden en que aparece por primera vez en la estrofa.

Tipos de rima soportados
------------------------
- **Consonante**: coinciden vocales y consonantes desde la tónica
                  (andar / hogar  → ambas terminan en 'ar').
- **Asonante**:   coinciden solo las vocales desde la tónica
                  (sangre / calle  → 'a-e' / 'a-e').

Esta clasificación se hace en `clasificar_rima()` y se pasa después a la
Fase 4 (DCG + unificación), que verifica formalmente la compatibilidad
de terminaciones. Aquí solo necesitamos las **etiquetas simbólicas**.
"""

from __future__ import annotations

# El silabeador se importa de forma diferida (dentro de las funciones que
# lo usan) para que `src.cfg` siga siendo importable 


VOCALES = set("aeiouáéíóúü")


# --------------------------------------------------------------------------- #
# Paso 1: extraer la terminación rímica de una palabra
# --------------------------------------------------------------------------- #
def terminacion_consonante(palabra: str) -> str:
    """
    Devuelve la terminación CONSONANTE de la palabra: todo lo que va
    desde la vocal de la sílaba tónica hasta el final, sin tilde.

    Ejemplos:
        andar    -> 'ar'
        hogar    -> 'ar'
        corazón  -> 'on'
        sílaba   -> 'ilaba'
        canta    -> 'anta'   (llana: tónica es la penúltima)
    """
    from src.silabeo import silabas, tonicidad

    sil = silabas(palabra)
    if not sil:
        return ""

    clase, pos_desde_final = tonicidad(palabra)
    # Índice de la sílaba tónica dentro de la lista.
    idx_tonica = len(sil) - pos_desde_final

    # Concatena desde la tónica hasta el final.
    cola = "".join(sil[idx_tonica:])

    # Recorta al primer núcleo vocálico de esa cola y conserva lo que sigue.
    i = 0
    while i < len(cola) and cola[i] not in VOCALES:
        i += 1
    cola = cola[i:]

    # Normalización: minúsculas y sin tilde.
    return _sin_tilde(cola.lower())


def terminacion_asonante(palabra: str) -> str:
    """
    Devuelve la terminación ASONANTE: solo las vocales desde la tónica.

    Ejemplos:
        andar    -> 'a'
        sangre   -> 'ae'
        canta    -> 'aa'
        corazón  -> 'o'
        sílaba   -> 'iaa'
    """
    cons = terminacion_consonante(palabra)
    return "".join(c for c in cons if c in VOCALES)


def _sin_tilde(s: str) -> str:
    """Quita tildes manteniendo ñ."""
    tabla = str.maketrans("áéíóúü", "aeiouu")
    return s.translate(tabla)


# --------------------------------------------------------------------------- #
# Paso 2: extraer la última palabra significativa de un verso
# --------------------------------------------------------------------------- #
def palabra_final(palabras_verso) -> str:
    """De la lista de palabras de un verso, devuelve la última que tiene
    al menos una letra alfabética."""
    for palabra in reversed(palabras_verso):
        if any(c.isalpha() for c in palabra):
            return palabra
    return ""


# --------------------------------------------------------------------------- #
# Paso 3: clasificar la rima de toda la estrofa
# --------------------------------------------------------------------------- #
def secuencia_rimas(versos, modo: str = "consonante"):
    """
    Convierte una lista de versos (cada verso = lista de palabras) en la
    secuencia simbólica de etiquetas de rima.

    Parámetros
    ----------
    versos : lista de listas de palabras.
    modo   : 'consonante' o 'asonante'.

    Retorna
    -------
    (etiquetas, mapa) donde:
        etiquetas = ['A', 'A', 'B', 'B']
        mapa      = {'A': 'ar', 'B': 'on'}   ← qué terminación es cada letra

    La etiqueta se asigna por orden de aparición: la primera terminación
    distinta es A, la segunda B, etc. Esto es exactamente lo que se hace
    en la métrica clásica para anotar esquemas.
    """
    if modo not in ("consonante", "asonante"):
        raise ValueError("modo debe ser 'consonante' o 'asonante'")

    extraer = terminacion_consonante if modo == "consonante" else terminacion_asonante

    etiquetas = []
    mapa      = {}                # terminación -> etiqueta
    inverso   = {}                # etiqueta -> terminación

    siguiente_letra = ord('A')
    for palabras in versos:
        ultima = palabra_final(palabras)
        term   = extraer(ultima)

        if term not in mapa:
            letra = chr(siguiente_letra)
            mapa[term] = letra
            inverso[letra] = term
            siguiente_letra += 1

        etiquetas.append(mapa[term])

    return etiquetas, inverso


# --------------------------------------------------------------------------- #
# Utilidad: mostrar el esquema de rima de forma legible
# --------------------------------------------------------------------------- #
def describir_esquema(etiquetas, mapa) -> str:
    """
    Genera una descripción legible del esquema detectado.

    Ejemplo
        etiquetas = ['A','A','B','B']
        mapa      = {'A':'ar','B':'on'}
        -> "Esquema AABB:  A='-ar'  B='-on'"
    """
    if not etiquetas:
        return "(sin versos)"
    esquema = "".join(etiquetas)
    detalle = "  ".join(f"{letra}='-{term}'" for letra, term in mapa.items())
    return f"Esquema {esquema}:  {detalle}"
