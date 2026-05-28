# Tests — SpaceDementia

Tests unitarios de la lógica del juego, escritos con `pytest`.

## Cómo correrlos

Desde la raíz del proyecto (carpeta SpaceDementia):

```bash
python3 -m pytest tests/ -v
```

## Qué se prueba

- **test_scoreboard.py** — Tabla de puntajes: orden de mayor a menor,
  manejo case-insensitive de nombres (Tomas = TOMas), conservación del
  mejor puntaje, límite de top 10, claves combinadas para 2 jugadores y
  separación de las tablas 1j / 2j.
- **test_worlds.py** — Configuración de los 5 mundos: existencia de todos
  los mundos, fallback seguro ante ids inválidos, presencia de los campos
  que el juego espera y validez de los estilos de boss.

Estos tests cubren lógica pura (sin pygame), por lo que corren rápido y sin
necesitar entorno gráfico.
