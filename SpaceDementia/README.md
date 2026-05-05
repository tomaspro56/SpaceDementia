# SpaceDementia

Shoot'em up espacial horizontal desarrollado con Pygame para la materia de Lógica de Programación II — ITM, Medellín.

## Descripción

SpaceDementia es un juego de naves espaciales con scroll horizontal donde el jugador debe sobrevivir a 5 mundos, cada uno con 5 niveles y un boss final. Incluye modo cooperativo de 2 jugadores en el mismo teclado.

## Características

- 5 mundos temáticos con dificultad progresiva (25 niveles + 5 bosses)
- Modo 1 jugador y modo cooperativo 2 jugadores (mismo teclado)
- Sistema de oleadas con enemigos variados: normales, ágiles, ráfaga y apuntadores
- Tienda entre niveles con mejoras: escudo, disparo doble, disparo plasma, vida extra, mega bomba
- Anomalías espaciales: asteroides, agujeros negros, inversión gravitacional, lluvia de meteoros, pulso EMP, zona de interferencia
- Sprites animados del pack SpaceRage (itch.io)
- Música y efectos de sonido
- Sistema de monedas y puntuación por jugador
- Opción de revivir compañero en modo cooperativo

## Requisitos

- Python 3.10+
- pygame o pygame-ce

## Instalación

```bash
pip install pygame-ce
```

## Ejecución

Desde la raíz del proyecto:
```bash
python src/main.py
```

Para audio en Windows (recomendado):
```powershell
cd \\wsl.localhost\Ubuntu\home\tomas\Logica2026-1\SpaceDementia
python src/main.py
```

## Controles

### Jugador 1 (Nave Azul)
| Acción | Tecla |
|--------|-------|
| Mover | Flechas |
| Disparar | Espacio |
| Mega Bomba | B |

### Jugador 2 (Nave Roja)
| Acción | Tecla |
|--------|-------|
| Mover | WASD |
| Disparar | F |
| Mega Bomba | G |

### General
| Acción | Tecla |
|--------|-------|
| Pausa | P |
| Mutear | M |

## Estructura del proyecto
```
SpaceDementia/
├── README.md
├── assets/          # Sprites, fondos, audio
│   ├── Player/      # Naves del jugador (azul y roja)
│   ├── Enemies/     # Enemigos y minas
│   ├── Explosions/  # Animaciones de explosión
│   ├── FX/          # Efectos (balas, propulsor)
│   ├── Planets/     # Planetas decorativos
│   ├── Asteroids/   # Sprites de asteroides
│   ├── Audio/       # Música y efectos de sonido
│   ├── BG.png       # Fondo espacial tileable
│   └── README.md
├── src/             # Código fuente
│   ├── main.py      # Punto de entrada
│   ├── game.py      # Controlador principal
│   ├── player.py    # Nave del jugador
│   ├── enemy.py     # Enemigos
│   ├── boss.py      # Boss de cada mundo
│   ├── bullet.py    # Proyectiles
│   ├── explosion.py # Animaciones de explosión
│   ├── obstaculo.py # Anomalías espaciales
│   ├── tienda.py    # Tienda entre niveles
│   ├── menu.py      # Menú principal
│   ├── background.py # Fondo parallax
│   ├── asset_loader.py # Carga de sprites
│   ├── sound.py     # Audio
│   ├── config.py    # Resolución y constantes
│   ├── worlds.py    # Configuración de mundos
│   ├── powerup.py   # Power-ups
│   └── README.md
└── requirements.txt
```

## Créditos

- **Sprites:** SpaceRage Asset Pack por Ravenmore (itch.io)
- **Música:** Sci-Fi Music Pack Vol. 2 (itch.io)
- **Efectos de sonido:** Retro Sci-Fi Sound Fx + Interface Bleeps (itch.io)
- **Desarrollo:** Tomás, Yesica Caro, Juan Manuel Castaño, Luis Daniel Zuluaga — ITM Medellín, 2025
