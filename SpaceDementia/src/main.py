import pygame

pygame.mixer.pre_init(frequency=22050, size=-16, channels=1, buffer=512)
pygame.init()

import config
from game import Game
from menu import Menu
from scoreboard import Scoreboard
from name_entry import pedir_nombre, mostrar_scoreboard
import asset_loader

# Detectar resolución del escritorio para SCALED
_info = pygame.display.Info()
_w, _h = _info.current_w, _info.current_h
# FULLSCREEN | SCALED → fullscreen real con escalado automático.
# Permite Alt+Tab y screenshots sin minimizar.
screen = pygame.display.set_mode((_w, _h), pygame.FULLSCREEN | pygame.SCALED)
config.set_dimensions(*screen.get_size())
asset_loader.inicializar()   # Carga todos los sprites UNA SOLA VEZ
pygame.display.set_caption("SpaceDementia")

scoreboard = Scoreboard()

ejecutando = True
while ejecutando:
    menu = Menu(screen, scoreboard=scoreboard)
    resultado_menu = menu.run()

    if not resultado_menu:
        break

    modo_2j = (resultado_menu == "2j")
    modo_str = "2j" if modo_2j else "1j"

    # Pedir nombre(s) ANTES de jugar
    if modo_2j:
        nombre1 = pedir_nombre(screen, prompt="JUGADOR 1 - TU NOMBRE",
                               color_acento=(80, 160, 255)) or "P1"
        nombre2 = pedir_nombre(screen, prompt="JUGADOR 2 - TU NOMBRE",
                               color_acento=(255, 80, 80)) or "P2"
    else:
        nombre1 = pedir_nombre(screen, prompt="INGRESA TU NOMBRE") or "ANON"
        nombre2 = "P2"

    resultado = "reintentar"
    while resultado == "reintentar":
        game = Game(screen, modo_2j=modo_2j,
                    nombre1=nombre1, nombre2=nombre2)
        resultado = game.run()

        # Si la partida terminó, guardar score en la tabla del modo
        if game.partida_terminada:
            puntaje = game.puntaje_total()
            if modo_2j:
                clave = Scoreboard.clave_combinada(nombre1, nombre2)
                scoreboard.agregar("2j", clave, puntaje)
                resaltado = clave
            else:
                scoreboard.agregar("1j", nombre1, puntaje)
                resaltado = nombre1
            mostrar_scoreboard(screen, scoreboard, modo=modo_str,
                               nombre_resaltado=resaltado)

    if resultado == "quit":
        ejecutando = False

pygame.quit()
