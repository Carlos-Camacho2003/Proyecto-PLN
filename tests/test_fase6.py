"""
Tests — Fase 6: Manejo de ambigüedad (estructural + léxica).

Cubre:
    - jerga.py     : cargar_jerga, consultar, es_polisemica, palabras_registradas
    - detector_lexico.py : detectar_palabras_ambiguas, analizar_ambiguedad_lexica,
                           contexto_palabra
    - reporte.py   : reportar_ambiguedad_estructural, reportar_ambiguedad_lexica,
                     reporte_completo

Los tests de reporte estructural usan un Nodo falso (stub) para no depender
del parser de la Fase 4. Los tests léxicos usan el JSON real de data/.
"""

from __future__ import annotations

import json
import os
import tempfile

import pytest

# ─── módulos bajo prueba ────────────────────────────────────────────────────
from src.ambiguedad.jerga import (
    cargar_jerga, consultar, es_polisemica, palabras_registradas,
)
from src.ambiguedad.detector_lexico import (
    detectar_palabras_ambiguas, analizar_ambiguedad_lexica, contexto_palabra,
)
from src.ambiguedad.reporte import (
    reportar_ambiguedad_estructural, reportar_ambiguedad_lexica, reporte_completo,
)


# ════════════════════════════════════════════════════════════════════════════ #
# Fixtures y utilidades
# ════════════════════════════════════════════════════════════════════════════ #

@pytest.fixture
def jerga_mini(tmp_path):
    """JSON mínimo con 3 palabras: 2 polisémicas, 1 con una sola acepción."""
    datos = {
        "vuelta": {
            "acepciones": [
                {"id": 1, "significado": "asunto / encargo", "region": "paisa",
                 "registro": "coloquial", "ejemplo": "tengo una vuelta"},
                {"id": 2, "significado": "venganza / represalia", "region": "urbano",
                 "registro": "informal", "ejemplo": "esa vuelta la cobro"},
            ]
        },
        "parcero": {
            "acepciones": [
                {"id": 1, "significado": "amigo cercano", "region": "paisa",
                 "registro": "coloquial", "ejemplo": "mi parcero"},
                {"id": 2, "significado": "apelativo genérico", "region": "nacional",
                 "registro": "informal", "ejemplo": "qué más, parcero"},
            ]
        },
        "barrio": {
            "acepciones": [
                {"id": 1, "significado": "zona residencial", "region": "nacional",
                 "registro": "estándar", "ejemplo": "vivo en el barrio"},
            ]
        },
    }
    ruta = str(tmp_path / "jerga_test.json")
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False)
    return ruta


class _NodoStub:
    """Stub mínimo de Nodo para probar reportar_ambiguedad_estructural sin parser."""
    def __init__(self, etiqueta, hijos=None):
        self.etiqueta = etiqueta
        self.hijos = hijos or []

    def mostrar(self):
        return f"({self.etiqueta})"

    def hojas(self):
        resultado = []
        for hijo in self.hijos:
            if isinstance(hijo, _NodoStub):
                resultado.extend(hijo.hojas())
            else:
                resultado.append(hijo)
        return resultado


# ════════════════════════════════════════════════════════════════════════════ #
# 1. jerga.py
# ════════════════════════════════════════════════════════════════════════════ #

class TestCargarJerga:
    def test_carga_dict(self, jerga_mini):
        j = cargar_jerga(jerga_mini)
        assert isinstance(j, dict)

    def test_filtra_claves_privadas(self, tmp_path):
        datos = {"_comentario": "ignorar", "vuelta": {"acepciones": [{"id": 1}]}}
        ruta = str(tmp_path / "j.json")
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f)
        j = cargar_jerga(ruta)
        assert "_comentario" not in j
        assert "vuelta" in j

    def test_contiene_palabras_conocidas(self, jerga_mini):
        j = cargar_jerga(jerga_mini)
        assert "vuelta" in j
        assert "parcero" in j


