"""
Tokenizador léxico del español (Fase 1).

Convierte la letra cruda de una canción en una lista de *tokens*:

    PALABRA       secuencia de letras            ("barrio", "sangre")
    CONTRACCION   reducción del habla            ("pa", "pa'", "to", "ke")
    NUMERO        secuencia de dígitos           ("100", "2")
    SIGNO         signo de puntuación            (",", ".", "¡", "?")
    VERSO_SEP     barra que separa versos        ("/")
    NEWLINE       salto(s) de línea (= verso)
    ESPACIO       espacios/tabuladores

Se apoya en el motor `DFA` (dfa.py). Como el alfabeto real del español es
enorme, NO alimentamos el autómata con caracteres sueltos, sino con *clases
de carácter* (letra, dígito, signo, ...). Esa correspondencia carácter→clase
es, en la práctica, la "gramática regular" que define el vocabulario léxico
del sistema.

El reconocimiento usa *maximal munch*: en cada posición se toma el token más
largo posible.
"""

from __future__ import annotations

from dataclasses import dataclass

from .dfa import DFA


# --------------------------------------------------------------------------- #
# Diccionario de contracciones del habla urbana / coloquial colombiana.
# Una PALABRA cuyo lexema (en minúsculas) esté aquí se reetiqueta CONTRACCION.
# --------------------------------------------------------------------------- #
CONTRACCIONES = {
    "pa", "pa'", "pal", "p'",        # para / para el
    "to", "to'", "toa", "toas",      # todo / toda(s)
    "na", "na'",                     # nada
    "ke", "k", "q", "xq",            # que / por qué
    "toy", "toi", "ta", "tá",        # estoy / está
    "ve'", "vo'", "voa",             # ve / vos / voy a
    "d'", "de'",                     # de
    "e'", "es'",                     # es / e'
    "mijo", "mija",                  # mi hijo / mi hija (lexicalizado)
}

# Caracteres tratados como apóstrofo (recorte: pa', to', d').
APOSTROFOS = {"'", "’", "ʼ"}   # '  ’  ʼ


# --------------------------------------------------------------------------- #
# Token
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Token:
    tipo: str       # PALABRA, CONTRACCION, NUMERO, SIGNO, VERSO_SEP, NEWLINE, ESPACIO
    texto: str      # lexema original
    inicio: int     # índice de inicio en el texto
    fin: int        # índice final (exclusivo)

    def __repr__(self):
        return f"<{self.tipo} {self.texto!r}>"


# --------------------------------------------------------------------------- #
# Clasificador de caracteres  (carácter -> símbolo del alfabeto Σ del DFA)
# --------------------------------------------------------------------------- #
#   'L' letra      'D' dígito     'A' apóstrofo    '/' barra de verso
#   'P' signo      'S' espacio    'N' salto de línea
ALFABETO = {"L", "D", "A", "/", "P", "S", "N"}


def clasificar(caracter: str) -> str:
    if caracter in "\n\r":
        return "N"
    if caracter in " \t":
        return "S"
    if caracter == "/":
        return "/"
    if caracter in APOSTROFOS:
        return "A"
    if caracter.isdigit():
        return "D"
    if caracter.isalpha():        # cubre tildes y ñ (Unicode)
        return "L"
    return "P"                    # cualquier otro signo de puntuación


# --------------------------------------------------------------------------- #
# Definición del DFA del tokenizador
# --------------------------------------------------------------------------- #
#
#                         L            L
#                   ┌───────────┐  ┌───────┐
#                   ▼           │  ▼       │
#   (q0) ──L──► (W:PALABRA) ──A──► (WA:PALABRA)
#     │              ▲ (A: apóstrofo intermedio "pa'")
#     ├──D──► (NUM:NUMERO) ──D──┐
#     │            ▲────────────┘
#     ├──/──► (SL:VERSO_SEP)
#     ├──P──► (PU:SIGNO)
#     ├──A──► (PU:SIGNO)          (apóstrofo suelto = signo)
#     ├──S──► (SP:ESPACIO) ──S──┐
#     │            ▲────────────┘
#     └──N──► (NL:NEWLINE) ──N──┐
#                  ▲────────────┘
#
ESTADOS = {"q0", "W", "WA", "NUM", "SL", "PU", "SP", "NL"}

TRANSICIONES = {
    ("q0", "L"): "W",   ("W", "L"): "W",   ("W", "A"): "WA",  ("WA", "L"): "W",
    ("q0", "D"): "NUM", ("NUM", "D"): "NUM",
    ("q0", "/"): "SL",
    ("q0", "P"): "PU",
    ("q0", "A"): "PU",
    ("q0", "S"): "SP",  ("SP", "S"): "SP",
    ("q0", "N"): "NL",  ("NL", "N"): "NL",
}

ACEPTACION = {
    "W": "PALABRA",
    "WA": "PALABRA",
    "NUM": "NUMERO",
    "SL": "VERSO_SEP",
    "PU": "SIGNO",
    "SP": "ESPACIO",
    "NL": "NEWLINE",
}


# --------------------------------------------------------------------------- #
# Tokenizador
# --------------------------------------------------------------------------- #
class Tokenizador:
    """Tokeniza texto en español usando el DFA definido arriba."""

    def __init__(self):
        self.dfa = DFA(
            estados=ESTADOS,
            alfabeto=ALFABETO,
            transiciones=TRANSICIONES,
            inicial="q0",
            aceptacion=ACEPTACION,
        )

    def tokenizar(self, texto: str):
        """Devuelve la lista de Token reconocidos en `texto`."""
        clases = [clasificar(c) for c in texto]
        tokens = []
        i = 0
        n = len(texto)

        while i < n:
            longitud, etiqueta = self.dfa.match_mas_largo(clases, i)

            if longitud == 0:
                # Carácter no reconocido por el autómata: lo emitimos como SIGNO
                # de un solo carácter para no quedarnos atascados.
                longitud, etiqueta = 1, "SIGNO"

            lexema = texto[i:i + longitud]

            # Reetiquetado: ¿es una contracción conocida?
            if etiqueta == "PALABRA" and lexema.lower() in CONTRACCIONES:
                etiqueta = "CONTRACCION"

            tokens.append(Token(etiqueta, lexema, i, i + longitud))
            i += longitud

        return tokens

    # ------------------------------------------------------------------ #
    @staticmethod
    def solo_palabras(tokens):
        """Filtra los tokens léxicos significativos (palabras y contracciones)."""
        return [t for t in tokens if t.tipo in ("PALABRA", "CONTRACCION")]

    @staticmethod
    def separar_versos(tokens):
        """Agrupa los tokens en versos, cortando por VERSO_SEP ('/') o NEWLINE.
        Devuelve una lista de listas de tokens (sin los separadores ni espacios)."""
        versos = []
        actual = []
        for t in tokens:
            if t.tipo in ("VERSO_SEP", "NEWLINE"):
                if actual:
                    versos.append(actual)
                    actual = []
            elif t.tipo != "ESPACIO":
                actual.append(t)
        if actual:
            versos.append(actual)
        return versos


# --------------------------------------------------------------------------- #
# Función de conveniencia
# --------------------------------------------------------------------------- #
_TOKENIZADOR_GLOBAL = Tokenizador()


def tokenizar(texto: str):
    """Atajo para tokenizar sin instanciar la clase."""
    return _TOKENIZADOR_GLOBAL.tokenizar(texto)
