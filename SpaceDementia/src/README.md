# src/ — Código fuente de SpaceDementia

## Archivos

| Archivo | Descripción |
|---------|-------------|
| `main.py` | Punto de entrada. Inicializa Pygame en modo FULLSCREEN+SCALED, setea dimensiones en config, carga assets y ejecuta el loop menú → juego |
| `game.py` | Controlador principal: estados (transición/jugando/completado/tienda/alerta/boss/game_over/victoria), oleadas, colisiones, HUD, pausa, screen shake |
| `player.py` | Clase Player: movimiento, escudo (temporal y permanente), disparo doble/plasma, mega-bomba, EMP, monedas y puntaje |
| `enemy.py` | Clase abstracta Enemy (ABC) y 5 subclases: EnemigoNormal, EnemigoAgil, EnemigoRafaga, EnemigoApuntador, EnemigoKamikaze |
| `boss.py` | Clase Boss: 3 fases según % de vida con patrones distintos (recto → abanico → ráfaga radial + embestida) |
| `bullet.py` | Clase Bullet: balas de jugador, enemigo y boss con sprites animados (plasma, vulcan, proton) |
| `explosion.py` | Clase Explosion: animación de sprites de explosión en 3 tamaños (grande/mediana/pequeña) |
| `obstaculo.py` | Clase abstracta Obstaculo (ABC) y subclases: AgujeronNegro, Asteroide, ZonaInterferencia, LluviaMeteoros, PulsoEMP |
| `tienda.py` | Tienda entre niveles: escudo, disparo doble, plasma, vida extra, mega bomba, revivir compañero (solo si está muerto en 2J) |
| `menu.py` | Menú principal con opciones JUGAR / 2 JUGADORES / CONTROLES / SALIR, pantalla de controles superpuesta |
| `background.py` | Fondo parallax: BG tileable + 3 capas de estrellas + planetas decorativos en movimiento lento |
| `asset_loader.py` | Carga centralizada de todos los sprites del pack SpaceRage. Único módulo que llama a `pygame.image.load()` |
| `sound.py` | SoundManager: efectos de sonido (con disparo generado por síntesis) y música de fondo con mute |
| `config.py` | Constantes globales. WIDTH/HEIGHT se inicializan vía `set_dimensions()` desde main.py tras crear la ventana |
| `worlds.py` | Configuración de los 5 mundos: paleta, tipos de enemigos por oleada, oleadas por nivel, vidas del boss |
| `diagram.puml` | Diagrama de clases en PlantUML (genera `diagram.png` con `plantuml diagram.puml`) |

## Arquitectura

El flujo es: `main.py` → `Menu` → `Game` → (loop de juego) → vuelve a `Menu`.

`Game` es una máquina de estados con las transiciones:
**transición → jugando → completado → tienda → alerta → boss → game_over/victoria**.

Cada módulo es independiente:
- `asset_loader.py` es el único que hace `pygame.image.load()`.
- `sound.py` es el único que toca `pygame.mixer`.
- `config.WIDTH` y `config.HEIGHT` se leen vía `import config` (no `from config import …`)
  para que las dimensiones reales del display estén disponibles después de
  `set_dimensions()`.

## Display

El juego corre en modo `FULLSCREEN | SCALED` de pygame:
- Ocupa toda la pantalla pero permite Alt+Tab y screenshots sin minimizar.
- El surface interno se escala automáticamente a la resolución del monitor.

## Diagrama UML

El archivo `diagram.puml` describe las clases del proyecto y sus relaciones
(herencia, composición, asociaciones). Para regenerar `diagram.png`:

```bash
plantuml diagram.puml
```