class TestConsultar:
    def test_palabra_polisemica(self, jerga_mini):
        j = cargar_jerga(jerga_mini)
        acepciones = consultar("vuelta", j)
        assert len(acepciones) == 2

    def test_palabra_monosémica(self, jerga_mini):
        j = cargar_jerga(jerga_mini)
        acepciones = consultar("barrio", j)
        assert len(acepciones) == 1

    def test_palabra_ausente(self, jerga_mini):
        j = cargar_jerga(jerga_mini)
        assert consultar("palabra_inexistente", j) == []

    def test_case_insensitive(self, jerga_mini):
        j = cargar_jerga(jerga_mini)
        assert len(consultar("VUELTA", j)) == 2
        assert len(consultar("Parcero", j)) == 2


class TestEsPolisemica:
    def test_polisemica_true(self, jerga_mini):
        j = cargar_jerga(jerga_mini)
        assert es_polisemica("vuelta", j) is True

    def test_monosémica_false(self, jerga_mini):
        j = cargar_jerga(jerga_mini)
        assert es_polisemica("barrio", j) is False

    def test_ausente_false(self, jerga_mini):
        j = cargar_jerga(jerga_mini)
        assert es_polisemica("inexistente", j) is False


class TestPalabrasRegistradas:
    def test_devuelve_set(self, jerga_mini):
        j = cargar_jerga(jerga_mini)
        reg = palabras_registradas(j)
        assert isinstance(reg, set)

    def test_contiene_todas(self, jerga_mini):
        j = cargar_jerga(jerga_mini)
        reg = palabras_registradas(j)
        assert {"vuelta", "parcero", "barrio"} <= reg


# ════════════════════════════════════════════════════════════════════════════ #
# 2. detector_lexico.py
# ════════════════════════════════════════════════════════════════════════════ #

class TestDetectarPalabrasAmbiguas:
    def test_detecta_polisemica(self, jerga_mini):
        j = cargar_jerga(jerga_mini)
        resultado = detectar_palabras_ambiguas(["esa", "vuelta", "es", "mía"], j)
        assert len(resultado) == 1
        pos, palabra, acepciones = resultado[0]
        assert palabra == "vuelta"
        assert pos == 1
        assert len(acepciones) == 2

    def test_ignora_monosémica(self, jerga_mini):
        j = cargar_jerga(jerga_mini)
        resultado = detectar_palabras_ambiguas(["vivo", "en", "el", "barrio"], j)
        assert resultado == []

    def test_verso_sin_jerga(self, jerga_mini):
        j = cargar_jerga(jerga_mini)
        resultado = detectar_palabras_ambiguas(["llevo", "el", "rap", "conmigo"], j)
        assert resultado == []

    def test_varias_polisemicas(self, jerga_mini):
        j = cargar_jerga(jerga_mini)
        resultado = detectar_palabras_ambiguas(["mi", "parcero", "hace", "la", "vuelta"], j)
        assert len(resultado) == 2


class TestAnalizarAmbiguedadLexica:
    def test_informe_estructura(self, jerga_mini):
        j = cargar_jerga(jerga_mini)
        versos = [
            ["esa", "vuelta", "la", "cobro"],
            ["mi", "parcero", "me", "ayuda"],
        ]
        informe = analizar_ambiguedad_lexica(versos, j)
        assert len(informe) == 2
        assert informe[0]["palabra"] == "vuelta"
        assert informe[0]["verso_num"] == 1
        assert informe[1]["palabra"] == "parcero"
        assert informe[1]["verso_num"] == 2

    def test_sin_jerga_retorna_lista_vacia(self, jerga_mini):
        j = cargar_jerga(jerga_mini)
        versos = [["llevo", "el", "barrio"], ["en", "la", "sangre"]]
        # "barrio" es monosémica → no aparece en el informe
        informe = analizar_ambiguedad_lexica(versos, j)
        assert informe == []

    def test_verso_num_correcto(self, jerga_mini):
        j = cargar_jerga(jerga_mini)
        versos = [["sin", "jerga"], ["con", "vuelta"]]
        informe = analizar_ambiguedad_lexica(versos, j)
        assert informe[0]["verso_num"] == 2


