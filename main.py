"""
Analizador de letras de rap / música urbana colombiana — CLI.

Pipeline:
    [1] Tokenización con DFA
    [2] Silabeo + conteo métrico de versos (sinalefa + acento final)
    [3] Rima: terminación fonémica y secuencia simbólica de rima
    [4] CFG + parser tipo Chart (Earley): estructura métrica y ambigüedad
    [5] DCG + unificación: verifica que las rimas reales sean consistentes
    [6] Ambigüedad estructural (cuarteto vs dos pareados) y léxica (jerga)
    [7] PCFG: elige el esquema métrico más probable y reporta el ranking

Uso:
    python main.py                 # corre con la letra de demostración
    python main.py archivo.txt     # analiza la letra contenida en un archivo
    python main.py -               # lee la letra desde la entrada estándar

Versos:   se separan por '/' o por salto de línea simple.
Estrofas: se separan por una línea en blanco.
"""

from __future__ import annotations

import glob
import os
import sys

# Fuerza UTF-8 en la consola de Windows (evita UnicodeEncodeError con ═, →, etc.)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.tokenizer import Tokenizador
from src.silabeo import silabas, contar_silabas_verso
from src.gramatica import (
    gramatica, gramatica_con_libre,
    analizar_con_fallback, nombre_esquema,
    descripcion_formal,
)
from src.rima import secuencia_rimas, describir_esquema
from src.unificacion import verificar_esquema, filtrar_arboles_validos
from src.ambiguedad import (
    reportar_ambiguedad_estructural,
    reportar_ambiguedad_lexica,
)
from src.pcfg import (
    reporte_ranking,
    reporte_desglose_ganador,
)

