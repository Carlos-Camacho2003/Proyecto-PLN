"""
Tests — Fase 7: PCFG y desambiguación probabilística.

Demuestra el entregable del ROADMAP:
    "elige el esquema métrico más plausible del Ejemplo 2"
    (cuarteto vs dos pareados ante AABB / AAAA ambiguos)

Estructura de los tests
-----------------------
    TestValidacionPCFG      → las probabilidades de cada no-terminal suman 1
    TestProbabilidadRegla   → consulta de P(lhs → rhs)
    TestProbabilidadArbol   → P(árbol) = producto de P(reglas)
    TestEleccion            → mejor_arbol elige el más probable
    TestRanking             → rankear_arboles devuelve orden descendente
    TestReporte             → las cadenas de texto contienen lo esperado
"""

from __future__ import annotations

import pytest

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


def aprox(a: float, b: float, tol: float = 1e-6) -> bool:
    return abs(a - b) < tol


# ════════════════════════════════════════════════════════════════════════════ #
# 1. Validación formal de la PCFG
# ════════════════════════════════════════════════════════════════════════════ #

class TestValidacionPCFG:
    def test_todos_los_no_terminales_suman_uno(self):
        assert validar_pcfg()

    def test_cuarteto_suma_uno(self):
        total = sum(p for _, p in gramatica_pcfg["Cuarteto"])
        assert aprox(total, 1.0), f"Cuarteto suma {total}, no 1.0"

    def test_estrofa_suma_uno(self):
        total = sum(p for _, p in gramatica_pcfg["Estrofa"])
        assert aprox(total, 1.0), f"Estrofa suma {total}, no 1.0"

    def test_pareado_suma_uno(self):
        total = sum(p for _, p in gramatica_pcfg["Pareado"])
        assert aprox(total, 1.0), f"Pareado suma {total}, no 1.0"

    def test_pcfg_invalida_lanza_valueerror(self):
        gram_mala = {"TestNT": [(['A'], 0.3), (['B'], 0.4)]}  # suma 0.7, no 1.0
        with pytest.raises(ValueError, match="TestNT"):
            validar_pcfg(gram_mala)


# ════════════════════════════════════════════════════════════════════════════ #
# 2. Consulta de probabilidad de una regla
# ════════════════════════════════════════════════════════════════════════════ #

class TestProbabilidadRegla:
    def test_cuarteto_abab(self):
        assert aprox(probabilidad_regla("Cuarteto", ["A", "B", "A", "B"]), 0.40)

    def test_cuarteto_aabb(self):
        assert aprox(probabilidad_regla("Cuarteto", ["A", "A", "B", "B"]), 0.35)

    def test_cuarteto_abba(self):
        assert aprox(probabilidad_regla("Cuarteto", ["A", "B", "B", "A"]), 0.15)

    def test_cuarteto_aaaa(self):
        assert aprox(probabilidad_regla("Cuarteto", ["A", "A", "A", "A"]), 0.10)

    def test_regla_inexistente_devuelve_cero(self):
        assert probabilidad_regla("Cuarteto", ["X", "Y"]) == 0.0

    def test_no_terminal_inexistente(self):
        assert probabilidad_regla("Inexistente", ["A"]) == 0.0


# ════════════════════════════════════════════════════════════════════════════ #
# 3. Probabilidad de árboles completos — los números clave de la Fase 7
# ════════════════════════════════════════════════════════════════════════════ #

class TestProbabilidadArbol:
    def test_aabb_produce_dos_arboles(self):
        arboles, _ = analizar_con_fallback(['A','A','B','B'], gramatica, gramatica_con_libre)
        assert len(arboles) == 2

    def test_p_cuarteto_aabb_es_0175(self):
        """
        Estrofa→Cuarteto (0.50) × Cuarteto→AABB (0.35) = 0.175
        """
        arboles, _ = analizar_con_fallback(['A','A','B','B'], gramatica, gramatica_con_libre)
        for a in arboles:
            if "Cuarteto" in nombre_esquema(a):
                assert aprox(probabilidad_arbol(a), 0.175), (
                    f"P(Cuarteto AABB) = {probabilidad_arbol(a):.6f}, esperado 0.175"
                )

    def test_p_dos_pareados_aabb_es_0008(self):
        """
        Estrofa→DosPareados (0.20) × DosPareados→Pareado Pareado (1.00)
        × Pareado→AA (0.20) × Pareado→BB (0.20) = 0.008
        """
        arboles, _ = analizar_con_fallback(['A','A','B','B'], gramatica, gramatica_con_libre)
        for a in arboles:
            if "Dos pareados" in nombre_esquema(a):
                assert aprox(probabilidad_arbol(a), 0.008), (
                    f"P(Dos pareados AABB) = {probabilidad_arbol(a):.6f}, esperado 0.008"
                )

    def test_desglose_tiene_campos_correctos(self):
        arboles, _ = analizar_con_fallback(['A','A','B','B'], gramatica, gramatica_con_libre)
        info = desglose_probabilidad(arboles[0])
        assert "reglas" in info
        assert "probs" in info
        assert "total" in info
        assert len(info["reglas"]) == len(info["probs"])


