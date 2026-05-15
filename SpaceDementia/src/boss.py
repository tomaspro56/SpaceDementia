import math
import random

import pygame

import asset_loader
from bullet import Bullet
import config


class Boss:
    """Boss final de cada nivel. 3 fases según porcentaje de vida."""

    VIDA_MAX = 300
    SIZE = 90          # 3× el enemigo normal (30)

    def __init__(self, x, y, tema=None):
        self.x = float(x)
        self.y = float(config.HEIGHT // 2)
        self.X_BATALLA = config.WIDTH - 300
        self.size = self.SIZE
        self._vida = self.VIDA_MAX
        self.vida_max = self.VIDA_MAX
        self.tema = tema or {}
        self.fase = 1
        self.speed = 1.5
        self.direction_y = 1
        self.entrando = True
        self._frame = 0
        self._disparo_cooldown = 90   # Espera antes del primer disparo
        self._vel_y_erratica = 0.0

        # Embestida en fase 3
        self._cargando = False
        self._carga_timer = 0

        # Colas que game.py drena cada frame
        self.disparos_pendientes = []
        self.refuerzos_pendientes = 0

    # ------------------------------------------------------------ properties

    @property
    def vida(self):
        return self._vida

    @vida.setter
    def vida(self, valor):
        self._vida = max(0, min(self.vida_max, valor))

    @property
    def esta_en_fase_critica(self):
        """True si está en fase 3 (menos del 33 % de vida)."""
        return self._vida / self.vida_max <= 0.33

    # ---------------------------------------------------------------- lógica

    def _actualizar_fase(self):
        ratio = self.vida / self.vida_max
        nueva_fase = 1 if ratio > 0.66 else (2 if ratio > 0.33 else 3)
        if nueva_fase != self.fase:
            self.fase = nueva_fase
            # Al entrar en fase 3: acelera cooldown de disparo
            if self.fase == 3:
                self._disparo_cooldown = min(self._disparo_cooldown, 30)

    def update(self):
        self._frame += 1
        self._actualizar_fase()

        # --- Animación de entrada ---
        if self.entrando:
            if self.x > self.X_BATALLA:
                self.x -= 5
            else:
                self.x = float(self.X_BATALLA)
                self.entrando = False
            return  # Sin disparos durante la entrada

        # --- Refuerzos periódicos en fase 2 (cada 300 frames) ---
        if self.fase == 2 and self._frame % 300 == 0:
            self.refuerzos_pendientes += 2

        # --- Movimiento según fase ---
        if self.fase == 1:
            self.speed = 1.8
            self.y += self.direction_y * self.speed

        elif self.fase == 2:
            self.speed = 3.2
            self.y += self.direction_y * self.speed

        else:  # fase 3: movimiento errático + embestida
            self.speed = 5.0

            if self._cargando:
                self._carga_timer += 1
                if self._carga_timer <= 45:
                    # Embestir hacia la izquierda (hacia el jugador)
                    self.x = max(150.0, self.x - 8.0)
                else:
                    # Volver gradualmente a posición de batalla sin límite de tiempo
                    if self.x < self.X_BATALLA - 3:
                        self.x += 5.0
                    else:
                        self.x = float(self.X_BATALLA)
                        self._cargando = False
            else:
                # Movimiento errático normal
                if self._frame % 10 == 0:
                    self._vel_y_erratica = random.uniform(-self.speed, self.speed)
                self.y += self._vel_y_erratica
                # Disparar embestida cada 200 frames
                if self._frame % 200 == 0:
                    self._cargando = True
                    self._carga_timer = 0

        # Mantener dentro de la pantalla (margen mínimo 120 para sprite de 192px)
        margen = max(self.size + 15, 120)
        if self.y < margen:
            self.y = float(margen)
            self.direction_y = 1
            self._vel_y_erratica = abs(self._vel_y_erratica)
        if self.y > config.HEIGHT - margen:
            self.y = float(config.HEIGHT - margen)
            self.direction_y = -1
            self._vel_y_erratica = -abs(self._vel_y_erratica)
        # Limitar X para que el sprite no salga por los lados
        self.x = max(150.0, min(float(config.WIDTH - 150), self.x))

        # Cambio de dirección periódico (fases 1 y 2)
        if self.fase < 3 and self._frame % 80 == 0:
            self.direction_y *= -1

        # --- Disparos ---
        self._disparo_cooldown -= 1
        if self._disparo_cooldown <= 0:
            self._disparar()

    def _disparar(self):
        x, y = self.x, self.y

        if self.fase == 1:
            # Bala recta hacia la izquierda
            self.disparos_pendientes.append(
                Bullet(x, y, 12, "LEFT", tema=self.tema, es_enemigo=True, es_bala_boss=True)
            )
            self._disparo_cooldown = 55

        elif self.fase == 2:
            # Abanico de 3 balas (izquierda con ángulos ±25°)
            for angulo in [180, 155, 205]:
                self.disparos_pendientes.append(
                    Bullet(x, y, 12, "LEFT", tema=self.tema,
                           es_enemigo=True, angulo=angulo, es_bala_boss=True)
                )
            self._disparo_cooldown = 42

        else:  # fase 3: ráfaga radial de 8 direcciones
            for angulo in range(0, 360, 45):
                self.disparos_pendientes.append(
                    Bullet(x, y, 10, "LEFT", tema=self.tema,
                           es_enemigo=True, angulo=angulo, es_bala_boss=True)
                )
            self._disparo_cooldown = 30

    def recibir_daño(self, daño=1):
        """Aplica daño. Retorna True si el boss murió."""
        self.vida -= daño
        return self.vida <= 0

    def esta_muerto(self):
        return self.vida <= 0

    # ------------------------------------------------------------------ draw

    def draw(self, screen):
        # Flash rojo en fase 3 (detrás del sprite)
        if self.fase == 3 and self._frame % 8 < 3:
            self._flash_rojo(screen)

        # Sprite principal (enemy_2 escalado 3×, apunta izquierda)
        sprite = asset_loader.get_boss_sprite()
        w, h   = sprite.get_size()
        screen.blit(sprite, (int(self.x) - w // 2, int(self.y) - h // 2))

        # Indicador visual de embestida (encima del sprite)
        if self._cargando and self._carga_timer <= 45:
            self._dibujar_indicador_carga(screen)

        # La barra de vida la dibuja game.py DESPUÉS del HUD (mayor prioridad visual)

    def _dibujar_indicador_carga(self, screen):
        """Halo rojo pulsante durante la embestida."""
        surf = pygame.Surface((self.size * 2 + 20, self.size * 2 + 20), pygame.SRCALPHA)
        pulso = int(abs(math.sin(self._carga_timer * 0.3)) * 60) + 80
        pygame.draw.circle(surf, (255, 50, 0, pulso),
                           (self.size + 10, self.size + 10), self.size + 8)
        screen.blit(surf, (int(self.x) - self.size - 10, int(self.y) - self.size - 10))

    def _flash_rojo(self, screen):
        surf = pygame.Surface((self.size * 2 + 12, self.size * 2 + 12), pygame.SRCALPHA)
        pygame.draw.circle(surf, (255, 0, 0, 90),
                           (self.size + 6, self.size + 6), self.size + 4)
        screen.blit(surf, (int(self.x) - self.size - 6, int(self.y) - self.size - 6))

    def _dibujar_barra_vida(self, screen):
        barra_w = 380
        barra_h = 20
        bx = config.WIDTH // 2 - barra_w // 2
        by = 45   # Debajo del texto "MUNDO X · NIVEL Y" del HUD

        # Fondo
        pygame.draw.rect(screen, (40, 40, 40), (bx - 2, by - 2, barra_w + 4, barra_h + 4))

        # Relleno con color según fase
        ratio = self.vida / self.vida_max
        color_barra = (
            (30, 200, 60) if ratio > 0.66 else
            (210, 170, 0) if ratio > 0.33 else
            (210, 30, 30)
        )
        ancho_relleno = max(0, int(barra_w * ratio))
        pygame.draw.rect(screen, color_barra, (bx, by, ancho_relleno, barra_h))
        pygame.draw.rect(screen, (180, 180, 180), (bx, by, barra_w, barra_h), 2)

        # Nombre del boss centrado en la barra
        font = pygame.font.SysFont("monospace", 14, bold=True)
        nombre = self.tema.get("nombre_boss", "BOSS")
        fase_txt = f"  [FASE {self.fase}]"
        surf_n = font.render(nombre + fase_txt, True, (255, 255, 255))
        screen.blit(surf_n, (bx + barra_w // 2 - surf_n.get_width() // 2, by + 2))

