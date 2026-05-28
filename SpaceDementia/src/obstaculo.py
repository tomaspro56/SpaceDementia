"""
Obstáculos espaciales que aparecen entre oleadas (desde Mundo 2).
Solo colisionan con el jugador — las balas y los enemigos los ignoran.
"""

import math
import random
from abc import ABC, abstractmethod

import pygame

import asset_loader
import config


class Obstaculo(ABC):
    """Clase base abstracta para todas las anomalías espaciales."""

    causa_impacto_fisico = False

    def __init__(self):
        self.vida = 0

    @abstractmethod
    def update(self) -> None:
        """Avanza la lógica del obstáculo un frame. Obligatorio."""
        ...

    @abstractmethod
    def draw(self, screen) -> None:
        """Dibuja el obstáculo. Obligatorio."""
        ...

    def is_dead(self) -> bool:
        return self.vida <= 0

    def afectar_jugador(self, jugador) -> bool:
        """Aplica efecto al jugador. Retorna True si causó daño HP."""
        return False

    def afectar_jugadores(self, jugadores) -> list:
        """Verifica todos los jugadores. Retorna lista de los dañados."""
        dañados = []
        for j in jugadores:
            if self.afectar_jugador(j):
                dañados.append(j)
        return dañados


# ═════════════════════════════════════════════════════════════════════════════