#Para empezar xd
LETRA_DEMO = (
    "Llevo el barrio en la sangre, lo respiro al andar / "
    "cada esquina me canta, cada calle es mi hogar / "
    "llevo tu nombre grabado dentro del corazón / "
    "y cada verso que escribo vibra con tu razón"
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


def mostrar_metrica(versos):
    print()
    print(_linea("═"))
    print(" FASE 2 · MÉTRICA (silabeo + sinalefa + acento)")
    print(_linea("═"))

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


MODOS_RIMA = ("consonante", "asonante")


def elegir_analisis_rima(versos_palabras):
    """Prueba primero rima CONSONANTE; si la estrofa no encaja en ninguna forma
    clásica de la CFG, reintenta con rima ASONANTE y usa esa lectura si revela
    una estructura clásica. Prefiere consonante (más estricta) y solo recurre a
    asonante cuando aporta estructura — útil en letras de rima mayormente asonante
    (mucho rap/balada). Devuelve (etiquetas, mapa, arboles, modo_gramatica, modo_rima)."""
    respaldo = None
    for modo_rima in MODOS_RIMA:
        etiquetas, mapa = secuencia_rimas(versos_palabras, modo=modo_rima)
        arboles, modo_gram = analizar_con_fallback(etiquetas, gramatica, gramatica_con_libre)
        if modo_gram == "clasica":
            return etiquetas, mapa, arboles, modo_gram, modo_rima
        if respaldo is None:                       # guarda la lectura consonante
            respaldo = (etiquetas, mapa, arboles, modo_gram, modo_rima)
    return respaldo


def mostrar_estructura(versos):
    print()
    print(_linea("═"))
    print(" FASE 3 · ESTRUCTURA MÉTRICA (CFG + Parser)")
    print(_linea("═"))

    versos_palabras = [
        [t.texto for t in v if t.tipo in ("PALABRA", "CONTRACCION")]
        for v in versos
    ]

    etiquetas, mapa, arboles, modo, modo_rima = elegir_analisis_rima(versos_palabras)
    print(f"\n Rima evaluada: {modo_rima}")
    print(f" {describir_esquema(etiquetas, mapa)}")

    if not arboles:
        print(" -> No se pudo reconocer ninguna estructura.")
        return None

    if modo == 'clasica' and len(arboles) > 1:
        print(f"\n AMBIGÜEDAD ESTRUCTURAL: {len(arboles)} lecturas posibles")
        for i, a in enumerate(arboles, 1):
            print(f"   Lectura {i}: {nombre_esquema(a)}")
    else:
        print(f"\n Estructura detectada: {nombre_esquema(arboles[0])}")
        print("\n Árbol de derivación:")
        for linea in arboles[0].mostrar().split("\n"):
            if linea.strip():
                print(f"   {linea}")

    return versos_palabras, etiquetas, arboles, modo, modo_rima


def mostrar_verificacion_rima(versos_palabras, etiquetas, arboles, modo_rima):
    """Fase 5: verifica con DCG + unificación que las rimas reales sean
    consistentes con el esquema que propuso la CFG, en el mismo modo de rima
    (consonante o asonante) que se usó para detectar la estructura."""
    print()
    print(_linea("═"))
    print(" FASE 5 · VERIFICACIÓN DE RIMAS (DCG + unificación)")
    print(_linea("═"))

    # Verificación detallada del esquema observado.
    resultado = verificar_esquema(etiquetas, versos_palabras,
                                  modo=modo_rima, detalle=True)

    print("\n Unificación de variables de rima:")
    for paso in resultado["traza"]:
        print(f"   {paso}")

    if resultado["valido"]:
        ligaduras = "  ".join(f"[{k}]=-{v}" for k, v in resultado["ligaduras"].items())
        print(f"\n ✓ Esquema CONSISTENTE.  Ligaduras: {ligaduras}")
    else:
        print(f"\n ✗ Esquema INCONSISTENTE.  {resultado['motivo']}")

    # Filtra los árboles de la CFG que sobreviven a la verificación.
    if arboles:
        validos = filtrar_arboles_validos(arboles, versos_palabras, modo=modo_rima)
        print(f"\n Árboles que pasan la verificación DCG: {len(validos)}/{len(arboles)}")
        for a in validos:
            print(f"   ✓ {nombre_esquema(a)}")


def mostrar_ambiguedad(versos_palabras, arboles, modo):
    """Fase 6: reporta ambigüedad ESTRUCTURAL (cuarteto vs dos pareados)
    y LÉXICA (jerga colombiana polisémica como 'vuelta', 'parcero', ...)."""
    print()
    print(_linea("═"))
    print(" FASE 6 · MANEJO DE AMBIGÜEDAD")
    print(_linea("═"))

    print("\n ── Ambigüedad estructural ──")
    print(reportar_ambiguedad_estructural(arboles, modo))

    print("\n ── Ambigüedad léxica (jerga colombiana) ──")
    print(reportar_ambiguedad_lexica(versos_palabras))


def mostrar_pcfg(arboles):
    """Fase 7: asigna probabilidades a cada árbol y elige el más plausible."""
    print()
    print(_linea("═"))
    print(" FASE 7 · DESAMBIGUACIÓN PROBABILÍSTICA (PCFG)")
    print(_linea("═"))

    if not arboles:
        print(" (no hay árboles para evaluar con la PCFG)")
        return

    print()
    print(reporte_ranking(arboles))

    if len(arboles) > 1:
        print()
        print(reporte_desglose_ganador(arboles))


DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def cargar_texto(argv):
    """Lee la letra desde un archivo (argv[1]) o desde stdin (argv[1] == '-')."""
    if argv[1] == "-":
        return sys.stdin.read()
    with open(argv[1], "r", encoding="utf-8") as f:
        return f.read()


def listar_canciones():
    """Rutas de las letras en data/, ordenadas por nombre."""
    return sorted(glob.glob(os.path.join(DATA_DIR, "*.txt")))


def titulo_desde_ruta(ruta):
    """'data/manicomio_527.txt' -> 'Manicomio 527'."""
    nombre = os.path.splitext(os.path.basename(ruta))[0]
    return nombre.replace("_", " ").title()


def analizar_letra(tokenizador, texto, titulo=None):
    """Corre el pipeline completo sobre una letra, analizándola ESTROFA POR ESTROFA.

    La tokenización (Fase 1) se hace sobre toda la letra; el resto del pipeline
    (métrica, CFG, DCG, ambigüedad, PCFG) se aplica a cada estrofa por separado.
    Así las etiquetas de rima reinician en A en cada estrofa y los cuartetos /
    pareados reales pueden coincidir con la CFG (en vez de colapsar en una única
    estrofa libre que abarca toda la canción)."""
    print()
    if titulo:
        print(_linea("█"))
        print(f" ♪  {titulo}")
        print(_linea("█"))
    print(" Letra analizada:")
    print(f"   {texto.strip()}\n")

    tokens = mostrar_tokens(tokenizador, texto)

    estrofas = tokenizador.separar_estrofas(tokens)
    print()
    print(f" Se detectaron {len(estrofas)} estrofa(s) (separadas por línea en blanco).")

    for n, versos in enumerate(estrofas, start=1):
        print()
        print(_linea("▒"))
        print(f" ▶ ESTROFA {n}  ({len(versos)} verso(s))")
        print(_linea("▒"))

        mostrar_metrica(versos)
        resultado = mostrar_estructura(versos)
        if resultado:
            versos_palabras, etiquetas, arboles, modo, modo_rima = resultado
            mostrar_verificacion_rima(versos_palabras, etiquetas, arboles, modo_rima)
            mostrar_ambiguedad(versos_palabras, arboles, modo)
            mostrar_pcfg(arboles)
    print()


def main(argv=None):
    argv = argv if argv is not None else sys.argv
    tokenizador = Tokenizador()

    # Con argumento (archivo o '-'): analiza esa única letra.
    if len(argv) >= 2:
        analizar_letra(tokenizador, cargar_texto(argv))
        return

    # Sin argumentos: analiza todas las canciones de data/, una tras otra.
    canciones = listar_canciones()
    if not canciones:
        analizar_letra(tokenizador, LETRA_DEMO, "Letra demo")
        return

    for ruta in canciones:
        with open(ruta, "r", encoding="utf-8") as f:
            texto = f.read()
        analizar_letra(tokenizador, texto, titulo_desde_ruta(ruta))


if __name__ == "__main__":
    main()