class TestContextoPalabra:
    def test_ventana_centrada(self):
        palabras = ["esa", "vuelta", "la", "arreglo", "yo"]
        ctx = contexto_palabra(palabras, 1, ventana=2)
        assert "[vuelta]" in ctx
        assert "esa" in ctx
        assert "la" in ctx

    def test_primera_palabra(self):
        palabras = ["vuelta", "al", "barrio"]
        ctx = contexto_palabra(palabras, 0, ventana=2)
        assert ctx.startswith("[vuelta]")

    def test_ultima_palabra(self):
        palabras = ["lo", "hago", "por", "parcero"]
        ctx = contexto_palabra(palabras, 3, ventana=2)
        assert ctx.endswith("[parcero]")

    def test_ventana_uno(self):
        palabras = ["a", "b", "c", "d", "e"]
        ctx = contexto_palabra(palabras, 2, ventana=1)
        assert "b" in ctx
        assert "[c]" in ctx
        assert "d" in ctx
        assert "a" not in ctx
        assert "e" not in ctx


# ════════════════════════════════════════════════════════════════════════════ #
# 3. reporte.py
# ════════════════════════════════════════════════════════════════════════════ #

class TestReportarAmbiguedadEstructural:
    def test_sin_arboles(self):
        resultado = reportar_ambiguedad_estructural([], "clasica")
        assert "no se pudo" in resultado.lower()

    def test_un_arbol_sin_ambiguedad(self):
        nodo = _NodoStub("Cuarteto", ["A", "A", "B", "B"])
        resultado = reportar_ambiguedad_estructural([nodo], "clasica")
        assert "sin ambigüedad" in resultado.lower() or "única" in resultado.lower()

    def test_varios_arboles_con_ambiguedad(self):
        n1 = _NodoStub("Cuarteto", ["A", "A", "A", "A"])
        n2 = _NodoStub("DosPareados", ["A", "A", "B", "B"])
        resultado = reportar_ambiguedad_estructural([n1, n2], "clasica")
        assert "2" in resultado
        assert "Lectura 1" in resultado
        assert "Lectura 2" in resultado


class TestReportarAmbiguedadLexica:
    def test_sin_jerga_mensaje_negativo(self, jerga_mini):
        j = cargar_jerga(jerga_mini)
        versos = [["llevo", "el", "rap"]]
        resultado = reportar_ambiguedad_lexica(versos, j)
        assert "no se detectó" in resultado.lower()

    def test_con_jerga_muestra_acepciones(self, jerga_mini):
        j = cargar_jerga(jerga_mini)
        versos = [["esa", "vuelta", "la", "cobro", "yo"]]
        resultado = reportar_ambiguedad_lexica(versos, j)
        assert "vuelta" in resultado
        assert "2 lecturas" in resultado

    def test_contiene_region(self, jerga_mini):
        j = cargar_jerga(jerga_mini)
        versos = [["esa", "vuelta"]]
        resultado = reportar_ambiguedad_lexica(versos, j)
        assert "paisa" in resultado or "urbano" in resultado


class TestReporteCompleto:
    def test_contiene_ambas_secciones(self, jerga_mini):
        j = cargar_jerga(jerga_mini)
        nodo = _NodoStub("Cuarteto", ["A", "A", "B", "B"])
        versos = [["esa", "vuelta", "la", "cobro"]]
        resultado = reporte_completo([nodo], "clasica", versos, j)
        assert "estructural" in resultado.lower()
        assert "léxica" in resultado.lower() or "lexica" in resultado.lower()


# ════════════════════════════════════════════════════════════════════════════ #
# 4. Integración con el JSON real de data/
# ════════════════════════════════════════════════════════════════════════════ #

class TestJSONReal:
    def test_json_real_cargable(self):
        """El archivo data/jerga_colombiana.json existe y carga correctamente."""
        j = cargar_jerga()
        assert isinstance(j, dict)
        assert len(j) > 0

    def test_vuelta_polisemica_en_json_real(self):
        j = cargar_jerga()
        assert es_polisemica("vuelta", j)

    def test_parcero_polisemico_en_json_real(self):
        j = cargar_jerga()
        assert es_polisemica("parcero", j)

    def test_acepciones_tienen_campos_minimos(self):
        j = cargar_jerga()
        for palabra, entrada in j.items():
            for acep in entrada.get("acepciones", []):
                assert "id" in acep, f"Falta 'id' en {palabra}"
                assert "significado" in acep, f"Falta 'significado' en {palabra}"
                assert "region" in acep, f"Falta 'region' en {palabra}"
