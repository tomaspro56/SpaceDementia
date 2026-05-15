import random

import pygame

import asset_loader
import config


class Background:
    def __init__(self, nivel=1, tema=None):
        self.nivel = nivel
        self.tema = tema or {"id": "cosmic", "fondo_tipo": "espacio", "color_fondo": (5, 0, 20)}
        self.frame_count = 0
        self._generar(nivel)

    def _generar(self, nivel):
        """Genera los elementos del fondo de espacio para el nivel dado."""
        self.nivel = nivel
        velocidad_base = 1.0 + (nivel - 1) * 0.35
        self._generar_espacio(velocidad_base)

    # ------------------------------------------------------------------ espacio

    def _generar_espacio(self, vel):
        # Capa 1: estrellas lejanas (lentas, tenues)
        self.estrellas_fondo = [
            [float(random.randint(0, config.WIDTH)), float(random.randint(0, config.HEIGHT))]
            for _ in range(200)
        ]
        # Capa 2: estrellas medias
        self.estrellas_medias = [
            [float(random.randint(0, config.WIDTH)), float(random.randint(0, config.HEIGHT))]
            for _ in range(130)
        ]
        # Capa 3: estrellas rápidas y brillantes
        self.estrellas_rapidas = [
            [float(random.randint(0, config.WIDTH)), float(random.randint(0, config.HEIGHT))]
            for _ in range(60)
        ]
        # Planetas decorativos de fondo (5 planetas estáticos, semitransparentes)
        _tipos_planetas = [
            "Earth", "Mars", "Saturn", "Neptune", "Crystal",
            "Jupiter", "Hot", "Icy", "Radiated", "Venus",
            "Terrestrial", "Uranus", "Mercury", "Moon", "Sun",
        ]
        tipos_elegidos = random.sample(_tipos_planetas, 5)
        self.planetas = [
            [
                float(random.randint(0, config.WIDTH)),        # x
                float(random.randint(80, config.HEIGHT - 80)), # y
                float(random.randint(100, 250)),        # tamaño en px (reducido)
                tipo,                                   # nombre del planeta
                random.uniform(0.05, 0.2),              # vel_parallax (muy lento)
            ]
            for tipo in tipos_elegidos
        ]
        self.vel_base = vel
        self._bg_offset = 0.0   # Desplazamiento horizontal del BG tileable

    # ------------------------------------------------------------------ update

    def update(self, nivel=None, velocidad=False):
        """Mueve los elementos del fondo. Si el nivel cambió, regenera."""
        if nivel is not None and nivel != self.nivel:
            self._generar(nivel)
            return

        self.frame_count += 1
        vel_mult = 2.0 if velocidad else 1.0
        self._actualizar_espacio(vel_mult)

    def _actualizar_espacio(self, vel_mult=1.0):
        vel = self.vel_base * vel_mult
        # Avanzar offset del BG tileable (velocidad media, capa intermedia)
        bg_w = asset_loader.get_bg().get_width()
        self._bg_offset = (self._bg_offset + vel * 0.6) % bg_w
        # Planetas: parallax muy lento, reaparecen por la derecha
        for p in self.planetas:
            p[0] -= vel * p[4]
            if p[0] + p[2] * 0.5 < 0:
                p[0] = float(config.WIDTH + p[2] * 0.5)
                p[1] = float(random.randint(80, config.HEIGHT - 80))
        for s in self.estrellas_fondo:
            s[0] -= vel * 0.35
            if s[0] < 0:
                s[0] = float(config.WIDTH + random.randint(0, 60))
                s[1] = float(random.randint(0, config.HEIGHT))
        for s in self.estrellas_medias:
            s[0] -= vel * 0.9
            if s[0] < 0:
                s[0] = float(config.WIDTH + random.randint(0, 60))
                s[1] = float(random.randint(0, config.HEIGHT))
        for s in self.estrellas_rapidas:
            s[0] -= vel * 2.2
            if s[0] < 0:
                s[0] = float(config.WIDTH + random.randint(0, 60))
                s[1] = float(random.randint(0, config.HEIGHT))

    # ------------------------------------------------------------------- draw

    def draw(self, screen):
        """Rellena el fondo y dibuja el espacio estrellado."""
        screen.fill((8, 12, 24))   # Tono fijo que coincide con el borde del BG
        self._dibujar_espacio(screen)

    def _dibujar_espacio(self, screen):
        # BG tileable. Escalado a (config.WIDTH+2)×(config.HEIGHT+2) → blit en (-offset-1, -1)
        # para garantizar cobertura total sin gaps de redondeo.
        bg = asset_loader.get_bg()
        bg_w = bg.get_width()
        offset = int(self._bg_offset)
        x0 = -offset - 2
        screen.blit(bg, (x0, -2))
        screen.blit(bg, (x0 + bg_w, -2))
        if x0 + bg_w * 2 < config.WIDTH:
            screen.blit(bg, (x0 + bg_w * 2, -2))

        # Planetas: alpha horneado en asset_loader → blit directo respeta z-order
        for p in self.planetas:
            sprite = asset_loader.get_planet_sprite(p[3])
            tam    = int(p[2])
            scaled = pygame.transform.scale(sprite, (tam, tam))
            screen.blit(scaled, (int(p[0]) - tam // 2, int(p[1]) - tam // 2))

        # Estrellas lejanas: puntitos azulados tenues
        for s in self.estrellas_fondo:
            pygame.draw.circle(screen, (160, 170, 210), (int(s[0]), int(s[1])), 1)

        # Estrellas medias: blancas
        for s in self.estrellas_medias:
            pygame.draw.circle(screen, (230, 235, 255), (int(s[0]), int(s[1])), 1)

        # Estrellas rápidas: más grandes, parpadean
        for s in self.estrellas_rapidas:
            brilla = (self.frame_count // 8 + int(s[1])) % 3 != 0
            if brilla:
                x, y = int(s[0]), int(s[1])
                pygame.draw.circle(screen, (210, 230, 255), (x, y), 2)
                # Cruz de destello
                pygame.draw.line(screen, (255, 255, 255), (x - 3, y), (x + 3, y))
                pygame.draw.line(screen, (255, 255, 255), (x, y - 3), (x, y + 3))