class AgujeronNegro(Obstaculo):
    """
    Agujero negro estático.
    - Atrae al jugador si está a menos de 200 px (fuerza 1.5 px/frame).
    - Al tocar el núcleo: -1 vida.
    - Dura 8 segundos (240 frames) y luego se desvanece.
    """
    RADIO          = 35
    RADIO_GRAVEDAD = 200
    FUERZA         = 1.5
    DURACION       = 240

    def __init__(self):
        super().__init__()
        self.x      = float(random.randint(config.WIDTH // 3, int(config.WIDTH * 0.72)))
        self.y      = float(random.randint(180, config.HEIGHT - 180))
        self.vida   = self.DURACION
        self._frame = 0

    def update(self):
        self._frame += 1
        self.vida   -= 1

    def afectar_jugador(self, jugador):
        """Aplica gravedad y retorna True si el jugador tocó el núcleo."""
        dx   = self.x - jugador.x
        dy   = self.y - jugador.y
        dist = math.sqrt(dx * dx + dy * dy)
        if 0 < dist < self.RADIO_GRAVEDAD:
            factor = self.FUERZA * (1.0 - dist / self.RADIO_GRAVEDAD)
            jugador.x += (dx / dist) * factor
            jugador.y += (dy / dist) * factor
        return dist < self.RADIO - 8

    def draw(self, screen):
        x, y = int(self.x), int(self.y)
        R    = self.RADIO

        ratio = self.vida / self.DURACION
        if ratio > 0.9:
            alpha = int((1.0 - ratio) * 10 * 230)
        elif ratio < 0.2:
            alpha = int((ratio / 0.2) * 230)
        else:
            alpha = 230

        s_nucleo = pygame.Surface((R * 2 + 4, R * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(s_nucleo, (0, 0, 0, alpha), (R + 2, R + 2), R)
        screen.blit(s_nucleo, (x - R - 2, y - R - 2))

        for i in range(12):
            ang      = math.radians((self._frame * 3 + i * 30) % 360)
            r_anillo = R + 14 + int(math.sin(math.radians(self._frame * 6 + i * 60)) * 4)
            ax = x + int(math.cos(ang) * r_anillo)
            ay = y + int(math.sin(ang) * r_anillo)
            grosor = max(1, int(3 * alpha / 230))
            s_pt   = pygame.Surface((grosor * 2 + 2, grosor * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(s_pt, (180, 0, 255, int(alpha * 0.85)),
                               (grosor + 1, grosor + 1), grosor)
            screen.blit(s_pt, (ax - grosor - 1, ay - grosor - 1))

        s_halo = pygame.Surface((R * 2 + 30, R * 2 + 30), pygame.SRCALPHA)
        pygame.draw.circle(s_halo, (90, 0, 140, int(alpha * 0.4)),
                           (R + 15, R + 15), R + 12, 4)
        screen.blit(s_halo, (x - R - 15, y - R - 15))


class Asteroide(Obstaculo):
    """
    Roca espacial que cruza de derecha a izquierda.
    - NO es destruible por balas del jugador.
    - Colisiona con el jugador: -1 vida.
    """

    causa_impacto_fisico = True

    def __init__(self, x, y, radio, velocidad):
        # No llamamos super().__init__() — is_dead() se sobreescribe
        self.x          = float(x)
        self.y          = float(y)
        self.radio      = radio
        self.velocidad  = velocidad
        self._ang_rot   = random.uniform(0, 360)
        self._vel_rot   = random.uniform(-2.5, 2.5)
        self._variante  = random.randint(0, 3)
        self._tam_sprite = max(32, radio * 2)
        self._destruido = False

    def update(self):
        self.x       -= self.velocidad
        self._ang_rot += self._vel_rot

    def is_dead(self):
        return self._destruido or self.x < -self.radio * 2

    def afectar_jugador(self, jugador):
        """Colisiona con el jugador; se destruye al impactar. Retorna True si golpeó."""
        if self._destruido:
            return False
        dx = self.x - jugador.x
        dy = self.y - jugador.y
        if math.sqrt(dx * dx + dy * dy) < self.radio + jugador.size * 0.8:
            self._destruido = True
            return True
        return False

    def draw(self, screen):
        sprite_base = asset_loader.get_asteroid_sprite(self._variante)
        tam    = self._tam_sprite
        sprite = pygame.transform.rotozoom(sprite_base, self._ang_rot, tam / 80)
        screen.blit(sprite, (int(self.x) - sprite.get_width() // 2,
                              int(self.y) - sprite.get_height() // 2))


def generar_campo_asteroides():
    """Devuelve 8–15 asteroides de tamaños variados con gaps para esquivar.

    Mayoría pequeños/medianos y de vez en cuando uno grande. Los más
    grandes se mueven más lento (se sienten más pesados).
    """
    rocas = []
    n = random.randint(8, 15)
    for i in range(n):
        x = config.WIDTH + 40 + i * random.randint(30, 90)
        y = random.randint(60, config.HEIGHT - 60)
        # Categoría de tamaño: 55% pequeño, 30% mediano, 15% grande
        categoria = random.choices(
            ["pequeno", "mediano", "grande"],
            weights=[55, 30, 15]
        )[0]
        if categoria == "pequeno":
            radio = random.randint(14, 26)
            vel   = random.uniform(4.0, 6.5)
        elif categoria == "mediano":
            radio = random.randint(30, 48)
            vel   = random.uniform(3.0, 5.0)
        else:  # grande
            radio = random.randint(55, 80)
            vel   = random.uniform(2.0, 3.5)
        rocas.append(Asteroide(x, y, radio, vel))
    return rocas


class ZonaInterferencia(Obstaculo):
    """
    Franja horizontal de estática que cruza la pantalla.
    - Ralentiza al jugador al 50% mientras está dentro.
    - Dura 10 segundos (300 frames).
    """
    ALTO     = 180
    DURACION = 300

    def __init__(self):
        super().__init__()
        self.y      = float(random.randint(150, config.HEIGHT - self.ALTO - 150))
        self.vida   = self.DURACION
        self._vel_y = 0.7
        self._frame = 0

    def update(self):
        self._frame += 1
        self.vida   -= 1
        self.y      += self._vel_y
        if self.y > config.HEIGHT - self.ALTO - 60 or self.y < 60:
            self._vel_y *= -1

    def afectar_jugador(self, jugador):
        """Ralentiza al jugador si está dentro de la franja."""
        if self.y <= jugador.y <= self.y + self.ALTO:
            jugador.speed = max(1, jugador.velocidad_base // 2)
        return False

    def draw(self, screen):
        iy          = int(self.y)
        ratio       = self.vida / self.DURACION
        alpha_borde = int(min(1.0, ratio * 4) * 130)

        for _ in range(30):
            rx = random.randint(0, config.WIDTH - 1)
            ry = random.randint(iy, iy + self.ALTO - 1)
            rw = random.randint(6, 50)
            rh = random.randint(1, 5)
            cl = random.randint(80, 210)
            s  = pygame.Surface((rw, rh), pygame.SRCALPHA)
            s.fill((cl, cl, min(255, cl + 40), 55))
            screen.blit(s, (rx, ry))

        s_borde = pygame.Surface((config.WIDTH, 3), pygame.SRCALPHA)
        s_borde.fill((120, 180, 255, alpha_borde))
        screen.blit(s_borde, (0, iy))
        screen.blit(s_borde, (0, iy + self.ALTO))


# ══════════════════════════════════════════════════════════════════════════════

class _Meteoro:
    """Proyectil individual de la LluviaMeteoros."""

    def __init__(self, x, y, vx, vy, radio):
        self.x      = float(x)
        self.y      = float(y)
        self.vx     = vx
        self.vy     = vy
        self.radio  = radio
        self._estela: list = []
        self._vivo  = True

    def move(self):
        self._estela.append((self.x, self.y, 8))
        self.x += self.vx
        self.y += self.vy
        self._estela = [(sx, sy, sv - 1) for sx, sy, sv in self._estela if sv > 1]
        if self.x < -self.radio * 2 or self.y > config.HEIGHT + self.radio * 2:
            self._vivo = False

    def is_dead(self):
        return not self._vivo

    def colision(self, jugador):
        dx = self.x - jugador.x
        dy = self.y - jugador.y
        return math.sqrt(dx * dx + dy * dy) < self.radio + jugador.size * 0.7

    def draw(self, screen):
        for sx, sy, sv in self._estela:
            ratio = sv / 8
            r     = max(1, int(self.radio * 0.6 * ratio))
            alpha = int(ratio * 180)
            s     = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 120, 0, alpha), (r + 1, r + 1), r)
            screen.blit(s, (int(sx) - r - 1, int(sy) - r - 1))
        pygame.draw.circle(screen, (220, 180, 100),
                           (int(self.x), int(self.y)), self.radio)
        if self.radio > 4:
            pygame.draw.circle(screen, (255, 220, 140),
                               (int(self.x), int(self.y)), max(2, self.radio - 3))


class LluviaMeteoros(Obstaculo):
    """
    20-30 meteoros en diagonal desde la esquina superior derecha.
    Duran hasta 5 segundos (150 frames) o hasta que todos salgan de pantalla.
    """
    DURACION            = 150
    causa_impacto_fisico = True

    def __init__(self):
        super().__init__()
        self.vida   = self.DURACION
        self._frame = 0
        self._total = random.randint(20, 30)   # cuántos meteoros soltar en total
        self._soltados = 0                       # cuántos van soltados
        self.meteoros: list[_Meteoro] = []

    def _crear_meteoro(self):
        """Crea un meteoro nuevo entrando por la esquina superior derecha."""
        x       = float(config.WIDTH + random.randint(0, 200))
        y       = float(random.randint(-150, int(config.HEIGHT * 0.20)))
        vel     = random.uniform(8, 12)
        ang_deg = random.uniform(30, 55)
        ang_rad = math.radians(ang_deg)
        vx      = -vel * math.cos(ang_rad)
        vy      =  vel * math.sin(ang_rad)
        radio   = random.randint(8, 15)
        self.meteoros.append(_Meteoro(x, y, vx, vy, radio))
        self._soltados += 1

    def update(self):
        self._frame += 1
        self.vida   -= 1
        # Soltar meteoros escalonados mientras dure la lluvia (cada ~5 frames)
        if self._soltados < self._total and self.vida > 0:
            if self._frame % 5 == 0:
                self._crear_meteoro()
        # Mover los meteoros existentes; quitar solo los que YA salieron
        for m in self.meteoros[:]:
            m.move()
            if m.is_dead():
                self.meteoros.remove(m)

    def is_dead(self):
        ya_solto_todos = self._soltados >= self._total or self.vida <= 0
        return ya_solto_todos and not self.meteoros

    def afectar_jugadores(self, jugadores):
        """Retorna lista de jugadores golpeados por meteoros este frame."""
        golpeados = []
        for m in self.meteoros[:]:
            for jug in jugadores:
                if jug.life > 0 and m.colision(jug):
                    if m in self.meteoros:
                        self.meteoros.remove(m)
                    if jug not in golpeados:
                        golpeados.append(jug)
                    break
        return golpeados

    def draw(self, screen):
        for m in self.meteoros:
            m.draw(screen)


# ══════════════════════════════════════════════════════════════════════════════

class PulsoEMP(Obstaculo):
    """
    Onda expansiva circular que desactiva el disparo al contacto.
    Se expande de 0 a 600 px en 3 segundos (90 frames).
    Al tocar un jugador: bloquea su disparo 3 segundos (90 frames).
    """
    RADIO_MAX = 600
    DURACION  = 90

    def __init__(self):
        super().__init__()
        self.x      = float(random.randint(200, config.WIDTH - 200))
        self.y      = float(random.randint(150, config.HEIGHT - 150))
        self.radio  = 0.0
        self.vida   = self.DURACION
        self._frame = 0
        self._golpeados: set = set()

    def update(self):
        self._frame += 1
        self.vida   -= 1
        self.radio   = (1.0 - self.vida / self.DURACION) * self.RADIO_MAX

    def afectar_jugador(self, jugador):
        """Aplica el bloqueo EMP si la onda acaba de cruzar al jugador."""
        jid  = id(jugador)
        if jid in self._golpeados:
            return False
        dx   = jugador.x - self.x
        dy   = jugador.y - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        paso = self.RADIO_MAX / self.DURACION
        if self.radio - paso < dist <= self.radio + jugador.size:
            self._golpeados.add(jid)
            if not jugador.emp_activo:
                jugador.emp_activo = True
                jugador.emp_timer  = 120
        return False

    def draw(self, screen):
        ratio = 1.0 - self.vida / self.DURACION
        alpha = int(max(0, (1.0 - ratio) * 220))
        r     = int(self.radio)
        if r <= 0 or alpha <= 0:
            return
        tam = r * 2 + 20
        s   = pygame.Surface((tam, tam), pygame.SRCALPHA)
        cx  = tam // 2
        grosor = max(2, int(7 * (1.0 - ratio)))
        pygame.draw.circle(s, (50, 150, 255, alpha), (cx, cx), r, grosor)
        if r + 12 < cx:
            pygame.draw.circle(s, (100, 200, 255, alpha // 3), (cx, cx), r + 12, 2)
        for i in range(8):
            ang = math.radians(self._frame * 14 + i * 45)
            ex  = cx + int(math.cos(ang) * r)
            ey  = cx + int(math.sin(ang) * r)
            pygame.draw.circle(s, (180, 220, 255, min(255, alpha + 50)), (ex, ey), 4)
        screen.blit(s, (int(self.x) - cx, int(self.y) - cx))
