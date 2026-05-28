# docs/ — Documentación y material visual

Material de apoyo del proyecto: GIF de gameplay, capturas y documentación.

## Contenido

| Archivo | Descripción |
|---------|-------------|
| `gameplay.gif` | Animación del gameplay (boss fight del mundo 5 en cooperativo) |
| `menu.png` | Menú principal |
| `boss_fight.png` | Pelea contra un boss |
| `tienda.png` | Tienda entre niveles |
| `scoreboard.png` | Tabla de mejores puntajes |
| `game_over.png` | Pantalla de fin de partida con estadísticas |

## Diagrama de clases

El diagrama renderizado está en `../UML_FINAL.svg` y su fuente PlantUML en
`../diagram.puml` (ambos en la raíz de SpaceDementia). Para regenerar la
imagen desde la fuente:

```bash
plantuml ../diagram.puml
```

## Notas de diseño

- **Renderizado mixto:** la mayoría de elementos usan sprites del pack SpaceRage,
  pero algunas anomalías (meteoros, agujeros negros) se dibujan con primitivas de
  Pygame. Es una decisión deliberada que permite comparar el resultado del
  dibujo por código frente al de assets hechos por artistas.
- **Color por código:** los enemigos no tienen un sprite por color. Se parte de
  un sprite base y se tiñe en memoria al cargar, generando una paleta por tipo de
  enemigo que además rota según el mundo. Esto da variedad visual sin multiplicar
  los archivos de assets.
