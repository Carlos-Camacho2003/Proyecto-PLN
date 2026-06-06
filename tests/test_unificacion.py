"""
Pruebas de la Fase 5 — DCG + unificación de rimas.

Demuestra el entregable pedido:
    "rechaza AAAA si los versos no riman entre sí; acepta el esquema correcto."

Correr desde la raiz del proyecto:
    python tests/test_fase5.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.unificacion import unificar_rima, verificar_esquema, filtrar_arboles_validos
from src.rima import secuencia_rimas
from src.gramatica import gramatica, gramatica_con_libre, analizar_con_fallback, nombre_esquema


_RESULTADOS = {"ok": 0, "fail": 0}


def check(condicion, descripcion):
    if condicion:
        _RESULTADOS["ok"] += 1
        print("  [OK] " + descripcion)
    else:
        _RESULTADOS["fail"] += 1
        print("  [FALLO] " + descripcion)


# --------------------------------------------------------------------------- #
def test_unificacion_basica():
    print("\n[Unificacion de variables de rima]")

    # Variable libre se liga.
    r = unificar_rima({}, "A", "ar")
    check(r == {"A": "ar"}, "liga [A] libre con 'ar'")

    # Misma etiqueta, misma terminacion: unifica.
    r = unificar_rima({"A": "ar"}, "A", "ar")
    check(r == {"A": "ar"}, "[A]='ar' unifica con 'ar' otra vez")

    # Misma etiqueta, terminacion distinta: conflicto.
    r = unificar_rima({"A": "ar"}, "A", "or")
    check(r is None, "[A]='ar' NO unifica con 'or' (conflicto)")


def test_acepta_esquema_correcto():
    print("\n[Acepta esquema AABB correcto]")
    # andar/hogar riman (-ar); corazón/razón riman (-on).
    versos = [
        ["respiro", "al", "andar"],
        ["es", "mi", "hogar"],
        ["dentro", "del", "corazón"],
        ["vibra", "con", "tu", "razón"],
    ]
    etiquetas, _ = secuencia_rimas(versos, modo="consonante")
    valido = verificar_esquema(etiquetas, versos, modo="consonante")
    check(valido, f"esquema {''.join(etiquetas)} es consistente con las rimas reales")


def test_rechaza_aaaa_falso():
    print("\n[Rechaza AAAA cuando los versos NO riman]")
    # Forzamos un esquema AAAA pero las palabras NO riman entre si.
    versos = [
        ["camino", "sin", "andar"],   # -ar
        ["busco", "un", "hogar"],     # -ar
        ["siento", "el", "amor"],     # -or  ← rompe la rima
        ["choco", "con", "la", "pared"],  # -ed ← rompe la rima
    ]
    # Imponemos manualmente el esquema AAAA (como si la CFG lo propusiera).
    etiquetas_falsas = ["A", "A", "A", "A"]
    resultado = verificar_esquema(etiquetas_falsas, versos,
                                  modo="consonante", detalle=True)
    check(not resultado["valido"],
          "AAAA es RECHAZADO porque 'amor'/'pared' no riman con 'andar'/'hogar'")
    print(f"   Motivo: {resultado['motivo']}")
    print("   Traza:")
    for paso in resultado["traza"]:
        print(f"     {paso}")


def test_filtrado_arboles():
    print("\n[Filtrado de arboles de la CFG con la DCG]")
    # AABB real: la CFG da 2 arboles (cuarteto y dos pareados), ambos VALIDOS
    # porque las rimas reales SI son AABB.
    versos = [
        ["respiro", "al", "andar"],
        ["es", "mi", "hogar"],
        ["dentro", "del", "corazón"],
        ["vibra", "con", "tu", "razón"],
    ]
    etiquetas, _ = secuencia_rimas(versos, modo="consonante")
    arboles, modo = analizar_con_fallback(etiquetas, gramatica, gramatica_con_libre)
    validos = filtrar_arboles_validos(arboles, versos, modo="consonante")
    check(len(validos) == len(arboles),
          f"los {len(arboles)} arboles de AABB pasan la DCG (rimas correctas)")
    for a in validos:
        print(f"     árbol válido: {nombre_esquema(a)}")


def main():
    print("=" * 64)
    print(" PRUEBAS - Fase 5 (DCG + unificación de rimas)")
    print("=" * 64)
    test_unificacion_basica()
    test_acepta_esquema_correcto()
    test_rechaza_aaaa_falso()
    test_filtrado_arboles()

    print("\n" + "=" * 64)
    total = _RESULTADOS["ok"] + _RESULTADOS["fail"]
    print(" RESULTADO: %d/%d pruebas OK, %d fallidas"
          % (_RESULTADOS["ok"], total, _RESULTADOS["fail"]))
    print("=" * 64)
    sys.exit(1 if _RESULTADOS["fail"] else 0)


if __name__ == "__main__":
    main()
