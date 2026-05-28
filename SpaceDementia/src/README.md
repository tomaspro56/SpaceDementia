# src/ — Código fuente de SpaceDementia

## Archivos

| Archivo | Descripción |
|---------|-------------|
| `main.py` | Punto de entrada. Inicializa Pygame en FULLSCREEN+SCALED, setea dimensiones en config, carga assets, pide nombre(s) y ejecuta el loop menú → juego → scoreboard |
| `game.py` | Controlador principal: estados (transición/jugando/completado/tienda/alerta/boss/game_over/victoria), oleadas, colisiones, HUD, pausa |
| `player.py` | Clase Player: movimiento, escudo (temporal y permanente), disparo doble/plasma, mega-bomba, EMP, monedas, puntaje y kills |
| `enemy.py` | Clase abstracta Enemy (ABC) y 5 subclases: EnemigoNormal, EnemigoAgil, EnemigoRafaga, EnemigoApuntador, EnemigoKamikaze |
| `boss.py` | Clase Boss: 3 fases según % de vida y un estilo de ataque por mundo (tirador, embestidor, rociador, artillero, caótico) con mecánicas especiales (rayo láser, escudo temporal, muro de balas) |
| `bullet.py` | Clase Bullet: balas de jugador, enemigo y boss con sprites animados (plasma, vulcan, proton); las del boss van tintadas para distinguirlas |
| `explosion.py` | Clase Explosion: animación de sprites en 3 tamaños (grande/mediana/pequeña) |
| `obstaculo.py` | Clase abstracta Obstaculo (ABC) y subclases: AgujeronNegro, Asteroide, ZonaInterferencia, LluviaMeteoros, PulsoEMP |
| `tienda.py` | Tienda entre niveles: escudo, disparo doble, plasma, vida extra, mega bomba, revivir compañero (solo si está muerto en 2J) |
| `menu.py` | Menú principal: JUGAR (submenú 1/2 jugadores) / PUNTAJES / CONTROLES / SONIDO / SALIR, con pantallas de controles y tabla de puntajes |
| `scoreboard.py` | Clase Scoreboard: tablas top 10 con persistencia JSON, separadas por modo (1j/2j), claves case-insensitive |
| `name_entry.py` | Pantalla de captura de nombre estilo arcade y visualización del scoreboard |
| `background.py` | Fondo parallax: BG tileable + 3 capas de estrellas + planetas decorativos |
| `asset_loader.py` | Carga centralizada de todos los sprites. Genera variantes de color tintando en memoria. Único módulo que llama a `pygame.image.load()` |
| `sound.py` | SoundManager: efectos de sonido (disparo generado por síntesis) y música de fondo con mute compartido entre instancias |
| `config.py` | Constantes globales. WIDTH/HEIGHT se inicializan vía `set_dimensions()` desde main.py tras crear la ventana |
| `worlds.py` | Configuración de los 5 mundos: paleta, tipos de enemigos por oleada, oleadas por nivel, vida y estilo del boss, sprite del boss |

El diagrama UML del proyecto está en `../diagram.puml` (raíz de SpaceDementia).

## Arquitectura

El flujo es: `main.py` pide nombre(s) → `Menu` → `Game` → (loop de juego)
→ al terminar, guarda el puntaje en el `Scoreboard` y muestra la tabla.

`Game` es una máquina de estados con las transiciones:
**transición → jugando → completado → tienda → alerta → boss →
game_over/victoria**.

Cada módulo es independiente:
- `asset_loader.py` es el único que hace `pygame.image.load()`.
- `sound.py` es el único que toca `pygame.mixer`.
- `config.WIDTH` y `config.HEIGHT` se leen vía `import config` (no
  `from config import …`) para que las dimensiones reales del display
  estén disponibles después de `set_dimensions()`.

## Programación orientada a objetos

El proyecto usa clases base abstractas (ABC) del módulo `abc`:
- `Enemy` es abstracta con el método abstracto `_get_tipo_sprite()`.
  Sus 5 subclases lo implementan y sobreescriben `move()` / `shoot_frame()`
  para comportamientos distintos (polimorfismo).
- `Obstaculo` es abstracta con los métodos abstractos `update()` y
  `draw()`, implementados por sus 5 anomalías espaciales.

## Color de enemigos por código

En lugar de tener un archivo por cada color, `asset_loader.py` parte de un
sprite base y lo tiñe en memoria al iniciar:
- El tintado es **selectivo**: solo cambia el cuerpo de la nave, conservando
  los detalles claros y las ventanas.
- Cada tipo de enemigo tiene un color asignado que **rota según el mundo**, así
  el mismo tipo se ve distinto a lo largo de la campaña.

## Display

El juego corre en modo `FULLSCREEN | SCALED` de pygame:
- Ocupa toda la pantalla pero permite Alt+Tab y screenshots sin minimizar.
- El surface interno se escala automáticamente a la resolución del monitor.

## Diagrama UML

El archivo `../diagram.puml` (en la raíz de SpaceDementia) describe las
clases y sus relaciones. Para regenerar la imagen:

```bash
plantuml diagram.puml
```
