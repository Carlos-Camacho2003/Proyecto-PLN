"""
Silabeador del español — construido desde cero (Fase 2).

Divide una palabra en sílabas aplicando las reglas ortográficas del español:

  * Dígrafos inseparables que cuentan como UNA consonante: ch, ll, rr.
  * 'qu' y 'gu' (ante e/i) llevan una 'u' muda -> se tratan como una consonante.
  * Diptongos / triptongos vs. hiatos (vocales abiertas/cerradas, acento).
  * Distribución de consonantes entre núcleos (ataque máximo y grupos
    inseparables consonante + l/r: pr, bl, tr, gr, ...).

Sobre esta base se añade el **conteo métrico de un verso**, que es lo que
necesita el análisis de la letra:

  * sinalefa: si una palabra termina en vocal y la siguiente empieza por vocal
    (o 'h' muda + vocal), ambas sílabas se cuentan como una sola;
  * ajuste por acento de la última palabra del verso:
        aguda  -> +1     llana -> 0     esdrújula -> -1.

Ejemplo (alejandrino):
    "Llevo el barrio en la sangre, lo respiro al andar"  -> 14 sílabas métricas.
"""

from __future__ import annotations

import unicodedata

# --------------------------------------------------------------------------- #
# Conjuntos de vocales
# --------------------------------------------------------------------------- #
VOCALES_FUERTES = set("aeoáéó")        # abiertas (incl. acentuadas)
VOCALES_DEBILES = set("iuü")           # cerradas átonas
VOCALES_DEBILES_ACENT = set("íú")      # cerradas tónicas (rompen diptongo)
VOCALES = VOCALES_FUERTES | VOCALES_DEBILES | VOCALES_DEBILES_ACENT

VOCALES_ACENTUADAS = set("áéíóú")

# Grupos consonánticos inseparables (consonante + l/r).
GRUPOS_INSEPARABLES = {
    "bl", "cl", "fl", "gl", "kl", "pl",
    "br", "cr", "dr", "fr", "gr", "kr", "pr", "tr",
}

DIGRAFOS = {"ch", "ll", "rr"}


# --------------------------------------------------------------------------- #
# Utilidades
# --------------------------------------------------------------------------- #
def _quitar_tilde(c: str) -> str:
    """'á' -> 'a'. Mantiene 'ü' y 'ñ'."""
    if c in "áéíóú":
        return unicodedata.normalize("NFD", c)[0]
    return c


def es_fuerte(c: str) -> bool:
    return c in VOCALES_FUERTES


def es_hiato(a: str, b: str) -> bool:
    """¿Las vocales contiguas `a` y `b` forman hiato (sílabas distintas)?"""
    # Una vocal cerrada tónica (í, ú) siempre rompe el diptongo -> hiato.
    if a in VOCALES_DEBILES_ACENT or b in VOCALES_DEBILES_ACENT:
        return True
    # Dos vocales abiertas -> hiato.
    if es_fuerte(a) and es_fuerte(b):
        return True
    # En los demás casos (abierta+cerrada, cerrada+abierta, cerrada+cerrada) -> diptongo.
    return False


# --------------------------------------------------------------------------- #
# Paso 1: descomponer la palabra en "unidades" (vocal o consonante)
# --------------------------------------------------------------------------- #
def _unidades(palabra: str):
    """
    Devuelve una lista de tuplas (tipo, texto) donde tipo es 'V' o 'C'.
    Trata como una sola consonante: ch, ll, rr, qu, gu(+e/i).
    """
    w = palabra.lower()
    unidades = []
    i = 0
    n = len(w)
    while i < n:
        par = w[i:i + 2]

        if par in DIGRAFOS:                       # ch, ll, rr
            unidades.append(("C", par))
            i += 2
            continue
        if par == "qu":                           # 'u' muda
            unidades.append(("C", par))
            i += 2
            continue
        if par == "gu" and i + 2 < n and w[i + 2] in "eéií":   # gue, gui ('u' muda)
            unidades.append(("C", par))
            i += 2
            continue

        c = w[i]
        if c in VOCALES:
            unidades.append(("V", c))
        else:
            unidades.append(("C", c))             # incluye h, y, ñ, etc.
        i += 1
    return unidades


