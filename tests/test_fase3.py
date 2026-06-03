"""
Pruebas de la Fase 3 — CFG + Parser de esquemas de rima.

Correr desde la raiz del proyecto:
    python tests/test_fase3.py
(o con pytest si esta instalado:  pytest -q)
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cfg import (
    gramatica,
    gramatica_con_libre,
    analizar_con_fallback,
    nombre_esquema,
    descripcion_formal,
    secuencia_rimas,
    describir_esquema,
)


_RESULTADOS = {"ok": 0, "fail": 0}


def check(condicion, descripcion):
    if condicion:
        _RESULTADOS["ok"] += 1
        print("  [OK] " + descripcion)
    else:
        _RESULTADOS["fail"] += 1
        print("  [FALLO] " + descripcion)


def probar(secuencia, descripcion):
    print(f"\n  Entrada: {secuencia}   ({descripcion})")
    arboles, modo = analizar_con_fallback(secuencia, gramatica, gramatica_con_libre)

    if not arboles:
        print("    -> RECHAZADA por todas las gramaticas")
        return

    if modo == 'clasica' and len(arboles) > 1:
        print(f"    -> AMBIGUEDAD ESTRUCTURAL: {len(arboles)} lecturas clasicas")
        for i, a in enumerate(arboles, 1):
            print(f"       Lectura {i}: {nombre_esquema(a)}")
    elif modo == 'clasica':
        print(f"    -> {nombre_esquema(arboles[0])}")
    elif modo == 'libre':
        print(f"    -> Sin forma clasica reconocida, analizado como estrofa libre:")
        print(f"       {nombre_esquema(arboles[0])}")


def test_parser():
    print("\n[Parser CFG]")
    casos = [
        (['A', 'A'],           "pareado AA",           'clasica', False),
        (['A', 'A', 'B', 'B'], "AABB: ambiguo",        'clasica', True),
        (['A', 'A', 'A', 'A'], "AAAA: ambiguo",        'clasica', True),
        (['A', 'B', 'A', 'B'], "ABAB: sin ambiguedad", 'clasica', False),
        (['A', 'B', 'B', 'A'], "ABBA: sin ambiguedad", 'clasica', False),
        (['A', 'A', 'A'],      "AAA: terceto",         'clasica', False),
        (['A', 'B', 'C'],      "ABC: estrofa libre",   'libre',   False),
    ]
    for seq, desc, modo_esperado, ambiguo_esperado in casos:
        arboles, modo = analizar_con_fallback(seq, gramatica, gramatica_con_libre)
        check(modo == modo_esperado,
              f"{desc} → modo={modo} (esperado {modo_esperado})")
        if modo_esperado == 'clasica':
            check((len(arboles) > 1) == ambiguo_esperado,
                  f"{desc} → ambigüedad={'sí' if len(arboles) > 1 else 'no'} "
                  f"(esperado {'sí' if ambiguo_esperado else 'no'})")


def test_extractor_rima():
    print("\n[Extractor de rima — integracion con Fase 2]")
    # Cuatro versos del enunciado del proyecto.
    versos = [
        ["Llevo", "el", "barrio", "en", "la", "sangre", "lo", "respiro", "al", "andar"],
        ["cada", "esquina", "me", "canta", "cada", "calle", "es", "mi", "hogar"],
        ["no", "encuentro", "paz", "ni", "razon", "cuando", "me", "dices", "que", "no"],
        ["todo", "es", "un", "eco", "veloz", "que", "se", "queda", "en", "el", "adios"],
    ]
    etiquetas, mapa = secuencia_rimas(versos, modo="consonante")
    check(etiquetas[0] == etiquetas[1],
          "verso 1 y 2 riman (ambos en 'ar')")
    check(etiquetas[2] == etiquetas[3],
          "verso 3 y 4 riman")
    check(etiquetas[0] != etiquetas[2],
          "verso 1 y 3 no riman")
    print(f"   Esquema detectado: {describir_esquema(etiquetas, mapa)}")


def main():
    print("=" * 64)
    print(" GRAMATICA FORMAL (clasica)")
    print("=" * 64)
    print(descripcion_formal(gramatica))

    print("=" * 64)
    print(" PRUEBAS DEL PARSER")
    print("=" * 64)
    probar(['A', 'A'],                 "pareado AA")
    probar(['A', 'A', 'B', 'B'],       "AABB: cuarteto vs dos pareados (AMBIGUO esperado)")
    probar(['A', 'A', 'A', 'A'],       "AAAA: cuarteto vs dos pareados (AMBIGUO esperado)")
    probar(['A', 'B', 'A', 'B'],       "ABAB: cuarteto cruzado (sin ambiguedad)")
    probar(['A', 'B', 'B', 'A'],       "ABBA: cuarteto abrazado (sin ambiguedad)")
    probar(['A', 'A', 'A'],            "AAA: terceto monorrimo")
    probar(['A', 'B', 'A'],            "ABA: terceto encadenado")
    probar(['A', 'B', 'C'],            "ABC: sin patron, deberia caer en estrofa libre")
    probar(['A'],                      "un solo verso, estrofa libre")

    print("\n" + "=" * 64)
    print(" PRUEBAS AUTOMATIZADAS")
    print("=" * 64)
    test_parser()
    test_extractor_rima()

    print("\n" + "=" * 64)
    total = _RESULTADOS["ok"] + _RESULTADOS["fail"]
    print(" RESULTADO: %d/%d pruebas OK, %d fallidas"
          % (_RESULTADOS["ok"], total, _RESULTADOS["fail"]))
    print("=" * 64)
    sys.exit(1 if _RESULTADOS["fail"] else 0)


if __name__ == "__main__":
    main()
