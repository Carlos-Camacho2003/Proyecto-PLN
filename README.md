# Proyecto-PLN — Analizador de letras de rap / música urbana colombiana

Sistema de Procesamiento de Lenguaje Natural que recibe la letra de una canción y analiza su
estructura métrica, esquema de rimas, figuras retóricas y lecturas alternativas.


## Estado actual

- **Fase 1 — Tokenizador (DFA):** `src/tokenizer/` — separa palabras, signos,
  números, contracciones del habla (`pa'`, `to`, `ke`) y versos.
- **Fase 2 — Silabeador y métrica:** `src/silabeo/` — divide en sílabas
  (diptongos/hiatos), detecta tonicidad (aguda/llana/esdrújula) y cuenta sílabas
  métricas con sinalefa y ajuste por acento final.

## Cómo correr

Desde la raíz del proyecto (`Proyecto-PLN/`):

```bash
python main.py                 # corre con la letra de demostración
python main.py letra.txt       # analiza una letra desde un archivo
python tests/test_basico.py    # ejecuta las pruebas
```

## Estructura

```
Proyecto-PLN/
├── main.py                 # CLI / orquestador del pipeline             # plan por fases
├── src/
│   ├── tokenizer/          # Fase 1: motor DFA + tokenizador
│   └── silabeo/            # Fase 2: silabeador + conteo métrico
└── tests/
    └── test_basico.py      # pruebas de las fases 1 y 2
```