# --------------------------------------------------------------------------- #
# Paso 2: agrupar vocales en núcleos (diptongo/triptongo o hiato)
# --------------------------------------------------------------------------- #
def _nucleos(unidades):
    """Lista de núcleos; cada núcleo es una lista de índices (en `unidades`)
    de las vocales que lo componen."""
    nucleos = []
    j = 0
    n = len(unidades)
    while j < n:
        if unidades[j][0] == "V":
            run = [j]
            k = j + 1
            while k < n and unidades[k][0] == "V":
                run.append(k)
                k += 1
            # Separar el grupo vocálico en núcleos según hiato.
            actual = [run[0]]
            for idx in range(1, len(run)):
                a = unidades[run[idx - 1]][1]
                b = unidades[run[idx]][1]
                if es_hiato(a, b):
                    nucleos.append(actual)
                    actual = [run[idx]]
                else:
                    actual.append(run[idx])
            nucleos.append(actual)
            j = k
        else:
            j += 1
    return nucleos


# --------------------------------------------------------------------------- #
# Paso 3: distribuir un bloque de consonantes entre dos núcleos
# --------------------------------------------------------------------------- #
def _distribuir(bloque, unidades):
    """
    `bloque` es la lista de índices de consonantes entre dos núcleos.
    Devuelve (coda, ataque): consonantes que cierran la sílaba actual y
    consonantes que abren la siguiente.
    """
    m = len(bloque)
    if m == 0:
        return [], []
    if m == 1:
        return [], bloque                       # V-CV : la consonante abre la siguiente
    if m == 2:
        c1 = unidades[bloque[0]][1]
        c2 = unidades[bloque[1]][1]
        if (c1 + c2) in GRUPOS_INSEPARABLES:
            return [], bloque                   # grupo inseparable -> ambas a la siguiente
        return [bloque[0]], [bloque[1]]         # VC-CV
    # m >= 3: las dos últimas, si forman grupo, van juntas a la siguiente sílaba.
    c1 = unidades[bloque[-2]][1]
    c2 = unidades[bloque[-1]][1]
    if (c1 + c2) in GRUPOS_INSEPARABLES:
        return bloque[:-2], bloque[-2:]
    return bloque[:-1], [bloque[-1]]


# --------------------------------------------------------------------------- #
# Función pública: silabear una palabra
# --------------------------------------------------------------------------- #
def silabas(palabra: str):
    """Divide `palabra` en una lista de sílabas (cadenas)."""
    # Conservar solo la parte alfabética interna (apóstrofos, etc. se ignoran
    # para el silabeo, p. ej. "pa'" -> "pa").
    limpia = "".join(c for c in palabra if c.isalpha())
    if not limpia:
        return [palabra] if palabra else []

    unidades = _unidades(limpia)
    nucleos = _nucleos(unidades)

    if not nucleos:                             # palabra sin vocales (raro)
        return [limpia]

    # Construcción de sílabas como listas de índices de unidades.
    silabas_idx = []
    # Primera sílaba: consonantes iniciales + primer núcleo.
    cur = list(range(0, nucleos[0][0])) + nucleos[0]

    for m in range(len(nucleos) - 1):
        ini = nucleos[m][-1] + 1
        fin = nucleos[m + 1][0] - 1
        bloque = list(range(ini, fin + 1))
        coda, ataque = _distribuir(bloque, unidades)
        cur += coda
        silabas_idx.append(cur)
        cur = ataque + nucleos[m + 1]

    # Consonantes finales (coda de la última sílaba).
    cur += list(range(nucleos[-1][-1] + 1, len(unidades)))
    silabas_idx.append(cur)

    return ["".join(unidades[i][1] for i in s) for s in silabas_idx]


