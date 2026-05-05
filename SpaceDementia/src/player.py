import math

import pygame

import asset_loader

_MAX_BALAS_DEFAULT = 5


class Player:
    """Nave del jugador. Soporta jugador 1 (azul) y jugador 2 (rojo)."""

    def __init__(self, x, y, size, speed, life, tema=None, jugador_id=1):
        self.x = float(x)
        self.y = float(y)
        self._pos_inicial = (float(x), float(y))
        self.size = size
        self.velocidad_base = speed
        self.speed = speed
        self._life = life
        self._score = 0
        self._monedas = 0
        self.jugador_id = jugador_id
        self.tema = tema or {
            "color_jugador":         (80, 160, 255),
            "color_jugador_detalle": (0, 240, 255),
            "color_propulsor":       (255, 120, 0),
        }
        self._frame = 0
        self.tilt = 0.0

        # Power-ups
        self.powerups = {}
        self.powerups_temporales = {}
        self.mega_disparo_activo = False

        # Estado de partida (movido desde Game)
        self.mega_bombas = 0
        self.disparo_doble = False
        self.disparo_plasma = False
        self._max_balas = _MAX_BALAS_DEFAULT
        self._shoot_cooldown = 0

        # EMP: bloqueo temporal del disparo
        self.emp_activo = False
        self.emp_timer = 0

    # ------------------------------------------------------------ properties

    @property
    def life(self):
        return self._life

    @life.setter
    def life(self, valor):
        self._life = max(0, min(5, valor))

    @property
    def score(self):
        return self._score

    @score.setter
    def score(self, valor):
        self._score = max(0, valor)

    @property
    def monedas(self):
        return self._monedas

    @monedas.setter
    def monedas(self, valor):
        self._monedas = max(0, valor)

    # ---------------------------------------------------------------- update

    def update(self):
        """Decrementa timers de power-ups temporales y aplica efectos."""
        for tipo in list(self.powerups_temporales.keys()):
            self.powerups_temporales[tipo] -= 1
            if self.powerups_temporales[tipo] <= 0:
                del self.powerups_temporales[tipo]

        if "VELOCIDAD" in self.powerups_temporales:
            self.speed = self.velocidad_base * 2
        else:
            self.speed = self.velocidad_base

        # Temporizador de EMP
        if self.emp_timer > 0:
            self.emp_timer -= 1
            if self.emp_timer <= 0:
                self.emp_activo = False

        # Cooldown de disparo
        if self._shoot_cooldown > 0:
            self._shoot_cooldown -= 1

    # ------------------------------------------------------------ power-ups

    def add_powerup(self, powerup_type):
        max_count = 3 if powerup_type in ("WEAPON_RIGHT", "WEAPON_LEFT") else 1
        self.powerups.setdefault(powerup_type, 0)
        if self.powerups[powerup_type] < max_count:
            self.powerups[powerup_type] += 1

    def remove_powerup(self, powerup_type):
        if self.powerups.get(powerup_type, 0) > 0:
            self.powerups[powerup_type] -= 1
            if self.powerups[powerup_type] == 0:
                del self.powerups[powerup_type]

    def has_powerup(self, powerup_type):
        return self.powerups.get(powerup_type, 0) > 0

    def tiene_escudo(self):
        """Verifica escudo de campo (temporal) O escudo de tienda (permanente)."""
        return ("ESCUDO" in self.powerups_temporales or
                self.powerups.get("ESCUDO", 0) > 0)

    def consumir_escudo(self):
        """Consume el escudo al recibir un golpe. Retorna True si había escudo."""
        if "ESCUDO" in self.powerups_temporales:
            del self.powerups_temporales["ESCUDO"]
            return True
        if self.powerups.get("ESCUDO", 0) > 0:
            del self.powerups["ESCUDO"]
            return True
        return False

    # -------------------------------------------------------------- movimiento

    def move(self, direction):
        if direction == "LEFT":
            self.x -= self.speed
        elif direction == "RIGHT":
            self.x += self.speed
        elif direction == "UP":
            self.y -= self.speed
        elif direction == "DOWN":
            self.y += self.speed

    # ------------------------------------------------------------------- draw

    def draw(self, screen):
        self._frame += 1
        if self.tiene_escudo():
            self._dibujar_escudo(screen)
        self._dibujar_exhaust(screen)
        self._dibujar_nave(screen)

    def _dibujar_escudo(self, screen):
        """Burbuja protectora pulsante."""
        x, y, s = int(self.x), int(self.y), self.size
        radio = s + 14 + int(math.sin(self._frame * 0.2) * 3)
        surf = pygame.Surface((radio * 2 + 4, radio * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(surf, (80, 200, 255, 70),  (radio + 2, radio + 2), radio)
        pygame.draw.circle(surf, (160, 230, 255, 180), (radio + 2, radio + 2), radio, 2)
        screen.blit(surf, (x - radio - 2, y - radio - 2))

    def _dibujar_exhaust(self, screen):
        """Llama del propulsor con sprites exhaust animados."""
        sprite = asset_loader.get_exhaust_frame(self._frame)
        w, h = sprite.get_size()
        blit_x = int(self.x) - self.size - w + 8
        blit_y = int(self.y) - h // 2
        screen.blit(sprite, (blit_x, blit_y))

    def _dibujar_nave(self, screen):
        """Sprite del jugador centrado en (self.x, self.y), frame según tilt."""
        mega   = self.mega_disparo_activo
        sprite = asset_loader.get_player_frame(self.tilt, mega, self.jugador_id)
        w, h   = sprite.get_size()
        screen.blit(sprite, (int(self.x) - w // 2, int(self.y) - h // 2))
