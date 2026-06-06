# Proyecto-PLN — Analizador de letras de rap / música urbana

Sistema de Procesamiento de Lenguaje Natural, recibe la letra de una canción y analiza su estructura
métrica, esquema de rimas, ambigüedad estructural y lecturas léxicas alternativas.

El núcleo es una **Gramática de Contexto Libre (CFG)** con un **parser tipo Chart (Earley)**;
todo lo demás (tokenizador, silabeador, rimas, jerga, PCFG) alimenta o consume ese núcleo.

## Pipeline

```
Letra cruda
   │
   ▼
[1] Tokenizador (DFA) ──► tokens: palabra / contracción / signo / verso
   │
   ▼
[2] Silabeador ────────► sílabas + conteo métrico por verso (sinalefa + acento)
   │
   ▼
[3] Rima ──────────────► clave de rima por verso (consonante / asonante)
   │
   ▼
[4] CFG + Parser Chart ─► árbol(es) de derivación de la estrofa
   │
   ▼
[5] DCG + unificación ──► verifica que las rimas ligadas coincidan
   │
   ▼
[6] Ambigüedad ────────► derivaciones múltiples + lecturas léxicas (jerga)
   │
   ▼
[7] PCFG ──────────────► escoge la lectura métrica más probable + ranking
```

## Componentes

| Módulo               | Qué hace                                                              | Herramienta formal        |
|----------------------|----------------------------------------------------------------------|---------------------------|
| `src/tokenizer/`     | Separa palabras, contracciones del habla (`pa'`, `to`, `ke`) — incluido el apócope general con apóstrofo final (`má'`, `lo'`, `pistola'`) —, signos, números y versos. | Autómata finito (DFA) |
| `src/silabeo/`       | Divide en sílabas (diptongos/hiatos), detecta tonicidad y cuenta sílabas métricas con sinalefa y ajuste por acento final. | Autómata silábico |
| `src/rima/`          | Normaliza fonémicamente y extrae la terminación desde la última vocal tónica → clave de rima. | Transcripción fonética |
| `src/gramatica/`     | CFG de formas métricas (pareado, cuarteto, terceto, redondilla, estrofa libre) + parser tipo Chart y árbol de derivación. | **CFG + Parser Chart** |
| `src/unificacion/`   | Liga las variables de rima `[A]`, `[B]` a las terminaciones reales y rechaza esquemas inconsistentes. | DCG / unificación |
| `src/ambiguedad/`    | Reporta ambigüedad estructural (cuarteto AAAA vs dos pareados AA-AA) y léxica (jerga colombiana polisémica). | Manejo de ambigüedad |
| `src/pcfg/`          | Asigna probabilidades a las producciones y elige el esquema métrico más plausible. | PCFG |

## Cómo correr

Desde la raíz del proyecto (`Proyecto-PLN/`):

```bash
python main.py                 # analiza todas las letras de data/
python main.py letra.txt       # analiza una letra desde un archivo
python main.py -               # lee la letra desde la entrada estándar (teclear/pegar)
python main.py --detalle       # salida completa fase por fase (árbol, DCG, PCFG)
```

Los versos se separan por `/` o por salto de línea; las **estrofas** se separan
por una línea en blanco. El pipeline analiza cada estrofa por separado (las
etiquetas de rima reinician en `A` en cada una), de modo que los cuartetos y
pareados reales coinciden con la CFG en vez de colapsar en una única estrofa
libre que abarque toda la canción.

Para cada estrofa se prueba primero la rima **consonante**; si no encaja en
ninguna forma clásica, se reintenta en **asonante** y se usa esa lectura cuando
revela estructura (útil en letras de rima mayormente asonante, como mucho rap).

### Probar una letra nueva (entrada en vivo)

Para analizar una letra que **no** esté en `data/`, hay tres formas:

1. **Pegar o escribir** la letra por entrada estándar:
   ```bash
   python main.py -
   ```
   Pega la letra y termina la entrada con `Ctrl+Z` + `Enter` (Windows) o `Ctrl+D` (Linux/Mac).

2. **Desde un archivo** de texto UTF-8:
   ```bash
   python main.py mi_letra.txt
   ```

3. **Agregándola al corpus**: guárdala como `data/nombre.txt` y `python main.py` (sin argumentos) la incluirá junto a las demás.


El reporte por defecto es **conciso** (un bloque por estrofa + resumen). Añade
`--detalle` / `-d` para ver el árbol de derivación, la unificación DCG y el
ranking PCFG completos.

### Pruebas

Cada módulo tiene su propio archivo de pruebas autoejecutable (solo librería estándar):

```bash
python tests/test_basico.py        # tokenizador + silabeo
python tests/test_segmentacion.py  # segmentación en estrofas
python tests/test_gramatica.py     # CFG + parser Chart
python tests/test_unificacion.py   # DCG + unificación de rimas
python tests/test_ambiguedad.py    # ambigüedad estructural + léxica
python tests/test_pcfg.py          # PCFG + desambiguación probabilística
```

## Estructura

```
Proyecto-PLN/
├── README.md
├── main.py                  # CLI / orquestador del pipeline completo
├── src/
│   ├── tokenizer/           # motor DFA + tokenizador
│   ├── silabeo/             # silabeador + conteo métrico
│   ├── rima/                # terminación fonémica y clave de rima
│   ├── gramatica/           # CFG + parser tipo Chart (Earley) + árbol de derivación
│   ├── unificacion/         # DCG: liga variables de rima a las terminaciones reales
│   ├── ambiguedad/          # ambigüedad estructural y léxica (jerga colombiana)
│   └── pcfg/                # PCFG: desambiguación probabilística
├── data/
│   ├── jerga_colombiana.json
│   ├── falsedades.txt
│   ├── manicomio_527.txt
│   ├── querer_querernos.txt
│   ├── bandido.txt
│   └── la_maza.txt
└── tests/
    ├── test_basico.py
    ├── test_segmentacion.py
    ├── test_gramatica.py
    ├── test_unificacion.py
    ├── test_ambiguedad.py
    └── test_pcfg.py
```


