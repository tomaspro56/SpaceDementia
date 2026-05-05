import math

import pygame

import asset_loader


class Bullet:
    """Bala del jugador o del enemigo. Estilo visual único espacial."""

    def __init__(self, x, y, speed, direction, tema=None,
                 es_enemigo=False, angulo=None, es_mega=False, es_bala_boss=False,
                 es_proton=False, daño=1, jugador_id=1):
        self.x = float(x)
        self.y = float(y)
        self.speed = speed
        self.width = 5
        self.height = 10
        self.direction = direction
        self.tema = tema or {
            "color_bala_jugador": (0, 255, 200),
            "color_bala_enemigo": (130, 90, 255),
        }
        self.es_enemigo    = es_enemigo
        self.es_mega       = es_mega
        self.es_bala_boss  = es_bala_boss
        self.es_proton     = es_proton   # Usa sprites proton + hace 2 de daño
        self.daño          = daño        # Daño al impactar enemigo
        self.jugador_id    = jugador_id  # 1 o 2 (para atribuir puntos/monedas)
        self.frame = 0

        # Movimiento libre por ángulo (disparos apuntados / boss radial)
        self.angulo = angulo
        if angulo is not None:
            rad = math.radians(angulo)
            self.vx = math.cos(rad) * speed
            self.vy = math.sin(rad) * speed
        else:
            self.vx = 0.0
            self.vy = 0.0

    # ------------------------------------------------------------------ movimiento

    def move(self):
        if self.angulo is not None:
            self.x += self.vx
            self.y += self.vy
        elif self.direction == "LEFT":
            self.x -= self.speed
        elif self.direction == "RIGHT":
            self.x += self.speed
        elif self.direction == "UP":
            self.y -= self.speed
        elif self.direction == "DOWN":
            self.y += self.speed
        elif self.direction == "DIAG_LEFT":
            self.x -= self.speed * 0.7
            self.y -= self.speed * 0.7
        elif self.direction == "DIAG_RIGHT":
            self.x += self.speed * 0.7
            self.y -= self.speed * 0.7
        self.frame += 1

    # ------------------------------------------------------------------- draw

    def draw(self, screen):
        if self.es_mega:
            self._dibujar_mega(screen)
        elif self.es_bala_boss:
            self._dibujar_boss(screen)
        elif self.es_enemigo or self.angulo is not None:
            self._dibujar_enemigo(screen)
        elif self.direction == "RIGHT":
            if self.es_proton:
                self._dibujar_boss(screen)   # Reutiliza sprites proton para disparo plasma
            else:
                self._dibujar_principal(screen)
        else:
            self._dibujar_secundaria(screen)

    def _dibujar_mega(self, screen):
        color = self.tema.get("color_bala_jugador", (0, 255, 200))
        x, y = int(self.x), int(self.y)
        pygame.draw.circle(screen, color, (x, y), 15)
        pygame.draw.circle(screen, (255, 255, 255), (x, y), 15, 2)
        if (self.frame // 4) % 2 == 0:
            pygame.draw.circle(screen, (255, 255, 255), (x, y), 7)

    def _dibujar_boss(self, screen):
        """Bala del boss: sprite proton animado."""
        sprite = asset_loader.get_proton_frame(self.frame)
        w, h = sprite.get_size()
        screen.blit(sprite, (int(self.x) - w // 2, int(self.y) - h // 2))

    def _dibujar_principal(self, screen):
        """Bala principal del jugador (hacia la derecha): sprite plasma animado."""
        if self.jugador_id == 2:
            sprite = asset_loader.get_plasma_frame_p2(self.frame)
        else:
            sprite = asset_loader.get_plasma_frame(self.frame)
        w, h = sprite.get_size()
        screen.blit(sprite, (int(self.x) - w // 2, int(self.y) - h // 2))

    def _dibujar_enemigo(self, screen):
        """Bala del enemigo (izquierda/ángulo): sprite vulcan animado."""
        sprite = asset_loader.get_vulcan_frame(self.frame)
        w, h = sprite.get_size()
        screen.blit(sprite, (int(self.x) - w // 2, int(self.y) - h // 2))

    def _dibujar_secundaria(self, screen):
        """Balas secundarias del jugador (izquierda, diagonales, abajo)."""
        color = self.tema.get("color_bala_jugador", (0, 255, 200))
        x, y = int(self.x), int(self.y)
        if self.direction in ("DIAG_LEFT", "DIAG_RIGHT"):
            pygame.draw.polygon(screen, color, [
                (x, y - 5), (x + 5, y), (x, y + 5), (x - 5, y),
            ])
        elif self.direction == "LEFT":
            pygame.draw.rect(screen, color, (x - 10, y - 3, 14, 6))
        elif self.direction == "DOWN":
            pygame.draw.rect(screen, color, (x - 3, y, 6, 14))
        else:
            pygame.draw.rect(screen, color, (x, y, self.width, self.height))