# ════════════════════════════════════════════════════════════════════════════ #
# 4. Elección del mejor árbol (entregable del ROADMAP)
# ════════════════════════════════════════════════════════════════════════════ #

class TestEleccion:
    def test_ganador_aabb_es_cuarteto(self):
        arboles, _ = analizar_con_fallback(['A','A','B','B'], gramatica, gramatica_con_libre)
        ganador = mejor_arbol(arboles)
        assert "Cuarteto" in nombre_esquema(ganador), (
            f"Esperaba Cuarteto, obtuve: {nombre_esquema(ganador)}"
        )

    def test_ganador_aaaa_es_cuarteto(self):
        """Cuarteto AAAA (0.05) > DosPareados (0.008) → gana el cuarteto."""
        arboles, _ = analizar_con_fallback(['A','A','A','A'], gramatica, gramatica_con_libre)
        ganador = mejor_arbol(arboles)
        assert "Cuarteto" in nombre_esquema(ganador), (
            f"Esperaba Cuarteto, obtuve: {nombre_esquema(ganador)}"
        )

    def test_p_cuarteto_aaaa_es_005(self):
        """Estrofa→Cuarteto (0.50) × Cuarteto→AAAA (0.10) = 0.05"""
        arboles, _ = analizar_con_fallback(['A','A','A','A'], gramatica, gramatica_con_libre)
        ganador = mejor_arbol(arboles)
        assert aprox(probabilidad_arbol(ganador), 0.05), (
            f"P(Cuarteto AAAA) = {probabilidad_arbol(ganador):.6f}, esperado 0.05"
        )

    def test_mejor_arbol_lista_vacia(self):
        assert mejor_arbol([]) is None

    def test_abab_sin_ambiguedad(self):
        arboles, _ = analizar_con_fallback(['A','B','A','B'], gramatica, gramatica_con_libre)
        assert len(arboles) == 1
        assert "Cuarteto" in nombre_esquema(mejor_arbol(arboles))


# ════════════════════════════════════════════════════════════════════════════ #
# 5. Ranking ordenado
# ════════════════════════════════════════════════════════════════════════════ #

class TestRanking:
    def test_ranking_descendente(self):
        arboles, _ = analizar_con_fallback(['A','A','B','B'], gramatica, gramatica_con_libre)
        ranking = rankear_arboles(arboles)
        probs = [p for _, p in ranking]
        assert probs == sorted(probs, reverse=True)

    def test_ranking_lista_vacia(self):
        assert rankear_arboles([]) == []

    def test_ranking_devuelve_tuplas_arbol_prob(self):
        arboles, _ = analizar_con_fallback(['A','A','B','B'], gramatica, gramatica_con_libre)
        ranking = rankear_arboles(arboles)
        for arbol, prob in ranking:
            assert isinstance(prob, float)
            assert prob > 0


# ════════════════════════════════════════════════════════════════════════════ #
# 6. Reportes en texto
# ════════════════════════════════════════════════════════════════════════════ #

class TestReporte:
    def test_reporte_ranking_contiene_ganador(self):
        arboles, _ = analizar_con_fallback(['A','A','B','B'], gramatica, gramatica_con_libre)
        reporte = reporte_ranking(arboles)
        assert "Lectura elegida" in reporte
        assert "Cuarteto" in reporte

    def test_reporte_ranking_muestra_porcentajes(self):
        arboles, _ = analizar_con_fallback(['A','A','B','B'], gramatica, gramatica_con_libre)
        reporte = reporte_ranking(arboles)
        assert "%" in reporte

    def test_reporte_ranking_un_arbol(self):
        arboles, _ = analizar_con_fallback(['A','B','A','B'], gramatica, gramatica_con_libre)
        reporte = reporte_ranking(arboles)
        assert "Única lectura" in reporte

    def test_reporte_ranking_lista_vacia(self):
        reporte = reporte_ranking([])
        assert "no hay" in reporte.lower()

    def test_reporte_desglose_contiene_producto(self):
        arboles, _ = analizar_con_fallback(['A','A','B','B'], gramatica, gramatica_con_libre)
        desglose = reporte_desglose_ganador(arboles)
        assert "Producto total" in desglose
        assert "0.175" in desglose

    def test_reporte_desglose_lista_vacia(self):
        desglose = reporte_desglose_ganador([])
        assert "sin ganador" in desglose.lower()
