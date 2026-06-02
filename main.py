"""
Analizador de letras de rap / música urbana colombiana — CLI.

Estado actual del pipeline:
    [Fase 1] Tokenización con DFA
    [Fase 2] Silabeo + conteo métrico de versos (sinalefa + acento final)

Uso:
    python main.py                 # corre con la letra de demostración
    python main.py archivo.txt     # analiza la letra contenida en un archivo
    python main.py -               # lee la letra desde la entrada estándar

Versos: se separan por '/' o por salto de línea.
"""

from __future__ import annotations

import sys

from src.tokenizer import Tokenizador
from src.silabeo import silabas, contar_silabas_verso

#Para empezar xd
LETRA_DEMO = (
    "Llevo el barrio en la sangre, lo respiro al andar / "
    "cada esquina me canta, cada calle es mi hogar"
)


def _linea(caracter="─", n=64):
    return caracter * n


def mostrar_tokens(tokenizador, texto):
    print(_linea("═"))
    print(" FASE 1 · TOKENIZACIÓN (DFA)")
    print(_linea("═"))
    tokens = tokenizador.tokenizar(texto)
    visibles = [t for t in tokens if t.tipo not in ("ESPACIO",)]
    print(f" {len(visibles)} tokens (se omiten los espacios):\n")
    for t in visibles:
        etiqueta = t.tipo
        marca = "·"
        if etiqueta == "CONTRACCION":
            marca = "★"          # contracción del habla detectada
        print(f"   {marca} {etiqueta:<11} {t.texto!r}")
    return tokens


def mostrar_metrica(tokenizador, tokens):
    print()
    print(_linea("═"))
    print(" FASE 2 · MÉTRICA (silabeo + sinalefa + acento)")
    print(_linea("═"))
    versos = tokenizador.separar_versos(tokens)

    for n, verso_tokens in enumerate(versos, start=1):
        palabras = [t.texto for t in verso_tokens
                    if t.tipo in ("PALABRA", "CONTRACCION", "NUMERO")]
        texto_verso = " ".join(palabras)
        d = contar_silabas_verso(palabras, detalle=True)

        print(f"\n Verso {n}: {texto_verso}")
        # Silabeo palabra por palabra.
        desglose = "   ".join("-".join(silabas(p)) for p in palabras)
        print(f"   sílabas:   {desglose}")
        print(f"   gramaticales={d['gramaticales']}  "
              f"sinalefas=-{d['sinalefas']}  "
              f"acento({d['clase_final']})={'+' if d['ajuste']>=0 else ''}{d['ajuste']}")
        print(f"   ►  {d['metricas']} sílabas métricas")

    # Nota métrica rápida.
    nombres = {7: "heptasílabo", 8: "octosílabo", 11: "endecasílabo", 14: "alejandrino"}
    print()
    cuentas = [contar_silabas_verso(
        [t.texto for t in v if t.tipo in ("PALABRA", "CONTRACCION", "NUMERO")])
        for v in versos]
    for n, c in enumerate(cuentas, start=1):
        etiqueta = nombres.get(c, f"{c} sílabas")
        print(f"   Verso {n}: {c} sílabas ({etiqueta})")


def cargar_texto(argv):
    if len(argv) >= 2:
        if argv[1] == "-":
            return sys.stdin.read()
        with open(argv[1], "r", encoding="utf-8") as f:
            return f.read()
    return LETRA_DEMO


def main(argv=None):
    argv = argv if argv is not None else sys.argv
    texto = cargar_texto(argv)
    tokenizador = Tokenizador()

    print()
    print(" Letra analizada:")
    print(f"   {texto}\n")

    tokens = mostrar_tokens(tokenizador, texto)
    mostrar_metrica(tokenizador, tokens)
    print()


if __name__ == "__main__":
    main()
