"""
name_entry.py — Pantalla de captura de nombre estilo arcade.

Muestra un campo donde el jugador escribe su nombre (máx 12 chars).
En modo 2 jugadores, pide los dos nombres separados por "+".
"""

import pygame

import config

_MAX_CHARS = 12
_COLOR_TITULO = (0, 255, 200)
_COLOR_TEXTO  = (220, 230, 255)
_COLOR_CAMPO  = (255, 220, 80)
_COLOR_AYUDA  = (120, 140, 170)


def pedir_nombre(screen, sound=None, prompt="INGRESA TU NOMBRE", color_acento=(0, 255, 200)):
    """Captura un nombre del teclado. Retorna el string (puede ser vacío).

    Loop bloqueante propio: dibuja el campo y espera ENTER para confirmar.
    """
    clock = pygame.time.Clock()
    nombre = ""
    font_titulo = pygame.font.SysFont("monospace", 56, bold=True)
    font_campo  = pygame.font.SysFont("monospace", 64, bold=True)
    font_ayuda  = pygame.font.SysFont("monospace", 24)
    frame = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return nombre
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    return nombre.strip()
                elif event.key == pygame.K_BACKSPACE:
                    nombre = nombre[:-1]
                elif event.key == pygame.K_ESCAPE:
                    return nombre.strip()
                else:
                    ch = event.unicode
                    if ch and ch.isprintable() and ch != "+" and len(nombre) < _MAX_CHARS:
                        nombre += ch

        frame += 1

        # Fondo oscuro
        overlay = pygame.Surface((config.WIDTH, config.HEIGHT))
        overlay.fill((6, 8, 20))
        screen.blit(overlay, (0, 0))

        # Título
        surf_t = font_titulo.render(prompt, True, color_acento)
        screen.blit(surf_t, (config.WIDTH // 2 - surf_t.get_width() // 2,
                             config.HEIGHT // 2 - 140))

        # Campo de texto con cursor parpadeante
        cursor = "_" if (frame // 15) % 2 == 0 else " "
        texto_campo = nombre + cursor
        surf_c = font_campo.render(texto_campo, True, _COLOR_CAMPO)
        screen.blit(surf_c, (config.WIDTH // 2 - surf_c.get_width() // 2,
                             config.HEIGHT // 2 - 30))

        # Línea bajo el campo
        ancho_linea = 500
        pygame.draw.line(screen, color_acento,
                         (config.WIDTH // 2 - ancho_linea // 2, config.HEIGHT // 2 + 50),
                         (config.WIDTH // 2 + ancho_linea // 2, config.HEIGHT // 2 + 50), 2)

        # Ayuda
        ayuda = f"Escribe tu nombre (max {_MAX_CHARS})   ·   ENTER para confirmar"
        surf_a = font_ayuda.render(ayuda, True, _COLOR_AYUDA)
        screen.blit(surf_a, (config.WIDTH // 2 - surf_a.get_width() // 2,
                             config.HEIGHT // 2 + 90))

        pygame.display.flip()
        clock.tick(30)


def mostrar_scoreboard(screen, scoreboard, modo="1j", sound=None,
                       nombre_resaltado=None):
    """Muestra la tabla top 10 del modo dado. Espera ENTER o ESC."""
    clock = pygame.time.Clock()
    font_titulo = pygame.font.SysFont("monospace", 64, bold=True)
    font_sub    = pygame.font.SysFont("monospace", 30, bold=True)
    font_pos    = pygame.font.SysFont("monospace", 32, bold=True)
    font_ayuda  = pygame.font.SysFont("monospace", 24)
    frame = 0
    entradas = scoreboard.top(modo, 10)
    subtitulo = "1 JUGADOR" if modo == "1j" else "2 JUGADORES"

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER,
                                 pygame.K_ESCAPE, pygame.K_q):
                    return

        frame += 1
        overlay = pygame.Surface((config.WIDTH, config.HEIGHT))
        overlay.fill((6, 8, 20))
        screen.blit(overlay, (0, 0))

        surf_t = font_titulo.render("MEJORES PUNTAJES", True, _COLOR_TITULO)
        screen.blit(surf_t, (config.WIDTH // 2 - surf_t.get_width() // 2, 70))

        surf_s = font_sub.render(subtitulo, True, (160, 180, 220))
        screen.blit(surf_s, (config.WIDTH // 2 - surf_s.get_width() // 2, 145))

        y0 = 220
        if not entradas:
            vacio = font_pos.render("Aun no hay puntajes. Se el primero!",
                                    True, _COLOR_AYUDA)
            screen.blit(vacio, (config.WIDTH // 2 - vacio.get_width() // 2, y0 + 60))
        else:
            for i, (nombre, puntaje) in enumerate(entradas):
                resaltado = (nombre_resaltado is not None and
                             nombre.lower() == nombre_resaltado.lower())
                color = (255, 255, 120) if resaltado else _COLOR_TEXTO
                linea = f"{i+1:>2}.  {nombre:<14} {puntaje:>8}"
                surf = font_pos.render(linea, True, color)
                x = config.WIDTH // 2 - 250
                screen.blit(surf, (x, y0 + i * 48))

        ayuda = "ENTER / ESC para volver"
        surf_a = font_ayuda.render(ayuda, True, _COLOR_AYUDA)
        screen.blit(surf_a, (config.WIDTH // 2 - surf_a.get_width() // 2,
                             config.HEIGHT - 80))

        pygame.display.flip()
        clock.tick(30)
