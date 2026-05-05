# SpaceDementia - Arcade Shooter (Pygame)

## Qué es
Juego arcade retro horizontal tipo shoot'em up hecho con Python y Pygame. El jugador controla una nave en el lado izquierdo y dispara hacia enemigos que vienen desde la derecha. Proyecto universitario del curso de Lógica de Programación en el ITM (Medellín).

## Contexto
El juego fue creado por el profesor (Juan Navarro). La tarea es mejorarlo libremente: agregar features, mejorar mecánicas, pulir visuales, refactorizar código, etc.

## Stack
- Python 3.11+ con Pygame 2.6+
- Gestión de dependencias: Poetry
- Sin assets externos (todo se dibuja con primitivas de Pygame)
- Resolución: 1920x1200 a 30 FPS

## Arquitectura (8 archivos en src/)
```
main.py       → Punto de entrada, inicializa Pygame y lanza Game
config.py     → Constantes: WIDTH=1920, HEIGHT=1200, colores RGB
game.py       → Clase Game: loop principal, spawn, colisiones, estado, render
player.py     → Clase Player: movimiento 4-dir, sistema de powerups (dict con contadores)
enemy.py      → Clase Enemy: normal (rojo, lineal) y ágil (amarillo, zigzag)
bullet.py     → Clase Bullet: 6 direcciones, animación retro pulsante en RIGHT
powerup.py    → Clase PowerUp: 6 tipos de arma + LIFE, movimiento sinusoidal
explosion.py  → Clase Explosion: partículas sin física, fade progresivo
background.py → Clase Background: capas parallax que escalan con el nivel
```

## Mecánicas clave
- Niveles: sube cada 100 puntos (score se resetea), aumenta enemigos y velocidad
- Power-ups: estrellas flotantes, 50% chance al matar enemigo, auto-disparo cada 10 frames
- Colisiones: AABB simple con `check_collision()` y `check_attack()`
- Al recibir daño: pierde power-up aleatorio antes de perder vida
- WEAPON_RIGHT stackea hasta 5, WEAPON_LEFT hasta 3, el resto máximo 1

## Controles
- Flechas: mover nave
- Espacio: disparar
- P: pausar
- Q / ESC: salir

## Reglas para Claude
- Responder siempre en español
- Comentarios en el código en español
- Seguir PEP 8
- Mantener la estructura modular actual (una clase por archivo)
- No agregar assets externos (sprites, imágenes, sonidos) a menos que se pida explícitamente
- Al proponer mejoras, explicar brevemente qué cambia y por qué
- Testear mentalmente que los cambios no rompan el loop de juego en game.py

## Ideas de mejora pendientes
<!-- Agregar aquí las mejoras que vayas trabajando -->
- [ ] Mejorar el sprite del jugador (actualmente es un círculo azul)
- [ ] Sistema de sonido
- [ ] Pantalla de inicio / menú
- [ ] High scores persistentes
- [ ] Nuevos tipos de enemigos (jefes)
- [ ] Screen shake al recibir daño
- [ ] Partículas mejoradas en explosiones
