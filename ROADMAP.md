# Roadmap — Analizador de Letras de Rap / Música Urbana Colombiana

Sistema de PLN en español, construido **desde cero en Python** (sin librerías de NLP).
Entrada: la letra de una canción. Salida: estructura métrica, esquema de rimas, figuras
retóricas estructurales y lecturas alternativas ante ambigüedad.

---

## 1. Objetivo y requisito obligatorio

El núcleo del sistema es una **Gramática de Contexto Libre (CFG)** que modela las formas
métricas (cuarteto, redondilla, pareado, estrofa libre) y un **parser tipo Chart** que la
analiza. Todo lo demás (tokenizador, silabeador, rimas, jerga, PCFG) alimenta o consume ese
núcleo.

---

## 2. Mapeo: herramienta del curso → componente del sistema

| Herramienta del curso        | Componente en el proyecto                                          | Fase |
|------------------------------|--------------------------------------------------------------------|------|
| Autómata finito (DFA/AFN)    | Tokenizador léxico: palabras, signos, contracciones (pa, to, ke)   | 1    |
| Gramática regular            | Definición formal del vocabulario / clases de token                | 1    |
| (Autómata silábico)          | Silabeador del español (diptongos, hiatos, conteo de sílabas)      | 2    |
| Transcripción fonética       | Rimas: terminación fonémica desde la última vocal tónica           | 3    |
| **CFG** *(obligatorio)*      | **Formas métricas como producciones (estrofa → versos → rima)**    | 4    |
| **Parser Chart** *(oblig.)*  | **Análisis y validación de la estructura métrica**                 | 4    |
| Árbol de derivación          | Representación explícita de la estrofa analizada                   | 4    |
| DCG / unificación            | Liga variables de rima [A],[B] a secuencias fonémicas reales       | 5    |
| Manejo de ambigüedad         | Derivaciones múltiples (AAAA vs AA-AA) + lecturas léxicas (jerga)  | 6    |
| PCFG                         | Desambiguación: elige el esquema métrico más probable              | 7    |

---

## 3. Arquitectura (pipeline)

```
Letra cruda
   │
   ▼
[1] Tokenizador DFA ──► tokens (palabra / contracción / signo)
   │
   ▼
[2] Silabeador ──────► sílabas + conteo por verso (con sinalefa)
   │
   ▼
[3] Fonética/Rima ───► clave de rima por verso (consonante / asonante)
   │
   ▼
[4] CFG + Chart ─────► árbol(es) de derivación de la estrofa
   │
   ▼
[5] DCG/unificación ─► verifica que las rimas ligadas coincidan
   │
   ▼
[6] Ambigüedad ──────► expone derivaciones y lecturas alternativas
   │
   ▼
[7] PCFG ────────────► escoge la lectura métrica más probable
```

---

## 4. Fases — de lo más sencillo a lo más complejo

### Fase 1 — Tokenizador DFA  ← *EMPEZAMOS AQUÍ*
- Motor DFA genérico desde cero (estados, transiciones, aceptación).
- Tokenizador que separa: palabras, contracciones del habla (pa, to, pa', ke, q), signos,
  saltos de verso (`/` o salto de línea), espacios.
- **Entregable:** `src/tokenizer/` + demo en consola que imprime la lista de tokens.

### Fase 2 — Silabeador del español
- Reglas: vocales abiertas/cerradas, diptongos, triptongos, hiatos, grupos consonánticos
  inseparables (pr, tr, bl, ll, ch, rr…).
- Conteo silábico por verso. Ajuste métrico por terminación (aguda +1 / esdrújula −1).
- **Entregable:** conteo de sílabas correcto en los alejandrinos del Ejemplo 1.

### Fase 3 — Rima (fonética ligera)
- Normalización fonémica (c/qu/k → /k/, b/v → /b/, h muda, etc.).
- Terminación desde la última vocal tónica → clave de rima.
- Consonante (coincide todo) vs asonante (solo vocales).
- **Entregable:** detectar rima AA en "andar / hogar".

### Fase 4 — CFG + Parser Chart  *(núcleo obligatorio)*
- CFG con producciones para: pareado (AA), cuarteto (ABAB/AABB/ABBA), redondilla, terceto,
  estrofa libre.
- Parser tipo Chart (Earley) construido desde cero; soporta ambigüedad de forma nativa.
- **Entregable:** árbol(es) de derivación de una estrofa de 4 versos.

### Fase 5 — DCG / unificación de rimas
- Variables lógicas [A], [B] que se unifican con la clave de rima real de cada verso.
- Verifica que el esquema propuesto por la CFG sea consistente con las rimas observadas.
- **Entregable:** rechaza AAAA si los versos no riman entre sí; acepta el esquema correcto.

### Fase 6 — Manejo de ambigüedad
- Estructural: cuarteto monorrimo AAAA vs dos pareados AA-AA (Ejemplo 2) → muestra ambas.
- Léxica: diccionario de jerga colombiana polisémica ("vuelta" = encargo paisa / venganza
  urbana) (Ejemplo 3) → reporta ambas acepciones con su contexto.
- **Entregable:** salida con todas las derivaciones/lecturas válidas.

### Fase 7 — PCFG (desambiguación probabilística)
- Probabilidades en las producciones de la CFG.
- Ante varias derivaciones válidas, escoge la de mayor probabilidad y reporta el ranking.
- **Entregable:** elige el esquema métrico más plausible del Ejemplo 2.

### Fase 8 — Integración CLI + informe
- `main.py` orquesta el pipeline completo y produce un informe legible por la consola
  (versos, sílabas, esquema de rima, figuras, lecturas alternativas).
- Pruebas con los tres ejemplos del enunciado + casos extra.

---

## 5. Estructura de carpetas

```
Proyecto-PLN/
├── README.md
├── ROADMAP.md
├── main.py                  # CLI / orquestador del pipeline
├── src/
│   ├── tokenizer/           # Fase 1: DFA + tokenizador
│   ├── silabeo/             # Fase 2
│   ├── rima/                # Fase 3
│   ├── gramatica/           # Fase 4: CFG + Chart parser
│   ├── unificacion/         # Fase 5: DCG
│   ├── ambiguedad/          # Fase 6
│   └── pcfg/                # Fase 7
├── data/
│   └── jerga_colombiana.json
└── tests/
```

---

## 6. Principios

- **Todo desde cero:** sin NLTK, spaCy ni similares. Solo la librería estándar de Python.
- **Incremental y verificable:** cada fase tiene un entregable comprobable con un ejemplo.
- **Trazable al curso:** cada módulo nombra explícitamente la herramienta formal que aplica.

---

## 7. Estado actual

- [x] Fase 0 — Roadmap y estructura del proyecto
- [ ] **Fase 1 — Tokenizador DFA** *(en progreso)*
- [ ] Fase 2 — Silabeador
- [ ] Fase 3 — Rima
- [ ] Fase 4 — CFG + Chart parser *(núcleo)*
- [ ] Fase 5 — DCG / unificación
- [ ] Fase 6 — Ambigüedad
- [ ] Fase 7 — PCFG
- [ ] Fase 8 — Integración CLI
