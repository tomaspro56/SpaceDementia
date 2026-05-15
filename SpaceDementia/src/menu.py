import math
import random

import pygame

import config
from sound import SoundManager


# Config de fondo espacial para el menú
_FONDO_MENU = {
    "fondo_tipo":  "espacio",
    "color_fondo": (4, 2, 18),
}

# Colores del menú
_COLOR_TITULO  = (80, 160, 255)
_COLOR_GLITCH  = (200, 0, 255)
_COLOR_HUD     = (160, 200, 255)
_COLOR_SEL     = (0, 255, 200)
_COLOR_NORMAL  = (120, 160, 210)


class Menu:
    """Pantalla de inicio: JUGAR / 2 JUGADORES / SALIR.

    Retorna "1j", "2j" o False (salir).
    """

    def __init__(self, screen):
        self.screen = screen
        self._frame = 0
        self._seleccion = 0
        self._opciones = ["JUGAR", "2 JUGADORES", "CONTROLES", "SALIR"]
        from background import Background
        self._bg    = Background(1, tema=_FONDO_MENU)
        self._sound = SoundManager()
        self._sound.iniciar_musica("menu")
        self._estrellas = [
            [float(random.randint(0, config.WIDTH)),
             float(random.randint(0, config.HEIGHT)),
             random.uniform(0.5, 2.5)]
            for _ in range(80)
        ]

    # ----------------------------------------------------------------- loop

    def run(self):
        """Loop del menú. Retorna "1j", "2j" o False."""
        clock = pygame.time.Clock()
        while True:
            self._frame += 1
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self._seleccion = (self._seleccion - 1) % len(self._opciones)
                        self._sound.play("menu_click")
                    elif event.key == pygame.K_DOWN:
                        self._seleccion = (self._seleccion + 1) % len(self._opciones)
                        self._sound.play("menu_click")
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        if self._seleccion == 0:
                            self._sound.detener_musica()
                            return "1j"
                        elif self._seleccion == 1:
                            self._sound.detener_musica()
                            return "2j"
                        elif self._seleccion == 2:
                            self._mostrar_controles()
                        else:
                            return False
                    elif event.key in (pygame.K_q, pygame.K_ESCAPE):
                        return False

            self._bg.update()
            self._dibujar()
            pygame.display.flip()
            clock.tick(30)

    # --------------------------------------------------------------- dibujo

    def _dibujar(self):
        self._bg.draw(self.screen)
        self._dibujar_estrellas_menu()
        self._dibujar_titulo()
        self._dibujar_opciones()

    def _dibujar_estrellas_menu(self):
        """Estrellas adicionales animadas sobre el fondo."""
        for s in self._estrellas:
            s[0] -= s[2]
            if s[0] < 0:
                s[0] = float(config.WIDTH + 10)
                s[1] = float(random.randint(0, config.HEIGHT))
            brilla = (self._frame // 6 + int(s[1])) % 4 != 0
            if brilla:
                pygame.draw.circle(self.screen, (200, 220, 255),
                                   (int(s[0]), int(s[1])), 1)

    def _dibujar_titulo(self):
        font_titulo = pygame.font.SysFont("monospace", 100, bold=True)
        font_sub    = pygame.font.SysFont("monospace", 28)
        titulo = "SpaceDementia"
        surf_t = font_titulo.render(titulo, True, _COLOR_TITULO)
        cx = config.WIDTH // 2 - surf_t.get_width() // 2
        cy = config.HEIGHT // 2 - 270

        # Efecto glitch cada ~55 frames
        ciclo = self._frame % 55
        if ciclo < 6:
            ox = (ciclo % 3 + 1) * 5
            oy = (ciclo % 2) * 2
            surf_g = font_titulo.render(titulo, True, _COLOR_GLITCH)
            self.screen.blit(surf_g, (cx + ox, cy + oy))
            surf_g2 = font_titulo.render(titulo, True, (0, 220, 255))
            self.screen.blit(surf_g2, (cx - ox // 2, cy))

        self.screen.blit(surf_t, (cx, cy))

        y_linea = cy + surf_t.get_height() + 4
        pygame.draw.line(self.screen, _COLOR_TITULO,
                         (cx, y_linea), (cx + surf_t.get_width(), y_linea), 2)

        sub = "— 5 MUNDOS · 25 NIVELES · 5 BOSSES —"
        surf_s = font_sub.render(sub, True, _COLOR_HUD)
        self.screen.blit(surf_s, (config.WIDTH // 2 - surf_s.get_width() // 2, y_linea + 16))

    def _dibujar_opciones(self):
        font = pygame.font.SysFont("monospace", 52, bold=True)
        font_flecha = pygame.font.SysFont("monospace", 52, bold=True)

        cy_base = config.HEIGHT // 2 - 60
        for i, opcion in enumerate(self._opciones):
            seleccionada = (i == self._seleccion)
            color = _COLOR_SEL if seleccionada else _COLOR_NORMAL
            if seleccionada:
                pulso = int(math.sin(self._frame * 0.12) * 8)
                size = 52 + pulso // 4
                font_op = pygame.font.SysFont("monospace", size, bold=True)
            else:
                font_op = font

            surf = font_op.render(opcion, True, color)
            y = cy_base + i * 85
            x = config.WIDTH // 2 - surf.get_width() // 2
            self.screen.blit(surf, (x, y))

            if seleccionada:
                surf_fl = font_flecha.render(">", True, _COLOR_SEL)
                self.screen.blit(surf_fl, (x - surf_fl.get_width() - 18, y))

    # ---------------------------------------------------------------- controles

    def _mostrar_controles(self):
        """Sub-loop que muestra la pantalla de controles hasta que se presione ESC."""
        clock = pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_RETURN,
                                     pygame.K_KP_ENTER, pygame.K_q):
                        return
            self._frame += 1
            self._bg.update()
            self._dibujar()
            self._dibujar_overlay_controles(self.screen)
            pygame.display.flip()
            clock.tick(30)

    def _dibujar_overlay_controles(self, screen):
        """Panel semitransparente con la tabla de controles."""
        # Fondo oscuro global
        velo = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
        velo.fill((0, 0, 10, 170))
        screen.blit(velo, (0, 0))

        # Panel central
        panel_w, panel_h = 680, 480
        px = config.WIDTH  // 2 - panel_w // 2
        py = config.HEIGHT // 2 - panel_h // 2
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((8, 12, 35, 230))
        pygame.draw.rect(panel, (80, 160, 255), (0, 0, panel_w, panel_h), 2)
        screen.blit(panel, (px, py))

        font_t  = pygame.font.SysFont("monospace", 30, bold=True)
        font_s  = pygame.font.SysFont("monospace", 24, bold=True)
        font_n  = pygame.font.SysFont("monospace", 22)
        c_titulo = (80, 160, 255)
        c_sec    = (0, 220, 180)
        c_normal = (180, 210, 255)
        c_esc    = (120, 120, 140)

        def _linea(texto, y_rel, font, color, centrar=False):
            s = font.render(texto, True, color)
            x = px + (panel_w - s.get_width()) // 2 if centrar else px + 40
            screen.blit(s, (x, py + y_rel))

        _linea("CONTROLES", 22, font_t, c_titulo, centrar=True)
        pygame.draw.line(screen, c_titulo,
                         (px + 30, py + 62), (px + panel_w - 30, py + 62), 1)

        secciones = [
            (75,  c_sec,    "JUGADOR 1  (Nave Azul)",  font_s),
            (108, c_normal, "Mover ........... Flechas",  font_n),
            (132, c_normal, "Disparar ........ Espacio",  font_n),
            (156, c_normal, "Mega Bomba ...... B",         font_n),
            (195, c_sec,    "JUGADOR 2  (Nave Roja)",  font_s),
            (228, c_normal, "Mover ........... WASD",      font_n),
            (252, c_normal, "Disparar ........ F",         font_n),
            (276, c_normal, "Mega Bomba ...... G",         font_n),
            (315, c_sec,    "GENERAL",                     font_s),
            (348, c_normal, "Pausa ........... P",         font_n),
            (372, c_normal, "Mutear .......... M  (en juego)", font_n),
        ]
        for y_rel, color, texto, fnt in secciones:
            _linea(texto, y_rel, fnt, color)

        pygame.draw.line(screen, (60, 60, 80),
                         (px + 30, py + 418), (px + panel_w - 30, py + 418), 1)
        _linea("ESC  para volver", 428, font_n, c_esc, centrar=True)
