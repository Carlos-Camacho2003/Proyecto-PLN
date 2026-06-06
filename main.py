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
    python main.py                 # reporte conciso de todas las letras de data/
    python main.py archivo.txt     # analiza la letra contenida en un archivo
    python main.py -               # lee la letra desde la entrada estándar
    python main.py --detalle       # salida completa fase por fase (árbol, DCG, PCFG)

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
from src.unificacion import verificar_esquema, filtrar_hipotesis
from src.ambiguedad import (
    reportar_ambiguedad_estructural,
    reportar_ambiguedad_lexica,
    analizar_ambiguedad_lexica,
)
from src.pcfg import (
    mejor_arbol,
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
    print(" TOKENIZACIÓN (DFA)")
    print(_linea("═"))
    tokens = tokenizador.tokenizar(texto)
    visibles = [t for t in tokens if t.tipo != "ESPACIO"]

    # Resumen por tipo en vez de listar cada token.
    conteo = {}
    for t in visibles:
        conteo[t.tipo] = conteo.get(t.tipo, 0) + 1

    nombres = {
        "PALABRA": "palabras", "CONTRACCION": "contracciones", "NUMERO": "números",
        "SIGNO": "signos", "VERSO_SEP": "separadores de verso", "NEWLINE": "saltos de línea",
    }
    resumen = "  ".join(
        f"{conteo[tipo]} {nombres.get(tipo, tipo.lower())}"
        for tipo in ("PALABRA", "CONTRACCION", "NUMERO", "SIGNO", "VERSO_SEP", "NEWLINE")
        if conteo.get(tipo)
    )
    print(f" {len(visibles)} tokens (sin espacios): {resumen}")

    # Detalle solo de lo que el DFA detecta de forma interesante.
    contracciones = sorted({t.texto.lower() for t in visibles if t.tipo == "CONTRACCION"})
    if contracciones:
        print(f"   ★ contracciones del habla: {', '.join(contracciones)}")
    numeros = [t.texto for t in visibles if t.tipo == "NUMERO"]
    if numeros:
        print(f"   # números: {', '.join(numeros)}")

    return tokens


def mostrar_metrica(versos):
    print()
    print(_linea("═"))
    print(" MÉTRICA (silabeo + sinalefa + acento)")
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
    print(" ESTRUCTURA MÉTRICA (CFG + Parser)")
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


def mostrar_verificacion_rima(versos_palabras, etiquetas, modo_rima):
    """Fase 5: verifica con DCG + unificación que las rimas reales sean
    consistentes con el esquema que propuso la CFG, en el mismo modo de rima
    (consonante o asonante) que se usó para detectar la estructura."""
    print()
    print(_linea("═"))
    print(" VERIFICACIÓN DE RIMAS (DCG + unificación)")
    print(_linea("═"))

    # Verificación detallada del esquema observado.
    resultado = verificar_esquema(etiquetas, versos_palabras,
                                  modo=modo_rima, detalle=True)

    print("\n Unificación de variables de rima (esquema observado):")
    for paso in resultado["traza"]:
        print(f"   {paso}")

    if resultado["valido"]:
        ligaduras = "  ".join(f"[{k}]=-{v}" for k, v in resultado["ligaduras"].items())
        print(f"\n ✓ Esquema CONSISTENTE.  Ligaduras: {ligaduras}")
    else:
        print(f"\n ✗ Esquema INCONSISTENTE.  {resultado['motivo']}")

    # Prueba de hipótesis: la CFG propone TODOS los esquemas clásicos posibles
    # para esta estrofa y la DCG rechaza los que no unifican con las rimas reales.
    consistentes, rechazados = filtrar_hipotesis(versos_palabras, gramatica, modo=modo_rima)
    if consistentes or rechazados:
        print("\n Hipótesis de esquema (la DCG unifica cada una contra las rimas reales):")
        for _, esquema, _ in consistentes:
            print(f"   ✓ {esquema}: CONSISTENTE")
        for _, esquema, res in rechazados:
            print(f"   ✗ {esquema}: RECHAZADO — {res['motivo']}")
        if not consistentes:
            print("   → Ninguna hipótesis clásica unifica → la estrofa es libre.")


def mostrar_ambiguedad(versos_palabras, arboles, modo):
    """Fase 6: reporta ambigüedad ESTRUCTURAL (cuarteto vs dos pareados)
    y LÉXICA (jerga colombiana polisémica como 'vuelta', 'parcero', ...)."""
    print()
    print(_linea("═"))
    print(" MANEJO DE AMBIGÜEDAD")
    print(_linea("═"))

    print("\n ── Ambigüedad estructural ──")
    print(reportar_ambiguedad_estructural(arboles, modo))

    print("\n ── Ambigüedad léxica (jerga colombiana) ──")
    print(reportar_ambiguedad_lexica(versos_palabras))


def mostrar_pcfg(arboles):
    """Fase 7: asigna probabilidades a cada árbol y elige el más plausible."""
    print()
    print(_linea("═"))
    print(" DESAMBIGUACIÓN PROBABILÍSTICA (PCFG)")
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


# --------------------------------------------------------------------------- #
# Reporte CONCISO (modo por defecto): un bloque corto por estrofa + resumen.
# --------------------------------------------------------------------------- #
def datos_estrofa(versos):
    """Analiza una estrofa y devuelve sus hallazgos como dict (sin imprimir)."""
    versos_palabras = [
        [t.texto for t in v if t.tipo in ("PALABRA", "CONTRACCION")] for v in versos
    ]
    _, _, arboles, modo_gram, modo_rima = elegir_analisis_rima(versos_palabras)

    silabas = [
        contar_silabas_verso([t.texto for t in v
                              if t.tipo in ("PALABRA", "CONTRACCION", "NUMERO")])
        for v in versos
    ]

    ambigua = (modo_gram == "clasica" and len(arboles) > 1)
    if not arboles:
        estructura, lecturas = "(no reconocida)", []
    elif ambigua:
        estructura = nombre_esquema(mejor_arbol(arboles))
        lecturas = [nombre_esquema(a) for a in arboles]
    else:
        estructura, lecturas = nombre_esquema(arboles[0]), []

    jerga = sorted({d["palabra"].lower() for d in analizar_ambiguedad_lexica(versos_palabras)})

    return {
        "n_versos": len(versos), "silabas": silabas, "modo_rima": modo_rima,
        "estructura": estructura, "ambigua": ambigua, "lecturas": lecturas,
        "jerga": jerga,
    }


def imprimir_estrofa_breve(n, d):
    silabas = "·".join(str(s) for s in d["silabas"])
    print(f"\n ▶ Estrofa {n} ({d['n_versos']}v) · {silabas} síl · rima {d['modo_rima']}")
    if d["ambigua"]:
        print(f"     CFG: ambigua → {' / '.join(d['lecturas'])}")
        print(f"     PCFG elige: {d['estructura']}")
    else:
        print(f"     CFG: {d['estructura']}")
    if d["jerga"]:
        print(f"     jerga: {', '.join(d['jerga'])}")


def imprimir_resumen(titulo, hallazgos):
    print()
    print(_linea("═"))
    print(f" RESUMEN · {titulo}")
    print(_linea("═"))
    if not hallazgos:
        print(" (sin estrofas)")
        return

    formas = {}
    for d in hallazgos:
        clave = "Estrofa libre" if d["estructura"].startswith("Estrofa libre") else d["estructura"]
        formas[clave] = formas.get(clave, 0) + 1
    formas_str = ", ".join(f"{c}× {f}" for f, c in sorted(formas.items(), key=lambda kv: -kv[1]))
    print(f" {len(hallazgos)} estrofa(s):  {formas_str}")

    n_amb = sum(1 for d in hallazgos if d["ambigua"])
    if n_amb:
        print(f" Ambigüedad estructural: {n_amb} estrofa(s) desambiguada(s) por la PCFG")

    cons = sum(1 for d in hallazgos if d["modo_rima"] == "consonante")
    print(f" Rima: {cons} consonante · {len(hallazgos) - cons} asonante")

    silabas = [s for d in hallazgos for s in d["silabas"]]
    if silabas:
        print(f" Métrica: versos de {min(silabas)} a {max(silabas)} sílabas")

    jerga = sorted({w for d in hallazgos for w in d["jerga"]})
    if jerga:
        print(f" Jerga polisémica: {', '.join(jerga)}")


def analizar_letra(tokenizador, texto, titulo=None, detalle=False):
    """Corre el pipeline sobre una letra, estrofa por estrofa.

    Por defecto imprime un REPORTE CONCISO (un bloque por estrofa con los
    hallazgos relevantes + un resumen final). Con `detalle=True` despliega la
    salida completa fase por fase (tokens, métrica, árbol de derivación,
    unificación DCG, ambigüedad y PCFG)."""
    print()
    if titulo:
        print(_linea("█"))
        print(f" ♪  {titulo}")
        print(_linea("█"))
    print(" Letra:")
    for linea in texto.strip("\n").split("\n"):
        print(f"   {linea}" if linea.strip() else "")
    print()

    tokens = mostrar_tokens(tokenizador, texto)
    estrofas = tokenizador.separar_estrofas(tokens)
    print(f"\n {len(estrofas)} estrofa(s) (separadas por línea en blanco).")

    hallazgos = []
    for n, versos in enumerate(estrofas, start=1):
        d = datos_estrofa(versos)
        if detalle:
            print()
            print(_linea("▒"))
            print(f" ▶ ESTROFA {n}  ({len(versos)} verso(s))")
            print(_linea("▒"))
            mostrar_metrica(versos)
            resultado = mostrar_estructura(versos)
            if resultado:
                versos_palabras, etiquetas, arboles, modo, modo_rima = resultado
                mostrar_verificacion_rima(versos_palabras, etiquetas, modo_rima)
                mostrar_ambiguedad(versos_palabras, arboles, modo)
                mostrar_pcfg(arboles)
        else:
            imprimir_estrofa_breve(n, d)
        hallazgos.append(d)

    imprimir_resumen(titulo or "la letra", hallazgos)


def main(argv=None):
    argv = list(argv if argv is not None else sys.argv)

    # Flag opcional: --detalle / -d despliega la salida completa por fases.
    detalle = False
    for flag in ("--detalle", "-d"):
        while flag in argv:
            argv.remove(flag)
            detalle = True

    tokenizador = Tokenizador()

    # Con argumento (archivo o '-'): analiza esa única letra.
    if len(argv) >= 2:
        titulo = titulo_desde_ruta(argv[1]) if argv[1] != "-" else None
        analizar_letra(tokenizador, cargar_texto(argv), titulo=titulo, detalle=detalle)
        return

    # Sin argumentos: analiza todas las canciones de data/, una tras otra.
    canciones = listar_canciones()
    if not canciones:
        analizar_letra(tokenizador, LETRA_DEMO, "Letra demo", detalle=detalle)
        return

    for ruta in canciones:
        with open(ruta, "r", encoding="utf-8") as f:
            texto = f.read()
        analizar_letra(tokenizador, texto, titulo_desde_ruta(ruta), detalle=detalle)


if __name__ == "__main__":
    main()
