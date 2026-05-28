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
        self.tema = tema or {}
        self.x = float(x)
        self.y = float(config.HEIGHT // 2)
        self.X_BATALLA = config.WIDTH - 300

        # Sprite y tamaño según el mundo (con defaults seguros)
        self.sprite_tipo  = self.tema.get("boss_sprite_tipo", "2")
        self.sprite_color = self.tema.get("boss_sprite_color", "r")
        self.size         = self.tema.get("boss_size", 90)
        self.estilo       = self.tema.get("boss_estilo", "tirador")

        self.vida_max = self.tema.get("boss_vida", 300)
        self._vida    = self.vida_max
        self.fase = 1
        self.speed = 1.5
        # FIX: dirección inicial aleatoria (antes siempre bajaba)
        self.direction_y = random.choice([-1, 1])
        self.entrando = True
        self._frame = 0
        self._disparo_cooldown = 90
        self._vel_y_erratica = 0.0

        # Embestida
        self._cargando = False
        self._carga_timer = 0

        # Mecánicas especiales
        self._escudo_activo   = False
        self._escudo_timer    = 0
        self._escudo_cooldown = 360     # frames hasta poder volver a activar
        self._laser_activo    = False
        self._laser_timer     = 0
        self._laser_y         = 0.0     # altura del rayo
        self._laser_fase      = "idle"  # "idle" | "telegrafia" | "dispara"
        self._laser_cooldown  = 240
        self._muro_cooldown   = 300

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
            if self._cargando:
                self._carga_timer += 1
                if self._carga_timer <= 45:
                    self.x = max(150.0, self.x - 8.0)
                else:
                    if self.x < self.X_BATALLA - 3:
                        self.x += 5.0
                    else:
                        self.x = float(self.X_BATALLA)
                        self._cargando = False
            else:
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

        # FIX: margen simétrico respecto al centro, según el tamaño real del boss
        margen = self.size + 20
        limite_sup = margen
        limite_inf = config.HEIGHT - margen
        if self.y < limite_sup:
            self.y = float(limite_sup)
            self.direction_y = 1
            self._vel_y_erratica = abs(self._vel_y_erratica)
        if self.y > limite_inf:
            self.y = float(limite_inf)
            self.direction_y = -1
            self._vel_y_erratica = -abs(self._vel_y_erratica)
        # Limitar X para que el sprite no salga por los lados
        self.x = max(150.0, min(float(config.WIDTH - 150), self.x))

        # Cambio de dirección periódico (fases 1 y 2)
        if self.fase < 3 and self._frame % 80 == 0:
            self.direction_y *= -1

        # Embestida: el "embestidor" carga más seguido y desde fase 2
        if not self._cargando:
            if self.estilo == "embestidor":
                intervalo_embestida = 130
                puede_embestir = self.fase >= 2
            else:
                intervalo_embestida = 200
                puede_embestir = self.fase >= 3
            if puede_embestir and self._frame % intervalo_embestida == 0:
                self._cargando = True
                self._carga_timer = 0

        # ── Mecánica: ESCUDO temporal (rociador y caotico, desde fase 2) ──
        if self.estilo in ("rociador", "caotico") and self.fase >= 2:
            if self._escudo_activo:
                self._escudo_timer -= 1
                if self._escudo_timer <= 0:
                    self._escudo_activo = False
                    self._escudo_cooldown = 360
            else:
                self._escudo_cooldown -= 1
                if self._escudo_cooldown <= 0:
                    self._escudo_activo = True
                    self._escudo_timer  = 150   # 2.5 s indestructible

        # ── Mecánica: RAYO LÁSER barredor (artillero, desde fase 2) ──
        if self.estilo == "artillero" and self.fase >= 2:
            if self._laser_fase == "idle":
                self._laser_cooldown -= 1
                if self._laser_cooldown <= 0:
                    self._laser_fase  = "telegrafia"
                    self._laser_timer = 60        # 1 s de aviso
                    self._laser_y     = float(self.y)
            elif self._laser_fase == "telegrafia":
                self._laser_timer -= 1
                self._laser_y = float(self.y)     # sigue al boss hasta disparar
                if self._laser_timer <= 0:
                    self._laser_fase  = "dispara"
                    self._laser_timer = 45        # 0.75 s de rayo activo
            elif self._laser_fase == "dispara":
                self._laser_timer -= 1
                if self._laser_timer <= 0:
                    self._laser_fase     = "idle"
                    self._laser_cooldown = 240

        # ── Mecánica: MURO de balas con hueco (caotico, fase 3) ──
        if self.estilo == "caotico" and self.fase == 3:
            self._muro_cooldown -= 1
            if self._muro_cooldown <= 0:
                self._muro_cooldown = 300
                self._disparar_muro()

        # --- Disparos ---
        self._disparo_cooldown -= 1
        if self._disparo_cooldown <= 0:
            self._disparar()

    def _disparar(self):
        x, y = self.x, self.y
        t = self.tema

        if self.estilo == "tirador":
            # Balas rectas, ritmo según fase
            n = 1 if self.fase == 1 else (2 if self.fase == 2 else 3)
            for i in range(n):
                off = (i - (n - 1) / 2) * 30
                self.disparos_pendientes.append(
                    Bullet(x, y + off, 12, "LEFT", tema=t, es_enemigo=True, es_bala_boss=True))
            self._disparo_cooldown = 60 if self.fase == 1 else (48 if self.fase == 2 else 36)

        elif self.estilo == "embestidor":
            # Fase 1: 1 bala. Fase 2: 3 balas en abanico. Fase 3: 5 balas + rápido.
            if self.fase == 1:
                self.disparos_pendientes.append(
                    Bullet(x, y, 11, "LEFT", tema=t, es_enemigo=True, es_bala_boss=True))
            elif self.fase == 2:
                for ang in [180, 158, 202]:
                    self.disparos_pendientes.append(
                        Bullet(x, y, 11, "LEFT", tema=t, es_enemigo=True,
                               angulo=ang, es_bala_boss=True))
            else:
                for ang in [180, 160, 200, 145, 215]:
                    self.disparos_pendientes.append(
                        Bullet(x, y, 12, "LEFT", tema=t, es_enemigo=True,
                               angulo=ang, es_bala_boss=True))
            self._disparo_cooldown = 55 if self.fase == 1 else (45 if self.fase == 2 else 35)

        elif self.estilo == "rociador":
            # Abanico amplio de balas lentas
            base = 180
            spread = [base, base - 20, base + 20, base - 40, base + 40]
            if self.fase >= 2:
                spread += [base - 60, base + 60]
            for ang in spread:
                self.disparos_pendientes.append(
                    Bullet(x, y, 8, "LEFT", tema=t, es_enemigo=True, angulo=ang, es_bala_boss=True))
            self._disparo_cooldown = 75 if self.fase == 1 else (60 if self.fase == 2 else 48)

        elif self.estilo == "artillero":
            # Ráfaga rápida de balas hacia la izquierda, ritmo agresivo
            n = 2 if self.fase == 1 else (3 if self.fase == 2 else 4)
            for i in range(n):
                off = (i - (n - 1) / 2) * 22
                self.disparos_pendientes.append(
                    Bullet(x, y + off, 14, "LEFT", tema=t, es_enemigo=True, es_bala_boss=True))
            self._disparo_cooldown = 40 if self.fase == 1 else (30 if self.fase == 2 else 22)

        else:  # "caotico" — combina patrones, el más difícil
            if self.fase == 1:
                for ang in [180, 160, 200]:
                    self.disparos_pendientes.append(
                        Bullet(x, y, 11, "LEFT", tema=t, es_enemigo=True, angulo=ang, es_bala_boss=True))
                self._disparo_cooldown = 45
            elif self.fase == 2:
                for ang in range(140, 221, 20):
                    self.disparos_pendientes.append(
                        Bullet(x, y, 11, "LEFT", tema=t, es_enemigo=True, angulo=ang, es_bala_boss=True))
                self._disparo_cooldown = 38
            else:
                for ang in range(0, 360, 36):
                    self.disparos_pendientes.append(
                        Bullet(x, y, 10, "LEFT", tema=t, es_enemigo=True, angulo=ang, es_bala_boss=True))
                self._disparo_cooldown = 30

    def _disparar_muro(self):
        """Lanza una columna vertical de balas con UN hueco para esquivar."""
        t = self.tema
        n_balas = 11
        hueco   = random.randint(1, n_balas - 2)   # índice del hueco
        alto    = config.HEIGHT - 100
        for i in range(n_balas):
            if abs(i - hueco) <= 1:   # deja un hueco de 2-3 balas
                continue
            by = 50 + (alto / (n_balas - 1)) * i
            self.disparos_pendientes.append(
                Bullet(self.x, by, 9, "LEFT", tema=t, es_enemigo=True, es_bala_boss=True))

    def laser_activo_en(self, y_jugador, alto_jugador=30):
        """True si el rayo láser está disparando y cubre la altura dada."""
        if self.estilo == "artillero" and self._laser_fase == "dispara":
            return abs(y_jugador - self._laser_y) < (alto_jugador + 18)
        return False

    def recibir_daño(self, daño=1):
        """Aplica daño salvo que el escudo esté activo. Retorna True si murió."""
        if self._escudo_activo:
            return False          # inmune mientras el escudo está activo
        self.vida -= daño
        return self.vida <= 0

    def esta_muerto(self):
        return self.vida <= 0

    @property
    def escudo_activo(self):
        """True si el escudo protector está activo (boss inmune)."""
        return self._escudo_activo

    @property
    def radio_escudo(self):
        """Radio del escudo para colisión (un poco más grande que el boss)."""
        return self.size + 12

    # ------------------------------------------------------------------ draw

    def draw(self, screen):
        # Flash rojo en fase 3 (detrás del sprite)
        if self.fase == 3 and self._frame % 8 < 3:
            self._flash_rojo(screen)

        sprite = asset_loader.get_boss_sprite(self.sprite_tipo,
                                              self.sprite_color, self.size)
        w, h   = sprite.get_size()
        screen.blit(sprite, (int(self.x) - w // 2, int(self.y) - h // 2))

        # Escudo: aura azul cian giratoria alrededor del boss
        if self._escudo_activo:
            self._dibujar_escudo(screen)

        # Láser: telegrafía (línea fina parpadeante) o rayo grueso
        if self.estilo == "artillero" and self._laser_fase != "idle":
            self._dibujar_laser(screen)

        # Indicador visual de embestida (encima del sprite)
        if self._cargando and self._carga_timer <= 45:
            self._dibujar_indicador_carga(screen)

        # La barra de vida la dibuja game.py DESPUÉS del HUD (mayor prioridad visual)

    def _dibujar_escudo(self, screen):
        s = pygame.Surface((self.size * 2 + 30, self.size * 2 + 30), pygame.SRCALPHA)
        c = self.size + 15
        pulso = int(abs(math.sin(self._frame * 0.15)) * 60) + 120
        pygame.draw.circle(s, (60, 200, 255, pulso), (c, c), self.size + 10, 4)
        pygame.draw.circle(s, (140, 230, 255, pulso // 2), (c, c), self.size + 4, 2)
        screen.blit(s, (int(self.x) - c, int(self.y) - c))

    def _dibujar_laser(self, screen):
        if self._laser_fase == "telegrafia":
            # Línea fina roja parpadeante de aviso (de izquierda del boss a x=0)
            if (self._frame // 4) % 2 == 0:
                ly = int(self._laser_y)
                pygame.draw.line(screen, (255, 60, 60), (0, ly),
                                 (int(self.x), ly), 2)
        elif self._laser_fase == "dispara":
            # Rayo grueso brillante
            ly = int(self._laser_y)
            grosor = 36
            s = pygame.Surface((int(self.x), grosor), pygame.SRCALPHA)
            s.fill((255, 80, 40, 180))
            pygame.draw.rect(s, (255, 220, 180, 230), (0, grosor // 2 - 4, int(self.x), 8))
            screen.blit(s, (0, ly - grosor // 2))

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

