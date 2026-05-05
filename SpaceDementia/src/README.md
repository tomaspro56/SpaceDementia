# src/ — Código fuente de SpaceDementia

## Archivos

| Archivo | Descripción |
|---------|-------------|
| `main.py` | Punto de entrada. Inicializa Pygame, carga assets, ejecuta el loop menú → juego |
| `game.py` | Controlador principal: estados, oleadas, colisiones, HUD, pausa |
| `player.py` | Clase Player: movimiento, power-ups, escudo, disparo, EMP |
| `enemy.py` | Clase Enemy: 4 tipos (normal, ágil, ráfaga, apuntador) con sprites animados |
| `boss.py` | Clase Boss: 3 fases con patrones de disparo y embestida |
| `bullet.py` | Clase Bullet: balas de jugador, enemigo y boss con sprites |
| `explosion.py` | Clase Explosion: animación de sprites de explosión (3 tamaños) |
| `obstaculo.py` | Anomalías: asteroides, agujero negro, interferencia, meteoros, EMP, inversión gravitacional |
| `tienda.py` | Tienda entre niveles: escudo, disparo doble/plasma, vida, bomba, revivir compañero |
| `menu.py` | Menú principal: 1 jugador, 2 jugadores, controles, salir |
| `background.py` | Fondo parallax con BG tileable, estrellas en 3 capas, planetas decorativos |
| `asset_loader.py` | Carga centralizada de todos los sprites del pack SpaceRage |
| `sound.py` | SoundManager: efectos de sonido y música de fondo con mute |
| `config.py` | Detección automática de resolución del monitor |
| `worlds.py` | Configuración de los 5 mundos: colores, enemigos, oleadas, bosses |
| `powerup.py` | Clase PowerUp: tipos, colores, símbolos |

## Arquitectura

El flujo principal es: `main.py` → `Menu` → `Game` → (loop de juego) → volver a `Menu`.

`Game` maneja estados: transición → jugando → completado → tienda → alerta → boss → game_over/victoria.

Cada módulo es independiente. `asset_loader.py` es el único que hace `pygame.image.load()`. `sound.py` es el único que toca `pygame.mixer`.