def contar_silabas(palabra: str) -> int:
    """Número de sílabas gramaticales de una palabra."""
    limpia = "".join(c for c in palabra if c.isalpha())
    if not limpia:
        return 0
    return len(_nucleos(_unidades(limpia)))


# --------------------------------------------------------------------------- #
# Tonicidad: aguda / llana / esdrújula
# --------------------------------------------------------------------------- #
def tonicidad(palabra: str):
    """
    Devuelve (clase, posicion_desde_el_final) donde:
        clase ∈ {"aguda", "llana", "esdrujula", "monosilaba"}
        posicion 1 = última sílaba, 2 = penúltima, ...
    """
    sil = silabas(palabra)
    n = len(sil)
    if n == 0:
        return ("llana", 0)
    if n == 1:
        return ("monosilaba", 1)

    # 1) ¿Hay tilde escrita? Esa sílaba es la tónica.
    idx_tonica = None
    for k, s in enumerate(sil):
        if any(c in VOCALES_ACENTUADAS for c in s):
            idx_tonica = k
            break

    # 2) Si no hay tilde, aplicar la regla general.
    if idx_tonica is None:
        ultima_letra = "".join(c for c in palabra if c.isalpha())[-1].lower()
        if ultima_letra in "nsaeiouáéíóúü":      # termina en vocal, n o s -> llana
            idx_tonica = n - 2
        else:                                    # termina en otra consonante -> aguda
            idx_tonica = n - 1

    pos_desde_final = n - idx_tonica             # 1 = última
    if pos_desde_final == 1:
        clase = "aguda"
    elif pos_desde_final == 2:
        clase = "llana"
    else:
        clase = "esdrujula"
    return (clase, pos_desde_final)


# --------------------------------------------------------------------------- #
# Conteo métrico de un verso (sinalefa + ajuste por acento final)
# --------------------------------------------------------------------------- #
def _empieza_por_vocal(palabra: str) -> bool:
    letras = [c for c in palabra.lower() if c.isalpha()]
    if not letras:
        return False
    if letras[0] in VOCALES:
        return True
    # 'h' muda seguida de vocal cuenta como inicio vocálico (sinalefa).
    if letras[0] == "h" and len(letras) > 1 and letras[1] in VOCALES:
        return True
    return False


def _termina_en_vocal(palabra: str) -> bool:
    letras = [c for c in palabra.lower() if c.isalpha()]
    if not letras:
        return False
    return letras[-1] in VOCALES


def contar_silabas_verso(palabras, detalle: bool = False):
    """
    Cuenta las sílabas MÉTRICAS de un verso.

    `palabras` : lista de cadenas (las palabras del verso, ya sin signos).
    Aplica sinalefa entre palabras y el ajuste por acento de la última palabra.

    Si `detalle=True`, devuelve un dict con el desglose; si no, sólo el entero.
    """
    palabras = [p for p in palabras if any(c.isalpha() for c in p)]
    if not palabras:
        return {"metricas": 0} if detalle else 0

    gramaticales = sum(contar_silabas(p) for p in palabras)

    # Sinalefas entre palabras consecutivas.
    sinalefas = 0
    for i in range(len(palabras) - 1):
        if _termina_en_vocal(palabras[i]) and _empieza_por_vocal(palabras[i + 1]):
            sinalefas += 1

    # Ajuste por acento de la última palabra del verso.
    clase, _ = tonicidad(palabras[-1])
    if clase in ("aguda", "monosilaba"):
        ajuste = 1
    elif clase == "esdrujula":
        ajuste = -1
    else:
        ajuste = 0

    metricas = gramaticales - sinalefas + ajuste

    if detalle:
        return {
            "gramaticales": gramaticales,
            "sinalefas": sinalefas,
            "clase_final": clase,
            "ajuste": ajuste,
            "metricas": metricas,
        }
    return metricas
