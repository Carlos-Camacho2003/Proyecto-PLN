"""
Pruebas de las Fases 1 y 2 - ejecutables sin librerias externas.

Correr desde la raiz del proyecto:
    python tests/test_basico.py
(o con pytest si esta instalado:  pytest -q)
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tokenizer import Tokenizador, tokenizar          # noqa: E402
from src.silabeo import silabas, contar_silabas, tonicidad, contar_silabas_verso  # noqa: E402


_RESULTADOS = {"ok": 0, "fail": 0}


def check(condicion, descripcion):
    if condicion:
        _RESULTADOS["ok"] += 1
        print("  [OK] " + descripcion)
    else:
        _RESULTADOS["fail"] += 1
        print("  [FALLO] " + descripcion)


def igual(obtenido, esperado, descripcion):
    check(obtenido == esperado,
          "%s  (obtenido=%r, esperado=%r)" % (descripcion, obtenido, esperado))


def test_tokenizador():
    print("\n[Tokenizador / DFA]")
    tk = Tokenizador()

    toks = tk.tokenizar("Llevo el barrio, andar")
    palabras = [t.texto for t in tk.solo_palabras(toks)]
    igual(palabras, ["Llevo", "el", "barrio", "andar"], "separa palabras")
    igual([t.tipo for t in toks if t.tipo == "SIGNO"], ["SIGNO"], "detecta la coma como SIGNO")

    toks = tk.tokenizar("pa' to el barrio, ke vuelta")
    tipos = {t.texto.lower(): t.tipo for t in toks if t.tipo in ("PALABRA", "CONTRACCION")}
    igual(tipos.get("pa'"), "CONTRACCION", "reconoce contraccion pa'")
    igual(tipos.get("to"), "CONTRACCION", "reconoce contraccion to")
    igual(tipos.get("ke"), "CONTRACCION", "reconoce contraccion ke")
    igual(tipos.get("barrio"), "PALABRA", "barrio es PALABRA normal")

    toks = tk.tokenizar("uno dos / tres cuatro")
    versos = tk.separar_versos(toks)
    igual(len(versos), 2, "separa dos versos por '/'")

    toks = tk.tokenizar("tengo 100 problemas")
    igual([t.tipo for t in toks if t.tipo == "NUMERO"], ["NUMERO"], "reconoce numero 100")


def test_silabeo():
    print("\n[Silabeador]")
    casos = {
        "barrio":  ["ba", "rrio"],
        "sangre":  ["san", "gre"],
        "respiro": ["res", "pi", "ro"],
        "esquina": ["es", "qui", "na"],
        "calle":   ["ca", "lle"],
        "hogar":   ["ho", "gar"],
        "andar":   ["an", "dar"],
        "dia":     ["dia"],
        "limpia":  ["lim", "pia"],
        "ciudad":  ["ciu", "dad"],
        "instruccion": ["ins", "truc", "cion"],
    }
    for palabra, esperado in casos.items():
        igual(silabas(palabra), esperado, "silabea %r" % palabra)

    igual(silabas("día"), ["dí", "a"], "silabea 'dia' con tilde (hiato)")
    igual(contar_silabas("respiro"), 3, "cuenta silabas de respiro")
    igual(contar_silabas("día"), 2, "cuenta silabas de 'dia' con tilde (hiato)")


def test_tonicidad():
    print("\n[Tonicidad]")
    igual(tonicidad("andar")[0], "aguda", "andar es aguda")
    igual(tonicidad("hogar")[0], "aguda", "hogar es aguda")
    igual(tonicidad("barrio")[0], "llana", "barrio es llana")
    igual(tonicidad("sílaba")[0], "esdrujula", "silaba es esdrujula")
    igual(tonicidad("café")[0], "aguda", "cafe es aguda (con tilde)")


def test_metrica_alejandrino():
    print("\n[Metrica - ejemplo del enunciado]")
    tk = Tokenizador()
    letra = ("Llevo el barrio en la sangre, lo respiro al andar / "
             "cada esquina me canta, cada calle es mi hogar")
    versos = tk.separar_versos(tk.tokenizar(letra))
    conteos = []
    for v in versos:
        palabras = [t.texto for t in v if t.tipo in ("PALABRA", "CONTRACCION", "NUMERO")]
        conteos.append(contar_silabas_verso(palabras))
    igual(conteos, [14, 14], "ambos versos son alejandrinos (14 silabas)")


def main():
    print("=" * 64)
    print(" PRUEBAS - Analizador de letras (Fases 1 y 2)")
    print("=" * 64)
    test_tokenizador()
    test_silabeo()
    test_tonicidad()
    test_metrica_alejandrino()

    print("\n" + "=" * 64)
    total = _RESULTADOS["ok"] + _RESULTADOS["fail"]
    print(" RESULTADO: %d/%d pruebas OK, %d fallidas"
          % (_RESULTADOS["ok"], total, _RESULTADOS["fail"]))
    print("=" * 64)
    sys.exit(1 if _RESULTADOS["fail"] else 0)


if __name__ == "__main__":
    main()
