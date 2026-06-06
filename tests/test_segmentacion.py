"""
Pruebas de la segmentación en estrofas del tokenizador.

`Tokenizador.separar_estrofas` agrupa los tokens en estrofas (separadas por
una línea en blanco) y, dentro de cada una, en versos (separados por '/' o
por salto de línea simple).

Correr desde la raíz del proyecto:
    python tests/test_segmentacion.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.tokenizer import Tokenizador


_RESULTADOS = {"ok": 0, "fail": 0}
_TOK = Tokenizador()


def check(condicion, descripcion):
    if condicion:
        _RESULTADOS["ok"] += 1
        print("  [OK] " + descripcion)
    else:
        _RESULTADOS["fail"] += 1
        print("  [FALLO] " + descripcion)


def estrofas(texto):
    return _TOK.separar_estrofas(_TOK.tokenizar(texto))


def palabras(estrofa):
    """list[list[str]] con el texto de cada verso de una estrofa."""
    return [[t.texto for t in verso] for verso in estrofa]


# --------------------------------------------------------------------------- #
def test_dos_estrofas():
    print("\n[Dos estrofas separadas por línea en blanco]")
    texto = "verso uno\nverso dos\n\nverso tres\nverso cuatro"
    e = estrofas(texto)
    check(len(e) == 2, "dos bloques separados por línea en blanco → 2 estrofas")
    check(len(e[0]) == 2 and len(e[1]) == 2, "cada estrofa tiene 2 versos")


def test_salto_simple_no_corta_estrofa():
    print("\n[Salto simple = verso, no estrofa]")
    texto = "uno\ndos\ntres"
    e = estrofas(texto)
    check(len(e) == 1, "saltos simples NO abren estrofa nueva → 1 estrofa")
    check(len(e[0]) == 3, "la estrofa única tiene 3 versos")


def test_barra_separa_versos():
    print("\n[La barra '/' separa versos dentro de la estrofa]")
    texto = "uno / dos / tres"
    e = estrofas(texto)
    check(len(e) == 1 and len(e[0]) == 3, "'/' produce 1 estrofa de 3 versos")


def test_lineas_en_blanco_multiples():
    print("\n[Varias líneas en blanco seguidas no crean estrofas vacías]")
    texto = "uno\n\n\n\ndos"
    e = estrofas(texto)
    check(len(e) == 2, "huecos grandes → solo 2 estrofas (sin fantasmas)")
    check(all(len(es) >= 1 for es in e), "ninguna estrofa queda vacía")


def test_blancos_inicio_y_fin():
    print("\n[Blancos al inicio y al final se descartan]")
    texto = "\n\nuno\ndos\n\n"
    e = estrofas(texto)
    check(len(e) == 1 and len(e[0]) == 2, "1 estrofa de 2 versos, sin estrofas vacías")


def test_sin_blancos_una_estrofa():
    print("\n[Sin líneas en blanco = una sola estrofa]")
    texto = "uno\ndos\ntres\ncuatro"
    e = estrofas(texto)
    check(len(e) == 1, "degrada con gracia: toda la letra es una estrofa")


def test_etiquetas_reinician_por_estrofa():
    print("\n[Las palabras quedan limpias en cada verso de cada estrofa]")
    texto = "respiro al andar\nes mi hogar\n\ndentro del corazón\ncon tu razón"
    e = estrofas(texto)
    check(len(e) == 2, "cuarteto partido en dos pareados → 2 estrofas")
    check(palabras(e[0])[0] == ["respiro", "al", "andar"], "primer verso conserva sus palabras")
    check(palabras(e[1])[1] == ["con", "tu", "razón"], "último verso conserva sus palabras")


def test_crlf_windows():
    print("\n[Funciona con saltos CRLF de Windows]")
    texto = "uno\r\ndos\r\n\r\ntres"
    e = estrofas(texto)
    check(len(e) == 2, "CRLF: '\\r\\n\\r\\n' también cuenta como línea en blanco")


def main():
    print("=" * 64)
    print(" PRUEBAS - Segmentación en estrofas")
    print("=" * 64)
    test_dos_estrofas()
    test_salto_simple_no_corta_estrofa()
    test_barra_separa_versos()
    test_lineas_en_blanco_multiples()
    test_blancos_inicio_y_fin()
    test_sin_blancos_una_estrofa()
    test_etiquetas_reinician_por_estrofa()
    test_crlf_windows()

    print("\n" + "=" * 64)
    total = _RESULTADOS["ok"] + _RESULTADOS["fail"]
    print(" RESULTADO: %d/%d pruebas OK, %d fallidas"
          % (_RESULTADOS["ok"], total, _RESULTADOS["fail"]))
    print("=" * 64)
    sys.exit(1 if _RESULTADOS["fail"] else 0)


if __name__ == "__main__":
    main()
