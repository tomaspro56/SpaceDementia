import math
import random
from abc import ABC, abstractmethod

import pygame

import asset_loader
from bullet import Bullet
import config


class Enemy(ABC):
    """Clase base para todos los enemigos espaciales."""

    PUNTOS  = 10
    MONEDAS = 5

    def __init__(self, x, y, size, speed, tema=None):
        self.x      = float(x)
        self.y      = float(y)
        self.size   = size
        self.speed  = min(speed, 12)
        self.direction_y = 1
        self.tema   = tema or {
            "color_enemigo_normal": (90, 80, 230),
            "color_enemigo_agil":   (0, 180, 255),
            "color_bala_enemigo":   (130, 90, 255),
            "vel_bala_enemigo":     12,
        }
        self._frame      = 0
        self.color_sprite = "r"
        self.vida        = 1
        self.hit_flash   = 0

    # ------------------------------------------------------------------ lógica

    def shoot(self):
        """Dispara una bala recta hacia la izquierda."""
        vel = self.tema.get("vel_bala_enemigo", 12)
        return Bullet(self.x, self.y, vel, "LEFT",
                      tema=self.tema, es_enemigo=True)

    def shoot_apuntado(self, px, py):
        """Dispara en ángulo directo hacia la posición del jugador."""
        vel    = self.tema.get("vel_bala_enemigo", 12)
        angulo = math.degrees(math.atan2(py - self.y, px - self.x))
        return Bullet(self.x, self.y, vel, "LEFT",
                      tema=self.tema, es_enemigo=True, angulo=angulo)

    def recibir_daño(self, daño=1):
        """Aplica daño. Retorna True si el enemigo murió."""
        self.vida -= daño
        if self.vida > 0:
            self.hit_flash = 8
        return self.vida <= 0

    def move(self):
        """Movimiento base: avanzar hacia la izquierda."""
        self._frame += 1
        self.x -= self.speed

    def shoot_frame(self, jugadores):
        """Retorna lista de Bullet a generar este frame. Las subclases sobreescriben."""
        if random.randint(1, 100) <= 3:
            return [self.shoot()]
        return []

    # ------------------------------------------------------------------- draw

    def draw(self, screen):
        self._dibujar_sprite(screen)
        if self.hit_flash > 0:
            self.hit_flash -= 1
            s    = self.size + 2
            surf = pygame.Surface((s * 2 + 4, s * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255, 255, 255, 160), (s + 2, s + 2), s)
            screen.blit(surf, (int(self.x) - s - 2, int(self.y) - s - 2))

    @abstractmethod
    def _get_tipo_sprite(self) -> str:
        """Subclases sobreescriben para indicar sprite 1 (drone) o 2 (caza)."""
        ...

    def _dibujar_sprite(self, screen):
        sprite = asset_loader.get_enemy_frame(self._get_tipo_sprite(),
                                               self.color_sprite,
                                               self.direction_y)
        w, h = sprite.get_size()
        screen.blit(sprite, (int(self.x) - w // 2, int(self.y) - h // 2))


# ─────────────────────────────────────────────────────────────────────────────
# Subclases
# ─────────────────────────────────────────────────────────────────────────────

class EnemigoNormal(Enemy):
    """Drone básico. Avanza recto, disparo recto aleatorio."""

    PUNTOS  = 10
    MONEDAS = 5

    def _get_tipo_sprite(self):
        return "1"


class EnemigoAgil(Enemy):
    """Caza rápido. Movimiento zigzag vertical."""

    PUNTOS  = 20
    MONEDAS = 10

    def move(self):
        super().move()
        self.y += self.direction_y * 2
        if self.y < 50 or self.y > config.HEIGHT - 50:
            self.direction_y *= -1

    def _get_tipo_sprite(self):
        return "2"


class EnemigoRafaga(Enemy):
    """Drone que dispara en ráfagas de 3 balas seguidas."""

    PUNTOS  = 30
    MONEDAS = 15

    def __init__(self, x, y, size, speed, tema=None):
        super().__init__(x, y, size, speed, tema)
        self.burst_cooldown = 0
        self.burst_disparos = 0

    def shoot_frame(self, jugadores):
        if self.burst_cooldown > 0:
            self.burst_cooldown -= 1
            return []
        if self.burst_disparos > 0:
            bala = self.shoot()
            self.burst_disparos -= 1
            if self.burst_disparos == 0:
                self.burst_cooldown = 120
            return [bala]
        if random.randint(1, 100) <= 3:
            self.burst_disparos = 3
        return []

    def _get_tipo_sprite(self):
        return "1"


class EnemigoApuntador(Enemy):
    """Caza que apunta directamente al jugador más cercano."""

    PUNTOS  = 25
    MONEDAS = 12

    def __init__(self, x, y, size, speed, tema=None):
        super().__init__(x, y, size, speed, tema)
        self.disparo_timer = random.randint(30, 90)

    def move(self):
        super().move()
        self.y += self.direction_y * 2
        if self.y < 50 or self.y > config.HEIGHT - 50:
            self.direction_y *= -1

    def shoot_frame(self, jugadores):
        if self.disparo_timer > 0:
            self.disparo_timer -= 1
            return []
        if not jugadores:
            return []
        self.disparo_timer = 90
        target = min(jugadores, key=lambda p: abs(p.x - self.x) + abs(p.y - self.y))
        return [self.shoot_apuntado(target.x, target.y)]

    def draw(self, screen):
        super().draw(screen)
        self._dibujar_reticula(screen)

    def _dibujar_reticula(self, screen):
        """Retícula de apuntado que parpadea cuando está a punto de disparar."""
        x, y, s  = int(self.x), int(self.y), self.size
        cerca    = self.disparo_timer <= 20
        c        = (255, 50, 50) if cerca else (200, 80, 80)
        parpadeo = (self._frame // 4) % 2 == 0
        if cerca and not parpadeo:
            return
        radio = s + 8
        pygame.draw.circle(screen, c, (x, y), radio, 1)
        gap   = 4
        largo = 7
        pygame.draw.line(screen, c, (x - radio - largo, y), (x - radio - gap, y), 1)
        pygame.draw.line(screen, c, (x + radio + gap,  y), (x + radio + largo, y), 1)
        pygame.draw.line(screen, c, (x, y - radio - largo), (x, y - radio - gap), 1)
        pygame.draw.line(screen, c, (x, y + radio + gap),   (x, y + radio + largo), 1)

    def _get_tipo_sprite(self):
        return "2"


class EnemigoKamikaze(Enemy):
    """Enemigo suicida: persigue al jugador más cercano sin disparar.

    Pierde su disparo a cambio de velocidad y movimiento dirigido.
    Demuestra polimorfismo: anula move() para perseguir, anula
    shoot_frame() para no disparar nunca.
    """

    PUNTOS  = 35
    MONEDAS = 18

    def __init__(self, x, y, size, speed, tema=None):
        super().__init__(x, y, size, speed, tema)
        self.speed = min(speed * 1.4, 12)
        self.vida  = 2
        self._target_player = None
        self.color_sprite   = "g"

    def move(self):
        """Persigue al jugador más cercano en vez de avanzar recto."""
        self._frame += 1
        if self._target_player is not None and self._target_player.life > 0:
            dx = self._target_player.x - self.x
            dy = self._target_player.y - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 1:
                self.x += (dx / dist) * self.speed
                self.y += (dy / dist) * self.speed
        else:
            self.x -= self.speed

    def shoot_frame(self, jugadores):
        """No dispara. Al primer frame con jugadores vivos, fija objetivo."""
        if self._target_player is None and jugadores:
            self._target_player = min(
                jugadores,
                key=lambda p: abs(p.x - self.x) + abs(p.y - self.y)
            )
        return []

    def _get_tipo_sprite(self) -> str:
        return "2"
