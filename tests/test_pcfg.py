"""
Pruebas de la PCFG y la desambiguación probabilística.

Objetivo:
    "elige el esquema métrico más plausible"
    (cuarteto vs dos pareados ante AABB / AAAA ambiguos)

Cubre:
    validar_pcfg / gramatica_pcfg  → las probabilidades de cada no-terminal suman 1
    probabilidad_regla             → consulta de P(lhs → rhs)
    probabilidad_arbol             → P(árbol) = producto de P(reglas)
    mejor_arbol / rankear_arboles  → elección y ranking descendente
    reporte_ranking / desglose     → las cadenas de texto contienen lo esperado

Correr desde la raíz del proyecto:
    python tests/test_pcfg.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.pcfg import (
    gramatica_pcfg, validar_pcfg, probabilidad_regla,
    probabilidad_arbol, desglose_probabilidad,
    rankear_arboles, mejor_arbol,
    reporte_ranking, reporte_desglose_ganador,
)
from src.gramatica import (
    gramatica, gramatica_con_libre,
    analizar_con_fallback, nombre_esquema,
)


_RESULTADOS = {"ok": 0, "fail": 0}


def check(condicion, descripcion):
    if condicion:
        _RESULTADOS["ok"] += 1
        print("  [OK] " + descripcion)
    else:
        _RESULTADOS["fail"] += 1
        print("  [FALLO] " + descripcion)


def aprox(a: float, b: float, tol: float = 1e-6) -> bool:
    return abs(a - b) < tol


def _arboles(etiquetas):
    arboles, _ = analizar_con_fallback(etiquetas, gramatica, gramatica_con_libre)
    return arboles


# ════════════════════════════════════════════════════════════════════════════ #
# 1. Validación formal de la PCFG
# ════════════════════════════════════════════════════════════════════════════ #

def test_validacion_pcfg():
    print("\n[Validación: las probabilidades de cada no-terminal suman 1]")
    check(validar_pcfg(), "validar_pcfg() → True para la gramática real")
    check(aprox(sum(p for _, p in gramatica_pcfg["Cuarteto"]), 1.0),
          "las reglas de Cuarteto suman 1.0")
    check(aprox(sum(p for _, p in gramatica_pcfg["Estrofa"]), 1.0),
          "las reglas de Estrofa suman 1.0")
    check(aprox(sum(p for _, p in gramatica_pcfg["Pareado"]), 1.0),
          "las reglas de Pareado suman 1.0")

    # Una PCFG mal formada (suma 0.7) debe lanzar ValueError.
    gram_mala = {"TestNT": [(['A'], 0.3), (['B'], 0.4)]}
    lanzo = False
    try:
        validar_pcfg(gram_mala)
    except ValueError as e:
        lanzo = "TestNT" in str(e)
    check(lanzo, "validar_pcfg(PCFG inválida) lanza ValueError mencionando el no-terminal")


# ════════════════════════════════════════════════════════════════════════════ #
# 2. Probabilidad de una regla
# ════════════════════════════════════════════════════════════════════════════ #

def test_probabilidad_regla():
    print("\n[Probabilidad de reglas Cuarteto → ...]")
    check(aprox(probabilidad_regla("Cuarteto", ["A", "B", "A", "B"]), 0.40), "P(Cuarteto→ABAB)=0.40")
    check(aprox(probabilidad_regla("Cuarteto", ["A", "A", "B", "B"]), 0.35), "P(Cuarteto→AABB)=0.35")
    check(aprox(probabilidad_regla("Cuarteto", ["A", "B", "B", "A"]), 0.15), "P(Cuarteto→ABBA)=0.15")
    check(aprox(probabilidad_regla("Cuarteto", ["A", "A", "A", "A"]), 0.10), "P(Cuarteto→AAAA)=0.10")
    check(probabilidad_regla("Cuarteto", ["X", "Y"]) == 0.0, "regla inexistente → 0.0")
    check(probabilidad_regla("Inexistente", ["A"]) == 0.0, "no-terminal inexistente → 0.0")


# ════════════════════════════════════════════════════════════════════════════ #
# 3. Probabilidad de árboles completos — los números clave de la Fase 7
# ════════════════════════════════════════════════════════════════════════════ #

def test_probabilidad_arbol():
    print("\n[Probabilidad de árboles AABB]")
    arboles = _arboles(['A', 'A', 'B', 'B'])
    check(len(arboles) == 2, "AABB produce 2 árboles (cuarteto + dos pareados)")

    # Estrofa→Cuarteto (0.50) × Cuarteto→AABB (0.35) = 0.175
    for a in arboles:
        if "Cuarteto" in nombre_esquema(a):
            check(aprox(probabilidad_arbol(a), 0.175),
                  f"P(Cuarteto AABB)=0.175 (obtenido {probabilidad_arbol(a):.6f})")
    # Estrofa→DosPareados (0.20) × DosPareados (1.00) × Pareado→AA (0.20) × Pareado→BB (0.20) = 0.008
    for a in arboles:
        if "Dos pareados" in nombre_esquema(a):
            check(aprox(probabilidad_arbol(a), 0.008),
                  f"P(Dos pareados AABB)=0.008 (obtenido {probabilidad_arbol(a):.6f})")

    info = desglose_probabilidad(arboles[0])
    check("reglas" in info and "probs" in info and "total" in info
          and len(info["reglas"]) == len(info["probs"]),
          "desglose_probabilidad tiene reglas/probs/total coherentes")


# ════════════════════════════════════════════════════════════════════════════ #
# 4. Elección del mejor árbol (objetivo de la PCFG)
# ════════════════════════════════════════════════════════════════════════════ #

def test_eleccion():
    print("\n[Elección del esquema más probable]")
    ganador = mejor_arbol(_arboles(['A', 'A', 'B', 'B']))
    check("Cuarteto" in nombre_esquema(ganador),
          f"AABB → gana el Cuarteto (obtenido {nombre_esquema(ganador)})")

    # Cuarteto AAAA (0.05) > DosPareados (0.008) → gana el cuarteto.
    ganador_aaaa = mejor_arbol(_arboles(['A', 'A', 'A', 'A']))
    check("Cuarteto" in nombre_esquema(ganador_aaaa),
          f"AAAA → gana el Cuarteto (obtenido {nombre_esquema(ganador_aaaa)})")
    check(aprox(probabilidad_arbol(ganador_aaaa), 0.05),
          f"P(Cuarteto AAAA)=0.05 (obtenido {probabilidad_arbol(ganador_aaaa):.6f})")

    check(mejor_arbol([]) is None, "mejor_arbol([]) → None")

    arboles_abab = _arboles(['A', 'B', 'A', 'B'])
    check(len(arboles_abab) == 1 and "Cuarteto" in nombre_esquema(mejor_arbol(arboles_abab)),
          "ABAB no es ambiguo → un único Cuarteto")


# ════════════════════════════════════════════════════════════════════════════ #
# 5. Ranking ordenado
# ════════════════════════════════════════════════════════════════════════════ #

def test_ranking():
    print("\n[Ranking descendente por probabilidad]")
    ranking = rankear_arboles(_arboles(['A', 'A', 'B', 'B']))
    probs = [p for _, p in ranking]
    check(probs == sorted(probs, reverse=True), "el ranking está ordenado de mayor a menor")
    check(rankear_arboles([]) == [], "rankear_arboles([]) → []")
    check(all(isinstance(p, float) and p > 0 for _, p in ranking),
          "cada entrada es (árbol, probabilidad > 0)")


# ════════════════════════════════════════════════════════════════════════════ #
# 6. Reportes en texto
# ════════════════════════════════════════════════════════════════════════════ #

def test_reporte():
    print("\n[Reportes en texto]")
    rep = reporte_ranking(_arboles(['A', 'A', 'B', 'B']))
    check("Lectura elegida" in rep and "Cuarteto" in rep, "reporte_ranking nombra la lectura elegida")
    check("%" in rep, "reporte_ranking muestra porcentajes")
    check("Única lectura" in reporte_ranking(_arboles(['A', 'B', 'A', 'B'])),
          "ABAB → reporte de 'Única lectura'")
    check("no hay" in reporte_ranking([]).lower(), "reporte_ranking([]) → mensaje 'no hay'")

    desglose = reporte_desglose_ganador(_arboles(['A', 'A', 'B', 'B']))
    check("Producto total" in desglose and "0.175" in desglose,
          "reporte_desglose_ganador muestra el producto total (0.175)")
    check("sin ganador" in reporte_desglose_ganador([]).lower(),
          "reporte_desglose_ganador([]) → 'sin ganador'")


def main():
    print("=" * 64)
    print(" PRUEBAS - PCFG (desambiguación probabilística)")
    print("=" * 64)
    test_validacion_pcfg()
    test_probabilidad_regla()
    test_probabilidad_arbol()
    test_eleccion()
    test_ranking()
    test_reporte()

    print("\n" + "=" * 64)
    total = _RESULTADOS["ok"] + _RESULTADOS["fail"]
    print(" RESULTADO: %d/%d pruebas OK, %d fallidas"
          % (_RESULTADOS["ok"], total, _RESULTADOS["fail"]))
    print("=" * 64)
    sys.exit(1 if _RESULTADOS["fail"] else 0)


if __name__ == "__main__":
    main()
